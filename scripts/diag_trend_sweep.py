"""Investigate the Gate 1 trend/sweep conflict.

For every bar where a sweep IS detected (Gate 3 fixed), examine the trend state
under three definitions, at and around the sweep bar, to determine whether the
trend filter is a timeframe-mismatch bug or a genuine design tension:

  (1) H1 EMA(21/50/89)   — current code (Gate 1)
  (2) H4 EMA(21/50/89)   — higher-timeframe hypothesis
  (3) H1 EMA(50/100/200) — slower-EMA hypothesis

For each sweep bar we record:
  - trend at T=0 (the sweep bar) under each definition
  - trend at T-24..T-1 (was the macro trend aligned BEFORE the sweep?)
  - trend at T+1..T+24 (when does the H1 trend realign? — look-ahead, diagnosis only)
  - whether the trend was aligned at ANY point in the 24 bars before the sweep

A sweep is "aligned" when the trend matches the trade direction (BULLISH for long,
BEARISH for short). The strategy fades counter-trend sweeps, so the macro trend
SHOULD be aligned at the sweep — if H1 says otherwise but H4/slow-EMA says aligned,
that's a timeframe-mismatch bug.

Usage:  python scripts/diag_trend_sweep.py
"""

from __future__ import annotations

import sys
from collections import Counter
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from lsb.data.config import load_config
from lsb.backtest.data import load_parquet, history_path
from lsb.signals.engine import MIN_H1_WINDOW
from lsb.signals.resample import resample_h1_to_h4
from lsb.signals.trend import TrendState, trend_state
from lsb.signals.structure import StructureState, detect_triangle
from lsb.signals.liquidity import identify_block, detect_sweep
from lsb.signals.trend import current_emas, current_atr_state

_CONFIG = ROOT / "config"
_HISTORY = ROOT / "data" / "history"
_INSTRUMENTS = ["EURUSD", "XAUUSD", "BTCUSD"]

_LOOKBACK = 24   # bars before the sweep to check for prior alignment
_LOOKAHEAD = 24  # bars after (diagnosis only)


def _aligned(trend: TrendState, direction: str) -> bool:
    if direction == "long":
        return trend == TrendState.BULLISH
    return trend == TrendState.BEARISH


def _trend_h1(candles, p, idx):
    """H1 trend at bar idx (window must start at MIN_H1_WINDOW)."""
    win = candles[idx - MIN_H1_WINDOW + 1: idx + 1]
    return trend_state(win, p)


def _trend_h4(candles, p, idx):
    """H4 trend at bar idx: resample the H1 window to H4, then run trend_state."""
    win = candles[idx - MIN_H1_WINDOW + 1: idx + 1]
    h4 = resample_h1_to_h4(win)
    # H4 needs its own warm-up; trend_state returns INVALID if too short.
    return trend_state(h4, p)


def _resample_daily(h1_candles):
    """Resample H1 to daily (UTC midnight boundary)."""
    import pandas as pd
    df = pd.DataFrame([{
        "ts": pd.Timestamp(c.ts), "open": c.open, "high": c.high,
        "low": c.low, "close": c.close, "volume": c.volume,
    } for c in h1_candles])
    df = df.set_index("ts")
    d = df.resample("1D", label="left").agg({
        "open": "first", "high": "max", "low": "min",
        "close": "last", "volume": "sum",
    }).dropna()
    from lsb.signals import Candle
    out = []
    for row in d.itertuples(index=True):
        out.append(Candle(ts=row.Index, open=row.open, high=row.high,
                          low=row.low, close=row.close, volume=row.volume))
    return out


