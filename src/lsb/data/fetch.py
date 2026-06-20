"""fetch_history — cached H1 data retrieval.

Raw downloads are cached to data/raw/<instrument>/<YYYY-MM>.csv (git-ignored).
Subsequent calls read the cache; the network is never hit twice for the same
month.  Audit, resample, and load always read the cache — no live-network
dependency after the first fetch.

CachedSeries: a lightweight container returned by fetch_history.
  .instrument  — e.g. "EURUSD"
  .rows        — list of H1 OHLCV dicts (sorted ascending by ts, all Decimal)
  .source      — "dukascopy" | "binance"
  .cached_from — Path to the cache root used
"""

from __future__ import annotations

import csv
import io
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Sequence


_CACHE_ROOT = Path(__file__).parents[4] / "data" / "raw"


@dataclass
class CachedSeries:
    instrument: str
    source: str
    rows: list[dict] = field(default_factory=list)
    cached_from: Path = field(default_factory=lambda: _CACHE_ROOT)


def _month_cache_path(instrument: str, year: int, month: int, cache_root: Path) -> Path:
    return cache_root / instrument / f"{year}-{month:02d}.csv"


def _rows_to_csv(rows: list[dict]) -> str:
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["ts", "open", "high", "low", "close", "volume"])
    for r in rows:
        w.writerow([
            r["ts"].isoformat(),
            str(r["open"]),
            str(r["high"]),
            str(r["low"]),
            str(r["close"]),
            str(r["volume"]) if r["volume"] is not None else "0",
        ])
    return buf.getvalue()


def _csv_to_rows(text: str) -> list[dict]:
    rows = []
    reader = csv.DictReader(io.StringIO(text))
    for r in reader:
        ts = datetime.fromisoformat(r["ts"])
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        rows.append({
            "ts":     ts,
            "open":   Decimal(r["open"]),
            "high":   Decimal(r["high"]),
            "low":    Decimal(r["low"]),
            "close":  Decimal(r["close"]),
            "volume": Decimal(r["volume"]),
        })
    return rows


def _fetch_live(instrument: str, source: str, year: int, month: int) -> list[dict]:
    """Call the appropriate live source. Import is deferred so tests never hit it."""
    if source == "dukascopy":
        from .sources import fetch_dukascopy_month
        return fetch_dukascopy_month(instrument, year, month)
    elif source == "binance":
        from .sources import fetch_binance_month
        return fetch_binance_month(instrument, year, month)
    else:
        raise ValueError(f"Unknown data source: {source!r}")


def _months_between(start: date, end: date) -> list[tuple[int, int]]:
    """Return all (year, month) pairs covering start..end inclusive."""
    result = []
    y, m = start.year, start.month
    while (y, m) <= (end.year, end.month):
        result.append((y, m))
        m += 1
        if m > 12:
            m = 1
            y += 1
    return result


def fetch_history(
    instrument: str,
    source: str,
    start: date,
    end: date,
    cache_root: Path | None = None,
) -> CachedSeries:
    """Fetch H1 OHLCV for *instrument* over [start, end].

    Month files are cached to *cache_root*/<instrument>/<YYYY-MM>.csv on first
    fetch and read from cache on subsequent calls.  Tests supply a fixture
    cache_root to avoid any network calls.

    *source* must be "dukascopy" or "binance" (read from InstrumentConfig.data_source).
    """
    root = Path(cache_root) if cache_root is not None else _CACHE_ROOT
    all_rows: list[dict] = []

    for year, month in _months_between(start, end):
        cache_path = _month_cache_path(instrument, year, month, root)

        if cache_path.exists():
            rows = _csv_to_rows(cache_path.read_text(encoding="utf-8"))
        else:
            rows = _fetch_live(instrument, source, year, month)
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            cache_path.write_text(_rows_to_csv(rows), encoding="utf-8")

        all_rows.extend(rows)

    # Filter to [start, end] date range and sort
    start_dt = datetime(start.year, start.month, start.day, tzinfo=timezone.utc)
    end_dt   = datetime(end.year, end.month, end.day, 23, 59, 59, tzinfo=timezone.utc)
    all_rows = [r for r in all_rows if start_dt <= r["ts"] <= end_dt]
    all_rows.sort(key=lambda r: r["ts"])

    return CachedSeries(
        instrument=instrument,
        source=source,
        rows=all_rows,
        cached_from=root,
    )
