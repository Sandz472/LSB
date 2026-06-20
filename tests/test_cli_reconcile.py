"""CLI reconciliation tests — GBPUSD audit generated, counts reconcile.

These tests wire fetch → audit → load (dry-run) end-to-end using only
fixture data; no network or live DB is required.
"""

from __future__ import annotations

import json
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from lsb.data.fetch import fetch_history, _rows_to_csv
from lsb.data.resample import resample_h1
from lsb.data.audit import audit_history, write_audit
from lsb.data.load import load_candles


_FIXTURE_CACHE = Path(__file__).parent / "fixtures" / "raw"


def _make_fixture_cache(tmp_path: Path, instrument: str, rows: list[dict]) -> Path:
    """Write rows as a fixture month CSV and return the cache root."""
    cache_root = tmp_path / "raw"
    dest = cache_root / instrument / "2024-01.csv"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(_rows_to_csv(rows), encoding="utf-8")
    return cache_root


def _make_rows(instrument: str = "GBPUSD") -> list[dict]:
    """Return a minimal fixture H1 series for *instrument*: 3 bars + 1 weekend gap."""
    from datetime import datetime, timezone
    def ts(iso):
        return datetime.fromisoformat(iso).replace(tzinfo=timezone.utc)
    return [
        {"ts": ts("2024-01-05 16:00:00"), "open": Decimal("1.2700"),
         "high": Decimal("1.2750"), "low": Decimal("1.2680"), "close": Decimal("1.2720"), "volume": Decimal("800")},
        {"ts": ts("2024-01-05 17:00:00"), "open": Decimal("1.2720"),
         "high": Decimal("1.2760"), "low": Decimal("1.2700"), "close": Decimal("1.2740"), "volume": Decimal("650")},
        # Weekend gap here (Friday 17:00 → Monday 00:00)
        {"ts": ts("2024-01-08 00:00:00"), "open": Decimal("1.2740"),
         "high": Decimal("1.2780"), "low": Decimal("1.2720"), "close": Decimal("1.2760"), "volume": Decimal("700")},
    ]


# ---------------------------------------------------------------------------
# GBPUSD audit generated (ACCEPT-WHEN criterion)
# ---------------------------------------------------------------------------

def test_gbpusd_audit_file_generated(tmp_path):
    rows = _make_rows("GBPUSD")
    report = audit_history(rows, "GBPUSD", "fx")
    path = write_audit(report, tmp_path / "audit")
    assert path.exists()
    assert path.name == "GBPUSD_audit.json"


def test_gbpusd_audit_json_valid(tmp_path):
    rows = _make_rows("GBPUSD")
    report = audit_history(rows, "GBPUSD", "fx")
    path = write_audit(report, tmp_path / "audit")
    data = json.loads(path.read_text())
    assert data["instrument"] == "GBPUSD"
    assert "gaps_found" in data
    assert "counts" in data
    assert "gap_records" in data


# ---------------------------------------------------------------------------
# Count reconciliation (source ↔ audited ↔ loaded)
# ---------------------------------------------------------------------------

def test_counts_reconcile_source_equals_audited(tmp_path):
    rows = _make_rows("GBPUSD")
    cache_root = _make_fixture_cache(tmp_path, "GBPUSD", rows)

    series = fetch_history("GBPUSD", "dukascopy", date(2024, 1, 1), date(2024, 1, 31), cache_root)
    report = audit_history(series.rows, "GBPUSD", "fx")

    assert report.total_source_bars == len(series.rows), (
        f"source={len(series.rows)} audited={report.total_source_bars}"
    )


def test_counts_reconcile_audited_equals_loaded(tmp_path):
    """Loader receives the same row count that audit saw (no rows dropped)."""
    from tests.test_load import FakeExecutor

    rows = _make_rows("GBPUSD")
    cache_root = _make_fixture_cache(tmp_path, "GBPUSD", rows)

    series = fetch_history("GBPUSD", "dukascopy", date(2024, 1, 1), date(2024, 1, 31), cache_root)
    report = audit_history(series.rows, "GBPUSD", "fx")

    ex = FakeExecutor()
    n_loaded = load_candles(ex, "hash_xyz", "GBPUSD", "H1", series.rows)

    assert n_loaded == report.total_source_bars


def test_gap_counts_sum_to_gaps_found(tmp_path):
    rows = _make_rows("GBPUSD")
    report = audit_history(rows, "GBPUSD", "fx")
    assert sum(report.counts.values()) == report.gaps_found


# ---------------------------------------------------------------------------
# Full pipeline (fetch → audit → resample → load dry-run)
# ---------------------------------------------------------------------------

def test_full_pipeline_no_error(tmp_path):
    rows = _make_rows("EURUSD")
    cache_root = _make_fixture_cache(tmp_path, "EURUSD", rows)

    series = fetch_history("EURUSD", "dukascopy", date(2024, 1, 1), date(2024, 1, 31), cache_root)
    h4 = resample_h1(series.rows, "H4")
    d1 = resample_h1(series.rows, "D1")
    report = audit_history(series.rows, "EURUSD", "fx")
    write_audit(report, tmp_path / "audit")

    from tests.test_load import FakeExecutor
    ex = FakeExecutor()
    n_h1 = load_candles(ex, "hash_test", "EURUSD", "H1", series.rows)
    n_h4 = load_candles(ex, "hash_test", "EURUSD", "H4", h4)
    n_d1 = load_candles(ex, "hash_test", "EURUSD", "D1", d1)

    # Source count = audited count
    assert report.total_source_bars == n_h1
    # No rows lost
    assert n_h1 > 0


def test_pipeline_deterministic(tmp_path):
    """Running the full pipeline twice produces identical results."""
    rows = _make_rows("EURUSD")
    cache_root = _make_fixture_cache(tmp_path, "EURUSD", rows)

    def run():
        s = fetch_history("EURUSD", "dukascopy", date(2024, 1, 1), date(2024, 1, 31), cache_root)
        r = audit_history(s.rows, "EURUSD", "fx")
        return s.rows, r.gap_records, r.counts

    rows1, gaps1, counts1 = run()
    rows2, gaps2, counts2 = run()

    assert rows1 == rows2
    assert gaps1 == gaps2
    assert counts1 == counts2
