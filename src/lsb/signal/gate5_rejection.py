"""Gate 5 — Rejection Candle Confirmed (§8.1#5 · §4.3 · ADR-004).

BEAR (short) setup: the confirmation candle is a `REJECTION_BEAR` OR
`ENGULFING_BEAR`, with a bearish close, that closes BELOW the sweep high, and
whose UPPER wick ≥ rejection_wick_body_mult × body.

§4.3 definitions:
  REJECTION_BEAR  = upper wick ≥ mult×body AND lower wick ≤ opp_max×body AND close bearish
  ENGULFING_BEAR  = body engulfs prior body AND close < prior open
The §8.1 upper-wick ≥2×body requirement applies even to the engulfing case
(engulfing alone does not exempt it) — see GATE_SPECIFICATION.md Gate 5.

BULL mirror (ADR-004 — §8.1 mirror governs, NOT §4.3's upper-wick bull def):
  REJECTION_BULL  = lower wick ≥ mult×body AND upper wick ≤ opp_max×body AND close bullish
  ENGULFING_BULL  = body engulfs prior body AND close > prior open
  closes ABOVE the sweep low; LOWER wick ≥ mult×body.

Pure function — no DB writes.  All thresholds read from StrategyParams.
Evaluated on the LAST H1 bar (the confirmation candle).
"""

from __future__ import annotations
from decimal import Decimal
from typing import Sequence

from lsb.config.models import InstrumentConfig, StrategyParams
from .types import GateResult, Side

_ZERO = Decimal("0")


def _anatomy(c: dict) -> tuple[Decimal, Decimal, Decimal]:
    """Return (body, upper_wick, lower_wick) as non-negative Decimals."""
    o, h, l, cl = c["open"], c["high"], c["low"], c["close"]
    body = abs(cl - o)
    upper_wick = h - max(o, cl)
    lower_wick = min(o, cl) - l
    return body, upper_wick, lower_wick


def evaluate(
    candles_h1: Sequence[dict],
    sp: StrategyParams,
    ic: InstrumentConfig,
    side: Side,
    sweep_high: Decimal | None = None,
    sweep_low: Decimal | None = None,
) -> GateResult:
    """Return Gate 5 result for the LAST bar of *candles_h1*.

    sweep_high / sweep_low: the swept extreme from Gate 3 (the sweep candle's
    high for BEAR, low for BULL).  When None, the close-vs-sweep check is skipped
    (used only for isolated gate fixtures); the conjunction always supplies it.
    """
    n = len(candles_h1)
    if n < 2:
        return GateResult(False, state="INSUFFICIENT_DATA", detail={"bars": n})

    c = candles_h1[n - 1]
    prev = candles_h1[n - 2]
    body, upper_wick, lower_wick = _anatomy(c)

    mult = sp.rejection_wick_body_mult
    opp_max = sp.rejection_opp_wick_body_max
    # Guard against a doji (body == 0): the ratio is undefined and the candle is
    # not a structured rejection.  Treat as no rejection.
    if body == _ZERO:
        return GateResult(False, state="NO_REJECTION", detail={"reason": "doji_zero_body"})

    if side is Side.BEAR:
        dominant_wick, opp_wick = upper_wick, lower_wick
        directional_close = c["close"] < c["open"]            # bearish body
        engulf = (c["close"] < prev["open"] and c["open"] > prev["close"]
                  and abs(c["close"] - c["open"]) > abs(prev["close"] - prev["open"]))
        close_past_sweep = (sweep_high is None) or (c["close"] < sweep_high)
        rejection_state = "REJECTION_BEAR"
        engulf_state = "ENGULFING_BEAR"
        sweep_ref = sweep_high
    else:
        dominant_wick, opp_wick = lower_wick, upper_wick
        directional_close = c["close"] > c["open"]            # bullish body
        engulf = (c["close"] > prev["open"] and c["open"] < prev["close"]
                  and abs(c["close"] - c["open"]) > abs(prev["close"] - prev["open"]))
        close_past_sweep = (sweep_low is None) or (c["close"] > sweep_low)
        rejection_state = "REJECTION_BULL"
        engulf_state = "ENGULFING_BULL"
        sweep_ref = sweep_low

    # §8.1: dominant wick ≥ mult×body required for BOTH pure-rejection and engulfing.
    wick_ok = dominant_wick >= mult * body
    opp_ok = opp_wick <= opp_max * body

    if not directional_close:
        return GateResult(False, state="NO_REJECTION",
                          detail={"reason": "close_not_directional"})
    if not wick_ok:
        return GateResult(False, state="NO_REJECTION",
                          detail={"reason": "dominant_wick_too_small",
                                  "wick": str(dominant_wick), "body": str(body),
                                  "needed": str(mult * body)})
    if not close_past_sweep:
        return GateResult(False, state="NO_REJECTION",
                          detail={"reason": "close_not_past_sweep",
                                  "close": str(c["close"]),
                                  "sweep_ref": str(sweep_ref)})

    # Now classify: pure rejection (opposite wick tiny) OR engulfing.
    is_rejection = opp_ok
    if is_rejection:
        return GateResult(True, state=rejection_state,
                          detail={"body": str(body),
                                  "dominant_wick": str(dominant_wick),
                                  "opp_wick": str(opp_wick)})
    if engulf:
        return GateResult(True, state=engulf_state,
                          detail={"body": str(body),
                                  "dominant_wick": str(dominant_wick),
                                  "engulfed_prior": True})

    return GateResult(False, state="NO_REJECTION",
                      detail={"reason": "neither_rejection_nor_engulfing",
                              "opp_wick": str(opp_wick), "needed_opp_max": str(opp_max * body)})
