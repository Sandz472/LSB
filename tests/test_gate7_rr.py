"""Golden gate-fixtures for Gate 7 — Risk:Reward Minimum (§8.1#7 · §9.1 · §9.4).

Pass-path  : ATR×3 target gives R:R = 7.5 ≥ 2.5 → RR_OK
Near-miss 1: wide stop makes R:R < 2.5 → RR_BELOW_MIN
Liquidity  : a nearer liquidity pool clears the floor → chosen over ATR×3 (closest)
Elevated   : ATR ELEVATED selects the wider stop buffer (detail records it)
No target  : no ATR and no pool → NO_TARGET
Geometry   : stop not beyond entry → INVALID_GEOMETRY
Bull mirror: symmetric pass
"""

from __future__ import annotations
from decimal import Decimal
from datetime import datetime, timezone
from pathlib import Path

from lsb.config import load_strategy, load_instrument
from lsb.signal import gate7_rr
from lsb.signal.types import Side, AtrState

D = Decimal
CONFIG = Path(__file__).parent.parent / "config"


def _sp():
    return load_strategy(CONFIG / "strategy.yaml")


def _ic():
    return load_instrument(CONFIG / "EURUSD.yaml")


def _entry_candle(close):
    return [{"ts": datetime(2024, 3, 1, 10, tzinfo=timezone.utc),
             "open": D(close), "high": D(close), "low": D(close),
             "close": D(close), "volume": D("500")}]


def test_gate7_bear_pass():
    # entry 1.3000; stop = 1.3002 + 2pip = 1.3004; risk 4 pips; ATR×3 = 30 pips → RR 7.5
    res = gate7_rr.evaluate(_entry_candle("1.3000"), _sp(), _ic(), Side.BEAR,
                            rejection_extreme=D("1.3002"), atr_h1=D("0.0010"))
    assert res.passed, res
    assert res.state == "RR_OK"
    assert res.detail["via"] == "atr_x3"


def test_gate7_rr_below_min():
    # wide stop: rejection high 1.3050 → stop 1.3052, risk 52 pips; ATR×3 30 pips → RR 0.58
    res = gate7_rr.evaluate(_entry_candle("1.3000"), _sp(), _ic(), Side.BEAR,
                            rejection_extreme=D("1.3050"), atr_h1=D("0.0010"))
    assert not res.passed
    assert res.state == "RR_BELOW_MIN"


def test_gate7_liquidity_pool_closest():
    """Pool at 1.2985 (RR 3.75) is closer than ATR×3 at 1.2970 (RR 7.5); both clear 2.5."""
    res = gate7_rr.evaluate(_entry_candle("1.3000"), _sp(), _ic(), Side.BEAR,
                            rejection_extreme=D("1.3002"), atr_h1=D("0.0010"),
                            liquidity_pool=D("1.2985"))
    assert res.passed
    assert res.detail["via"] == "liquidity_pool"


def test_gate7_elevated_buffer_selected():
    res = gate7_rr.evaluate(_entry_candle("1.3000"), _sp(), _ic(), Side.BEAR,
                            rejection_extreme=D("1.3002"), atr_h1=D("0.0010"),
                            atr_state=AtrState.ELEVATED)
    assert res.passed
    assert res.detail["atr_state"] == "ELEVATED"
    # stop = 1.3002 + 4 pips elevated buffer = 1.3006
    assert res.detail["stop"] == "1.3006"


def test_gate7_no_target():
    res = gate7_rr.evaluate(_entry_candle("1.3000"), _sp(), _ic(), Side.BEAR,
                            rejection_extreme=D("1.3002"), atr_h1=None)
    assert not res.passed and res.state == "NO_TARGET"


def test_gate7_invalid_geometry():
    # rejection extreme BELOW entry → bear stop not above entry → risk ≤ 0
    res = gate7_rr.evaluate(_entry_candle("1.3000"), _sp(), _ic(), Side.BEAR,
                            rejection_extreme=D("1.2990"), atr_h1=D("0.0010"))
    assert not res.passed and res.state == "INVALID_GEOMETRY"


def test_gate7_bull_pass():
    res = gate7_rr.evaluate(_entry_candle("1.3000"), _sp(), _ic(), Side.BULL,
                            rejection_extreme=D("1.2998"), atr_h1=D("0.0010"))
    assert res.passed and res.state == "RR_OK"


def test_gate7_determinism():
    sp, ic = _sp(), _ic()
    args = dict(rejection_extreme=D("1.3002"), atr_h1=D("0.0010"))
    r1 = gate7_rr.evaluate(_entry_candle("1.3000"), sp, ic, Side.BEAR, **args)
    r2 = gate7_rr.evaluate(_entry_candle("1.3000"), sp, ic, Side.BEAR, **args)
    assert r1 == r2
