"""Report generators — plain text, markdown, JSON (PRD §31).

All formatters take a plain data dict so rendering stays presentation-pure;
`build_report` produces the contract :class:`Report` model for persistence.
"""

from __future__ import annotations

from datetime import datetime

from cloudops_sentinel.models.common import utcnow
from cloudops_sentinel.models.incident import Incident
from cloudops_sentinel.models.report import Report

from ..correlation.engine import Correlation
from .markdown import to_markdown
from .text import to_text

FORMATS = ("txt", "markdown", "json")

RECOMMENDATIONS: dict[str, list[str]] = {
    "cpu": [
        "Inspect top CPU consumers: sentinel processes --cpu",
        "Check for recent deploy/process changes",
    ],
    "memory": [
        "Check for memory leaks in application processes",
        "Review top memory consumers: sentinel processes --memory",
    ],
    "disk": ["Free disk space: sentinel disk --forecast", "Review log/artifact cleanup policy"],
    "service": [
        "Investigate service health and restart history",
        "Check service config for recent changes",
    ],
    "http_errors": [
        "Inspect upstream/application logs for 5xx causes",
        "Verify upstream dependency health",
    ],
    "log_error_spike": [
        "Inspect error logs: sentinel logs --level error",
        "Correlate error timestamps with deployments",
    ],
}


def duration_str(incident: Incident) -> str:
    if incident.resolved is None:
        return ""
    seconds = int((incident.resolved - incident.started).total_seconds())
    m, s = divmod(seconds, 60)
    return f"{m}m {s:02d}s"


def recommendations(incident: Incident) -> list[str]:
    out: list[str] = []
    for signal, items in RECOMMENDATIONS.items():
        if any(s.startswith(f"{signal}:") for s in incident.symptoms):
            out.extend(items)
    return out or ["Monitor and verify the system returns to baseline"]


def report_dict(incident: Incident, correlation: Correlation | None = None) -> dict:
    timeline = [e.as_dict() for e in correlation.timeline] if correlation else []
    metrics = []
    if correlation:
        for series in correlation.metrics.values():
            metrics.extend(
                {
                    "name": m.name,
                    "value": m.value,
                    "unit": m.unit,
                    "timestamp": m.timestamp.isoformat(),
                }
                for m in series[-20:]
            )
    logs = []
    if correlation:
        logs.extend(
            {
                "timestamp": l.timestamp.isoformat(),
                "severity": str(l.severity),
                "service": l.service,
                "message": l.message,
            }
            for l in correlation.logs[-50:]
        )
    return {
        "incident_id": incident.id,
        "summary": f"{incident.severity.value} incident — {incident.title or 'anomaly detected'}",
        "impact": f"{incident.severity.value} severity, score {incident.score:.0f}, {len(incident.symptoms)} symptom signal(s)",
        "timeline": timeline,
        "metrics": metrics,
        "logs": logs,
        "probable_cause": incident.probable_cause or "Not diagnosed",
        "evidence": list(incident.evidence),
        "resolution": f"RESOLVED after {duration_str(incident)}"
        if incident.resolved
        else f"Status: {incident.status.value}",
        "recommendations": recommendations(incident),
        "generated_at": utcnow().isoformat(),
    }


def build_report(incident: Incident, correlation: Correlation | None = None) -> Report:
    data = report_dict(incident, correlation)
    return Report(
        incident_id=data["incident_id"],
        summary=data["summary"],
        impact=data["impact"],
        timeline=data["timeline"],
        metrics=data["metrics"],
        logs=data["logs"],
        probable_cause=data["probable_cause"],
        evidence=data["evidence"],
        resolution=data["resolution"],
        recommendations=data["recommendations"],
        generated_at=datetime.fromisoformat(data["generated_at"]),
    )


def generate(incident: Incident, correlation: Correlation | None = None, fmt: str = "txt") -> str:
    if fmt not in FORMATS:
        raise ValueError(f"Unknown report format '{fmt}'. Use one of: {', '.join(FORMATS)}")
    data = report_dict(incident, correlation)
    if fmt == "txt":
        return to_text(data)
    if fmt == "markdown":
        return to_markdown(data)
    from .json import to_json

    return to_json(data)
