"""M5 liquidity block, sweep detection, and 5-factor score tests.

Each score factor is verified against a hand-computed expected value.
Sweep detection: 1 pass + 2 near-misses per condition.
"""

import pytest
from datetime import datetime, timezone, timedelta

from lsb.data.config import (
    BrokerCosts, InstrumentConfig, SignalParams, WalkForwardWindow,
)
from lsb.signals import Candle
from lsb.signals.indicators import ATRState
from lsb.signals.liquidity import (
    BlockResult,
    SweepResult,
    _atr_state_component,
    _close_quality_component,
    _density_component,
    _ema_proximity_component,
    _wick_extension_component,
    detect_sweep,
    identify_block,
)
from lsb.signals.structure import StructureResult, StructureState

_SIGNAL_PARAMS = SignalParams(
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
    sl_buffer_pips=2.0,
    sl_buffer_pips_elevated=4.0,
)

_EURUSD_CONFIG = InstrumentConfig(
    schema_version=4, instrument='EURUSD', display_name='Euro/USD',
    asset_class='fx', timeframes=('H1',), pip_size=0.0001, contract_size=100000,
    broker_costs=BrokerCosts(1.2, 0.05, 7.0, -0.8, -0.3),
    walkforward=WalkForwardWindow(18, 6),
    signals=_SIGNAL_PARAMS,
)


def _ts(i):
    return datetime(2024, 6, 1, i, 0, 0, tzinfo=timezone.utc)


def _candle(i, o, h, l, c):
    return Candle(ts=_ts(i), open=o, high=h, low=l, close=c, volume=1.0)


def _ascending_structure(res_level=1.2000, res_high=1.2010, res_low=1.1990, touches=3, start=0):
    return StructureResult(
        state=StructureState.ASCENDING_TRIANGLE,
        apex_proximity=0.82,
        resistance_level=res_level,
        resistance_high=res_high,
        resistance_low=res_low,
        support_level=None, support_high=None, support_low=None,
        resistance_touches=touches,
        pattern_start_idx=start,
    )


# ---------------------------------------------------------------------------
# Block identification
# ---------------------------------------------------------------------------

class TestIdentifyBlock:
    def test_valid_block_from_ascending_triangle(self):
        structure = _ascending_structure(touches=3, start=5)
        h4 = [_candle(i, 1.1, 1.2, 1.0, 1.15) for i in range(20)]
        block = identify_block(structure, h4, _EURUSD_CONFIG)
        assert block is not None
        assert block.valid is True
        assert block.upper == pytest.approx(1.2010)
        assert block.lower == pytest.approx(1.1990)
        assert block.level == pytest.approx(1.2000)
        assert block.touches == 3

    def test_block_invalid_if_too_narrow(self):
        # Width = 0.0001 = 1 pip < block_min_width_pips=5 → invalid
        structure = _ascending_structure(res_high=1.2001, res_low=1.2000)
        h4 = [_candle(i, 1.1, 1.2, 1.0, 1.15) for i in range(20)]
        block = identify_block(structure, h4, _EURUSD_CONFIG)
        assert block is not None
        assert block.valid is False

    def test_block_invalid_if_insufficient_touches(self):
        structure = _ascending_structure(touches=1)
        h4 = [_candle(i, 1.1, 1.2, 1.0, 1.15) for i in range(20)]
        block = identify_block(structure, h4, _EURUSD_CONFIG)
        assert block is not None
        assert block.valid is False

    def test_none_for_no_structure(self):
        from lsb.signals.structure import _NO_STRUCTURE
        block = identify_block(_NO_STRUCTURE, [], _EURUSD_CONFIG)
        assert block is None


# ---------------------------------------------------------------------------
# 5-factor score components — hand-computed expected values
# ---------------------------------------------------------------------------

