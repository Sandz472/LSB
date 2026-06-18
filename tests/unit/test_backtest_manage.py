"""Tests for backtest/manage.py — §11 management pure functions."""

import pytest

from lsb.signals import Candle
from lsb.backtest.position import PosState, Position
from lsb.backtest.manage import (
    EXPIRY_BARS,
    apply_breakeven,
    apply_ema_trail,
    order_expired,
    record_partial_exit,
    stop_hit,
    target_hit,
)


def _long_pos(entry=1.1000, stop=1.0900, target=1.1250):
    risk = abs(entry - stop)
    return Position(
        instrument="EURUSD", direction="long",
        entry_price=entry, stop=stop, target=target, risk=risk,
        config_hash="abc", state=PosState.FILLED,
    )


def _short_pos(entry=1.1000, stop=1.1100, target=1.0750):
    risk = abs(entry - stop)
    return Position(
        instrument="EURUSD", direction="short",
        entry_price=entry, stop=stop, target=target, risk=risk,
        config_hash="abc", state=PosState.FILLED,
    )


def _candle(high, low, close=None, open_=None):
    close = close or (high + low) / 2
    open_ = open_ or close
    return Candle(ts=None, open=open_, high=high, low=low, close=close, volume=1.0)


# --- stop_hit / target_hit ---

def test_long_stop_hit():
    pos = _long_pos(entry=1.10, stop=1.09)
    assert stop_hit(pos, _candle(high=1.105, low=1.088))

def test_long_stop_not_hit():
    pos = _long_pos(entry=1.10, stop=1.09)
    assert not stop_hit(pos, _candle(high=1.115, low=1.095))

def test_long_target_hit():
    pos = _long_pos(entry=1.10, target=1.125)
    assert target_hit(pos, _candle(high=1.130, low=1.100))

def test_short_stop_hit():
    pos = _short_pos(entry=1.10, stop=1.11)
    assert stop_hit(pos, _candle(high=1.115, low=1.095))

def test_short_target_hit():
    pos = _short_pos(entry=1.10, target=1.075)
    assert target_hit(pos, _candle(high=1.100, low=1.070))


# --- §11.2 breakeven ---

def test_breakeven_applied_at_1r():
    pos = _long_pos(entry=1.10, stop=1.09)  # risk=0.01
    apply_breakeven(pos, high_water_price=1.11)  # r=1.0
    assert pos.breakeven_applied
    assert pos.stop == pos.entry_price
    assert pos.state == PosState.MANAGED

def test_breakeven_not_applied_below_1r():
    pos = _long_pos(entry=1.10, stop=1.09)
    apply_breakeven(pos, high_water_price=1.109)  # r=0.9
    assert not pos.breakeven_applied
    assert pos.stop == 1.09

def test_breakeven_idempotent():
    pos = _long_pos(entry=1.10, stop=1.09)
    apply_breakeven(pos, 1.11)
    old_stop = pos.stop
    apply_breakeven(pos, 1.12)
    assert pos.stop == old_stop  # ratchet — not moved back

def test_breakeven_short():
    pos = _short_pos(entry=1.10, stop=1.11)  # risk=0.01
    apply_breakeven(pos, high_water_price=1.09)  # r=1.0 short
    assert pos.breakeven_applied
    assert pos.stop == pos.entry_price


# --- §11.3 EMA21 trail ---

def test_ema_trail_applied_at_1_5r():
    pos = _long_pos(entry=1.10, stop=1.09)  # risk=0.01
    pos.breakeven_applied = True
    pos.stop = 1.10  # BE applied
    # current_price=1.116 → r=1.6, clearly ≥1.5; ema21=1.108 > stop=1.10
    apply_ema_trail(pos, current_price=1.116, ema21=1.108, swing_stop=None)
    assert pos.trail_applied
    assert pos.stop == pytest.approx(1.108)

def test_ema_trail_not_applied_below_1_5r():
    pos = _long_pos(entry=1.10, stop=1.09)
    apply_ema_trail(pos, current_price=1.113, ema21=1.108, swing_stop=None)  # r=1.3
    assert not pos.trail_applied
    assert pos.stop == 1.09  # unchanged

def test_ema_trail_ratchet_does_not_lower():
    pos = _long_pos(entry=1.10, stop=1.09)
    pos.stop = 1.108
    pos.trail_applied = True
    # EMA21 dipped below current stop → should not move stop down
    apply_ema_trail(pos, current_price=1.116, ema21=1.105, swing_stop=None)
    assert pos.stop == pytest.approx(1.108)

def test_ema_trail_swing_fallback_tighter():
    pos = _long_pos(entry=1.10, stop=1.09)
    # current_price=1.116 → r=1.6; swing low at 1.110 > ema21=1.108 → swing wins
    apply_ema_trail(pos, current_price=1.116, ema21=1.108, swing_stop=1.110)
    assert pos.stop == pytest.approx(1.110)


# --- §11.4 partial exit ---

def test_record_partial_exit():
    pos = _long_pos()
    record_partial_exit(pos, price=1.110, ts="t1", reason="opposing_sweep")
    assert len(pos.partial_exits) == 1
    pe = pos.partial_exits[0]
    assert pe.price == pytest.approx(1.110)
    assert pe.reason == "opposing_sweep"


# --- §10.3 expiry ---

def test_order_expired_after_expiry_bars():
    assert order_expired(bar_placed=0, current_bar=EXPIRY_BARS)

def test_order_not_expired_before():
    assert not order_expired(bar_placed=0, current_bar=EXPIRY_BARS - 1)
