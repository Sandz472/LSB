"""Golden gate-fixtures for Gate 1 — Trend State Confirmed (§8.1#1).

Each fixture is hand-labelled: given the described input series, the listed
GateResult is the owner-verified correct output.  CI replays these on every run.

Pass-path fixture  : clear D1 bear trend → passed=True, state="BEARISH"
Near-miss 1        : EMA compression   → passed=False, state="INVALID"
Near-miss 2        : recent EMA cross  → passed=False, state="INVALID"
Near-miss 3        : wrong stack       → passed=False, state="NEUTRAL"
Bull mirror        : same data flipped → passed=True, state="BULLISH"
"""

from __future__ import annotations
from decimal import Decimal
from datetime import datetime, timezone, timedelta

import pytest

from lsb.config.models import InstrumentConfig, StrategyParams
from lsb.signal import gate1_trend
from lsb.signal.types import Side

D = Decimal


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------

def _d1_candles(closes: list[str], h_delta: str = "0.0025") -> list[dict]:
    """Build minimal D1 OHLCV dicts from a close sequence."""
    base = datetime(2022, 1, 1, tzinfo=timezone.utc)
    hd = D(h_delta)
    return [
        {
            "ts": base + timedelta(days=i),
            "open": D(c), "high": D(c) + hd, "low": D(c) - hd,
            "close": D(c), "volume": D("1000"),
        }
        for i, c in enumerate(closes)
    ]


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
        sessions="fx", flat_tolerance=D("0.15"),
        sweep_penetration=D("2"), sweep_pen_unit="pips",
        block_min_width=D("5"), block_width_unit="pips",
        stop_buffer=D("2"), stop_buffer_elev=D("4"), stop_buffer_unit="pips",
        data_source="dukascopy", swing_lookback=2,
        ema_touch=D("3"), ema_touch_unit="pips",
    )


def _bear_closes(n: int = 95) -> list[str]:
    """Steadily descending close series: clear EMA21<50<89 bearish stack after warm-up."""
    start = D("1.3000")
    step  = D("0.0010")
    return [str(start - step * i) for i in range(n)]


def _bull_closes(n: int = 95) -> list[str]:
    """Steadily ascending close series: clear EMA21>50>89 bullish stack."""
    start = D("1.1000")
    step  = D("0.0010")
    return [str(start + step * i) for i in range(n)]


# ---------------------------------------------------------------------------
# Golden gate-fixtures
# ---------------------------------------------------------------------------

def test_gate1_bear_pass():
    """Pass-path: 95-bar descending D1 series → BEARISH trend confirmed."""
    candles = _d1_candles(_bear_closes())
    result = gate1_trend.evaluate(candles, _default_sp(), _default_ic(), Side.BEAR)
    assert result.passed, f"Expected pass; got {result}"
    assert result.state == "BEARISH"


def test_gate1_compression_invalid():
    """Near-miss 1: flat closes (EMAs converge) → compression → INVALID."""
    # All closes equal → EMA21≈EMA50≈EMA89, spread ≈ 0 < ATR*0.10 → INVALID
    closes = ["1.2500"] * 95
    candles = _d1_candles(closes)
    result = gate1_trend.evaluate(candles, _default_sp(), _default_ic(), Side.BEAR)
    assert not result.passed
    assert result.state == "INVALID"
    assert result.detail.get("reason") == "compression"


def test_gate1_recent_cross_invalid():
    """Near-miss 2: long downtrend then a moderate reversal → recent EMA cross → INVALID.

    89 bearish bars build the EMA21<50<89 stack; a 20-bar rally (continuing from
    the last bear close, no gap) lifts EMA21 just enough to cross EMA50 on the
    evaluation bar.  The rally is deliberately gentle so EMA21 stays far below
    EMA89 (|EMA21−EMA89| ≫ ATR×0.10) — i.e. the *cross* fires, not compression,
    which is the condition this fixture must isolate.
    """
    last_bear = D("1.3000") - D("0.0010") * 88
    closes = _bear_closes(89) + [str(last_bear + D("0.0020") * i) for i in range(1, 21)]
    candles = _d1_candles(closes, h_delta="0.0030")
    result = gate1_trend.evaluate(candles, _default_sp(), _default_ic(), Side.BEAR)
    assert not result.passed
    assert result.state == "INVALID"
    assert result.detail.get("reason") == "recent_cross"


def test_gate1_wrong_stack_neutral():
    """Near-miss 3: ascending series → EMA21>50>89 → BEAR stack fails → NEUTRAL."""
    candles = _d1_candles(_bull_closes())
    result = gate1_trend.evaluate(candles, _default_sp(), _default_ic(), Side.BEAR)
    assert not result.passed
    assert result.state == "NEUTRAL"


def test_gate1_bull_pass():
    """Bull mirror: ascending series → BULLISH trend confirmed."""
    candles = _d1_candles(_bull_closes())
    result = gate1_trend.evaluate(candles, _default_sp(), _default_ic(), Side.BULL)
    assert result.passed, f"Expected pass; got {result}"
    assert result.state == "BULLISH"


def test_gate1_bull_wrong_stack_neutral():
    """Bull near-miss: descending series → BEAR stack → BULL check NEUTRAL."""
    candles = _d1_candles(_bear_closes())
    result = gate1_trend.evaluate(candles, _default_sp(), _default_ic(), Side.BULL)
    assert not result.passed
    assert result.state == "NEUTRAL"


def test_gate1_insufficient_data():
    """Fewer bars than warm-up → INSUFFICIENT_DATA, not a crash."""
    candles = _d1_candles(["1.2500"] * 10)
    result = gate1_trend.evaluate(candles, _default_sp(), _default_ic(), Side.BEAR)
    assert not result.passed
    assert result.state == "INSUFFICIENT_DATA"


def test_gate1_determinism():
    """Same candles + config → byte-identical GateResult (rule 4)."""
    candles = _d1_candles(_bear_closes())
    sp, ic = _default_sp(), _default_ic()
    r1 = gate1_trend.evaluate(candles, sp, ic, Side.BEAR)
    r2 = gate1_trend.evaluate(candles, sp, ic, Side.BEAR)
    assert r1 == r2
