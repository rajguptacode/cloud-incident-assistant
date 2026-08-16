from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field

from .common import utcnow


class LogLevel(StrEnum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogEntry(BaseModel):
    timestamp: datetime
    severity: LogLevel = LogLevel.INFO
    service: str = ""
    host: str = ""
    message: str = ""
    source: str = ""
    event_id: str = ""
    timestamp_utc: datetime = Field(default_factory=utcnow)
