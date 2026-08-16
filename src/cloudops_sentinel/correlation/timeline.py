"""Incident timeline (PRD §26) — merged, sorted signal stream.

Entry kinds map to CLI-DESIGN §17 visual levels:
info | warning | degraded | ok.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from ..detection.engine import DetectionEvent


@dataclass(frozen=True)
class TimelineEntry:
    timestamp: datetime
    kind: str
    message: str

    def as_dict(self) -> dict:
        return {"timestamp": self.timestamp.isoformat(), "kind": self.kind, "message": self.message}


_EVENT_KIND = {
    "service_down": "degraded",
    "service_up": "ok",
    "http_errors": "warning",
    "process_started": "info",
    "deployment": "info",
}

_EVENT_MESSAGE = {
    "service_down": lambda p: f"Service {p.get('service', '?')} down",
    "service_up": lambda p: f"Service {p.get('service', '?')} up",
    "http_errors": lambda p: f"HTTP {p.get('status', '5xx')} errors",
}


def build_timeline(
    system_events: list,
    detections: list[DetectionEvent] | None = None,
    incident_events: list | None = None,
) -> list[TimelineEntry]:
    entries: list[TimelineEntry] = []
    for d in detections or []:
        entries.append(TimelineEntry(d.timestamp, "warning", d.message))
    for ev in system_events:
        kind = _EVENT_KIND.get(ev.type, "info")
        message = _EVENT_MESSAGE.get(
            ev.type, lambda p, _t=ev.type: _t.replace("_", " ").capitalize()
        )(ev.payload)
        entries.append(TimelineEntry(ev.timestamp, kind, message))
    for ie in incident_events or []:
        kind = "ok" if ie.type == "incident_resolved" else "info"
        entries.append(TimelineEntry(ie.timestamp, kind, ie.type.replace("_", " ").capitalize()))
    entries.sort(key=lambda e: e.timestamp)
    return entries
