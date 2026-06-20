"""Real-data regression guard: Gate 1 daily-trend fix (ADR-007).

Before ADR-007, Gate 1 assessed trend on H1 EMA(21/50/89). A triangle's sloped
leg (rising lows / falling highs) is a counter-trend move that dominates the
reactive H1 EMAs, so at the sweep the H1 trend always opposed the trade
direction — 100% of detected sweeps were vetoed at Gate 1.

The fix: Gate 1 uses the daily (macro) trend, which preserves the macro
direction through the counter-trend pullback/rally. These tests assert:

  1. At the known BTC sweep bar, the daily trend ALIGNS with the trade, so
     evaluate() passes gates 1-3 (no longer rejected at Gate 1).
  2. At the same bar, the H1 trend (fallback) still REJECTS at Gate 1 —
     proving the daily timeframe is what unblocks the setup.

Indices are stable for the committed data/history/BTCUSD_H1.parquet cache.
"""

from pathlib import Path

import pytest

from lsb.data.config import load_config, config_hash as compute_hash
from lsb.backtest.data import load_parquet, history_path
from lsb.signals.engine import MIN_H1_WINDOW, evaluate
from lsb.signals.resample import resample_h1_to_h4, resample_h1_to_daily
from lsb.signals.structure import StructureState, detect_triangle
from lsb.signals.liquidity import identify_block, detect_sweep
from lsb.signals.trend import TrendState, trend_state, current_emas, current_atr_state

_HISTORY = Path("data/history")
_CONFIG = Path("config")


@pytest.fixture(scope="module")
def btcusd():
    cfg = load_config(_CONFIG / "BTCUSD.yaml")
    candles = load_parquet(history_path(_HISTORY, "BTCUSD"))
    return cfg, candles


def _daily_trend_at(candles, cfg, idx):
    """Macro (daily) trend at H1 bar idx — resample all prior H1 to daily."""
    p = cfg.signals
    h1_win = candles[max(0, idx - MIN_H1_WINDOW + 1): idx + 1]
    # Daily window: use all H1 history up to and including this bar, resampled.
    # (A daily bar is complete only once its last H1 bar has closed; the batch
    # resample drops the trailing incomplete day, so no look-ahead.)
    daily = resample_h1_to_daily(candles[: idx + 1])
    if len(daily) < p.ema_long_period + 1:
        return TrendState.INVALID
    return trend_state(daily, p)


def _eval_at(candles, cfg, idx, daily_trend=None):
    h = compute_hash(cfg)
    win = candles[idx - MIN_H1_WINDOW + 1: idx + 1]
    return evaluate(win, cfg, h, daily_trend=daily_trend)


def test_daily_trend_unblocks_btc_sweep(btcusd):
    """At the known BTC sweep window (2025-03-19), the daily trend aligns with
    the short setup, so gates 1-3 pass — the setup is no longer dead at Gate 1."""
    cfg, candles = btcusd
    # Scan the known sweep window for a bar where gates 1-3 pass under daily trend.
    found = False
    for i in range(15390, 15415):
        if i >= len(candles):
            break
        dt = _daily_trend_at(candles, cfg, i)
        result = _eval_at(candles, cfg, i, daily_trend=dt)
        # Gates 1-3 pass if not rejected at 1, 2, or 3.
        if result.rejected_at_gate is None or result.rejected_at_gate >= 4:
            found = True
            # The daily trend must be BEARISH (short setup needs bearish macro trend).
            assert dt == TrendState.BEARISH, (
                f"daily trend {dt.name} — expected BEARISH for the short setup"
            )
            break
    assert found, (
        "No bar in the known BTC sweep window passes gates 1-3 under daily trend — "
        "the Gate 1 daily-trend fix may have regressed"
    )


def test_h1_trend_still_rejects_btc_sweep(btcusd):
    """Contrast: under the H1 trend (fallback, no daily_trend), the same sweep
    window is rejected at Gate 1 — proving the H1 timeframe was the blocker and
    the daily timeframe is what unblocks it."""
    cfg, candles = btcusd
    rejected_at_1 = False
    for i in range(15390, 15415):
        if i >= len(candles):
            break
        # H1 fallback: daily_trend=None → evaluate uses H1 trend.
        result = _eval_at(candles, cfg, i, daily_trend=None)
        if result.rejected_at_gate == 1:
            rejected_at_1 = True
            break
    assert rejected_at_1, (
        "H1 trend did not reject the BTC sweep window — the contrast that proves "
        "the daily-trend fix matters no longer holds"
    )
