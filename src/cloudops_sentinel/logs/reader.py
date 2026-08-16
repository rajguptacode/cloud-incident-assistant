from __future__ import annotations

from collections import deque
from pathlib import Path


def read_tail(path: str | Path, max_lines: int = 1000) -> list[str]:
    p = Path(path)
    if not p.is_file():
        return []
    with p.open(errors="replace") as f:
        lines = deque(f, maxlen=max_lines)
    return [line.rstrip("\n") for line in lines]