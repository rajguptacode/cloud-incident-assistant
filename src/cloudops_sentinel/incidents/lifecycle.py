"""Incident lifecycle (PRD §17).

DETECTED → TRIAGED → INVESTIGATING → MITIGATED → RESOLVED → CLOSED
with a FALSE_POSITIVE escape. Transitions are validated; no free-form jumps.
"""

from __future__ import annotations

from cloudops_sentinel.models.incident import Incident, IncidentStatus

_TRANSITIONS: dict[IncidentStatus, set[IncidentStatus]] = {
    IncidentStatus.DETECTED: {
        IncidentStatus.TRIAGED,
        IncidentStatus.INVESTIGATING,
        IncidentStatus.MITIGATED,
        IncidentStatus.RESOLVED,
        IncidentStatus.CLOSED,
        IncidentStatus.FALSE_POSITIVE,
    },
    IncidentStatus.TRIAGED: {
        IncidentStatus.INVESTIGATING,
        IncidentStatus.MITIGATED,
        IncidentStatus.RESOLVED,
        IncidentStatus.CLOSED,
        IncidentStatus.FALSE_POSITIVE,
    },
    IncidentStatus.INVESTIGATING: {
        IncidentStatus.MITIGATED,
        IncidentStatus.RESOLVED,
        IncidentStatus.CLOSED,
        IncidentStatus.FALSE_POSITIVE,
    },
    IncidentStatus.MITIGATED: {
        IncidentStatus.RESOLVED,
        IncidentStatus.CLOSED,
        IncidentStatus.FALSE_POSITIVE,
    },
    IncidentStatus.RESOLVED: {IncidentStatus.CLOSED},
    IncidentStatus.CLOSED: set(),
    IncidentStatus.FALSE_POSITIVE: set(),
}

CLOSED_STATUSES = {IncidentStatus.RESOLVED, IncidentStatus.CLOSED, IncidentStatus.FALSE_POSITIVE}


def can_transition(current: IncidentStatus, target: IncidentStatus) -> bool:
    return target in _TRANSITIONS.get(current, set())


def transition(incident: Incident, target: IncidentStatus) -> Incident:
    """Apply a validated status change; raises ValueError on illegal jumps."""
    if not can_transition(incident.status, target):
        raise ValueError(f"Illegal incident transition: {incident.status} → {target}")
    incident.status = target
    return incident
