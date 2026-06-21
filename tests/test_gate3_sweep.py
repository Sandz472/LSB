"""Golden gate-fixtures for Gate 3 — Liquidity Sweep Detected (§8.1#3).

Pass-path fixture : H1 series with valid block + sweep above block HIGH → SWEEP_BEAR
Near-miss 1       : wick doesn't reach block HIGH → NO_SWEEP
Near-miss 2       : wick exceeds block HIGH but candle closes above (not below) → NO_SWEEP
Near-miss 3       : false-sweep — later close above block HIGH after initial sweep → FALSE_SWEEP
Bull mirror       : SWEEP_BULL

Key invariant: sweep target is the block HIGH (highest swing-high wick) — not a mean level.
"""

from __future__ import annotations
from decimal import Decimal
from datetime import datetime, timezone, timedelta

import pytest

from lsb.config.models import InstrumentConfig, StrategyParams
from lsb.signal import gate3_sweep
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
        rejection_wick_body_mult=D("2.0"), rejection_opp_wick_body_max=D("0.30"),
        session_edge_buffer_min=30, news_buffer_min=60,
        rr_min=D("2.5"), atr_target_mult=D("3.0"),
        sweep_w_density=D("30"), sweep_w_wick=D("20"), sweep_w_close=D("20"),
        sweep_w_ema=D("15"), sweep_w_atr=D("15"),
        risk_tier_high_min=D("80"), risk_tier_mid_min=D("50"), skip_below_50=False,
    )


def _default_ic() -> InstrumentConfig:
    return InstrumentConfig(
        instrument="EURUSD", instrument_class="fx_major",
        pip_size=D("0.0001"), max_spread=D("1.5"), max_spread_unit="pips",
        sessions="fx", flat_tolerance=D("0.15"), swing_lookback=2,
        sweep_penetration=D("2"), sweep_pen_unit="pips",
        block_min_width=D("5"), block_width_unit="pips",
        stop_buffer=D("2"), stop_buffer_elev=D("4"), stop_buffer_unit="pips",
        data_source="dukascopy", ema_touch=D("3"), ema_touch_unit="pips",
    )


def _h1(offset_h: int, h: str, l: str, c: str) -> dict:
    base = datetime(2024, 3, 1, tzinfo=timezone.utc)
    return {
        "ts": base + timedelta(hours=offset_h),
        "open": D(l), "high": D(h), "low": D(l), "close": D(c),
        "volume": D("500"),
    }


def _build_bear_sweep_series() -> list[dict]:
    """
    Build a valid BEAR sweep scenario (5-bar fractal — swing_lookback=2).

    A pivot needs 2 strictly-bracketing bars on EACH side, so the two block
    swing-highs are placed at indices 2 and 6 (both fully bracketed); the sweep
    bar (index 9) and the confirmation/eval bar (index 10) sit at the tail and
    cannot themselves be pivots (no right-hand window).

      - bar 2: h=1.3060  → SWING HIGH 1 (close 1.3015)
      - bar 6: h=1.307   → SWING HIGH 2 (close 1.3020)  ← highest wick = block HIGH
    Block:
      - swing-high closes: 1.3015, 1.3020 → block_low  = 1.3015
      - swing-high wicks:  1.3060, 1.307  → block_HIGH = 1.307
      - width = 1.307 − 1.3015 = 55 pips ≥ 5-pip min ✓ ; 2 touches ✓

    Bar 9: SWEEP bar — wick 20 pips above block HIGH, close below it.
    Bar 10: confirmation/eval bar, closes well below the block.
    """
    block_high = D("1.307")
    sweep_high = block_high + D("0.0020")   # 20 pips above → well above 2-pip threshold
    return [
        _h1(0,  "1.3030", "1.3000", "1.3010"),
        _h1(1,  "1.3040", "1.3005", "1.3015"),
        _h1(2,  "1.3060", "1.3010", "1.3015"),  # swing high 1
        _h1(3,  "1.3035", "1.3000", "1.3010"),
        _h1(4,  "1.3030", "1.2995", "1.3005"),
        _h1(5,  "1.3038", "1.3000", "1.3008"),
        _h1(6,  "1.307",  "1.3010", "1.3020"),  # swing high 2 (block HIGH wick)
        _h1(7,  "1.3040", "1.3000", "1.3010"),
        _h1(8,  "1.3035", "1.2990", "1.3000"),
        _h1(9,  str(sweep_high), "1.3030", "1.3060"),  # SWEEP bar (close < block HIGH)
        _h1(10, "1.3065", "1.2980", "1.2990"),          # confirmation (eval bar)
    ]


# ---------------------------------------------------------------------------
# Golden gate-fixtures
# ---------------------------------------------------------------------------

