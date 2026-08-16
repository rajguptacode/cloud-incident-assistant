from datetime import UTC, datetime

import pytest

from cloudops_sentinel.storage.database import (
    DEFAULT_DB,
    Base,
    Database,
    HostRow,
    StorageError,
    as_utc,
    utc_now,
)


def test_default_db_path_under_xdg():
    assert "cloudops-sentinel" in str(DEFAULT_DB)
    assert DEFAULT_DB.suffix == ".db"


def test_create_tables_creates_all_contract_tables(db):
    tables = set(Base.metadata.tables)
    for name in (
        "hosts",
        "metrics",
        "logs",
        "events",
        "services",
        "incidents",
        "incident_events",
        "rules",
        "reports",
    ):
        assert name in tables, f"missing table {name}"


def test_session_commits(db):
    with db.session() as session:
        session.add(HostRow(hostname="web-01"))
    with db.session() as session:
        assert session.get(HostRow, 1).hostname == "web-01"


def test_session_rolls_back_on_error_and_raises_storage_error(db):
    with db.session() as session:
        session.add(HostRow(hostname="web-01"))
    with pytest.raises(StorageError), db.session() as session:
        session.add(HostRow(hostname="web-01"))  # duplicate unique hostname


def test_is_healthy(db):
    assert db.is_healthy() is True


def test_is_healthy_false_on_broken_db(tmp_path):
    broken = Database(tmp_path / "not-a-dir")
    broken.path.mkdir()
    assert broken.is_healthy() is False


def test_as_utc_normalizes_naive_and_aware():
    naive = datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC).replace(tzinfo=None)
    aware = datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC)
    assert as_utc(naive) == aware
    assert as_utc(aware) == aware
    assert as_utc(None) is None


def test_utc_now_is_aware():
    assert utc_now().tzinfo == UTC