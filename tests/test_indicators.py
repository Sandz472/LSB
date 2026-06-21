"""Unit tests for signal indicators.

Each function is tested against hand-computed reference values.
All computations use Decimal — these tests also assert determinism.
"""

from __future__ import annotations
from decimal import Decimal
from datetime import datetime, timezone, timedelta
import pytest

from lsb.signal.indicators import ema, atr, swing_high_mask, swing_low_mask, to_price_delta


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def D(s: str) -> Decimal:
    return Decimal(s)


def _candles(highs, lows, closes) -> list[dict]:
    base = datetime(2024, 1, 1, tzinfo=timezone.utc)
    return [
        {"ts": base + timedelta(hours=i),
         "open": D(str(c)), "high": D(str(h)), "low": D(str(l)),
         "close": D(str(c)), "volume": D("1000")}
        for i, (h, l, c) in enumerate(zip(highs, lows, closes))
    ]


# ---------------------------------------------------------------------------
# EMA
# ---------------------------------------------------------------------------

class TestEma:
    def test_length_shorter_than_period_all_none(self):
        result = ema([D("1"), D("2")], period=3)
        assert result == [None, None]

    def test_seed_is_sma_of_first_period_closes(self):
        # EMA(3) on [1, 2, 3, 4, 5]:
        # seed at index 2 = (1+2+3)/3 = 2.0
        closes = [D("1"), D("2"), D("3"), D("4"), D("5")]
        result = ema(closes, 3)
        assert result[0] is None
        assert result[1] is None
        assert result[2] == D("2")   # SMA(1,2,3)/3

    def test_ema_values_hand_computed(self):
        # k = 2/(3+1) = 0.5
        # EMA[3] = 4*0.5 + 2*0.5 = 3.0
        # EMA[4] = 5*0.5 + 3*0.5 = 4.0
        closes = [D("1"), D("2"), D("3"), D("4"), D("5")]
        result = ema(closes, 3)
        assert result[3] == D("3")
        assert result[4] == D("4")

    def test_period_1_equals_close(self):
        closes = [D("1.1"), D("2.2"), D("3.3")]
        result = ema(closes, 1)
        assert result == [D("1.1"), D("2.2"), D("3.3")]

    def test_determinism(self):
        closes = [D(str(i)) for i in range(30)]
        r1 = ema(closes, 10)
        r2 = ema(closes, 10)
        assert r1 == r2

    def test_invalid_period(self):
        with pytest.raises(ValueError):
            ema([D("1")], 0)


# ---------------------------------------------------------------------------
# ATR (Wilder's)
# ---------------------------------------------------------------------------

class TestAtr:
    def test_fewer_bars_than_period_all_none(self):
        candles = _candles([2], [1], [1.5])
        assert atr(candles, 3) == [None]

    def test_seed_is_average_of_first_period_trs(self):
        # TR[0] = H-L = 1.0 (no prev close)
        # TR[1] = max(2,|3-1.5|,|1-1.5|) = max(2,1.5,0.5) = 2.0
        # seed = (1+2)/2 = 1.5
        candles = _candles([2, 3], [1, 1], [1.5, 2.5])
        result = atr(candles, 2)
        assert result[0] is None
        assert result[1] == D("1.5")

    def test_wilder_smoothing_hand_computed(self):
        # Continuing: TR[2] = max(4-2,|4-2.5|,|2-2.5|) = max(2,1.5,0.5) = 2.0
        # ATR[2] = (1.5*1 + 2.0)/2 = 1.75
        candles = _candles([2, 3, 4], [1, 1, 2], [1.5, 2.5, 3.5])
        result = atr(candles, 2)
        assert result[2] == D("1.75")

    def test_determinism(self):
        candles = _candles(
            [i + 0.5 for i in range(20)],
            [i - 0.5 for i in range(20)],
            [float(i) for i in range(20)],
        )
        r1 = atr(candles, 5)
        r2 = atr(candles, 5)
        assert r1 == r2


# ---------------------------------------------------------------------------
# Swing masks
# ---------------------------------------------------------------------------

class TestSwingMasks:
    def _simple_candles(self, highs, lows):
        return _candles(highs, lows, [(h + l) / 2 for h, l in zip(highs, lows)])

    def test_swing_high_detected(self):
        # highs: 1, 3, 5, 4, 2  — index 2 is the swing high with lookback=2
        candles = self._simple_candles([1, 3, 5, 4, 2], [0, 2, 4, 3, 1])
        mask = swing_high_mask(candles, 2)
        assert mask == [False, False, True, False, False]

    def test_swing_high_not_strict(self):
        # Tie at the peak — not strictly highest
        candles = self._simple_candles([1, 5, 5, 4, 2], [0, 4, 4, 3, 1])
        mask = swing_high_mask(candles, 2)
        assert not any(mask)

    def test_swing_low_detected(self):
        # lows: 5, 3, 1, 2, 4  — index 2 is the swing low with lookback=2
        candles = self._simple_candles([6, 4, 2, 3, 5], [5, 3, 1, 2, 4])
        mask = swing_low_mask(candles, 2)
        assert mask == [False, False, True, False, False]

    def test_boundary_bars_always_false(self):
        candles = self._simple_candles([1, 5, 3, 5, 1], [0, 4, 2, 4, 0])
        mask = swing_high_mask(candles, 2)
        assert mask[0] is False
        assert mask[1] is False
        assert mask[-1] is False
        assert mask[-2] is False

    def test_invalid_lookback(self):
        candles = self._simple_candles([1, 2], [0, 1])
        with pytest.raises(ValueError):
            swing_high_mask(candles, 0)


# ---------------------------------------------------------------------------
# to_price_delta
# ---------------------------------------------------------------------------

class TestToPriceDelta:
    def test_pips(self):
        delta = to_price_delta(D("3"), "pips", D("1.2500"), D("0.0001"))
        assert delta == D("0.0003")

    def test_pct(self):
        # 0.03% of 50000 = 15
        delta = to_price_delta(D("0.03"), "pct", D("50000"), D("0.01"))
        assert delta == D("15")

    def test_unknown_unit(self):
        with pytest.raises(ValueError):
            to_price_delta(D("1"), "bps", D("1"), D("0.0001"))
