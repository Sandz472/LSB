"""Real-data regression guard: Gate 2 (structure) must not be silently dead.

Before the §6.1.1 fix, detect_triangle returned a CONFIRMED triangle exactly
ZERO times across the entire 3-year EURUSD history — every signal died at gate 1
or gate 2, so the backtest engine never had a single setup to act on. The strict
all-pivot monotonicity test in the rising-lows leg was the cause.

These tests assert the confirmed path is reachable on real H4 data. If they fail,
the structure gate has regressed to (effectively) always-NONE again.

Indices below are stable for the committed data/history/EURUSD_H1.parquet cache.
If that file is regenerated, the exact indices may shift — the slice-scan tests
tolerate small drift; the pinned-index tests document the known-good windows.
"""

from pathlib import Path

import pytest

from lsb.data.config import load_config
from lsb.backtest.data import load_parquet, history_path
from lsb.signals.engine import MIN_H1_WINDOW
from lsb.signals.resample import resample_h1_to_h4
from lsb.signals.structure import detect_triangle, StructureState

_HISTORY = Path("data/history")
_CONFIG = Path("config")


@pytest.fixture(scope="module")
def eurusd():
    cfg = load_config(_CONFIG / "EURUSD.yaml")
    candles = load_parquet(history_path(_HISTORY, "EURUSD"))
    return cfg, candles


def _detect_at(cfg, candles, i):
    p = cfg.signals
    win = candles[i - MIN_H1_WINDOW + 1: i + 1]
    h4 = resample_h1_to_h4(win)
    sub = h4[-p.triangle_max_candles:] if len(h4) > p.triangle_max_candles else h4
    return detect_triangle(sub, p)


def test_ascending_triangle_reachable(eurusd):
    cfg, candles = eurusd
    # Known-good ascending-triangle window (2024-07-22 cluster).
    found = any(
        _detect_at(cfg, candles, i).state == StructureState.ASCENDING_TRIANGLE
        for i in range(6930, 6940)
    )
    assert found, "No ASCENDING_TRIANGLE confirmed in the known-good slice — gate 2 may be dead"


def test_descending_triangle_reachable(eurusd):
    cfg, candles = eurusd
    # Known-good descending-triangle window (2024-10-29 cluster).
    found = any(
        _detect_at(cfg, candles, i).state == StructureState.DESCENDING_TRIANGLE
        for i in range(8625, 8640)
    )
    assert found, "No DESCENDING_TRIANGLE confirmed in the known-good slice — gate 2 may be dead"


def test_confirmed_triangles_exist_in_history(eurusd):
    """Sampled sweep: at least a handful of confirmed triangles over the history."""
    cfg, candles = eurusd
    confirmed = 0
    for i in range(MIN_H1_WINDOW, len(candles), 5):  # step 5 → fast, still catches clusters
        s = _detect_at(cfg, candles, i).state
        if s in (StructureState.ASCENDING_TRIANGLE, StructureState.DESCENDING_TRIANGLE):
            confirmed += 1
    assert confirmed >= 1, (
        f"Only {confirmed} confirmed triangles in sampled EURUSD history — "
        "structure gate has effectively regressed to always-NONE"
    )