class TestScoreComponents:
    def test_density_component_max_30(self):
        # density_raw = 100.0 → normalized = 1.0 → 30
        block = BlockResult(upper=1.2010, lower=1.1990, touches=8, age_h4=5,
                            density_raw=100.0, valid=True)
        assert _density_component(block) == 30

    def test_density_component_half(self):
        # density_raw = 50.0 → normalized = 0.5 → 15
        block = BlockResult(upper=1.2010, lower=1.1990, touches=4, age_h4=5,
                            density_raw=50.0, valid=True)
        assert _density_component(block) == 15

    def test_wick_extension_4_pips_equals_20(self):
        # 4 pips × 5 pts/pip = 20, capped at 20
        # penetration = 4 pips × pip_size = 4 × 0.0001 = 0.0004
        pts = _wick_extension_component(0.0004, pip_size=0.0001, is_crypto=False)
        assert pts == 20

    def test_wick_extension_2_pips_equals_10(self):
        pts = _wick_extension_component(0.0002, pip_size=0.0001, is_crypto=False)
        assert pts == 10

    def test_wick_extension_capped_at_20(self):
        pts = _wick_extension_component(0.001, pip_size=0.0001, is_crypto=False)
        assert pts == 20

    def test_close_quality_lower_25pct_bearish(self):
        # Bearish sweep: close near low of candle → +20
        # H=1.21, L=1.19, range=0.02; close=1.191 → position=(1.191-1.19)/0.02=0.05 → ≤0.25 → +20
        c = _candle(0, 1.205, 1.210, 1.190, 1.191)
        assert _close_quality_component(c, 'bearish') == 20

    def test_close_quality_upper_25_50pct_bearish(self):
        # close=1.196 → position=(1.196-1.19)/0.02=0.30 → 25-50% → +10
        c = _candle(0, 1.205, 1.210, 1.190, 1.196)
        assert _close_quality_component(c, 'bearish') == 10

    def test_close_quality_above_50pct_bearish(self):
        # close=1.205 → position=(1.205-1.19)/0.02=0.75 → >50% → +0
        c = _candle(0, 1.200, 1.210, 1.190, 1.205)
        assert _close_quality_component(c, 'bearish') == 0

    def test_ema_proximity_ema21_gives_15(self):
        # Sweep candle high within 3 pips (0.0003) of EMA21
        c = _candle(0, 1.200, 1.2003, 1.195, 1.199)  # high=1.2003
        pts = _ema_proximity_component(c, ema21=1.2002, ema50=1.1950,
                                        direction='bearish', pip_size=0.0001,
                                        is_crypto=False)
        assert pts == 15

    def test_ema_proximity_ema50_gives_10(self):
        c = _candle(0, 1.200, 1.2003, 1.195, 1.199)
        pts = _ema_proximity_component(c, ema21=1.1800, ema50=1.2002,
                                        direction='bearish', pip_size=0.0001,
                                        is_crypto=False)
        assert pts == 10

    def test_ema_proximity_neither_gives_0(self):
        c = _candle(0, 1.200, 1.2003, 1.195, 1.199)
        pts = _ema_proximity_component(c, ema21=1.1900, ema50=1.1800,
                                        direction='bearish', pip_size=0.0001,
                                        is_crypto=False)
        assert pts == 0

    def test_atr_compressed_gives_15(self):
        assert _atr_state_component(ATRState.COMPRESSED) == 15

    def test_atr_normal_gives_8(self):
        assert _atr_state_component(ATRState.NORMAL) == 8

    def test_atr_elevated_gives_0(self):
        assert _atr_state_component(ATRState.ELEVATED) == 0

    def test_atr_extreme_gives_0(self):
        assert _atr_state_component(ATRState.EXTREME) == 0


# ---------------------------------------------------------------------------
# Sweep detection — 1 pass + 2 near-misses
# ---------------------------------------------------------------------------

