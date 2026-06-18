"""Tests for backtest/book.py — PositionBook and ADR-003 pyramiding policy."""

import pytest

from lsb.backtest.book import PositionBook
from lsb.backtest.position import PosState, Position
from lsb.data.config import SignalParams


def _params(pyramid_enabled=False, max_legs=3, add_at_r=1.0, same_dir=True):
    return SignalParams(
        ema_short_period=21, ema_mid_period=50, ema_long_period=89,
        ema_slope_lookback=3, atr_period=14,
        atr_elevated_multiplier=1.25, atr_extreme_multiplier=2.0,
        ema_compression_atr_mult=0.1, slope_threshold_atr_mult=0.05,
        triangle_min_candles=8, triangle_max_candles=60,
        triangle_flat_tolerance_pct=0.005, swing_lookback=2,
        apex_proximity_min=0.75, apex_proximity_max=0.95,
        block_min_touches=2, block_min_width_pips=5.0,
        sweep_penetration_pips=2.0, sweep_expiry_candles=3,
        sweep_score_min=50, rejection_wick_body_mult=2.0,
        allowed_atr_states=('NORMAL', 'ELEVATED'), max_spread_pips=3.0,
        session_edge_buffer_min=30, min_rr_ratio=2.5,
        sl_buffer_pips=2.0, sl_buffer_pips_elevated=4.0,
        pyramid_enabled=pyramid_enabled, pyramid_max_legs=max_legs,
        pyramid_add_at_r=add_at_r, pyramid_same_direction_only=same_dir,
    )


def _pos(direction='long', entry=1.10, stop=1.09, state=PosState.FILLED):
    risk = abs(entry - stop)
    return Position(
        instrument='EURUSD', direction=direction,
        entry_price=entry, stop=stop, target=1.13, risk=risk,
        config_hash='x', state=state,
    )


# --- first leg always allowed ---

def test_first_leg_always_allowed():
    book = PositionBook(_params(pyramid_enabled=False))
    assert book.may_add('long', current_price=1.10)


# --- pyramiding disabled ---

def test_second_leg_blocked_when_disabled():
    book = PositionBook(_params(pyramid_enabled=False))
    book.add(_pos('long'))
    assert not book.may_add('long', current_price=1.20)


# --- pyramid_max_legs cap ---

def test_max_legs_cap():
    book = PositionBook(_params(pyramid_enabled=True, max_legs=2, add_at_r=0.0))
    book.add(_pos('long', entry=1.10, stop=1.09))
    book.add(_pos('long', entry=1.11, stop=1.10, state=PosState.MANAGED))
    # Both active, max=2 → denied
    assert not book.may_add('long', current_price=1.20)


# --- same-direction only ---

def test_same_direction_blocks_opposing():
    book = PositionBook(_params(pyramid_enabled=True, add_at_r=0.0, same_dir=True))
    book.add(_pos('long'))
    assert not book.may_add('short', current_price=1.20)

def test_same_direction_disabled_allows_opposing():
    book = PositionBook(_params(pyramid_enabled=True, add_at_r=0.0, same_dir=False))
    book.add(_pos('long'))
    assert book.may_add('short', current_price=1.20)


# --- winner-only (newest leg R check) ---

def test_winner_only_blocked_when_not_in_profit():
    # newest leg entry=1.10, stop=1.09 → risk=0.01; at 1.105 → r=0.5 < 1.0
    book = PositionBook(_params(pyramid_enabled=True, add_at_r=1.0))
    book.add(_pos('long', entry=1.10, stop=1.09))
    assert not book.may_add('long', current_price=1.105)

def test_winner_only_allowed_when_in_profit():
    # at 1.11 → r=1.0 ≥ 1.0
    book = PositionBook(_params(pyramid_enabled=True, add_at_r=1.0))
    book.add(_pos('long', entry=1.10, stop=1.09))
    assert book.may_add('long', current_price=1.110)


# --- close_all ---

def test_close_all_flattens_active_legs():
    book = PositionBook(_params(pyramid_enabled=True, add_at_r=0.0))
    p1 = _pos('long', entry=1.10, stop=1.09)
    p2 = _pos('long', entry=1.11, stop=1.10)
    book.add(p1)
    book.add(p2)
    book.close_all(price=1.095, ts='t', bar=10, reason='test')
    assert p1.state == PosState.CLOSED
    assert p2.state == PosState.CLOSED
    assert len(book.active_legs()) == 0


# --- active_legs excludes closed ---

def test_active_legs_excludes_closed():
    book = PositionBook(_params())
    p = _pos()
    book.add(p)
    p.close(price=1.095, ts='t', bar=1, reason='stop')
    assert len(book.active_legs()) == 0
    assert len(book.closed_legs()) == 1
