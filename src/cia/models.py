"""Incident data models."""

from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone

STATUSES = ("open", "investigating", "resolved")


@dataclass
class Incident:
    """A single cloud incident."""

    title: str
    severity: str = "medium"
    status: str = "open"
    service: str = ""
    description: str = ""
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    created_at: str = field(default_factory=lambda: _now())
    updated_at: str = field(default_factory=lambda: _now())

    def __post_init__(self) -> None:
        if not self.title.strip():
            raise ValueError("Incident title cannot be empty")
        if self.severity not in ("low", "medium", "high", "critical"):
            raise ValueError(f"Invalid severity: {self.severity}")
        if self.status not in STATUSES:
            raise ValueError(f"Invalid status: {self.status}")

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Incident":
        return cls(**data)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()