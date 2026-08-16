"""Plain-text incident report renderer."""

from __future__ import annotations


def to_text(data: dict) -> str:
    lines = [
        f"INCIDENT {data['incident_id']}",
        "=" * 40,
        f"Summary:  {data['summary']}",
        f"Impact:   {data['impact']}",
        "",
        "TIMELINE",
        *(f"  {e['timestamp'][11:19]}  {e['message']}" for e in data["timeline"]),
        "",
        "METRICS",
        *(
            f"  {m['timestamp'][11:19]}  {m['name']:<16} {m['value']:.0f} {m['unit']}"
            for m in data["metrics"]
        ),
        "",
        "LOGS",
        *(
            f"  {l['timestamp'][11:19]}  {l['severity']:<8} {l['service']:<12} {l['message']}"
            for l in data["logs"]
        ),
        "",
        "PROBABLE CAUSE",
        f"  {data['probable_cause']}",
        "",
        "EVIDENCE",
        *(f"  • {e}" for e in data["evidence"]),
        "",
        "RESOLUTION",
        f"  {data['resolution']}",
        "",
        "RECOMMENDATIONS",
        *(f"  {i}. {r}" for i, r in enumerate(data["recommendations"], 1)),
        "",
    ]
    return "\n".join(lines).rstrip() + "\n"
