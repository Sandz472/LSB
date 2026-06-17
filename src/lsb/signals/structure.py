"""M4 — Structure Detection Engine.

Detects ascending and descending triangles on H4 candles. Pure functions.

Spec: LSB_System_Requirements_v2.0.md §6.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Sequence

from lsb.data.config import SignalParams
from lsb.signals import Candle

# Tolerance for "flat" resistance/support: swing high/low range < this multiple
# of the resistance/support level (used to validate the horizontal leg).
_FLAT_TOLERANCE_PCT = 0.005   # 0.5% — configurable candidate; kept internal for now
_SWING_LOOKBACK = 2           # N bars on each side for pivot detection


class StructureState(Enum):
    ASCENDING_TRIANGLE = auto()   # flat resistance + rising lows → bearish setup
    DESCENDING_TRIANGLE = auto()  # flat support + falling highs → bullish setup
    FORMING = auto()              # pattern developing but criteria not yet met
    NONE = auto()                 # no qualifying structure
    INVALIDATED = auto()          # previously valid pattern broken


@dataclass(frozen=True)
class StructureResult:
    state: StructureState
    apex_proximity: float         # 0.0 if NONE / INVALIDATED / FORMING
    resistance_level: float | None  # horizontal resistance (ascending triangle)
    resistance_high: float | None   # highest swing wick (block upper boundary)
    resistance_low: float | None    # lowest swing close (block lower boundary)
    support_level: float | None     # horizontal support (descending triangle)
    support_high: float | None      # highest swing close (block upper boundary)
    support_low: float | None       # lowest swing wick (block lower boundary)
    resistance_touches: int         # confirmed touches on the horizontal leg
    pattern_start_idx: int          # index in H4 window where pattern begins


_NO_STRUCTURE = StructureResult(
    state=StructureState.NONE,
    apex_proximity=0.0,
    resistance_level=None,
    resistance_high=None,
    resistance_low=None,
    support_level=None,
    support_high=None,
    support_low=None,
    resistance_touches=0,
    pattern_start_idx=0,
)


def _swing_highs(candles: Sequence[Candle], lookback: int = _SWING_LOOKBACK) -> list[int]:
    """Indices of swing highs (bar.high ≥ all neighbors within lookback)."""
    result = []
    for i in range(lookback, len(candles) - lookback):
        if all(candles[i].high >= candles[i - j].high for j in range(1, lookback + 1)) and \
           all(candles[i].high >= candles[i + j].high for j in range(1, lookback + 1)):
            result.append(i)
    return result


def _swing_lows(candles: Sequence[Candle], lookback: int = _SWING_LOOKBACK) -> list[int]:
    """Indices of swing lows (bar.low ≤ all neighbors within lookback)."""
    result = []
    for i in range(lookback, len(candles) - lookback):
        if all(candles[i].low <= candles[i - j].low for j in range(1, lookback + 1)) and \
           all(candles[i].low <= candles[i + j].low for j in range(1, lookback + 1)):
            result.append(i)
    return result


def _linear_regression(xs: list[float], ys: list[float]) -> tuple[float, float]:
    """Returns (slope, intercept) of the least-squares line through (xs, ys)."""
    n = len(xs)
    if n < 2:
        return (0.0, ys[0] if ys else 0.0)
    sx = sum(xs)
    sy = sum(ys)
    sxy = sum(x * y for x, y in zip(xs, ys))
    sxx = sum(x * x for x in xs)
    denom = n * sxx - sx * sx
    if denom == 0:
        return (0.0, sy / n)
    slope = (n * sxy - sx * sy) / denom
    intercept = (sy - slope * sx) / n
    return (slope, intercept)


def _apex_proximity(
    current_idx: int,
    pattern_start_idx: int,
    slope: float,
    intercept: float,
    resistance: float,
) -> float:
    """Fractional progress from pattern_start to the apex (triangle convergence point).

    Apex is where the ascending support line reaches the resistance level.
    Returns 0.0 if the apex is behind the current bar or slope <= 0.
    """
    if slope <= 0:
        return 0.0
    # Time index where support line reaches resistance: t_apex = (R - b) / m
    t_apex = (resistance - intercept) / slope
    span = t_apex - pattern_start_idx
    if span <= 0:
        return 0.0
    progress = (current_idx - pattern_start_idx) / span
    return max(0.0, min(1.0, progress))


def detect_triangle(h4_candles: Sequence[Candle], p: SignalParams) -> StructureResult:
    """Detect ascending or descending triangle on H4 candles (spec §6).

    Evaluates the last `triangle_max_candles` H4 bars. Returns FORMING if
    a pattern is developing but apex proximity or candle count isn't met yet.
    """
    if len(h4_candles) < p.triangle_min_candles:
        return StructureResult(
            state=StructureState.FORMING,
            apex_proximity=0.0,
            resistance_level=None,
            resistance_high=None,
            resistance_low=None,
            support_level=None,
            support_high=None,
            support_low=None,
            resistance_touches=0,
            pattern_start_idx=0,
        )

    # Use the last triangle_max_candles bars.
    window = list(h4_candles[-p.triangle_max_candles:])
    current_idx = len(window) - 1

    highs_idx = _swing_highs(window)
    lows_idx = _swing_lows(window)

    # Need at least 2 swing highs and 2 swing lows.
    if len(highs_idx) < 2 or len(lows_idx) < 2:
        return _NO_STRUCTURE

    # --- Try ASCENDING TRIANGLE ---
    # Condition: swing highs cluster at a flat resistance; swing lows are rising.
    high_vals = [window[i].high for i in highs_idx]
    resistance = sum(high_vals) / len(high_vals)
    high_range = max(high_vals) - min(high_vals)

    if high_range <= resistance * _FLAT_TOLERANCE_PCT and resistance > 0:
        # Check rising lows.
        low_vals = [window[i].low for i in lows_idx]
        rising = all(low_vals[j] > low_vals[j - 1] for j in range(1, len(low_vals)))
        if rising:
            pattern_start = min(highs_idx[0], lows_idx[0])
            low_xs = [float(i) for i in lows_idx]
            slope, intercept = _linear_regression(low_xs, low_vals)
            prox = _apex_proximity(current_idx, pattern_start, slope, intercept, resistance)
            if p.apex_proximity_min <= prox <= p.apex_proximity_max:
                # Block boundaries (spec §7.1.1):
                # upper = highest swing high wick, lower = lowest swing high close
                res_high = max(window[i].high for i in highs_idx)
                res_low = min(window[i].close for i in highs_idx)
                return StructureResult(
                    state=StructureState.ASCENDING_TRIANGLE,
                    apex_proximity=prox,
                    resistance_level=resistance,
                    resistance_high=res_high,
                    resistance_low=res_low,
                    support_level=None,
                    support_high=None,
                    support_low=None,
                    resistance_touches=len(highs_idx),
                    pattern_start_idx=pattern_start,
                )
            elif prox < p.apex_proximity_min:
                return StructureResult(
                    state=StructureState.FORMING,
                    apex_proximity=prox,
                    resistance_level=resistance,
                    resistance_high=None,
                    resistance_low=None,
                    support_level=None,
                    support_high=None,
                    support_low=None,
                    resistance_touches=len(highs_idx),
                    pattern_start_idx=pattern_start,
                )

    # --- Try DESCENDING TRIANGLE ---
    # Condition: swing lows cluster at a flat support; swing highs are falling.
    low_vals = [window[i].low for i in lows_idx]
    support = sum(low_vals) / len(low_vals)
    low_range = max(low_vals) - min(low_vals)

    if low_range <= support * _FLAT_TOLERANCE_PCT and support > 0:
        high_vals = [window[i].high for i in highs_idx]
        falling = all(high_vals[j] < high_vals[j - 1] for j in range(1, len(high_vals)))
        if falling:
            pattern_start = min(highs_idx[0], lows_idx[0])
            high_xs = [float(i) for i in highs_idx]
            slope, intercept = _linear_regression(high_xs, high_vals)
            # For descending triangle, apex is where the falling resistance meets support.
            # slope is negative; apex: t = (support - intercept) / slope
            if slope < 0:
                t_apex = (support - intercept) / slope
                span = t_apex - pattern_start
                prox = (
                    max(0.0, min(1.0, (current_idx - pattern_start) / span))
                    if span > 0 else 0.0
                )
                if p.apex_proximity_min <= prox <= p.apex_proximity_max:
                    # Block boundaries (spec §7.1.2 mirror of 7.1.1):
                    # upper = highest swing low close, lower = lowest swing low wick
                    sup_high = max(window[i].close for i in lows_idx)
                    sup_low = min(window[i].low for i in lows_idx)
                    return StructureResult(
                        state=StructureState.DESCENDING_TRIANGLE,
                        apex_proximity=prox,
                        resistance_level=None,
                        resistance_high=None,
                        resistance_low=None,
                        support_level=support,
                        support_high=sup_high,
                        support_low=sup_low,
                        resistance_touches=len(lows_idx),
                        pattern_start_idx=pattern_start,
                    )
                elif prox < p.apex_proximity_min:
                    return StructureResult(
                        state=StructureState.FORMING,
                        apex_proximity=prox,
                        resistance_level=None,
                        resistance_high=None,
                        resistance_low=None,
                        support_level=support,
                        support_high=None,
                        support_low=None,
                        resistance_touches=len(lows_idx),
                        pattern_start_idx=pattern_start,
                    )

    return _NO_STRUCTURE
