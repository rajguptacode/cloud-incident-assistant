# CloudOps Sentinel

**CLI-first, local-first intelligent infrastructure monitoring and incident-analysis platform.**

CloudOps Sentinel watches a Linux system, collects metrics, logs and events, detects anomalies, correlates signals into incidents, diagnoses probable root causes with evidence, detects recovery, and generates reports — all from your terminal, fully offline, with no cloud account required.

It is built to be *explainable*: every incident carries its evidence, confidence score, and alternative hypotheses. Never blind alerts, never alert floods — repeated observations update one incident instead of spamming.

---

## Why it exists

Monitoring tools either dump raw numbers and leave analysis to you, or send alerts with no context. CloudOps Sentinel closes that gap for a single host:

1. **Collect** — CPU, memory, disk, network, processes, services, host telemetry (psutil-first, read-only).
2. **Detect** — threshold, duration, rate-of-change and baseline-anomaly rules; severity is never decided by one metric alone.
3. **Correlate** — signals that fire together inside a window are merged into a single incident.
4. **Diagnose** — probable root cause, supporting evidence, confidence, and alternative explanations.
5. **Recover** — the system notices when metrics return to normal and resolves the incident automatically.
6. **Report** — text, Markdown or JSON reports per incident, plus historical analytics.

The entire pipeline runs locally and offline. It never modifies your system, never executes destructive actions, and observes itself — collector, database and detection health are visible via `sentinel health`.

## Features

- **Real-time status** — `sentinel status` shows host health, per-resource utilization bars, service states and open incident counts at a glance.
- **Live monitoring** — `sentinel monitor` streams per-second resource telemetry with sparklines.
- **Incident lifecycle** — `DETECTED → TRIAGED → INVESTIGATING → MITIGATED → RESOLVED → CLOSED`, with deduplication (one incident per problem, not an alert storm) and automatic recovery detection.
- **Severity scoring** — multi-signal scoring (0–100) combining metric severity, breadth of symptoms, service impact and incident age. Exit codes map to health: `0` healthy, `1` warning, `2` critical — scriptable for CI and paging hooks.
- **Diagnosis** — evidence-backed probable cause with confidence (0–100%), contributing factors and alternatives. Never claims certainty without stored evidence.
- **Safe simulation** — `sentinel simulate` injects realistic scenarios (`cpu-spike`, `memory-pressure`, `disk-pressure`, `service-down`, `network-latency`, `http-errors`) through the *real* detection pipeline for testing and demos — no fake stubs.
- **End-to-end demo** — `sentinel demo` walks the full flow in seconds: normal → anomaly → detection → incident → severity → evidence → diagnosis → recovery → report.
- **Optional AI analysis** — a provider-neutral AI adapter can add natural-language diagnosis on top of sanitized incident context. Disabled by default; the core works without it.
- **Retention** — 30-day data retention by default, configurable.
- **Machine output** — every command supports `--json` for scripting; colors via semantic tokens with `--no-color` / `NO_COLOR` support and ASCII fallback.

## Architecture

```
SYSTEM → COLLECT → NORMALIZE → STORE → DETECT → CORRELATE → ANALYZE → INCIDENT → RECOMMEND → REPORT
```

Strict layering — presentation never touches system calls, and collectors never render output, so the same data feeds CLI, JSON and future Web UI/API:

```
┌─────────────────────────────────────────────────────────────┐
│  cli/        Typer commands, args, JSON output, exit codes  │
│  ui/         Rich terminal UI (theme tokens, panels, bars)  │
├─────────────────────────────────────────────────────────────┤
│  incidents/  lifecycle, dedup, severity, recovery           │
│  detection/  thresholds, duration, rate-of-change, baseline │
│  correlation/  signal windows & merging                     │
│  diagnosis/  probable cause, evidence, confidence           │
│  simulator/  synthetic scenarios, demo mode                 │
│  reports/    txt / markdown / json, analytics               │
│  health/     self-observation                              │
├─────────────────────────────────────────────────────────────┤
│  storage/    SQLite repositories (metrics, logs, events,    │
│              incidents), retention, WAL pragmas             │
├─────────────────────────────────────────────────────────────┤
│  collectors/ read-only psutil reads (CPU, memory, disk,     │
│              network, processes, services, host)            │
│  logs/       log reading, parsing, normalization            │
│  models/     Pydantic domain models                         │
└─────────────────────────────────────────────────────────────┘
```

**Tech stack:** Python 3.12 · Typer · Rich · psutil · Pydantic · SQLAlchemy/SQLite · PyYAML — deliberately minimal dependencies, standard library first.

## Installation

```bash
git clone https://github.com/rajguptacode/cloud-incident-assistant.git
cd cloud-incident-assistant
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Quick start

```bash
sentinel status                 # live system health
sentinel demo                   # end-to-end demo: anomaly → incident → report
sentinel simulate cpu-spike     # run a realistic scenario through the real pipeline
sentinel incidents              # list incidents
sentinel diagnose INC-000001    # probable cause, evidence, confidence
sentinel report INC-000001 --format markdown
sentinel analytics              # historical summary
sentinel health                 # self-health; exit 0/1/2
```

### Command reference

| Group | Command | Purpose |
|---|---|---|
| Monitoring | `status` | Current system health |
| | `monitor` | Live per-second monitoring |
| | `cpu` `memory` `disk` `network` | Per-resource metrics |
| System | `processes` | Top processes by CPU |
| | `services` | Service states |
| | `logs` | Stored logs first, then system log tail |
| | `health` | Sentinel self-health (exit code) |
| Incidents | `incidents` | List incidents |
| | `diagnose` | Probable cause, evidence, confidence |
| | `timeline` | Incident event timeline |
| | `report` | txt / markdown / json report |
| | `analytics` | Historical analytics |
| Tools | `simulate` | Safe scenario simulation |
| | `demo` | End-to-end demonstration |
| System | `config` | View configuration |
| | `retention` | Data retention settings |

**Exit codes:** `0` healthy · `1` warning · `2` critical — safe to wire into monitoring/CI hooks.

### Configuration

Defaults live in `config/default.yaml`; user overrides go to `~/.config/cloudops-sentinel/config.yaml`. Data and logs are stored under `~/.local/share/cloudops-sentinel/` (override with `SENTINEL_DB`). No secrets in code — environment variables only.

## Testing

```bash
pytest            # unit + integration + simulation tests (metric → detection → incident)
ruff check .      # lint
```

## Roadmap

- **V1 (current)** — stable local CLI: collect → detect → correlate → incident → diagnose → recover → report, with simulator and demo.
- **V1.1** — optional AI diagnosis adapter.
- **V1.2** — Docker packaging.
- **V2** — Web UI (same data layer, new presentation).
- **V3** — multi-cloud collection.
- **V4** — OpenTelemetry support.