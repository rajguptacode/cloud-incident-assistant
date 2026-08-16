from __future__ import annotations

import os
import socket
import time

import psutil

from ..models.metric import Metric


def _default_interface() -> str:
    for name, addrs in psutil.net_if_stats().items():
        if name == "lo" or not addrs.isup:
            continue
        if any(a.family == socket.AF_INET for a in psutil.net_if_addrs().get(name, [])):
            return name
    return ""


def _latency_ms(host: str = "1.1.1.1", port: int = 53, timeout: float = 1.0) -> float | None:
    try:
        start = time.time()
        with socket.create_connection((host, port), timeout=timeout):
            return (time.time() - start) * 1000
    except OSError:
        return None


def _dns_ok(timeout: float = 1.0) -> bool:
    try:
        socket.setdefaulttimeout(timeout)
        socket.gethostbyname("example.com")
        return True
    except OSError:
        return False


def collect() -> list[Metric]:
    host = os.uname().nodename
    stats = psutil.net_io_counters()
    latency = _latency_ms()
    metrics = [
        Metric(name="network.rx_bytes", value=stats.bytes_recv, unit="bytes", host=host),
        Metric(name="network.tx_bytes", value=stats.bytes_sent, unit="bytes", host=host),
        Metric(name="network.rx_errors", value=stats.errin, host=host),
        Metric(name="network.tx_errors", value=stats.errout, host=host),
        Metric(name="network.latency_ms", value=latency or -1.0, unit="ms", host=host),
        Metric(name="network.packet_loss", value=0.0, unit="%", host=host),
        Metric(name="network.dns_ok", value=1.0 if _dns_ok() else 0.0, host=host),
        Metric(name="network.internet_ok", value=1.0 if latency is not None else 0.0, host=host),
    ]
    iface = _default_interface()
    if iface:
        metrics.append(Metric(name="network.interface", value=0.0, unit=iface, host=host))
    return metrics