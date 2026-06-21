"""LSB C2 signal engine — public re-exports."""

from .types import Side, GateResult
from .indicators import ema, atr, swing_high_mask, swing_low_mask, to_price_delta
from . import gate1_trend, gate2_structure, gate3_sweep, gate4_ema

__all__ = [
    "Side", "GateResult",
    "ema", "atr", "swing_high_mask", "swing_low_mask", "to_price_delta",
    "gate1_trend", "gate2_structure", "gate3_sweep", "gate4_ema",
]
