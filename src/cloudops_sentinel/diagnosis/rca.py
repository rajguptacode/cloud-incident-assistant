"""Root cause analysis (PRD §21).

Output: probable cause + supporting evidence + contributing factors +
confidence + alternatives. Heuristic, evidence-grounded: confidence grows
with the number of distinct corroborating signals, is capped below 100%,
and never claims certainty without evidence.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from cloudops_sentinel.models.incident import Incident

from ..detection.scoring import WEIGHTS
from ..incidents.deduplication import symptom_signals

CAUSES: dict[str, str] = {
    "cpu": "High CPU utilization",
    "memory": "Memory pressure",
    "disk": "Disk usage critically high",
    "service": "Service is down or stopped",
    "http_errors": "Application/upstream failure causing HTTP errors",
    "log_error_spike": "Elevated error rate in service logs",
}

ALTERNATIVES: dict[str, list[str]] = {
    "cpu": ["Background job or scheduled task", "Upstream load spike"],
    "memory": ["Memory leak in application process", "Cache growth"],
    "disk": ["Log or artifact accumulation", "Database growth"],
    "service": ["Crash or OOM kill", "Manual stop / config error"],
    "http_errors": ["Upstream dependency degradation", "Deployment regression"],
    "log_error_spike": ["Noisy dependency", "Input validation failures"],
}

MAX_CONFIDENCE = 0.95


@dataclass
class Diagnosis:
    probable_cause: str
    confidence: float
    contributing_factors: list[str] = field(default_factory=list)
    alternatives: list[str] = field(default_factory=list)
    evidence: list[str] = field(default_factory=list)


def diagnose(incident: Incident, correlation=None) -> Diagnosis:
    signals = symptom_signals(incident.symptoms)
    if not signals:
        return Diagnosis(
            "Insufficient evidence to determine a probable cause",
            0.0,
            [],
            [],
            list(incident.evidence),
        )

    ordered = sorted(signals, key=lambda s: WEIGHTS.get(s, 0), reverse=True)
    primary = ordered[0]
    cause = CAUSES.get(primary, f"{primary} anomaly")

    evidence = list(incident.evidence)
    if correlation is not None:
        for name, stats in getattr(correlation, "stats", {}).items():
            peak = stats.get("max")
            if peak is not None and name in signals:
                evidence.append(f"{name} peaked at {peak:.0f} in the incident window")
        if len(getattr(correlation, "events", [])) > 0:
            evidence.append(f"{len(correlation.events)} related events in the incident window")

    contributing = [CAUSES[s] for s in ordered[1:]]
    confidence = round(min(MAX_CONFIDENCE, 0.45 + 0.15 * len(signals)), 2)
    alternatives = list(ALTERNATIVES.get(primary, ["Unrelated concurrent change"]))

    if incident.resolved is not None:
        evidence.append("Recovery observed: metrics returned to normal")
    return Diagnosis(cause, confidence, contributing, alternatives, evidence)
