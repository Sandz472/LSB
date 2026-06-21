"""Candle-table loader.

Writes normalized OHLCV rows into the candle table using an injectable
executor so the module can be unit-tested without a live database.

The real executor wraps a psycopg cursor.  The test executor is a fake sink.

Idempotent: ON CONFLICT DO NOTHING on (config_hash, instrument, timeframe, ts)
mirrors the UNIQUE in migrations/001_core.sql so re-runs do not duplicate rows.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Callable, Protocol, Sequence


_INSERT = """
INSERT INTO candle (config_hash, instrument, timeframe, ts, open, high, low, close, volume)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
ON CONFLICT (config_hash, instrument, timeframe, ts) DO NOTHING
"""


class Executor(Protocol):
    """Minimal protocol for a DB cursor or test fake."""
    def execute(self, sql: str, params: tuple) -> None: ...
    def executemany(self, sql: str, params_seq: list[tuple]) -> None: ...


def load_candles(
    executor: Executor,
    config_hash: str,
    instrument: str,
    timeframe: str,
    rows: Sequence[dict],
) -> int:
    """Insert *rows* into the candle table via *executor*.

    Returns the number of rows submitted (not necessarily inserted — duplicates
    are silently skipped by ON CONFLICT DO NOTHING).

    All numeric fields must be Decimal; ts must be a tz-aware datetime (UTC).
    """
    if timeframe not in ("H1", "H4", "D1"):
        raise ValueError(f"timeframe must be H1, H4, or D1; got {timeframe!r}")

    params_seq = [
        (
            config_hash,
            instrument,
            timeframe,
            row["ts"],
            row["open"],
            row["high"],
            row["low"],
            row["close"],
            row["volume"],
        )
        for row in rows
    ]
    executor.executemany(_INSERT, params_seq)
    return len(params_seq)
