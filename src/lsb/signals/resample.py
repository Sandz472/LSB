"""H1 → H4 OHLCV resampling.

H4 boundaries are pinned to fixed UTC hours: 00, 04, 08, 12, 16, 20.
This is deterministic regardless of market session or DST — the candle
close timestamp falls within the bar that contains it.

An incomplete trailing H4 bar (where the current H1 does not fall on a
boundary) is dropped, so the result always contains complete H4 candles.

Spec decision: resample-in-engine rather than fetching native H4, to keep
Session A4 self-contained on already-audited H1 data. See plan notes.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Sequence

from lsb.signals import Candle

# H4 boundary hours in UTC (00:00, 04:00, 08:00, 12:00, 16:00, 20:00)
_H4_BOUNDARY_HOURS = frozenset({0, 4, 8, 12, 16, 20})
_H4_PERIOD_HOURS = 4


def _h4_bar_start(ts: datetime) -> datetime:
    """Return the UTC start of the H4 bar that contains `ts`."""
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    h = ts.hour
    bar_hour = (h // _H4_PERIOD_HOURS) * _H4_PERIOD_HOURS
    return ts.replace(hour=bar_hour, minute=0, second=0, microsecond=0)


def resample_h1_to_h4(h1_candles: Sequence[Candle]) -> list[Candle]:
    """Aggregate H1 candles into complete H4 candles.

    OHLC aggregation: O = first, H = max, L = min, C = last.
    Volume = sum; spread = mean of available spread values (or None).
    Timestamp of the H4 candle = the close of the last H1 bar in the group
    (i.e., the last H1 ts in that 4-hour window).
    """
    if not h1_candles:
        return []

    bars: dict[datetime, list[Candle]] = {}
    for candle in h1_candles:
        ts = candle.ts
        if isinstance(ts, str):
            ts = datetime.fromisoformat(ts)
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        key = _h4_bar_start(ts)
        bars.setdefault(key, []).append(candle)

    result: list[Candle] = []
    for bar_start in sorted(bars):
        group = bars[bar_start]
        open_ = group[0].open
        high = max(c.high for c in group)
        low = min(c.low for c in group)
        close = group[-1].close
        volume = sum(c.volume for c in group)
        spreads = [c.spread for c in group if c.spread is not None]
        spread = sum(spreads) / len(spreads) if spreads else None
        ts_close = group[-1].ts
        result.append(Candle(ts=ts_close, open=open_, high=high, low=low,
                              close=close, volume=volume, spread=spread))

    # Drop the trailing incomplete bar if the last H1 doesn't land on a boundary.
    if result:
        last_ts = result[-1].ts
        if isinstance(last_ts, str):
            last_ts = datetime.fromisoformat(last_ts)
        if isinstance(last_ts, datetime):
            if last_ts.tzinfo is None:
                last_ts = last_ts.replace(tzinfo=timezone.utc)
            # A complete H4 bar's last H1 falls at hour 03, 07, 11, 15, 19, or 23.
            if last_ts.hour not in {3, 7, 11, 15, 19, 23}:
                result.pop()

    return result


def _day_start(ts: datetime) -> datetime:
    """Return the UTC midnight start of the day that contains `ts`."""
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    return ts.replace(hour=0, minute=0, second=0, microsecond=0)


def resample_h1_to_daily(h1_candles: Sequence[Candle]) -> list[Candle]:
    """Aggregate H1 candles into complete daily (UTC midnight) candles.

    OHLC aggregation: O = first, H = max, L = min, C = last.
    Volume = sum; spread = mean of available spread values (or None).
    Timestamp of the daily candle = the close of the last H1 bar in the day.

    The trailing incomplete day (if the last H1 is not the final bar of its
    day) is dropped, so the result always contains complete daily candles.
    Used for the macro trend filter (Gate 1, ADR-007).
    """
    if not h1_candles:
        return []

    bars: dict[datetime, list[Candle]] = {}
    for candle in h1_candles:
        ts = candle.ts
        if isinstance(ts, str):
            ts = datetime.fromisoformat(ts)
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        key = _day_start(ts)
        bars.setdefault(key, []).append(candle)

    result: list[Candle] = []
    for day_start in sorted(bars):
        group = bars[day_start]
        open_ = group[0].open
        high = max(c.high for c in group)
        low = min(c.low for c in group)
        close = group[-1].close
        volume = sum(c.volume for c in group)
        spreads = [c.spread for c in group if c.spread is not None]
        spread = sum(spreads) / len(spreads) if spreads else None
        ts_close = group[-1].ts
        result.append(Candle(ts=ts_close, open=open_, high=high, low=low,
                             close=close, volume=volume, spread=spread))

    return result
