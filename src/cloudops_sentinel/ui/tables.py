"""Compact Rich tables. Color severity/status cells only, not every cell (CLI-DESIGN.md §18)."""

from __future__ import annotations

from rich.console import Console
from rich.table import Table
from rich.text import Text

from . import theme
from .console import severity_style, status_style


def table(title: str | None = None) -> Table:
    return Table(title=title, border_style=theme.BORDER, header_style=theme.SECONDARY, expand=False)


def render_table(
    console: Console,
    headers: list[str],
    rows: list[list[str]],
    title: str | None = None,
    severity_column: int | None = None,
    status_column: int | None = None,
) -> None:
    t = table(title)
    for h in headers:
        t.add_column(h)
    for row in rows:
        cells = [Text(c) for c in row]
        if severity_column is not None:
            cells[severity_column].style = severity_style(row[severity_column])
        if status_column is not None:
            cells[status_column].style = status_style(row[status_column])
        t.add_row(*cells)
    console.print(t)