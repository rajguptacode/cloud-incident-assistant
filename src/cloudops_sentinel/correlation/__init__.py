"""Correlation engine — time windows, timeline, incident-window grouping."""

from .engine import Correlation, CorrelationEngine
from .timeline import TimelineEntry, build_timeline
from .windows import Window, around, for_incident

__all__ = [
    "Correlation",
    "CorrelationEngine",
    "TimelineEntry",
    "Window",
    "around",
    "build_timeline",
    "for_incident",
]
