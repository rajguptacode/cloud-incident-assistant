"""disk-pressure scenario — disk fills toward critical, write errors in logs.

Signals: disk (+20, CRITICAL), log_error_spike (+15) → LOW.
"""

from __future__ import annotations

from cloudops_sentinel.models.log import LogEntry, LogLevel
from cloudops_sentinel.models.metric import Metric

from ..base import ScenarioContext, ScenarioData, timestamps
from ._helpers import fraction, ramp, wave


def generate(ctx: ScenarioContext) -> ScenarioData:
    data = ScenarioData()
    total = (ctx.end - ctx.start).total_seconds()
    crit_begin = total * 0.7

    for ts in timestamps(ctx.start, ctx.end, ctx.interval):
        t = (ts - ctx.start).total_seconds()
        f = fraction(t, total)
        disk = ramp(t, 0, crit_begin, 68, 93) + wave(t, 0.5, 1.5)
        data.metrics.append(
            Metric(
                name="disk", value=round(min(disk, 97), 1), unit="%", host=ctx.host, timestamp=ts
            )
        )
        if f >= 0.7:
            data.logs.append(
                LogEntry(
                    timestamp=ts,
                    severity=LogLevel.ERROR,
                    service="postgres",
                    host=ctx.host,
                    message="disk write failure: no space left",
                    source="simulator",
                )
            )
    return data
