from datetime import UTC, datetime, timedelta

import pytest

from cloudops_sentinel.models.incident import Incident, IncidentEvent, IncidentStatus
from cloudops_sentinel.storage.database import Database, StorageError
from cloudops_sentinel.storage.repositories.incidents import IncidentsRepository


def _at(minutes_ago: int) -> datetime:
    return datetime.now(UTC) - timedelta(minutes=minutes_ago)


@pytest.fixture
def session(db: Database):
    with db.session() as s:
        yield s


def test_incident_create_assigns_sequential_ids(session):
    repo = IncidentsRepository(session)
    first = repo.create(Incident(severity="HIGH", status=IncidentStatus.DETECTED))
    second = repo.create(Incident(severity="LOW", status=IncidentStatus.TRIAGED))
    assert first.id == "INC-000001"
    assert second.id == "INC-000002"


def test_incident_respects_explicit_id(session):
    repo = IncidentsRepository(session)
    incident = repo.create(Incident(id="INC-000100", severity="MEDIUM"))
    assert incident.id == "INC-000100"
    assert repo.create(Incident()).id == "INC-000101"


def test_incident_get_update_list(session):
    repo = IncidentsRepository(session)
    incident = repo.create(
        Incident(severity="HIGH", title="CPU anomaly", symptoms=["cpu 95%"], evidence=["cpu>90"])
    )
    stored = repo.get(incident.id)
    assert stored is not None
    assert stored.symptoms == ["cpu 95%"]
    assert stored.severity == "HIGH"
    assert stored.title == "CPU anomaly"

    incident.status = IncidentStatus.RESOLVED
    incident.confidence = 82.0
    incident.probable_cause = "python-worker"
    repo.update(incident)
    updated = repo.get(incident.id)
    assert updated.status == IncidentStatus.RESOLVED
    assert updated.confidence == 82.0
    assert updated.probable_cause == "python-worker"

    assert len(repo.list()) == 1
    assert len(repo.list(status="resolved")) == 1
    assert len(repo.list(status="open")) == 0


def test_incident_get_missing_returns_none(session):
    assert IncidentsRepository(session).get("INC-999999") is None


def test_incident_update_missing_raises(session):
    repo = IncidentsRepository(session)
    with pytest.raises(StorageError):
        repo.update(Incident(id="INC-999999"))


def test_incident_timeline_events_in_order(session):
    repo = IncidentsRepository(session)
    incident = repo.create(Incident(severity="HIGH"))
    repo.add_event(IncidentEvent(incident_id=incident.id, type="cpu-anomaly", timestamp=_at(9)))
    repo.add_event(IncidentEvent(incident_id=incident.id, type="incident-created", timestamp=_at(8)))
    repo.add_event(IncidentEvent(incident_id=incident.id, type="recovered", timestamp=_at(1)))

    timeline = repo.events(incident.id)
    assert [e.type for e in timeline] == ["cpu-anomaly", "incident-created", "recovered"]
    assert timeline[0].timestamp.tzinfo == UTC


def test_incident_timeline_empty_for_unknown(session):
    assert IncidentsRepository(session).events("INC-000000") == []