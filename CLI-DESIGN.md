# CloudOps Sentinel — CLI UI, Color & Animation Design Specification

## 1. Purpose

CloudOps Sentinel is CLI-first, but the terminal experience should feel like a polished modern developer/SRE product rather than a plain text utility.

The visual system must be:

- professional
- readable
- information-dense without being noisy
- useful over SSH
- accessible in light/dark terminal themes
- fast and low-overhead
- consistent across every command

The CLI should feel like a terminal dashboard, not a web UI squeezed into a terminal.

## 2. Visual Identity

### Product personality

Technical + Premium + Calm + Operational

### Avoid

- excessive emojis
- rainbow colors
- constant flashing
- giant ASCII art
- unnecessary animations
- decorative output that hides important information

The visual hierarchy should make the important operational state immediately visible.

## 3. Color System

Use semantic colors instead of arbitrary colors.

### Primary palette

| Token | Purpose | Suggested color |
|-------|---------|-----------------|
| primary | headings, selected UI | Cyan |
| secondary | metadata, secondary labels | Blue |
| success | healthy/recovered | Green |
| warning | warning/degraded | Yellow |
| danger | high/critical/error | Red |
| critical | urgent incident | Bright Red |
| muted | timestamps, hints | Dim/Gray |
| info | informational events | Cyan |
| accent | important interactive values | Magenta/Purple |
| text | normal content | Terminal default |

These are semantic tokens. The implementation should allow the actual RGB/ANSI values to be changed from one central theme.

## 4. Do Not Hard-Code Colors Everywhere

Create one theme module:

```
src/cloudops_sentinel/ui/theme.py
```

Example conceptual tokens:

```
PRIMARY
SECONDARY
SUCCESS
WARNING
DANGER
CRITICAL
MUTED
INFO
ACCENT
```

All CLI rendering should use these tokens.

This makes future themes possible without rewriting commands.

## 5. Theme Support

Future command:

```
sentinel config theme
```

Possible themes:

- dark
- light
- mono
- high-contrast

Default: **dark**

The CLI must also support:

```
sentinel status --no-color
```

and detect terminals that do not support ANSI colors.

Environment override:

```
NO_COLOR=1 sentinel status
```

## 6. Status Visualization

| State | Icon | Color |
|-------|------|-------|
| Healthy | `● HEALTHY` | Green |
| Warning | `▲ WARNING` | Yellow |
| Degraded | `◆ DEGRADED` | Yellow/orange |
| High | `● HIGH` | Red |
| Critical | `◆ CRITICAL` | Bright red |
| Unknown | `? UNKNOWN` | Muted gray |

Icons should supplement color, never replace it.

## 7. Main CLI Header

```
╭──────────────────────────────────────────────────────╮
│  CLOUDOPS SENTINEL                                   │
│  Infrastructure Monitoring & Incident Analysis      │
╰──────────────────────────────────────────────────────╯
```

- Keep the header compact.
- Do not display a giant banner every time.
- For commands such as `sentinel monitor`, the header can be shown once and then remain persistent.

## 8. Status Command UI

Command:

```
sentinel status
```

Design:

```
╭─ CloudOps Sentinel ─────────────────────────────────╮
│ Host       ubuntu-pc                                │
│ Uptime     3d 04h                                   │
│ Health     ● HEALTHY   92/100                      │
╰─────────────────────────────────────────────────────╯

SYSTEM

CPU       42%    ████████░░░░░░░░
Memory    61%    ████████████░░░░░
Disk      73%    ██████████████░░░
Network   ● NORMAL

SERVICES

  ● nginx       RUNNING
  ● ssh         RUNNING
  ● docker      RUNNING

INCIDENTS

  ● Critical    0
  ▲ Warning     1
```

The layout should adapt to terminal width.

## 9. Progress Bars

Progress bars are useful for:

- CPU
- memory
- disk
- network utilization
- health scores

Example:

```
CPU      42%  ████████░░░░░░░░
Memory   61%  ████████████░░░░░
Disk     73%  ██████████████░░░
```

Color should follow state:

- normal → success/primary
- warning → warning
- critical → danger

