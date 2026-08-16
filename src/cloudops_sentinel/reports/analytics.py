"""Historical analytics (PRD §32) — counts, distribution, resolution time."""

from __future__ import annotations

from cloudops_sentinel.models.incident import Incident, Severity

from ..incidents.deduplication import symptom_signals


def _duration_seconds(incident: Incident) -> float | None:
    if incident.resolved is None:
        return None
    return (incident.resolved - incident.started).total_seconds()


def _fmt_duration(seconds: float | None) -> str:
    if seconds is None:
        return ""
    m, s = divmod(int(seconds), 60)
    return f"{m}m {s:02d}s"


def summarize(incidents: list[Incident], uptime: str = "") -> dict:
    distribution = {s.value.lower(): 0 for s in Severity}
    durations = [d for d in (_duration_seconds(i) for i in incidents) if d is not None]
    signal_counts: dict[str, int] = {}
    for incident in incidents:
        distribution[incident.severity.value.lower()] += 1
        for signal in symptom_signals(incident.symptoms):
            signal_counts[signal] = signal_counts.get(signal, 0) + 1
    most_common = max(signal_counts, key=signal_counts.get) if signal_counts else ""

    return {
        "total": len(incidents),
        "severity_distribution": distribution,
        "avg_resolution": _fmt_duration(sum(durations) / len(durations)) if durations else "",
        "resolved_count": len(durations),
        "most_common": most_common,
        "uptime": uptime,
    }
