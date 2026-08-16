---
name: sentinel-architecture
description: Use when making architectural decisions for CloudOps Sentinel — layering, security, reliability, performance, testing, build order. Trigger words: architecture, design, security, reliability, performance, testing, layering, roadmap, v0.1, dependency, module.
---

# Sentinel Architecture & Engineering Rules

## Layering (non-negotiable)

```
Collector → Domain model → Application service → CLI renderer → Rich UI
```

- `cli/` — commands, args, presentation only. No business logic.
- `collectors/` — read-only system reads, small, testable.
- `detection/`, `correlation/`, `incidents/`, `diagnosis/` — domain logic, no rendering, no SQL.
- `storage/` — persistence only, repositories.
- `ai/` — provider-neutral; the rest of the app works when AI is unavailable.
- `integrations/` — adapters (linux, docker, http, cloud).

## Build order (follow the roadmap, one version at a time)

V0.1 Foundation (Python project + CLI + config + logging) → V0.2 Monitoring (CPU/RAM/Disk/Network) → V0.3 Linux (processes/services/logs) → V0.4 Storage (SQLite) → V0.5 Detection → V0.6 Incidents → V0.7 Correlation → V0.8 Diagnosis → V0.9 Simulator → V1.0 Stable CLI. Do not build later phases early.

## Security

- No hard-coded secrets — environment variables for credentials (`.env.example`).
- Read-only by default; no automatic destructive actions; no autonomous remediation in V1.
- AI receives sanitized structured context only — never raw machine access, never arbitrary shell execution.
- Input validation everywhere; bounded log processing.

## Reliability

- Monitoring failure must never crash or destabilize the monitored system.
- Sentinel recovers after restart (config → database recovery → resume).
- Core monitoring continues if AI is unavailable.
- Storage failures fail gracefully.
- Sentinel observes itself (`health/checks.py`, `self_monitor.py`) — if the agent dies you must know.

## Performance

- Low CPU/memory overhead; configurable collection interval; async where appropriate.
- Bounded log processing + DB retention. Benchmarks later, no arbitrary hard limits now.

## Dependency philosophy

- Low V1 dependency count: Typer, Rich, psutil, Pydantic, PyYAML, SQLAlchemy (SQLite), pytest, Ruff.
- Stdlib first; add libraries only for clear value.
- AI/cloud deps optional, out of the core install.

## Testing

- Unit: collectors, parsers, severity, scoring, log parser.
- Integration: metric → detection → incident.
- Simulation tests (expected severity per scenario).
- Regression: new features must not break old detection.
- CLI command tests.

## Exit codes & automation

`sentinel health`: 0 healthy / 1 warning / 2 critical. JSON output on every command.