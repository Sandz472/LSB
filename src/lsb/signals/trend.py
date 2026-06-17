"""M3 — Trend Analysis Engine.

Outputs exactly one of four trend states on each candle evaluation.
Pure functions: no I/O, no side effects.

Spec: LSB_System_Requirements_v2.0.md §5.
"""

from __future__ import annotations

from enum import Enum, auto
from typing import Sequence

from lsb.data.config import SignalParams
from lsb.signals import Candle
from lsb.signals.indicators import (
    ATRState,
    SlopeState,
    atr_baseline,
    atr_series,
    classify_atr_state,
    ema_series,
    slope_state,
)


class TrendState(Enum):
    BULLISH = auto()
    BEARISH = auto()
    NEUTRAL = auto()
    INVALID = auto()


_EMA_CROSS_LOOKBACK = 3  # bars over which a crossing invalidates trend


def _ema_order_bullish(e21: float, e50: float, e89: float) -> bool:
    return e21 > e50 > e89


def _ema_order_bearish(e21: float, e50: float, e89: float) -> bool:
    return e21 < e50 < e89


def _has_recent_crossing(
    ema21_vals: Sequence[float],
    ema50_vals: Sequence[float],
    lookback: int = _EMA_CROSS_LOOKBACK,
) -> bool:
    """True if EMA21/EMA50 relative ordering changed within the last `lookback` bars."""
    n = min(lookback + 1, len(ema21_vals), len(ema50_vals))
    if n < 2:
        return False
    signs = [ema21_vals[-n + i] - ema50_vals[-n + i] for i in range(n)]
    # A sign change in the sequence means a crossing occurred.
    for i in range(1, len(signs)):
        if (signs[i] >= 0) != (signs[i - 1] >= 0):
            return True
    return False


def trend_state(candles: Sequence[Candle], p: SignalParams) -> TrendState:
    """Compute M3 trend state for the last candle in `candles`.

    Requires sufficient warm-up candles for EMA89 (at least p.ema_long_period + 1)
    and ATR (at least p.atr_period + 1). Returns INVALID if the window is too small.
    """
    closes = [c.close for c in candles]

    e21_series = ema_series(closes, p.ema_short_period)
    e50_series = ema_series(closes, p.ema_mid_period)
    e89_series = ema_series(closes, p.ema_long_period)
    atr_vals = atr_series(candles, p.atr_period)

    # Not enough data for a valid evaluation.
    if not e21_series or not e50_series or not e89_series or not atr_vals:
        return TrendState.INVALID

    e21 = e21_series[-1]
    e50 = e50_series[-1]
    e89 = e89_series[-1]
    current_atr = atr_vals[-1]

    # EMA Compression (spec §5.2): |EMA21 − EMA89| < ATR × compression_mult → INVALID.
    if abs(e21 - e89) < current_atr * p.ema_compression_atr_mult:
        return TrendState.INVALID

    # Recent EMA crossing check (spec §5.1 INVALID condition):
    # Align the two series to the same length for comparison.
    n_compare = min(len(e21_series), len(e50_series))
    if _has_recent_crossing(e21_series[-n_compare:], e50_series[-n_compare:]):
        return TrendState.INVALID

    # Slope threshold — convert ATR to EMA-slope terms.
    slope_threshold = current_atr * p.slope_threshold_atr_mult

    # BULLISH: EMA21 > EMA50 > EMA89 AND slope21 POSITIVE AND slope50 POSITIVE.
    if _ema_order_bullish(e21, e50, e89):
        s21 = slope_state(e21_series, p.ema_slope_lookback, slope_threshold)
        s50 = slope_state(e50_series, p.ema_slope_lookback, slope_threshold)
        if s21 == SlopeState.POSITIVE and s50 == SlopeState.POSITIVE:
            return TrendState.BULLISH
        return TrendState.NEUTRAL

    # BEARISH: EMA21 < EMA50 < EMA89 AND slope21 NEGATIVE AND slope50 NEGATIVE.
    if _ema_order_bearish(e21, e50, e89):
        s21 = slope_state(e21_series, p.ema_slope_lookback, slope_threshold)
        s50 = slope_state(e50_series, p.ema_slope_lookback, slope_threshold)
        if s21 == SlopeState.NEGATIVE and s50 == SlopeState.NEGATIVE:
            return TrendState.BEARISH
        return TrendState.NEUTRAL

    return TrendState.NEUTRAL


def current_emas(
    candles: Sequence[Candle], p: SignalParams
) -> tuple[float | None, float | None, float | None]:
    """Return (EMA21, EMA50, EMA89) for the last candle, or None if insufficient data."""
    closes = [c.close for c in candles]
    e21 = ema_series(closes, p.ema_short_period)
    e50 = ema_series(closes, p.ema_mid_period)
    e89 = ema_series(closes, p.ema_long_period)
    return (
        e21[-1] if e21 else None,
        e50[-1] if e50 else None,
        e89[-1] if e89 else None,
    )


def current_atr_state(candles: Sequence[Candle], p: SignalParams) -> ATRState | None:
    """ATR state for the last candle, or None if insufficient data."""
    atr_vals = atr_series(candles, p.atr_period)
    if not atr_vals:
        return None
    baseline = atr_baseline(atr_vals)
    if baseline is None:
        return None
    return classify_atr_state(
        atr_vals[-1], baseline, p.atr_elevated_multiplier, p.atr_extreme_multiplier
    )
