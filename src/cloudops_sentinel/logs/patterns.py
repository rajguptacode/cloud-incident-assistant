from __future__ import annotations

import re
from collections import Counter

_PATTERNS: dict[str, re.Pattern[str]] = {
    "timeout": re.compile(r"\b(timeout|timed?\s*out|timed out)\b", re.IGNORECASE),
    "connection_refused": re.compile(r"\b(connection refused|connect.*refused)\b", re.IGNORECASE),
    "connection_reset": re.compile(r"\b(connection reset|reset by peer)\b", re.IGNORECASE),
    "restart": re.compile(r"\b(restart(ing)?|started)\b", re.IGNORECASE),
    "error": re.compile(r"\b(error|exception|traceback|failed|fatal)\b", re.IGNORECASE),
    "retry": re.compile(r"\bretry(ing)?\b", re.IGNORECASE),
}

_RESTART_LOOP_RE = re.compile(r"\b(restart(ing)?|failed|crash(ed)?|exited|exit)\b", re.IGNORECASE)


def detect_patterns(message: str) -> list[str]:
    return [name for name, pattern in _PATTERNS.items() if pattern.search(message)]


def count_levels(entries: list[object]) -> dict[str, int]:
    return dict(Counter(getattr(e, "severity", "INFO").value for e in entries))


def is_restart_loop(messages: list[str], window: int = 10) -> bool:
    failing = sum(1 for m in messages[-window:] if _RESTART_LOOP_RE.search(m))
    return failing >= 3