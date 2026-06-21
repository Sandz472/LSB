"""Gate 4 — EMA Interaction Confirmed (§8.1#4).

The sweep candle OR confirmation candle HIGH (BEAR) / LOW (BULL) must touch or
penetrate EMA21 or EMA50 on H1 — within ema_touch threshold from config.

This is a HARD gate in §8.1.  The prior build dropped it (see §R).

Evaluated on H1 candles.  EMAs are H1 EMAs (§4.1, ADR-003).
All thresholds read from InstrumentConfig / StrategyParams.
"""

from __future__ import annotations
from decimal import Decimal
from typing import Sequence

from lsb.config.models import InstrumentConfig, StrategyParams
from .indicators import ema, to_price_delta
from .types import GateResult, Side

_ZERO = Decimal("0")


def evaluate(
    candles_h1: Sequence[dict],
    sp: StrategyParams,
    ic: InstrumentConfig,
    side: Side,
    sweep_bar: int | None = None,
) -> GateResult:
    """Return Gate 4 result for the LAST bar of *candles_h1*.

    sweep_bar: index of the sweep candle from Gate 3 (optional).  When provided,
    also checks that bar in addition to the last bar (confirmation candle).
    When None, only the last bar is checked.
    """
    n = len(candles_h1)
    if n < sp.ema_mid + 1:
        return GateResult(False, state="INSUFFICIENT_DATA",
                          detail={"bars": n, "needed": sp.ema_mid + 1})

    closes = [c["close"] for c in candles_h1]
    ema21_series = ema(closes, sp.ema_fast)
    ema50_series = ema(closes, sp.ema_mid)

    i = n - 1
    bars_to_check = [i]
    if sweep_bar is not None and sweep_bar != i:
        bars_to_check.append(sweep_bar)

    for bar_idx in bars_to_check:
        e21 = ema21_series[bar_idx]
        e50 = ema50_series[bar_idx]
        if e21 is None and e50 is None:
            continue

        # Reference price for pct unit conversion
        c = candles_h1[bar_idx]
        ref_price = (c["high"] + c["low"]) / Decimal("2")
        touch_delta = to_price_delta(ic.ema_touch, ic.ema_touch_unit, ref_price, ic.pip_size)

        # BEAR: check candle HIGH against EMA values; BULL: check candle LOW
        probe = c["high"] if side is Side.BEAR else c["low"]

        touched21 = (e21 is not None and abs(probe - e21) <= touch_delta)
        touched50 = (e50 is not None and abs(probe - e50) <= touch_delta)

        if touched21 or touched50:
            which = "EMA21" if touched21 else "EMA50"
            return GateResult(True, state="EMA_TOUCHED",
                              detail={"bar": bar_idx,
                                      "ema": which,
                                      "probe": str(probe),
                                      "ema_val": str(e21 if touched21 else e50),
                                      "delta": str(touch_delta)})

    # No touch on any checked bar
    last_e21 = ema21_series[i]
    last_e50 = ema50_series[i]
    last_c   = candles_h1[i]
    probe    = last_c["high"] if side is Side.BEAR else last_c["low"]
    ref_price = (last_c["high"] + last_c["low"]) / Decimal("2")
    touch_delta = to_price_delta(ic.ema_touch, ic.ema_touch_unit, ref_price, ic.pip_size)
    return GateResult(False, state="NO_EMA_TOUCH",
                      detail={"probe": str(probe),
                              "ema21": str(last_e21),
                              "ema50": str(last_e50),
                              "touch_delta": str(touch_delta)})
