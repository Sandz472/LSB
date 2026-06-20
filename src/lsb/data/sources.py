"""Raw data sources for Dukascopy (FX/XAU) and Binance (BTC).

The live download functions are intentionally thin and separated from the cache
layer in fetch.py.  Tests never call these directly — they use the fixture cache.

All returned rows are dicts:
  ts: datetime (UTC, tz-aware)
  open/high/low/close: Decimal
  volume: Decimal (tick volume for Dukascopy, trade volume for Binance)
"""

from __future__ import annotations

from datetime import datetime, date, timezone
from decimal import Decimal
from typing import Iterator
import csv
import io
import urllib.request
import struct
import zipfile


def _decimal(value: str | float | int) -> Decimal:
    return Decimal(str(value))


# ---------------------------------------------------------------------------
# Dukascopy (EUR, GBP, XAU) — downloads hourly JForex CSV
# ---------------------------------------------------------------------------

_DUKA_BASE = "https://www.dukascopy.com/datafeed"


def _dukascopy_url(instrument: str, year: int, month: int) -> str:
    """Build a Dukascopy monthly H1 CSV URL."""
    sym_map = {
        "EURUSD": "EURUSD",
        "GBPUSD": "GBPUSD",
        "XAUUSD": "XAUUSD",
    }
    sym = sym_map.get(instrument, instrument)
    return f"{_DUKA_BASE}/{sym}/{year}/{month:02d}/BID_candles_min_60.csv"


def fetch_dukascopy_month(instrument: str, year: int, month: int) -> list[dict]:
    """Fetch one month of H1 bars from Dukascopy for *instrument*.

    Returns rows sorted ascending by ts.  Raises on HTTP error.
    """
    url = _dukascopy_url(instrument, year, month)
    with urllib.request.urlopen(url, timeout=30) as resp:
        raw = resp.read().decode("utf-8")

    rows = []
    reader = csv.DictReader(io.StringIO(raw))
    for r in reader:
        ts_str = r.get("Gmt time") or r.get("Local time") or r.get("Time")
        if not ts_str:
            continue
        ts = datetime.strptime(ts_str.strip(), "%d.%m.%Y %H:%M:%S.%f")
        ts = ts.replace(tzinfo=timezone.utc)
        rows.append({
            "ts": ts,
            "open":   _decimal(r["Open"]),
            "high":   _decimal(r["High"]),
            "low":    _decimal(r["Low"]),
            "close":  _decimal(r["Close"]),
            "volume": _decimal(r.get("Volume") or "0"),
        })
    return sorted(rows, key=lambda r: r["ts"])


# ---------------------------------------------------------------------------
# Binance (BTC) — public klines endpoint, no auth required
# ---------------------------------------------------------------------------

_BINANCE_KLINES = "https://api.binance.com/api/v3/klines"


def fetch_binance_month(instrument: str, year: int, month: int) -> list[dict]:
    """Fetch one month of H1 bars from Binance for *instrument* (e.g. 'BTCUSD').

    Binance symbol: BTCUSD → BTCUSDT (the most liquid pair).
    Returns rows sorted ascending by ts.
    """
    sym_map = {"BTCUSD": "BTCUSDT"}
    symbol = sym_map.get(instrument, instrument)

    from calendar import monthrange
    start_ms = int(datetime(year, month, 1, tzinfo=timezone.utc).timestamp() * 1000)
    last_day = monthrange(year, month)[1]
    end_ms   = int(datetime(year, month, last_day, 23, 59, 59, tzinfo=timezone.utc).timestamp() * 1000)

    url = (
        f"{_BINANCE_KLINES}?symbol={symbol}&interval=1h"
        f"&startTime={start_ms}&endTime={end_ms}&limit=1000"
    )
    import json
    with urllib.request.urlopen(url, timeout=30) as resp:
        data = json.loads(resp.read())

    rows = []
    for k in data:
        ts = datetime.fromtimestamp(k[0] / 1000, tz=timezone.utc)
        rows.append({
            "ts":     ts,
            "open":   _decimal(k[1]),
            "high":   _decimal(k[2]),
            "low":    _decimal(k[3]),
            "close":  _decimal(k[4]),
            "volume": _decimal(k[5]),
        })
    return sorted(rows, key=lambda r: r["ts"])
