from __future__ import annotations

from cloudops_sentinel import collectors


def test_cpu_collect():
    metrics = collectors.cpu.collect(interval=0.0)
    names = {m.name for m in metrics}
    assert "cpu.percent" in names
    assert "load.1m" in names
    assert all(m.host for m in metrics)


def test_memory_collect():
    metrics = collectors.memory.collect()
    names = {m.name for m in metrics}
    assert "memory.total" in names
    assert "memory.percent" in names
    assert "swap.percent" in names
    assert all(m.value >= 0 for m in metrics)


def test_disk_collect():
    disks = collectors.disk.collect()
    assert isinstance(disks, list)
    for d in disks:
        assert d.mountpoint
        assert 0.0 <= d.percent <= 100.0


def test_network_collect():
    metrics = collectors.network.collect()
    names = {m.name for m in metrics}
    assert "network.rx_bytes" in names
    assert "network.tx_bytes" in names
    assert "network.rx_errors" in names


def test_processes_top():
    procs = collectors.processes.top(limit=5, by="cpu")
    assert len(procs) <= 5
    for p in procs:
        assert p.pid > 0
        assert p.name


def test_processes_invalid_by():
    import pytest

    with pytest.raises(ValueError):
        collectors.processes.top(by="nope")


def test_services_collect():
    services = collectors.services.collect(["ssh", "nonexistent-svc-xyz"])
    assert len(services) == 2
    assert all(s.name for s in services)
    assert all(s.status.value in ("RUNNING", "STOPPED", "UNKNOWN") for s in services)


def test_host_collect():
    info = collectors.host.collect()
    assert info.hostname
    assert info.os
    assert info.uptime_seconds >= 0