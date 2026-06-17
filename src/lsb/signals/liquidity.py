"""M5 — Liquidity Zone Engine.

Block identification, sweep detection, and the 5-factor Sweep Probability
Score (0–100). Pure functions: no I/O, no side effects.

Spec: LSB_System_Requirements_v2.0.md §7.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence

from lsb.data.config import InstrumentConfig
from lsb.signals import Candle
from lsb.signals.indicators import ATRState
from lsb.signals.structure import StructureResult, StructureState

# Max density score before normalization to [0, 30].
_DENSITY_SCORE_CAP = 100.0
# Age (H4 candles) beyond which block density is penalized ×0.5 (spec §7.1.1).
_BLOCK_AGE_PENALTY_THRESHOLD = 80


@dataclass(frozen=True)
class BlockResult:
    upper: float          # block ceiling (highest swing wick)
    lower: float          # block floor (lowest swing close, or vice versa for bull)
    touches: int          # number of confirmed touches
    age_h4: int           # approximate age in H4 candles
    density_raw: float    # raw score before normalization
    valid: bool           # False if block doesn't meet min_touches / min_width


@dataclass(frozen=True)
class SweepResult:
    detected: bool
    direction: str            # 'bearish' (short setup) or 'bullish' (long setup)
    sweep_candle_bars_ago: int  # 1 = just-closed candle, 2 = one before, etc.
    penetration_value: float  # wick extension in native price units
    score: int                # 0–100 sweep probability score
    score_detail: dict        # per-factor breakdown for gate_results JSONB
    reason: str               # human-readable pass/fail reason


_NO_SWEEP = SweepResult(
    detected=False,
    direction='',
    sweep_candle_bars_ago=0,
    penetration_value=0.0,
    score=0,
    score_detail={},
    reason='no active sweep',
)


def _penetration_threshold(config: InstrumentConfig) -> float:
    """Minimum wick extension in price units to qualify as a sweep.

    FX/gold: sweep_penetration_pips × pip_size (absolute pips).
    Crypto:  sweep_penetration_pips is stored as a percentage (e.g. 0.02 = 0.02%);
             at evaluation we only have the block price, not current price, so for
             crypto we use the block level as the price reference.
    """
    p = config.signals
    if config.asset_class == 'crypto':
        # Stored as a percentage value; caller should scale by reference price.
        # Return the percentage as-is; liquidity.py checks handle this.
        return p.sweep_penetration_pips  # ← percentage form; engine multiplies by price
    return p.sweep_penetration_pips * config.pip_size


def _block_min_width(config: InstrumentConfig) -> float:
    """Minimum block width in price units (spec §7.1.1)."""
    p = config.signals
    if config.asset_class == 'crypto':
        return p.block_min_width_pips  # percentage; caller scales by reference price
    return p.block_min_width_pips * config.pip_size


def identify_block(
    structure: StructureResult,
    h4_candles: Sequence[Candle],
    config: InstrumentConfig,
) -> BlockResult | None:
    """Build a resistance or support block from a confirmed triangle structure.

    Returns None if structure is not ASCENDING or DESCENDING, or if the block
    fails minimum width / touch requirements.
    """
    p = config.signals

    if structure.state == StructureState.ASCENDING_TRIANGLE:
        upper = structure.resistance_high
        lower = structure.resistance_low
        touches = structure.resistance_touches
    elif structure.state == StructureState.DESCENDING_TRIANGLE:
        upper = structure.support_high
        lower = structure.support_low
        touches = structure.resistance_touches
    else:
        return None

    if upper is None or lower is None:
        return None

    width = upper - lower
    min_width = _block_min_width(config)

    # For crypto, min_width is a percentage; use the block mid-price as reference.
    if config.asset_class == 'crypto' and upper > 0:
        min_width = p.block_min_width_pips / 100.0 * ((upper + lower) / 2.0)

    if width < min_width:
        return BlockResult(
            upper=upper, lower=lower, touches=touches,
            age_h4=0, density_raw=0.0, valid=False,
        )

    if touches < p.block_min_touches:
        return BlockResult(
            upper=upper, lower=lower, touches=touches,
            age_h4=0, density_raw=0.0, valid=False,
        )

    # Age in H4 candles = distance from pattern start to end of window.
    age_h4 = len(h4_candles) - structure.pattern_start_idx
    # Density: (touches × 10) + (age × 0.5), penalty ×0.5 if age > 80 H4 candles.
    density_raw = (touches * 10) + (age_h4 * 0.5)
    if age_h4 > _BLOCK_AGE_PENALTY_THRESHOLD:
        density_raw *= 0.5

    return BlockResult(
        upper=upper, lower=lower, touches=touches,
        age_h4=age_h4, density_raw=density_raw, valid=True,
    )


def _density_component(block: BlockResult) -> int:
    """Liquidity density score component: 0–30 (spec §7.3)."""
    normalized = min(block.density_raw / _DENSITY_SCORE_CAP, 1.0)
    return round(normalized * 30)


def _wick_extension_component(penetration: float, pip_size: float, is_crypto: bool) -> int:
    """Wick extension component: 0–5 pts per pip / 0.01%, capped at 20 (spec §7.3)."""
    if is_crypto:
        # penetration is already in price units; convert to 0.01% units
        # This is evaluated at sweep time; reference price = block level (approximate)
        pct_units = penetration * 100.0  # e.g., 0.0005 × 100 = 0.05 → 5 × 0.01% units
        pts = pct_units * 5
    else:
        pips = penetration / pip_size if pip_size > 0 else 0.0
        pts = pips * 5
    return min(int(pts), 20)


def _close_quality_component(candle: Candle, direction: str) -> int:
    """Close quality: lower 25% of candle range = +20, 25–50% = +10, else 0 (spec §7.3)."""
    candle_range = candle.high - candle.low
    if candle_range <= 0:
        return 0
    # For bear sweep: "close in lower 25% of candle body" means close is near the low.
    # For bull sweep: close near the high.
    if direction == 'bearish':
        position = (candle.close - candle.low) / candle_range  # 0 = at low, 1 = at high
        if position <= 0.25:
            return 20
        if position <= 0.50:
            return 10
    else:  # bullish
        position = (candle.high - candle.close) / candle_range  # 0 = at high
        if position <= 0.25:
            return 20
        if position <= 0.50:
            return 10
    return 0


def _ema_proximity_component(
    candle: Candle,
    ema21: float | None,
    ema50: float | None,
    direction: str,
    pip_size: float,
    is_crypto: bool,
) -> int:
    """EMA proximity component: EMA21 touch = +15, EMA50 = +10, neither = 0 (spec §7.3).

    Spec §8.1: 'touch' = within 3 pips / 0.03% of EMA value.
    For bear sweep: check candle HIGH vs EMAs. For bull sweep: candle LOW vs EMAs.
    """
    price = candle.high if direction == 'bearish' else candle.low

    def within(ema: float) -> bool:
        if is_crypto:
            return abs(price - ema) / ema <= 0.0003  # 0.03%
        return abs(price - ema) <= 3 * pip_size       # 3 pips

    if ema21 is not None and within(ema21):
        return 15
    if ema50 is not None and within(ema50):
        return 10
    return 0


def _atr_state_component(state: ATRState | None) -> int:
    """ATR state component: COMPRESSED=+15, NORMAL=+8, ELEVATED=+0, EXTREME=+0 (spec §7.3)."""
    if state == ATRState.COMPRESSED:
        return 15
    if state == ATRState.NORMAL:
        return 8
    return 0


def detect_sweep(
    h1_candles: Sequence[Candle],
    block: BlockResult,
    structure: StructureResult,
    config: InstrumentConfig,
    ema21: float | None,
    ema50: float | None,
    atr_state: ATRState | None,
) -> SweepResult:
    """Scan the last `sweep_expiry_candles` H1 bars for a valid sweep event.

    Bear sweep (ascending triangle → short setup):
      - Candle wick extends ABOVE block.upper by ≥ penetration threshold
      - Candle CLOSES below block.upper (back inside or below block)
      - No subsequent candle closes above block.upper (false-sweep filter)

    Bull sweep (descending triangle → long setup):
      - Candle wick extends BELOW block.lower by ≥ penetration threshold
      - Candle CLOSES above block.lower
      - No subsequent candle closes below block.lower
    """
    p = config.signals
    is_crypto = config.asset_class == 'crypto'
    pip_size = config.pip_size
    expiry = p.sweep_expiry_candles

    if structure.state == StructureState.ASCENDING_TRIANGLE:
        direction = 'bearish'
    elif structure.state == StructureState.DESCENDING_TRIANGLE:
        direction = 'bullish'
    else:
        return SweepResult(
            detected=False, direction='', sweep_candle_bars_ago=0,
            penetration_value=0.0, score=0, score_detail={},
            reason='no confirmed structure',
        )

    # Penetration threshold in price units.
    threshold = _penetration_threshold(config)
    if is_crypto:
        ref_price = (block.upper + block.lower) / 2.0
        threshold = p.sweep_penetration_pips / 100.0 * ref_price

    n = len(h1_candles)
    if n < 1:
        return _NO_SWEEP

    for bars_ago in range(1, min(expiry + 1, n + 1)):
        sweep_idx = n - bars_ago
        candle = h1_candles[sweep_idx]

        if direction == 'bearish':
            penetration = candle.high - block.upper
            close_inside = candle.close <= block.upper
        else:
            penetration = block.lower - candle.low
            close_inside = candle.close >= block.lower

        if penetration < threshold:
            continue
        if not close_inside:
            continue

        # False-sweep filter: check all candles AFTER the sweep candle.
        false_sweep = False
        for post_idx in range(sweep_idx + 1, n):
            post = h1_candles[post_idx]
            if direction == 'bearish' and post.close > block.upper:
                false_sweep = True
                break
            if direction == 'bullish' and post.close < block.lower:
                false_sweep = True
                break
        if false_sweep:
            continue

        # Valid sweep found. Compute the 5-factor score.
        density_pts = _density_component(block)
        wick_pts = _wick_extension_component(penetration, pip_size, is_crypto)
        close_pts = _close_quality_component(candle, direction)
        ema_pts = _ema_proximity_component(candle, ema21, ema50, direction, pip_size, is_crypto)
        atr_pts = _atr_state_component(atr_state)
        total = density_pts + wick_pts + close_pts + ema_pts + atr_pts

        detail = {
            'density': density_pts,
            'wick': wick_pts,
            'close': close_pts,
            'ema': ema_pts,
            'atr': atr_pts,
        }

        return SweepResult(
            detected=True,
            direction=direction,
            sweep_candle_bars_ago=bars_ago,
            penetration_value=penetration,
            score=total,
            score_detail=detail,
            reason=f'sweep confirmed {bars_ago} bars ago, score {total}',
        )

    return SweepResult(
        detected=False, direction=direction, sweep_candle_bars_ago=0,
        penetration_value=0.0, score=0, score_detail={},
        reason='no sweep within expiry window',
    )
