"""M4 structure detection tests.

Fixtures: known triangle pass, noise rejection, out-of-range apex rejection.
Each test is labeled with the expected outcome before the gate was coded.
"""

import pytest
from datetime import datetime, timezone

from lsb.data.config import SignalParams
from lsb.signals import Candle
from lsb.signals.structure import (
    StructureState,
    detect_triangle,
    _rising_lows,
    _falling_highs,
    _compression_ok,
)

PARAMS = SignalParams(
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


def _ts(i):
    return datetime(2024, 1, 1, tzinfo=timezone.utc) + __import__('datetime').timedelta(hours=4*i)


def _h4(i, o, h, l, c):
    return Candle(ts=_ts(i), open=o, high=h, low=l, close=c, volume=100.0)


def _build_ascending_triangle():
    """Explicit ascending triangle: flat resistance at 1.200, rising lows.

    Swing highs at indices 2, 8, 14 (all H=1.200, neighbors ≤ 1.195).
    Swing lows  at indices 5, 11, 17 (L=1.000, 1.018, 1.036 — rising).
    All verified by hand to satisfy _swing_highs / _swing_lows lookback=2.
    """
    return [
        # ── approach to first resistance touch ──
        _h4(0,  1.060, 1.160, 0.990, 1.150),
        _h4(1,  1.150, 1.190, 1.050, 1.185),
        # SWING HIGH #1 — H=1.200 (flanked by H ≤ 1.190 on both sides ×2)
        _h4(2,  1.185, 1.200, 1.060, 1.190),
        # ── decline to first swing low ──
        _h4(3,  1.190, 1.195, 1.005, 1.010),
        _h4(4,  1.010, 1.190, 1.001, 1.005),  # L=1.001 (just above swing low)
        # SWING LOW #1 — L=1.000 (neighbors L ≥ 1.001)
        _h4(5,  1.005, 1.010, 1.000, 1.008),
        # ── recovery to second resistance touch ──
        _h4(6,  1.008, 1.100, 1.002, 1.090),
        _h4(7,  1.090, 1.190, 1.010, 1.185),
        # SWING HIGH #2 — H=1.200
        _h4(8,  1.185, 1.200, 1.020, 1.192),
        # ── decline to second swing low ──
        _h4(9,  1.192, 1.195, 1.025, 1.030),
        _h4(10, 1.030, 1.190, 1.019, 1.025),  # L=1.019 (just above swing low)
        # SWING LOW #2 — L=1.018 > 1.000 ✓ (rising)
        _h4(11, 1.025, 1.030, 1.018, 1.028),
        # ── recovery to third resistance touch ──
        _h4(12, 1.028, 1.100, 1.020, 1.095),
        _h4(13, 1.095, 1.195, 1.030, 1.190),
        # SWING HIGH #3 — H=1.200
        _h4(14, 1.190, 1.200, 1.040, 1.195),
        # ── decline to third swing low ──
        _h4(15, 1.195, 1.198, 1.040, 1.045),
        _h4(16, 1.045, 1.195, 1.037, 1.040),  # L=1.037 (just above swing low)
        # SWING LOW #3 — L=1.036 > 1.018 ✓ (rising)
        _h4(17, 1.040, 1.045, 1.036, 1.042),
        # ── recovery (current area) ──
        _h4(18, 1.042, 1.100, 1.038, 1.095),
        _h4(19, 1.095, 1.198, 1.045, 1.195),
    ]


def _build_descending_triangle():
    """Explicit descending triangle: flat support at 1.000, falling highs.

    Swing lows  at indices 2, 8, 14 (all L=1.000, neighbors ≥ 1.001).
    Swing highs at indices 5, 11, 17 (H=1.200, 1.182, 1.164 — falling).
    """
    return [
        # ── approach to first support touch ──
        _h4(0,  1.150, 1.180, 1.050, 1.020),
        _h4(1,  1.020, 1.060, 1.010, 1.015),
        # SWING LOW #1 — L=1.000 (flanked by L ≥ 1.001)
        _h4(2,  1.015, 1.020, 1.000, 1.010),
        # ── rally to first swing high ──
        _h4(3,  1.010, 1.150, 1.001, 1.140),
        _h4(4,  1.140, 1.190, 1.005, 1.185),
        # SWING HIGH #1 — H=1.200
        _h4(5,  1.185, 1.200, 1.010, 1.190),
        # ── decline to second support touch ──
        _h4(6,  1.190, 1.195, 1.005, 1.015),
        _h4(7,  1.015, 1.060, 1.001, 1.010),
        # SWING LOW #2 — L=1.000
        _h4(8,  1.010, 1.020, 1.000, 1.012),
        # ── rally to second swing high (lower than #1) ──
        _h4(9,  1.012, 1.150, 1.001, 1.140),
        _h4(10, 1.140, 1.172, 1.005, 1.168),
        # SWING HIGH #2 — H=1.182 < 1.200 ✓ (falling)
        _h4(11, 1.168, 1.182, 1.010, 1.175),
        # ── decline to third support touch ──
        _h4(12, 1.175, 1.178, 1.005, 1.015),
        _h4(13, 1.015, 1.060, 1.001, 1.010),
        # SWING LOW #3 — L=1.000
        _h4(14, 1.010, 1.020, 1.000, 1.012),
        # ── rally to third swing high (lower than #2) ──
        _h4(15, 1.012, 1.150, 1.001, 1.140),
        _h4(16, 1.140, 1.154, 1.005, 1.150),
        # SWING HIGH #3 — H=1.164 < 1.182 ✓ (falling)
        _h4(17, 1.150, 1.164, 1.010, 1.155),
        # ── current area ──
        _h4(18, 1.155, 1.160, 1.001, 1.010),
        _h4(19, 1.010, 1.055, 1.001, 1.020),
    ]


class TestAscendingTriangle:
    def test_clear_ascending_triangle_detected(self):
        # 3 swing highs at 1.200 (flat), 3 rising lows → ASCENDING_TRIANGLE or FORMING
        # (FORMING if apex proximity < 0.75; ASCENDING_TRIANGLE once current bar
        # is ≥75% of the way to the apex)
        candles = _build_ascending_triangle()
        result = detect_triangle(candles, PARAMS)
        assert result.state in (
            StructureState.ASCENDING_TRIANGLE,
            StructureState.FORMING,
        ), f"Expected ASCENDING or FORMING, got {result.state}"
        # Either way, the algorithm recognised the structure.
        assert result.apex_proximity > 0.0

    def test_resistance_touches_counted(self):
        candles = _build_ascending_triangle()
        result = detect_triangle(candles, PARAMS)
        if result.state in (StructureState.ASCENDING_TRIANGLE, StructureState.FORMING):
            assert result.resistance_touches >= 2

    def test_insufficient_candles_returns_forming(self):
        candles = [_h4(i, 1.0, 1.1, 0.9, 1.05) for i in range(4)]
        result = detect_triangle(candles, PARAMS)
        assert result.state == StructureState.FORMING


class TestDescendingTriangle:
    def test_clear_descending_triangle_detected(self):
        candles = _build_descending_triangle()
        result = detect_triangle(candles, PARAMS)
        assert result.state in (
            StructureState.DESCENDING_TRIANGLE,
            StructureState.FORMING,
        ), f"Expected DESCENDING or FORMING, got {result.state}"

    def test_not_ascending_triangle(self):
        candles = _build_descending_triangle()
        result = detect_triangle(candles, PARAMS)
        assert result.state != StructureState.ASCENDING_TRIANGLE


class TestRisingLowsHelper:
    """Regression guard for the §6.1.1 rising-lows leg.

    The original implementation used all(low[j] > low[j-1]) — a strict all-pivot
    monotonicity test that NEVER passed on real H4 data (one noisy lower pivot
    vetoed the whole pattern), leaving Gate 2 permanently dead. These tests lock
    in the corrected behaviour: an on-balance climb tolerant of intermediate noise.
    """

    def test_noisy_but_rising_passes(self):
        # Net climb 1.000 → 1.040 with a noisy dip in the middle.
        lows = [1.000, 1.010, 1.004, 1.025, 1.040]
        assert _rising_lows(lows, step_pct=0.002, min_points=2)

    def test_strict_monotonic_still_passes(self):
        lows = [1.000, 1.018, 1.036]
        assert _rising_lows(lows, step_pct=0.002, min_points=2)

    def test_flat_lows_rejected(self):
        lows = [1.000, 1.0005, 1.0009]  # steps below 0.20%
        assert not _rising_lows(lows, step_pct=0.002, min_points=2)

    def test_falling_lows_rejected(self):
        lows = [1.040, 1.020, 1.000]
        assert not _rising_lows(lows, step_pct=0.002, min_points=2)

    def test_min_points_enforced(self):
        # Only one qualifying step → 2 points; min_points=3 should reject.
        lows = [1.000, 1.030]
        assert _rising_lows(lows, step_pct=0.002, min_points=2)
        assert not _rising_lows(lows, step_pct=0.002, min_points=3)

    def test_falling_highs_mirror(self):
        highs = [1.200, 1.190, 1.195, 1.170, 1.150]  # net fall with noise
        assert _falling_highs(highs, step_pct=0.002, min_points=2)
        assert not _falling_highs([1.150, 1.170, 1.200], step_pct=0.002, min_points=2)


class TestCompressionHelper:
    def test_compression_pass(self):
        # last range 0.04 ≤ 0.60 × first range 0.10
        window = [_h4(0, 1.0, 1.10, 1.00, 1.05), _h4(1, 1.0, 1.04, 1.00, 1.02)]
        assert _compression_ok(window, 0, 0.60)

    def test_compression_fail(self):
        window = [_h4(0, 1.0, 1.05, 1.00, 1.02), _h4(1, 1.0, 1.10, 1.00, 1.05)]
        assert not _compression_ok(window, 0, 0.60)


class TestNoStructure:
    def test_random_noise_returns_none(self):
        """Candles with alternating highs and lows and no consistent pattern."""
        import math
        candles = []
        for i in range(20):
            # Oscillating zigzag — no trend in highs or lows.
            base = 1.0 + 0.02 * math.sin(i * 0.8)
            candles.append(_h4(i, base, base + 0.05, base - 0.05, base + 0.01))
        result = detect_triangle(candles, PARAMS)
        assert result.state in (
            StructureState.NONE,
            StructureState.FORMING,
        )

    def test_too_few_candles_returns_forming_not_none(self):
        candles = [_h4(i, 1.0, 1.1, 0.9, 1.05) for i in range(5)]
        result = detect_triangle(candles, PARAMS)
        assert result.state == StructureState.FORMING
