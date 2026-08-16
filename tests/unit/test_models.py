from __future__ import annotations

from datetime import UTC

from cloudops_sentinel.models.incident import Incident, IncidentStatus, Severity


def test_incident_defaults():
    inc = Incident()
    assert inc.id == ""
    assert inc.severity == Severity.INFO
    assert inc.status == IncidentStatus.DETECTED
    assert inc.occurrences == 1
    assert inc.symptoms == []


def test_incident_custom():
    inc = Incident(id="INC-000001", severity=Severity.HIGH, status=IncidentStatus.RESOLVED, score=75.0)
    assert inc.id == "INC-000001"
    assert inc.severity.value == "HIGH"
    assert inc.score == 75.0


def test_incident_status_flow():
    flow = [
        IncidentStatus.DETECTED,
        IncidentStatus.TRIAGED,
        IncidentStatus.INVESTIGATING,
        IncidentStatus.MITIGATED,
        IncidentStatus.RESOLVED,
        IncidentStatus.CLOSED,
    ]
    assert flow[-1] == IncidentStatus.CLOSED
    assert IncidentStatus.FALSE_POSITIVE.value == "FALSE_POSITIVE"


def test_timestamp_utc():
    from cloudops_sentinel.models.common import utcnow

    now = utcnow()
    assert now.tzinfo == UTC