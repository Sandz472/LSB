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

from dataclasses import dataclass
from typing import Protocol

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
