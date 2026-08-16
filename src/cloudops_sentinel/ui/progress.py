"""Progress bar wrapper — only active for interactive terminals (CLI-DESIGN.md §14)."""

from __future__ import annotations

from rich.console import Console
from rich.progress import BarColumn, Progress, TextColumn

from . import theme


def make_progress(console: Console, enabled: bool = True) -> Progress | None:
    if not enabled or not console.is_interactive:
        return None
    return Progress(
        TextColumn("[progress.description]{task.description}", style=theme.PRIMARY),
        BarColumn(bar_width=20),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        console=console,
    )