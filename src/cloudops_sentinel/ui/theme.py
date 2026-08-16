"""Semantic color tokens — the only place ANSI colors are defined.

Premium dark-first design system: dark surfaces, yellow primary brand,
purple secondary accent, clean green/red/orange semantic states.
All CLI rendering must use these tokens, never raw colors (CLI-DESIGN.md §3-4).

Semantics (kept consistent app-wide):
YELLOW = primary/action/brand · PURPLE = secondary/special/AI
GREEN = success/healthy · RED = error/critical · ORANGE = warning
BLUE = info · WHITE = important text · GRAY = secondary/muted
"""

from __future__ import annotations

from rich.style import Style

# Background & surfaces
BACKGROUND = "#0B0B0F"
SURFACE = "#12121A"
SURFACE_ELEVATED = "#181824"

# Primary — yellow (brand/action)
PRIMARY = "#F5C542"
PRIMARY_HOVER = "#FFD95A"
PRIMARY_ACTIVE = "#D9A91F"

# Secondary — purple (advanced/special/AI)
SECONDARY = "#7C3AED"
SECONDARY_DARK = "#4C1D95"
SECONDARY_BRIGHT = "#A78BFA"

# Semantic states
SUCCESS = "#22C55E"
SUCCESS_LIGHT = "#4ADE80"
DANGER = "#EF4444"
DANGER_LIGHT = "#F87171"
CRITICAL = "#EF4444"
WARNING = "#F59E0B"
WARNING_LIGHT = "#FBBF24"
INFO = "#38BDF8"

# Text hierarchy
TEXT_PRIMARY = "#F8FAFC"
TEXT_SECONDARY = "#A1A1AA"
TEXT_MUTED = "#71717A"
TEXT_DISABLED = "#52525B"

# Borders
BORDER = "#27272A"
BORDER_STRONG = "#3F3F46"
BORDER_HOVER = "#52525B"

# Legacy aliases (consumers use these names)
TEXT = TEXT_PRIMARY
MUTED = TEXT_MUTED
ACCENT = SECONDARY

PANEL_BORDER = Style(color=BORDER)
SEVERITY_STYLES = {
    "INFO": Style(color=INFO),
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
    "UNKNOWN": Style(color=TEXT_MUTED),
    "RUNNING": Style(color=SUCCESS),
    "STOPPED": Style(color=DANGER),
}