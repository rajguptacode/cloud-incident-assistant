"""Simulator engine — synthetic telemetry through the NORMAL pipeline.

Scenarios generate metrics/events/logs, save them via repositories
(storage → detection — never bypassed), then run the real detection and
incident pipeline (PRD §29).

Expected severities per scenario (weights from PRD §22):
  cpu-spike        HIGH    (cpu 20 + memory 15 + http 25 + log 15 = 75)
  memory-pressure  MEDIUM  (memory 15 + http 25 + log 15 = 55)
  disk-pressure    LOW     (disk 20 + log 15 = 35)
  service-down     HIGH    (service 30 + http 25 + log 15 = 70)
  network-latency  LOW     (http 25 + log 15 = 40)
  http-errors      LOW     (http 25 + log 15 = 40)
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta

from cloudops_sentinel.models.common import utcnow
from cloudops_sentinel.models.incident import Incident
from cloudops_sentinel.models.rule import Rule

from ..detection.engine import DetectionEngine, DetectionEvent
from ..detection.rules import rules_from_config
from ..incidents.manager import IncidentManager
from .base import ScenarioContext, ScenarioData, timestamps  # noqa: F401 (re-exported)
from .scenarios import (
    cpu_spike,
    disk_pressure,
    http_errors,
    memory_pressure,
    network_latency,
    service_down,
)

SCENARIOS: dict[str, Callable] = {
    "cpu-spike": cpu_spike.generate,
    "memory-pressure": memory_pressure.generate,
    "disk-pressure": disk_pressure.generate,
    "service-down": service_down.generate,
    "network-latency": network_latency.generate,
    "http-errors": http_errors.generate,
}

EXPECTED_SEVERITY: dict[str, str] = {
    "cpu-spike": "HIGH",
    "memory-pressure": "MEDIUM",
    "disk-pressure": "LOW",
    "service-down": "HIGH",
    "network-latency": "LOW",
    "http-errors": "LOW",
}


@dataclass
class SimulationResult:
    scenario: str
    host: str
    metrics_saved: int
    events_saved: int
    logs_saved: int
    detections: list[DetectionEvent]
    incident: Incident | None
    expected_severity: str


def run(
    repos,
    scenario: str,
    *,
    host: str = "simulated-host",
    duration: int = 300,
    now: datetime | None = None,
    rules: dict[str, Rule] | None = None,
) -> SimulationResult:
    """Run one scenario end-to-end through storage → detection → incidents."""
    if scenario not in SCENARIOS:
        raise ValueError(f"Unknown scenario '{scenario}'. Pick one of: {', '.join(SCENARIOS)}")
    now = now or utcnow()
    start = now - timedelta(seconds=duration)
    interval = max(1, duration // 40)
    data = SCENARIOS[scenario](ScenarioContext(host=host, start=start, end=now, interval=interval))

    for m in data.metrics:
        repos.metric_repo.save(m)
    for e in data.events:
        repos.event_repo.save(e)
    for log in data.logs:
        repos.log_repo.save(log)

    rules = rules or rules_from_config()
    detections = DetectionEngine(
        repos.metric_repo, repos.event_repo, repos.log_repo, rules, now=lambda: now
    ).evaluate(window_seconds=max(300, duration * 2))
    incident = IncidentManager(
        repos.incident_repo,
        repos.metric_repo,
        repos.event_repo,
        repos.log_repo,
        rules,
        now=lambda: now,
    ).process(detections)

    return SimulationResult(
        scenario=scenario,
        host=host,
        metrics_saved=len(data.metrics),
        events_saved=len(data.events),
        logs_saved=len(data.logs),
        detections=detections,
        incident=incident,
        expected_severity=EXPECTED_SEVERITY[scenario],
    )
