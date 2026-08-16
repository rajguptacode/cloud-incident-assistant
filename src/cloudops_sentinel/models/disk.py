from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from .common import utcnow


class DiskUsage(BaseModel):
    mountpoint: str
    device: str = ""
    total: int = 0
    used: int = 0
    free: int = 0
    percent: float = 0.0
    inode_percent: float | None = None
    timestamp: datetime = Field(default_factory=utcnow)
