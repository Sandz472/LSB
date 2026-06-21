"""Shared types for the C2 signal engine."""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum


class Side(Enum):
    BEAR = "BEAR"   # short setup (spec primary direction)
    BULL = "BULL"   # exact mirror (§8.1 footnote)


@dataclass(frozen=True, slots=True)
class GateResult:
    """Immutable result from a single gate evaluation.

    passed: True iff this gate's condition is met.
    state:  machine-readable qualifier (e.g. "BEARISH", "INVALID", "INVALIDATED", "NONE").
    detail: arbitrary diagnostic values (block_high, ema_vals, …) for A5 conjunction
            and A10 reporting.  Never read by the gate itself after construction.
    """
    passed: bool
    state: str | None = None
    detail: dict = field(default_factory=dict)
