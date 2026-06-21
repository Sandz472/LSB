"""Gate 2 — Structure Confirmed (§8.1#2 · §6.1.1).

Evaluates the LAST bar of *candles_h4* for an ASCENDING_TRIANGLE (BEAR setup)
or DESCENDING_TRIANGLE (BULL mirror).

Key invariants:
  - Resistance level = ≥2 swing highs within ±flat_tolerance% (§6.1.1)
  - ≥2 rising lows, each ≥rising_low_min_pct% above prior (§6.1.1)
  - Duration 8–60 H4 bars; compression ≤60%; apex proximity 75–95%
  - Invalidation: close >0.30% above resistance → INVALIDATED (§6.1.1)
    (Bull mirror: close >0.30% below support → INVALIDATED)
All thresholds read from StrategyParams / InstrumentConfig — never hard-coded.
"""

from __future__ import annotations
from decimal import Decimal
from typing import Sequence

from lsb.config.models import InstrumentConfig, StrategyParams
from .indicators import swing_high_mask, swing_low_mask
from .types import GateResult, Side

_HUNDRED = Decimal("100")
_ZERO = Decimal("0")


def _pct_diff(a: Decimal, b: Decimal) -> Decimal:
    """Percentage difference of a relative to b: (a-b)/b * 100."""
    return (a - b) / b * _HUNDRED


def _find_resistance(
    highs: list[Decimal],
    sh_mask: list[bool],
    flat_tol_pct: Decimal,
    min_touches: int,
    end_idx: int,
) -> tuple[Decimal | None, list[int]]:
    """Return (resistance_level, [touch_bar_indices]) or (None, []) if not found.

    Looks backward from end_idx for a set of ≥min_touches swing highs all
    within ±flat_tol_pct of each other.  Uses the average of the group as the level.
    """
    candidates: list[int] = []
    for j in range(end_idx, -1, -1):
        if sh_mask[j]:
            candidates.append(j)

    if len(candidates) < min_touches:
        return None, []

    # Greedy: start from the most-recent pair and add earlier hits
    for start in range(len(candidates) - min_touches + 1):
        group = candidates[start: start + min_touches]
        group_highs = [highs[j] for j in group]
        avg = sum(group_highs, _ZERO) / Decimal(str(len(group_highs)))
        if all(abs(_pct_diff(h, avg)) <= flat_tol_pct for h in group_highs):
            # Expand: add earlier touches within tolerance
            for k in range(start + min_touches, len(candidates)):
                h = highs[candidates[k]]
                if abs(_pct_diff(h, avg)) <= flat_tol_pct:
                    group.append(candidates[k])
                    avg = sum(highs[j] for j in group) / Decimal(str(len(group)))
                else:
                    break
            return avg, group
    return None, []


def _find_support(
    lows: list[Decimal],
    sl_mask: list[bool],
    flat_tol_pct: Decimal,
    min_touches: int,
    end_idx: int,
) -> tuple[Decimal | None, list[int]]:
    """Bull mirror of _find_resistance — looks for ≥min_touches swing lows near each other."""
    candidates = [j for j in range(end_idx, -1, -1) if sl_mask[j]]
    if len(candidates) < min_touches:
        return None, []
    for start in range(len(candidates) - min_touches + 1):
        group = candidates[start: start + min_touches]
        group_lows = [lows[j] for j in group]
        avg = sum(group_lows, _ZERO) / Decimal(str(len(group_lows)))
        if all(abs(_pct_diff(lo, avg)) <= flat_tol_pct for lo in group_lows):
            for k in range(start + min_touches, len(candidates)):
                lo = lows[candidates[k]]
                if abs(_pct_diff(lo, avg)) <= flat_tol_pct:
                    group.append(candidates[k])
                    avg = sum(lows[j] for j in group) / Decimal(str(len(group)))
                else:
                    break
            return avg, group
    return None, []


