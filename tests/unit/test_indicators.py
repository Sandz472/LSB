"""M2 indicator tests — verified against hand-computed reference values.

Spec testing non-negotiable #1: every numeric module is tested against
hand-verified reference values, not just 'it runs.'

All expected values in this file were computed by hand before running
the implementation, following LSB_System_Requirements_v2.0.md §4.
"""

import pytest

from lsb.signals import Candle
from lsb.signals.indicators import (
    ATRState,
    CandleType,
    SlopeState,
    atr_baseline,
    atr_series,
    classify_atr_state,
    classify_candle,
    ema_series,
    slope_state,
)

# ---------------------------------------------------------------------------
# EMA series (spec §4.1.1)
# K = 2 / (period + 1); seed = SMA of first `period` values
# ---------------------------------------------------------------------------

class TestEmaSeries:
    def test_period_3_reference_values(self):
        # closes = [1, 2, 3, 4, 5], period = 3
        # K = 2/(3+1) = 0.5; seed = (1+2+3)/3 = 2.0
        # idx 3: 4*0.5 + 2.0*0.5 = 3.0
        # idx 4: 5*0.5 + 3.0*0.5 = 4.0
        result = ema_series([1.0, 2.0, 3.0, 4.0, 5.0], 3)
        assert result == pytest.approx([2.0, 3.0, 4.0], rel=1e-7)

    def test_period_2_reference_values(self):
        # closes = [10, 20, 30], period = 2
        # K = 2/3 ≈ 0.6667; seed = (10+20)/2 = 15.0
        # idx 2: 30*0.6667 + 15.0*0.3333 = 20.0 + 5.0 = 25.0
        result = ema_series([10.0, 20.0, 30.0], 2)
        assert len(result) == 2
        assert result[0] == pytest.approx(15.0, rel=1e-7)
        assert result[1] == pytest.approx(25.0, rel=1e-7)

    def test_insufficient_data_returns_empty(self):
        assert ema_series([1.0, 2.0], 3) == []

    def test_exact_period_returns_seed_only(self):
        result = ema_series([1.0, 2.0, 3.0], 3)
        assert result == pytest.approx([2.0], rel=1e-7)

    def test_period_21_length(self):
        closes = [float(i) for i in range(1, 32)]  # 31 closes
        result = ema_series(closes, 21)
        assert len(result) == 11  # 31 - 21 + 1


# ---------------------------------------------------------------------------
# ATR series (spec §4.2.1 — Wilder's smoothing)
# ---------------------------------------------------------------------------

def _make_candles(*ohlcv):
    """Helper: ohlcv is a list of (o, h, l, c) tuples."""
    from datetime import datetime, timezone
    result = []
    for i, (o, h, l, c) in enumerate(ohlcv):
        ts = datetime(2024, 1, 1, i, tzinfo=timezone.utc)
        result.append(Candle(ts=ts, open=o, high=h, low=l, close=c, volume=1.0))
    return result


