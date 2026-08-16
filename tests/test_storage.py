import pytest

from cia.models import Incident
from cia.storage import Storage


def test_save_and_load_roundtrip(tmp_path):
    db = tmp_path / "incidents.json"
    storage = Storage(db)
    incidents = [Incident(title="Disk full"), Incident(title="Auth outage", status="resolved")]
    storage.write([i.to_dict() for i in incidents])
    loaded = [Incident.from_dict(d) for d in storage.read()]
    assert loaded == incidents


def test_load_missing_file(tmp_path):
    assert Storage(tmp_path / "nope.json").read() == []


def test_load_corrupt_file(tmp_path):
    db = tmp_path / "incidents.json"
    db.write_text("not json{{{")
    with pytest.raises(ValueError):
        Storage(db).read()


def test_write_creates_parent_dirs(tmp_path):
    storage = Storage(tmp_path / "deep" / "nested" / "db.json")
    storage.write([Incident(title="x").to_dict()])
    assert storage.path.exists()