"""Gate 6 — Session Active (§8.1#6 · §3.3).

Session VALID per §3.3 (all times UTC):
  London   07:00–16:00
  New York 13:00–21:00
  Overlap  13:00–16:00  (emergent — London ∩ New York)
  Asia     00:00–09:00  (JPY pairs ONLY)
  Crypto   24/7

A bar is BLOCKED if it is within session_edge_buffer_min minutes of any session
open/close, OR within news_buffer_min minutes of a Tier-1 news event
(M12 — Phase-A stub: no feed wired, so news never blocks unless windows passed).

Crypto (sessions="24_7") is continuous: no time-of-day band, no session edges
(prior build wrongly applied FX bands to BTC — §R).  Only the news stub can block.

Pure, deterministic function of the candle's own timestamp — never wall-clock.
"""

from __future__ import annotations
from datetime import datetime, timezone, timedelta
from typing import Sequence

from lsb.config.models import InstrumentConfig, StrategyParams
from .types import GateResult, Side

# Session bands as (open_minute, close_minute) in UTC minutes-of-day (§3.3).
_LONDON = (7 * 60, 16 * 60)
_NEW_YORK = (13 * 60, 21 * 60)
_ASIA = (0 * 60, 9 * 60)        # JPY pairs only


def _fx_bands(instrument: str) -> list[tuple[int, int]]:
    bands = [_LONDON, _NEW_YORK]
    if "JPY" in instrument.upper():
        bands.append(_ASIA)
    return bands


def evaluate(
    candle: dict,
    sp: StrategyParams,
    ic: InstrumentConfig,
    side: Side,
    news_windows: Sequence[tuple[datetime, datetime]] = (),
) -> GateResult:
    """Return Gate 6 result for a single H1 *candle* (uses candle['ts']).

    *side* is unused (session validity is direction-agnostic) but kept in the
    uniform gate signature for the conjunction.
    news_windows: optional [(start, end)] Tier-1 event spans; empty = stub-pass.
    """
    ts = candle["ts"]
    if ts.tzinfo is None:
        return GateResult(False, state="NO_TZ",
                          detail={"reason": "candle ts must be tz-aware UTC"})
    ts_utc = ts.astimezone(timezone.utc)

    # News stub (§3.3 M12): BLOCKED within news_buffer_min of any event span.
    news_buf = timedelta(minutes=sp.news_buffer_min)
    for start, end in news_windows:
        if (start - news_buf) <= ts_utc <= (end + news_buf):
            return GateResult(False, state="NEWS_BLOCKED",
                              detail={"event_start": start.isoformat(),
                                      "event_end": end.isoformat()})

    # Crypto 24/7 — continuous, no session edges.
    if ic.sessions == "24_7":
        return GateResult(True, state="SESSION_24_7", detail={})

    # FX/commodity: time-of-day bands with edge buffers.
    buf = sp.session_edge_buffer_min
    m = ts_utc.hour * 60 + ts_utc.minute
    bands = _fx_bands(ic.instrument)

    in_any_band = False
    for o, c in bands:
        if o <= m < c:
            in_any_band = True
            # Clear of both edges within THIS band → valid.
            if o + buf <= m < c - buf:
                return GateResult(True, state="SESSION_ACTIVE",
                                  detail={"minute_utc": m, "band": [o, c]})

    if in_any_band:
        return GateResult(False, state="SESSION_EDGE",
                          detail={"minute_utc": m, "buffer_min": buf,
                                  "reason": "within edge buffer of every active band"})
    return GateResult(False, state="SESSION_CLOSED",
                      detail={"minute_utc": m, "bands": [list(b) for b in bands]})
