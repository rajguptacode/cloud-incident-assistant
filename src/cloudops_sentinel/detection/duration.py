"""Level 2 detection: sustained threshold (PRD §14, e.g. CPU > 90% for 5 minutes).

``series`` is a list of ``(timestamp, value)`` tuples sorted ascending.
"""

from __future__ import annotations

from datetime import datetime

from cloudops_sentinel.models.rule import Rule

from .thresholds import classify


def sustained(
    series: list[tuple[datetime, float]], rule: Rule, level: str, now: datetime | None = None
) -> bool:
    """True when the trailing run of ``level`` readings lasts >= rule.duration seconds."""
    if rule.duration <= 0 or not series:
        return False
    streak_start: datetime | None = None
    for ts, value in reversed(series):
        if classify(value, rule) == level:
            streak_start = ts
        else:
            break
    if streak_start is None:
        return False
    end = now or series[-1][0]
    return (end - streak_start).total_seconds() >= rule.duration
