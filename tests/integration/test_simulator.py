"""Simulator tests — each scenario produces the expected incident severity
through the real pipeline; demo runs end-to-end (PRD §29-30)."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from cloudops_sentinel.simulator import EXPECTED_SEVERITY, SCENARIOS, run, run_demo

from .fakes import FakeRepos

T0 = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)


@pytest.mark.parametrize("scenario", sorted(SCENARIOS))
def test_scenario_produces_expected_severity(scenario):
    repos = FakeRepos()
    result = run(repos, scenario, duration=300, now=T0)
    assert result.incident is not None, f"{scenario}: no incident created"
    assert result.incident.severity.value == EXPECTED_SEVERITY[scenario]
    assert result.metrics_saved > 0
    assert result.detections, f"{scenario}: no detections"


def test_unknown_scenario_rejected():
    with pytest.raises(ValueError):
        run(FakeRepos(), "nope", now=T0)


def test_demo_runs_full_lifecycle():
    repos = FakeRepos()
    result = run_demo(repos, host="demo-host", now=T0)
    phases = [s.phase for s in result.steps]
    for phase in (
        "normal",
        "anomaly",
        "detection",
        "incident",
        "investigation",
        "recovery",
        "report",
    ):
        assert phase in phases, f"demo missed phase {phase}"
    assert all(s.status == "ok" for s in result.steps)
    assert result.incident is not None
    assert result.incident.status.value == "RESOLVED"
    assert "INCIDENT" in result.report


def test_demo_recovery_duration_positive():
    repos = FakeRepos()
    result = run_demo(repos, now=T0)
    assert (result.incident.resolved - result.incident.started).total_seconds() > 0
