"""Gate 1 — Trend State Confirmed (§8.1#1 · §5.1 · §3.2 · ADR-003 · ADR-006).

Evaluated on D1 candles (ADR-003).  ATR is D1 ATR(14) (ADR-006).
All thresholds read from StrategyParams — never hard-coded.
"""

from __future__ import annotations
from decimal import Decimal
from typing import Sequence

from lsb.config.models import InstrumentConfig, StrategyParams
from .indicators import ema, atr
from .types import GateResult, Side


def evaluate(
    candles_d1: Sequence[dict],
    sp: StrategyParams,
    ic: InstrumentConfig,
    side: Side,
) -> GateResult:
    """Return Gate 1 result for the LAST bar in *candles_d1*.

    candles_d1 must be sorted ascending.  Needs ≥ (ema_slow + slope_lookback) bars.
    """
    min_bars = sp.ema_slow + sp.slope_lookback
    if len(candles_d1) < min_bars:
        return GateResult(
            False, state="INSUFFICIENT_DATA",
            detail={"bars": len(candles_d1), "needed": min_bars},
        )

    closes = [c["close"] for c in candles_d1]
    ema21 = ema(closes, sp.ema_fast)
    ema50 = ema(closes, sp.ema_mid)
    ema89 = ema(closes, sp.ema_slow)
    atr14 = atr(list(candles_d1), sp.atr_period)

    i = len(candles_d1) - 1
    e21, e50, e89 = ema21[i], ema50[i], ema89[i]
    atr_v = atr14[i]

    if e21 is None or e50 is None or e89 is None or atr_v is None:
        return GateResult(False, state="INSUFFICIENT_DATA",
                          detail={"index": i, "ema21": e21, "ema89": e89, "atr": atr_v})

    # INVALID check 1 — EMA compression (§5.2)
    compression = abs(e21 - e89)
    threshold_compression = atr_v * sp.ema_compression_atr_mult
    if compression < threshold_compression:
        return GateResult(False, state="INVALID",
                          detail={"reason": "compression",
                                  "spread": str(compression),
                                  "threshold": str(threshold_compression)})

    # INVALID check 2 — recent EMA21/50 cross within last ema_cross_lookback bars
    for j in range(max(0, i - sp.ema_cross_lookback), i):
        prev21, prev50 = ema21[j], ema50[j]
        curr21, curr50 = ema21[j + 1], ema50[j + 1]
        if any(v is None for v in (prev21, prev50, curr21, curr50)):
            continue
        # Sign change in (EMA21 - EMA50) → cross
        diff_before = prev21 - prev50  # type: ignore[operator]
        diff_after  = curr21  - curr50  # type: ignore[operator]
        if diff_before * diff_after <= Decimal("0"):
            return GateResult(False, state="INVALID",
                              detail={"reason": "recent_cross", "at_bar": j + 1})

    # Stack + slope (mirrored by side)
    slope_min = atr_v * sp.ema_slope_atr_mult * Decimal(str(sp.slope_lookback))
    e21_prev = ema21[i - sp.slope_lookback]
    e50_prev = ema50[i - sp.slope_lookback]
    if e21_prev is None or e50_prev is None:
        return GateResult(False, state="INSUFFICIENT_DATA",
                          detail={"reason": "slope_warmup"})

    if side is Side.BEAR:
        stack_ok  = e21 < e50 < e89
        slope_ok  = (e21 - e21_prev < -slope_min) and (e50 - e50_prev < -slope_min)
        trend_state = "BEARISH"
    else:
        stack_ok  = e21 > e50 > e89
        slope_ok  = (e21 - e21_prev > slope_min) and (e50 - e50_prev > slope_min)
        trend_state = "BULLISH"

    if not stack_ok:
        return GateResult(False, state="NEUTRAL",
                          detail={"e21": str(e21), "e50": str(e50), "e89": str(e89)})
    if not slope_ok:
        return GateResult(False, state="NEUTRAL",
                          detail={"reason": "slope_insufficient",
                                  "e21_move": str(e21 - e21_prev),
                                  "threshold": str(slope_min)})

    return GateResult(True, state=trend_state,
                      detail={"e21": str(e21), "e50": str(e50), "e89": str(e89),
                              "atr": str(atr_v)})