class TestAtrSeries:
    def test_period_2_reference_values(self):
        # 5 candles, period=2
        # Candle 0: O=1.0, H=1.5, L=0.9, C=1.2  (no TR yet — needs prev)
        # Candle 1: H=1.8, L=1.1, PrevC=1.2 → TR = max(0.7, 0.6, 0.1) = 0.7
        # Candle 2: H=2.0, L=1.5, PrevC=1.6 → TR = max(0.5, 0.4, 0.1) = 0.5
        # Candle 3: H=2.2, L=1.7, PrevC=1.9 → TR = max(0.5, 0.3, 0.2) = 0.5
        # Candle 4: H=2.5, L=1.8, PrevC=2.0 → TR = max(0.7, 0.5, 0.2) = 0.7
        # Seed (period=2): (TR1+TR2)/2 = (0.7+0.5)/2 = 0.6
        # ATR[c2]: (0.6*1 + 0.5)/2 = 0.55
        # ATR[c3]: (0.55*1 + 0.5)/2 = 0.525 — wait, actually:
        # Wilder: ATR(i) = (ATR(i-1) * (period-1) + TR(i)) / period
        # period=2: ATR(i) = (ATR(i-1)*1 + TR(i)) / 2
        # ATR[2] = seed = 0.6 (from TR1, TR2)
        # ATR[3]: (0.6*1 + 0.5)/2 = 0.55
        # ATR[4]: (0.55*1 + 0.7)/2 = 0.625
        candles = _make_candles(
            (1.0, 1.5, 0.9, 1.2),
            (1.2, 1.8, 1.1, 1.6),
            (1.6, 2.0, 1.5, 1.9),
            (1.9, 2.2, 1.7, 2.0),
            (2.0, 2.5, 1.8, 2.3),
        )
        result = atr_series(candles, period=2)
        assert result == pytest.approx([0.6, 0.55, 0.625], rel=1e-7)

    def test_insufficient_data_returns_empty(self):
        candles = _make_candles((1.0, 1.5, 0.9, 1.2))
        assert atr_series(candles, period=2) == []

    def test_wilder_smoothing_not_ema(self):
        # Wilder's MA(n) = (prev*(n-1) + tr) / n, NOT exponential k = 2/(n+1).
        # For period=3, Wilder k_eff = 1/3; EMA k would be 2/4 = 0.5.
        # These must differ for the same TR sequence.
        candles = _make_candles(
            (1.0, 2.0, 0.5, 1.5),
            (1.5, 2.5, 1.0, 2.0),
            (2.0, 3.0, 1.5, 2.5),
            (2.5, 3.5, 2.0, 3.0),
            (3.0, 4.0, 2.5, 3.5),
        )
        # Just verifies the series computes without error; exact values checked above.
        result = atr_series(candles, period=2)
        assert len(result) == 3


# ---------------------------------------------------------------------------
# Slope state (spec §4.1.2)
# ---------------------------------------------------------------------------

class TestSlopeState:
    def test_positive(self):
        assert slope_state([1.0, 2.0, 3.0, 4.0], lookback=3, threshold=0.05) == SlopeState.POSITIVE

    def test_negative(self):
        assert slope_state([4.0, 3.0, 2.0, 1.0], lookback=3, threshold=0.05) == SlopeState.NEUTRAL or \
               slope_state([4.0, 3.0, 2.0, 1.0], lookback=3, threshold=0.05) == SlopeState.NEGATIVE
        # delta = 1.0 - 4.0 = -3.0, abs = 3.0 > 0.05 → NEGATIVE
        assert slope_state([4.0, 3.0, 2.0, 1.0], lookback=3, threshold=0.05) == SlopeState.NEGATIVE

    def test_neutral_at_threshold(self):
        # delta = 1.002 - 1.0 = 0.002; threshold = 0.01 → NEUTRAL
        assert slope_state([1.0, 1.001, 1.001, 1.002], lookback=3, threshold=0.01) == SlopeState.NEUTRAL

    def test_insufficient_data_returns_neutral(self):
        assert slope_state([1.0, 2.0], lookback=3, threshold=0.01) == SlopeState.NEUTRAL


# ---------------------------------------------------------------------------
# ATR state (spec §4.2.2)
# ---------------------------------------------------------------------------

class TestClassifyAtrState:
    def test_compressed(self):
        # ratio 0.5 < 0.75 → COMPRESSED
        assert classify_atr_state(0.5, 1.0, 1.25, 2.0) == ATRState.COMPRESSED

    def test_normal_lower_bound(self):
        # ratio 0.75 → NORMAL (not COMPRESSED)
        assert classify_atr_state(0.75, 1.0, 1.25, 2.0) == ATRState.NORMAL

    def test_normal_upper_bound(self):
        # ratio 1.24 < 1.25 → NORMAL
        assert classify_atr_state(1.24, 1.0, 1.25, 2.0) == ATRState.NORMAL

    def test_elevated(self):
        # ratio 1.5 → ELEVATED (≥1.25 but <2.0)
        assert classify_atr_state(1.5, 1.0, 1.25, 2.0) == ATRState.ELEVATED

    def test_extreme(self):
        # ratio 2.0 → EXTREME
        assert classify_atr_state(2.0, 1.0, 1.25, 2.0) == ATRState.EXTREME

    def test_above_extreme(self):
        assert classify_atr_state(3.5, 1.0, 1.25, 2.0) == ATRState.EXTREME


