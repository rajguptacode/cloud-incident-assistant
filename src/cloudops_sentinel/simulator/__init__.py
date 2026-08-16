"""Simulator — safe, repeatable synthetic scenarios + end-to-end demo (PRD §29-30)."""

from .base import INTERVAL_SECONDS, ScenarioContext, ScenarioData, timestamps
from .demo import DemoResult, DemoStep, run_demo
from .engine import (
    EXPECTED_SEVERITY,
    SCENARIOS,
    SimulationResult,
    run,
)

__all__ = [
    "EXPECTED_SEVERITY",
    "INTERVAL_SECONDS",
    "SCENARIOS",
    "DemoResult",
    "DemoStep",
    "ScenarioContext",
    "ScenarioData",
    "SimulationResult",
    "run",
    "run_demo",
    "timestamps",
]