def analyze(instrument: str) -> None:
    cfg = load_config(_CONFIG / f"{instrument}.yaml")
    p = cfg.signals
    candles = load_parquet(history_path(_HISTORY, instrument))

    # Slower-EMA config variant (50/100/200).
    p_slow = replace(
        p,
        ema_short_period=50,
        ema_mid_period=100,
        ema_long_period=200,
    )

    # Precompute daily trend series (macro trend hypothesis).
    daily_all = _resample_daily(candles)
    daily_trend = {}
    for i in range(90, len(daily_all)):
        win = daily_all[i - 90 + 1: i + 1]
        daily_trend[daily_all[i].ts] = trend_state(win, p)
    daily_ts_sorted = sorted(daily_trend.keys())
    import bisect

    def _daily_at(idx):
        ts = candles[idx].ts
        i = bisect.bisect_right(daily_ts_sorted, ts) - 1
        if i < 0:
            return TrendState.INVALID
        return daily_trend[daily_ts_sorted[i]]

    sweep_bars = []  # (idx, direction)
    n = 0
    for i in range(MIN_H1_WINDOW, len(candles)):
        n += 1
        win = candles[i - MIN_H1_WINDOW + 1: i + 1]
        h4 = resample_h1_to_h4(win)
        sub = h4[-p.triangle_max_candles:] if len(h4) > p.triangle_max_candles else h4
        structure = detect_triangle(sub, p)
        if structure.state not in (StructureState.ASCENDING_TRIANGLE,
                                   StructureState.DESCENDING_TRIANGLE):
            continue
        block = identify_block(structure, h4, cfg)
        if block is None or not block.valid:
            continue
        ema21, ema50, _ = current_emas(win, p)
        atr_st = current_atr_state(win, p)
        sweep = detect_sweep(win, block, structure, cfg, ema21, ema50, atr_st)
        if sweep.detected:
            direction = "short" if structure.state == StructureState.ASCENDING_TRIANGLE else "long"
            sweep_bars.append((i, direction))

    print(f"\n=== {instrument} === ({n} bars, {len(sweep_bars)} sweeps)")

    if not sweep_bars:
        print("  no sweeps — nothing to analyse")
        return

    # Per-definition alignment at T=0.
    align_t0 = {"h1": 0, "h4": 0, "h1_slow": 0, "daily": 0}
    # Was the trend aligned at ANY point in the 24 bars BEFORE the sweep?
    align_pre = {"h1": 0, "h4": 0, "h1_slow": 0, "daily": 0}
    # Bars after the sweep until H1 trend realigns (None = never within window).
    realign_h1 = []

    detail_lines = []
    detail_shown = 0

    for idx, direction in sweep_bars:
        t0_h1 = _trend_h1(candles, p, idx)
        t0_h4 = _trend_h4(candles, p, idx)
        t0_slow = _trend_h1(candles, p_slow, idx)
        t0_daily = _daily_at(idx)

        if _aligned(t0_h1, direction):
            align_t0["h1"] += 1
        if _aligned(t0_h4, direction):
            align_t0["h4"] += 1
        if _aligned(t0_slow, direction):
            align_t0["h1_slow"] += 1
        if _aligned(t0_daily, direction):
            align_t0["daily"] += 1

        # Prior alignment (lookback).
        pre_h1 = any(_aligned(_trend_h1(candles, p, j), direction)
                     for j in range(max(MIN_H1_WINDOW, idx - _LOOKBACK), idx))
        pre_h4 = any(_aligned(_trend_h4(candles, p, j), direction)
                     for j in range(max(MIN_H1_WINDOW, idx - _LOOKBACK), idx))
        pre_slow = any(_aligned(_trend_h1(candles, p_slow, j), direction)
                       for j in range(max(MIN_H1_WINDOW, idx - _LOOKBACK), idx))
        pre_daily = any(_aligned(_daily_at(j), direction)
                        for j in range(max(MIN_H1_WINDOW, idx - _LOOKBACK), idx))
        if pre_h1:
            align_pre["h1"] += 1
        if pre_h4:
            align_pre["h4"] += 1
        if pre_slow:
            align_pre["h1_slow"] += 1
        if pre_daily:
            align_pre["daily"] += 1

        # H1 realignment after sweep (look-ahead, diagnosis only).
        realign = None
        for k in range(1, _LOOKAHEAD + 1):
            j = idx + k
            if j >= len(candles):
                break
            if _aligned(_trend_h1(candles, p, j), direction):
                realign = k
                break
        realign_h1.append(realign)

        if detail_shown < 8:
            last = candles[idx]
            detail_lines.append(
                f"    ts={last.ts} dir={direction} "
                f"T0: h1={t0_h1.name:8s} h4={t0_h4.name:8s} slow={t0_slow.name:8s} "
                f"daily={t0_daily.name:8s} | "
                f"pre24 aligned: h1={pre_h1} h4={pre_h4} slow={pre_slow} daily={pre_daily} | "
                f"h1 realign in +{realign}h"
            )
            detail_shown += 1

    tot = len(sweep_bars)
    print(f"  aligned at T=0 (the sweep bar):")
    print(f"    H1 EMA(21/50/89)  [current]: {align_t0['h1']}/{tot}")
    print(f"    H4 EMA(21/50/89)  [higher TF]: {align_t0['h4']}/{tot}")
    print(f"    H1 EMA(50/100/200)[slower]: {align_t0['h1_slow']}/{tot}")
    print(f"    Daily EMA(21/50/89)[macro]: {align_t0['daily']}/{tot}")
    print(f"  aligned at ANY bar in the 24h BEFORE the sweep:")
    print(f"    H1 EMA(21/50/89)  [current]: {align_pre['h1']}/{tot}")
    print(f"    H4 EMA(21/50/89)  [higher TF]: {align_pre['h4']}/{tot}")
    print(f"    H1 EMA(50/100/200)[slower]: {align_pre['h1_slow']}/{tot}")
    print(f"    Daily EMA(21/50/89)[macro]: {align_pre['daily']}/{tot}")
    if realign_h1:
        never = sum(1 for r in realign_h1 if r is None)
        soon = sum(1 for r in realign_h1 if r is not None and r <= 6)
        print(f"  H1 trend realigns after sweep: within 6h={soon}/{tot}, "
              f"never(within 24h)={never}/{tot}")
    if detail_lines:
        print("  per-sweep detail:")
        for ln in detail_lines:
            print(ln)


def main():
    for instr in _INSTRUMENTS:
        analyze(instr)


if __name__ == "__main__":
    main()