Do not use gradients.

## 10. Sparklines

For historical mini-trends:

```
CPU      42%   ▁▂▃▄▅▆▅▄▃▂
Memory   61%   ▃▃▄▅▅▆▆▇▇█
```

Use sparklines for quick context.

Do not replace detailed charts with sparklines when the user requests history.

## 11. Live Monitor

Command:

```
sentinel monitor
```

The screen should update in place rather than printing unlimited lines.

Example:

```
╭─ LIVE MONITOR ────────────────────────────────╮
│ Updated 14:32:08                               │
╰───────────────────────────────────────────────╯

CPU       67%   █████████████░░░░░
Memory    61%   ████████████░░░░░
Disk      73%   ██████████████░░░
Network   2.4 MB/s ↓   0.8 MB/s ↑

SERVICES
● nginx       healthy
● ssh         healthy
● docker      healthy

INCIDENTS
▲ INC-00021   HIGH   CPU anomaly
```

Refresh interval:

```
sentinel monitor --interval 2
```

## 12. Live Animation Rules

Animations should communicate state changes.

**Allowed:**

- spinner while loading
- live metric updates
- progress indicators
- subtle status transitions
- pulse for an active critical incident

**Avoid:**

- constant flashing
- rapidly changing colors
- full-screen transitions
- long intro animations
- animations that slow commands

## 13. Spinner

For short operations:

```
⠋ Collecting system telemetry
```

Then:

```
✓ Telemetry collected
```

Spinner animation should be subtle.

Recommended cycle:

```
⠋ ⠙ ⠹ ⠸ ⠼ ⠴ ⠦ ⠧ ⠇ ⠏
```

If Unicode is unavailable, use:

```
| / - \
```

## 14. Progress Animation

For longer tasks:

```
Analyzing incident...

████████████████░░░░  82%
```

For unknown duration:

```
⠹ Analyzing incident...
```

Never fake progress percentages when actual progress is unknown.

## 15. Incident Detection Animation

When a new incident is detected:

```
⚠ Detecting anomaly...
```

Then:

```
▲ ANOMALY DETECTED
```

Then:

```
╭─ INCIDENT CREATED ───────────────────────────╮
│ INC-000021                                   │
│ Severity   HIGH                              │
│ Type       CPU anomaly                       │
╰──────────────────────────────────────────────╯
```

The animation should happen once.

Do not continuously flash the terminal.

## 16. Critical Incident Presentation

Critical incidents deserve strong but controlled emphasis.

```
╭─ CRITICAL INCIDENT ──────────────────────────╮
│ ◆ INC-000042                                 │
│                                               │
│ Service: nginx                                │
│ Status:   DOWN                                │
│ Impact:   HTTP unavailable                    │
│                                               │
│ Probable cause: upstream failure              │
│ Confidence:     91%                            │
╰───────────────────────────────────────────────╯
```

- Use bright red only for the important elements.
- Do not color the entire screen red.

## 17. Incident Timeline UI

```
INC-000042  HIGH

14:29:10   ● Process started
14:30:12   ▲ CPU anomaly detected
14:31:04   ▲ HTTP latency increased
14:31:20   ◆ Error spike detected
14:32:01   ● Incident created
14:35:20   ● Metrics normalized
14:37:42   ✓ Incident resolved
```

Colors should correspond to event severity/type.

## 18. Tables

Tables should be compact and aligned.

Example:

```
┏━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━━┓
┃ ID   ┃ SEVERITY     ┃ STATUS   ┃ DURATION   ┃
┡━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━━┩
│ 021  │ HIGH         │ ACTIVE   │ 08m        │
│ 020  │ MEDIUM       │ RESOLVED │ 04m        │
│ 019  │ LOW          │ CLOSED   │ 02m        │
└──────┴──────────────┴──────────┴────────────┘
```

- Use color for severity/status.
- Do not color every cell.

## 19. Interactive Selection

Future commands may use keyboard navigation:

```
Select incident:

❯ INC-000021  HIGH
  INC-000020  MEDIUM
  INC-000019  LOW
```