def _find_rising_lows(
    lows: list[Decimal],
    sl_mask: list[bool],
    rising_low_min_pct: Decimal,
    min_count: int,
    start_idx: int,
    end_idx: int,
) -> list[int]:
    """Return swing-low indices forming a rising sequence (BEAR ascending triangle).

    Each successive low must be ≥rising_low_min_pct% above the prior one.
    """
    sl_indices = [j for j in range(start_idx, end_idx + 1) if sl_mask[j]]
    if len(sl_indices) < min_count:
        return []
    rising = [sl_indices[0]]
    for j in sl_indices[1:]:
        prev_low = lows[rising[-1]]
        curr_low = lows[j]
        min_level = prev_low * (_HUNDRED + rising_low_min_pct) / _HUNDRED
        if curr_low >= min_level:
            rising.append(j)
    return rising if len(rising) >= min_count else []


def _find_declining_highs(
    highs: list[Decimal],
    sh_mask: list[bool],
    declining_pct: Decimal,
    min_count: int,
    start_idx: int,
    end_idx: int,
) -> list[int]:
    """Bull mirror: each successive high must be ≥declining_pct% BELOW the prior."""
    sh_indices = [j for j in range(start_idx, end_idx + 1) if sh_mask[j]]
    if len(sh_indices) < min_count:
        return []
    declining = [sh_indices[0]]
    for j in sh_indices[1:]:
        prev_high = highs[declining[-1]]
        curr_high = highs[j]
        max_level = prev_high * (_HUNDRED - declining_pct) / _HUNDRED
        if curr_high <= max_level:
            declining.append(j)
    return declining if len(declining) >= min_count else []


def _apex_proximity(
    pattern_start: int,
    current: int,
    level_bar: int,
    trend_bar: int,
    level_price: Decimal,
    trend_price_at_level_bar: Decimal,
    slope_per_bar: Decimal,
) -> Decimal | None:
    """Fraction of the way from pattern_start to the apex (convergence point).

    The apex is where the trendline meets the horizontal level.
    Returns None if the trendline does not converge (slope is zero or wrong direction).
    """
    if slope_per_bar == _ZERO:
        return None
    # Apex bar: level_price = trend_price_at_level_bar + slope*(apex - level_bar)
    apex_bar = level_bar + (level_price - trend_price_at_level_bar) / slope_per_bar
    if apex_bar <= pattern_start:
        return None
    total = apex_bar - Decimal(str(pattern_start))
    elapsed = Decimal(str(current - pattern_start))
    return elapsed / total


