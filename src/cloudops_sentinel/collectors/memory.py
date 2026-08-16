from __future__ import annotations

import os

import psutil

from ..models.metric import Metric


def collect() -> list[Metric]:
    host = os.uname().nodename
    vm = psutil.virtual_memory()
    swap = psutil.swap_memory()
    return [
        Metric(name="memory.total", value=vm.total, unit="bytes", host=host),
        Metric(name="memory.used", value=vm.used, unit="bytes", host=host),
        Metric(name="memory.available", value=vm.available, unit="bytes", host=host),
        Metric(name="memory.percent", value=vm.percent, unit="%", host=host),
        Metric(name="swap.total", value=swap.total, unit="bytes", host=host),
        Metric(name="swap.used", value=swap.used, unit="bytes", host=host),
        Metric(name="swap.percent", value=swap.percent, unit="%", host=host),
    ]
