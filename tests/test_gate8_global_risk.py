"""Golden gate-fixtures for Gate 8 — Global Risk State Clear (§8.1#8 · §9.3 · §12).

Phase-A: documented stub-pass (TRADING_ALLOWED).  The ATR EXTREME → no-trade
pre-filter (§4.2.2/§9.3) is active regardless.
"""

from __future__ import annotations
from pathlib import Path

from lsb.config import load_strategy, load_instrument
from lsb.signal import gate8_global_risk
from lsb.signal.types import Side, AtrState

CONFIG = Path(__file__).parent.parent / "config"


def _sp():
    return load_strategy(CONFIG / "strategy.yaml")


def _ic():
    return load_instrument(CONFIG / "EURUSD.yaml")


def test_gate8_stub_pass_normal():
    res = gate8_global_risk.evaluate(_sp(), _ic(), Side.BEAR, atr_state=AtrState.NORMAL)
    assert res.passed and res.state == "TRADING_ALLOWED"


def test_gate8_elevated_still_passes():
    res = gate8_global_risk.evaluate(_sp(), _ic(), Side.BEAR, atr_state=AtrState.ELEVATED)
    assert res.passed and res.state == "TRADING_ALLOWED"


def test_gate8_atr_extreme_no_trade():
    res = gate8_global_risk.evaluate(_sp(), _ic(), Side.BEAR, atr_state=AtrState.EXTREME)
    assert not res.passed and res.state == "ATR_EXTREME_NO_TRADE"


def test_gate8_trading_halted():
    res = gate8_global_risk.evaluate(_sp(), _ic(), Side.BEAR, trading_allowed=False)
    assert not res.passed and res.state == "TRADING_HALTED"


def test_gate8_determinism():
    sp, ic = _sp(), _ic()
    r1 = gate8_global_risk.evaluate(sp, ic, Side.BEAR)
    r2 = gate8_global_risk.evaluate(sp, ic, Side.BEAR)
    assert r1 == r2
