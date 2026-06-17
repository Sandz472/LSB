"""Fetch raw H1 OHLCV history into data/history/<INSTRUMENT>_H1.parquet.

Sources:
  EURUSD, XAUUSD -- Dukascopy daily 1-minute BID candle files
    (https://datafeed.dukascopy.com/datafeed/<SYM>/<YYYY>/<MM-1>/<DD>/BID_candles_min_1.bi5),
    LZMA-compressed, 24-byte big-endian records (time_offset_s, open, close,
    low, high as integers scaled by 10/pip_size, volume as float32),
    resampled to H1. Falls back to Stooq's H1 CSV export if Dukascopy is
    unreachable.
  BTCUSD -- Binance public klines API (BTC/USDT spot, no auth required).
    Dukascopy only provides ~15 months of BTC history; Binance covers 3y+.

Usage:
    python scripts/fetch_history.py --instrument {EURUSD,XAUUSD,BTCUSD,all} [--years 3]
"""

import argparse
import asyncio
import hashlib
import json
import lzma
import re
import struct
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
import requests
import websockets

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lsb.data.config import InstrumentConfig, load_config  # noqa: E402

HISTORY_DIR = ROOT / "data" / "history"
CONFIG_DIR = ROOT / "config"

DUKASCOPY_BASE = "https://datafeed.dukascopy.com/datafeed"
BINANCE_KLINES_URL = "https://api.binance.com/api/v3/klines"
DERIV_WS_URL = "wss://ws.derivws.com/websockets/v3?app_id=1089"
DERIV_GRANULARITY = 3600
DERIV_MAX_COUNT = 5000

OHLCV_COLUMNS = ["ts", "open", "high", "low", "close", "volume", "spread"]


# ---------------------------------------------------------------------------
# Dukascopy (EURUSD, XAUUSD)
# ---------------------------------------------------------------------------

def _dukascopy_day_url(instrument: str, day: date) -> str:
    # Dukascopy encodes month 0-indexed (00 = January).
    return f"{DUKASCOPY_BASE}/{instrument}/{day.year}/{day.month - 1:02d}/{day.day:02d}/BID_candles_min_1.bi5"


def _parse_dukascopy_day(content: bytes, day: date, pip_size: float) -> list[tuple]:
    """Decode a daily BID_candles_min_1.bi5 file into per-minute OHLCV rows."""
    scale = 10.0 / pip_size
    decompressed = lzma.decompress(content)
    n_records = len(decompressed) // 24
    rows = []
    for i in range(n_records):
        offset_s, o, c, lo, hi, vol = struct.unpack_from(">IIIIIf", decompressed, i * 24)
        if vol == 0:
            # No trades this minute (overnight/weekend/holiday) - Dukascopy
            # still emits a flat carry-forward OHLC with volume=0.
            continue
        ts = datetime(day.year, day.month, day.day, tzinfo=timezone.utc) + timedelta(seconds=offset_s)
        rows.append((ts, o / scale, hi / scale, lo / scale, c / scale, float(vol)))
    return rows


DUKASCOPY_WORKERS = 16


def _fetch_dukascopy_day(session: requests.Session, instrument: str, day: date, pip_size: float) -> list[tuple]:
    try:
        resp = session.get(_dukascopy_day_url(instrument, day), timeout=15)
    except requests.RequestException:
        return []
    if resp.status_code != 200 or not resp.content:
        return []
    try:
        return _parse_dukascopy_day(resp.content, day, pip_size)
    except lzma.LZMAError:
        return []  # empty/corrupt day file (instrument didn't trade)


def fetch_dukascopy_h1(instrument: str, start: date, end: date, pip_size: float) -> pd.DataFrame:
    """Download daily 1-minute BID candles from Dukascopy (in parallel) and resample to H1."""
    days = []
    day = start
    while day <= end:
        days.append(day)
        day += timedelta(days=1)

    rows: list[tuple] = []
    with ThreadPoolExecutor(max_workers=DUKASCOPY_WORKERS) as pool:
        sessions = [requests.Session() for _ in range(DUKASCOPY_WORKERS)]
        futures = [
            pool.submit(_fetch_dukascopy_day, sessions[i % DUKASCOPY_WORKERS], instrument, d, pip_size)
            for i, d in enumerate(days)
        ]
        for future in futures:
            rows.extend(future.result())
    if not rows:
        raise ValueError(f"No Dukascopy data retrieved for {instrument} {start}..{end}")

    minute_df = pd.DataFrame(rows, columns=["ts", "open", "high", "low", "close", "volume"])
    minute_df = minute_df.set_index("ts").sort_index()
    h1 = minute_df.resample("1h").agg(
        open=("open", "first"),
        high=("high", "max"),
        low=("low", "min"),
        close=("close", "last"),
        volume=("volume", "sum"),
    )
    h1 = h1.dropna(subset=["open"])
    h1["spread"] = None
    return h1.reset_index()[OHLCV_COLUMNS]


