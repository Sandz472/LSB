"""Sweep-probability score tests (§7.3 → §9.3 risk tier; NOT a gate). ADR-010 formulas."""

from __future__ import annotations
from decimal import Decimal
from pathlib import Path

from lsb.config import load_strategy
from lsb.signal import sweep_score
from lsb.signal.types import AtrState, RiskTier

D = Decimal
CONFIG = Path(__file__).parent.parent / "config"


def _sp():
    return load_strategy(CONFIG / "strategy.yaml")


def test_score_perfect_is_100():
    s = sweep_score.score(
        _sp(), block_touches=4, penetration=D("1"), penetration_ref=D("1"),
        close_retrace_frac=D("1"), ema_delta=D("0"), ema_tol=D("0.0003"),
        atr_state=AtrState.NORMAL,
    )
    assert s == D("100")


def test_score_floor_is_0():
    s = sweep_score.score(
        _sp(), block_touches=0, penetration=D("0"), penetration_ref=D("1"),
        close_retrace_frac=D("0"), ema_delta=D("1"), ema_tol=D("0.0003"),
        atr_state=AtrState.EXTREME,
    )
    assert s == D("0")


def test_score_in_range_and_weighted():
    sp = _sp()
    s = sweep_score.score(
        sp, block_touches=2, penetration=D("0.0005"), penetration_ref=D("0.0010"),
        close_retrace_frac=D("0.5"), ema_delta=D("0.0001"), ema_tol=D("0.0003"),
        atr_state=AtrState.ELEVATED,
    )
    assert D("0") <= s <= D("100")


def test_risk_tier_mapping():
    sp = _sp()
    assert sweep_score.risk_tier_for(D("85"), sp, AtrState.NORMAL) is RiskTier.HIGH
    assert sweep_score.risk_tier_for(D("60"), sp, AtrState.NORMAL) is RiskTier.MID
    assert sweep_score.risk_tier_for(D("30"), sp, AtrState.NORMAL) is RiskTier.LOW
    # boundary values (≥ is inclusive)
    assert sweep_score.risk_tier_for(D("80"), sp, AtrState.NORMAL) is RiskTier.HIGH
    assert sweep_score.risk_tier_for(D("50"), sp, AtrState.NORMAL) is RiskTier.MID


def test_risk_tier_extreme_forces_zero():
    sp = _sp()
    assert sweep_score.risk_tier_for(D("95"), sp, AtrState.EXTREME) is RiskTier.ZERO
    assert sweep_score.risk_tier_for(D("95"), sp, AtrState.NORMAL, drawdown_breach=True) is RiskTier.ZERO


def test_risk_tier_none_is_skip():
    assert sweep_score.risk_tier_for(None, _sp(), AtrState.NORMAL) is RiskTier.SKIP


def test_skip_below_50_off_by_default():
    """Baseline keeps the score non-gating: a <50 score is LOW tier, never SKIP."""
    sp = _sp()
    assert sp.skip_below_50 is False
    assert sweep_score.risk_tier_for(D("10"), sp, AtrState.NORMAL) is RiskTier.LOW