def evaluate(
    candles_h4: Sequence[dict],
    sp: StrategyParams,
    ic: InstrumentConfig,
    side: Side,
) -> GateResult:
    """Return Gate 2 result for the LAST bar of *candles_h4*."""
    n = len(candles_h4)
    min_bars = sp.triangle_min_candles + ic.swing_lookback * 2 + 1
    if n < min_bars:
        return GateResult(False, state="NONE",
                          detail={"reason": "insufficient_bars", "bars": n})

    highs  = [c["high"]  for c in candles_h4]
    lows   = [c["low"]   for c in candles_h4]
    closes = [c["close"] for c in candles_h4]
    ranges = [c["high"] - c["low"] for c in candles_h4]

    sh_mask = swing_high_mask(list(candles_h4), ic.swing_lookback)
    sl_mask = swing_low_mask(list(candles_h4), ic.swing_lookback)

    i = n - 1  # evaluation bar (last)

    if side is Side.BEAR:
        # ASCENDING TRIANGLE: flat resistance, rising lows
        level, touch_bars = _find_resistance(
            highs, sh_mask, ic.flat_tolerance, sp.resistance_min_touches, i
        )
        if level is None:
            return GateResult(False, state="NONE",
                              detail={"reason": "no_resistance_level"})

        # Check invalidation: current close >0.30% above resistance
        inv_threshold = level * (_HUNDRED + sp.invalidation_break_pct) / _HUNDRED
        if closes[i] > inv_threshold:
            return GateResult(False, state="INVALIDATED",
                              detail={"resistance": str(level),
                                      "close": str(closes[i]),
                                      "threshold": str(inv_threshold)})

        # Pattern start = earliest resistance touch
        pattern_start = touch_bars[-1]
        pattern_end   = touch_bars[0]
        duration = pattern_end - pattern_start
        if duration < sp.triangle_min_candles:
            return GateResult(False, state="NONE",
                              detail={"reason": "too_short", "duration": duration})
        if duration > sp.triangle_max_candles:
            return GateResult(False, state="NONE",
                              detail={"reason": "too_long", "duration": duration})

        # Compression: current range ≤ 60% of first range in pattern
        first_range = ranges[pattern_start]
        curr_range  = ranges[i]
        if first_range == _ZERO or curr_range / first_range > sp.compression_max_ratio:
            return GateResult(False, state="NONE",
                              detail={"reason": "no_compression",
                                      "ratio": str(curr_range / first_range if first_range else "inf")})

        # Rising lows
        rising = _find_rising_lows(
            lows, sl_mask, sp.rising_low_min_pct, 2, pattern_start, i
        )
        if not rising:
            return GateResult(False, state="NONE",
                              detail={"reason": "no_rising_lows"})

        # Apex proximity
        if len(rising) >= 2:
            b1, b2 = rising[0], rising[-1]
            l1, l2 = lows[b1], lows[b2]
            slope = (l2 - l1) / Decimal(str(b2 - b1)) if b2 != b1 else _ZERO
            prox = _apex_proximity(
                pattern_start, i, b2, b2, level, l2, slope
            )
            if prox is None or not (sp.apex_proximity_lo <= prox <= sp.apex_proximity_hi):
                return GateResult(False, state="NONE",
                                  detail={"reason": "apex_proximity",
                                          "proximity": str(prox) if prox else "None"})

        return GateResult(True, state="ASCENDING_TRIANGLE",
                          detail={"resistance": str(level), "duration": duration,
                                  "touches": len(touch_bars), "rising_lows": len(rising)})

    else:
        # BULL mirror: DESCENDING TRIANGLE — flat support, declining highs
        level, touch_bars = _find_support(
            lows, sl_mask, ic.flat_tolerance, sp.resistance_min_touches, i
        )
        if level is None:
            return GateResult(False, state="NONE",
                              detail={"reason": "no_support_level"})

        # Invalidation: close >0.30% below support
        inv_threshold = level * (_HUNDRED - sp.invalidation_break_pct) / _HUNDRED
        if closes[i] < inv_threshold:
            return GateResult(False, state="INVALIDATED",
                              detail={"support": str(level),
                                      "close": str(closes[i]),
                                      "threshold": str(inv_threshold)})

        pattern_start = touch_bars[-1]
        pattern_end   = touch_bars[0]
        duration = pattern_end - pattern_start
        if duration < sp.triangle_min_candles:
            return GateResult(False, state="NONE",
                              detail={"reason": "too_short", "duration": duration})
        if duration > sp.triangle_max_candles:
            return GateResult(False, state="NONE",
                              detail={"reason": "too_long", "duration": duration})

        first_range = ranges[pattern_start]
        curr_range  = ranges[i]
        if first_range == _ZERO or curr_range / first_range > sp.compression_max_ratio:
            return GateResult(False, state="NONE",
                              detail={"reason": "no_compression"})

        declining = _find_declining_highs(
            highs, sh_mask, sp.rising_low_min_pct, 2, pattern_start, i
        )
        if not declining:
            return GateResult(False, state="NONE",
                              detail={"reason": "no_declining_highs"})

        if len(declining) >= 2:
            b1, b2 = declining[0], declining[-1]
            h1, h2 = highs[b1], highs[b2]
            slope = (h2 - h1) / Decimal(str(b2 - b1)) if b2 != b1 else _ZERO
            prox = _apex_proximity(
                pattern_start, i, b2, b2, level, h2, slope
            )
            if prox is None or not (sp.apex_proximity_lo <= prox <= sp.apex_proximity_hi):
                return GateResult(False, state="NONE",
                                  detail={"reason": "apex_proximity",
                                          "proximity": str(prox) if prox else "None"})

        return GateResult(True, state="DESCENDING_TRIANGLE",
                          detail={"support": str(level), "duration": duration,
                                  "touches": len(touch_bars),
                                  "declining_highs": len(declining)})
