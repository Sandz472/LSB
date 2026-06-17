"""Gates 1–4 unit tests — 1 pass + ≥2 near-misses per gate.

Fixtures are hand-labeled synthetic scenarios determined from spec definitions
(LSB_System_Requirements_v2.0.md §8) before the gate predicates were coded.
"""

import pytest

from lsb.signals.gates import (
    gate_1_trend_alignment,
    gate_2_structure_present,
    gate_3_liquidity_sweep,
    gate_4_sweep_quality,
)
from lsb.signals.trend import TrendState
from lsb.signals.structure import StructureResult, StructureState
from lsb.signals.liquidity import SweepResult


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
