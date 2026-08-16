"""Incident engine — lifecycle, dedup, severity, evidence, recovery, manager."""

from .deduplication import active_incidents, dedup_key, find_match, symptom_signals
from .evidence import add_evidence, symptom
from .lifecycle import CLOSED_STATUSES, can_transition, transition
from .manager import TITLES, IncidentManager
from .recovery import recovered
from .severity import WEIGHTS, score_signals, severity_from_score

__all__ = [
    "CLOSED_STATUSES",
    "TITLES",
    "WEIGHTS",
    "IncidentManager",
    "active_incidents",
    "add_evidence",
    "can_transition",
    "dedup_key",
    "find_match",
    "recovered",
    "score_signals",
    "severity_from_score",
    "symptom",
    "symptom_signals",
    "transition",
]
