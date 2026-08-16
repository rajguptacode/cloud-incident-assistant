---
name: sentinel-storage
description: Use when building or fixing CloudOps Sentinel storage layer — SQLite schema, repositories, retention, database reliability. Trigger words: sqlite, database, storage, retention, table, schema, repository, sqlalchemy, purge, migration.
---

# Sentinel Storage

## Database

- V1: SQLite via SQLAlchemy abstraction. Alembic only if/when migrations are needed.
- Future: PostgreSQL for multi-host/cloud.

## Tables (V1)

`hosts`, `metrics`, `logs`, `events`, `services`, `incidents`, `incident_events`, `rules`, `reports`.

## Repository pattern

Persistence only — domain logic never touches SQL. Repositories:

- `repositories/metrics.py`
- `repositories/logs.py`
- `repositories/events.py`
- `repositories/incidents.py`

## Data retention

- Default: 30 days, configurable (`storage.retention_days`).
- CLI: `sentinel retention set 60`.
- Old telemetry auto-purged on schedule — bounded growth, bounded log processing.
- Never store unlimited data on the local machine.

## Reliability

- Storage failures must fail gracefully: the monitored system is never destabilized by database problems.
- On restart: load config → recover database → resume monitoring.
- Sentinel's own health reports database status (observability).

## Rules

- Normalized models (Pydantic) cross the boundary into repositories; repositories return models back.
- Timestamps UTC everywhere.
- Incidents: sequential `INC-000001` IDs, plus incident_events rows for the timeline.