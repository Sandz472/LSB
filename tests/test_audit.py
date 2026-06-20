"""Unit tests for audit_history and classify_gap — hand-verified reference values."""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from decimal import Decimal

import pytest

from lsb.data.audit import classify_gap, audit_history, AuditReport, GapRecord


def _ts(iso: str) -> datetime:
    return datetime.fromisoformat(iso).replace(tzinfo=timezone.utc)


def _row(iso: str) -> dict:
    ts = _ts(iso)
    return {"ts": ts, "open": Decimal("1.0"), "high": Decimal("1.1"),
            "low": Decimal("0.9"), "close": Decimal("1.0"), "volume": Decimal("100")}


# ---------------------------------------------------------------------------
# classify_gap
# ---------------------------------------------------------------------------

def test_classify_weekend_gap_fx():
    # Friday 17:00 → Monday 00:00 UTC — spans Sat+Sun
    prev = _ts("2024-01-05 17:00:00")  # Friday
    nxt  = _ts("2024-01-08 00:00:00")  # Monday
    assert classify_gap(prev, nxt, "fx") == "weekend"


def test_classify_holiday_gap_christmas():
    # Dec 24 → Dec 26 on a weekday (non-weekend year check)
    prev = _ts("2024-12-24 17:00:00")
    nxt  = _ts("2024-12-26 00:00:00")
    assert classify_gap(prev, nxt, "fx") == "holiday"


def test_classify_new_years_gap():
    prev = _ts("2023-12-31 22:00:00")
    nxt  = _ts("2024-01-02 00:00:00")
    assert classify_gap(prev, nxt, "fx") == "holiday"


def test_classify_dst_gap_fx():
    # Spring-forward: 1-bar gap on a March Sunday
    prev = _ts("2024-03-31 00:00:00")  # Sunday March
    nxt  = _ts("2024-03-31 02:00:00")  # 1 bar missing
    assert classify_gap(prev, nxt, "fx") == "dst"


def test_classify_genuine_missing_fx():
    # Midweek gap, not a holiday, not DST
    prev = _ts("2024-02-14 10:00:00")  # Wednesday
    nxt  = _ts("2024-02-14 20:00:00")  # 9 bars missing
    assert classify_gap(prev, nxt, "fx") == "genuine_missing"


def test_classify_crypto_no_weekend_exemption():
    # Same weekend gap — but sessions="24_7" → NOT classified as weekend
    prev = _ts("2024-01-05 17:00:00")  # Friday
    nxt  = _ts("2024-01-08 00:00:00")  # Monday
    result = classify_gap(prev, nxt, "24_7")
    assert result != "weekend"


def test_classify_crypto_genuine_missing_on_weekday():
    prev = _ts("2024-02-07 08:00:00")
    nxt  = _ts("2024-02-07 18:00:00")
    assert classify_gap(prev, nxt, "24_7") == "genuine_missing"


def test_classify_bad_sessions_raises():
    with pytest.raises(ValueError, match="sessions"):
        classify_gap(_ts("2024-01-03 08:00:00"), _ts("2024-01-03 18:00:00"), "forex")


# ---------------------------------------------------------------------------
# audit_history
# ---------------------------------------------------------------------------

def _make_series(timestamps: list[str]) -> list[dict]:
    return [_row(ts) for ts in timestamps]


def test_audit_no_gaps():
    # Contiguous 5-bar series — no gaps > 2
    rows = _make_series([
        "2024-01-03 08:00:00",
        "2024-01-03 09:00:00",
        "2024-01-03 10:00:00",
        "2024-01-03 11:00:00",
        "2024-01-03 12:00:00",
    ])
    report = audit_history(rows, "EURUSD", "fx")
    assert report.gaps_found == 0
    assert report.gap_records == []
    assert report.total_source_bars == 5


def test_audit_small_gap_not_dispositioned():
    # 2-bar gap (within the ≤2 threshold) — should NOT appear in the report
    rows = _make_series([
        "2024-01-03 08:00:00",
        "2024-01-03 11:00:00",  # 2 bars missing
        "2024-01-03 12:00:00",
    ])
    report = audit_history(rows, "EURUSD", "fx")
    assert report.gaps_found == 0


def test_audit_weekend_gap_dispositioned():
    rows = _make_series([
        "2024-01-05 17:00:00",  # Friday
        "2024-01-08 00:00:00",  # Monday — weekend gap ~55 bars
        "2024-01-08 01:00:00",
    ])
    report = audit_history(rows, "EURUSD", "fx")
    assert report.gaps_found == 1
    assert report.gap_records[0].disposition == "weekend"
    assert "weekend" in report.counts


def test_audit_gbpusd_audit_generated(tmp_path):
    """ACCEPT-WHEN criterion: GBPUSD audit is generated."""
    from lsb.data.audit import write_audit
    rows = _make_series([
        "2024-01-05 17:00:00",
        "2024-01-08 00:00:00",
        "2024-01-08 01:00:00",
    ])
    report = audit_history(rows, "GBPUSD", "fx")
    path = write_audit(report, tmp_path)
    assert path.exists()
    assert path.name == "GBPUSD_audit.json"
    import json
    data = json.loads(path.read_text())
    assert data["instrument"] == "GBPUSD"
    assert data["total_source_bars"] == 3
    assert data["gaps_found"] == 1


def test_audit_counts_reconcile():
    """Counts dict must sum to gaps_found."""
    rows = _make_series([
        "2024-01-05 17:00:00",   # Friday → weekend
        "2024-01-08 00:00:00",   # Monday
        "2024-01-08 04:00:00",   # gap of 3 → genuine
        "2024-01-08 18:00:00",
        "2024-12-24 17:00:00",   # Christmas holiday gap
        "2024-12-26 00:00:00",
    ])
    report = audit_history(rows, "EURUSD", "fx")
    total_in_counts = sum(report.counts.values())
    assert total_in_counts == report.gaps_found


def test_audit_crypto_no_weekend_exemption():
    """BTC (24_7): weekend gap is classified as genuine_missing, not weekend."""
    rows = _make_series([
        "2024-01-05 17:00:00",
        "2024-01-08 00:00:00",
        "2024-01-08 01:00:00",
    ])
    report = audit_history(rows, "BTCUSD", "24_7")
    assert report.gaps_found == 1
    assert report.gap_records[0].disposition != "weekend"


def test_audit_deterministic():
    rows = _make_series([
        "2024-01-05 17:00:00",
        "2024-01-08 00:00:00",
        "2024-01-08 01:00:00",
    ])
    r1 = audit_history(rows, "EURUSD", "fx")
    r2 = audit_history(rows, "EURUSD", "fx")
    assert r1.gap_records == r2.gap_records
    assert r1.counts == r2.counts


def test_audit_bad_sessions_raises():
    rows = _make_series(["2024-01-03 08:00:00", "2024-01-03 09:00:00"])
    with pytest.raises(ValueError, match="sessions"):
        audit_history(rows, "EURUSD", "bad_sessions")
