"""ATR-state classifier (§4.2.2 / §15.1 — ADR-011, Accepted).

Volatility regime from current H1 ATR(14) vs a rolling baseline:

    baseline = simple mean of the atr_baseline_window ATR(14) values immediately
               PRECEDING the current bar (the current bar is excluded, so "is now
               unusual vs recent history" is measured against an established base).
    r        = ATR(14)_current / baseline

    r < atr_compressed_mult (0.75)   → COMPRESSED
    r < atr_elevated_mult   (1.25)   → NORMAL
    r < atr_extreme_mult    (2.0)    → ELEVATED
    r ≥ atr_extreme_mult             → EXTREME

Boundaries are inclusive at the upper state (r == 1.25 → ELEVATED; r == 2.0 →
EXTREME; r == 0.75 → NORMAL).  Pure, deterministic; thresholds read from config.

When there is not enough history to form the baseline (or the baseline is zero),
classification defaults to NORMAL — the safe regime that neither widens the stop
nor blocks a trade, so missing warm-up never manufactures a no-trade or a wider
stop.
"""

from __future__ import annotations
from decimal import Decimal
from typing import Sequence

from lsb.config.models import StrategyParams
from .indicators import atr
from .types import AtrState

_ZERO = Decimal("0")


def state_for_ratio(ratio: Decimal, sp: StrategyParams) -> AtrState:
    """Map an ATR/baseline ratio to a regime (the pure threshold rule)."""
    if ratio < sp.atr_compressed_mult:
        return AtrState.COMPRESSED
    if ratio >= sp.atr_extreme_mult:
        return AtrState.EXTREME
    if ratio >= sp.atr_elevated_mult:
        return AtrState.ELEVATED
    return AtrState.NORMAL


def classify(candles_h1: Sequence[dict], sp: StrategyParams) -> AtrState:
    """Classify the volatility regime at the LAST H1 bar.  Defaults to NORMAL on
    insufficient warm-up (see module docstring)."""
    n = len(candles_h1)
    w = sp.atr_baseline_window
    # Need the current ATR plus w preceding ATR values, and ATR needs its own warm-up.
    if n < sp.atr_period + w + 1:
        return AtrState.NORMAL

    series = atr(list(candles_h1), sp.atr_period)
    current = series[-1]
    window = series[n - 1 - w: n - 1]            # the w values before the current bar
    if current is None or any(v is None for v in window):
        return AtrState.NORMAL

    baseline = sum(window, _ZERO) / Decimal(str(w))
    if baseline <= _ZERO:
        return AtrState.NORMAL

    return state_for_ratio(current / baseline, sp)
