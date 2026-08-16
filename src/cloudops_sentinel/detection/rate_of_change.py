"""Level 3 detection: rate of change (PRD §14, e.g. CPU 30% → 91% in 2 minutes).

``series`` is a list of ``(timestamp, value)`` tuples sorted ascending.
"""

from __future__ import annotations

from datetime import datetime

ROC_WINDOW_SECONDS = 120
ROC_DELTA = 40


def rate_change(
    series: list[tuple[datetime, float]],
    window: int = ROC_WINDOW_SECONDS,
    delta: float = ROC_DELTA,
) -> tuple[bool, float]:
    """(spiked, delta) — did the value jump >= delta over the trailing window?"""
    if len(series) < 2:
        return False, 0.0
    last_ts, last_value = series[-1]
    for ts, value in reversed(series[:-1]):
        if (last_ts - ts).total_seconds() >= window:
            return (last_value - value) >= delta, last_value - value
    return False, 0.0
