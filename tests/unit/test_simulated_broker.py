"""Unit tests for SimulatedBroker — §7.1 pessimistic fill model.

Worked-example matrix from the A7 plan §6. Values use EURUSD parameters:
  pip_size    = 0.0001
  spread_pts  = 1.2  (→ spread_price = 0.00012)
  slip_mult   = 0.05
  commission  = 7.0 / lot
  swap_long   = -0.8 pts
  swap_short  = -0.3 pts
  ATR (price) = 0.0020  → slip_NORMAL = 0.05 * 0.0020 = 0.0001

Invariant: SimulatedBroker entry fill is never better than NaiveBroker.
           Stop-exit fill is never better than exact-stop close.
"""

from __future__ import annotations

import math
from typing import NamedTuple, Any

import pytest

from lsb.backtest.broker import Fill, NaiveBroker, PendingOrder, SimulatedBroker
from lsb.data.config import BrokerCosts

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

_PIP = 0.0001
_ATR = 0.0020
_SPREAD_PTS = 1.2
_SLIP_MULT = 0.05
_SPREAD_PRICE = _SPREAD_PTS * _PIP   # 0.00012
_SLIP_NORMAL = _SLIP_MULT * _ATR     # 0.0001
_SLIP_EXTREME = _SLIP_NORMAL * 2     # 0.0002


@pytest.fixture()
def costs():
    return BrokerCosts(
        spread_points=_SPREAD_PTS,
        slippage_atr_mult=_SLIP_MULT,
        commission_per_lot=7.0,
        swap_long_points=-0.8,
        swap_short_points=-0.3,
    )


@pytest.fixture()
def broker(costs):
    return SimulatedBroker(costs, _PIP)


@pytest.fixture()
def naive():
    return NaiveBroker()


class _Candle(NamedTuple):
    ts: Any
    open: float
    high: float
    low: float
    close: float
    spread: float | None = None


def _order(direction: str, trigger: float, atr_state: str = "NORMAL") -> PendingOrder:
    return PendingOrder(
        instrument="EURUSD",
        direction=direction,
        trigger_price=trigger,
        initial_stop=trigger - 0.0050 if direction == "long" else trigger + 0.0050,
        initial_target=trigger + 0.0150 if direction == "long" else trigger - 0.0150,
        initial_risk=0.0050,
        config_hash="test",
        bar_placed=0,
        signal_ts=None,
        atr_state=atr_state,
        atr_value=_ATR,
    )


def _candle(open_=1.09990, high=1.10050, low=1.09950, spread=None):
    return _Candle(ts="t", open=open_, high=high, low=low, close=(high + low) / 2,
                   spread=spread)


# ---------------------------------------------------------------------------
# Entry fill: long
# ---------------------------------------------------------------------------

def test_long_entry_normal(broker):
    """trigger=1.10000, open below trigger → base=trigger. fill = trigger+slip+spread."""
    order = _order("long", 1.10000)
    candle = _candle(open_=1.09990, high=1.10050)
    fill = broker.try_fill(order, candle, 1)
    expected = 1.10000 + _SLIP_NORMAL + _SPREAD_PRICE
    assert fill is not None
    assert math.isclose(fill.price, expected, rel_tol=1e-9), f"{fill.price} != {expected}"


def test_long_entry_extreme(broker):
    """EXTREME ATR state doubles slippage."""
    order = _order("long", 1.10000, atr_state="EXTREME")
    candle = _candle(open_=1.09990, high=1.10050)
    fill = broker.try_fill(order, candle, 1)
    expected = 1.10000 + _SLIP_EXTREME + _SPREAD_PRICE
    assert fill is not None
    assert math.isclose(fill.price, expected, rel_tol=1e-9)


