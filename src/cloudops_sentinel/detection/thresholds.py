"""Level 1 detection: static threshold classification (PRD §14)."""

from __future__ import annotations

from cloudops_sentinel.models.rule import Rule

NORMAL = "NORMAL"
WARNING = "WARNING"
CRITICAL = "CRITICAL"

LEVELS = (NORMAL, WARNING, CRITICAL)


def exceeds(value: float, threshold: float, operator: str) -> bool:
    return value >= threshold if operator == "gte" else value > threshold


def classify(value: float, rule: Rule) -> str:
    """NORMAL / WARNING / CRITICAL for a single reading against a rule."""
    if rule.critical is not None and exceeds(value, rule.critical, rule.operator):
        return CRITICAL
    if rule.warning is not None and exceeds(value, rule.warning, rule.operator):
        return WARNING
    return NORMAL


def worst(a: str, b: str) -> str:
    return (
        CRITICAL
        if (a == CRITICAL or b == CRITICAL)
        else WARNING
        if (a == WARNING or b == WARNING)
        else NORMAL
    )
