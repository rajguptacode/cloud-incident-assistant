"""memory-pressure scenario — RAM climbs to 92%, OOM restarts, 5xxs.

Signals: memory (+15), http_errors (+25), log_error_spike (+15) → MEDIUM.
"""

from __future__ import annotations

from cloudops_sentinel.models.event import Event
from cloudops_sentinel.models.log import LogEntry, LogLevel
from cloudops_sentinel.models.metric import Metric

from ..base import ScenarioContext, ScenarioData, timestamps
from ._helpers import fraction, ramp, wave


def generate(ctx: ScenarioContext) -> ScenarioData:
    data = ScenarioData()
    total = (ctx.end - ctx.start).total_seconds()
    high_begin = total * 0.5

    for ts in timestamps(ctx.start, ctx.end, ctx.interval):
        t = (ts - ctx.start).total_seconds()
        f = fraction(t, total)
        memory = ramp(t, 0, high_begin, 52, 90) + wave(t, 2, 4) if f < 0.8 else 88 + wave(t, 0, 3)
        cpu = 30 + wave(t, 5, 8) + (20 * max(0.0, f - 0.5) if f >= 0.5 else 0)
        data.metrics.append(
            Metric(
                name="memory",
                value=round(min(memory, 98), 1),
                unit="%",
                host=ctx.host,
                timestamp=ts,
            )
        )
        data.metrics.append(
            Metric(name="cpu", value=round(min(cpu, 98), 1), unit="%", host=ctx.host, timestamp=ts)
        )

        if t >= high_begin:
            data.events.append(
                Event(type="http_errors", timestamp=ts, payload={"status": 503, "service": "api"})
            )
            data.logs.append(
                LogEntry(
                    timestamp=ts,
                    severity=LogLevel.ERROR,
                    service="api",
                    host=ctx.host,
                    message="OutOfMemoryError — worker restarted",
                    source="simulator",
                )
            )
    return data
