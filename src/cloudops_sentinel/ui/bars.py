"""Percent bars and sparklines. Colors follow state: normal/warning/critical, no gradients (CLI-DESIGN.md §9-10)."""

from __future__ import annotations

from rich.text import Text

from . import theme
from .icons import icon


def _state_style(value: float, warn: float, crit: float) -> str:
    if value >= crit:
        return theme.DANGER
    if value >= warn:
        return theme.WARNING
    return theme.SUCCESS


def percent_bar(value: float, width: int = 16, warn: float = 70, crit: float = 90) -> Text:
    filled = round(value / 100 * width)
    filled = min(filled, width)
    text = Text()
    text.append(icon("block") * filled, style=_state_style(value, warn, crit))
    text.append(icon("empty") * (width - filled), style=theme.MUTED)
    return text


def sparkline(values: list[float], width: int = 10) -> Text:
    if not values:
        return Text("")
    buckets = ["▁", "▂", "▃", "▄", "▅", "▆", "▇", "█"]
    sampled = values
    step = max(1, len(values) // width)
    if len(values) > width:
        sampled = values[::step][:width]
    lo, hi = min(sampled), max(sampled)
    span = (hi - lo) or 1.0
    text = Text()
    for v in sampled:
        idx = min(len(buckets) - 1, int((v - lo) / span * (len(buckets) - 1)))
        text.append(buckets[idx], style=theme.SECONDARY)
    return text