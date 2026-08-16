from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from .common import utcnow


class ProcessInfo(BaseModel):
    pid: int
    name: str
    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    command: str = ""
    timestamp: datetime = Field(default_factory=utcnow)
