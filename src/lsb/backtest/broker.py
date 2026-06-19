"""Broker protocol seam: order submission and fill simulation.

NaiveBroker is the Phase A optimistic fill model — assumes the best-case
fill price whenever the trigger is touched. SimulatedBroker (A7) replaces it
with pessimistic slippage/spread without changing the loop.

§10.1: entry is a Buy Stop (long) or Sell Stop (short) at rejection-candle
       extreme ± 1 pip.
§10.3: pending orders expire after 4 bars without fill.

Same-bar ambiguity rule (NaiveBroker): if both stop and target are within a
fill bar, stop is assumed hit first (worst case for the opening position
credit; consistent with A7 SimulatedBroker).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from lsb.data.config import BrokerCosts
from lsb.signals import Candle


@dataclass
class PendingOrder:
    instrument: str
    direction: str          # 'long' | 'short'
    trigger_price: float    # Buy Stop / Sell Stop trigger level
    initial_stop: float     # §9.1 structural stop at signal time
    initial_target: float   # §9.4 target at signal time
    initial_risk: float     # |trigger - initial_stop|
    config_hash: str
    bar_placed: int         # loop bar index when order was submitted
    signal_ts: object       # candle timestamp of the qualifying signal
    atr_state: str = field(default="NORMAL")  # ATR state at signal time (entry slippage scaling)
    atr_value: float = field(default=0.0)     # ATR in price units at signal time


@dataclass
class Fill:
    price: float
    bar_idx: int
    ts: object


class Broker(Protocol):
    def try_fill(self, order: PendingOrder, candle: Candle, bar_idx: int) -> Fill | None:
        """Attempt to fill order against candle. Returns Fill or None."""
        ...


class NaiveBroker:
    """Optimistic fill: triggers on first bar the price touches the level.

    Long (Buy Stop):  fill when candle.high >= trigger_price → fill at trigger.
    Short (Sell Stop): fill when candle.low  <= trigger_price → fill at trigger.
    """

    def try_fill(self, order: PendingOrder, candle: Candle, bar_idx: int) -> Fill | None:
        if order.direction == 'long':
            if candle.high >= order.trigger_price:
                return Fill(price=order.trigger_price, bar_idx=bar_idx, ts=candle.ts)
        else:
            if candle.low <= order.trigger_price:
                return Fill(price=order.trigger_price, bar_idx=bar_idx, ts=candle.ts)
        return None


class SimulatedBroker:
    """§7.1 pessimistic fills: spread + ATR-scaled slippage + gap-through.

    EXTREME ATR state doubles entry slippage. Never fills better than the model.
    D3: commission/swap recorded on the leg at close; do not affect r_at_close.
    D4: full spread at entry only (same round-trip total as half-entry/half-exit).
    Q3: target exits fill exactly at target — no positive slippage credited.
    """

    def __init__(self, costs: BrokerCosts, pip_size: float) -> None:
        self.costs = costs
        self.pip = pip_size

    def slip_for(self, atr_value: float, atr_state: str) -> float:
        """Slippage in price units, EXTREME state doubles it."""
        s = self.costs.slippage_atr_mult * atr_value
        return s * (2.0 if atr_state == "EXTREME" else 1.0)

    def _slip(self, order: PendingOrder) -> float:
        return self.slip_for(order.atr_value, order.atr_state)

    def try_fill(self, order: PendingOrder, candle: Candle, bar_idx: int) -> Fill | None:
        spread = (
            candle.spread if candle.spread is not None else self.costs.spread_points
        ) * self.pip
        slip = self._slip(order)
        if order.direction == 'long':
            if candle.high < order.trigger_price:
                return None
            base = max(order.trigger_price, candle.open)   # gap-through-trigger
            return Fill(base + slip + spread, bar_idx, candle.ts)
        else:
            if candle.low > order.trigger_price:
                return None
            base = min(order.trigger_price, candle.open)   # gap-through-trigger
            return Fill(base - slip - spread, bar_idx, candle.ts)

    def fill_stop(self, leg, candle: Candle, slip: float) -> float:
        """Honest stop-exit price including gap-through-stop (D1)."""
        if leg.direction == 'long':
            return min(leg.stop, candle.open) - slip
        return max(leg.stop, candle.open) + slip
