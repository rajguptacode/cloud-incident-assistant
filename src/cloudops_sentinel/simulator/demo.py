"""End-to-end demo (PRD §30, V1 definition of DONE).

`run_demo` drives the full lifecycle over the REAL pipeline with a virtual
clock (no sleeping): normal → anomaly → detection → incident → severity →
evidence → diagnosis → recovery → report. CLI renders the steps.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta

from cloudops_sentinel.models.common import utcnow
from cloudops_sentinel.models.event import Event
from cloudops_sentinel.models.incident import Incident
from cloudops_sentinel.models.metric import Metric

from ..detection.engine import DetectionEngine
from ..incidents.manager import IncidentManager
from .base import ScenarioContext, timestamps
from .engine import SCENARIOS
from .scenarios._helpers import wave


class _Clock:
    """Mutable clock so the demo can let time pass without sleeping."""

    def __init__(self, start: datetime) -> None:
        self.now = start

    def __call__(self) -> datetime:
        return self.now


@dataclass
class DemoStep:
    phase: str
    status: str
    detail: str


@dataclass
class DemoResult:
    steps: list[DemoStep] = field(default_factory=list)
    incident: Incident | None = None
    report: str = ""


def run_demo(
    repos, *, host: str = "demo-host", now: datetime | None = None, rules=None
) -> DemoResult:
    clock = _Clock(now or utcnow())
    result = DemoResult()
    result.steps.append(DemoStep("initializing", "ok", "storage + detection engine ready"))

    # 1. Normal phase — steady metrics, no anomalies.
    normal_start = clock.now - timedelta(minutes=15)
    for ts in timestamps(normal_start, clock.now, 30):
        t = (ts - normal_start).total_seconds()
        repos.metric_repo.save(
            Metric(
                name="cpu", value=round(28 + wave(t, 6, 8), 1), unit="%", host=host, timestamp=ts
            )
        )
        repos.metric_repo.save(
            Metric(
                name="memory", value=round(54 + wave(t, 3, 6), 1), unit="%", host=host, timestamp=ts
            )
        )
        repos.metric_repo.save(
            Metric(
                name="disk", value=round(67 + wave(t, 1, 2), 1), unit="%", host=host, timestamp=ts
            )
        )
    engine = DetectionEngine(repos.metric_repo, repos.event_repo, repos.log_repo, rules, now=clock)
    normal = engine.evaluate(window_seconds=900)
    result.steps.append(
        DemoStep(
            "normal",
            "ok" if not normal else "fail",
            f"steady-state telemetry, {len(normal)} anomalies",
        )
    )

    # 2. Anomaly — cpu-spike scenario through the normal storage pipeline.
    spike = SCENARIOS["cpu-spike"](
        ScenarioContext(
            host=host, start=clock.now - timedelta(minutes=5), end=clock.now, interval=10
        )
    )
    for m in spike.metrics:
        repos.metric_repo.save(m)
    for e in spike.events:
        repos.event_repo.save(e)
    for log in spike.logs:
        repos.log_repo.save(log)
    result.steps.append(
        DemoStep(
            "anomaly",
            "ok",
            f"cpu-spike injected ({len(spike.metrics)} metrics, {len(spike.events)} events, {len(spike.logs)} logs)",
        )
    )

    # 3. Detection + 4. incident creation/severity.
    detections = engine.evaluate(window_seconds=600)
    manager = IncidentManager(
        repos.incident_repo, repos.metric_repo, repos.event_repo, repos.log_repo, rules, now=clock
    )
    incident = manager.process(detections)
    result.steps.append(
        DemoStep(
            "detection",
            "ok" if detections else "fail",
            f"{len(detections)} signals: " + ", ".join(d.signal for d in detections),
        )
    )
    if incident is not None:
        result.steps.append(
            DemoStep(
                "incident",
                "ok",
                f"{incident.id} severity={incident.severity.value} score={incident.score}",
            )
        )
        result.incident = incident

        # 5. Evidence + diagnosis (correlation + RCA).
        _, _correlation, diagnosis = manager.investigate(incident.id, window_seconds=600)
        result.steps.append(
            DemoStep(
                "investigation",
                "ok",
                f"cause: {diagnosis.probable_cause} (confidence {int(diagnosis.confidence * 100)}%)",
            )
        )

        # 6. Recovery — time passes, metrics return to normal, service back up.
        # Wait 11 min so the 600s recovery window strictly excludes the spike's
        # last sample (repo queries use `>= since`).
        clock.now = clock.now + timedelta(minutes=11)
        recovery_start = clock.now - timedelta(minutes=5)
        for i, ts in enumerate(timestamps(recovery_start, clock.now, 30)):
            t = (ts - recovery_start).total_seconds()
            repos.metric_repo.save(
                Metric(
                    name="cpu",
                    value=round(26 + wave(t, 4, 6), 1),
                    unit="%",
                    host=host,
                    timestamp=ts,
                )
            )
            repos.metric_repo.save(
                Metric(
                    name="memory",
                    value=round(55 + wave(t, 2, 4), 1),
                    unit="%",
                    host=host,
                    timestamp=ts,
                )
            )
            if i == 0:
                repos.event_repo.save(
                    Event(type="service_up", timestamp=ts, payload={"service": "nginx"})
                )
        resolved = manager.check_recovery(samples=2, window=600)
        if resolved:
            r = resolved[0]
            result.steps.append(
                DemoStep(
                    "recovery", "ok", f"{r.id} RESOLVED after {manager.duration_seconds(r):.0f}s"
                )
            )

        # 7. Report.
        result.report = manager.report(incident.id, "txt", window_seconds=600)
        result.steps.append(
            DemoStep("report", "ok", f"report generated ({len(result.report)} chars)")
        )
    return result
