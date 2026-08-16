---
name: sentinel-cli
description: Use when building or editing CloudOps Sentinel CLI commands, terminal UI, colors, themes, animations. Trigger words: cli, typer, rich, command, ui, theme, color, panel, table, spinner, progress, sparkline, monitor, help output.
---

# Sentinel CLI & UI

## Stack

- Typer for command structure and help
- Rich for tables, panels, progress, live updates
- psutil for metrics
- All rendering lives in `src/cloudops_sentinel/ui/` — commands never implement styling themselves

## Command map (implement in this order)

```
status monitor cpu memory disk network processes services logs
incidents incidents show INC-xxxx diagnose timeline report
analytics config maintenance start|stop simulate demo health
```

## Architecture rule — NEVER bypass

```
Collector → Domain model → Application service → CLI renderer → Rich UI
```

Collectors/domain must never render terminal output. Same data must later feed CLI, Web UI, API, JSON without rewriting logic.

## Semantic colors (theme.py tokens only)

| Token | Color |
|-------|-------|
| PRIMARY | Cyan |
| SECONDARY | Blue |
| SUCCESS | Green |
| WARNING | Yellow |
| DANGER | Red |
| CRITICAL | Bright Red |
| MUTED | Dim/Gray |
| INFO | Cyan |
| ACCENT | Magenta/Purple |

Never hard-code ANSI codes in commands.

## Status icons

- `● HEALTHY` green, `▲ WARNING` yellow, `◆ DEGRADED` yellow/orange
- `● HIGH` red, `◆ CRITICAL` bright red, `? UNKNOWN` muted
- Icons supplement color, never replace it

## UI rules

- Compact header, no giant banners. `monitor` header shows once, stays persistent.
- Progress bars follow state color (normal/warning/critical). No gradients.
- Sparklines (`▁▂▃▄▅▆▇█`) for mini-trends only; full history = real charts.
- Live monitor updates in place (Rich Live), never prints unlimited lines.
- Success: `✓ Configuration saved.` — no filler prose.
- Errors: message + reason + what to try + error code (e.g. `STORAGE_PERMISSION_DENIED`).
- Warnings must tell the user the next command to run.
- AI output rendered in a labeled `AI ANALYSIS` panel, distinct from telemetry.
- Tables: color severity/status cells only, not every cell.

## Responsiveness & accessibility

- Works at 80 / 100 / 120+ columns. Narrow = hide secondary columns, wrap, simplify.
- `--no-color` flag and `NO_COLOR=1` env var support.
- Unicode icons (`● ▲ ◆ ✓ ✗ █ ░`) with ASCII fallback (`[OK] [WARN] [CRITICAL] [PASS] [FAIL] ####....`).
- Animations: `sentinel config animations off`; ON for interactive terminal, OFF for redirected/non-interactive output. Never fake progress percentages.
- `--json` flag for machine-readable output.
- Exit codes: `0` healthy, `1` warning, `2` critical.

## Detection/incident animation sequence

`⚠ Detecting anomaly...` → `▲ ANOMALY DETECTED` → incident panel. Happens once, no flashing.