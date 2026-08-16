"""Evidence collection — stored, never fabricated (AGENTS.md).

Evidence entries are plain strings on the Incident model; this module only
keeps appends idempotent and symptom strings structured.
"""

from __future__ import annotations

from collections.abc import Iterable

from cloudops_sentinel.models.incident import Incident


def add_evidence(incident: Incident, lines: Iterable[str]) -> None:
    for line in lines:
        if line and line not in incident.evidence:
            incident.evidence.append(line)


def symptom(signal: str, detail: str) -> str:
    """Structured symptom: the leading ``signal:`` token drives dedup."""
    return f"{signal}: {detail}"