# ---------------------------------------------------------------------------
# Stooq fallback (EURUSD, XAUUSD)
# ---------------------------------------------------------------------------

def _solve_stooq_pow(challenge: str, difficulty: int) -> int:
    target = "0" * difficulty
    nonce = 0
    while True:
        digest = hashlib.sha256(f"{challenge}{nonce}".encode("utf-8")).hexdigest()
        if digest.startswith(target):
            return nonce
        nonce += 1


def fetch_stooq_h1(symbol: str, start: date, end: date) -> pd.DataFrame:
    """Fallback H1 fetch via Stooq's CSV export, solving its JS proof-of-work."""
    session = requests.Session()
    url = f"https://stooq.com/q/d/l/?s={symbol}&i=60"
    resp = session.get(url, timeout=15)
    if resp.status_code == 200 and resp.text.lstrip().startswith("Date"):
        csv_text = resp.text
    else:
        match = re.search(r'c="([^"]+)",d=(\d+)', resp.text)
        if not match:
            raise ValueError("Could not locate Stooq proof-of-work challenge in response")
        challenge, difficulty = match.group(1), int(match.group(2))
        nonce = _solve_stooq_pow(challenge, difficulty)
        session.post(
            "https://stooq.com/__verify",
            json={"c": challenge, "n": nonce},
            timeout=15,
        )
        resp = session.get(url, timeout=15)
        csv_text = resp.text

    from io import StringIO

    raw = pd.read_csv(StringIO(csv_text))
    raw.columns = [c.strip().lower() for c in raw.columns]
    raw["ts"] = pd.to_datetime(raw["date"] + " " + raw["time"], utc=True)
    raw = raw.rename(columns={"vol": "volume"})
    if "volume" not in raw.columns:
        raw["volume"] = 0.0
    raw["spread"] = None
    df = raw[OHLCV_COLUMNS]
    mask = (df["ts"].dt.date >= start) & (df["ts"].dt.date <= end)
    return df.loc[mask].reset_index(drop=True)


# ---------------------------------------------------------------------------
# Binance (BTCUSD)
# ---------------------------------------------------------------------------

def fetch_binance_h1(start: date, end: date) -> pd.DataFrame:
    """Download H1 BTC/USDT klines from Binance public API (no auth required).

    Binance returns up to 1 000 candles per request; we paginate forward via
    startTime.  Prices are already in human-readable USD — no pip_size scaling.
    """
    start_ms = int(datetime.combine(start, datetime.min.time(), tzinfo=timezone.utc).timestamp() * 1000)
    end_ms = int(datetime.combine(end + timedelta(days=1), datetime.min.time(), tzinfo=timezone.utc).timestamp() * 1000)

    session = requests.Session()
    rows: list[tuple] = []
    cursor_ms = start_ms

    while cursor_ms < end_ms:
        resp = session.get(
            BINANCE_KLINES_URL,
            params={
                "symbol": "BTCUSDT",
                "interval": "1h",
                "startTime": cursor_ms,
                "endTime": end_ms - 1,
                "limit": 1000,
            },
            timeout=15,
        )
        resp.raise_for_status()
        batch = resp.json()
        if not batch:
            break
        for k in batch:
            ts = datetime.fromtimestamp(k[0] / 1000, tz=timezone.utc)
            rows.append((ts, float(k[1]), float(k[2]), float(k[3]), float(k[4]), float(k[5])))
        cursor_ms = batch[-1][0] + 3_600_000  # advance past the last returned candle

    if not rows:
        raise ValueError(f"No Binance data retrieved for BTCUSD {start}..{end}")

    df = pd.DataFrame(rows, columns=["ts", "open", "high", "low", "close", "volume"])
    df["spread"] = None
    return df[OHLCV_COLUMNS]


