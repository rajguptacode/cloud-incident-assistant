# CloudOps Sentinel — Tech Stack & File Structure

## 1. Recommended stack

### Runtime

- Python 3.12+ (use a supported stable Python release available on the development machine)
- Linux/Ubuntu for V1 development

### CLI

- **Typer** for command structure
- **Rich** for terminal tables, panels, progress/live output and readable formatting

### System monitoring

- **psutil** for CPU, memory, disk, process and network statistics
- Linux-native interfaces/commands only where psutil does not provide the needed information

### Backend/core

- Pure Python service/domain modules
- **Pydantic** for typed data models and validation
- **PyYAML** for YAML configuration

### Storage

- **SQLite** for V1
- **SQLAlchemy** as the database abstraction layer
- **Alembic** if/when schema migrations become necessary

### Logs

- Python `logging` for Sentinel's own logs
- Standard-library parsing plus structured parsing for JSON logs
- Linux journal/system logs through a controlled adapter

### API/future UI

- **FastAPI** in a later phase
- WebSocket/SSE later for live dashboard updates

### AI

- Provider-agnostic AI adapter
- AI receives structured, sanitized incident context
- AI is optional and disabled by default in the core offline system

### Testing

- pytest
- pytest-asyncio if asynchronous components are introduced
- coverage for test coverage measurement

### Quality

- **Ruff** for linting/formatting
- mypy or another type checker as the codebase matures
- pre-commit for local quality checks

### Packaging

- `pyproject.toml`
- uv or another modern Python environment/package workflow
- Docker later, not required for V1

## 2. Architecture

```
CLI
 |
 v
Application Services
 |
 +--> Collectors ----> Normalization ----> Storage
 |
 +--> Detection Engine
 |        |
 |        v
 |   Correlation Engine
 |        |
 |        v
 |   Incident Engine
 |        |
 |        +--> RCA / Evidence
 |        +--> Reports
 |
 +--> Config
 +--> Health
 +--> Simulator
 +--> Optional AI Adapter
```

Future:

- FastAPI/Web UI
- Multi-host backend
- Cloud adapters
- OpenTelemetry integration

## 3. Repository structure

