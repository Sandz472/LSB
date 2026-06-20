"""Raw data sources for Dukascopy (FX/XAU) and Binance (BTC).

Dukascopy:
  Per-hour LZMA-compressed tick files (bi5 format) are fetched and aggregated
  into H1 bid-side OHLCV bars.  Tick record layout (big-endian, 20 bytes):
    ms_offset : uint32   milliseconds from start of hour
    ask_raw   : uint32   ask price * _DUKA_POINT[symbol]
    bid_raw   : uint32   bid price * _DUKA_POINT[symbol]
    ask_vol   : float32  ask-side volume
    bid_vol   : float32  bid-side volume

Binance:
  Public /api/v3/klines endpoint — no auth required.

All returned rows are dicts:
  ts: datetime (UTC, tz-aware)
  open/high/low/close: Decimal
  volume: Decimal (tick volume for Dukascopy, trade volume for Binance)
"""

from __future__ import annotations

import lzma
import struct
import urllib.request
import urllib.error
from calendar import monthrange
from datetime import datetime, timezone
from decimal import Decimal


def _decimal(value: str | float | int) -> Decimal:
    return Decimal(str(value))


# ---------------------------------------------------------------------------
# Dukascopy (EUR, GBP, XAU) — per-hour bi5 tick files → H1 OHLCV
# ---------------------------------------------------------------------------

_DUKA_BASE = "https://datafeed.dukascopy.com/datafeed"

# Integer divisor to recover the floating-point price
_DUKA_POINT: dict[str, int] = {
    "EURUSD": 100000,
    "GBPUSD": 100000,
    "XAUUSD": 1000,
}


def fetch_dukascopy_month(instrument: str, year: int, month: int) -> list[dict]:
    """Fetch one month of H1 bars from Dukascopy bi5 tick files.

    For each hour in the month a separate bi5 file is fetched.  404s (weekends,
    holidays, zero-liquidity hours) are silently skipped.  H1 bars are bid-side
    OHLCV: open = first tick bid, high = max bid, low = min bid, close = last bid,
    volume = sum(bid_vol + ask_vol).
    """
    scale = _DUKA_POINT.get(instrument, 100000)
    month0 = month - 1  # Dukascopy months are 0-indexed
    last_day = monthrange(year, month)[1]
    rows: list[dict] = []

    for day in range(1, last_day + 1):
        for hour in range(24):
            url = (
                f"{_DUKA_BASE}/{instrument}/{year}"
                f"/{month0:02d}/{day:02d}/{hour:02d}h_ticks.bi5"
            )
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
            )
            try:
                with urllib.request.urlopen(req, timeout=30) as resp:
                    compressed = resp.read()
            except urllib.error.HTTPError as exc:
                if exc.code == 404:
                    continue
                raise

            if not compressed:
                continue

            try:
                raw = lzma.decompress(compressed, format=lzma.FORMAT_ALONE)
            except lzma.LZMAError:
                continue

            n = len(raw) // 20
            if n == 0:
                continue

            bids: list[float] = []
            total_vol = 0.0
            for i in range(n):
                _ms, _ask_raw, bid_raw, ask_vol, bid_vol = struct.unpack_from(">IIIff", raw, i * 20)
                bids.append(bid_raw / scale)
                total_vol += ask_vol + bid_vol

            bar_ts = datetime(year, month, day, hour, 0, 0, tzinfo=timezone.utc)
            rows.append({
                "ts":     bar_ts,
                "open":   _decimal(bids[0]),
                "high":   _decimal(max(bids)),
                "low":    _decimal(min(bids)),
                "close":  _decimal(bids[-1]),
                "volume": _decimal(round(total_vol, 2)),
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
    import json

    sym_map = {"BTCUSD": "BTCUSDT"}
    symbol = sym_map.get(instrument, instrument)

    last_day = monthrange(year, month)[1]
    start_ms = int(datetime(year, month, 1, tzinfo=timezone.utc).timestamp() * 1000)
    end_ms   = int(datetime(year, month, last_day, 23, 59, 59, tzinfo=timezone.utc).timestamp() * 1000)

    url = (
        f"{_BINANCE_KLINES}?symbol={symbol}&interval=1h"
        f"&startTime={start_ms}&endTime={end_ms}&limit=1000"
    )
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
