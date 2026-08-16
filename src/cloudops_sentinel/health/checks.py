"""Sentinel self-monitoring (PRD §45) — collector/database/detection/storage/AI.

Observability of the monitor itself: if the monitoring system fails, the
operator must see it. Checks are data, not rendering — CLI decides display.
"""

from __future__ import annotations

from dataclasses import dataclass

OK = "OK"
WARN = "WARN"
FAIL = "FAIL"
OFF = "OFF"


@dataclass(frozen=True)
class ComponentHealth:
    name: str
    status: str
    detail: str = ""


def check_database(database=None) -> ComponentHealth:
    if database is None:
        return ComponentHealth("database", WARN, "database not initialized")
    healthy = getattr(database, "is_healthy", lambda: False)()
    return ComponentHealth(
        "database",
        OK if healthy else FAIL,
        "readiness probe ok" if healthy else "readiness probe failed",
    )


def run_checks(
    database=None,
    *,
    collectors_ok: bool = True,
    detection_ok: bool = True,
    storage_ok: bool = True,
    ai_enabled: bool = False,
) -> list[ComponentHealth]:
    return [
        ComponentHealth("collector", OK if collectors_ok else FAIL, "system telemetry collectors"),
        check_database(database),
        ComponentHealth("detection", OK if detection_ok else FAIL, "detection engine"),
        ComponentHealth("storage", OK if storage_ok else FAIL, "repositories + retention"),
        ComponentHealth("ai", OFF if not ai_enabled else OK, "AI module (disabled by default)"),
    ]


def overall(checks: list[ComponentHealth]) -> str:
    statuses = [c.status for c in checks]
    if FAIL in statuses:
        return FAIL
    if WARN in statuses:
        return WARN
    return OK
