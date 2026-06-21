"""Golden gate-fixtures for Gate 2 — Structure Confirmed (§8.1#2 · §6.1.1).

Pass-path fixture  : H4 series with flat resistance + rising lows → ASCENDING_TRIANGLE
Near-miss 1        : duration too short (< 8 H4 bars)
Near-miss 2        : no sufficient compression
Invalidation       : close >0.30% above resistance → INVALIDATED (§6.1.1, must be reachable)
Bull mirror        : DESCENDING_TRIANGLE
"""

from __future__ import annotations
from decimal import Decimal
from datetime import datetime, timezone, timedelta

import pytest

from lsb.config.models import InstrumentConfig, StrategyParams
from lsb.signal import gate2_structure
from lsb.signal.types import Side

D = Decimal


def _default_sp() -> StrategyParams:
    return StrategyParams(
        ema_fast=21, ema_mid=50, ema_slow=89, atr_period=14,
        ema_compression_atr_mult=D("0.10"), ema_slope_atr_mult=D("0.05"),
        slope_lookback=3, ema_cross_lookback=3,
        resistance_min_touches=2, rising_low_min_pct=D("0.20"),
        triangle_min_candles=8, triangle_max_candles=60,
        compression_max_ratio=D("0.60"),
        apex_proximity_lo=D("0.75"), apex_proximity_hi=D("0.95"),
        invalidation_break_pct=D("0.30"),
        block_min_touches=2, sweep_expiry_candles=3,
    )


def _default_ic() -> InstrumentConfig:
    return InstrumentConfig(
        instrument="EURUSD", instrument_class="fx_major",
        pip_size=D("0.0001"), max_spread=D("1.5"), max_spread_unit="pips",
        sessions="fx", flat_tolerance=D("0.15"),
        swing_lookback=2,
        sweep_penetration=D("2"), sweep_pen_unit="pips",
        block_min_width=D("5"), block_width_unit="pips",
        stop_buffer=D("2"), stop_buffer_elev=D("4"), stop_buffer_unit="pips",
        data_source="dukascopy", ema_touch=D("3"), ema_touch_unit="pips",
    )


def _h4_candle(ts_offset_h: int, high: str, low: str, close: str | None = None) -> dict:
    base = datetime(2023, 6, 1, tzinfo=timezone.utc)
    c = close if close is not None else low
    h, lo = D(high), D(low)
    return {
        "ts": base + timedelta(hours=ts_offset_h * 4),
        "open": lo, "high": h, "low": lo, "close": D(c),
        "volume": D("1000"),
    }


# Canonical ASCENDING TRIANGLE (5-bar fractal — swing_lookback=2).
#   Flat resistance pivots (swing highs = 1.3050) at bars 3, 9, 15, 21.
#   Rising-low pivots (swing lows) at bars 6, 12, 18 → 1.2920, 1.2950, 1.2980
#     (each ≥0.20% above the prior low).
#   Pattern start = bar 3, end = bar 21 → duration 18 ∈ [8, 60].
#   Compression: eval-bar (25) range 8 pips ≪ 60% of bar-3 range (110 pips).
#   Apex proximity ≈ 0.76 ∈ [0.75, 0.95].
_ASC_HIGHS = [
    "1.3030", "1.3035", "1.3040", "1.3050", "1.3038", "1.3032", "1.3030",
    "1.3035", "1.3042", "1.3050", "1.3040", "1.3034", "1.3030", "1.3035",
    "1.3043", "1.3050", "1.3041", "1.3035", "1.3032", "1.3036", "1.3044",
    "1.3050", "1.3042", "1.3037", "1.3034", "1.3038",
]
_ASC_LOWS = [
    "1.2960", "1.2950", "1.2935", "1.2940", "1.2932", "1.2926", "1.2920",
    "1.2930", "1.2942", "1.2955", "1.2958", "1.2954", "1.2950", "1.2960",
    "1.2972", "1.2985", "1.2988", "1.2984", "1.2980", "1.2990", "1.3002",
    "1.3015", "1.3018", "1.3020", "1.3022", "1.3030",
]


def _build_triangle(n_bars: int = 40) -> list[dict]:
    """Return the canonical ascending-triangle series, truncated to n_bars.

    The full pattern is 26 H4 bars; callers asking for more simply get the full
    pattern, callers asking for fewer (e.g. the too-short near-miss) get a prefix.
    """
    candles = []
    count = min(n_bars, len(_ASC_HIGHS))
    for i in range(count):
        h, l = D(_ASC_HIGHS[i]), D(_ASC_LOWS[i])
        c = l + (h - l) * D("0.3")  # close in lower third (bearish candle shape)
        candles.append({
            "ts": datetime(2023, 6, 1, tzinfo=timezone.utc) + timedelta(hours=i * 4),
            "open": l + (h - l) * D("0.4"),
            "high": h, "low": l, "close": c,
            "volume": D("1000"),
        })
    return candles


