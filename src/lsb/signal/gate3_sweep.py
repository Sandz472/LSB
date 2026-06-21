"""Gate 3 — Liquidity Sweep Detected (§8.1#3 · §7.1.1 · §7.2).

Block (§7.1.1):
  zone between lowest swing-high CLOSE and highest swing-high WICK (= block HIGH).
  min width per instrument config; ≥2 touches.

Sweep (§7.2):
  - wick extends ABOVE block HIGH by ≥sweep_penetration, AND
  - candle closes below block HIGH (inside or below), AND
  - within last sweep_expiry_candles H1 bars, AND
  - false-sweep filter: NOT if price later closes beyond block in the sweep direction.

The sweep target is the block HIGH — not a mean level (§R: ADR-006 diverged).

Bull mirror: wick below support block LOW, close above it.
"""

from __future__ import annotations
from decimal import Decimal
from typing import Sequence

from lsb.config.models import InstrumentConfig, StrategyParams
from .indicators import swing_high_mask, swing_low_mask, to_price_delta
from .types import GateResult, Side

_ZERO = Decimal("0")


def _find_block_bear(
    candles: list[dict],
    sh_mask: list[bool],
    min_width: Decimal,
    min_touches: int,
    end_idx: int,
) -> tuple[Decimal | None, Decimal | None, int]:
    """Return (block_low, block_high, touch_count) for the most recent valid BEAR block.

    block_low  = lowest swing-high CLOSE
    block_high = highest swing-high WICK (high)
    """
    sh_indices = [j for j in range(end_idx, -1, -1) if sh_mask[j]]
    if len(sh_indices) < min_touches:
        return None, None, 0
    # Aggregate all swing-high closes and wicks
    sh_closes = [candles[j]["close"] for j in sh_indices]
    sh_highs  = [candles[j]["high"]  for j in sh_indices]
    block_low  = min(sh_closes)
    block_high = max(sh_highs)
    width = block_high - block_low
    if width < min_width:
        return None, None, 0
    return block_low, block_high, len(sh_indices)


def _find_block_bull(
    candles: list[dict],
    sl_mask: list[bool],
    min_width: Decimal,
    min_touches: int,
    end_idx: int,
) -> tuple[Decimal | None, Decimal | None, int]:
    """Bull mirror: block_high = highest swing-low CLOSE, block_low = lowest swing-low WICK."""
    sl_indices = [j for j in range(end_idx, -1, -1) if sl_mask[j]]
    if len(sl_indices) < min_touches:
        return None, None, 0
    sl_closes = [candles[j]["close"] for j in sl_indices]
    sl_lows   = [candles[j]["low"]   for j in sl_indices]
    block_high = max(sl_closes)
    block_low  = min(sl_lows)
    width = block_high - block_low
    if width < min_width:
        return None, None, 0
    return block_low, block_high, len(sl_indices)


def evaluate(
    candles_h1: Sequence[dict],
    sp: StrategyParams,
    ic: InstrumentConfig,
    side: Side,
) -> GateResult:
    """Return Gate 3 result for the LAST bar of *candles_h1*."""
    n = len(candles_h1)
    need = sp.sweep_expiry_candles + ic.swing_lookback * 2 + sp.block_min_touches
    if n < need:
        return GateResult(False, state="NO_SWEEP",
                          detail={"reason": "insufficient_bars", "bars": n})

    candles = list(candles_h1)
    i = n - 1

    sh_mask = swing_high_mask(candles, ic.swing_lookback)
    sl_mask = swing_low_mask(candles, ic.swing_lookback)

    # Use a reference price for pct conversions (mid of last bar)
    ref_price = (candles[i]["high"] + candles[i]["low"]) / Decimal("2")
    sweep_pen   = to_price_delta(ic.sweep_penetration, ic.sweep_pen_unit, ref_price, ic.pip_size)
    block_width = to_price_delta(ic.block_min_width, ic.block_width_unit, ref_price, ic.pip_size)

    if side is Side.BEAR:
        block_low, block_high, touches = _find_block_bear(
            candles, sh_mask, block_width, sp.block_min_touches, i
        )
        if block_high is None or block_low is None:
            return GateResult(False, state="NO_BLOCK",
                              detail={"reason": "no_valid_block"})

        # Sweep check: within last sweep_expiry_candles bars
        sweep_bar: int | None = None
        for k in range(max(0, i - sp.sweep_expiry_candles + 1), i + 1):
            c = candles[k]
            wick_above = c["high"] - block_high
            if wick_above >= sweep_pen and c["close"] < block_high:
                sweep_bar = k
                break  # use the most recent qualifying sweep

        if sweep_bar is None:
            return GateResult(False, state="NO_SWEEP",
                              detail={"block_high": str(block_high),
                                      "block_low": str(block_low)})

        # False-sweep filter: any bar AFTER sweep_bar closes above block_high?
        for k in range(sweep_bar + 1, i + 1):
            if candles[k]["close"] > block_high:
                return GateResult(False, state="FALSE_SWEEP",
                                  detail={"sweep_bar": sweep_bar,
                                          "false_close_bar": k,
                                          "block_high": str(block_high)})

        return GateResult(True, state="SWEEP_BEAR",
                          detail={"block_high": str(block_high),
                                  "block_low": str(block_low),
                                  "sweep_bar": sweep_bar,
                                  "touches": touches})

    else:
        # BULL mirror: wick below support block LOW, close above it
        block_low, block_high, touches = _find_block_bull(
            candles, sl_mask, block_width, sp.block_min_touches, i
        )
        if block_high is None or block_low is None:
            return GateResult(False, state="NO_BLOCK",
                              detail={"reason": "no_valid_block"})

        sweep_bar = None
        for k in range(max(0, i - sp.sweep_expiry_candles + 1), i + 1):
            c = candles[k]
            wick_below = block_low - c["low"]
            if wick_below >= sweep_pen and c["close"] > block_low:
                sweep_bar = k
                break

        if sweep_bar is None:
            return GateResult(False, state="NO_SWEEP",
                              detail={"block_high": str(block_high),
                                      "block_low": str(block_low)})

        for k in range(sweep_bar + 1, i + 1):
            if candles[k]["close"] < block_low:
                return GateResult(False, state="FALSE_SWEEP",
                                  detail={"sweep_bar": sweep_bar,
                                          "false_close_bar": k,
                                          "block_low": str(block_low)})

        return GateResult(True, state="SWEEP_BULL",
                          detail={"block_high": str(block_high),
                                  "block_low": str(block_low),
                                  "sweep_bar": sweep_bar,
                                  "touches": touches})
