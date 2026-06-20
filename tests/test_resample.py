"""Unit tests for resample_h1 — hand-verified reference values."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

import pytest

from lsb.data.resample import resample_h1


def _ts(iso: str) -> datetime:
    return datetime.fromisoformat(iso).replace(tzinfo=timezone.utc)


def _row(iso: str, o: str, h: str, l: str, c: str, v: str = "1000") -> dict:
    return {
        "ts": _ts(iso),
        "open": Decimal(o),
        "high": Decimal(h),
        "low": Decimal(l),
        "close": Decimal(c),
        "volume": Decimal(v),
    }


# ---------------------------------------------------------------------------
# H4 resampling
# ---------------------------------------------------------------------------

# 8 bars spanning two complete H4 buckets (00:00 and 04:00 UTC)
_H4_INPUT = [
    _row("2024-01-03 00:00:00", "1.0900", "1.0910", "1.0895", "1.0905"),
    _row("2024-01-03 01:00:00", "1.0905", "1.0915", "1.0900", "1.0910"),
    _row("2024-01-03 02:00:00", "1.0910", "1.0920", "1.0905", "1.0915"),
    _row("2024-01-03 03:00:00", "1.0915", "1.0925", "1.0910", "1.0920"),
    _row("2024-01-03 04:00:00", "1.0920", "1.0930", "1.0915", "1.0925"),
    _row("2024-01-03 05:00:00", "1.0925", "1.0935", "1.0920", "1.0930"),
    _row("2024-01-03 06:00:00", "1.0930", "1.0940", "1.0925", "1.0935"),
    _row("2024-01-03 07:00:00", "1.0935", "1.0945", "1.0930", "1.0940"),
]


def test_h4_two_complete_buckets():
    result = resample_h1(_H4_INPUT, "H4")
    assert len(result) == 2


def test_h4_first_bucket_ts():
    result = resample_h1(_H4_INPUT, "H4")
    assert result[0]["ts"] == _ts("2024-01-03 00:00:00")


def test_h4_second_bucket_ts():
    result = resample_h1(_H4_INPUT, "H4")
    assert result[1]["ts"] == _ts("2024-01-03 04:00:00")


def test_h4_ohlcv_hand_verified():
    # Bucket 00:00: bars 0-3
    # open = first bar open = 1.0900
    # high = max(1.0910, 1.0915, 1.0920, 1.0925) = 1.0925
    # low  = min(1.0895, 1.0900, 1.0905, 1.0910) = 1.0895
    # close = last bar close = 1.0920
    # volume = 4 × 1000 = 4000
    result = resample_h1(_H4_INPUT, "H4")
    b0 = result[0]
    assert b0["open"]   == Decimal("1.0900")
    assert b0["high"]   == Decimal("1.0925")
    assert b0["low"]    == Decimal("1.0895")
    assert b0["close"]  == Decimal("1.0920")
    assert b0["volume"] == Decimal("4000")


def test_h4_incomplete_trailing_bucket_dropped():
    # 9 bars: 2 full + 1 partial
    rows = _H4_INPUT + [_row("2024-01-03 08:00:00", "1.0940", "1.0950", "1.0935", "1.0945")]
    result = resample_h1(rows, "H4")
    assert len(result) == 2  # partial third bucket dropped


def test_h4_empty_input():
    assert resample_h1([], "H4") == []


# ---------------------------------------------------------------------------
# D1 resampling
# ---------------------------------------------------------------------------

_D1_INPUT = [
    _row("2024-01-03 00:00:00", "1.0800", "1.0900", "1.0750", "1.0850", "500"),
    _row("2024-01-03 06:00:00", "1.0850", "1.0950", "1.0820", "1.0900", "600"),
    _row("2024-01-03 12:00:00", "1.0900", "1.1000", "1.0880", "1.0980", "700"),
    _row("2024-01-03 18:00:00", "1.0980", "1.1020", "1.0960", "1.1000", "400"),
    _row("2024-01-04 00:00:00", "1.1000", "1.1050", "1.0990", "1.1020", "800"),
    _row("2024-01-04 06:00:00", "1.1020", "1.1060", "1.1000", "1.1040", "750"),
]


def test_d1_two_days():
    result = resample_h1(_D1_INPUT, "D1")
    assert len(result) == 2


def test_d1_first_day_ts():
    result = resample_h1(_D1_INPUT, "D1")
    assert result[0]["ts"] == _ts("2024-01-03 00:00:00")


def test_d1_hand_verified_ohlcv():
    # Day 2024-01-03: 4 bars
    # open = 1.0800, high = max(1.0900,1.0950,1.1000,1.1020) = 1.1020
    # low  = min(1.0750,1.0820,1.0880,1.0960) = 1.0750
    # close = 1.1000, volume = 500+600+700+400 = 2200
    result = resample_h1(_D1_INPUT, "D1")
    d0 = result[0]
    assert d0["open"]   == Decimal("1.0800")
    assert d0["high"]   == Decimal("1.1020")
    assert d0["low"]    == Decimal("1.0750")
    assert d0["close"]  == Decimal("1.1000")
    assert d0["volume"] == Decimal("2200")


def test_d1_empty_input():
    assert resample_h1([], "D1") == []


# ---------------------------------------------------------------------------
# Shared
# ---------------------------------------------------------------------------

def test_bad_timeframe_raises():
    with pytest.raises(ValueError, match="H4.*D1"):
        resample_h1(_H4_INPUT, "H1")


def test_output_sorted_ascending():
    # Provide D1 bars in reverse order
    rows = list(reversed(_D1_INPUT))
    result = resample_h1(rows, "D1")
    ts_list = [r["ts"] for r in result]
    assert ts_list == sorted(ts_list)


def test_deterministic_same_output_twice():
    r1 = resample_h1(_H4_INPUT, "H4")
    r2 = resample_h1(_H4_INPUT, "H4")
    assert r1 == r2
