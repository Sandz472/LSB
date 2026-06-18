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

# Triangle-leg flatness tolerance and swing-pivot lookback are now instrument
# config (SignalParams.triangle_flat_tolerance_pct / .swing_lookback). The
# default below is used only by the bare _swing_highs/_swing_lows helpers when
# called without an explicit lookback (kept for backwards-compatible signatures).
_DEFAULT_SWING_LOOKBACK = 2


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


def _swing_highs(candles: Sequence[Candle], lookback: int = _DEFAULT_SWING_LOOKBACK) -> list[int]:
    """Indices of swing highs (bar.high ≥ all neighbors within lookback)."""
    result = []
    for i in range(lookback, len(candles) - lookback):
        if all(candles[i].high >= candles[i - j].high for j in range(1, lookback + 1)) and \
           all(candles[i].high >= candles[i + j].high for j in range(1, lookback + 1)):
            result.append(i)
    return result


def _swing_lows(candles: Sequence[Candle], lookback: int = _DEFAULT_SWING_LOOKBACK) -> list[int]:
    """Indices of swing lows (bar.low ≤ all neighbors within lookback)."""
    result = []
    for i in range(lookback, len(candles) - lookback):
        if all(candles[i].low <= candles[i - j].low for j in range(1, lookback + 1)) and \
           all(candles[i].low <= candles[i + j].low for j in range(1, lookback + 1)):
            result.append(i)
    return result


def _rising_lows(low_vals: list[float], step_pct: float, min_points: int) -> bool:
    """§6.1.1 rising-lows leg: ≥ min_points swing lows forming an ascending line,
    each confirmed low at least step_pct above the previously confirmed low.

    Greedily walks the chronological swing lows, anchoring on the first and
    counting each subsequent low that steps up by ≥ step_pct. A real ascending
    triangle has rising lows on balance; this tolerates noisy lower pivots in
    between (unlike a strict all-pivot monotonicity test) while still requiring
    a genuine, quantified climb. Returns True if the ascending sequence has at
    least min_points points.
    """
    if not low_vals:
        return False
    seq = 1
    anchor = low_vals[0]
    for v in low_vals[1:]:
        if anchor > 0 and v >= anchor * (1.0 + step_pct):
            seq += 1
            anchor = v
    return seq >= min_points


def _falling_highs(high_vals: list[float], step_pct: float, min_points: int) -> bool:
    """§6.1.2 falling-highs leg: mirror of _rising_lows for descending triangles."""
    if not high_vals:
        return False
    seq = 1
    anchor = high_vals[0]
    for v in high_vals[1:]:
        if anchor > 0 and v <= anchor * (1.0 - step_pct):
            seq += 1
            anchor = v
    return seq >= min_points


def _compression_ok(
    window: Sequence[Candle], pattern_start_idx: int, ratio: float
) -> bool:
    """§6.1.1 compression: current candle range ≤ ratio × pattern-start candle range."""
    start = max(0, min(pattern_start_idx, len(window) - 1))
    first_range = window[start].high - window[start].low
    last_range = window[-1].high - window[-1].low
    return first_range > 0 and last_range <= ratio * first_range


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

    highs_idx = _swing_highs(window, p.swing_lookback)
    lows_idx = _swing_lows(window, p.swing_lookback)

    # Need at least 2 swing highs and 2 swing lows.
    if len(highs_idx) < 2 or len(lows_idx) < 2:
        return _NO_STRUCTURE

    # --- Try ASCENDING TRIANGLE ---
    # Condition: swing highs cluster at a flat resistance; swing lows are rising.
    high_vals = [window[i].high for i in highs_idx]
    resistance = sum(high_vals) / len(high_vals)
    high_range = max(high_vals) - min(high_vals)

    if high_range <= resistance * p.triangle_flat_tolerance_pct and resistance > 0:
        # Check rising lows (§6.1.1): ≥ triangle_min_higher_lows ascending swing
        # lows, each ≥ triangle_low_step_pct above the prior confirmed low.
        low_vals = [window[i].low for i in lows_idx]
        rising = _rising_lows(low_vals, p.triangle_low_step_pct, p.triangle_min_higher_lows)
        if rising:
            pattern_start = min(highs_idx[0], lows_idx[0])
            low_xs = [float(i) for i in lows_idx]
            slope, intercept = _linear_regression(low_xs, low_vals)
            prox = _apex_proximity(current_idx, pattern_start, slope, intercept, resistance)
            if p.apex_proximity_min <= prox <= p.apex_proximity_max:
                # §6.1.1 compression: confirmed only if price has compressed into the apex.
                if not _compression_ok(window, pattern_start, p.triangle_compression_ratio):
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

    if low_range <= support * p.triangle_flat_tolerance_pct and support > 0:
        high_vals = [window[i].high for i in highs_idx]
        # Check falling highs (§6.1.2): ≥ triangle_min_higher_lows descending swing
        # highs, each ≥ triangle_low_step_pct below the prior confirmed high.
        falling = _falling_highs(high_vals, p.triangle_low_step_pct, p.triangle_min_higher_lows)
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
                    # §6.1.2 compression: confirmed only if price has compressed into the apex.
                    if not _compression_ok(window, pattern_start, p.triangle_compression_ratio):
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
