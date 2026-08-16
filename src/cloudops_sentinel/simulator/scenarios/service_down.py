"""service-down scenario — nginx goes DOWN, then 502s and connection errors.

Signals: service (+30), http_errors (+25), log_error_spike (+15) → HIGH.
"""

from __future__ import annotations

from cloudops_sentinel.models.event import Event
from cloudops_sentinel.models.log import LogEntry, LogLevel
from cloudops_sentinel.models.metric import Metric

from ..base import ScenarioContext, ScenarioData, timestamps
from ._helpers import fraction, wave


def generate(ctx: ScenarioContext) -> ScenarioData:
    data = ScenarioData()
    total = (ctx.end - ctx.start).total_seconds()
    down_at = total * 0.3
    down_emitted = False

    for ts in timestamps(ctx.start, ctx.end, ctx.interval):
        t = (ts - ctx.start).total_seconds()
        f = fraction(t, total)
        cpu = 25 + wave(t, 5, 8) if f < 0.3 else 8 + wave(t, 2, 4)
        data.metrics.append(
            Metric(name="cpu", value=round(cpu, 1), unit="%", host=ctx.host, timestamp=ts)
        )
        if not down_emitted and t >= down_at:
            data.events.append(
                Event(type="service_down", timestamp=ts, payload={"service": "nginx"})
            )
            down_emitted = True
        if t > down_at:
            data.events.append(
                Event(type="http_errors", timestamp=ts, payload={"status": 502, "service": "nginx"})
            )
            data.logs.append(
                LogEntry(
                    timestamp=ts,
                    severity=LogLevel.ERROR,
                    service="nginx",
                    host=ctx.host,
                    message="connection refused",
                    source="simulator",
                )
            )
    return data
