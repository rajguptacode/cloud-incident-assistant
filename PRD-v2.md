# CloudOps Sentinel — PRD v2

## Product

CloudOps Sentinel

## Positioning

CLI-first, local-first intelligent infrastructure monitoring and incident-analysis platform.

## Vision

CloudOps Sentinel monitors a Linux system, collects metrics/logs/events, detects abnormal behavior, correlates related signals, creates incidents, provides evidence-backed probable diagnosis, detects recovery, and generates reports.

## Core pipeline

```
SYSTEM → COLLECT → NORMALIZE → STORE → DETECT → CORRELATE → ANALYZE → INCIDENT → RECOMMEND → REPORT
```

## Primary interface

CLI.

## Future interfaces

Web dashboard, multi-host backend, cloud adapters.

## Key principles

- Local-first: V1 works without a cloud account.
- Offline-capable: core monitoring/detection/storage works without internet.
- Read-only by default.
- AI is an assistance layer, not the detection foundation.
- No autonomous destructive actions.
- Explainable results: evidence, confidence, and alternatives.
- Same core engine should support future CLI and Web UI.

## Core features

### Monitoring

- CPU utilization, per-core usage, load average.
- Memory, available RAM, swap.
- Disk capacity and inode usage.
- Network interfaces, traffic, latency, packet loss, DNS/HTTP checks.
- Top processes by CPU/memory.
- Linux service status.
- Sentinel's own health.

### Logs

- Read system/application/service logs.
- Parse plain text and structured JSON logs.
- Normalize timestamp, severity, service, host, message, source, event ID.
- Detect error spikes, timeouts, connection failures, restart loops and repeated failures.

### Detection

- Static thresholds.
- Duration-based thresholds.
- Rate-of-change detection.
- Baseline/anomaly detection.
- Configurable rules.

### Incidents

- Lifecycle:
  `DETECTED → TRIAGED → INVESTIGATING → MITIGATED → RESOLVED → CLOSED`
- Alternative: `FALSE POSITIVE`.
- Each incident has a unique ID, severity, score, symptoms, evidence, timeline, probable cause, confidence, contributing factors and alternatives.

### Severity

- INFO / LOW / MEDIUM / HIGH / CRITICAL.
- Severity should combine multiple signals instead of relying on a single metric.

### Correlation

- Correlate metrics, logs, processes, services, network state and events inside an incident time window.

### RCA

- Produce:
  - probable cause
  - supporting evidence
  - contributing factors
  - confidence
  - alternative possibilities
- Do not claim certainty unless evidence supports it.

### Alert deduplication

- Repeated observations should update one incident instead of creating alert floods.

### Recovery

- Detect when metrics/services return to healthy state and record recovery duration.

## CLI

Core commands:

```
sentinel status
sentinel monitor
sentinel cpu
sentinel memory
sentinel disk
sentinel network
sentinel processes
sentinel services
sentinel logs
sentinel incidents
sentinel diagnose INC-xxxx
sentinel timeline INC-xxxx
sentinel report INC-xxxx
sentinel analytics
sentinel config
sentinel maintenance start|stop
sentinel simulate <scenario>
sentinel demo
sentinel health
sentinel ask "<question>" (future AI feature)
```

## Simulator

Controlled, non-destructive scenarios:

- cpu-spike
- memory-pressure
- disk-pressure
- service-down
- network-latency
- http-errors

`sentinel demo` should demonstrate an end-to-end incident lifecycle.

## Reports

Generate incident reports in Markdown, text and JSON; PDF can be a later feature.

## Analytics

- incident count
- severity distribution
- common incident types
- average resolution time
- error frequency
- resource trends
- uptime

## Configuration

YAML configuration for collection intervals, thresholds, retention, alerts and optional AI.

## Data retention

Default retention target: 30 days, configurable.

## JSON/automation

- CLI commands should support JSON output.
- Health command should expose meaningful exit codes: `0` healthy, `1` warning, `2` critical.

## Security

- No hard-coded secrets.
- Environment variables for credentials.
- Read-only monitoring by default.
- AI cannot directly execute arbitrary shell commands.
- Input validation.
- Bounded log processing.
- Monitoring failure must not destabilize the monitored system.

## Reliability

- Sentinel should recover after restart.
- Core monitoring must continue if AI is unavailable.
- Database/storage failures should fail gracefully.
- Resource usage should remain small enough not to become an operational problem.

## Testing

- Unit tests for collectors, parsers, scoring and rules.
- Integration tests for metric → detection → incident.
- Simulation tests.
- Regression tests.
- CLI command tests.

## Future roadmap

V0.1 Foundation → V0.2 Monitoring → V0.3 Linux → V0.4 Storage → V0.5 Detection → V0.6 Incidents → V0.7 Correlation → V0.8 Diagnosis → V0.9 Simulator → V1.0 Stable CLI → V1.1 AI → V1.2 Docker → V2 Web UI → V3 Cloud/multi-host → V4 advanced observability/OpenTelemetry.

## V1 definition of done

`sentinel demo` must demonstrate:

Normal state → simulated anomaly → detection → incident creation → severity → evidence → probable diagnosis → recovery detection → incident report.