```
cloudops-sentinel/
├── pyproject.toml
├── README.md
├── LICENSE
├── .gitignore
├── .env.example
├── Makefile
│
├── src/
│   └── cloudops_sentinel/
│       ├── __init__.py
│       ├── __main__.py
│       │
│       ├── cli/
│       │   ├── __init__.py
│       │   ├── app.py
│       │   ├── status.py
│       │   ├── monitor.py
│       │   ├── metrics.py
│       │   ├── processes.py
│       │   ├── services.py
│       │   ├── logs.py
│       │   ├── incidents.py
│       │   ├── reports.py
│       │   ├── analytics.py
│       │   ├── config.py
│       │   ├── simulator.py
│       │   └── output.py
│       │
│       ├── core/
│       │   ├── config.py
│       │   ├── constants.py
│       │   ├── exceptions.py
│       │   ├── clock.py
│       │   └── types.py
│       │
│       ├── models/
│       │   ├── host.py
│       │   ├── metric.py
│       │   ├── log.py
│       │   ├── event.py
│       │   ├── service.py
│       │   ├── incident.py
│       │   ├── rule.py
│       │   └── report.py
│       │
│       ├── collectors/
│       │   ├── cpu.py
│       │   ├── memory.py
│       │   ├── disk.py
│       │   ├── network.py
│       │   ├── processes.py
│       │   ├── services.py
│       │   └── host.py
│       │
│       ├── logs/
│       │   ├── reader.py
│       │   ├── parser.py
│       │   ├── normalizer.py
│       │   └── patterns.py
│       │
│       ├── detection/
│       │   ├── engine.py
│       │   ├── thresholds.py
│       │   ├── duration.py
│       │   ├── rate_of_change.py
│       │   ├── baseline.py
│       │   └── scoring.py
│       │
│       ├── correlation/
│       │   ├── engine.py
│       │   ├── timeline.py
│       │   └── windows.py
│       │
│       ├── incidents/
│       │   ├── manager.py
│       │   ├── lifecycle.py
│       │   ├── deduplication.py
│       │   ├── severity.py
│       │   ├── evidence.py
│       │   └── recovery.py
│       │
│       ├── diagnosis/
│       │   ├── rca.py
│       │   ├── hypotheses.py
│       │   └── confidence.py
│       │
│       ├── storage/
│       │   ├── database.py
│       │   ├── repositories/
│       │   │   ├── metrics.py
│       │   │   ├── logs.py
│       │   │   ├── events.py
│       │   │   └── incidents.py
│       │   └── migrations/
│       │
│       ├── reports/
│       │   ├── generator.py
│       │   ├── markdown.py
│       │   ├── text.py
│       │   └── json.py
│       │
│       ├── simulator/
│       │   ├── engine.py
│       │   ├── scenarios/
│       │   │   ├── cpu_spike.py
│       │   │   ├── memory_pressure.py
│       │   │   ├── disk_pressure.py
│       │   │   ├── service_down.py
│       │   │   ├── network_latency.py
│       │   │   └── http_errors.py
│       │   └── demo.py
│       │
│       ├── health/
│       │   ├── checks.py
│       │   └── self_monitor.py
│       │
│       ├── ai/
│       │   ├── interface.py
│       │   ├── context.py
│       │   ├── prompts.py
│       │   └── providers/
│       │
│       └── integrations/
│           ├── linux/
│           ├── docker/
│           ├── http/
│           └── cloud/
│
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── cli/
│   ├── detection/
│   ├── incidents/
│   └── simulator/
│
├── config/
│   ├── default.yaml
│   └── examples/
│
├── docs/
│   ├── architecture.md
│   ├── cli-reference.md
│   ├── configuration.md
│   ├── detection-engine.md
│   ├── incident-lifecycle.md
│   ├── simulator.md
│   ├── security.md
│   └── development.md
│
├── scripts/
│   ├── dev.sh
│   └── demo.sh
│
└── .github/
    └── workflows/
        ├── tests.yml
        └── quality.yml
```

## 4. Module responsibilities

- **cli/** — Only CLI concerns: commands, argument parsing and terminal presentation. Business logic should not live here.
- **collectors/** — Read system state and return normalized data. Collectors should be small, testable and read-only.
- **detection/** — Convert observations into detection events using configurable rules.
- **correlation/** — Group related observations/events within time windows.
- **incidents/** — Create, update, deduplicate, score and close incidents.
- **diagnosis/** — Generate evidence-backed hypotheses and confidence scores.
- **storage/** — Persistence only. Keep database details away from domain logic.
- **simulator/** — Safe, repeatable synthetic scenarios for development and demos.
- **ai/** — Provider-neutral interface. The rest of the application should work when AI is unavailable.
- **integrations/** — Adapters for Linux, Docker, HTTP and future cloud providers.

## 5. Data flow

```
Linux
  ↓
Collectors
  ↓
Normalized Models
  ↓
SQLite
  ↓
Detection Engine
  ↓
Detection Events
  ↓
Correlation Engine
  ↓
Incident Manager
  ↓
Evidence + RCA
  ↓
CLI / Reports
  ↓
Optional AI explanation
```

## 6. Example command map

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
sentinel incidents show INC-000001
sentinel diagnose INC-000001
sentinel timeline INC-000001
sentinel report INC-000001
sentinel analytics
sentinel config
sentinel maintenance start
sentinel maintenance stop
sentinel simulate cpu-spike
sentinel demo
sentinel health
```

## 7. Dependency philosophy

- Keep V1 dependency count low.
- Prefer Python standard library for simple tasks.
- Add third-party libraries only where they provide clear value.
- Keep optional AI/cloud dependencies out of the core installation where practical.

## 8. Future expansion

The repository intentionally reserves integration boundaries for:

- Docker monitoring
- HTTP endpoint checks
- AWS/GCP/Azure adapters
- OpenTelemetry
- FastAPI/Web UI
- multi-host monitoring
- PostgreSQL