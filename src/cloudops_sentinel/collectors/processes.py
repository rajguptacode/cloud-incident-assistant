from __future__ import annotations

import psutil

from ..models.process import ProcessInfo


def top(limit: int = 10, by: str = "cpu") -> list[ProcessInfo]:
    if by not in ("cpu", "memory"):
        raise ValueError("by must be 'cpu' or 'memory'")
    attr = "cpu_percent" if by == "cpu" else "memory_percent"
    result: list[ProcessInfo] = []
    for proc in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent", "cmdline"]):
        try:
            info = proc.info
            result.append(
                ProcessInfo(
                    pid=info["pid"],
                    name=info["name"] or "?",
                    cpu_percent=float(info["cpu_percent"] or 0.0),
                    memory_percent=float(info["memory_percent"] or 0.0),
                    command=" ".join(info["cmdline"] or [])[:200],
                )
            )
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    result.sort(key=lambda p: getattr(p, attr), reverse=True)
    return result[:limit]