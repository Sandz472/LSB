"""Golden gate-fixtures for Gate 4 — EMA Interaction Confirmed (§8.1#4).

Gate 4 is a HARD gate — the prior build dropped it (§R).  These tests
assert it exists, is reachable, and is rejectable.

Pass-path fixture  : H1 series where the last bar's high is within 3 pips of EMA21
Near-miss 1        : high is far from both EMA21 and EMA50 → NO_EMA_TOUCH
Near-miss 2        : sweep_bar provided but neither bar touches either EMA → NO_EMA_TOUCH
Bull mirror        : low within 3 pips of EMA50 → EMA_TOUCHED
"""

from __future__ import annotations
from decimal import Decimal
from datetime import datetime, timezone, timedelta

from lsb.config.models import InstrumentConfig, StrategyParams
from lsb.signal import gate4_ema
from lsb.signal.indicators import ema as compute_ema
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
        atr_baseline_window=20, atr_compressed_mult=D("0.75"),
        atr_elevated_mult=D("1.25"), atr_extreme_mult=D("2.0"),
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


def _h1_series(n: int, close_val: str) -> list[dict]:
    """Flat H1 series of *n* bars — EMA21 converges to close_val."""
    base = datetime(2024, 5, 1, tzinfo=timezone.utc)
    c = D(close_val)
    return [
        {
            "ts": base + timedelta(hours=i),
            "open": c, "high": c + D("0.0010"), "low": c - D("0.0010"),
            "close": c, "volume": D("500"),
        }
        for i in range(n)
    ]


def _find_ema21_at_bar(candles: list[dict], bar: int) -> Decimal:
    closes = [c["close"] for c in candles]
    series = compute_ema(closes, 21)
    val = series[bar]
    assert val is not None
    return val


# ---------------------------------------------------------------------------
# Golden gate-fixtures
# ---------------------------------------------------------------------------

def test_gate4_bear_ema_touch_pass():
    """Pass-path: last bar's high is within 3 pips of EMA21 → EMA_TOUCHED.

    Strategy: build a flat series so EMA21 converges to close, then set
    the last bar's high to be exactly 2 pips above close (= 1 pip inside
    the 3-pip touch threshold).
    """
    candles = _h1_series(55, "1.3000")
    e21 = _find_ema21_at_bar(candles, len(candles) - 1)
    # Set last bar high = EMA21 + 0.0002 (2 pips, inside 3-pip threshold)
    last = candles[-1]
    touch_high = e21 + D("0.0002")
    candles[-1] = {**last, "high": touch_high}
    result = gate4_ema.evaluate(candles, _default_sp(), _default_ic(), Side.BEAR)
    assert result.passed, f"Expected pass; got state={result.state} detail={result.detail}"
    assert result.state == "EMA_TOUCHED"


def test_gate4_no_touch_far_from_ema():
    """Near-miss 1: bar high is 20 pips above EMA21/50 → NO_EMA_TOUCH."""
    candles = _h1_series(55, "1.3000")
    e21 = _find_ema21_at_bar(candles, len(candles) - 1)
    # High is 20 pips ABOVE EMA21 — well outside the 3-pip touch window
    last = candles[-1]
    far_high = e21 + D("0.0020")
    candles[-1] = {**last, "high": far_high}
    result = gate4_ema.evaluate(candles, _default_sp(), _default_ic(), Side.BEAR)
    assert not result.passed
    assert result.state == "NO_EMA_TOUCH"


def test_gate4_no_touch_both_bars_far():
    """Near-miss 2: sweep_bar and eval bar both far from EMAs → NO_EMA_TOUCH."""
    candles = _h1_series(55, "1.3000")
    e21 = _find_ema21_at_bar(candles, len(candles) - 1)
    # Both bars: high = EMA21 + 50 pips
    for j in (-1, -2):
        last = candles[j]
        candles[j] = {**last, "high": e21 + D("0.0050")}
    result = gate4_ema.evaluate(
        candles, _default_sp(), _default_ic(), Side.BEAR,
        sweep_bar=len(candles) - 2,
    )
    assert not result.passed
    assert result.state == "NO_EMA_TOUCH"


def test_gate4_sweep_bar_touch():
    """Sweep bar touches EMA even though confirmation bar does not → pass."""
    candles = _h1_series(55, "1.3000")
    e21 = _find_ema21_at_bar(candles, len(candles) - 2)  # sweep bar is second-to-last
    # Sweep bar high = EMA21 + 1 pip (within touch threshold)
    sb = len(candles) - 2
    candles[sb] = {**candles[sb], "high": e21 + D("0.0001")}
    # Confirmation bar (last) is far from EMA
    candles[-1] = {**candles[-1], "high": e21 + D("0.0050")}
    result = gate4_ema.evaluate(
        candles, _default_sp(), _default_ic(), Side.BEAR, sweep_bar=sb
    )
    assert result.passed, f"Expected pass (sweep bar touches); got {result}"
    assert result.state == "EMA_TOUCHED"


def test_gate4_bull_ema_touch_pass():
    """Bull mirror: bar LOW within 3 pips of EMA50 → EMA_TOUCHED."""
    candles = _h1_series(55, "1.3000")
    closes = [c["close"] for c in candles]
    e50_series = compute_ema(closes, 50)
    e50 = e50_series[-1]
    assert e50 is not None
    last = candles[-1]
    # Low = EMA50 - 1 pip (inside 3-pip threshold)
    touch_low = e50 - D("0.0001")
    candles[-1] = {**last, "low": touch_low}
    result = gate4_ema.evaluate(candles, _default_sp(), _default_ic(), Side.BULL)
    assert result.passed, f"Expected BULL pass; got {result}"
    assert result.state == "EMA_TOUCHED"


def test_gate4_insufficient_data():
    candles = _h1_series(10, "1.3000")
    result = gate4_ema.evaluate(candles, _default_sp(), _default_ic(), Side.BEAR)
    assert not result.passed
    assert result.state == "INSUFFICIENT_DATA"


def test_gate4_determinism():
    candles = _h1_series(55, "1.3000")
    e21 = _find_ema21_at_bar(candles, len(candles) - 1)
    candles[-1] = {**candles[-1], "high": e21 + D("0.0002")}
    sp, ic = _default_sp(), _default_ic()
    r1 = gate4_ema.evaluate(candles, sp, ic, Side.BEAR)
    r2 = gate4_ema.evaluate(candles, sp, ic, Side.BEAR)
    assert r1 == r2
