"""network-latency scenario — latency climbs (data only), timeouts + 5xxs.

Signals: http_errors (+25), log_error_spike (+15) → LOW.
"""

from __future__ import annotations

from cloudops_sentinel.models.event import Event
from cloudops_sentinel.models.log import LogEntry, LogLevel
from cloudops_sentinel.models.metric import Metric

from ..base import ScenarioContext, ScenarioData, timestamps
from ._helpers import ramp, wave


def generate(ctx: ScenarioContext) -> ScenarioData:
    data = ScenarioData()
    total = (ctx.end - ctx.start).total_seconds()
    bad_begin = total * 0.5

    for ts in timestamps(ctx.start, ctx.end, ctx.interval):
        t = (ts - ctx.start).total_seconds()
        latency = ramp(t, 0, bad_begin, 25, 1500) + wave(t, 20, 50)
        data.metrics.append(
            Metric(
                name="network_latency",
                value=round(latency, 0),
                unit="ms",
                host=ctx.host,
                timestamp=ts,
            )
        )
        if t >= bad_begin:
            data.events.append(
                Event(type="http_errors", timestamp=ts, payload={"status": 504, "service": "api"})
            )
            data.logs.append(
                LogEntry(
                    timestamp=ts,
                    severity=LogLevel.ERROR,
                    service="api",
                    host=ctx.host,
                    message="upstream timeout after 30s",
                    source="simulator",
                )
            )
    return data
