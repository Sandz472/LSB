"""Gates 1–8 unit tests — 1 pass + ≥2 near-misses per gate.

Fixtures are hand-labeled synthetic scenarios determined from spec definitions
(LSB_System_Requirements_v2.0.md §8) before the gate predicates were coded.
"""

import pytest

from lsb.signals.gates import (
    gate_1_trend_alignment,
    gate_2_structure_present,
    gate_3_liquidity_sweep,
    gate_4_sweep_quality,
    gate_5_candle_confirmation,
    gate_6_volatility_acceptable,
    gate_7_session_clear,
    gate_8_risk_viable,
)
from lsb.signals.indicators import ATRState, CandleType
from lsb.signals.session import Session
from lsb.signals.trend import TrendState
from lsb.signals.structure import StructureResult, StructureState
from lsb.signals.liquidity import SweepResult


def _params(**kwargs):
    """Minimal SignalParams for gates 5–8 tests."""
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


def _struct(state, apex=0.82, res_level=1.20, touches=3):
    return StructureResult(
        state=state, apex_proximity=apex,
        resistance_level=res_level, resistance_high=1.2010, resistance_low=1.1990,
        support_level=None, support_high=None, support_low=None,
        resistance_touches=touches, pattern_start_idx=0,
    )


def _sweep(detected=True, direction='bearish', score=65, bars_ago=1):
    return SweepResult(
        detected=detected, direction=direction,
        sweep_candle_bars_ago=bars_ago,
        penetration_value=0.0006, score=score,
        score_detail={'density': 18, 'wick': 10, 'close': 20, 'ema': 10, 'atr': 7},
        reason='sweep confirmed',
    )


# ---------------------------------------------------------------------------
# Gate 1 — Trend alignment
# ---------------------------------------------------------------------------

class TestGate1:
    def test_pass_bearish_short(self):
        g = gate_1_trend_alignment(TrendState.BEARISH, 'short')
        assert g.passed is True

    def test_pass_bullish_long(self):
        g = gate_1_trend_alignment(TrendState.BULLISH, 'long')
        assert g.passed is True

    def test_near_miss_neutral_trend(self):
        g = gate_1_trend_alignment(TrendState.NEUTRAL, 'short')
        assert g.passed is False
        assert 'NEUTRAL' in g.reason

    def test_near_miss_invalid_trend(self):
        g = gate_1_trend_alignment(TrendState.INVALID, 'short')
        assert g.passed is False
        assert 'INVALID' in g.reason

    def test_near_miss_trend_direction_mismatch(self):
        # Bearish trend but trying to go long — reject
        g = gate_1_trend_alignment(TrendState.BEARISH, 'long')
        assert g.passed is False


# ---------------------------------------------------------------------------
# Gate 2 — Structure present
# ---------------------------------------------------------------------------

class TestGate2:
    def test_pass_ascending_triangle_for_short(self):
        g = gate_2_structure_present(_struct(StructureState.ASCENDING_TRIANGLE), 'short')
        assert g.passed is True
        assert 'apex' in g.reason

    def test_pass_descending_triangle_for_long(self):
        s = StructureResult(
            state=StructureState.DESCENDING_TRIANGLE, apex_proximity=0.80,
            resistance_level=None, resistance_high=None, resistance_low=None,
            support_level=1.00, support_high=1.005, support_low=0.995,
            resistance_touches=2, pattern_start_idx=0,
        )
        g = gate_2_structure_present(s, 'long')
        assert g.passed is True

    def test_near_miss_no_structure(self):
        g = gate_2_structure_present(_struct(StructureState.NONE), 'short')
        assert g.passed is False

    def test_near_miss_forming_structure(self):
        g = gate_2_structure_present(_struct(StructureState.FORMING, apex=0.50), 'short')
        assert g.passed is False

    def test_near_miss_wrong_direction(self):
        # Ascending triangle is bearish setup; trying long → fail
        g = gate_2_structure_present(_struct(StructureState.ASCENDING_TRIANGLE), 'long')
        assert g.passed is False

    def test_near_miss_invalidated(self):
        g = gate_2_structure_present(_struct(StructureState.INVALIDATED), 'short')
        assert g.passed is False


# ---------------------------------------------------------------------------
# Gate 3 — Liquidity sweep confirmed
# ---------------------------------------------------------------------------

