from __future__ import annotations

import os
import platform
import time

import psutil

from ..models.host import HostInfo


def collect() -> HostInfo:
    return HostInfo(
        hostname=os.uname().nodename,
        os=f"{platform.system()} {platform.release()}",
        kernel=platform.version(),
        uptime_seconds=max(0.0, time.time() - psutil.boot_time()),
    )