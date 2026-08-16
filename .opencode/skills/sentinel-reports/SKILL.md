---
name: sentinel-reports
description: Use when building or fixing CloudOps Sentinel report generation — incident reports, analytics, JSON output, exit codes. Trigger words: report, generate, analytics, json, markdown, format, exit code, incidents list.
---

# Sentinel Reports & Output

## Incident reports

`sentinel report INC-xxxx` generates:

- Incident Summary, Impact, Timeline, Metrics, Logs, Probable Cause, Evidence, Resolution, Recommendations.

Formats:

- `--format json`
- `--format markdown`
- `--format txt`
- PDF: later feature.

Renderers: `reports/markdown.py`, `reports/text.py`, `reports/json.py` behind `reports/generator.py`.

## Analytics

`sentinel analytics` shows:

- incident count, severity distribution, most frequent incident type,
- average resolution time, most common error, uptime, resource trends.

## JSON output

- Every CLI command supports `--json` for machine-readable output (future automation/API).
- Example: `sentinel status --json` → `{"cpu": 42, "memory": 61, "disk": 73, "health": 82}`.

## Exit codes (DevOps/CI)

`sentinel health`:

- `0` = healthy
- `1` = warning
- `2` = critical

## Rules

- Reports are built from stored telemetry/incident data — no fabrication.
- Domain data is rendered in CLI layer; report generator produces plain formats independent of terminal styling.
- Recovery detection writes resolution + duration into the report.