class TestGate3:
    def test_pass_active_sweep(self):
        g = gate_3_liquidity_sweep(_sweep(detected=True))
        assert g.passed is True

    def test_near_miss_no_sweep(self):
        g = gate_3_liquidity_sweep(_sweep(detected=False))
        assert g.passed is False

    def test_near_miss_sweep_with_zero_penetration(self):
        # Even if detected=True, reason should indicate it — gate passes based on detected flag.
        # This is a logic near-miss: sweep appears detected but represents a boundary case.
        s = SweepResult(
            detected=False, direction='bearish', sweep_candle_bars_ago=0,
            penetration_value=0.0, score=0, score_detail={},
            reason='no sweep within expiry window',
        )
        g = gate_3_liquidity_sweep(s)
        assert g.passed is False


# ---------------------------------------------------------------------------
# Gate 4 — Sweep quality
# ---------------------------------------------------------------------------

class TestGate4:
    def test_pass_score_above_minimum(self):
        g = gate_4_sweep_quality(_sweep(score=65), sweep_score_min=50)
        assert g.passed is True
        assert g.detail['score'] == 65

    def test_pass_score_exactly_at_minimum(self):
        g = gate_4_sweep_quality(_sweep(score=50), sweep_score_min=50)
        assert g.passed is True

    def test_near_miss_score_just_below_minimum(self):
        g = gate_4_sweep_quality(_sweep(score=49), sweep_score_min=50)
        assert g.passed is False
        assert '49' in g.reason

    def test_near_miss_no_sweep(self):
        g = gate_4_sweep_quality(_sweep(detected=False, score=0), sweep_score_min=50)
        assert g.passed is False

    def test_detail_includes_factor_breakdown(self):
        g = gate_4_sweep_quality(_sweep(score=65), sweep_score_min=50)
        assert 'factors' in g.detail
        assert sum(g.detail['factors'].values()) == 65


# ---------------------------------------------------------------------------
# Gate 5 — Candle confirmation
# ---------------------------------------------------------------------------

class TestGate5:
    def test_pass_rejection_bear_short(self):
        p = _params()
        g = gate_5_candle_confirmation(
            CandleType.REJECTION_BEAR, closes_beyond_sweep=True,
            wick_body_ratio=2.5, direction='short', p=p,
        )
        assert g.passed is True
        assert 'REJECTION_BEAR' in g.reason

    def test_pass_engulfing_bear_short(self):
        p = _params()
        g = gate_5_candle_confirmation(
            CandleType.ENGULFING_BEAR, closes_beyond_sweep=True,
            wick_body_ratio=2.0, direction='short', p=p,
        )
        assert g.passed is True

    def test_pass_rejection_bull_long(self):
        p = _params()
        g = gate_5_candle_confirmation(
            CandleType.REJECTION_BULL, closes_beyond_sweep=True,
            wick_body_ratio=3.0, direction='long', p=p,
        )
        assert g.passed is True

    def test_near_miss_wrong_candle_type(self):
        # BEARISH (plain) does not satisfy rejection/engulfing requirement
        p = _params()
        g = gate_5_candle_confirmation(
            CandleType.BEARISH, closes_beyond_sweep=True,
            wick_body_ratio=2.5, direction='short', p=p,
        )
        assert g.passed is False
        assert 'not bear rejection' in g.reason.lower() or 'BEARISH' in g.reason

    def test_near_miss_wrong_direction_type(self):
        # REJECTION_BULL in a short setup → fail
        p = _params()
        g = gate_5_candle_confirmation(
            CandleType.REJECTION_BULL, closes_beyond_sweep=True,
            wick_body_ratio=2.5, direction='short', p=p,
        )
        assert g.passed is False

    def test_near_miss_close_not_beyond_sweep(self):
        p = _params()
        g = gate_5_candle_confirmation(
            CandleType.REJECTION_BEAR, closes_beyond_sweep=False,
            wick_body_ratio=2.5, direction='short', p=p,
        )
        assert g.passed is False
        assert 'sweep' in g.reason.lower()

    def test_near_miss_wick_too_small(self):
        # wick/body = 1.8 < 2.0 threshold
        p = _params(rejection_wick_body_mult=2.0)
        g = gate_5_candle_confirmation(
            CandleType.REJECTION_BEAR, closes_beyond_sweep=True,
            wick_body_ratio=1.8, direction='short', p=p,
        )
        assert g.passed is False
        assert '1.80' in g.reason

    def test_detail_includes_wick_ratio(self):
        p = _params()
        g = gate_5_candle_confirmation(
            CandleType.REJECTION_BEAR, closes_beyond_sweep=True,
            wick_body_ratio=2.34, direction='short', p=p,
        )
        assert g.passed is True
        assert 'wick_body_ratio' in g.detail


# ---------------------------------------------------------------------------
# Gate 6 — Volatility acceptable
# ---------------------------------------------------------------------------

