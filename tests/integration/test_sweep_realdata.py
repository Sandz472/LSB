"""Real-data regression guard: Gate 3 (liquidity sweep) must not be silently dead.

Before the §7 sweep-target fix (ADR-006), detect_sweep measured penetration
against block.upper / block.lower — the *extreme swing wick* — which is an
outlier that price almost never reaches. The gate rejected 100% of setups across
all three instruments over 3 years: zero sweeps were ever detected.

The fix targets the block *level* (mean of swing wicks — the horizontal
resistance/support line where resting liquidity sits). These tests assert the
sweep path is reachable on real H1 data. If they fail, the sweep gate has
regressed to (effectively) always-False again.

Indices below are stable for the committed data/history/*_H1.parquet cache.
If a file is regenerated, the exact indices may shift — the slice-scan tests
tolerate small drift; the pinned-index tests document the known-good windows.
"""

from pathlib import Path

import pytest

from lsb.data.config import load_config
from lsb.backtest.data import load_parquet, history_path
from lsb.signals.engine import MIN_H1_WINDOW
from lsb.signals.resample import resample_h1_to_h4
from lsb.signals.structure import detect_triangle, StructureState
from lsb.signals.liquidity import identify_block, detect_sweep
from lsb.signals.trend import current_emas, current_atr_state

_HISTORY = Path("data/history")
_CONFIG = Path("config")


@pytest.fixture(scope="module")
def xauusd():
    cfg = load_config(_CONFIG / "XAUUSD.yaml")
    candles = load_parquet(history_path(_HISTORY, "XAUUSD"))
    return cfg, candles


@pytest.fixture(scope="module")
def btcusd():
    cfg = load_config(_CONFIG / "BTCUSD.yaml")
    candles = load_parquet(history_path(_HISTORY, "BTCUSD"))
    return cfg, candles


def _sweep_at(cfg, candles, i):
    """Replicate the engine's gate 2→3 flow (no trend dependency) for bar i."""
    p = cfg.signals
    win = candles[i - MIN_H1_WINDOW + 1: i + 1]
    h4 = resample_h1_to_h4(win)
    sub = h4[-p.triangle_max_candles:] if len(h4) > p.triangle_max_candles else h4
    structure = detect_triangle(sub, p)
    if structure.state not in (StructureState.ASCENDING_TRIANGLE,
                               StructureState.DESCENDING_TRIANGLE):
        return None
    block = identify_block(structure, h4, cfg)
    if block is None or not block.valid:
        return None
    ema21, ema50, _ = current_emas(win, p)
    atr_st = current_atr_state(win, p)
    return detect_sweep(win, block, structure, cfg, ema21, ema50, atr_st)


def _sweep_found_in_history(cfg, candles):
    """Scan every bar (step=1) and return True as soon as one sweep is detected.

    Sweeps are transient (1–3 bars, per sweep_expiry_candles), unlike triangles
    which persist for dozens of bars — so a coarse step can skip over every sweep
    window. Step=1 with early-exit stays fast while guaranteeing coverage.
    """
    for i in range(MIN_H1_WINDOW, len(candles)):
        s = _sweep_at(cfg, candles, i)
        if s is not None and s.detected:
            return True
    return False


def test_sweep_reachable_xauusd(xauusd):
    """Known-good sweep window (2024-02-12 cluster): a descending-triangle
    support sweep that the old max-wick target could never detect."""
    cfg, candles = xauusd
    found = any(
        _sweep_at(cfg, candles, i) is not None
        and _sweep_at(cfg, candles, i).detected
        for i in range(3960, 3985)
    )
    assert found, "No sweep detected in the known-good XAUUSD slice — gate 3 may be dead"


def test_sweep_reachable_btcusd(btcusd):
    """Known-good sweep window (2025-03-19 cluster): an ascending-triangle
    resistance sweep that the old max-wick target could never detect."""
    cfg, candles = btcusd
    found = any(
        _sweep_at(cfg, candles, i) is not None
        and _sweep_at(cfg, candles, i).detected
        for i in range(15390, 15415)
    )
    assert found, "No sweep detected in the known-good BTCUSD slice — gate 3 may be dead"


def test_sweeps_exist_in_history_xauusd(xauusd):
    """Full-history guard: at least one sweep must be detectable over XAUUSD."""
    cfg, candles = xauusd
    assert _sweep_found_in_history(cfg, candles), (
        "No sweep detected anywhere in XAUUSD history — "
        "sweep gate has effectively regressed to always-False"
    )


def test_sweeps_exist_in_history_btcusd(btcusd):
    """Full-history guard: at least one sweep must be detectable over BTCUSD."""
    cfg, candles = btcusd
    assert _sweep_found_in_history(cfg, candles), (
        "No sweep detected anywhere in BTCUSD history — "
        "sweep gate has effectively regressed to always-False"
    )
