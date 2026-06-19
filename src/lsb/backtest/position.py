"""Position lifecycle: pending → filled → managed → closed.

Each Position is one leg. Multiple concurrent legs per instrument are held
by PositionBook (book.py).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any


class PosState(Enum):
    PENDING = auto()   # order placed, awaiting fill
    FILLED = auto()    # order filled, no management applied yet
    MANAGED = auto()   # at least one management rule (BE/trail) applied
    CLOSED = auto()    # position closed


@dataclass
class PartialExitEvent:
    """Records a §11.4 50%-partial-exit trigger (deferred sizing to A10)."""
    price: float
    ts: Any
    r_at_event: float
    reason: str


@dataclass
class Position:
    instrument: str
    direction: str          # 'long' | 'short'
    entry_price: float
    stop: float             # current stop; ratchets up (long) or down (short)
    target: float
    risk: float             # |entry - initial_stop|, frozen at fill time
    config_hash: str

    state: PosState = field(default=PosState.PENDING)

    # Fill metadata
    fill_ts: Any = field(default=None)
    fill_bar: int = field(default=0)

    # Management state flags
    breakeven_applied: bool = field(default=False)
    trail_applied: bool = field(default=False)

    # §11.4 50% partial exit events (may have multiple across a trade)
    partial_exits: list[PartialExitEvent] = field(default_factory=list)

    # A7 cost fields — recorded at close, do NOT affect r_at_close (A10 aggregates).
    # commission: currency/lot (scale by contract size in A10).
    # swap: price-units = nights_held × swap_pts × pip_size (convert via contract size in A10).
    commission: float = field(default=0.0)
    swap: float = field(default=0.0)

    # Close metadata
    close_price: float | None = field(default=None)
    close_ts: Any = field(default=None)
    close_bar: int | None = field(default=None)
    close_reason: str | None = field(default=None)
    r_at_close: float | None = field(default=None)

    def r_now(self, price: float) -> float:
        """Current floating R-multiple at given price (1 notional unit)."""
        if self.risk == 0.0:
            return 0.0
        sign = 1.0 if self.direction == 'long' else -1.0
        return sign * (price - self.entry_price) / self.risk

    def close(self, price: float, ts: Any, bar: int, reason: str) -> None:
        self.close_price = price
        self.close_ts = ts
        self.close_bar = bar
        self.close_reason = reason
        self.r_at_close = self.r_now(price)
        self.state = PosState.CLOSED
