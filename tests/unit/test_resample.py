"""H1 → H4 resample tests.

Property test: resampled OHLC reconciles exactly with source H1 candles.
Determinism: same H1 input always produces identical H4 output.
"""

import pytest
from datetime import datetime, timezone, timedelta

from lsb.signals import Candle
from lsb.signals.resample import resample_h1_to_h4


def _h1(hour: int, o, h, l, c, vol=100.0):
    ts = datetime(2024, 1, 2, hour, 0, 0, tzinfo=timezone.utc)
    return Candle(ts=ts, open=o, high=h, low=l, close=c, volume=vol)


class TestResampleBasic:
    def test_four_h1_bars_become_one_h4(self):
        h1 = [
            _h1(0,  1.10, 1.15, 1.08, 1.12, 10),
            _h1(1,  1.12, 1.18, 1.11, 1.16, 20),
            _h1(2,  1.16, 1.20, 1.14, 1.17, 15),
            _h1(3,  1.17, 1.22, 1.15, 1.19, 25),
        ]
        h4 = resample_h1_to_h4(h1)
        assert len(h4) == 1
        bar = h4[0]
        assert bar.open == pytest.approx(1.10)
        assert bar.high == pytest.approx(1.22)
        assert bar.low == pytest.approx(1.08)
        assert bar.close == pytest.approx(1.19)
        assert bar.volume == pytest.approx(70.0)

    def test_eight_h1_bars_become_two_h4(self):
        bars_00_03 = [_h1(h, 1.10, 1.20, 1.05, 1.15) for h in range(4)]
        bars_04_07 = [_h1(h, 1.15, 1.25, 1.10, 1.20) for h in range(4, 8)]
        h4 = resample_h1_to_h4(bars_00_03 + bars_04_07)
        assert len(h4) == 2
        assert h4[0].open == pytest.approx(1.10)
        assert h4[1].open == pytest.approx(1.15)

    def test_ohlc_reconciles_with_source(self):
        """H = max(H1 highs), L = min(H1 lows), O = first, C = last."""
        h1 = [
            _h1(8,  2.00, 2.10, 1.95, 2.05),
            _h1(9,  2.05, 2.20, 2.00, 2.15),
            _h1(10, 2.15, 2.25, 2.10, 2.18),
            _h1(11, 2.18, 2.30, 2.05, 2.28),
        ]
        h4 = resample_h1_to_h4(h1)
        assert len(h4) == 1
        bar = h4[0]
        assert bar.open == pytest.approx(2.00)   # first H1 open
        assert bar.high == pytest.approx(2.30)   # max of highs
        assert bar.low == pytest.approx(1.95)    # min of lows
        assert bar.close == pytest.approx(2.28)  # last H1 close

    def test_incomplete_trailing_bar_is_dropped(self):
        # Hours 0-3 = complete H4 bar; hour 4 = start of next bar (incomplete)
        h1 = [_h1(h, 1.0, 1.1, 0.9, 1.05) for h in range(5)]
        h4 = resample_h1_to_h4(h1)
        assert len(h4) == 1

    def test_empty_input(self):
        assert resample_h1_to_h4([]) == []

    def test_deterministic_same_output_twice(self):
        h1 = [_h1(h, 1.0 + h * 0.001, 1.1 + h * 0.001, 0.9, 1.05) for h in range(8)]
        assert resample_h1_to_h4(h1) == resample_h1_to_h4(h1)

    def test_volume_is_sum(self):
        h1 = [_h1(h, 1.0, 1.1, 0.9, 1.0, vol=float(10 * (h + 1))) for h in range(4)]
        h4 = resample_h1_to_h4(h1)
        assert h4[0].volume == pytest.approx(10 + 20 + 30 + 40)
