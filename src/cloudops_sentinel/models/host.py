from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from .common import utcnow


class HostInfo(BaseModel):
    hostname: str
    os: str
    kernel: str
    uptime_seconds: float
    timestamp: datetime = Field(default_factory=utcnow)
