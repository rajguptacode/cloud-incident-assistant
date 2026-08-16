"""In-memory fakes matching Part 3's repository API — hermetic pipeline tests."""

from __future__ import annotations

from datetime import datetime

from cloudops_sentinel.models.incident import Incident, IncidentEvent


class FakeMetricRepo:
    def __init__(self) -> None:
        self.items: list = []

    def save(self, metric) -> None:
        self.items.append(metric)

    def query(
        self,
        *,
        name: str | None = None,
        host: str | None = None,
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> list:
        out = []
        for m in self.items:
            if name and m.name != name:
                continue
            if host and m.host != host:
                continue
            if since and m.timestamp < since:
                continue
            if until and m.timestamp > until:
                continue
            out.append(m)
        return sorted(out, key=lambda m: m.timestamp)


class FakeEventRepo:
    def __init__(self) -> None:
        self.items: list = []

    def save(self, event) -> None:
        self.items.append(event)

    def query(
        self,
        *,
        type: str | None = None,
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> list:
        out = []
        for e in self.items:
            if type and e.type != type:
                continue
            if since and e.timestamp < since:
                continue
            if until and e.timestamp > until:
                continue
            out.append(e)
        return sorted(out, key=lambda e: e.timestamp)


class FakeLogRepo:
    def __init__(self) -> None:
        self.items: list = []

    def save(self, log) -> None:
        self.items.append(log)

    def query(
        self,
        *,
        level: str | None = None,
        service: str | None = None,
        host: str | None = None,
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> list:
        out = []
        for log in self.items:
            if level and log.severity.value.upper() != level.upper():
                continue
            if service and log.service != service:
                continue
            if host and log.host != host:
                continue
            if since and log.timestamp < since:
                continue
            if until and log.timestamp > until:
                continue
            out.append(log)
        return sorted(out, key=lambda l: l.timestamp)


class FakeIncidentRepo:
    def __init__(self) -> None:
        self.incidents: list[Incident] = []
        self.timeline: list[IncidentEvent] = []

    def create(self, incident: Incident) -> Incident:
        if not incident.id:
            highest = 0
            for i in self.incidents:
                try:
                    highest = max(highest, int(i.id.split("-")[1]))
                except (IndexError, ValueError):
                    continue
            incident.id = f"INC-{highest + 1:06d}"
        self.incidents.append(incident)
        return incident

    def get(self, incident_id: str) -> Incident | None:
        return next((i for i in self.incidents if i.id == incident_id), None)

    def update(self, incident: Incident) -> None:
        for i, existing in enumerate(self.incidents):
            if existing.id == incident.id:
                self.incidents[i] = incident
                return
        raise KeyError(f"Incident {incident.id} not found")

    def list(self, status: str | None = None) -> list[Incident]:
        if status:
            return [i for i in self.incidents if i.status.value == status.upper()]
        return list(self.incidents)

    def add_event(self, event: IncidentEvent) -> None:
        self.timeline.append(event)

    def events(self, incident_id: str) -> list[IncidentEvent]:
        return [e for e in self.timeline if e.incident_id == incident_id]


class FakeRepos:
    def __init__(self) -> None:
        self.metric_repo = FakeMetricRepo()
        self.event_repo = FakeEventRepo()
        self.log_repo = FakeLogRepo()
        self.incident_repo = FakeIncidentRepo()
