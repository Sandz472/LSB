"""Gates 1–4 of the M7 entry qualifier.

Each gate is a pure predicate returning a GateResult. Gates are evaluated
sequentially in engine.py; the first failure short-circuits the chain.

Spec: LSB_System_Requirements_v2.0.md §8, LSB_Implementation_Plan_v3.0.md Part 1.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from lsb.data.config import InstrumentConfig
from lsb.signals.indicators import ATRState
from lsb.signals.liquidity import SweepResult
from lsb.signals.structure import StructureResult, StructureState
from lsb.signals.trend import TrendState


@dataclass(frozen=True)
class GateResult:
    gate: int
    name: str
    passed: bool
    reason: str
    detail: dict = field(default_factory=dict)


def gate_1_trend_alignment(
    trend: TrendState,
    direction: str,
) -> GateResult:
    """Gate 1 — Trend alignment (M3).

    Pass: M3 trend state is BULLISH (long setup) or BEARISH (short setup) and
    matches the intended trade direction. NEUTRAL and INVALID are hard blockers.
    """
    name = 'trend_alignment'

    if trend == TrendState.INVALID:
        return GateResult(1, name, False, 'trend INVALID (EMA compression or crossing)')
    if trend == TrendState.NEUTRAL:
        return GateResult(1, name, False, 'trend NEUTRAL')

    expected = TrendState.BEARISH if direction == 'short' else TrendState.BULLISH
    if trend != expected:
        return GateResult(
            1, name, False,
            f'trend {trend.name} does not match direction {direction}',
        )

    return GateResult(1, name, True, f'trend {trend.name}, direction {direction}')


def gate_2_structure_present(
    structure: StructureResult,
    direction: str,
) -> GateResult:
    """Gate 2 — Structure present (M4).

    Pass: M4 reports a confirmed triangle on H4 that matches the trade direction.
    - Short setup (bearish): requires ASCENDING_TRIANGLE
    - Long setup (bullish): requires DESCENDING_TRIANGLE
    Apex proximity must be within [min, max] (already validated by detect_triangle).
    """
    name = 'structure_present'

    expected = (
        StructureState.ASCENDING_TRIANGLE
        if direction == 'short'
        else StructureState.DESCENDING_TRIANGLE
    )

    if structure.state == StructureState.NONE:
        return GateResult(2, name, False, 'no qualifying structure')
    if structure.state == StructureState.INVALIDATED:
        return GateResult(2, name, False, 'structure invalidated')
    if structure.state == StructureState.FORMING:
        return GateResult(
            2, name, False,
            f'structure forming, apex proximity {structure.apex_proximity:.2f}',
        )
    if structure.state != expected:
        return GateResult(
            2, name, False,
            f'structure {structure.state.name} does not match direction {direction}',
        )

    return GateResult(
        2, name, True,
        f'{structure.state.name}, apex {structure.apex_proximity:.2f}',
        detail={'apex_proximity': structure.apex_proximity},
    )


def gate_3_liquidity_sweep(sweep: SweepResult) -> GateResult:
    """Gate 3 — Liquidity sweep confirmed (M5).

    Pass: M5 detects an active sweep event within the last sweep_expiry_candles H1 bars.
    """
    name = 'liquidity_sweep'
    if not sweep.detected:
        return GateResult(3, name, False, sweep.reason)
    return GateResult(
        3, name, True,
        f'sweep {sweep.direction} {sweep.sweep_candle_bars_ago} bar(s) ago',
        detail={'bars_ago': sweep.sweep_candle_bars_ago},
    )


def gate_4_sweep_quality(
    sweep: SweepResult,
    sweep_score_min: int,
) -> GateResult:
    """Gate 4 — Sweep quality (5-factor score ≥ sweep_score_min).

    Spec §7.3: score 80–100 = HIGH, 50–79 = MODERATE, <50 = LOW/skip.
    """
    name = 'sweep_quality'
    if not sweep.detected:
        return GateResult(4, name, False, 'no sweep to score')
    if sweep.score < sweep_score_min:
        return GateResult(
            4, name, False,
            f'score {sweep.score} < sweep_score_min {sweep_score_min}',
            detail={'score': sweep.score, 'factors': sweep.score_detail},
        )
    return GateResult(
        4, name, True,
        f'score {sweep.score} ≥ {sweep_score_min}',
        detail={'score': sweep.score, 'factors': sweep.score_detail},
    )
