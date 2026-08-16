from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from typing import Any

from ..models.log import LogEntry, LogLevel

_LEVEL_MAP: dict[str, LogLevel] = {
    "DEBUG": LogLevel.DEBUG,
    "INFO": LogLevel.INFO,
    "WARN": LogLevel.WARNING,
    "WARNING": LogLevel.WARNING,
    "ERROR": LogLevel.ERROR,
    "CRITICAL": LogLevel.CRITICAL,
    "FATAL": LogLevel.CRITICAL,
}


def normalize(raw: dict[str, Any], source: str = "", host: str = "") -> LogEntry:
    ts = raw.get("timestamp")
    if not isinstance(ts, datetime):
        ts = datetime.now(UTC)
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=UTC)
    severity = _LEVEL_MAP.get(str(raw.get("severity", "INFO")).upper(), LogLevel.INFO)
    message = str(raw.get("message", ""))
    service = str(raw.get("service", ""))
    event_id = hashlib.sha1(f"{source}:{ts.isoformat()}:{message}".encode()).hexdigest()[:16]
    return LogEntry(
        timestamp=ts,
        severity=severity,
        service=service,
        host=host,
        message=message,
        source=source,
        event_id=event_id,
    )