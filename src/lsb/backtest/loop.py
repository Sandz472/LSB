"""Backtest event loop — per-candle replay driver.

run_backtest() streams a pre-loaded candle list through the signal engine,
manages position lifecycles, and writes signal rows to a sink.

Look-ahead guard: pending orders placed at bar i are filled/expired against
bar i+1+. Management runs BEFORE evaluation each bar — so a position opened
on bar i's signal is not managed until bar i+1 at the earliest.

Per-bar sequence:
  1. Fill / expire pending orders against the current candle.
  2. Check stop/target hits on all active positions.
  3. Apply §11.2 breakeven and §11.3 EMA21 trail on still-active positions.
  4. Evaluate the current bar through the eight-gate engine.
  5. §11.4 book-wide defensive exits triggered by the current signal result.
  6. If the signal qualifies and the book allows, stage a new pending order.
"""

from __future__ import annotations

from collections import deque
from typing import Sequence

from lsb.data.config import InstrumentConfig
from lsb.signals import Candle
from lsb.signals.engine import SignalResult, evaluate, MIN_H1_WINDOW
from lsb.signals.indicators import ATRState, ema_series, atr_series
from lsb.signals.risk import structural_stop, rr_target
from lsb.signals.trend import current_atr_state

from lsb.backtest.broker import Broker, Fill, NaiveBroker, PendingOrder, SimulatedBroker
from lsb.backtest.book import PositionBook
from lsb.backtest.clock import ReplayClock
from lsb.backtest.manage import (
    EXPIRY_BARS,
    apply_breakeven,
    apply_ema_trail,
    nearest_swing_stop,
    order_expired,
    record_partial_exit,
    stop_hit,
    target_hit,
)
from lsb.backtest.position import PosState, Position
from lsb.backtest.sink import NullSink, Sink

WINDOW_MAXLEN = MIN_H1_WINDOW * 2  # 600 — O(n) deque, always feeds ≥300 to evaluate()


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def run_backtest(
    candles: list[Candle],
    config: InstrumentConfig,
    config_hash_val: str,
    sink: Sink | None = None,
    broker: Broker | None = None,
) -> tuple[PositionBook, Sink]:
    """Run a full replay over `candles` for a single instrument/config.

    Returns (book, sink) so callers can inspect positions and signal rows.
    """
    if sink is None:
        sink = NullSink()
    if broker is None:
        broker = NaiveBroker()

    book = PositionBook(config.signals)
    clock = ReplayClock(candles)
    window: deque[Candle] = deque(maxlen=WINDOW_MAXLEN)
    pending: list[PendingOrder] = []

    for bar_idx in clock:
        candle = candles[bar_idx]
        window.append(candle)

        if len(window) < MIN_H1_WINDOW:
            continue

        h1_win: list[Candle] = list(window)

        # --- 1. Fill / expire pending orders ---
        pending = _process_pending(pending, candle, bar_idx, config, broker, book)

        # --- 2. & 3. Stop/target + management ---
        _manage_book(book, candle, h1_win, config, broker)

        # --- 4. Signal evaluation ---
        result: SignalResult = evaluate(h1_win, config, config_hash_val)
        sink.write(result)

        # --- 5. Book-wide §11.4 defensive exits ---
        _defensive_exits(book, result, candle, bar_idx, config)

        # --- 6. Stage new pending order if qualified ---
        if result.qualified and result.direction is not None:
            _maybe_stage_order(
                pending, book, result, candle, h1_win, config, config_hash_val, bar_idx
            )

    return book, sink


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _process_pending(
    pending: list[PendingOrder],
    candle: Candle,
    bar_idx: int,
    config: InstrumentConfig,
    broker: Broker,
    book: PositionBook,
) -> list[PendingOrder]:
    """Attempt fills; expire stale orders. Returns remaining pending list."""
    still_pending: list[PendingOrder] = []

    for order in pending:
        if order_expired(order.bar_placed, bar_idx):
            continue  # §10.3 expiry — silently drop

        fill: Fill | None = broker.try_fill(order, candle, bar_idx)
        if fill:
            pos = Position(
                instrument=order.instrument,
                direction=order.direction,
                entry_price=fill.price,
                stop=order.initial_stop,
                target=order.initial_target,
                risk=order.initial_risk,
                config_hash=order.config_hash,
                state=PosState.FILLED,
                fill_ts=fill.ts,
                fill_bar=fill.bar_idx,
            )
            book.add(pos)
        else:
            still_pending.append(order)

    return still_pending


def _record_costs(leg, close_ts, config: InstrumentConfig) -> None:
    """Record commission and swap on the leg (D3). Does not affect r_at_close."""
    costs = config.broker_costs
    nights = max(0, (close_ts - leg.fill_ts).days) if leg.fill_ts is not None else 0
    swap_pts = costs.swap_long_points if leg.direction == 'long' else costs.swap_short_points
    leg.commission = costs.commission_per_lot
    leg.swap = nights * swap_pts * config.pip_size


