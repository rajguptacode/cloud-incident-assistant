---
name: sentinel-collectors
description: Use when writing or fixing CloudOps Sentinel system collectors — CPU, memory, disk, network, processes, services, host. Trigger words: collector, psutil, cpu, memory, ram, disk, network, process, service, host, uptime, metrics collection.
---

# Sentinel Collectors

## Rules

- Read-only: collectors collect information, never modify system state.
- Small and testable: one collector = one responsibility, returns normalized data.
- No terminal/UI rendering inside collectors.
- psutil first; Linux-native interfaces/commands only where psutil lacks the data.
- Collectors feed `models/` (Pydantic) via the app service layer, then storage.

## Collector list (V1)

| Module | Data |
|--------|------|
| `collectors/cpu.py` | usage, per-core, user/system/idle, load average (1m/5m/15m) |
| `collectors/memory.py` | total, used, available, swap, percentage; detect abnormal growth |
| `collectors/disk.py` | filesystem, used/free %, inode usage; forecast marked as estimate |
| `collectors/network.py` | interface, IP, RX/TX, packet errors, latency, packet loss, DNS, HTTP connectivity |
| `collectors/processes.py` | top processes by CPU/memory: PID, process, cpu%, ram% |
| `collectors/services.py` | Linux service status: RUNNING/STOPPED (read-only, no restart) |
| `collectors/host.py` | hostname, OS, uptime |

## Patterns

- psutil API: `psutil.cpu_percent`, `psutil.virtual_memory`, `psutil.disk_usage`, `psutil.net_io_counters`, `psutil.process_iter`, `psutil.boot_time`.
- Each collector returns a Pydantic model from `models/` — normalized, validated.
- Collectors must never crash the daemon: catch and report per-collector errors (observability), continue the rest.
- Async collection where appropriate; keep Sentinel overhead small.