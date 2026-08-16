from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field

from .common import utcnow


class Severity(StrEnum):
    INFO = "INFO"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class IncidentStatus(StrEnum):
    DETECTED = "DETECTED"
    TRIAGED = "TRIAGED"
    INVESTIGATING = "INVESTIGATING"
    MITIGATED = "MITIGATED"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"
    FALSE_POSITIVE = "FALSE_POSITIVE"


class Incident(BaseModel):
    id: str = ""
    title: str = ""
    severity: Severity = Severity.INFO
    score: float = 0.0
    status: IncidentStatus = IncidentStatus.DETECTED
    started: datetime = Field(default_factory=utcnow)
    resolved: datetime | None = None
    occurrences: int = 1
    symptoms: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)
    probable_cause: str = ""
    confidence: float = 0.0
    contributing_factors: list[str] = Field(default_factory=list)
    alternatives: list[str] = Field(default_factory=list)


class IncidentEvent(BaseModel):
    incident_id: str = ""
    type: str
    timestamp: datetime = Field(default_factory=utcnow)
    payload: dict[str, object] = Field(default_factory=dict)
