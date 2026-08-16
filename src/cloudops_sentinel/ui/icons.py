"""Status icons with ASCII fallback. Icons supplement color, never replace it (CLI-DESIGN.md §6, §27)."""

from __future__ import annotations

import os
import sys

UNICODE = {
    "healthy": "●",
    "warning": "▲",
    "degraded": "◆",
    "high": "●",
    "critical": "◆",
    "unknown": "?",
    "ok": "✓",
    "fail": "✗",
    "down": "↓",
    "up": "↑",
    "block": "█",
    "empty": "░",
    "info": "●",
}

ASCII = {
    "healthy": "[OK]",
    "warning": "[WARN]",
    "degraded": "[DEG]",
    "high": "[HIGH]",
    "critical": "[CRIT]",
    "unknown": "[?]",
    "ok": "[PASS]",
    "fail": "[FAIL]",
    "down": "v",
    "up": "^",
    "block": "#",
    "empty": ".",
    "info": "[*]",
}


def unicode_ok() -> bool:
    forced = os.environ.get("SENTINEL_ASCII", "").strip().lower()
    if forced in ("1", "true", "yes"):
        return False
    if forced in ("0", "false", "no"):
        return True
    if os.environ.get("TERM") == "dumb":
        return False
    return bool(sys.stdout.isatty())


def icon(name: str) -> str:
    table = UNICODE if unicode_ok() else ASCII
    return table[name]