class TestDetectSweep:
    def _h1_window_with_sweep(self, bars_ago=1, wick_above=0.0006, close=1.1985):
        """Build an H1 window where bar `bars_ago` sweeps above resistance 1.2000."""
        n = 10
        candles = [_candle(i, 1.195, 1.199, 1.190, 1.195) for i in range(n - bars_ago - 1)]
        # The sweep candle: high sweeps above 1.2000 by wick_above, closes below
        sweep_c = _candle(n - bars_ago - 1,
                          1.196, 1.2000 + wick_above, 1.193, close)
        candles.append(sweep_c)
        # Bars after the sweep (back inside)
        for j in range(bars_ago):
            candles.append(_candle(n - bars_ago + j, 1.195, 1.199, 1.192, 1.196))
        return candles

    # Block for all sweep tests: level=1.2000 (the resistance line) so that a
    # 0.0006 wick reaches 1.2006, giving penetration = 0.0006 ≥ threshold of
    # 2 pips = 0.0002. upper/lower retain the full zone for width/density.
    _BLOCK = BlockResult(upper=1.2010, lower=1.1980, touches=3, age_h4=10,
                         density_raw=60.0, valid=True, level=1.2000)

    def test_valid_bear_sweep_detected(self):
        structure = _ascending_structure(res_level=1.2000, res_high=1.2000, res_low=1.1980)
        h1 = self._h1_window_with_sweep(bars_ago=1, wick_above=0.0006, close=1.1985)
        result = detect_sweep(h1, self._BLOCK, structure, _EURUSD_CONFIG,
                               ema21=1.200, ema50=1.195, atr_state=ATRState.NORMAL)
        assert result.detected is True
        assert result.direction == 'bearish'
        assert result.score > 0

    def test_near_miss_insufficient_penetration(self):
        # Wick only 1 pip above block.level (need 2 pips = 0.0002 minimum)
        structure = _ascending_structure(res_level=1.2000, res_high=1.2000, res_low=1.1980)
        h1 = self._h1_window_with_sweep(bars_ago=1, wick_above=0.0001, close=1.1985)
        result = detect_sweep(h1, self._BLOCK, structure, _EURUSD_CONFIG,
                               ema21=1.200, ema50=1.195, atr_state=ATRState.NORMAL)
        assert result.detected is False

    def test_near_miss_close_above_block(self):
        # Sufficient wick but candle closes ABOVE block.level → close_inside fails
        structure = _ascending_structure(res_level=1.2000, res_high=1.2000, res_low=1.1980)
        h1 = self._h1_window_with_sweep(bars_ago=1, wick_above=0.0006, close=1.2020)
        result = detect_sweep(h1, self._BLOCK, structure, _EURUSD_CONFIG,
                               ema21=1.200, ema50=1.195, atr_state=ATRState.NORMAL)
        assert result.detected is False

    def test_near_miss_sweep_expired(self):
        # Sweep was 4 bars ago → beyond sweep_expiry_candles=3 → expired
        structure = _ascending_structure(res_level=1.2000, res_high=1.2000, res_low=1.1980)
        h1 = self._h1_window_with_sweep(bars_ago=4, wick_above=0.0006, close=1.1985)
        result = detect_sweep(h1, self._BLOCK, structure, _EURUSD_CONFIG,
                               ema21=1.200, ema50=1.195, atr_state=ATRState.NORMAL)
        assert result.detected is False

    def test_false_sweep_filter(self):
        # Price closes ABOVE the block AFTER the sweep → false sweep, invalidated
        structure = _ascending_structure(res_level=1.2000, res_high=1.2000, res_low=1.1980)
        candles = [_candle(i, 1.195, 1.199, 1.190, 1.195) for i in range(7)]
        # Sweep candle (will be 2 bars ago in detect_sweep)
        candles.append(_candle(7, 1.196, 1.2006, 1.193, 1.1985))
        # Bar after sweep: closes ABOVE block.level → false sweep
        candles.append(_candle(8, 1.1985, 1.2025, 1.197, 1.2020))
        # Current bar
        candles.append(_candle(9, 1.2020, 1.2030, 1.200, 1.2015))
        result = detect_sweep(candles, self._BLOCK, structure, _EURUSD_CONFIG,
                               ema21=1.200, ema50=1.195, atr_state=ATRState.NORMAL)
        assert result.detected is False