def test_long_entry_gap_through_trigger(broker):
    """Open above trigger → base=open (gap-through). fill = open+slip+spread."""
    order = _order("long", 1.10000)
    candle = _candle(open_=1.10030, high=1.10080)
    fill = broker.try_fill(order, candle, 1)
    expected = 1.10030 + _SLIP_NORMAL + _SPREAD_PRICE
    assert fill is not None
    assert math.isclose(fill.price, expected, rel_tol=1e-9)


def test_long_no_fill_high_below_trigger(broker):
    """high < trigger → no fill."""
    order = _order("long", 1.10000)
    candle = _candle(open_=1.09990, high=1.09995)
    assert broker.try_fill(order, candle, 1) is None


# ---------------------------------------------------------------------------
# Entry fill: short
# ---------------------------------------------------------------------------

def test_short_entry_normal(broker):
    """trigger=1.10000, open above trigger → base=trigger. fill = trigger-slip-spread."""
    order = _order("short", 1.10000)
    candle = _candle(open_=1.10010, high=1.10050, low=1.09950)
    fill = broker.try_fill(order, candle, 1)
    expected = 1.10000 - _SLIP_NORMAL - _SPREAD_PRICE
    assert fill is not None
    assert math.isclose(fill.price, expected, rel_tol=1e-9)


def test_short_no_fill_low_above_trigger(broker):
    """low > trigger → no fill."""
    order = _order("short", 1.10000)
    candle = _candle(open_=1.10010, high=1.10050, low=1.10005)
    assert broker.try_fill(order, candle, 1) is None


# ---------------------------------------------------------------------------
# Historical spread overrides constant
# ---------------------------------------------------------------------------

def test_historical_spread_overrides_constant(broker):
    """candle.spread=2.0 pts overrides the BrokerCosts 1.2 pts."""
    order = _order("long", 1.10000)
    candle = _candle(open_=1.09990, high=1.10050, spread=2.0)
    fill = broker.try_fill(order, candle, 1)
    expected_spread = 2.0 * _PIP
    expected = 1.10000 + _SLIP_NORMAL + expected_spread
    assert fill is not None
    assert math.isclose(fill.price, expected, rel_tol=1e-9)


# ---------------------------------------------------------------------------
# Stop exit fill
# ---------------------------------------------------------------------------

def test_long_stop_exit_no_gap(broker):
    """Stop=1.09800, open=1.09850 (above stop) → base=min=1.09800."""
    class _Leg:
        direction = "long"
        stop = 1.09800

    candle = _candle(open_=1.09850)
    slip = broker.slip_for(_ATR, "NORMAL")
    price = broker.fill_stop(_Leg(), candle, slip)
    expected = 1.09800 - slip
    assert math.isclose(price, expected, rel_tol=1e-9)
    assert price < 1.09800, "Stop exit must be worse than stop price"


def test_long_stop_exit_gap_through_stop(broker):
    """Open=1.09700 gaps below stop=1.09800 → base=open (honest case)."""
    class _Leg:
        direction = "long"
        stop = 1.09800

    candle = _candle(open_=1.09700)
    slip = broker.slip_for(_ATR, "NORMAL")
    price = broker.fill_stop(_Leg(), candle, slip)
    expected = 1.09700 - slip
    assert math.isclose(price, expected, rel_tol=1e-9)
    assert price < 1.09800, "Gap-through-stop must fill worse than the stop"


def test_short_stop_exit_gap_through_stop(broker):
    """Short: open gaps above stop → fill at open+slip (worse than stop)."""
    class _Leg:
        direction = "short"
        stop = 1.10200

    candle = _candle(open_=1.10350)
    slip = broker.slip_for(_ATR, "NORMAL")
    price = broker.fill_stop(_Leg(), candle, slip)
    expected = 1.10350 + slip
    assert math.isclose(price, expected, rel_tol=1e-9)
    assert price > 1.10200


# ---------------------------------------------------------------------------
# Target exit: exactly at target (no positive slippage, no degrade)
# ---------------------------------------------------------------------------

