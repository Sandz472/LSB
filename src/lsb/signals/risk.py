"""Pure R:R and structural-stop helpers for Gate 8.

No position sizing, no account equity, no broker state — those belong to
Phase B (M8/M11). These functions only compute the candle/config math
that Gate 8 needs to decide whether a trade is structurally viable.

Spec: LSB_System_Requirements_v2.0.md §9.1 (structural stop), §9.4 (target
hierarchy). Entry price is the rejection-candle break trigger per §10.1.
"""

from __future__ import annotations

from typing import Sequence

from lsb.data.config import SignalParams
from lsb.signals import Candle
from lsb.signals.indicators import ATRState


def structural_stop(
    rejection_candle: Candle,
    direction: str,
    atr_state: ATRState | None,
    p: SignalParams,
    pip_size: float,
) -> float | None:
    """Structural stop level per §9.1.

    Bear (short): stop = rejection_candle.high + buffer.
    Bull (long):  stop = rejection_candle.low  – buffer.
    Buffer is sl_buffer_pips * pip_size for NORMAL ATR, sl_buffer_pips_elevated
    * pip_size for ELEVATED ATR (doubles for elevated volatility per §9.1).
    Returns None when atr_state is unavailable (insufficient window data).
    """
    if atr_state is None:
        return None
    buf_pips = (
        p.sl_buffer_pips_elevated if atr_state == ATRState.ELEVATED else p.sl_buffer_pips
    )
    buffer = buf_pips * pip_size
    if direction == 'short':
        return rejection_candle.high + buffer
    return rejection_candle.low - buffer


def rr_target(
    entry: float,
    stop: float,
    h1_window: Sequence[Candle],
    atr: float,
    direction: str,
    p: SignalParams,
) -> tuple[float, float]:
    """Adaptive target price and R:R ratio per §9.4.

    Candidate hierarchy: 2.5R floor · nearest liquidity pool · ATR×3.
    Picks the closest candidate (most conservative) that is ≥ min_rr_ratio × risk
    from entry. Falls back to the 2.5R floor if no pool is found.
    Returns (target_price, rr_ratio).
    """
    risk = abs(entry - stop)
    if risk == 0.0:
        return (entry, 0.0)

    sign = -1.0 if direction == 'short' else 1.0
    min_dist = p.min_rr_ratio * risk

    t_2_5r = entry + sign * min_dist
    t_atr3 = entry + sign * 3.0 * atr
    pool = _nearest_liquidity_pool(h1_window, entry, min_dist, direction, p.swing_lookback)

    candidates: list[float] = [t_2_5r]
    if pool is not None:
        candidates.append(pool)
    if abs(t_atr3 - entry) >= min_dist:
        candidates.append(t_atr3)

    # Closest to entry (most conservative) among all valid candidates.
    # Short: highest candidate price; Long: lowest candidate price.
    target = max(candidates) if direction == 'short' else min(candidates)
    rr_ratio = abs(entry - target) / risk
    return (target, rr_ratio)


def _nearest_liquidity_pool(
    h1_window: Sequence[Candle],
    entry: float,
    min_dist: float,
    direction: str,
    swing_lookback: int,
) -> float | None:
    """Nearest swing extreme that is ≥ min_dist beyond entry in trade direction.

    Short: scan for swing lows below entry (trade targets price to fall).
    Long:  scan for swing highs above entry.
    Returns the closest qualifying level, or None if none found.
    """
    n = len(h1_window)
    best: float | None = None

    for i in range(swing_lookback, n - swing_lookback):
        c = h1_window[i]
        neighbours = [h1_window[j] for j in range(i - swing_lookback, i + swing_lookback + 1) if j != i]

        if direction == 'short':
            if all(c.low <= nb.low for nb in neighbours):
                level = c.low
                if entry - level >= min_dist:
                    if best is None or level > best:
                        best = level
        else:
            if all(c.high >= nb.high for nb in neighbours):
                level = c.high
                if level - entry >= min_dist:
                    if best is None or level < best:
                        best = level

    return best
