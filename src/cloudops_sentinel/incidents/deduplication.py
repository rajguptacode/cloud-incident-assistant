"""Alert deduplication (PRD §23).

Repeated observations update ONE incident instead of flooding. The dedup key
is derived from stored symptoms (each symptom string is ``signal: detail``),
so it survives DB round-trips without extra fields.
"""

from __future__ import annotations

from cloudops_sentinel.models.incident import Incident

from .lifecycle import CLOSED_STATUSES


def symptom_signals(symptoms: list[str]) -> frozenset[str]:
    signals = set()
    for symptom in symptoms:
        name = symptom.split(":", 1)[0].strip()
        if name:
            signals.add(name)
    return frozenset(signals)


def dedup_key(signals: frozenset[str]) -> str:
    return ",".join(sorted(signals))


def active_incidents(incidents: list[Incident]) -> list[Incident]:
    return [i for i in incidents if i.status not in CLOSED_STATUSES]


def find_match(active: list[Incident], signals: frozenset[str]) -> Incident | None:
    """Same signal set as an already-open incident → that incident gets updated."""
    for incident in active:
        if symptom_signals(incident.symptoms) == signals:
            return incident
    return None
