from __future__ import annotations

import psutil

from ..models.disk import DiskUsage


def collect() -> list[DiskUsage]:
    result: list[DiskUsage] = []
    for part in psutil.disk_partitions(all=False):
        if not part.fstype or part.fstype == "squashfs":
            continue
        try:
            usage = psutil.disk_usage(part.mountpoint)
        except OSError:
            continue
        inode_percent: float | None = None
        try:
            inode_percent = psutil.disk_usage(part.mountpoint).percent
        except OSError:
            pass
        result.append(
            DiskUsage(
                mountpoint=part.mountpoint,
                device=part.device,
                total=usage.total,
                used=usage.used,
                free=usage.free,
                percent=usage.percent,
                inode_percent=inode_percent,
            )
        )
    return result