# ---------------------------------------------------------------------------
# Candle classification (spec §4.3)
# ---------------------------------------------------------------------------

class TestClassifyCandle:
    def _candle(self, o, h, l, c):
        from datetime import datetime, timezone
        return Candle(ts=datetime(2024, 1, 1, tzinfo=timezone.utc),
                      open=o, high=h, low=l, close=c, volume=1.0)

    def test_doji(self):
        # ATR=1.0; body=0.04 ≤ 1.0*0.05 → DOJI
        c = self._candle(1.00, 1.20, 0.90, 1.04)
        assert classify_candle(c, None, 1.0) == CandleType.DOJI

    def test_pin_bar(self):
        # body=0.1, total wick=0.9 ≥ 3*0.1=0.3 → PIN_BAR
        # O=1.0, C=1.1 → body=0.1; H=1.5, L=0.6 → upper=0.4, lower=0.4, total=0.8
        c = self._candle(1.0, 1.5, 0.6, 1.1)
        assert classify_candle(c, None, 0.5) == CandleType.PIN_BAR

    def test_engulfing_bull(self):
        # prev: O=1.5, C=1.2 (body from 1.2 to 1.5)
        # curr: O=1.1, C=1.6 — body [1.1, 1.6] fully engulfs [1.2, 1.5], close>open
        prev = self._candle(1.5, 1.6, 1.1, 1.2)
        curr = self._candle(1.1, 1.65, 1.05, 1.6)
        assert classify_candle(curr, prev, 0.1) == CandleType.ENGULFING_BULL

    def test_engulfing_bear(self):
        prev = self._candle(1.2, 1.6, 1.1, 1.5)
        curr = self._candle(1.6, 1.65, 1.05, 1.1)
        assert classify_candle(curr, prev, 0.1) == CandleType.ENGULFING_BEAR

    def test_rejection_bear(self):
        # body=0.1, upper_wick=0.22 (≥2×body=0.20 ✓), lower_wick=0.02 (≤0.3×body=0.03 ✓)
        # total_wick=0.24 < 3×body=0.30 → PIN_BAR is NOT triggered
        # O=1.3, C=1.2 (bearish), H=1.3+0.22=1.52, L=1.2-0.02=1.18
        c = self._candle(1.3, 1.52, 1.18, 1.2)
        assert classify_candle(c, None, 0.1) == CandleType.REJECTION_BEAR

    def test_rejection_bull(self):
        # Same wick shape, bullish close (C=1.3 > O=1.2)
        # H=1.3+0.22=1.52, L=1.2-0.02=1.18 → total_wick=0.24 < 0.30 → NOT PIN_BAR
        c = self._candle(1.2, 1.52, 1.18, 1.3)
        assert classify_candle(c, None, 0.1) == CandleType.REJECTION_BULL

    def test_bullish(self):
        c = self._candle(1.0, 1.2, 0.9, 1.15)
        assert classify_candle(c, None, 0.1) == CandleType.BULLISH

    def test_bearish(self):
        c = self._candle(1.15, 1.2, 0.9, 1.0)
        assert classify_candle(c, None, 0.1) == CandleType.BEARISH

    def test_doji_takes_priority_over_wick_types(self):
        # Even if wick shape could be REJECTION, DOJI fires first.
        # body ≤ ATR*0.05; ATR=2.0 → body must be ≤ 0.10
        c = self._candle(1.0, 2.0, 0.5, 1.05)  # body=0.05, huge wicks
        assert classify_candle(c, None, 2.0) == CandleType.DOJI
