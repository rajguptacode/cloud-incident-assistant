"""Machine output + exit codes (PRD §47-48)."""

from __future__ import annotations

import json
import sys
from typing import Any

import typer

EXIT_OK = 0
EXIT_WARNING = 1
EXIT_CRITICAL = 2


def emit(data: Any) -> None:
    print(json.dumps(data, indent=2, default=str))


def exit_with(code: int) -> None:
    raise typer.Exit(code)


def err(message: str) -> None:
    print(message, file=sys.stderr)