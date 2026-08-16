from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from .common import utcnow
from .log import LogEntry
from .metric import Metric


class Report(BaseModel):
    incident_id: str
    summary: str = ""
    impact: str = ""
    timeline: list[object] = Field(default_factory=list)
    metrics: list[Metric] = Field(default_factory=list)
    logs: list[LogEntry] = Field(default_factory=list)
    probable_cause: str = ""
    evidence: list[str] = Field(default_factory=list)
    resolution: str = ""
    recommendations: list[str] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=utcnow)
