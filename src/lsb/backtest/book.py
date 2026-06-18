"""PositionBook — manages concurrent legs per instrument.

Implements the ADR-003 pyramiding policy:
  - same-direction only (no hedging)
  - winner-only: newest active leg must be ≥ pyramid_add_at_r before adding
  - capped at pyramid_max_legs concurrent active legs

Book-wide §11.4 exits (opposing sweep, structure break) flatten all legs.
Each leg is independently managed by manage.py (§11.2/11.3/11.4).
"""

from __future__ import annotations

from lsb.data.config import SignalParams
from lsb.backtest.position import PosState, Position


class PositionBook:
    def __init__(self, params: SignalParams) -> None:
        self._legs: list[Position] = []
        self._params = params

    # ------------------------------------------------------------------
    # ADR-003 pyramiding gate
    # ------------------------------------------------------------------

    def may_add(self, direction: str, current_price: float) -> bool:
        """Return True if another leg may be opened per ADR-003 policy."""
        active = self.active_legs()

        if not active:
            return True  # first leg always allowed

        if not self._params.pyramid_enabled:
            return False

        if len(active) >= self._params.pyramid_max_legs:
            return False

        if self._params.pyramid_same_direction_only:
            if any(leg.direction != direction for leg in active):
                return False

        # Winner-only: newest active leg must be ≥ pyramid_add_at_r
        newest = active[-1]
        if newest.r_now(current_price) < self._params.pyramid_add_at_r:
            return False

        return True

    # ------------------------------------------------------------------
    # Mutations
    # ------------------------------------------------------------------

    def add(self, pos: Position) -> None:
        self._legs.append(pos)

    def close_all(self, price: float, ts: object, bar: int, reason: str) -> None:
        """Flatten all active legs (book-wide defensive exit)."""
        for leg in self.active_legs():
            leg.close(price=price, ts=ts, bar=bar, reason=reason)

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def active_legs(self) -> list[Position]:
        """Legs that are filled or in managed state (not pending or closed)."""
        return [
            leg for leg in self._legs
            if leg.state in (PosState.FILLED, PosState.MANAGED)
        ]

    def pending_filled(self) -> list[Position]:
        """Legs that were just filled this bar (state == FILLED, fill_bar == current)."""
        return [leg for leg in self._legs if leg.state == PosState.FILLED]

    def all_legs(self) -> list[Position]:
        return list(self._legs)

    def closed_legs(self) -> list[Position]:
        return [leg for leg in self._legs if leg.state == PosState.CLOSED]
