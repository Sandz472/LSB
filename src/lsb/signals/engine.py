"""Signal engine — evaluates all eight M7 entry gates for a candle window.

Accepts a sequence of H1 Candle objects and a fully-loaded InstrumentConfig
(including SignalParams). Returns a SignalResult with per-gate pass/fail and
reasons, suitable for persisting to the `signal` table.

No I/O, no side effects: pure transformation of a candle window to a result.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence

from lsb.data.config import InstrumentConfig
from lsb.signals import Candle
from lsb.signals.gates import (
    GateResult,
    gate_1_trend_alignment,
    gate_2_structure_present,
    gate_3_liquidity_sweep,
    gate_4_sweep_quality,
    gate_5_candle_confirmation,
    gate_6_volatility_acceptable,
    gate_7_session_clear,
    gate_8_risk_viable,
)
from lsb.signals.indicators import ATRState, CandleType, atr_series, classify_candle, ema_series
from lsb.signals.liquidity import detect_sweep, identify_block
from lsb.signals.resample import resample_h1_to_h4
from lsb.signals.risk import rr_target, structural_stop
from lsb.signals.session import minutes_to_edge, session_of
from lsb.signals.structure import StructureState, detect_triangle
from lsb.signals.trend import TrendState, current_atr_state, current_emas, trend_state

# Minimum H1 window required for a valid evaluation.
# EMA89 seed needs 89 bars; H4 triangle needs up to 60 H4 × 4 = 240 H1 bars.
# Using 300 as a comfortable floor.
MIN_H1_WINDOW = 300


@dataclass(frozen=True)
class SignalResult:
    instrument: str
    timeframe: str
    ts: object            # evaluation candle timestamp
    config_hash: str
    direction: str | None   # 'long' | 'short' | None if direction undetermined
    qualified: bool          # True if all eight gates pass (eight-gate conjunction)
    rejected_at_gate: int | None
    gates: tuple[GateResult, ...]


def evaluate(
    h1_window: Sequence[Candle],
    config: InstrumentConfig,
    config_hash_val: str,
) -> SignalResult:
    """Evaluate all eight M7 gates for the last candle in h1_window.

    h1_window must be sorted ascending by timestamp, with the candle under
    evaluation at index -1. The window must be at least MIN_H1_WINDOW candles.
    """
    p = config.signals
    ts = h1_window[-1].ts if h1_window else None

    def _reject(gate_num: int, gates: list[GateResult]) -> SignalResult:
        return SignalResult(
            instrument=config.instrument,
            timeframe='H1',
            ts=ts,
            config_hash=config_hash_val,
            direction=direction if gate_num > 2 else None,
            qualified=False,
            rejected_at_gate=gate_num,
            gates=tuple(gates),
        )

    if len(h1_window) < MIN_H1_WINDOW:
        g = GateResult(1, 'trend_alignment', False, f'insufficient window ({len(h1_window)} < {MIN_H1_WINDOW})')
        return _reject(1, [g])

    # M3: trend state
    t_state = trend_state(h1_window, p)
    ema21, ema50, _ = current_emas(h1_window, p)
    atr_st = current_atr_state(h1_window, p)

    # Determine direction from trend before Gate 1 so we can pass it to all gates.
    if t_state == TrendState.BEARISH:
        direction = 'short'
    elif t_state == TrendState.BULLISH:
        direction = 'long'
    else:
        direction = None  # will fail Gate 1

    g1 = gate_1_trend_alignment(t_state, direction or 'short')
    gates: list[GateResult] = [g1]
    if not g1.passed:
        return _reject(1, gates)

    # M4: structure on H4
    h4_window = resample_h1_to_h4(h1_window)
    structure = detect_triangle(h4_window[-p.triangle_max_candles:] if len(h4_window) > p.triangle_max_candles else h4_window, p)

    g2 = gate_2_structure_present(structure, direction)
    gates.append(g2)
    if not g2.passed:
        return _reject(2, gates)

    # M5: block + sweep
    block = identify_block(structure, h4_window, config)
    if block is None or not block.valid:
        g3 = GateResult(3, 'liquidity_sweep', False, 'block invalid or too narrow')
        gates.append(g3)
        return _reject(3, gates)

    sweep = detect_sweep(h1_window, block, structure, config, ema21, ema50, atr_st)
    g3 = gate_3_liquidity_sweep(sweep)
    gates.append(g3)
    if not g3.passed:
        return _reject(3, gates)

    g4 = gate_4_sweep_quality(sweep, p.sweep_score_min)
    gates.append(g4)
    if not g4.passed:
        return _reject(4, gates)

    # --- Gates 5–8 (Session A5) ---
    atr_vals = atr_series(h1_window, p.atr_period)
    atr_last = atr_vals[-1] if atr_vals else 1e-6

    # Gate 5 — candle confirmation
    confirm_type = classify_candle(h1_window[-1], h1_window[-2], atr_last)
    body = abs(h1_window[-1].close - h1_window[-1].open)
    if direction == 'short':
        dir_wick = h1_window[-1].high - max(h1_window[-1].open, h1_window[-1].close)
        closes_beyond = h1_window[-1].close < block.upper
    else:
        dir_wick = min(h1_window[-1].open, h1_window[-1].close) - h1_window[-1].low
        closes_beyond = h1_window[-1].close > block.lower
    wick_ratio = dir_wick / body if body > 0 else 0.0

    g5 = gate_5_candle_confirmation(confirm_type, closes_beyond, wick_ratio, direction, p)
    gates.append(g5)
    if not g5.passed:
        return _reject(5, gates)

    # Gate 6 — volatility acceptable
    spread = h1_window[-1].spread
    spread_pips = (spread / config.pip_size) if spread is not None else None
    g6 = gate_6_volatility_acceptable(atr_st, spread_pips, p)
    gates.append(g6)
    if not g6.passed:
        return _reject(6, gates)

    # Gate 7 — session & news
    g7 = gate_7_session_clear(session_of(ts), minutes_to_edge(ts), p)
    gates.append(g7)
    if not g7.passed:
        return _reject(7, gates)

    # Gate 8 — risk viable
    entry_price = h1_window[-1].low if direction == 'short' else h1_window[-1].high
    stop = structural_stop(h1_window[-1], direction, atr_st, p, config.pip_size)
    if stop is not None and atr_last > 0:
        _, rr = rr_target(entry_price, stop, h1_window, atr_last, direction, p)
    else:
        rr = 0.0
    g8 = gate_8_risk_viable(rr, stop is not None, p)
    gates.append(g8)
    if not g8.passed:
        return _reject(8, gates)

    return SignalResult(
        instrument=config.instrument,
        timeframe='H1',
        ts=ts,
        config_hash=config_hash_val,
        direction=direction,
        qualified=True,   # true eight-gate conjunction
        rejected_at_gate=None,
        gates=tuple(gates),
    )
