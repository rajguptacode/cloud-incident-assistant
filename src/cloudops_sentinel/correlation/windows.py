"""Correlation time windows (PRD §20)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from cloudops_sentinel.models.incident import Incident


@dataclass(frozen=True)
class Window:
    start: datetime
    end: datetime

    def contains(self, ts: datetime) -> bool:
        return self.start <= ts <= self.end


def for_incident(incident: Incident, now: datetime | None = None) -> Window:
    """From incident start to resolution (or now while active)."""
    end = incident.resolved or now
    if end is None:
        end = incident.started
    return Window(incident.started, end)


def around(anchor: datetime, seconds: int) -> Window:
    half = timedelta(seconds=seconds / 2)
    return Window(anchor - half, anchor + half)
