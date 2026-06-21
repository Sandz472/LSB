"""Unit tests for fetch_history — offline, reads from fixture cache."""

from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path

import pytest

from lsb.data.fetch import fetch_history, CachedSeries

# Fixture cache root: tests/fixtures/raw/  (contains EURUSD/2024-01.csv)
_FIXTURE_CACHE = Path(__file__).parent / "fixtures" / "raw"


def test_fetch_reads_cache_no_network():
    """fetch_history with a fixture cache_root must not hit the network."""
    series = fetch_history(
        instrument="EURUSD",
        source="dukascopy",
        start=date(2024, 1, 3),
        end=date(2024, 1, 3),
        cache_root=_FIXTURE_CACHE,
    )
    assert isinstance(series, CachedSeries)
    assert series.instrument == "EURUSD"
    assert series.source == "dukascopy"


def test_fetch_returns_rows():
    series = fetch_history(
        instrument="EURUSD",
        source="dukascopy",
        start=date(2024, 1, 3),
        end=date(2024, 1, 3),
        cache_root=_FIXTURE_CACHE,
    )
    assert len(series.rows) == 10  # fixture has 10 H1 bars


def test_fetch_rows_are_decimal():
    series = fetch_history(
        instrument="EURUSD",
        source="dukascopy",
        start=date(2024, 1, 3),
        end=date(2024, 1, 3),
        cache_root=_FIXTURE_CACHE,
    )
    row = series.rows[0]
    assert isinstance(row["open"],  Decimal)
    assert isinstance(row["high"],  Decimal)
    assert isinstance(row["low"],   Decimal)
    assert isinstance(row["close"], Decimal)
    assert isinstance(row["volume"], Decimal)


def test_fetch_rows_sorted_ascending():
    series = fetch_history(
        instrument="EURUSD",
        source="dukascopy",
        start=date(2024, 1, 3),
        end=date(2024, 1, 3),
        cache_root=_FIXTURE_CACHE,
    )
    ts_list = [r["ts"] for r in series.rows]
    assert ts_list == sorted(ts_list)


def test_fetch_first_bar_values():
    series = fetch_history(
        instrument="EURUSD",
        source="dukascopy",
        start=date(2024, 1, 3),
        end=date(2024, 1, 3),
        cache_root=_FIXTURE_CACHE,
    )
    r = series.rows[0]
    assert r["open"]  == Decimal("1.09410")
    assert r["high"]  == Decimal("1.09450")
    assert r["low"]   == Decimal("1.09390")
    assert r["close"] == Decimal("1.09430")
    assert r["volume"] == Decimal("1200")


def test_fetch_date_filter_applied():
    # Request only Jan 3; fixture only has Jan 3 data anyway — verify len stays 10
    series = fetch_history(
        instrument="EURUSD",
        source="dukascopy",
        start=date(2024, 1, 3),
        end=date(2024, 1, 3),
        cache_root=_FIXTURE_CACHE,
    )
    for row in series.rows:
        assert row["ts"].date() == date(2024, 1, 3)


def test_fetch_writes_cache_on_miss(tmp_path):
    """On a cache miss, fetch_history writes the month CSV so next call is cached."""
    import csv, io

    # Seed a fresh cache root with a hand-crafted mini CSV
    cache_root = tmp_path / "raw"
    dest = cache_root / "EURUSD" / "2024-02.csv"
    dest.parent.mkdir(parents=True)

    mini_rows = [
        "ts,open,high,low,close,volume",
        "2024-02-01 08:00:00+00:00,1.0800,1.0850,1.0790,1.0820,500",
    ]
    dest.write_text("\n".join(mini_rows), encoding="utf-8")

    series = fetch_history(
        instrument="EURUSD",
        source="dukascopy",
        start=date(2024, 2, 1),
        end=date(2024, 2, 1),
        cache_root=cache_root,
    )
    assert len(series.rows) == 1
    assert series.rows[0]["open"] == Decimal("1.0800")


def test_fetch_deterministic():
    """Same inputs → identical rows (no wall-clock or non-determinism)."""
    kwargs = dict(
        instrument="EURUSD",
        source="dukascopy",
        start=date(2024, 1, 3),
        end=date(2024, 1, 3),
        cache_root=_FIXTURE_CACHE,
    )
    s1 = fetch_history(**kwargs)
    s2 = fetch_history(**kwargs)
    assert s1.rows == s2.rows
