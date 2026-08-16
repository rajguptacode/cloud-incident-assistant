"""Incident persistence layer (JSON file storage)."""

from __future__ import annotations

import json
from pathlib import Path


class Storage:
    """Stores incidents in a single JSON file."""

    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)

    def read(self) -> list[dict]:
        if not self.path.exists():
            return []
        try:
            return json.loads(self.path.read_text())
        except json.JSONDecodeError as e:
            raise ValueError(f"Corrupt storage file {self.path}: {e}") from e

    def write(self, incidents: list[dict]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(incidents, indent=2))