"""Shared types for the C2 signal engine."""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum


class Side(Enum):
    BEAR = "BEAR"   # short setup (spec primary direction)
    BULL = "BULL"   # exact mirror (§8.1 footnote)


class AtrState(Enum):
    """Volatility regime (§4.2.2 / §9.3).

    Explicit INPUT to Gate 7 (buffer selection) and Gate 8 (EXTREME pre-filter).
    The numeric classifier that derives this from an ATR series is a deferred
    owner decision (ADR-008) pinned before backtest integration (A6-A7); it is
    deliberately kept OUT of the gate decision path so A5 invents no thresholds.
    """
    NORMAL = "NORMAL"
    ELEVATED = "ELEVATED"
    EXTREME = "EXTREME"


class Verdict(Enum):
    """Terminal classification of an evaluated candle (A5 persistence boundary)."""
    QUALIFIED = "QUALIFIED"      # all 8 gates TRUE
    REJECTED = "REJECTED"        # at least one gate FALSE (ordinary miss)
    INVALIDATED = "INVALIDATED"  # §6.1.1/.2 structure invalidation reached


class RiskTier(Enum):
    """§9.3 position-size tier selected by the sweep-probability score (NOT a gate)."""
    HIGH = "1.0pct"      # score 80-100
    MID = "0.5pct"       # score 50-79
    LOW = "0.25pct"      # score <50 (or discretionary skip)
    SKIP = "skip"        # discretionary skip<50, or zeroed by EXTREME/drawdown
    ZERO = "0pct"        # ATR EXTREME / drawdown breach → no size


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


@dataclass(frozen=True, slots=True)
class SignalResult:
    """Complete result of the §8.1 conjunction for one evaluated H1 candle.

    This is what the persistence boundary serialises into a `signal` row — one
    row for 100% of evaluated candles, QUALIFIED / REJECTED / INVALIDATED.

    gates:    ordered tuple of the 8 GateResults (index 0 = Gate 1 … index 7 = Gate 8).
              A gate not reached (short-circuit) is still recorded as its FALSE result.
    all_gates: True iff every gate passed.
    verdict:  QUALIFIED / REJECTED / INVALIDATED.
    sweep_score: 0-100 §7.3 score (None if not computed). NOT a gate.
    risk_tier: §9.3 tier from the score. NOT a gate.
    side / ts / instrument: identity of the evaluated bar.
    reasons: per-gate human-readable miss reason, for the signal row + A10 report.
    """
    instrument: str
    ts: object                       # tz-aware datetime (UTC)
    side: Side
    gates: tuple[GateResult, ...]
    all_gates: bool
    verdict: Verdict
    sweep_score: object | None = None        # Decimal | None
    risk_tier: RiskTier | None = None
    reasons: tuple[str, ...] = ()
