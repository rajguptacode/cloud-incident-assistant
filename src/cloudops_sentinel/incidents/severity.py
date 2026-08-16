"""Severity facade — PRD §22 scoring lives in detection.scoring; re-exported
here so incident code and CLI import from one place."""

from __future__ import annotations

from cloudops_sentinel.detection.scoring import WEIGHTS, score_signals, severity_from_score

__all__ = ["WEIGHTS", "score_signals", "severity_from_score"]
