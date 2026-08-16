"""Reusable Rich panels: header, sections, errors, warnings (CLI-DESIGN.md §7-8, §22-23)."""

from __future__ import annotations

from rich.console import Console, Group, RenderableType
from rich.panel import Panel
from rich.text import Text

from . import theme


def header(console: Console, version: str) -> None:
    title = Text("CLOUDOPS SENTINEL", style=theme.PRIMARY, justify="center")
    subtitle = Text("Infrastructure Monitoring & Incident Analysis", style=theme.MUTED, justify="center")
    console.print(Panel(Group(title, subtitle), border_style=theme.BORDER, padding=(0, 1)))


def section(title: str, body: RenderableType, border: str = theme.BORDER) -> Panel:
    return Panel(
        body,
        title=Text(title, style=theme.SECONDARY),
        border_style=border,
        title_align="left",
        padding=(0, 1),
    )


def error_panel(console: Console, message: str, reason: str, try_: str, code: str) -> None:
    body = Group(
        Text("Reason:", style=theme.MUTED),
        Text(reason),
        Text("Try:", style=theme.MUTED),
        Text(try_),
        Text(f"Error code: {code}", style=theme.MUTED),
    )
    console.print(Panel(body, title=Text(f"✗ {message}", style=theme.DANGER), border_style=theme.DANGER))


def warning_panel(console: Console, message: str, detail: str, next_command: str) -> None:
    body = Group(
        Text(detail),
        Text("Run:", style=theme.MUTED),
        Text(next_command),
    )
    console.print(Panel(body, title=Text("▲ WARNING", style=theme.WARNING), border_style=theme.WARNING))


def info_line(console: Console, message: str) -> None:
    console.print(Text(message, style=theme.INFO))