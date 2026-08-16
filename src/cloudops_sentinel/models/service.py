from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field

from .common import utcnow


class ServiceStatus(StrEnum):
    RUNNING = "RUNNING"
    STOPPED = "STOPPED"
    UNKNOWN = "UNKNOWN"


class Service(BaseModel):
    name: str
    status: ServiceStatus = ServiceStatus.UNKNOWN
    timestamp: datetime = Field(default_factory=utcnow)
