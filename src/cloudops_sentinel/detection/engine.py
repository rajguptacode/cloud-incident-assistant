"""Detection engine — Level 1-4 evaluation over stored telemetry (PRD §14).

Pure domain logic: reads metrics/events/logs through repositories, emits
:class:`DetectionEvent` per anomalous signal. No rendering, no SQL.

Metrics are expected under names ``cpu``, ``memory``, ``disk`` (the names
Part 1's config thresholds use); event/log signals are ``service``,
``http_errors``, ``log_error_spike``.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Protocol

from cloudops_sentinel.models.common import utcnow
from cloudops_sentinel.models.event import Event
from cloudops_sentinel.models.metric import Metric
from cloudops_sentinel.models.rule import Rule

from .baseline import baseline_anomaly
from .duration import sustained
from .rate_of_change import rate_change
from .rules import rules_from_config
from .thresholds import CRITICAL, NORMAL, WARNING, classify, worst


class MetricRepo(Protocol):
    def query(
        self,
        *,
        name: str | None = None,
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> list[Metric]: ...


class EventRepo(Protocol):
    def query(
        self,
        *,
        type: str | None = None,
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> list[Event]: ...


class LogRepo(Protocol):
    def query(
        self,
        *,
        level: str | None = None,
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> list: ...


@dataclass
class DetectionEvent:
    signal: str
    level: str
    message: str
    evidence: list[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=utcnow)
    value: float | None = None


class DetectionEngine:
    def __init__(
        self,
        metric_repo: MetricRepo,
        event_repo: EventRepo | None = None,
        log_repo: LogRepo | None = None,
        rules: dict[str, Rule] | None = None,
        now: Callable[[], datetime] = utcnow,
    ) -> None:
        self.metric_repo = metric_repo
        self.event_repo = event_repo
        self.log_repo = log_repo
        self.rules = rules or rules_from_config()
        self._now = now

    def evaluate(self, window_seconds: int = 300) -> list[DetectionEvent]:
        """One DetectionEvent per anomalous signal in the trailing window."""
        now = self._now()
        since = now - timedelta(seconds=window_seconds)
        detections: dict[str, DetectionEvent] = {}

        for metric in self.metric_repo.query(since=since):
            if metric.name not in self.rules:
                continue
            self._evaluate_metric(detections, metric.name, self.rules[metric.name], now)

        self._evaluate_events(
            detections, self.event_repo.query(since=since) if self.event_repo else []
        )
        self._evaluate_logs(detections, since)
        return list(detections.values())

    def _evaluate_metric(
        self, detections: dict[str, DetectionEvent], name: str, rule: Rule, now: datetime
    ) -> None:
        series = sorted(
            (m for m in self.metric_repo.query(name=name, since=now - timedelta(seconds=300))),
            key=lambda m: m.timestamp,
        )
        if not series:
            return
        values = [(m.timestamp, m.value) for m in series]
        last = series[-1]
        level = classify(last.value, rule)
        evidence: list[str] = []

        if rule.duration > 0 and level == CRITICAL and not sustained(values, rule, CRITICAL, now):
            level = WARNING
        spiked, delta = rate_change(values)
        if spiked and level != CRITICAL:
            level = worst(level, CRITICAL)
            evidence.append(f"{name} jumped +{delta:.0f} in the trailing rate-of-change window")

        if name in ("cpu", "memory"):
            anomaly, mean, std = baseline_anomaly([v for _, v in values[:-1]], last.value)
            if anomaly and level == NORMAL:
                level = WARNING
            if anomaly:
                evidence.append(
                    f"{name} at {last.value:.0f}% is above baseline (mean {mean:.0f}% ± {std:.0f}%)"
                )

        if level == NORMAL:
            return
        evidence.insert(
            0, f"{name} at {last.value:.0f} (warning {rule.warning}, critical {rule.critical})"
        )
        self._merge(
            detections,
            DetectionEvent(name, level, f"{name} anomaly", evidence, last.timestamp, last.value),
        )

    def _evaluate_events(self, detections: dict[str, DetectionEvent], events: list[Event]) -> None:
        service = next((e for e in events if e.type == "service_down"), None)
        if service is not None:
            svc = service.payload.get("service", "unknown")
            self._merge(
                detections,
                DetectionEvent(
                    "service",
                    CRITICAL,
                    f"Service {svc} is down",
                    [f"Service {svc} reported DOWN"],
                    service.timestamp,
                    0.0,
                ),
            )
        http_events = [e for e in events if e.type == "http_errors"]
        if http_events:
            rule = self.rules["http_errors"]
            level = classify(len(http_events), rule)
            if level != NORMAL:
                self._merge(
                    detections,
                    DetectionEvent(
                        "http_errors",
                        level,
                        f"{len(http_events)} HTTP error events in window",
                        [f"{len(http_events)} HTTP 5xx events detected"],
                        http_events[0].timestamp,
                        float(len(http_events)),
                    ),
                )

    def _evaluate_logs(self, detections: dict[str, DetectionEvent], since: datetime) -> None:
        if self.log_repo is None:
            return
        errors = self.log_repo.query(level="ERROR", since=since)
        rule = self.rules["log_error_spike"]
        level = classify(len(errors), rule)
        if level != NORMAL:
            self._merge(
                detections,
                DetectionEvent(
                    "log_error_spike",
                    level,
                    f"{len(errors)} ERROR log entries in window",
                    [f"{len(errors)} ERROR-level log entries detected"],
                    since,
                    float(len(errors)),
                ),
            )

    @staticmethod
    def _merge(detections: dict[str, DetectionEvent], event: DetectionEvent) -> None:
        existing = detections.get(event.signal)
        if existing is None or worst(existing.level, event.level) != existing.level:
            detections[event.signal] = event
