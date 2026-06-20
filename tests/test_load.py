"""Unit tests for load_candles — fake executor, round-trip and idempotency."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

import pytest

from lsb.data.load import load_candles
from conftest import FakeExecutor


def _ts(iso: str) -> datetime:
    return datetime.fromisoformat(iso).replace(tzinfo=timezone.utc)


def _row(iso: str, o: str = "1.0900", h: str = "1.0950", l: str = "1.0850", c: str = "1.0920") -> dict:
    return {
        "ts": _ts(iso),
        "open": Decimal(o),
        "high": Decimal(h),
        "low": Decimal(l),
        "close": Decimal(c),
        "volume": Decimal("1000"),
    }


_HASH = "abc123"
_INST = "EURUSD"

_ROWS = [
    _row("2024-01-03 08:00:00"),
    _row("2024-01-03 09:00:00"),
    _row("2024-01-03 10:00:00"),
]


# ---------------------------------------------------------------------------
# Basic round-trip
# ---------------------------------------------------------------------------

def test_load_returns_count():
    ex = FakeExecutor()
    n = load_candles(ex, _HASH, _INST, "H1", _ROWS)
    assert n == 3


def test_load_all_rows_inserted():
    ex = FakeExecutor()
    load_candles(ex, _HASH, _INST, "H1", _ROWS)
    assert len(ex.rows) == 3


def test_load_decimal_preserved():
    ex = FakeExecutor()
    load_candles(ex, _HASH, _INST, "H1", _ROWS[:1])
    row = ex.rows[0]
    assert isinstance(row[4], Decimal)  # open
    assert isinstance(row[5], Decimal)  # high
    assert isinstance(row[6], Decimal)  # low
    assert isinstance(row[7], Decimal)  # close


def test_load_config_hash_and_instrument_in_row():
    ex = FakeExecutor()
    load_candles(ex, _HASH, _INST, "H1", _ROWS[:1])
    assert ex.rows[0][0] == _HASH
    assert ex.rows[0][1] == _INST


def test_load_timeframe_in_row():
    ex = FakeExecutor()
    load_candles(ex, _HASH, _INST, "H4", _ROWS[:1])
    assert ex.rows[0][2] == "H4"


# ---------------------------------------------------------------------------
# Idempotency (ON CONFLICT DO NOTHING simulation)
# ---------------------------------------------------------------------------

def test_load_idempotent_no_duplicates():
    ex = FakeExecutor()
    load_candles(ex, _HASH, _INST, "H1", _ROWS)
    n_before = len(ex.rows)
    load_candles(ex, _HASH, _INST, "H1", _ROWS)  # re-run same rows
    assert len(ex.rows) == n_before  # zero new rows inserted


def test_load_idempotent_different_config_hash():
    # Different config_hash → different rows, both inserted
    ex = FakeExecutor()
    load_candles(ex, "hash_a", _INST, "H1", _ROWS[:1])
    load_candles(ex, "hash_b", _INST, "H1", _ROWS[:1])
    assert len(ex.rows) == 2


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def test_load_bad_timeframe_raises():
    ex = FakeExecutor()
    with pytest.raises(ValueError, match="H1.*H4.*D1"):
        load_candles(ex, _HASH, _INST, "M15", _ROWS)


def test_load_empty_rows():
    ex = FakeExecutor()
    n = load_candles(ex, _HASH, _INST, "H1", [])
    assert n == 0
    assert len(ex.rows) == 0
