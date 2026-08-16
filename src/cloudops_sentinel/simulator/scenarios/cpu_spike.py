"""cpu-spike scenario — CPU 20-40% → 95% spike held at peak, 502s + error logs.

Signals: cpu (+20), memory (+15), http_errors (+25), log_error_spike (+15) → HIGH.
The spike holds at peak until the scenario ends; recovery is injected by the
demo/next evaluation cycle (real incidents stay anomalous until fixed).
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
    spike_begin = total * 0.4
    spike_end = total * 0.6

    for ts in timestamps(ctx.start, ctx.end, ctx.interval):
        t = (ts - ctx.start).total_seconds()
        f = fraction(t, total)
        if f < 0.4:
            cpu = wave(t, 28, 8)
        elif f < 0.6:
            cpu = ramp(t, spike_begin, spike_end, 28, 95)
        else:
            cpu = 93 + wave(t, 0, 2)
        memory = 55 + wave(t, 5, 10) + (ramp(t, spike_begin, spike_end, 0, 25) if f >= 0.4 else 0)
        data.metrics.append(
            Metric(name="cpu", value=round(cpu, 1), unit="%", host=ctx.host, timestamp=ts)
        )
        data.metrics.append(
            Metric(
                name="memory",
                value=round(min(memory, 98), 1),
                unit="%",
                host=ctx.host,
                timestamp=ts,
            )
        )

        if t >= spike_begin:
            data.events.append(
                Event(type="http_errors", timestamp=ts, payload={"status": 502, "service": "nginx"})
            )
            data.logs.append(
                LogEntry(
                    timestamp=ts,
                    severity=LogLevel.ERROR,
                    service="nginx",
                    host=ctx.host,
                    message="upstream timeout",
                    source="simulator",
                )
            )
    return data
