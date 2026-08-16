---
name: sentinel-detection
description: Use when building or fixing CloudOps Sentinel detection engine — thresholds, duration rules, rate of change, baseline anomaly, rule config. Trigger words: detection, threshold, rule, anomaly, baseline, duration, rate of change, spike, alert.
---

# Sentinel Detection Engine

## Four detection levels

| Level | Type | Example |
|-------|------|---------|
| 1 | Static threshold | CPU > 90% |
| 2 | Duration | CPU > 90% continuously for 5 minutes |
| 3 | Rate of change | CPU 30% → 91% in 2 minutes |
| 4 | Baseline anomaly | current value vs historical normal range (e.g. normal 20–40%, current 91%) |

Each level builds on the previous. Detection converts observations into detection events using configurable rules.

## Default rules (config/default.yaml)

```yaml
cpu:
  warning: 70
  critical: 90
  duration: 300
memory:
  warning: 75
  critical: 90
disk:
  warning: 80
  critical: 90
```

## Rule engine behavior

- Rules are user-configurable via `sentinel config edit`.
- Detection events feed the correlation engine, not incidents directly.
- Config validation: rules must be validated (types, ranges) before use.
- Duration/rate/baseline logic lives in separate modules:
  `thresholds.py`, `duration.py`, `rate_of_change.py`, `baseline.py`, `scoring.py`.

## Scoring (detection signals → incident score)

| Signal | Score |
|--------|-------|
| CPU anomaly | +20 |
| Memory anomaly | +15 |
| Disk critical | +20 |
| Service down | +30 |
| HTTP errors | +25 |
| Log error spike | +15 |

Weights configurable. Score bands: 0–20 INFO, 21–40 LOW, 41–60 MEDIUM, 61–80 HIGH, 81–100 CRITICAL.

## Baseline notes

- Baselines come from stored historical metrics (SQLite), default retention 30 days.
- Never claim an anomaly without stored evidence.
- Baseline must degrade gracefully when history is insufficient (fall back to thresholds).