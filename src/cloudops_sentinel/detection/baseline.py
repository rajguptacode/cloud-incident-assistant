"""Level 4 detection: baseline anomaly (PRD §14) — current vs historical mean.

z-score heuristic: current above mean + z*std is an anomaly. Applied to
cpu/memory only; disk growth is monotonic by nature and would false-positive.
"""

from __future__ import annotations

import statistics

MIN_SAMPLES = 5


def baseline_anomaly(
    values: list[float], current: float, z: float = 2.0
) -> tuple[bool, float, float]:
    """(is_anomaly, mean, std). Never an anomaly with fewer than MIN_SAMPLES."""
    if len(values) < MIN_SAMPLES:
        return False, 0.0, 0.0
    mean = statistics.fmean(values)
    std = statistics.stdev(values) if len(values) > 1 else 0.0
    if std == 0:
        return False, mean, std
    return current > mean + z * std, mean, std
