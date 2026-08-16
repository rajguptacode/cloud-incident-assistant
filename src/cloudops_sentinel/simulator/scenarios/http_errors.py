"""http-errors scenario — 5xx storm with matching error logs.

Signals: http_errors (+25, CRITICAL count), log_error_spike (+15) → LOW.
"""

from __future__ import annotations

from cloudops_sentinel.models.event import Event
from cloudops_sentinel.models.log import LogEntry, LogLevel
from cloudops_sentinel.models.metric import Metric

from ..base import ScenarioContext, ScenarioData, timestamps
from ._helpers import wave


def generate(ctx: ScenarioContext) -> ScenarioData:
    data = ScenarioData()
    total = (ctx.end - ctx.start).total_seconds()
    storm_begin = total * 0.4

    for ts in timestamps(ctx.start, ctx.end, ctx.interval):
        t = (ts - ctx.start).total_seconds()
        cpu = 40 + wave(t, 6, 10)
        data.metrics.append(
            Metric(name="cpu", value=round(cpu, 1), unit="%", host=ctx.host, timestamp=ts)
        )
        if t >= storm_begin:
            data.events.append(
                Event(type="http_errors", timestamp=ts, payload={"status": 502, "service": "nginx"})
            )
            data.logs.append(
                LogEntry(
                    timestamp=ts,
                    severity=LogLevel.ERROR,
                    service="nginx",
                    host=ctx.host,
                    message="bad gateway",
                    source="simulator",
                )
            )
    return data
