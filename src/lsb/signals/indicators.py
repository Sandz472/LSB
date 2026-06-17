"""M2 — Indicator Engine.

EMA (21/50/89), ATR(14), EMA slope, ATR-state classification, 8-way candle
classification. All functions are pure: (sequence) → value / enum. No I/O.

Spec: LSB_System_Requirements_v2.0.md §4.
"""

from __future__ import annotations

from enum import Enum, auto
from typing import Sequence

from lsb.signals import Candle


class SlopeState(Enum):
    POSITIVE = auto()
    NEGATIVE = auto()
    NEUTRAL = auto()


class ATRState(Enum):
    COMPRESSED = auto()  # < 0.75× 20-period avg ATR
    NORMAL = auto()      # 0.75× – 1.25×
    ELEVATED = auto()    # 1.25× – 2.0×
    EXTREME = auto()     # ≥ 2.0×


class CandleType(Enum):
    BULLISH = auto()
    BEARISH = auto()
    DOJI = auto()
    REJECTION_BULL = auto()
    REJECTION_BEAR = auto()
    ENGULFING_BULL = auto()
    ENGULFING_BEAR = auto()
    PIN_BAR = auto()


# Spec §4.2.2: COMPRESSED threshold is fixed at 0.75 (not a configurable param).
_ATR_COMPRESSED_MULT: float = 0.75
_ATR_BASELINE_PERIODS: int = 20   # periods for the ATR baseline SMA


def ema_series(closes: Sequence[float], period: int) -> list[float]:
    """EMA series seeded with SMA of the first `period` values.

    Returns a list aligned to closes[period-1:] — index 0 of the result
    corresponds to closes[period-1] (the SMA seed), then each subsequent
    value is the EMA of the next close.
    """
    if len(closes) < period:
        return []
    k = 2.0 / (period + 1)
    seed = sum(closes[:period]) / period
    result = [seed]
    for c in closes[period:]:
        result.append(c * k + result[-1] * (1.0 - k))
    return result


def atr_series(candles: Sequence[Candle], period: int = 14) -> list[float]:
    """Wilder-smoothed ATR series.

    Requires len(candles) ≥ period + 1.
    Result index i corresponds to candles[period + i] (i.e. the result is
    shifted forward by `period` relative to the input candles).
    """
    if len(candles) < period + 1:
        return []
    trs = [
        max(
            candles[i].high - candles[i].low,
            abs(candles[i].high - candles[i - 1].close),
            abs(candles[i].low - candles[i - 1].close),
        )
        for i in range(1, len(candles))
    ]
    if len(trs) < period:
        return []
    seed = sum(trs[:period]) / period
    result = [seed]
    for tr in trs[period:]:
        result.append((result[-1] * (period - 1) + tr) / period)
    return result


def slope_state(
    ema_vals: Sequence[float],
    lookback: int,
    threshold: float,
) -> SlopeState:
    """Slope direction from `lookback` bars ago to the last value.

    abs(delta) < threshold → NEUTRAL (spec §4.1.2: default threshold = ATR × 0.05).
    """
    if len(ema_vals) < lookback + 1:
        return SlopeState.NEUTRAL
    delta = ema_vals[-1] - ema_vals[-(lookback + 1)]
    if abs(delta) < threshold:
        return SlopeState.NEUTRAL
    return SlopeState.POSITIVE if delta > 0 else SlopeState.NEGATIVE


def atr_baseline(atr_vals: Sequence[float], n: int = _ATR_BASELINE_PERIODS) -> float | None:
    """20-period SMA of ATR values. Returns None if not enough data."""
    if len(atr_vals) < n:
        return None
    return sum(atr_vals[-n:]) / n


def classify_atr_state(
    current_atr: float,
    baseline: float,
    elevated_mult: float,
    extreme_mult: float,
) -> ATRState:
    """Classify ATR state relative to the 20-period baseline (spec §4.2.2)."""
    ratio = current_atr / baseline if baseline > 0 else 1.0
    if ratio >= extreme_mult:
        return ATRState.EXTREME
    if ratio >= elevated_mult:
        return ATRState.ELEVATED
    if ratio >= _ATR_COMPRESSED_MULT:
        return ATRState.NORMAL
    return ATRState.COMPRESSED


def classify_candle(
    candle: Candle,
    prev_candle: Candle | None,
    atr: float,
) -> CandleType:
    """8-way candle classifier per spec §4.3.

    Classification priority (first match wins):
      DOJI → PIN_BAR → ENGULFING → REJECTION → BULLISH/BEARISH
    """
    body = abs(candle.close - candle.open)
    upper_wick = candle.high - max(candle.open, candle.close)
    lower_wick = min(candle.open, candle.close) - candle.low
    total_wick = upper_wick + lower_wick

    # DOJI: body ≤ ATR × 0.05
    if body <= atr * 0.05:
        return CandleType.DOJI

    # PIN_BAR: total wick ≥ 3× body
    if body > 0 and total_wick >= 3.0 * body:
        return CandleType.PIN_BAR

    # ENGULFING: requires prior candle
    if prev_candle is not None:
        prev_body_high = max(prev_candle.open, prev_candle.close)
        prev_body_low = min(prev_candle.open, prev_candle.close)
        body_high = max(candle.open, candle.close)
        body_low = min(candle.open, candle.close)
        if body_high > prev_body_high and body_low < prev_body_low:
            return (
                CandleType.ENGULFING_BULL
                if candle.close > candle.open
                else CandleType.ENGULFING_BEAR
            )

    # REJECTION: upper wick ≥ 2× body AND lower wick ≤ 0.3× body (spec §4.3)
    if body > 0 and upper_wick >= 2.0 * body and lower_wick <= 0.3 * body:
        return (
            CandleType.REJECTION_BULL
            if candle.close > candle.open
            else CandleType.REJECTION_BEAR
        )

    return CandleType.BULLISH if candle.close > candle.open else CandleType.BEARISH
