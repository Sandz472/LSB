"""Pure, deterministic indicator functions for the C2 signal engine.

All inputs and outputs use Decimal — never bare float (CLAUDE.md rule 4).
No wall-clock, no randomness, no dict-order dependence in any computation.
"""

from __future__ import annotations
from decimal import Decimal
from typing import Sequence

_ZERO = Decimal("0")
_ONE = Decimal("1")
_TWO = Decimal("2")
_HUNDRED = Decimal("100")


# ---------------------------------------------------------------------------
# EMA (exponential moving average, SMA-seeded)
# ---------------------------------------------------------------------------

def ema(closes: Sequence[Decimal], period: int) -> list[Decimal | None]:
    """EMA with SMA seed.  Returns None for the first period-1 positions.

    Seed  = simple average of the first `period` closes.
    k     = 2 / (period + 1)  (standard multiplier)
    EMA_n = close_n * k + EMA_{n-1} * (1 - k)
    """
    if period < 1:
        raise ValueError(f"period must be >= 1, got {period}")
    n = len(closes)
    result: list[Decimal | None] = [None] * n
    if n < period:
        return result

    period_d = Decimal(str(period))
    k = _TWO / (period_d + _ONE)
    one_minus_k = _ONE - k

    seed = sum(closes[:period], _ZERO) / period_d
    result[period - 1] = seed

    for i in range(period, n):
        result[i] = closes[i] * k + result[i - 1] * one_minus_k  # type: ignore[operator]

    return result


# ---------------------------------------------------------------------------
# Wilder's ATR
# ---------------------------------------------------------------------------

def atr(candles: Sequence[dict], period: int) -> list[Decimal | None]:
    """Wilder's ATR.  Candles are dicts with Decimal keys high, low, close.

    TR[0]  = high - low  (no prior close)
    TR[i]  = max(high-low, |high-prev_close|, |low-prev_close|)
    ATR seed (index period-1) = average of first `period` TRs.
    ATR[n] = (ATR[n-1] * (period-1) + TR[n]) / period
    """
    if period < 1:
        raise ValueError(f"period must be >= 1, got {period}")
    n = len(candles)
    result: list[Decimal | None] = [None] * n
    if n < period:
        return result

    period_d = Decimal(str(period))
    period_m1 = period_d - _ONE

    # True ranges
    trs: list[Decimal] = []
    for i, c in enumerate(candles):
        h, l = c["high"], c["low"]
        if i == 0:
            trs.append(h - l)
        else:
            pc = candles[i - 1]["close"]
            trs.append(max(h - l, abs(h - pc), abs(l - pc)))

    seed = sum(trs[:period], _ZERO) / period_d
    result[period - 1] = seed
    for i in range(period, n):
        result[i] = (result[i - 1] * period_m1 + trs[i]) / period_d  # type: ignore[operator]

    return result


# ---------------------------------------------------------------------------
# Swing-high / swing-low masks
# ---------------------------------------------------------------------------

def swing_high_mask(candles: Sequence[dict], lookback: int) -> list[bool]:
    """True iff candle i has strictly the highest `high` in [i-lookback, i+lookback].

    Bars within `lookback` of either end always return False (no full context).
    """
    if lookback < 1:
        raise ValueError(f"lookback must be >= 1, got {lookback}")
    n = len(candles)
    result = [False] * n
    for i in range(lookback, n - lookback):
        h = candles[i]["high"]
        window = [candles[j]["high"] for j in range(i - lookback, i + lookback + 1) if j != i]
        if all(h > w for w in window):
            result[i] = True
    return result


def swing_low_mask(candles: Sequence[dict], lookback: int) -> list[bool]:
    """True iff candle i has strictly the lowest `low` in [i-lookback, i+lookback]."""
    if lookback < 1:
        raise ValueError(f"lookback must be >= 1, got {lookback}")
    n = len(candles)
    result = [False] * n
    for i in range(lookback, n - lookback):
        lo = candles[i]["low"]
        window = [candles[j]["low"] for j in range(i - lookback, i + lookback + 1) if j != i]
        if all(lo < w for w in window):
            result[i] = True
    return result


# ---------------------------------------------------------------------------
# Unit conversion helper
# ---------------------------------------------------------------------------

def to_price_delta(value: Decimal, unit: str, price: Decimal, pip_size: Decimal) -> Decimal:
    """Convert a threshold to an absolute price delta.

    unit='pips': delta = value * pip_size
    unit='pct' : delta = price * value / 100
    """
    if unit == "pips":
        return value * pip_size
    if unit == "pct":
        return price * value / _HUNDRED
    raise ValueError(f"Unknown unit {unit!r}; expected 'pips' or 'pct'")