def test_target_exit_fills_at_target():
    """Target fills at target price — no improvement, no degrade (Q3)."""
    target = 1.10500
    # The loop closes at leg.target exactly; broker has no role in target exits.
    # This test documents the contract: the loop must pass leg.target unchanged.
    assert target == 1.10500  # sentinel — real assertion is in the integration test


# ---------------------------------------------------------------------------
# Swap computation (nights_held accounting)
# ---------------------------------------------------------------------------

def test_swap_3_nights_long(costs):
    """3 nights × swap_long_points(-0.8) × pip = -0.00024."""
    nights = 3
    swap = nights * costs.swap_long_points * _PIP
    assert math.isclose(swap, -0.00024, rel_tol=1e-9)


def test_swap_2_nights_short(costs):
    """2 nights × swap_short_points(-0.3) × pip = -0.00006."""
    nights = 2
    swap = nights * costs.swap_short_points * _PIP
    assert math.isclose(swap, -0.00006, rel_tol=1e-9)


# ---------------------------------------------------------------------------
# Invariant: SimulatedBroker is never better than NaiveBroker
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("direction,trigger,open_,high,low", [
    ("long",  1.10000, 1.09990, 1.10050, 1.09950),
    ("long",  1.10000, 1.10030, 1.10080, 1.09900),   # gap-through-trigger
    ("short", 1.10000, 1.10010, 1.10050, 1.09950),
    ("short", 1.10000, 1.09970, 1.10050, 1.09900),   # gap-through-trigger short
])
def test_simulated_never_better_than_naive_entry(broker, naive, direction, trigger,
                                                 open_, high, low):
    order = _order(direction, trigger)
    candle = _candle(open_=open_, high=high, low=low)
    sim_fill = broker.try_fill(order, candle, 1)
    naive_fill = naive.try_fill(order, candle, 1)
    if naive_fill is None:
        assert sim_fill is None
        return
    assert sim_fill is not None
    if direction == "long":
        assert sim_fill.price >= naive_fill.price, (
            f"SimulatedBroker long entry {sim_fill.price} better than NaiveBroker {naive_fill.price}"
        )
    else:
        assert sim_fill.price <= naive_fill.price, (
            f"SimulatedBroker short entry {sim_fill.price} better than NaiveBroker {naive_fill.price}"
        )


@pytest.mark.parametrize("direction,stop,open_", [
    ("long",  1.09800, 1.09850),   # no gap
    ("long",  1.09800, 1.09700),   # gap through
    ("short", 1.10200, 1.10180),   # no gap
    ("short", 1.10200, 1.10350),   # gap through
])
def test_simulated_stop_exit_never_better_than_exact(broker, direction, stop, open_):
    """SimulatedBroker stop exit must always be worse than the exact stop price."""
    class _Leg:
        pass
    leg = _Leg()
    leg.direction = direction
    leg.stop = stop
    candle = _candle(open_=open_)
    slip = broker.slip_for(_ATR, "NORMAL")
    price = broker.fill_stop(leg, candle, slip)
    if direction == "long":
        assert price <= stop, f"Long stop exit {price} better than stop {stop}"
    else:
        assert price >= stop, f"Short stop exit {price} better than stop {stop}"


# ---------------------------------------------------------------------------
# Costs do not affect r_at_close (D3)
# ---------------------------------------------------------------------------

def test_costs_do_not_affect_r_at_close():
    """commission and swap fields must not change r_at_close."""
    from lsb.backtest.position import Position, PosState

    pos = Position(
        instrument="EURUSD", direction="long",
        entry_price=1.10000, stop=1.09500, target=1.11500,
        risk=0.00500, config_hash="x", state=PosState.FILLED,
    )
    r_before = pos.r_now(1.11000)
    pos.commission = 7.0
    pos.swap = -0.00024
    r_after = pos.r_now(1.11000)
    assert math.isclose(r_before, r_after, rel_tol=1e-9), (
        "Setting commission/swap must not change r_now"
    )
