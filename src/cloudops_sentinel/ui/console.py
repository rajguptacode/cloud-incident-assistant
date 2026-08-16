"""Console factory — central place for color/no-color and terminal detection."""

from __future__ import annotations

import os

from rich.console import Console

from . import theme


def make_console(no_color: bool = False) -> Console:
    if no_color or os.environ.get("NO_COLOR"):
        return Console(color_system=None)
    return Console()


def styled(text: str, style: str) -> str:
    return f"[{style}]{text}[/{style}]"


def colorize(text: str, style: str, console: Console) -> str:
    if console.color_system is None:
        return text
    return styled(text, style)


def severity_style(severity: str) -> str:
    style = theme.SEVERITY_STYLES.get(severity.upper())
    return style.color.name if style and style.color else theme.TEXT


def status_style(state: str) -> str:
    style = theme.STATUS_STYLES.get(state.upper())
    return style.color.name if style and style.color else theme.TEXT