"""§8.1 conjunction — evaluate all 8 gates on one H1 bar → SignalResult.

§8.1: all eight conditions must be TRUE on the same H1 bar; a single FALSE
disqualifies.  This module is the ONLY place the 8 gates are combined; the
sweep-probability score is computed alongside but is NOT part of the conjunction
(it sets risk tier only — §7.3/§9.3).

Timeframes (per gate spec):
  Gate 1 (trend)      → D1 candles  (ADR-003)
  Gate 2 (structure)  → H4 candles
  Gates 3-7           → H1 candles
  Gate 8 (global risk)→ regime/account state

Gates 4, 5, 7 depend on Gate 3's sweep; when Gate 3 fails they are recorded as
FALSE/DEP_UNMET (still a recorded result, so the signal row is complete for
100% of evaluated candles — A5 acceptance).

verdict:
  INVALIDATED  if structure (Gate 2) reached §6.1.1/.2 invalidation,
  QUALIFIED    if all 8 gates passed,
  REJECTED     otherwise.

Deterministic: pure function of the candle slices + config + explicit inputs.
"""

from __future__ import annotations
from decimal import Decimal
from typing import Sequence

from lsb.config.models import InstrumentConfig, StrategyParams
from . import (gate1_trend, gate2_structure, gate3_sweep, gate4_ema,
               gate5_rejection, gate6_session, gate7_rr, gate8_global_risk)
from . import sweep_score as _sweep
from .indicators import atr as _atr
from .types import (GateResult, Side, AtrState, Verdict, RiskTier, SignalResult)

_ZERO = Decimal("0")
_ONE = Decimal("1")
_DEP_UNMET = GateResult(False, state="DEP_UNMET",
                        detail={"reason": "upstream Gate 3 (sweep) not satisfied"})


def _sweep_score_for(
    side: Side, candles_h1: Sequence[dict], sp: StrategyParams, ic: InstrumentConfig,
    g3: GateResult, g4: GateResult, atr_h1: Decimal | None, atr_state: AtrState,
) -> Decimal | None:
    """Best-effort §7.3 score when a block+sweep exist; else None (ADR-007 formulas)."""
    if not g3.passed:
        return None
    d = g3.detail
    block_high = Decimal(d["block_high"])
    block_low = Decimal(d["block_low"])
    sweep_bar = d["sweep_bar"]
    sc = candles_h1[sweep_bar]

    if side is Side.BEAR:
        penetration = sc["high"] - block_high
    else:
        penetration = block_low - sc["low"]
    rng = sc["high"] - sc["low"]
    if side is Side.BEAR:
        retrace = (sc["high"] - sc["close"]) / rng if rng > _ZERO else _ZERO
    else:
        retrace = (sc["close"] - sc["low"]) / rng if rng > _ZERO else _ZERO

    # EMA factor inputs from Gate 4 detail (passed or not).
    ema_tol = Decimal(g4.detail.get("delta") or g4.detail.get("touch_delta") or "0")
    if g4.passed:
        ema_delta = abs(Decimal(g4.detail["probe"]) - Decimal(g4.detail["ema_val"]))
    else:
        ema_delta = ema_tol  # factor → 0 when no touch

    ref = atr_h1 if (atr_h1 is not None and atr_h1 > _ZERO) else (block_high - block_low)
    return _sweep.score(
        sp,
        block_touches=int(d.get("touches", 0)),
        penetration=penetration,
        penetration_ref=ref,
        close_retrace_frac=retrace,
        ema_delta=ema_delta,
        ema_tol=ema_tol,
        atr_state=atr_state,
    )


def evaluate(
    instrument: str,
    side: Side,
    candles_d1: Sequence[dict],
    candles_h4: Sequence[dict],
    candles_h1: Sequence[dict],
    sp: StrategyParams,
    ic: InstrumentConfig,
    *,
    atr_state: AtrState = AtrState.NORMAL,
    trading_allowed: bool = True,
    news_windows: Sequence = (),
) -> SignalResult:
    """Evaluate the §8.1 conjunction for the LAST H1 bar.  Returns a SignalResult."""
    ts = candles_h1[-1]["ts"]

    # H1 ATR(14) at the entry bar — for Gate 7 target and the sweep score.
    atr_series = _atr(list(candles_h1), sp.atr_period)
    atr_h1 = atr_series[-1] if atr_series else None

    g1 = gate1_trend.evaluate(candles_d1, sp, ic, side)
    g2 = gate2_structure.evaluate(candles_h4, sp, ic, side)
    g3 = gate3_sweep.evaluate(candles_h1, sp, ic, side)

    # Gate-3-dependent gates.
    if g3.passed:
        sweep_bar = g3.detail["sweep_bar"]
        block_high = Decimal(g3.detail["block_high"])
        block_low = Decimal(g3.detail["block_low"])
        sweep_high = candles_h1[sweep_bar]["high"]
        sweep_low = candles_h1[sweep_bar]["low"]

        g4 = gate4_ema.evaluate(candles_h1, sp, ic, side, sweep_bar=sweep_bar)
        g5 = gate5_rejection.evaluate(candles_h1, sp, ic, side,
                                      sweep_high=sweep_high, sweep_low=sweep_low)
        # Stop anchored on the confirmation candle's wick; opposing block edge = liquidity pool.
        rej = candles_h1[-1]
        rej_extreme = rej["high"] if side is Side.BEAR else rej["low"]
        pool = block_low if side is Side.BEAR else block_high
        g7 = gate7_rr.evaluate(candles_h1, sp, ic, side,
                               rejection_extreme=rej_extreme, atr_h1=atr_h1,
                               atr_state=atr_state, liquidity_pool=pool)
    else:
        g4 = g5 = g7 = _DEP_UNMET

    g6 = gate6_session.evaluate(candles_h1[-1], sp, ic, side, news_windows=news_windows)
    g8 = gate8_global_risk.evaluate(sp, ic, side, atr_state=atr_state,
                                    trading_allowed=trading_allowed)

    gates = (g1, g2, g3, g4, g5, g6, g7, g8)
    all_gates = all(g.passed for g in gates)

    if g2.state == "INVALIDATED":
        verdict = Verdict.INVALIDATED
    elif all_gates:
        verdict = Verdict.QUALIFIED
    else:
        verdict = Verdict.REJECTED

    s = _sweep_score_for(side, candles_h1, sp, ic, g3, g4, atr_h1, atr_state)
    tier = _sweep.risk_tier_for(s, sp, atr_state)

    reasons = tuple(
        f"gate{idx+1}:{g.state}" for idx, g in enumerate(gates) if not g.passed
    )

    return SignalResult(
        instrument=instrument, ts=ts, side=side,
        gates=gates, all_gates=all_gates, verdict=verdict,
        sweep_score=s, risk_tier=tier, reasons=reasons,
    )
