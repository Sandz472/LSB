"""Signal engine — evaluates gates 1–4 for a candle window.

Accepts a sequence of H1 Candle objects and a fully-loaded InstrumentConfig
(including SignalParams). Returns a SignalResult with per-gate pass/fail and
reasons, suitable for persisting to the `signal` table.

Gates 5–8 and the full eight-gate conjunction are Session A5.

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
)
from lsb.signals.indicators import atr_series, ema_series
from lsb.signals.liquidity import detect_sweep, identify_block
from lsb.signals.resample import resample_h1_to_h4
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
    direction: str | None   # 'long' | 'short' | None if no structure
    qualified: bool          # True if all 4 gates pass (A4 scope only)
    rejected_at_gate: int | None
    gates: tuple[GateResult, ...]


def evaluate(
    h1_window: Sequence[Candle],
    config: InstrumentConfig,
    config_hash_val: str,
) -> SignalResult:
    """Evaluate gates 1–4 for the last candle in h1_window.

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
            direction=None if gate_num <= 2 else gates[1].detail.get('direction'),
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

    return SignalResult(
        instrument=config.instrument,
        timeframe='H1',
        ts=ts,
        config_hash=config_hash_val,
        direction=direction,
        qualified=True,
        rejected_at_gate=None,
        gates=tuple(gates),
    )
