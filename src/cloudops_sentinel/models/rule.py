from __future__ import annotations

from pydantic import BaseModel


class Rule(BaseModel):
    metric: str
    warning: float | None = None
    critical: float | None = None
    duration: int = 0
    operator: str = "gt"
