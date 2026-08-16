from __future__ import annotations

import os

import psutil

from ..models.metric import Metric


def collect(interval: float = 0.0) -> list[Metric]:
    host = os.uname().nodename
    per_core = psutil.cpu_percent(interval=interval, percpu=True)
    times = psutil.cpu_times_percent(interval=0.0)
    load1, load5, load15 = psutil.getloadavg()
    metrics = [
        Metric(name="cpu.percent", value=psutil.cpu_percent(interval=interval), unit="%", host=host),
        Metric(name="cpu.user", value=times.user, unit="%", host=host),
        Metric(name="cpu.system", value=times.system, unit="%", host=host),
        Metric(name="cpu.idle", value=times.idle, unit="%", host=host),
        Metric(name="load.1m", value=load1, host=host),
        Metric(name="load.5m", value=load5, host=host),
        Metric(name="load.15m", value=load15, host=host),
    ]
    for idx, core in enumerate(per_core):
        metrics.append(Metric(name=f"cpu.core.{idx}.percent", value=core, unit="%", host=host))
    return metrics
