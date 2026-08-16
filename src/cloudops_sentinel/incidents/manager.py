"""Incident manager — create/update/dedup/resolve, wiring storage repos.

Domain logic only: takes detection events, scores severity (PRD §22),
deduplicates (PRD §23), persists via the incidents repository, tracks
timeline events, and resolves incidents on recovery (PRD §25).
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from typing import Protocol

from cloudops_sentinel.models.common import utcnow
from cloudops_sentinel.models.incident import Incident, IncidentEvent, IncidentStatus
from cloudops_sentinel.models.rule import Rule

from ..correlation.engine import CorrelationEngine
from ..detection.engine import DetectionEvent
from ..detection.rules import rules_from_config
from ..detection.scoring import WEIGHTS, score_signals, severity_from_score
from ..diagnosis.rca import diagnose
from .deduplication import active_incidents, find_match
from .evidence import add_evidence, symptom
from .lifecycle import transition
from .recovery import recovered

TITLES: dict[str, str] = {
    "cpu": "CPU anomaly",
    "memory": "Memory pressure",
    "disk": "Disk usage critical",
    "service": "Service down",
    "http_errors": "HTTP errors",
    "log_error_spike": "Log error spike",
}


class IncidentRepo(Protocol):
    def create(self, incident: Incident) -> Incident: ...
    def get(self, incident_id: str) -> Incident | None: ...
    def update(self, incident: Incident) -> None: ...
    def list(self, status: str | None = None) -> list[Incident]: ...
    def add_event(self, event: IncidentEvent) -> None: ...
    def events(self, incident_id: str) -> list[IncidentEvent]: ...


class IncidentManager:
    def __init__(
        self,
        incidents_repo: IncidentRepo,
        metric_repo=None,
        event_repo=None,
        log_repo=None,
        rules: dict[str, Rule] | None = None,
        now: Callable[[], datetime] = utcnow,
    ) -> None:
        self.repo = incidents_repo
        self.metric_repo = metric_repo
        self.event_repo = event_repo
        self.log_repo = log_repo
        self.rules = rules or rules_from_config()
        self._now = now

    # ── creation / dedup ──────────────────────────────────────────────────

    def process(self, detections: list[DetectionEvent]) -> Incident | None:
        """Turn detections into incidents. Repeats update the SAME incident."""
        if not detections:
            return None
        signals = {d.signal: d.level for d in detections}
        existing = find_match(active_incidents(self.repo.list()), frozenset(signals))
        if existing is not None:
            return self._update(existing, detections, signals)
        return self._create(detections, signals)

    def _create(self, detections: list[DetectionEvent], signals: dict[str, str]) -> Incident:
        score = score_signals(signals)
        primary = max(signals, key=lambda s: WEIGHTS.get(s, 0))
        incident = Incident(
            id="",  # repo assigns INC-xxxxxx
            title=TITLES.get(primary, f"{primary} anomaly"),
            severity=severity_from_score(score),
            score=score,
            status=IncidentStatus.DETECTED,
            started=min(d.timestamp for d in detections),
        )
        for d in detections:
            incident.symptoms.append(symptom(d.signal, d.message))
            add_evidence(incident, d.evidence)
        self.repo.create(incident)
        self.repo.add_event(
            IncidentEvent(
                incident_id=incident.id,
                type="incident_created",
                timestamp=self._now(),
                payload={"signals": sorted(signals), "score": score},
            )
        )
        return incident

    def _update(
        self, incident: Incident, detections: list[DetectionEvent], signals: dict[str, str]
    ) -> Incident:
        incident.occurrences += 1
        incident.score = max(incident.score, score_signals(signals))
        incident.severity = severity_from_score(incident.score)
        for d in detections:
            if symptom(d.signal, d.message) not in incident.symptoms:
                incident.symptoms.append(symptom(d.signal, d.message))
            add_evidence(incident, d.evidence)
        self.repo.update(incident)
        self.repo.add_event(
            IncidentEvent(
                incident_id=incident.id,
                type="incident_updated",
                timestamp=self._now(),
                payload={"occurrences": incident.occurrences},
            )
        )
        return incident

    # ── queries ──────────────────────────────────────────────────────────

    def get(self, incident_id: str) -> Incident | None:
        return self.repo.get(incident_id)

    def list(self, status: str | None = None) -> list[Incident]:
        return self.repo.list(status=status)

    # ── lifecycle ────────────────────────────────────────────────────────

    def transition(self, incident_id: str, status: IncidentStatus) -> Incident:
        incident = self._require(incident_id)
        transition(incident, status)
        self.repo.update(incident)
        self.repo.add_event(
            IncidentEvent(
                incident_id=incident.id,
                type=f"incident_{status.value.lower()}",
                timestamp=self._now(),
            )
        )
        return incident

    # ── recovery ─────────────────────────────────────────────────────────

    def check_recovery(self, *, samples: int = 2, window: int = 300) -> list[Incident]:
        """Resolve every active incident whose symptoms all returned to normal."""
        resolved: list[Incident] = []
        for incident in active_incidents(self.repo.list()):
            if not recovered(
                incident,
                self.metric_repo,
                self.event_repo,
                self.log_repo,
                self.rules,
                samples=samples,
                window=window,
                now=self._now(),
            ):
                continue
            incident.status = IncidentStatus.RESOLVED
            incident.resolved = self._now()
            self.repo.update(incident)
            self.repo.add_event(
                IncidentEvent(
                    incident_id=incident.id,
                    type="incident_resolved",
                    timestamp=incident.resolved,
                    payload={"duration_seconds": self.duration_seconds(incident)},
                )
            )
            resolved.append(incident)
        return resolved

    # ── investigation / diagnosis / report ───────────────────────────────

    def investigate(
        self, incident_id: str, window_seconds: int = 300
    ) -> tuple[Incident, object, object]:
        """Correlate + diagnose. Returns (incident, correlation, diagnosis)."""
        incident = self._require(incident_id)
        correlation = CorrelationEngine(
            self.metric_repo, self.event_repo, self.log_repo, self.repo, now=self._now
        ).correlate(incident, window_seconds=window_seconds)
        diagnosis = diagnose(incident, correlation)
        incident.probable_cause = diagnosis.probable_cause
        incident.confidence = diagnosis.confidence
        incident.contributing_factors = diagnosis.contributing_factors
        incident.alternatives = diagnosis.alternatives
        add_evidence(incident, diagnosis.evidence)
        self.repo.update(incident)
        self.repo.add_event(
            IncidentEvent(incident_id=incident.id, type="incident_diagnosed", timestamp=self._now())
        )
        return incident, correlation, diagnosis

    def report(self, incident_id: str, fmt: str = "txt", window_seconds: int = 300) -> str:
        from ..reports.generator import generate

        incident, correlation, _ = self.investigate(incident_id, window_seconds=window_seconds)
        return generate(incident, correlation, fmt)

    # ── helpers ──────────────────────────────────────────────────────────

    def _require(self, incident_id: str) -> Incident:
        incident = self.repo.get(incident_id)
        if incident is None:
            raise KeyError(f"Incident {incident_id} not found")
        return incident

    @staticmethod
    def duration_seconds(incident: Incident) -> float:
        if incident.resolved is None:
            return 0.0
        return (incident.resolved - incident.started).total_seconds()