def _build_compressed_triangle() -> list[dict]:
    """Ascending triangle where the current range is about 30% of the first range."""
    candles = _build_triangle(40)
    # Override: make the last bar have a tiny range
    last = candles[-1]
    mid = (last["high"] + last["low"]) / D("2")
    tiny = D("0.0001")
    candles[-1] = {**last, "high": mid + tiny, "low": mid - tiny, "close": mid}
    return candles


# ---------------------------------------------------------------------------
# Golden gate-fixtures
# ---------------------------------------------------------------------------

def test_gate2_ascending_triangle_pass():
    """Pass-path: 40 H4 bars with flat resistance + rising lows → ASCENDING_TRIANGLE."""
    candles = _build_triangle(40)
    result = gate2_structure.evaluate(candles, _default_sp(), _default_ic(), Side.BEAR)
    assert result.passed, f"Expected pass; got state={result.state} detail={result.detail}"
    assert result.state == "ASCENDING_TRIANGLE"


def test_gate2_too_short():
    """Near-miss 1: only 5 bars (< triangle_min_candles=8) → NONE."""
    # Build a minimal series — duration between swing touches < 8
    candles = _build_triangle(5)
    result = gate2_structure.evaluate(candles, _default_sp(), _default_ic(), Side.BEAR)
    assert not result.passed
    # Either NONE (no pattern found) or insufficient bars
    assert result.state in ("NONE", "NO_BLOCK")


def test_gate2_no_compression():
    """Near-miss 2: current range ≈ first range → no compression → NONE."""
    # All candles have large equal ranges — no compression
    candles = []
    for i in range(40):
        candles.append({
            "ts": datetime(2023, 6, 1, tzinfo=timezone.utc) + timedelta(hours=i * 4),
            "open": D("1.2900"), "high": D("1.3100"),
            "low": D("1.2700"), "close": D("1.2800"),
            "volume": D("1000"),
        })
    result = gate2_structure.evaluate(candles, _default_sp(), _default_ic(), Side.BEAR)
    assert not result.passed


def test_gate2_invalidated():
    """Invalidation path: close >0.30% above resistance → INVALIDATED (§6.1.1)."""
    candles = _build_triangle(40)
    # Overwrite last bar close to be >0.30% above resistance
    res = D("1.3050")
    break_close = res * (D("100") + D("0.31")) / D("100")
    last = candles[-1]
    candles[-1] = {**last, "close": break_close, "high": break_close + D("0.0005")}
    result = gate2_structure.evaluate(candles, _default_sp(), _default_ic(), Side.BEAR)
    assert not result.passed
    assert result.state == "INVALIDATED", f"Expected INVALIDATED; got {result}"


def test_gate2_bull_descending_triangle_pass():
    """Bull mirror: descending triangle (falling highs, flat support) → DESCENDING_TRIANGLE."""
    # Canonical DESCENDING TRIANGLE — mirror of the ascending fixture:
    #   Flat support pivots (swing lows = 1.2680) at bars 3, 9, 15, 21.
    #   Declining-high pivots (swing highs) at bars 6, 12, 18 → 1.2800, 1.2770,
    #     1.2740 (each ≥0.20% below the prior high).
    #   Duration 18; eval-bar range ≪ 60% of bar-3 range; apex prox ≈ 0.81.
    desc_highs = [
        "1.2770", "1.2775", "1.2780", "1.2784", "1.2790", "1.2796", "1.2800",
        "1.2788", "1.2778", "1.2772", "1.2762", "1.2766", "1.2770", "1.2760",
        "1.2750", "1.2742", "1.2738", "1.2736", "1.2740", "1.2730", "1.2720",
        "1.2715", "1.2718", "1.2720", "1.2722", "1.2720",
    ]
    desc_lows = [
        "1.2700", "1.2695", "1.2690", "1.2680", "1.2692", "1.2698", "1.2700",
        "1.2695", "1.2688", "1.2680", "1.2690", "1.2696", "1.2700", "1.2695",
        "1.2687", "1.2680", "1.2689", "1.2695", "1.2698", "1.2694", "1.2686",
        "1.2680", "1.2688", "1.2693", "1.2696", "1.2692",
    ]
    candles = []
    for i in range(len(desc_highs)):
        h, l = D(desc_highs[i]), D(desc_lows[i])
        c = h - (h - l) * D("0.3")
        candles.append({
            "ts": datetime(2023, 6, 1, tzinfo=timezone.utc) + timedelta(hours=i * 4),
            "open": h - (h - l) * D("0.4"),
            "high": h, "low": l, "close": c,
            "volume": D("1000"),
        })
    result = gate2_structure.evaluate(candles, _default_sp(), _default_ic(), Side.BULL)
    assert result.passed, f"Expected pass; got state={result.state} detail={result.detail}"
    assert result.state == "DESCENDING_TRIANGLE"


def test_gate2_determinism():
    candles = _build_triangle(40)
    sp, ic = _default_sp(), _default_ic()
    r1 = gate2_structure.evaluate(candles, sp, ic, Side.BEAR)
    r2 = gate2_structure.evaluate(candles, sp, ic, Side.BEAR)
    assert r1 == r2
