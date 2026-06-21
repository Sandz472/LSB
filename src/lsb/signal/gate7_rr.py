"""Gate 7 — Risk:Reward Minimum (§8.1#7 · §9.1 · §9.4).

Structural stop (§9.1):
  BEAR → rejection-candle wick HIGH + stop buffer   (elevated buffer if ATR ELEVATED/EXTREME)
  BULL → rejection-candle wick LOW  − stop buffer

Target hierarchy (§9.4): next liquidity pool / ATR×3, with a 2.5R FLOOR.
The 2.5R floor is the *minimum acceptable* reward — it is NOT itself a placeable
target.  The gate asks: does a real structural target (a liquidity pool, or the
ATR×3 level) sit at ≥ rr_min R?  Among the structural candidates that clear the
floor, the CLOSEST (smallest R:R) is chosen.  PASS iff R:R ≥ rr_min.

ATR state is an EXPLICIT input (default NORMAL).  The numeric classifier that
derives it from an ATR series is deferred to ADR-008 (pinned before backtest
integration); it is kept OUT of this decision path so A5 invents no thresholds.

Pure function — no DB writes.  All thresholds read from config.
"""

from __future__ import annotations
from decimal import Decimal
from typing import Sequence

from lsb.config.models import InstrumentConfig, StrategyParams
from .indicators import to_price_delta
from .types import GateResult, Side, AtrState

_ZERO = Decimal("0")


def evaluate(
    candles_h1: Sequence[dict],
    sp: StrategyParams,
    ic: InstrumentConfig,
    side: Side,
    rejection_extreme: Decimal,
    atr_h1: Decimal | None,
    atr_state: AtrState = AtrState.NORMAL,
    liquidity_pool: Decimal | None = None,
) -> GateResult:
    """Return Gate 7 result for the LAST bar of *candles_h1* (the entry candle).

    rejection_extreme: rejection-candle wick HIGH (BEAR) / LOW (BULL) — stop anchor.
    atr_h1:            H1 ATR(14) at the entry bar — the ATR×3 target candidate.
    atr_state:         volatility regime → selects normal vs elevated stop buffer.
    liquidity_pool:    optional "next liquidity pool" price (e.g. opposing block edge).
    """
    n = len(candles_h1)
    if n < 1:
        return GateResult(False, state="INSUFFICIENT_DATA", detail={"bars": n})

    entry = candles_h1[n - 1]["close"]

    # Buffer: elevated for ELEVATED or EXTREME (§9.1 "4 pip if ATR ELEVATED").
    buf_val = (ic.stop_buffer if atr_state is AtrState.NORMAL
               else ic.stop_buffer_elev)
    buffer = to_price_delta(buf_val, ic.stop_buffer_unit, rejection_extreme, ic.pip_size)

    if side is Side.BEAR:
        stop = rejection_extreme + buffer
        risk = stop - entry
        # Structural target candidates BELOW entry.
        candidates: list[tuple[str, Decimal]] = []
        if atr_h1 is not None:
            candidates.append(("atr_x3", entry - atr_h1 * sp.atr_target_mult))
        if liquidity_pool is not None and liquidity_pool < entry:
            candidates.append(("liquidity_pool", liquidity_pool))
        reward = lambda t: entry - t
    else:
        stop = rejection_extreme - buffer
        risk = entry - stop
        candidates = []
        if atr_h1 is not None:
            candidates.append(("atr_x3", entry + atr_h1 * sp.atr_target_mult))
        if liquidity_pool is not None and liquidity_pool > entry:
            candidates.append(("liquidity_pool", liquidity_pool))
        reward = lambda t: t - entry

    if risk <= _ZERO:
        return GateResult(False, state="INVALID_GEOMETRY",
                          detail={"reason": "stop not beyond entry",
                                  "entry": str(entry), "stop": str(stop)})
    if not candidates:
        return GateResult(False, state="NO_TARGET",
                          detail={"reason": "no ATR and no liquidity pool"})

    # R:R for each structural candidate; keep those clearing the floor.
    scored = [(name, t, reward(t) / risk) for name, t in candidates]
    eligible = [(name, t, rr) for name, t, rr in scored if rr >= sp.rr_min]

    if not eligible:
        best = max(scored, key=lambda x: x[2])
        return GateResult(False, state="RR_BELOW_MIN",
                          detail={"best_rr": str(best[2]), "rr_min": str(sp.rr_min),
                                  "risk": str(risk), "target": str(best[1]),
                                  "via": best[0]})

    # Closest candidate not below the floor = smallest qualifying R:R.
    name, target, rr = min(eligible, key=lambda x: x[2])
    return GateResult(True, state="RR_OK",
                      detail={"rr": str(rr), "entry": str(entry), "stop": str(stop),
                              "target": str(target), "via": name, "risk": str(risk),
                              "atr_state": atr_state.value})
