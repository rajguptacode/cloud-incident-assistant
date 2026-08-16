"""Recovery detection (PRD §25).

An incident is recovered when every symptom signal returns to normal:
metrics below thresholds (last N readings), the service came back up, or
error counts stopped. All signals must recover — one still-anomalous signal
keeps the incident open.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from cloudops_sentinel.models.common import utcnow
from cloudops_sentinel.models.incident import Incident
from cloudops_sentinel.models.rule import Rule

from ..detection.thresholds import NORMAL, classify
from .deduplication import symptom_signals


def recovered(
    incident: Incident,
    metric_repo,
    event_repo,
    log_repo,
    rules: dict[str, Rule],
    *,
    samples: int = 2,
    window: int = 300,
    now: datetime | None = None,
) -> bool:
    now = now or utcnow()
    signals = symptom_signals(incident.symptoms)
    if not signals:
        return False

    for signal in signals:
        rule = rules.get(signal)
        if signal in ("cpu", "memory", "disk"):
            if rule is None:
                return False
            recent = metric_repo.query(name=signal, since=incident.started)
            if len(recent) < 1:
                return False
            tail = [m.value for m in recent[-samples:]]
            if not all(classify(v, rule) == NORMAL for v in tail):
                return False
        elif signal == "service":
            if event_repo is None:
                return False
            if not event_repo.query(type="service_up", since=incident.started):
                return False
        elif signal == "http_errors":
            if event_repo is None:
                return False
            since = now - timedelta(seconds=window)
            if event_repo.query(type="http_errors", since=since):
                return False
        elif signal == "log_error_spike":
            if log_repo is None or rule is None:
                return False
            since = now - timedelta(seconds=window)
            recent = log_repo.query(level="ERROR", since=since)
            if classify(len(recent), rule) != NORMAL:
                return False
        else:
            return False
    return True
