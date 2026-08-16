import pytest

from cia.models import Incident, STATUSES


def test_create_valid_incident():
    i = Incident(title="DB down")
    assert i.status == "open"
    assert i.id


def test_title_required():
    with pytest.raises(ValueError):
        Incident(title="  ")


def test_invalid_severity():
    with pytest.raises(ValueError):
        Incident(title="x", severity="extreme")


def test_invalid_status():
    with pytest.raises(ValueError):
        Incident(title="x", status="closed")


def test_roundtrip_dict():
    i = Incident(title="API latency", severity="high", service="api-gateway")
    assert Incident.from_dict(i.to_dict()) == i


def test_statuses_defined():
    assert STATUSES == ("open", "investigating", "resolved")