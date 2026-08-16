from __future__ import annotations

import shutil
import subprocess

from ..models.service import Service, ServiceStatus


def _systemctl_is_active(name: str) -> ServiceStatus:
    if shutil.which("systemctl") is None:
        return ServiceStatus.UNKNOWN
    try:
        result = subprocess.run(
            ["systemctl", "is-active", "--quiet", name],
            capture_output=True,
            timeout=5,
            check=False,
        )
        return ServiceStatus.RUNNING if result.returncode == 0 else ServiceStatus.STOPPED
    except (subprocess.SubprocessError, OSError):
        return ServiceStatus.UNKNOWN


def check(name: str) -> Service:
    return Service(name=name, status=_systemctl_is_active(name))


def collect(names: list[str]) -> list[Service]:
    return [check(name) for name in names]