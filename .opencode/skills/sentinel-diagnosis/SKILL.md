---
name: sentinel-diagnosis
description: Use when building or fixing CloudOps Sentinel diagnosis/RCA — probable cause, evidence, confidence, hypotheses, alternatives. Trigger words: diagnosis, rca, root cause, probable cause, evidence, confidence, hypothesis, diagnose, contributing factor.
---

# Sentinel Diagnosis / RCA

## RCA output (always complete)

1. **Probable cause** — top hypothesis.
2. **Supporting evidence** — concrete stored signals (metrics, logs, process data, events).
3. **Contributing factors** — secondary conditions (e.g. memory pressure while CPU is high).
4. **Confidence** — percentage derived from evidence strength.
5. **Alternative possibilities** — competing hypotheses, explicitly labeled as alternatives.

## Rules

- Never claim certainty unless evidence supports it.
- Evidence must be real stored telemetry: metric crossings, process consumption, latency changes, error counts. No invented log lines.
- Confidence is computed, not guessed: weigh evidence count, strength, and correlation.

## Correlation input

RCA consumes correlation-engine output grouped in the incident time window:

- Metrics (CPU/memory/disk/network)
- Logs (error spikes, timeouts, connection failures, restart loops)
- Processes (top consumers at anomaly time)
- Services (down/flapping)
- Events (deployments, process starts)

## Timeline correlation example

```
14:29 Deployment/event → 14:30 CPU ↑ → 14:31 Memory ↑ → 14:31 Latency ↑ → 14:32 HTTP 502 ↑ → 14:32 Incident
```

Related events are grouped into the same incident window automatically.

## Modules

`rca.py` (assembly), `hypotheses.py` (candidate generation + ranking), `confidence.py` (scoring).

## CLI

`sentinel diagnose INC-xxxx` shows symptoms, probable cause, confidence, evidence list.