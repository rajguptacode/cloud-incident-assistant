from datetime import UTC, datetime, timedelta

import pytest

from cloudops_sentinel.models.event import Event
from cloudops_sentinel.models.log import LogEntry
from cloudops_sentinel.models.metric import Metric
from cloudops_sentinel.storage.database import Database
from cloudops_sentinel.storage.repositories.events import EventsRepository
from cloudops_sentinel.storage.repositories.logs import LogsRepository
from cloudops_sentinel.storage.repositories.metrics import MetricsRepository


def _at(minutes_ago: int) -> datetime:
    return datetime.now(UTC) - timedelta(minutes=minutes_ago)


@pytest.fixture
def session(db: Database):
    with db.session() as s:
        yield s


def _metric(name, value, host="web-01", minutes_ago=10):
    return Metric(name=name, value=value, host=host, timestamp=_at(minutes_ago))


def test_metric_save_and_query_all(session):
    repo = MetricsRepository(session)
    repo.save(_metric("cpu", 42.0))
    repo.save(_metric("memory", 61.0, host="db-01"))
    rows = repo.query()
    assert len(rows) == 2
    assert rows[0].name == "cpu"


def test_metric_query_by_name_host_and_range(session):
    repo = MetricsRepository(session)
    repo.save(_metric("cpu", 30.0, minutes_ago=30))
    repo.save(_metric("cpu", 80.0, minutes_ago=5))
    repo.save(_metric("cpu", 90.0, host="db-01", minutes_ago=5))
    repo.save(_metric("memory", 50.0, minutes_ago=5))

    assert len(repo.query(name="cpu")) == 3
    assert len(repo.query(host="db-01")) == 1
    assert len(repo.query(name="cpu", since=_at(10), until=_at(0))) == 2
    assert len(repo.query(name="cpu", since=_at(10))) == 2
    assert len(repo.query(name="cpu", until=_at(10))) == 1


def test_log_save_and_query_filters(session):
    repo = LogsRepository(session)
    repo.save(LogEntry(severity="ERROR", service="nginx", message="timeout", timestamp=_at(9)))
    repo.save(LogEntry(severity="WARNING", service="nginx", message="retry", timestamp=_at(5)))
    repo.save(LogEntry(severity="ERROR", service="postgres", message="down", timestamp=_at(1)))

    assert len(repo.query()) == 3
    assert len(repo.query(level="error")) == 2
    assert len(repo.query(service="nginx")) == 2
    assert len(repo.query(level="ERROR", service="postgres")) == 1
    assert len(repo.query(since=_at(6))) == 2


def test_event_save_and_query(session):
    repo = EventsRepository(session)
    repo.save(Event(type="deploy", timestamp=_at(20), payload={"app": "api"}))
    repo.save(Event(type="restart", timestamp=_at(2), payload={"pid": 42}))

    assert len(repo.query()) == 2
    assert len(repo.query(type="deploy")) == 1
    assert len(repo.query(since=_at(10))) == 1
    assert repo.query(type="restart")[0].payload == {"pid": 42}