---
name: sentinel-simulator
description: Use when building or fixing CloudOps Sentinel simulator and demo mode — synthetic scenarios, demo flow, portfolio demo. Trigger words: simulate, simulator, cpu-spike, memory-pressure, disk-pressure, service-down, network-latency, http-errors, demo, scenario.
---

# Sentinel Simulator & Demo

## Purpose

Synthetic, non-destructive telemetry generation so the full pipeline (collect → detect → correlate → incident → recover → report) can be demonstrated without a cloud account or real system damage.

## Scenarios

| Scenario | Module |
|----------|--------|
| cpu-spike | `scenarios/cpu_spike.py` |
| memory-pressure | `scenarios/memory_pressure.py` |
| disk-pressure | `scenarios/disk_pressure.py` |
| service-down | `scenarios/service_down.py` |
| network-latency | `scenarios/network_latency.py` |
| http-errors | `scenarios/http_errors.py` |

Usage: `sentinel simulate cpu-spike --duration 60`

Expected result: synthetic telemetry → detection → `🚨 INCIDENT DETECTED INC-000021 CPU anomaly Severity: HIGH`.

## Demo mode (`sentinel demo`)

The V1 "definition of DONE". Runs end-to-end automatically:

```
Normal system → Simulated anomaly → Detection → Incident creation
→ Severity → Evidence collection → Probable diagnosis
→ Recovery detection → Incident report
```

## Demo UI sequence (per CLI-DESIGN.md)

```
[1] Initializing ✓ → [2] Normal system ✓ → [3] Simulating CPU anomaly (progress 100%)
[4] Detection ▲ Anomaly detected → [5] Correlation ✓ Metrics/Process evidence/Timeline
[6] Incident ◆ HIGH — INC-000001 → [7] Recovery ✓ System returned to baseline → Demo complete.
```

## Rules

- Scenarios inject telemetry through the normal storage/detection path — never bypass the pipeline, or the demo lies.
- Scenarios must not damage the real system.
- Repeatable: same scenario yields a deterministic, testable outcome (simulation tests assert expected severity).