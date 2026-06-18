"""Parquet history loader for the backtest engine.

Reads data/history/<INSTR>_H1.parquet into a sorted list of Candle objects.
No Postgres dependency — offline/CI-safe.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from lsb.signals import Candle


def load_parquet(path: Path) -> list[Candle]:
    """Load a history Parquet file and return ascending-sorted Candle list.

    Validates that required columns exist and that there are no duplicate
    timestamps. Spread is carried through as-is (may be None).
    """
    df = pd.read_parquet(path)
    required = {"ts", "open", "high", "low", "close", "volume"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"{path.name}: missing columns {missing}")

    df = df.sort_values("ts").reset_index(drop=True)

    dupes = df["ts"].duplicated().sum()
    if dupes:
        raise ValueError(f"{path.name}: {dupes} duplicate timestamps after sort")

    has_spread = "spread" in df.columns

    candles: list[Candle] = []
    for row in df.itertuples(index=False):
        spread = row.spread if has_spread else None
        # pandas may give NaN for numeric spread; normalise to None
        if spread is not None and spread != spread:  # NaN check
            spread = None
        candles.append(Candle(
            ts=row.ts,
            open=float(row.open),
            high=float(row.high),
            low=float(row.low),
            close=float(row.close),
            volume=float(row.volume),
            spread=spread,
        ))
    return candles


def history_path(data_dir: Path, instrument: str, timeframe: str = "H1") -> Path:
    return data_dir / f"{instrument}_{timeframe}.parquet"
