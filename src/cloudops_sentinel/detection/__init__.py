"""Detection engine — levels 1-4, configurable rules, scoring (PRD §14, §22)."""

from .baseline import baseline_anomaly
from .duration import sustained
from .engine import DetectionEngine, DetectionEvent
from .rate_of_change import rate_change
from .rules import DEFAULT_RULES, rules_from_config
from .scoring import WEIGHTS, score_signals, severity_from_score
from .thresholds import CRITICAL, NORMAL, WARNING, classify

__all__ = [
    "CRITICAL",
    "DEFAULT_RULES",
    "NORMAL",
    "WARNING",
    "WEIGHTS",
    "DetectionEngine",
    "DetectionEvent",
    "baseline_anomaly",
    "classify",
    "rate_change",
    "rules_from_config",
    "score_signals",
    "severity_from_score",
    "sustained",
]
