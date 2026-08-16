---
name: sentinel-incidents
description: Use when building or fixing CloudOps Sentinel incident engine — lifecycle, IDs, severity, scoring, deduplication, suppression, recovery, timeline. Trigger words: incident, lifecycle, severity, score, dedup, deduplication, suppression, maintenance, recovery, timeline, INC-.
---

# Sentinel Incident Engine

## Lifecycle

```
DETECTED → TRIAGED → INVESTIGATING → MITIGATED → RESOLVED → CLOSED
```

False alarm: `DETECTED → FALSE POSITIVE`.

## IDs and storage

- Unique IDs: `INC-000001`, `INC-000002`, ... sequential.
- Each incident stores: ID, severity, score, status, symptoms, evidence, timeline, probable cause, confidence, contributing factors, alternatives, start time, duration, recovery time.

## Severity

INFO / LOW / MEDIUM / HIGH / CRITICAL (score bands 0–20/21–40/41–60/61–80/81–100). Combine multiple signals — never base severity on a single metric.

## Deduplication (critical)

- Repeated observations update ONE incident (occurrences + duration), never create alert floods.
- Example: 50 readings at 95% CPU → one incident `INC-000123`, occurrences: 50, duration: 8m.

## Suppression

- `sentinel maintenance start|stop` — expected alerts suppressed during maintenance.

## Recovery detection

- When metrics/services return to baseline/healthy, mark incident RESOLVED and record recovery duration.
- Example: CPU 96% → 42% → `Status: RESOLVED ✓ Recovery detected after 8m 12s.`

## Timeline

- `sentinel timeline INC-xxxx` lists ordered events with timestamps:
  process started, CPU anomaly, latency ↑, error spike, incident created, metrics normalized, service healthy.

## Modules

`manager.py` (create/update/close), `lifecycle.py`, `deduplication.py`, `severity.py`, `evidence.py`, `recovery.py`.

## Rules

- Incident events/timeline entries must come from stored telemetry — never fabricate.
- Dedup keys: metric+rule+host within an active incident window.