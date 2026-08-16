"""Spinner wrapper — subtle, interactive-terminal only, never in CI/redirected output (CLI-DESIGN.md §13, §28)."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from rich.console import Console


@contextmanager
def status(console: Console, text: str, enabled: bool = True) -> Iterator[None]:
    if enabled and console.is_interactive:
        with console.status(text, spinner="dots") as _status:
            yield
    else:
        console.print(f"{text}...")
        yield