def test_gate3_bear_sweep_pass():
    """Pass-path: block established, sweep 20 pips above block HIGH, close below → SWEEP_BEAR."""
    candles = _build_bear_sweep_series()
    result = gate3_sweep.evaluate(candles, _default_sp(), _default_ic(), Side.BEAR)
    assert result.passed, f"Expected pass; got state={result.state} detail={result.detail}"
    assert result.state == "SWEEP_BEAR"
    # Block HIGH must be the highest swing-high wick (1.3070), not the mean
    assert result.detail["block_high"] == "1.307"


def test_gate3_no_penetration():
    """Near-miss 1: sweep bar wick only reaches block HIGH (no 2-pip penetration) → NO_SWEEP."""
    candles = list(_build_bear_sweep_series())
    # Replace sweep bar: high = block_HIGH exactly (0 pip penetration)
    block_high = D("1.3070")
    s = candles[9]
    candles[9] = {**s, "high": block_high, "close": D("1.3060")}
    result = gate3_sweep.evaluate(candles, _default_sp(), _default_ic(), Side.BEAR)
    assert not result.passed
    assert result.state == "NO_SWEEP"


def test_gate3_close_above_block_high():
    """Near-miss 2: wick exceeds block HIGH but candle CLOSES above it → NO_SWEEP."""
    candles = list(_build_bear_sweep_series())
    block_high = D("1.3070")
    sweep_high = block_high + D("0.0020")
    s = candles[9]
    candles[9] = {**s, "high": sweep_high, "close": block_high + D("0.0010")}
    result = gate3_sweep.evaluate(candles, _default_sp(), _default_ic(), Side.BEAR)
    assert not result.passed
    assert result.state == "NO_SWEEP"


def test_gate3_false_sweep():
    """Near-miss 3: sweep looked valid but a later bar closes above block HIGH → FALSE_SWEEP."""
    candles = list(_build_bear_sweep_series())
    block_high = D("1.3070")
    # Overwrite the confirmation bar to close above block_HIGH (false sweep signal)
    last = candles[10]
    candles[10] = {**last, "close": block_high + D("0.0010"),
                   "high": block_high + D("0.0015")}
    result = gate3_sweep.evaluate(candles, _default_sp(), _default_ic(), Side.BEAR)
    assert not result.passed
    assert result.state == "FALSE_SWEEP"


def test_gate3_sweep_expiry():
    """Near-miss 4: sweep happened >3 bars ago → outside expiry window → NO_SWEEP."""
    candles = list(_build_bear_sweep_series())
    # Add 4 more neutral bars so the sweep at bar 9 is now 4+ bars ago
    last_ts = candles[-1]["ts"]
    for k in range(4):
        candles.append({
            "ts": last_ts + timedelta(hours=k + 1),
            "open": D("1.2990"), "high": D("1.2995"),
            "low": D("1.2985"), "close": D("1.2990"),
            "volume": D("500"),
        })
    result = gate3_sweep.evaluate(candles, _default_sp(), _default_ic(), Side.BEAR)
    assert not result.passed
    assert result.state == "NO_SWEEP"


def test_gate3_bull_sweep_pass():
    """Bull mirror: wick below support block LOW, close above → SWEEP_BULL."""
    block_low = D("1.2930")
    sweep_low  = block_low - D("0.0020")
    # Swing lows at indices 2 and 6 (5-bar fractal — fully bracketed).
    candles = [
        _h1(0,  "1.2980", "1.2950", "1.2970"),
        _h1(1,  "1.2975", "1.2945", "1.2960"),
        _h1(2,  "1.2970", "1.2930", "1.2940"),  # swing low 1 (block LOW wick)
        _h1(3,  "1.2975", "1.2950", "1.2960"),
        _h1(4,  "1.2980", "1.2955", "1.2965"),
        _h1(5,  "1.2975", "1.2948", "1.2958"),
        _h1(6,  "1.2980", "1.2932", "1.2945"),  # swing low 2
        _h1(7,  "1.2985", "1.2955", "1.2970"),
        _h1(8,  "1.2990", "1.2960", "1.2975"),
        _h1(9,  "1.2970", str(sweep_low), "1.2950"),   # BULL sweep bar
        _h1(10, "1.2975", "1.2945", "1.2960"),          # confirmation
    ]
    result = gate3_sweep.evaluate(candles, _default_sp(), _default_ic(), Side.BULL)
    assert result.passed, f"Expected pass; got {result}"
    assert result.state == "SWEEP_BULL"


def test_gate3_determinism():
    candles = _build_bear_sweep_series()
    sp, ic = _default_sp(), _default_ic()
    r1 = gate3_sweep.evaluate(candles, sp, ic, Side.BEAR)
    r2 = gate3_sweep.evaluate(candles, sp, ic, Side.BEAR)
    assert r1 == r2
