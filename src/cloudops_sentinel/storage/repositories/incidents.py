"""Incidents repository — create/update/get, sequential INC-xxxxxx IDs, timeline events."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from cloudops_sentinel.models.incident import Incident, IncidentEvent
from cloudops_sentinel.storage.database import (
    IncidentEventRow,
    IncidentRow,
    StorageError,
    as_utc,
    utc_now,
)


class IncidentsRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, incident: Incident) -> Incident:
        if not incident.id:
            incident.id = self._next_id()
        row = IncidentRow(
            id=incident.id,
            title=incident.title,
            severity=incident.severity.value,
            status=incident.status.value,
            started=as_utc(incident.started) or utc_now(),
            resolved=as_utc(incident.resolved),
            score=incident.score,
            occurrences=incident.occurrences,
            symptoms=incident.symptoms or [],
            evidence=incident.evidence or [],
            probable_cause=incident.probable_cause,
            confidence=incident.confidence,
            contributing_factors=incident.contributing_factors or [],
            alternatives=incident.alternatives or [],
        )
        self.session.add(row)
        return incident

    def get(self, incident_id: str) -> Incident | None:
        row = self.session.get(IncidentRow, incident_id)
        return self._to_model(row) if row else None

    def update(self, incident: Incident) -> None:
        row = self.session.get(IncidentRow, incident.id)
        if row is None:
            raise StorageError(f"Incident {incident.id} not found")
        row.title = incident.title
        row.severity = incident.severity.value
        row.status = incident.status.value
        row.started = as_utc(incident.started) or row.started
        row.resolved = as_utc(incident.resolved)
        row.score = incident.score
        row.occurrences = incident.occurrences
        row.symptoms = incident.symptoms or []
        row.evidence = incident.evidence or []
        row.probable_cause = incident.probable_cause
        row.confidence = incident.confidence
        row.contributing_factors = incident.contributing_factors or []
        row.alternatives = incident.alternatives or []

    def list(self, status: str | None = None) -> list[Incident]:
        stmt = select(IncidentRow).order_by(IncidentRow.started.desc())
        if status:
            stmt = stmt.where(IncidentRow.status == status.upper())
        return [self._to_model(row) for row in self.session.scalars(stmt)]

    def add_event(self, event: IncidentEvent) -> None:
        self.session.add(
            IncidentEventRow(
                incident_id=event.incident_id,
                type=event.type,
                timestamp=as_utc(event.timestamp) or utc_now(),
                payload=event.payload or {},
            )
        )

    def events(self, incident_id: str) -> list[IncidentEvent]:
        stmt = (
            select(IncidentEventRow)
            .where(IncidentEventRow.incident_id == incident_id)
            .order_by(IncidentEventRow.timestamp)
        )
        return [
            IncidentEvent.model_validate(
                {
                    "incident_id": row.incident_id,
                    "type": row.type,
                    "timestamp": as_utc(row.timestamp),
                    "payload": row.payload or {},
                }
            )
            for row in self.session.scalars(stmt)
        ]

    def _next_id(self) -> str:
        # ponytail: full-table scan for max id; fine at local single-machine scale,
        # switch to a counter table if throughput ever matters.
        highest = 0
        for (incident_id,) in self.session.execute(select(IncidentRow.id)):
            try:
                highest = max(highest, int(incident_id.split("-")[1]))
            except (IndexError, ValueError):
                continue
        return f"INC-{highest + 1:06d}"

    @staticmethod
    def _to_model(row: IncidentRow) -> Incident:
        return Incident.model_validate(
            {
                "id": row.id,
                "title": row.title,
                "severity": row.severity,
                "status": row.status,
                "started": as_utc(row.started),
                "resolved": as_utc(row.resolved),
                "score": row.score,
                "occurrences": row.occurrences,
                "symptoms": row.symptoms or [],
                "evidence": row.evidence or [],
                "probable_cause": row.probable_cause,
                "confidence": row.confidence,
                "contributing_factors": row.contributing_factors or [],
                "alternatives": row.alternatives or [],
            }
        )