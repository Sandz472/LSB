"""Trade management — §11 pure functions.

All functions take a Position and return a bool indicating whether state
changed. They mutate the position in place.

§11.2  Breakeven: move stop to entry when floating R ≥ 1.0. One-way ratchet.
§11.3  EMA21 trail: trail stop behind EMA21 when R ≥ 1.5. One-way ratchet;
       swing fallback if the nearest recent pivot is tighter.
§11.4  Defensive exits (called by loop, not here — these are predicates only):
         - Opposing sweep   → partial exit event (50%, deferred to A10)
         - Structure break  → full close all legs
         - EXTREME ATR      → full close all legs
§10.3  Order expiry (predicate): pending order expires if not filled within
       4 bars of placement or if sweep has been invalidated.
"""

from __future__ import annotations

from typing import Sequence

from lsb.signals import Candle
from lsb.backtest.position import PosState, PartialExitEvent, Position


# ---------------------------------------------------------------------------
# Stop/target checks
# ---------------------------------------------------------------------------

def stop_hit(pos: Position, candle: Candle) -> bool:
    """True if the candle's range reached the current stop."""
    if pos.direction == 'long':
        return candle.low <= pos.stop
    return candle.high >= pos.stop


def target_hit(pos: Position, candle: Candle) -> bool:
    """True if the candle's range reached the target."""
    if pos.direction == 'long':
        return candle.high >= pos.target
    return candle.low <= pos.target


# ---------------------------------------------------------------------------
# §11.2 Breakeven
# ---------------------------------------------------------------------------

def apply_breakeven(pos: Position, high_water_price: float) -> bool:
    """§11.2: move stop to entry when R ≥ 1.0. Returns True if applied."""
    if pos.breakeven_applied:
        return False
    if pos.r_now(high_water_price) >= 1.0:
        pos.stop = pos.entry_price
        pos.breakeven_applied = True
        if pos.state == PosState.FILLED:
            pos.state = PosState.MANAGED
        return True
    return False


# ---------------------------------------------------------------------------
# §11.3 EMA21 trail
# ---------------------------------------------------------------------------

def apply_ema_trail(
    pos: Position,
    current_price: float,
    ema21: float,
    swing_stop: float | None,
) -> bool:
    """§11.3: trail stop behind EMA21 when R ≥ 1.5. One-way ratchet.

    swing_stop is the nearest recent pivot on the correct side (long: swing low,
    short: swing high). If it's tighter than EMA21, prefer it.
    Returns True if the stop was moved.
    """
    if pos.r_now(current_price) < 1.5:
        return False

    if pos.direction == 'long':
        # Trail candidate: EMA21; tighten with swing low if higher
        candidate = ema21
        if swing_stop is not None and swing_stop > candidate:
            candidate = swing_stop
        if candidate > pos.stop:
            pos.stop = candidate
            pos.trail_applied = True
            if pos.state == PosState.FILLED:
                pos.state = PosState.MANAGED
            return True
    else:
        # Trail candidate: EMA21; tighten with swing high if lower
        candidate = ema21
        if swing_stop is not None and swing_stop < candidate:
            candidate = swing_stop
        if candidate < pos.stop:
            pos.stop = candidate
            pos.trail_applied = True
            if pos.state == PosState.FILLED:
                pos.state = PosState.MANAGED
            return True

    return False


# ---------------------------------------------------------------------------
# §11.4 Partial exit event (50% — deferred sizing)
# ---------------------------------------------------------------------------

def record_partial_exit(pos: Position, price: float, ts: object, reason: str) -> None:
    """Record a §11.4 50%-partial-exit event on the leg.

    The leg continues; fractional P&L calculation is deferred to A10.
    """
    pos.partial_exits.append(PartialExitEvent(
        price=price,
        ts=ts,
        r_at_event=pos.r_now(price),
        reason=reason,
    ))
    if pos.state == PosState.FILLED:
        pos.state = PosState.MANAGED


# ---------------------------------------------------------------------------
# §10.3 Order expiry predicate
# ---------------------------------------------------------------------------

EXPIRY_BARS = 4   # pending order expires after this many bars without fill


def order_expired(bar_placed: int, current_bar: int) -> bool:
    """§10.3: True if the pending order has been open ≥ EXPIRY_BARS without fill."""
    return (current_bar - bar_placed) >= EXPIRY_BARS


# ---------------------------------------------------------------------------
# Swing stop helper (for EMA21 trail fallback)
# ---------------------------------------------------------------------------

def nearest_swing_stop(
    h1_window: Sequence[Candle],
    entry_price: float,
    direction: str,
    lookback: int = 2,
) -> float | None:
    """Return the nearest swing pivot on the protective side of entry.

    Long: nearest swing LOW below entry.
    Short: nearest swing HIGH above entry.
    Uses the same pivot detection as signals/risk.py (±lookback bars).
    """
    n = len(h1_window)
    best: float | None = None

    for i in range(lookback, n - lookback):
        c = h1_window[i]
        nbrs = [h1_window[j] for j in range(i - lookback, i + lookback + 1) if j != i]

        if direction == 'long':
            if all(c.low <= nb.low for nb in nbrs) and c.low < entry_price:
                if best is None or c.low > best:
                    best = c.low
        else:
            if all(c.high >= nb.high for nb in nbrs) and c.high > entry_price:
                if best is None or c.high < best:
                    best = c.high

    return best
