"""Correlation engine (PRD §20) — gather metrics/logs/events/services inside
the incident window and produce a timeline plus per-metric stats.

Note: Part 3's LogsRepository currently imports ``Log`` while models/log.py
defines ``LogEntry`` — if wiring logs fails at merge, fix that import in
``storage/repositories/logs.py`` (Part 3 territory).
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime

from cloudops_sentinel.models.common import utcnow
from cloudops_sentinel.models.incident import Incident

from ..detection.engine import DetectionEvent
from .timeline import TimelineEntry, build_timeline
from .windows import Window, for_incident


@dataclass
class Correlation:
    incident_id: str
    window: Window
    metrics: dict[str, list] = field(default_factory=dict)
    events: list = field(default_factory=list)
    logs: list = field(default_factory=list)
    timeline: list[TimelineEntry] = field(default_factory=list)
    stats: dict[str, dict[str, float]] = field(default_factory=dict)


class CorrelationEngine:
    def __init__(
        self,
        metric_repo,
        event_repo=None,
        log_repo=None,
        incident_repo=None,
        now: Callable[[], datetime] = utcnow,
    ) -> None:
        self.metric_repo = metric_repo
        self.event_repo = event_repo
        self.log_repo = log_repo
        self.incident_repo = incident_repo
        self._now = now

    def correlate(
        self,
        incident: Incident,
        detections: list[DetectionEvent] | None = None,
        window_seconds: int = 300,
    ) -> Correlation:
        window = for_incident(incident, now=self._now())
        metrics = self.metric_repo.query(since=window.start, until=window.end)
        events = (
            self.event_repo.query(since=window.start, until=window.end) if self.event_repo else []
        )
        logs = self.log_repo.query(since=window.start, until=window.end) if self.log_repo else []
        incident_events = self.incident_repo.events(incident.id) if self.incident_repo else []

        by_name: dict[str, list] = {}
        stats: dict[str, dict[str, float]] = {}
        for m in metrics:
            by_name.setdefault(m.name, []).append(m)
        for name, series in by_name.items():
            values = [m.value for m in series]
            stats[name] = {
                "max": max(values),
                "avg": sum(values) / len(values),
                "min": min(values),
                "samples": len(values),
            }

        return Correlation(
            incident_id=incident.id,
            window=window,
            metrics=by_name,
            events=events,
            logs=logs,
            timeline=build_timeline(events, detections, incident_events),
            stats=stats,
        )
