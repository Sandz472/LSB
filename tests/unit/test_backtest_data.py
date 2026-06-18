"""Tests for backtest/data.py — Parquet loader."""

from pathlib import Path

import pytest

from lsb.backtest.data import load_parquet
from lsb.signals import Candle

_HISTORY = Path("data/history")
_INSTRUMENTS = ["EURUSD", "XAUUSD", "BTCUSD"]


@pytest.mark.parametrize("instr", _INSTRUMENTS)
def test_load_returns_candles(instr):
    candles = load_parquet(_HISTORY / f"{instr}_H1.parquet")
    assert len(candles) > 0
    assert all(isinstance(c, Candle) for c in candles)


@pytest.mark.parametrize("instr", _INSTRUMENTS)
def test_ascending_sort(instr):
    candles = load_parquet(_HISTORY / f"{instr}_H1.parquet")
    ts_list = [c.ts for c in candles]
    assert ts_list == sorted(ts_list)


@pytest.mark.parametrize("instr", _INSTRUMENTS)
def test_no_duplicate_timestamps(instr):
    candles = load_parquet(_HISTORY / f"{instr}_H1.parquet")
    ts_list = [c.ts for c in candles]
    assert len(ts_list) == len(set(ts_list))


@pytest.mark.parametrize("instr", _INSTRUMENTS)
def test_ohlcv_are_floats(instr):
    candles = load_parquet(_HISTORY / f"{instr}_H1.parquet")
    for c in candles[:5]:
        assert isinstance(c.open, float)
        assert isinstance(c.high, float)
        assert isinstance(c.low, float)
        assert isinstance(c.close, float)
        assert isinstance(c.volume, float)


def test_missing_column_raises(tmp_path):
    import pandas as pd
    bad = tmp_path / "BAD_H1.parquet"
    pd.DataFrame({"ts": [], "open": [], "high": [], "low": []}).to_parquet(bad)
    with pytest.raises(ValueError, match="missing columns"):
        load_parquet(bad)
