"""Semantic color tokens — the only place ANSI colors are defined.

All CLI rendering must use these tokens, never raw colors (CLI-DESIGN.md §3-4).
"""

from __future__ import annotations

from rich.style import Style

PRIMARY = "cyan"
SECONDARY = "blue"
SUCCESS = "green"
WARNING = "yellow"
DANGER = "red"
CRITICAL = "bright_red"
MUTED = "grey50"
INFO = "cyan"
ACCENT = "magenta"

BORDER = "cyan"
TEXT = ""

PANEL_BORDER = Style(color=BORDER)
SEVERITY_STYLES = {
    "INFO": Style(color=SECONDARY),
    "LOW": Style(color=SUCCESS),
    "MEDIUM": Style(color=WARNING),
    "HIGH": Style(color=DANGER),
    "CRITICAL": Style(color=CRITICAL, bold=True),
}
STATUS_STYLES = {
    "HEALTHY": Style(color=SUCCESS),
    "WARNING": Style(color=WARNING),
    "DEGRADED": Style(color=WARNING),
    "HIGH": Style(color=DANGER),
    "CRITICAL": Style(color=CRITICAL, bold=True),
    "UNKNOWN": Style(color=MUTED),
    "RUNNING": Style(color=SUCCESS),
    "STOPPED": Style(color=DANGER),
}