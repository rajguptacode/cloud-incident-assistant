"""Shared helpers for scenario generators — deterministic waves and phases."""

from __future__ import annotations

import math


def wave(seconds_from_start: float, base: float, amplitude: float, period: float = 600.0) -> float:
    """Deterministic pseudo-noise: base ± amplitude sinusoid."""
    return base + amplitude * math.sin(2 * math.pi * seconds_from_start / period)


def ramp(seconds_from_start: float, t0: float, t1: float, v0: float, v1: float) -> float:
    """Linear interpolation between (t0, v0) and (t1, v1), clamped outside."""
    if seconds_from_start <= t0:
        return v0
    if seconds_from_start >= t1:
        return v1
    return v0 + (v1 - v0) * (seconds_from_start - t0) / (t1 - t0)


def fraction(seconds_from_start: float, total: float) -> float:
    return min(1.0, max(0.0, seconds_from_start / total))
