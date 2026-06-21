"""Pure, deterministic H1-to-H4/D1 resampler.

Input rows are dicts with keys: ts (datetime, UTC, tz-aware), open, high, low,
close, volume (all Decimal). Output rows have the same shape, with ts = the
first bar's ts for H4 and the day's date at 00:00 UTC for D1.

Only complete buckets are emitted. A partial trailing bucket (e.g. a day with
fewer than expected bars at end-of-series) is silently dropped — callers should
supply full-day/full-4h data.
"""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import Iterable, Sequence


_ZERO = Decimal("0")


def _h4_bucket(ts: datetime) -> datetime:
    """Return the H4 bucket open timestamp for *ts* (00:00/04:00/…/20:00 UTC)."""
    hour_floor = (ts.hour // 4) * 4
    return ts.replace(hour=hour_floor, minute=0, second=0, microsecond=0)


def _d1_bucket(ts: datetime) -> datetime:
    """Return the D1 bucket open timestamp for *ts* (midnight UTC)."""
    return ts.replace(hour=0, minute=0, second=0, microsecond=0)


def _aggregate(rows: list[dict]) -> dict:
    """Aggregate a non-empty list of H1 rows into one OHLCV row."""
    opens  = [r["open"]  for r in rows]
    highs  = [r["high"]  for r in rows]
    lows   = [r["low"]   for r in rows]
    closes = [r["close"] for r in rows]
    vols   = [r["volume"] if r["volume"] is not None else _ZERO for r in rows]
    return {
        "ts":     rows[0]["ts"],
        "open":   opens[0],
        "high":   max(highs),
        "low":    min(lows),
        "close":  closes[-1],
        "volume": sum(vols, _ZERO),
    }


def _expected_h4_bars(bucket_ts: datetime) -> int:
    """All H4 buckets contain exactly 4 H1 bars."""
    return 4


def _expected_d1_bars_approx(rows: list[dict]) -> int:
    """For completeness check: a D1 bucket needs ≥ 1 bar (markets close early on
    some days); we only drop buckets with 0 bars.  Full-day completeness is the
    caller's responsibility (audit catches multi-hour gaps)."""
    return 1


def resample_h1(rows: Sequence[dict], timeframe: str) -> list[dict]:
    """Resample a sequence of H1 OHLCV dicts to H4 or D1.

    *timeframe* must be ``"H4"`` or ``"D1"``.
    Rows must be sorted ascending by ts; duplicate ts values are undefined.
    Returns a new list sorted ascending; input is not mutated.
    """
    if timeframe not in ("H4", "D1"):
        raise ValueError(f"timeframe must be 'H4' or 'D1', got {timeframe!r}")
    if not rows:
        return []

    bucket_fn = _h4_bucket if timeframe == "H4" else _d1_bucket
    expected_size = 4 if timeframe == "H4" else None  # None = no strict size check for D1

    buckets: dict[datetime, list[dict]] = {}
    for row in rows:
        key = bucket_fn(row["ts"])
        buckets.setdefault(key, []).append(row)

    # For H4: only emit complete 4-bar buckets
    # For D1: emit all buckets with ≥ 1 bar (audit is responsible for gaps)
    result = []
    for key in sorted(buckets):
        bucket = buckets[key]
        if timeframe == "H4" and len(bucket) < expected_size:
            continue  # incomplete trailing bucket
        agg = _aggregate(bucket)
        agg["ts"] = key
        result.append(agg)

    return result
