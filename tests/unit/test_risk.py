"""Risk helper unit tests — structural_stop + rr_target worked examples."""

import pytest
from datetime import datetime, timezone, timedelta

from lsb.signals import Candle
from lsb.signals.indicators import ATRState
from lsb.signals.risk import structural_stop, rr_target


def _c(i: int, price: float, high_add: float = 0.001, low_sub: float = 0.001) -> Candle:
    ts = datetime(2024, 1, 1, tzinfo=timezone.utc) + timedelta(hours=i)
    return Candle(ts=ts, open=price, high=price + high_add, low=price - low_sub,
                  close=price, volume=1.0)


# Spec values: EURUSD pip_size=0.0001
PIP = 0.0001


class TestStructuralStop:
    def test_short_normal_atr(self):
        # rejection candle high = 1.1025; buffer = 2 pips = 0.0002
        candle = Candle(
            ts=datetime(2024, 1, 1, tzinfo=timezone.utc),
            open=1.1010, high=1.1025, low=1.0995, close=1.1000, volume=1.0,
        )
        from lsb.data.config import SignalParams
        # minimal params object — only fields structural_stop uses
        p = _make_params(sl_buffer_pips=2.0, sl_buffer_pips_elevated=4.0)
        stop = structural_stop(candle, 'short', ATRState.NORMAL, p, PIP)
        assert stop == pytest.approx(1.1025 + 2 * PIP)

    def test_short_elevated_atr_doubles_buffer(self):
        candle = Candle(
            ts=datetime(2024, 1, 1, tzinfo=timezone.utc),
            open=1.1010, high=1.1025, low=1.0995, close=1.1000, volume=1.0,
        )
        p = _make_params(sl_buffer_pips=2.0, sl_buffer_pips_elevated=4.0)
        stop = structural_stop(candle, 'short', ATRState.ELEVATED, p, PIP)
        assert stop == pytest.approx(1.1025 + 4 * PIP)

    def test_long_normal_atr(self):
        # rejection candle low = 1.0995; buffer = 2 pips below
        candle = Candle(
            ts=datetime(2024, 1, 1, tzinfo=timezone.utc),
            open=1.1010, high=1.1025, low=1.0995, close=1.1010, volume=1.0,
        )
        p = _make_params(sl_buffer_pips=2.0, sl_buffer_pips_elevated=4.0)
        stop = structural_stop(candle, 'long', ATRState.NORMAL, p, PIP)
        assert stop == pytest.approx(1.0995 - 2 * PIP)

    def test_none_atr_state_returns_none(self):
        candle = Candle(
            ts=datetime(2024, 1, 1, tzinfo=timezone.utc),
            open=1.1000, high=1.1010, low=1.0990, close=1.1000, volume=1.0,
        )
        p = _make_params(sl_buffer_pips=2.0, sl_buffer_pips_elevated=4.0)
        assert structural_stop(candle, 'short', None, p, PIP) is None


class TestRRTarget:
    def test_short_2_5r_floor(self):
        # entry=1.1000, stop=1.1020 → risk=20 pips
        # 2.5R target = 1.1000 - 2.5×0.0020 = 1.0950
        # ATR=0.0015 → ATR×3=0.0045 (< 2×risk of 0.004, so < 2.5R) → not a valid candidate
        # only 2.5R floor qualifies → target=1.0950, rr=2.5
        entry, stop = 1.1000, 1.1020
        p = _make_params(min_rr_ratio=2.5, swing_lookback=2)
        window = [_c(i, 1.1010 - i * 0.0001) for i in range(50)]  # no clear swing lows beyond 2.5R
        target, rr = rr_target(entry, stop, window, atr=0.0015, direction='short', p=p)
        assert rr == pytest.approx(2.5)
        assert target == pytest.approx(1.0950)

    def test_short_rr_exactly_at_minimum(self):
        entry, stop = 1.2000, 1.2030   # risk = 30 pips
        p = _make_params(min_rr_ratio=2.5, swing_lookback=2)
        window = [_c(i, 1.2015 - i * 0.0001) for i in range(50)]
        target, rr = rr_target(entry, stop, window, atr=0.002, direction='short', p=p)
        assert rr >= 2.5

    def test_long_2_5r_floor(self):
        # entry=1.1000, stop=1.0980 → risk=20 pips
        # 2.5R target = 1.1000 + 2.5×0.0020 = 1.1050
        entry, stop = 1.1000, 1.0980
        p = _make_params(min_rr_ratio=2.5, swing_lookback=2)
        window = [_c(i, 1.0990 + i * 0.0001) for i in range(50)]
        target, rr = rr_target(entry, stop, window, atr=0.0015, direction='long', p=p)
        assert rr == pytest.approx(2.5)
        assert target == pytest.approx(1.1050)

    def test_zero_risk_returns_zero_rr(self):
        p = _make_params(min_rr_ratio=2.5, swing_lookback=2)
        window = [_c(i, 1.1000) for i in range(50)]
        _, rr = rr_target(1.1000, 1.1000, window, atr=0.001, direction='short', p=p)
        assert rr == 0.0

    def test_atr3_used_when_closer_than_2_5r_floor(self):
        # entry=1.1000, stop=1.1005 → risk=5 pips
        # 2.5R = entry - 0.00125 = 1.09875
        # ATR×3 = 3×0.001 = 0.003 → target = 1.097 (< 2.5R floor of 1.09875)
        # So ATR×3 target IS further (more negative) than 2.5R floor.
        # 2.5R is closer → target = 1.09875
        entry, stop = 1.1000, 1.1005
        p = _make_params(min_rr_ratio=2.5, swing_lookback=2)
        window = [_c(i, 1.0990 - i * 0.0001) for i in range(50)]
        target, rr = rr_target(entry, stop, window, atr=0.001, direction='short', p=p)
        assert rr == pytest.approx(2.5)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_params(**kwargs):
    """Build a minimal fake SignalParams with only the fields risk.py needs."""
    from lsb.data.config import SignalParams
    defaults = dict(
        ema_short_period=21, ema_mid_period=50, ema_long_period=89,
        ema_slope_lookback=3, atr_period=14,
        atr_elevated_multiplier=1.25, atr_extreme_multiplier=2.0,
        ema_compression_atr_mult=0.10, slope_threshold_atr_mult=0.05,
        triangle_min_candles=8, triangle_max_candles=60,
        triangle_flat_tolerance_pct=0.005, swing_lookback=2,
        apex_proximity_min=0.75, apex_proximity_max=0.95,
        block_min_touches=2, block_min_width_pips=5.0,
        sweep_penetration_pips=2.0, sweep_expiry_candles=3, sweep_score_min=50,
        rejection_wick_body_mult=2.0,
        allowed_atr_states=('NORMAL', 'ELEVATED'),
        max_spread_pips=3.0,
        session_edge_buffer_min=30,
        min_rr_ratio=2.5,
        sl_buffer_pips=2.0, sl_buffer_pips_elevated=4.0,
    )
    defaults.update(kwargs)
    return SignalParams(**defaults)
