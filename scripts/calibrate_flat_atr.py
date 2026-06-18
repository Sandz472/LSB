"""Calibration: pick a single shared k_atr for the ATR-relative flat leg.

Pre-computes H4 once per instrument (fast), then slides a window over H4.
For every window with >=2 swing highs and >=2 swing lows, computes the
flat-leg dispersion in ATR units: min(high_range/ATR, low_range/ATR).
Reports per-instrument distribution and the admit rate each candidate k_atr
would yield so we can pick one shared multiplier.

Target: EURUSD ~7.7% (its current admit rate at tol=0.5%).

Usage:  python scripts/calibrate_flat_atr.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from lsb.data.config import load_config
from lsb.backtest.data import load_parquet, history_path
from lsb.signals.resample import resample_h1_to_h4
from lsb.signals import structure as S
from lsb.signals.indicators import atr_series

_CONFIG = ROOT / "config"
_HISTORY = ROOT / "data" / "history"
_INSTRUMENTS = ["EURUSD", "XAUUSD", "BTCUSD"]
_CANDIDATES = [0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0]


def collect(instrument: str):
    cfg = load_config(_CONFIG / f"{instrument}.yaml")
    p = cfg.signals

    h1 = load_parquet(history_path(_HISTORY, instrument))
    h4 = resample_h1_to_h4(h1)          # single resample for the full series
    print(f"  {instrument}: {len(h1)} H1 -> {len(h4)} H4 bars")

    win = p.triangle_max_candles
    warm = p.atr_period + 1             # bars needed before ATR is valid

    best_ratios: list[float] = []
    n_windows = 0

    for end in range(win + warm, len(h4) + 1):
        sub = h4[end - win: end]        # exactly triangle_max_candles H4 bars
        n_windows += 1

        # ATR on the same window (Wilder; needs atr_period+1 bars — always met here)
        atrs = atr_series(sub, p.atr_period)
        if not atrs:
            continue
        atr = atrs[-1]
        if atr <= 0:
            continue

        highs_idx = S._swing_highs(sub, p.swing_lookback)
        lows_idx  = S._swing_lows(sub, p.swing_lookback)
        if len(highs_idx) < 2 or len(lows_idx) < 2:
            continue

        high_vals = [sub[k].high for k in highs_idx]
        low_vals  = [sub[k].low  for k in lows_idx]
        high_range = max(high_vals) - min(high_vals)
        low_range  = max(low_vals)  - min(low_vals)

        best_ratios.append(min(high_range / atr, low_range / atr))

    return n_windows, best_ratios


def main():
    print("flat-leg dispersion in ATR units (min of asc/desc leg per window)\n")
    data: dict[str, tuple[int, list[float]]] = {}
    for instr in _INSTRUMENTS:
        n, ratios = collect(instr)
        data[instr] = (n, ratios)
        if not ratios:
            print(f"  {instr}: no qualifying windows\n")
            continue
        s = sorted(ratios)
        m = len(s)
        pct = lambda q: s[min(m - 1, int(q * m))]
        print(f"  {instr}: {m} qualifying windows (of {n})")
        print(f"    p05={pct(.05):.3f}  p10={pct(.10):.3f}  median={pct(.50):.3f}  "
              f"p90={pct(.90):.3f}  p95={pct(.95):.3f}\n")

    print("admit rate by candidate k_atr (high_range or low_range <= k*ATR):\n")
    print("  instrument " + "".join(f"  k={k:.2f}" for k in _CANDIDATES))
    for instr, (n, ratios) in data.items():
        cells = []
        for k in _CANDIDATES:
            passed = sum(1 for r in ratios if r <= k)
            rate = 100.0 * passed / n if n else 0.0
            cells.append(f"{rate:6.2f}%")
        print(f"  {instr:10s}" + "".join(cells))
    print("\n  (target: EURUSD ~7.7% to match current tol=0.5% behaviour)")


if __name__ == "__main__":
    main()