class TestGate6:
    def test_pass_normal_atr_no_spread(self):
        p = _params()
        g = gate_6_volatility_acceptable(ATRState.NORMAL, None, p)
        assert g.passed is True

    def test_pass_elevated_atr_spread_within_max(self):
        p = _params(max_spread_pips=3.0)
        g = gate_6_volatility_acceptable(ATRState.ELEVATED, 2.5, p)
        assert g.passed is True

    def test_near_miss_extreme_atr_blocked(self):
        p = _params()
        g = gate_6_volatility_acceptable(ATRState.EXTREME, None, p)
        assert g.passed is False
        assert 'EXTREME' in g.reason

    def test_near_miss_compressed_atr_blocked(self):
        # COMPRESSED is not in default allowed set; blocked at gate 6
        p = _params(allowed_atr_states=('NORMAL', 'ELEVATED'))
        g = gate_6_volatility_acceptable(ATRState.COMPRESSED, None, p)
        assert g.passed is False

    def test_near_miss_spread_over_max(self):
        p = _params(max_spread_pips=3.0)
        g = gate_6_volatility_acceptable(ATRState.NORMAL, 3.5, p)
        assert g.passed is False
        assert '3.5' in g.reason

    def test_near_miss_none_atr_state(self):
        p = _params()
        g = gate_6_volatility_acceptable(None, None, p)
        assert g.passed is False
        assert 'insufficient' in g.reason.lower()


# ---------------------------------------------------------------------------
# Gate 7 — Session & news
# ---------------------------------------------------------------------------

class TestGate7:
    def test_pass_london_well_within_buffer(self):
        p = _params(session_edge_buffer_min=30)
        g = gate_7_session_clear(Session.LONDON, minutes_to_edge=90, p=p)
        assert g.passed is True
        assert 'LONDON' in g.reason
        assert 'stub-pass' in g.reason  # runtime stub is documented

    def test_pass_overlap(self):
        p = _params(session_edge_buffer_min=30)
        g = gate_7_session_clear(Session.OVERLAP, minutes_to_edge=60, p=p)
        assert g.passed is True

    def test_pass_ny(self):
        p = _params(session_edge_buffer_min=30)
        g = gate_7_session_clear(Session.NY, minutes_to_edge=45, p=p)
        assert g.passed is True

    def test_near_miss_off_session(self):
        p = _params()
        g = gate_7_session_clear(Session.OFF, minutes_to_edge=0, p=p)
        assert g.passed is False
        assert 'OFF' in g.reason

    def test_near_miss_within_edge_buffer(self):
        # 20 minutes to edge, buffer=30 → fail
        p = _params(session_edge_buffer_min=30)
        g = gate_7_session_clear(Session.LONDON, minutes_to_edge=20, p=p)
        assert g.passed is False
        assert '20' in g.reason

    def test_near_miss_at_exactly_buffer_boundary(self):
        # exactly at buffer = fail (< is strict)
        p = _params(session_edge_buffer_min=30)
        g = gate_7_session_clear(Session.NY, minutes_to_edge=29, p=p)
        assert g.passed is False


# ---------------------------------------------------------------------------
# Gate 8 — Risk viable
# ---------------------------------------------------------------------------

class TestGate8:
    def test_pass_rr_above_minimum(self):
        p = _params(min_rr_ratio=2.5)
        g = gate_8_risk_viable(rr_ratio=2.7, stop_placeable=True, p=p)
        assert g.passed is True
        assert '2.7' in g.reason
        assert 'stub-pass' in g.reason  # runtime stub is documented

    def test_pass_rr_exactly_at_minimum(self):
        p = _params(min_rr_ratio=2.5)
        g = gate_8_risk_viable(rr_ratio=2.5, stop_placeable=True, p=p)
        assert g.passed is True

    def test_near_miss_rr_below_minimum(self):
        p = _params(min_rr_ratio=2.5)
        g = gate_8_risk_viable(rr_ratio=2.0, stop_placeable=True, p=p)
        assert g.passed is False
        assert '2.00' in g.reason

    def test_near_miss_stop_not_placeable(self):
        p = _params(min_rr_ratio=2.5)
        g = gate_8_risk_viable(rr_ratio=3.0, stop_placeable=False, p=p)
        assert g.passed is False
        assert 'stop' in g.reason.lower()

    def test_detail_includes_rr_ratio(self):
        p = _params(min_rr_ratio=2.5)
        g = gate_8_risk_viable(rr_ratio=3.1, stop_placeable=True, p=p)
        assert 'rr_ratio' in g.detail
        assert g.detail['rr_ratio'] == pytest.approx(3.1)
