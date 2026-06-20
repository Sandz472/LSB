"""Broaden the trend/structure conflict analysis to ALL structure-admitted bars.

Hypothesis: the triangle's sloped leg drifts OPPOSITE to the trade direction
(ascending triangle = rising lows = bullish drift, but trade is SHORT;
 descending triangle = falling highs = bearish drift, but trade is LONG).
If true, Gate 1 (trend) and Gate 2 (structure) are structurally anti-correlated,
and no EMA speed on the SAME timeframe as the structure will resolve it.

Test: for every bar where Gate 2 admits a matching structure, measure the trend
alignment rate under three timeframes, each with EMA(21/50/89):
  (1) H1     — current code
  (2) H4     — same TF as the structure
  (3) Daily  — macro trend (the intended "trade with the trend" filter)

If H1 alignment ~0% but Daily alignment is meaningfully >0%, the conflict is a
timeframe-mismatch bug (fixable: assess trend on a higher TF). If alignment is
~0% on ALL timeframes, the conflict is structural (Gate 1 vs Gate 2 design
tension — an owner decision).

Trend series are precomputed once per timeframe and mapped by timestamp.

Usage:  python scripts/diag_trend_structure.py
"""

from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from lsb.data.config import load_config
from lsb.backtest.data import load_parquet, history_path
from lsb.signals.engine import MIN_H1_WINDOW
from lsb.signals.resample import resample_h1_to_h4
from lsb.signals.trend import TrendState, trend_state
from lsb.signals.structure import StructureState, detect_triangle

_CONFIG = ROOT / "config"
_HISTORY = ROOT / "data" / "history"
_INSTRUMENTS = ["EURUSD", "XAUUSD", "BTCUSD"]


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


def _trend_series(candles, p, min_window):
    """Return list of (ts, TrendState) for each bar from min_window onward."""
    out = []
    for i in range(min_window, len(candles)):
        win = candles[i - min_window + 1: i + 1]
        out.append((candles[i].ts, trend_state(win, p)))
    return out


def _aligned(trend, direction):
    if direction == "long":
        return trend == TrendState.BULLISH
    return trend == TrendState.BEARISH


def analyze(instrument: str) -> None:
    cfg = load_config(_CONFIG / f"{instrument}.yaml")
    p = cfg.signals
    candles = load_parquet(history_path(_HISTORY, instrument))

    # Precompute trend series per timeframe.
    # H1: MIN_H1_WINDOW warm-up. H4: need 89 H4 bars. Daily: need 89 daily bars.
    h4_all = resample_h1_to_h4(candles)
    daily_all = _resample_daily(candles)

    h1_trend = {ts: st for ts, st in _trend_series(candles, p, MIN_H1_WINDOW)}
    h4_trend = {ts: st for ts, st in _trend_series(h4_all, p, 90)}
    daily_trend = {ts: st for ts, st in _trend_series(daily_all, p, 90)}

    # Map each H1 bar's ts to the most recent H4/daily ts <= it.
    h4_ts_sorted = sorted(h4_trend.keys())
    daily_ts_sorted = sorted(daily_trend.keys())

    import bisect

    def latest_at(sorted_ts, target):
        i = bisect.bisect_right(sorted_ts, target) - 1
        return sorted_ts[i] if i >= 0 else None

    struct_admitted = 0
    align = {"h1": 0, "h4": 0, "daily": 0}
    have = {"h1": 0, "h4": 0, "daily": 0}
    # Track the sloped-leg drift direction vs trade direction.
    drift_opposite = 0
    # Direction breakdown + daily trend distribution per direction.
    dir_count = Counter()
    daily_by_dir = {"short": Counter(), "long": Counter()}

    for i in range(MIN_H1_WINDOW, len(candles)):
        win = candles[i - MIN_H1_WINDOW + 1: i + 1]
        h4 = resample_h1_to_h4(win)
        sub = h4[-p.triangle_max_candles:] if len(h4) > p.triangle_max_candles else h4
        structure = detect_triangle(sub, p)
        if structure.state == StructureState.ASCENDING_TRIANGLE:
            direction = "short"
        elif structure.state == StructureState.DESCENDING_TRIANGLE:
            direction = "long"
        else:
            continue
        struct_admitted += 1
        dir_count[direction] += 1

        ts = candles[i].ts
        # H1 trend
        st = h1_trend.get(ts)
        if st is not None:
            have["h1"] += 1
            if _aligned(st, direction):
                align["h1"] += 1
        # H4 trend (latest H4 bar at or before this H1 bar)
        h4ts = latest_at(h4_ts_sorted, ts)
        if h4ts is not None:
            st4 = h4_trend[h4ts]
            have["h4"] += 1
            if _aligned(st4, direction):
                align["h4"] += 1
        # Daily trend
        dts = latest_at(daily_ts_sorted, ts)
        if dts is not None:
            std = daily_trend[dts]
            have["daily"] += 1
            daily_by_dir[direction][std.name] += 1
            if _aligned(std, direction):
                align["daily"] += 1

    print(f"\n=== {instrument} === ({struct_admitted} structure-admitted bars)")
    print(f"  direction: short(asc)={dir_count['short']}  long(desc)={dir_count['long']}")
    for tf in ["h1", "h4", "daily"]:
        h = have[tf]
        a = align[tf]
        pct = (100 * a / h) if h else 0.0
        print(f"  {tf:6s} trend aligned: {a}/{h} ({pct:.1f}%)")
    print("  daily trend distribution per trade direction:")
    for d in ["short", "long"]:
        if daily_by_dir[d]:
            parts = ", ".join(f"{k}={v}" for k, v in sorted(daily_by_dir[d].items()))
            print(f"    {d:5s} (need {'BEARISH' if d=='short' else 'BULLISH'}): {parts}")


def main():
    for instr in _INSTRUMENTS:
        analyze(instr)


if __name__ == "__main__":
    main()
