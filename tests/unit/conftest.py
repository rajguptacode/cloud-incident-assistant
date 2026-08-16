"""Shared fixtures for Part 3 storage tests."""

from __future__ import annotations

import pytest
import sqlalchemy

from cloudops_sentinel.storage.database import Database


@pytest.fixture
def db(tmp_path) -> Database:
    database = Database(tmp_path / "sentinel.db")

    @sqlalchemy.event.listens_for(database.engine, "connect")
    def _fast_test_db(dbapi_conn, _record) -> None:
        # ponytail: throwaway test DBs don't need fsync durability; prod DB untouched.
        # Slow-HDD fsync made each create_all ~2.6s.
        dbapi_conn.execute("PRAGMA synchronous=OFF")

    database.create_tables()
    return database