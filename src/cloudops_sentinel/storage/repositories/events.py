"""Events repository — persistence only, no domain logic."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from cloudops_sentinel.models.event import Event
from cloudops_sentinel.storage.database import EventRow, as_utc, utc_now


class EventsRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def save(self, event: Event) -> None:
        self.session.add(
            EventRow(
                type=event.type,
                timestamp=as_utc(event.timestamp) or utc_now(),
                payload=event.payload or {},
            )
        )

    def query(
        self,
        *,
        type: str | None = None,
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> list[Event]:
        stmt = select(EventRow)
        if type:
            stmt = stmt.where(EventRow.type == type)
        if since:
            stmt = stmt.where(EventRow.timestamp >= as_utc(since))
        if until:
            stmt = stmt.where(EventRow.timestamp <= as_utc(until))
        stmt = stmt.order_by(EventRow.timestamp)
        return [self._to_model(row) for row in self.session.scalars(stmt)]

    @staticmethod
    def _to_model(row: EventRow) -> Event:
        return Event.model_validate(
            {"type": row.type, "timestamp": as_utc(row.timestamp), "payload": row.payload or {}}
        )