Keys:

```
↑ / ↓   navigate
Enter   select
Esc     cancel
```

Interactive features must always have a non-interactive alternative.

## 20. CLI Help UI

Command:

```
sentinel --help
```

Should be grouped:

```
CloudOps Sentinel

MONITORING
  status       Show system health
  monitor      Live monitoring
  cpu          CPU metrics
  memory       Memory metrics
  disk         Disk metrics
  network      Network health

INCIDENTS
  incidents    List incidents
  diagnose     Analyze an incident
  timeline     Show incident timeline
  report       Generate report

SYSTEM
  processes    Show processes
  services     Show services
  logs         Inspect logs

TOOLS
  simulate     Run safe incident simulation
  demo         Run complete demo
  config       Manage configuration
```

## 21. Command Success UI

Don't print unnecessary text.

**Bad:**

```
The command has successfully completed successfully.
```

**Good:**

```
✓ Configuration saved.
```

## 22. Error UI

Errors should be actionable.

**Bad:**

```
Error: database error
```

**Good:**

```
✗ Unable to open telemetry database.

Reason:
Permission denied.

Try:
  sentinel health
  Check permissions for ~/.local/share/cloudops-sentinel/

Error code:
STORAGE_PERMISSION_DENIED
```

## 23. Warning UI

```
▲ WARNING

Disk usage is above 80%.

Current: 84%
Threshold: 80%

Run:
  sentinel disk --forecast
```

Warnings should tell the user what they can do next.

## 24. AI Output UI

AI output should look different from raw telemetry.

```
╭─ AI ANALYSIS ─────────────────────────────────╮
│                                               │
│ Summary                                       │
│ The service experienced elevated latency      │
│ during a CPU utilization spike.                │
│                                               │
│ Probable cause                                │
│ python-worker CPU consumption                 │
│                                               │
│ Confidence                                    │
│ 82%                                            │
│                                               │
│ Recommended investigation                     │
│ 1. Inspect python-worker logs                 │
│ 2. Check recent process changes               │
│ 3. Compare CPU trend with deployment events   │
╰───────────────────────────────────────────────╯
```

Clearly label AI-generated content.

## 25. Terminal Width Responsiveness

The CLI must work at:

- 80 columns
- 100 columns
- 120+ columns

At narrow width:

- hide secondary columns
- wrap descriptions
- simplify tables

At wide width:

- show additional metadata
- show more timeline context

Never create horizontal overflow if avoidable.

## 26. Accessibility

Color must never be the only indicator.

Instead of:

```
red = critical
```

use:

```
◆ CRITICAL
```

plus red.

Support:

```
sentinel status --no-color
```

and:

```
NO_COLOR=1 sentinel status
```

High-contrast theme should avoid subtle color differences.

## 27. Unicode Fallback

Preferred:

```
● ▲ ◆ ✓ ✗ █ ░
```

Fallback ASCII:

```
[OK]
[WARN]
[CRITICAL]
[PASS]
[FAIL]
####....
```

Detect terminal capabilities.

## 28. Animation Accessibility

Support:

```
sentinel config animations off
```

Then:

```
Collecting telemetry...
```

instead of:

```
⠋ Collecting telemetry
```

Also support environment configuration if desired.

Default:

- animations ON for interactive terminal
- animations OFF for redirected/non-interactive output

## 29. Non-Interactive / CI Mode

When output is redirected:

```
sentinel status > status.txt
```

The CLI should automatically disable:

- colors
- spinners
- live refresh
- interactive prompts

Output becomes stable plain text.

Optional:

```
sentinel status --json
```

for automation.

## 30. Notification Style

When a new incident appears in live monitor:

```
14:32:01  ◆ NEW INCIDENT
          INC-000021
          HIGH — CPU anomaly
```

Keep notifications compact.

## 31. Startup Animation

Avoid a long startup animation.

Optional first-run:

```
CloudOps Sentinel
Initializing...
✓ Configuration
✓ Database
✓ Collectors
✓ Detection engine

Ready.
```

Only use this during:

- `sentinel demo`
- or explicit initialization

Normal commands should start immediately.

