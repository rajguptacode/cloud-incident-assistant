"""Markdown incident report renderer."""

from __future__ import annotations


def to_markdown(data: dict) -> str:
    lines = [
        f"# Incident {data['incident_id']}",
        "",
        f"- **Summary:** {data['summary']}",
        f"- **Impact:** {data['impact']}",
        f"- **Probable cause:** {data['probable_cause']}",
        f"- **Resolution:** {data['resolution']}",
        "",
        "## Timeline",
        "",
        *(f"- `{e['timestamp'][11:19]}` {e['message']}" for e in data["timeline"]),
        "",
        "## Metrics",
        "",
        *(
            f"- {m['timestamp'][11:19]} `{m['name']}` = {m['value']:.0f} {m['unit']}"
            for m in data["metrics"]
        ),
        "",
        "## Logs",
        "",
        *(
            f"- `{l['timestamp'][11:19]}` **{l['severity']}** {l['service']}: {l['message']}"
            for l in data["logs"]
        ),
        "",
        "## Evidence",
        "",
        *(f"- {e}" for e in data["evidence"]),
        "",
        "## Recommendations",
        "",
        *(f"{i}. {r}" for i, r in enumerate(data["recommendations"], 1)),
        "",
    ]
    return "\n".join(lines)
