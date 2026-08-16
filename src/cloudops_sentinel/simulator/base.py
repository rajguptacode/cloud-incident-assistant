"""Shared scenario types — no imports from engine/scenarios to avoid cycles."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta

from cloudops_sentinel.models.event import Event
from cloudops_sentinel.models.log import LogEntry
from cloudops_sentinel.models.metric import Metric

INTERVAL_SECONDS = 10


@dataclass
class ScenarioContext:
    host: str
    start: datetime
    end: datetime
    interval: int = INTERVAL_SECONDS


@dataclass
class ScenarioData:
    metrics: list[Metric] = field(default_factory=list)
    events: list[Event] = field(default_factory=list)
    logs: list[LogEntry] = field(default_factory=list)


def timestamps(start: datetime, end: datetime, interval: int = INTERVAL_SECONDS) -> list[datetime]:
    out = []
    ts = start
    while ts <= end:
        out.append(ts)
        ts += timedelta(seconds=interval)
    return out
