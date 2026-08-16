"""Logs repository — persistence only, no domain logic."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from cloudops_sentinel.models.log import LogEntry
from cloudops_sentinel.storage.database import LogRow, as_utc, utc_now


class LogsRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def save(self, log: LogEntry) -> None:
        self.session.add(
            LogRow(
                timestamp=as_utc(log.timestamp) or utc_now(),
                severity=log.severity.value,
                service=log.service,
                host=log.host,
                message=log.message,
                source=log.source,
                event_id=log.event_id,
            )
        )

    def query(
        self,
        *,
        level: str | None = None,
        service: str | None = None,
        host: str | None = None,
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> list[LogEntry]:
        stmt = select(LogRow)
        if level:
            stmt = stmt.where(LogRow.severity == level.upper())
        if service:
            stmt = stmt.where(LogRow.service == service)
        if host:
            stmt = stmt.where(LogRow.host == host)
        if since:
            stmt = stmt.where(LogRow.timestamp >= as_utc(since))
        if until:
            stmt = stmt.where(LogRow.timestamp <= as_utc(until))
        stmt = stmt.order_by(LogRow.timestamp)
        return [self._to_model(row) for row in self.session.scalars(stmt)]

    @staticmethod
    def _to_model(row: LogRow) -> LogEntry:
        return LogEntry.model_validate(
            {
                "timestamp": as_utc(row.timestamp),
                "severity": row.severity,
                "service": row.service,
                "host": row.host,
                "message": row.message,
                "source": row.source,
                "event_id": row.event_id,
            }
        )