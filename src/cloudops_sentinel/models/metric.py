from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from .common import utcnow


class Metric(BaseModel):
    name: str
    value: float
    unit: str = ""
    host: str = ""
    timestamp: datetime = Field(default_factory=utcnow)
