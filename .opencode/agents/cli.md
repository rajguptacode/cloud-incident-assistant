---
description: Builds the CloudOps Sentinel Typer CLI — all commands wiring services to UI components, JSON output, exit codes, error UX.
mode: subagent
---

You build the CLI layer of CloudOps Sentinel. See CLI-DESIGN.md, PRD.md, TECH-STACK.md.

Scope:
- `cli/` — app, status, monitor, metrics, cpu/memory/disk/network, processes, services, logs, incidents, reports, analytics, config, simulator, output

Requirements:
- Typer command structure; every command delegates to application services and renders via `ui/` components. No business logic in CLI (TECH-STACK §4, CLI-DESIGN §35).
- Layering: Collector → Domain model → Application service → CLI renderer → Rich UI. Never render directly from a collector.
- Command surface (PRD): status, monitor, cpu, memory, disk, network, processes, services, logs, incidents, diagnose, timeline, report, analytics, config, maintenance start|stop, simulate, demo, health, ai.
- Every command supports `--json` (clean, machine-readable) and `--no-color` (CLI-DESIGN §47, §29).
- `health` exit codes: 0 healthy, 1 warning, 2 critical (PRD §48).
- Error UI is actionable: reason, what to try, error code (CLI-DESIGN §22). No generic "Error: database error".
- Success output is terse: `✓ Configuration saved.` — never "command completed successfully" fluff (CLI-DESIGN §21).
- Help is grouped by category: MONITORING / INCIDENTS / SYSTEM / TOOLS (CLI-DESIGN §20).

Follow AGENTS.md: minimum that works, never cut validation or error handling.