def _manage_book(
    book: PositionBook,
    candle: Candle,
    h1_win: list[Candle],
    config: InstrumentConfig,
    broker: Broker,
) -> None:
    """Apply per-candle management to every active leg."""
    p = config.signals
    atr_vals = atr_series(h1_win, p.atr_period)
    ema21_vals = ema_series([c.close for c in h1_win], p.ema_short_period)
    ema21 = ema21_vals[-1] if ema21_vals else candle.close

    # Pre-compute exit slippage once per bar for SimulatedBroker
    sim_slip: float | None = None
    if isinstance(broker, SimulatedBroker):
        atr_last = atr_vals[-1] if atr_vals else 1e-6
        atr_st_name = current_atr_state(h1_win, p).name
        sim_slip = broker.slip_for(atr_last, atr_st_name)

    for leg in book.active_legs():
        # --- 2. Check stop/target ---
        s_hit = stop_hit(leg, candle)
        t_hit = target_hit(leg, candle)

        if s_hit and t_hit:
            # Same-bar ambiguity: stop first (worst case, consistent with NaiveBroker)
            exit_px = broker.fill_stop(leg, candle, sim_slip) if sim_slip is not None else leg.stop
            _record_costs(leg, candle.ts, config)
            leg.close(price=exit_px, ts=candle.ts, bar=0, reason='stop')
            continue
        if s_hit:
            exit_px = broker.fill_stop(leg, candle, sim_slip) if sim_slip is not None else leg.stop
            _record_costs(leg, candle.ts, config)
            leg.close(price=exit_px, ts=candle.ts, bar=0, reason='stop')
            continue
        if t_hit:
            _record_costs(leg, candle.ts, config)
            leg.close(price=leg.target, ts=candle.ts, bar=0, reason='target')
            continue

        # --- 3. Management rules ---
        high_water = candle.high if leg.direction == 'long' else candle.low
        apply_breakeven(leg, high_water)

        swing = nearest_swing_stop(h1_win, leg.entry_price, leg.direction, p.swing_lookback)
        apply_ema_trail(leg, high_water, ema21, swing)


def _defensive_exits(
    book: PositionBook,
    result: SignalResult,
    candle: Candle,
    bar_idx: int,
    config: InstrumentConfig,
) -> None:
    """§11.4 book-wide defensive exits triggered by the current bar's signal.

    Opposing sweep (qualified, opposite direction) → partial exit event on each leg.
    Structure break (rejected at gate 2 in the same direction as active legs) →
        full close.
    ATR EXTREME is detected in _manage_book via stop moves; full systematic close
    is deferred to the natural stop-hit path in Phase A.
    """
    active = book.active_legs()
    if not active:
        return

    # Opposing sweep: qualified signal in the opposite direction
    if result.qualified and result.direction is not None:
        for leg in active:
            if leg.direction != result.direction:
                record_partial_exit(
                    leg, price=candle.close, ts=candle.ts, reason='opposing_sweep'
                )

    # Structure break: signal rejected at gate 2 for the same direction as active legs
    if not result.qualified and result.rejected_at_gate == 2:
        for leg in active:
            if leg.direction == result.direction:
                _record_costs(leg, candle.ts, config)
                leg.close(
                    price=candle.close,
                    ts=candle.ts,
                    bar=bar_idx,
                    reason='structure_break',
                )


def _maybe_stage_order(
    pending: list[PendingOrder],
    book: PositionBook,
    result: SignalResult,
    candle: Candle,
    h1_win: list[Candle],
    config: InstrumentConfig,
    config_hash_val: str,
    bar_idx: int,
) -> None:
    """Compute entry/stop/target and stage a PendingOrder if book policy allows."""
    p = config.signals
    direction = result.direction

    # §10.1: trigger at rejection-candle extreme ± 1 pip
    if direction == 'long':
        trigger = candle.high + config.pip_size
    else:
        trigger = candle.low - config.pip_size

    atr_st = current_atr_state(h1_win, p)
    stop = structural_stop(candle, direction, atr_st, p, config.pip_size)
    if stop is None:
        return

    atr_vals = atr_series(h1_win, p.atr_period)
    atr_last = atr_vals[-1] if atr_vals else 1e-6
    target, _ = rr_target(trigger, stop, h1_win, atr_last, direction, p)
    risk = abs(trigger - stop)
    if risk == 0.0:
        return

    if not book.may_add(direction, candle.close):
        return

    pending.append(PendingOrder(
        instrument=config.instrument,
        direction=direction,
        trigger_price=trigger,
        initial_stop=stop,
        initial_target=target,
        initial_risk=risk,
        config_hash=config_hash_val,
        bar_placed=bar_idx,
        signal_ts=candle.ts,
        atr_state=atr_st.name,
        atr_value=atr_last,
    ))
