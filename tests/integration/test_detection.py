"""Detection engine unit tests — thresholds, duration, rate of change,
baseline, scoring bands (PRD §14, §22)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from cloudops_sentinel.detection import (
    baseline_anomaly,
    classify,
    rate_change,
    score_signals,
    severity_from_score,
    sustained,
)
from cloudops_sentinel.models.rule import Rule

T0 = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)
CPU = Rule(metric="cpu", warning=70, critical=90, duration=300)


def ts(seconds: int) -> datetime:
    return T0 + timedelta(seconds=seconds)


def series(start: int, step: int, values: list[float]) -> list[tuple[datetime, float]]:
    return [(ts(start + i * step), v) for i, v in enumerate(values)]


def test_classify_levels():
    assert classify(50, CPU) == "NORMAL"
    assert classify(80, CPU) == "WARNING"
    assert classify(95, CPU) == "CRITICAL"


def test_classify_gte_operator():
    rule = Rule(metric="http_errors", warning=5, critical=20, operator="gte")
    assert classify(5, rule) == "WARNING"
    assert classify(20, rule) == "CRITICAL"


def test_duration_sustained_fires():
    values = [95.0] * 6
    assert sustained(series(0, 60, values), CPU, "CRITICAL", now=ts(360))


def test_duration_short_spike_does_not_fire():
    values = [95.0] * 2
    assert not sustained(series(0, 60, values), CPU, "CRITICAL", now=ts(120))


def test_rate_change_spike():
    values = [30.0] * 6 + [91.0]
    spiked, delta = rate_change(series(0, 60, values), window=120, delta=40)
    assert spiked and delta >= 40


def test_baseline_anomaly_detects_deviation():
    normal = [22, 24, 25, 23, 26, 24, 25, 22, 23, 24]
    assert baseline_anomaly(normal, 61)[0]


def test_baseline_anomaly_ignores_normal():
    normal = [22, 24, 25, 23, 26, 24, 25, 22, 23, 24]
    assert not baseline_anomaly(normal, 25)[0]


def test_baseline_needs_min_samples():
    assert not baseline_anomaly([20, 21], 95)[0]


def test_severity_bands():
    assert severity_from_score(20) == "INFO"
    assert severity_from_score(21) == "LOW"
    assert severity_from_score(60) == "MEDIUM"
    assert severity_from_score(61) == "HIGH"
    assert severity_from_score(100) == "CRITICAL"


def test_score_signals_weights():
    assert score_signals({"cpu": "WARNING"}) == 20
    assert score_signals({"cpu": "CRITICAL", "memory": "CRITICAL", "disk": "CRITICAL"}) == 55
    assert score_signals({"disk": "WARNING"}) == 0  # disk counts only when CRITICAL
    assert (
        score_signals(
            {"service": "CRITICAL", "http_errors": "CRITICAL", "log_error_spike": "CRITICAL"}
        )
        == 70
    )


def test_score_capped_at_100():
    assert (
        score_signals(
            {
                "cpu": "CRITICAL",
                "memory": "CRITICAL",
                "disk": "CRITICAL",
                "service": "CRITICAL",
                "http_errors": "CRITICAL",
                "log_error_spike": "CRITICAL",
            }
        )
        == 100
    )
