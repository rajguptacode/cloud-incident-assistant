"""Signal weights and severity bands (PRD §22).

Weights: CPU +20, Memory +15, Disk critical +20, Service down +30,
HTTP errors +25, Log error spike +15. Bands: 0-20 INFO, 21-40 LOW,
41-60 MEDIUM, 61-80 HIGH, 81-100 CRITICAL.

Severity combines multiple signals — never one metric alone (AGENTS.md).
Each distinct signal counts once per incident (dedup, no alert floods).
"""

from __future__ import annotations

from cloudops_sentinel.models.incident import Severity

WEIGHTS: dict[str, int] = {
    "cpu": 20,
    "memory": 15,
    "disk": 20,
    "service": 30,
    "http_errors": 25,
    "log_error_spike": 15,
}

_BANDS: tuple[tuple[int, Severity], ...] = (
    (20, Severity.INFO),
    (40, Severity.LOW),
    (60, Severity.MEDIUM),
    (80, Severity.HIGH),
    (100, Severity.CRITICAL),
)


def score_signals(signals: dict[str, str]) -> int:
    """Score {signal: level} detections. Disk counts only when CRITICAL (PRD §22)."""
    total = 0
    for signal, level in signals.items():
        weight = WEIGHTS.get(signal)
        if weight is None:
            continue
        if signal == "disk" and level != "CRITICAL":
            continue
        total += weight
    return min(total, 100)


def severity_from_score(score: float) -> Severity:
    for ceiling, severity in _BANDS:
        if score <= ceiling:
            return severity
    return Severity.CRITICAL
