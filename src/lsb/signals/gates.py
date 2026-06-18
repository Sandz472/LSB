"""Gates 1–8 of the M7 entry qualifier.

Each gate is a pure predicate returning a GateResult. Gates are evaluated
sequentially in engine.py; the first failure short-circuits the chain.

Spec: LSB_System_Requirements_v2.0.md §8, LSB_Implementation_Plan_v3.0.md Part 1.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from lsb.data.config import InstrumentConfig, SignalParams
from lsb.signals.indicators import ATRState, CandleType
from lsb.signals.liquidity import SweepResult
from lsb.signals.session import Session
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


def gate_5_candle_confirmation(
    candle_type: CandleType,
    closes_beyond_sweep: bool,
    wick_body_ratio: float,
    direction: str,
    p: SignalParams,
) -> GateResult:
    """Gate 5 — Candle confirmation (§8 cond 5).

    Pass: confirmation candle is REJECTION or ENGULFING in trade direction,
    close re-enters beyond the swept level, and directional wick ≥ rejection_wick_body_mult × body.

    §8 uses the *directional* wick (upper wick for short, lower wick for long), not the
    raw classify_candle §4.3 wick; the engine pre-computes wick_body_ratio accordingly.
    """
    name = 'candle_confirmation'
    expected = (
        (CandleType.REJECTION_BEAR, CandleType.ENGULFING_BEAR)
        if direction == 'short'
        else (CandleType.REJECTION_BULL, CandleType.ENGULFING_BULL)
    )
    type_label = 'bear' if direction == 'short' else 'bull'

    if candle_type not in expected:
        return GateResult(5, name, False, f'candle {candle_type.name} not {type_label} rejection/engulfing')
    if not closes_beyond_sweep:
        return GateResult(5, name, False, 'close does not re-enter beyond sweep level')
    if wick_body_ratio < p.rejection_wick_body_mult:
        return GateResult(
            5, name, False,
            f'wick/body {wick_body_ratio:.2f} < {p.rejection_wick_body_mult}',
        )
    return GateResult(
        5, name, True,
        f'{candle_type.name}, wick/body {wick_body_ratio:.2f}',
        detail={'candle_type': candle_type.name, 'wick_body_ratio': round(wick_body_ratio, 4)},
    )


def gate_6_volatility_acceptable(
    atr_state: ATRState | None,
    spread_pips: float | None,
    p: SignalParams,
) -> GateResult:
    """Gate 6 — Volatility acceptable (§9.3).

    Blocks EXTREME ATR (§9.3 "ATR=EXTREME → no trade"). COMPRESSED is handled
    upstream by gate 1 (INVALID trend). Spread check is skipped when Candle.spread
    is None (no spread data available for that instrument/source).
    """
    name = 'volatility_acceptable'
    if atr_state is None:
        return GateResult(6, name, False, 'insufficient data for ATR state')
    if atr_state.name not in p.allowed_atr_states:
        return GateResult(6, name, False, f'ATR state {atr_state.name} not in allowed set')
    if spread_pips is not None and spread_pips > p.max_spread_pips:
        return GateResult(
            6, name, False,
            f'spread {spread_pips:.1f} pips > max {p.max_spread_pips}',
            detail={'spread_pips': round(spread_pips, 2)},
        )
    spread_info = f', spread {spread_pips:.1f} pips' if spread_pips is not None else ''
    return GateResult(6, name, True, f'ATR {atr_state.name}{spread_info}')


def gate_7_session_clear(
    session: Session,
    minutes_to_edge: int,
    p: SignalParams,
) -> GateResult:
    """Gate 7 — Session & news clear (§8 cond 6).

    Deterministic part: session must be an active trading session (not OFF)
    and the timestamp must not be within session_edge_buffer_min of a boundary.

    Runtime sliver (deferred to Phase B / M12): Tier-1 news feed and live
    liquidity-adequacy checks are not available in Phase A. These are represented
    as a documented always-pass stub — not a silent omission.
    """
    name = 'session_clear'
    if session == Session.OFF:
        return GateResult(7, name, False, 'OFF session — no active market')
    if minutes_to_edge < p.session_edge_buffer_min:
        return GateResult(
            7, name, False,
            f'{session.name}: {minutes_to_edge} min to edge < buffer {p.session_edge_buffer_min}',
        )
    # Runtime stub: news feed and live liquidity check (M12, Phase B)
    return GateResult(
        7, name, True,
        f'{session.name}, {minutes_to_edge} min to edge; news/liquidity stub-pass (M12, Phase B)',
        detail={'session': session.name, 'minutes_to_edge': minutes_to_edge},
    )


def gate_8_risk_viable(
    rr_ratio: float,
    stop_placeable: bool,
    p: SignalParams,
) -> GateResult:
    """Gate 8 — Risk viable (§9.1 + §9.4).

    Deterministic part: structural stop must be placeable (§9.1) and R:R ≥
    min_rr_ratio via the target hierarchy (§9.4).

    Runtime sliver (deferred to Phase B / M11): drawdown headroom check and
    tier-position limits require live account state unavailable in Phase A.
    These are represented as a documented always-pass stub.
    """
    name = 'risk_viable'
    if not stop_placeable:
        return GateResult(8, name, False, 'structural stop not placeable (insufficient ATR data)')
    if rr_ratio < p.min_rr_ratio:
        return GateResult(
            8, name, False,
            f'R:R {rr_ratio:.2f} < min {p.min_rr_ratio}',
            detail={'rr_ratio': round(rr_ratio, 4)},
        )
    # Runtime stub: drawdown / tier-limit check (M11, Phase B)
    return GateResult(
        8, name, True,
        f'R:R {rr_ratio:.2f} ≥ {p.min_rr_ratio}; drawdown/tier stub-pass (M11, Phase B)',
        detail={'rr_ratio': round(rr_ratio, 4)},
    )
