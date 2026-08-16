"""Metrics repository — persistence only, no domain logic."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from cloudops_sentinel.models.metric import Metric
from cloudops_sentinel.storage.database import MetricRow, as_utc, utc_now


class MetricsRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def save(self, metric: Metric) -> None:
        self.session.add(
            MetricRow(
                name=metric.name,
                value=metric.value,
                unit=metric.unit,
                host=metric.host,
                timestamp=as_utc(metric.timestamp) or utc_now(),
            )
        )

    def query(
        self,
        *,
        name: str | None = None,
        host: str | None = None,
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> list[Metric]:
        stmt = select(MetricRow)
        if name:
            stmt = stmt.where(MetricRow.name == name)
        if host:
            stmt = stmt.where(MetricRow.host == host)
        if since:
            stmt = stmt.where(MetricRow.timestamp >= as_utc(since))
        if until:
            stmt = stmt.where(MetricRow.timestamp <= as_utc(until))
        stmt = stmt.order_by(MetricRow.timestamp)
        return [self._to_model(row) for row in self.session.scalars(stmt)]

    @staticmethod
    def _to_model(row: MetricRow) -> Metric:
        return Metric.model_validate(
            {
                "name": row.name,
                "value": row.value,
                "unit": row.unit,
                "host": row.host,
                "timestamp": as_utc(row.timestamp),
            }
        )