## 32. Demo Mode Visual Experience

`sentinel demo` can be the most visually polished command.

Sequence:

```
CloudOps Sentinel Demo

[1] Initializing
✓

[2] Normal system
✓

[3] Simulating CPU anomaly
████████████████████ 100%

[4] Detection
▲ Anomaly detected

[5] Correlation
✓ Metrics correlated
✓ Process evidence found
✓ Timeline generated

[6] Incident
◆ HIGH — INC-000001

[7] Recovery
✓ System returned to baseline

Demo complete.
```

This becomes the main portfolio/GitHub demonstration.

## 33. UI Component Library

Create reusable components:

```
src/cloudops_sentinel/ui/
├── __init__.py
├── theme.py
├── console.py
├── panels.py
├── tables.py
├── progress.py
├── spinners.py
├── bars.py
├── sparklines.py
├── timeline.py
├── status.py
├── alerts.py
├── prompts.py
├── icons.py
└── formatting.py
```

Commands should use these components instead of implementing styling individually.

## 34. Recommended Libraries

**Rich** — Primary terminal rendering framework:

- colors
- tables
- panels
- progress
- live updates
- syntax highlighting
- terminal layout

**Typer** — CLI command structure and help.

**psutil** — System metrics.

Keep UI dependencies isolated from monitoring logic.

## 35. Architecture Rule

Never do this:

```
collector
   ↓
Rich output
```

Instead:

```
Collector
   ↓
Domain model
   ↓
Application service
   ↓
CLI renderer
   ↓
Rich UI
```

This is important because later the same data can be used by:

- CLI
- Web UI
- API
- JSON

without rewriting monitoring logic.

## 36. Example Final CLI Experience

```
╭──────────────────────────────────────────────────────────╮
│ CLOUDOPS SENTINEL                              v0.1.0     │
│ Intelligent Infrastructure Monitoring                    │
╰──────────────────────────────────────────────────────────╯

HOST
ubuntu-pc                         ● HEALTHY
Uptime                            3d 04h

RESOURCES

CPU       42%    ████████░░░░░░░░   ▁▂▃▄▃▂
Memory    61%    ████████████░░░░   ▃▄▅▅▆▆
Disk      73%    ██████████████░░   ▆▆▇▇▇█
Network   NORMAL

SERVICES

● nginx          RUNNING
● ssh            RUNNING
● docker         RUNNING

INCIDENTS

◆ 0 Critical
▲ 1 Warning

────────────────────────────────────────────────────────────
Last update: 14:32:08     Monitoring interval: 2s
Press Ctrl+C to exit
```

The goal is professional terminal UX, not visual overload.

## 37. Implementation Priority

| Version | Scope |
|---------|-------|
| **V0.1** | theme system, Rich console, status indicators, panels, tables, basic progress/spinner, `--no-color` |
| **V0.2** | live monitor, progress bars, sparklines, responsive layouts |
| **V0.3** | incident UI, severity visualization, timeline, alert notifications |
| **V0.4** | interactive selection, demo mode, advanced terminal layouts |
| **V0.5** | accessibility, high contrast, ASCII fallback, non-interactive/CI mode |
| **V1** | Complete polished CLI design across every command |

## 38. UX Acceptance Criteria

The CLI is considered visually ready when:

- every command follows the same theme
- status meaning is clear without relying solely on color
- live monitor updates in place
- critical incidents are noticeable but not distracting
- no unnecessary flashing occurs
- output works at 80-column terminals
- `--no-color` works
- redirected output contains no animation
- JSON output is clean
- animations can be disabled
- all visual components are reusable
- monitoring/business logic contains no terminal-specific rendering code

## 39. Final Design Direction

CloudOps Sentinel should feel like:

> A professional SRE/DevOps terminal tool

not:

> a colorful beginner Python CLI.

Visual hierarchy:

```
CRITICAL INCIDENT
        ↓
IMPORTANT METRICS
        ↓
SYSTEM STATE
        ↓
DETAILS
        ↓
DEBUG INFORMATION
```

The terminal should be visually impressive, but the most important information must always win.