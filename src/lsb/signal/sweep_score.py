"""Sweep Probability Score — NOT a gate (§7.3 → §9.3 risk tier).

The 5-factor 0–100 score sets the §9.3 position-size RISK TIER; it does NOT
qualify a trade.  The prior build wrongly promoted "score ≥ 50" to a hard gate
(§R) — this build keeps it out of the §8.1 conjunction entirely.

§7.3 weights (sum to 100, enforced by the loader):
    density 30 · wick 20 · close 20 · EMA 15 · ATR 15

Each factor is normalised to [0, 1]; score = Σ weightᵢ·factorᵢ ∈ [0, 100].
The sub-factor FORMULAS below are the deferred owner decision recorded in
ADR-007 (only the weights are pinned by §7.3).  Because the score never gates
the baseline (skip_below_50 = false), the formula choice cannot contaminate the
qualification funnel — it only colours position size, unused in Phase-A backtest.

§9.3 tier mapping: ≥80 → 1.0% · ≥50 → 0.5% · <50 → 0.25% (or skip if enabled).
ATR EXTREME / drawdown breach → 0% (ZERO), independent of the score.
"""

from __future__ import annotations
from decimal import Decimal

from lsb.config.models import StrategyParams
from .types import AtrState, RiskTier

_ZERO = Decimal("0")
_ONE = Decimal("1")
_HUNDRED = Decimal("100")
_DENSITY_TARGET = Decimal("4")   # touches at/above which density factor saturates (ADR-007)

# ATR-regime favourability factor (ADR-010): calmer regime → higher sweep quality.
# COMPRESSED (coiled, low vol) is treated as favourable as NORMAL.
_ATR_FACTOR = {
    AtrState.COMPRESSED: _ONE,
    AtrState.NORMAL: _ONE,
    AtrState.ELEVATED: Decimal("0.5"),
    AtrState.EXTREME: _ZERO,
}


def _clamp01(x: Decimal) -> Decimal:
    if x < _ZERO:
        return _ZERO
    if x > _ONE:
        return _ONE
    return x


def score(
    sp: StrategyParams,
    *,
    block_touches: int,
    penetration: Decimal,
    penetration_ref: Decimal,
    close_retrace_frac: Decimal,
    ema_delta: Decimal,
    ema_tol: Decimal,
    atr_state: AtrState,
) -> Decimal:
    """Return the 0–100 sweep-probability score (Decimal).  ADR-007 formulas.

    block_touches:      swing-high touches forming the block (density).
    penetration:        how far the sweep wick extended beyond the block edge.
    penetration_ref:    reference for normalising penetration (e.g. H1 ATR or block width).
    close_retrace_frac: 0–1, how far back inside the block the candle closed (rejection strength).
    ema_delta / ema_tol: distance of the interaction probe to the nearest EMA, and the
                         touch tolerance (closer → stronger EMA factor).
    atr_state:          volatility regime (ATR factor).
    """
    f_density = _clamp01(Decimal(block_touches) / _DENSITY_TARGET)
    f_wick = _clamp01(penetration / penetration_ref) if penetration_ref > _ZERO else _ZERO
    f_close = _clamp01(close_retrace_frac)
    f_ema = _clamp01(_ONE - ema_delta / ema_tol) if ema_tol > _ZERO else _ZERO
    f_atr = _ATR_FACTOR[atr_state]

    raw = (sp.sweep_w_density * f_density
           + sp.sweep_w_wick * f_wick
           + sp.sweep_w_close * f_close
           + sp.sweep_w_ema * f_ema
           + sp.sweep_w_atr * f_atr)
    return raw


def risk_tier_for(
    s: Decimal | None,
    sp: StrategyParams,
    atr_state: AtrState,
    drawdown_breach: bool = False,
) -> RiskTier:
    """Map a sweep score to a §9.3 risk tier.

    ATR EXTREME or a drawdown breach forces ZERO size regardless of the score.
    When the score is None (e.g. setup rejected before scoring) returns SKIP.
    """
    if atr_state is AtrState.EXTREME or drawdown_breach:
        return RiskTier.ZERO
    if s is None:
        return RiskTier.SKIP
    if s >= sp.risk_tier_high_min:
        return RiskTier.HIGH
    if s >= sp.risk_tier_mid_min:
        return RiskTier.MID
    # <50: discretionary skip (§9.3) — OFF in the validation baseline.
    return RiskTier.SKIP if sp.skip_below_50 else RiskTier.LOW
