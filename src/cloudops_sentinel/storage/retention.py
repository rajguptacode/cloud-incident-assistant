"""Data retention — bounded growth, auto-purge of old telemetry.

Telemetry (metrics, logs, events) older than ``retention_days`` is purged.
Incidents, reports and services are kept — they are small and valuable.
"""

from __future__ import annotations

from datetime import timedelta

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from cloudops_sentinel.storage.database import (
    EventRow,
    LogRow,
    MetricRow,
    SettingRow,
    as_utc,
    utc_now,
)

DEFAULT_RETENTION_DAYS = 30


def get_retention_days(session: Session) -> int:
    value = session.execute(
        select(SettingRow.value).where(SettingRow.key == "retention_days")
    ).scalar()
    return int(value) if value else DEFAULT_RETENTION_DAYS


def set_retention_days(session: Session, days: int) -> None:
    if days < 1:
        raise ValueError("retention days must be >= 1")
    row = session.get(SettingRow, "retention_days")
    if row is None:
        session.add(SettingRow(key="retention_days", value=str(days)))
    else:
        row.value = str(days)


def purge_old(session: Session, retention_days: int | None = None) -> int:
    """Delete telemetry older than the retention window; returns rows deleted."""
    days = retention_days if retention_days is not None else get_retention_days(session)
    cutoff = as_utc(utc_now() - timedelta(days=days))
    deleted = 0
    for table in (MetricRow, LogRow, EventRow):
        result = session.execute(delete(table).where(table.timestamp < cutoff))
        deleted += result.rowcount or 0
    return deleted