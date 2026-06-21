"""Gate 8 — Global Risk State Clear (§8.1#8 · §9.3 · §12).

M11 = TRADING_ALLOWED: daily/weekly drawdown not breached; consecutive-loss
limit not hit.

Phase-A: there is no live account, so the drawdown / loss-streak machine is a
documented STUB-PASS (TRADING_ALLOWED assumed) — see GATE_SPECIFICATION.md Gate 8.

The ATR EXTREME → no-trade rule (§4.2.2 / §9.3 risk tier = 0%) is an ACTIVE
pre-filter regardless of the stub: an EXTREME volatility regime forces no-trade.
atr_state is the explicit input (classifier deferred to ADR-008).

Pure function — no DB writes.
"""

from __future__ import annotations

from lsb.config.models import InstrumentConfig, StrategyParams
from .types import GateResult, Side, AtrState


def evaluate(
    sp: StrategyParams,
    ic: InstrumentConfig,
    side: Side,
    atr_state: AtrState = AtrState.NORMAL,
    trading_allowed: bool = True,
) -> GateResult:
    """Return Gate 8 result.

    atr_state:        ATR EXTREME forces no-trade (§4.2.2 / §9.3).
    trading_allowed:  M11 stub.  Phase-A default True; a live risk machine (Phase B)
                      would set this False on a drawdown/loss-streak breach.
    """
    if atr_state is AtrState.EXTREME:
        return GateResult(False, state="ATR_EXTREME_NO_TRADE",
                          detail={"reason": "ATR EXTREME pre-filter (§4.2.2/§9.3)"})
    if not trading_allowed:
        return GateResult(False, state="TRADING_HALTED",
                          detail={"reason": "M11 drawdown/loss-streak breach"})
    return GateResult(True, state="TRADING_ALLOWED",
                      detail={"phase_a_stub": True})