# ---------------------------------------------------------------------------
# Deriv (BOOM500)
# ---------------------------------------------------------------------------

async def _deriv_candles_batch(symbol: str, end_ts: int) -> list[dict]:
    async with websockets.connect(DERIV_WS_URL) as ws:
        request = {
            "ticks_history": symbol,
            "end": str(end_ts),
            "count": DERIV_MAX_COUNT,
            "style": "candles",
            "granularity": DERIV_GRANULARITY,
        }
        await ws.send(json.dumps(request))
        response = json.loads(await ws.recv())
        if "error" in response:
            raise RuntimeError(response["error"]["message"])
        return response.get("candles", [])


def fetch_deriv_h1(symbol: str, start: date, end: date) -> pd.DataFrame:
    """Page backwards through Deriv's ticks_history (H1 candles) until `start` is covered."""
    start_ts = int(datetime.combine(start, datetime.min.time(), tzinfo=timezone.utc).timestamp())
    end_ts = int(datetime.combine(end, datetime.min.time(), tzinfo=timezone.utc).timestamp()) + 86400

    candles_by_epoch: dict[int, dict] = {}
    cursor = end_ts
    while cursor > start_ts:
        candles = asyncio.run(_deriv_candles_batch(symbol, cursor))
        if not candles:
            break
        oldest = min(int(c["epoch"]) for c in candles)
        for c in candles:
            candles_by_epoch[int(c["epoch"])] = c
        if oldest >= cursor - DERIV_GRANULARITY:
            break  # no progress, stop paginating
        cursor = oldest

    rows = []
    for epoch, c in sorted(candles_by_epoch.items()):
        ts = datetime.fromtimestamp(epoch, tz=timezone.utc)
        if ts.date() < start or ts.date() > end:
            continue
        rows.append((ts, float(c["open"]), float(c["high"]), float(c["low"]), float(c["close"]), 0.0, None))
    if not rows:
        raise ValueError(f"No Deriv data retrieved for {symbol} {start}..{end}")
    return pd.DataFrame(rows, columns=OHLCV_COLUMNS)


# ---------------------------------------------------------------------------
# Dispatch + CLI
# ---------------------------------------------------------------------------

def fetch_ohlcv(instrument: str, start: date, end: date, config: InstrumentConfig) -> tuple[pd.DataFrame, str]:
    """Fetch H1 OHLCV for `instrument`, returning (dataframe, source_name_used)."""
    if instrument in ("EURUSD", "XAUUSD"):
        try:
            return fetch_dukascopy_h1(instrument, start, end, config.pip_size), "dukascopy"
        except Exception as exc:  # noqa: BLE001 - record and fall back
            print(f"  Dukascopy fetch failed ({exc!r}); falling back to Stooq")
            return fetch_stooq_h1(instrument.lower(), start, end), "stooq"
    if instrument == "BTCUSD":
        return fetch_binance_h1(start, end), "binance"
    raise ValueError(f"No fetch source configured for instrument {instrument!r}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--instrument", required=True, choices=["EURUSD", "XAUUSD", "BTCUSD", "all"])
    parser.add_argument("--years", type=float, default=3.0)
    args = parser.parse_args()

    instruments = ["EURUSD", "XAUUSD", "BTCUSD"] if args.instrument == "all" else [args.instrument]
    end = date.today()
    start = end - timedelta(days=round(args.years * 365.25))

    HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    for instrument in instruments:
        config = load_config(CONFIG_DIR / f"{instrument}.yaml")
        print(f"Fetching {instrument} H1 {start} .. {end} ...")
        df, source = fetch_ohlcv(instrument, start, end, config)
        out_path = HISTORY_DIR / f"{instrument}_H1.parquet"
        df.to_parquet(out_path, index=False)
        meta = {
            "instrument": instrument,
            "source": source,
            "requested_start": start.isoformat(),
            "requested_end": end.isoformat(),
            "rows": len(df),
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        }
        (HISTORY_DIR / f"{instrument}_H1.meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
        print(f"  {instrument}: {len(df)} H1 candles from {source} -> {out_path}")


if __name__ == "__main__":
    main()
