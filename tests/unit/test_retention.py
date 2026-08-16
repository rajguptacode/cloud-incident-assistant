from datetime import UTC, datetime, timedelta

import pytest

from cloudops_sentinel.models.event import Event
from cloudops_sentinel.models.log import LogEntry
from cloudops_sentinel.models.metric import Metric
from cloudops_sentinel.storage.database import Database
from cloudops_sentinel.storage.repositories.events import EventsRepository
from cloudops_sentinel.storage.repositories.logs import LogsRepository
from cloudops_sentinel.storage.repositories.metrics import MetricsRepository
from cloudops_sentinel.storage.retention import (
    DEFAULT_RETENTION_DAYS,
    get_retention_days,
    purge_old,
    set_retention_days,
)


def _at(days_ago: int) -> datetime:
    return datetime.now(UTC) - timedelta(days=days_ago)


@pytest.fixture
def session(db: Database):
    with db.session() as s:
        yield s


def _seed(session, days_ago):
    MetricsRepository(session).save(
        Metric(name="cpu", value=10.0, host="web-01", timestamp=_at(days_ago))
    )
    LogsRepository(session).save(
        LogEntry(severity="ERROR", service="nginx", message="x", timestamp=_at(days_ago))
    )
    EventsRepository(session).save(Event(type="deploy", timestamp=_at(days_ago)))


def test_default_retention_days(session):
    assert get_retention_days(session) == DEFAULT_RETENTION_DAYS == 30


def test_set_and_get_retention_days(session):
    set_retention_days(session, 60)
    assert get_retention_days(session) == 60


def test_set_retention_rejects_invalid(session):
    with pytest.raises(ValueError):
        set_retention_days(session, 0)
    with pytest.raises(ValueError):
        set_retention_days(session, -5)


def test_purge_old_removes_only_expired_telemetry(session):
    _seed(session, days_ago=40)
    _seed(session, days_ago=10)

    deleted = purge_old(session, retention_days=30)
    assert deleted == 3
    assert len(MetricsRepository(session).query()) == 1
    assert len(LogsRepository(session).query()) == 1
    assert len(EventsRepository(session).query()) == 1


def test_purge_old_uses_configured_retention(session):
    _seed(session, days_ago=40)
    set_retention_days(session, 10)
    deleted = purge_old(session)
    assert deleted == 3
    assert len(MetricsRepository(session).query()) == 0


def test_purge_old_keeps_recent_when_retention_long(session):
    _seed(session, days_ago=40)
    deleted = purge_old(session, retention_days=90)
    assert deleted == 0
    assert len(MetricsRepository(session).query()) == 1