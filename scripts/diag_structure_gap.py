"""Diagnostic: where does the structure detector fall out, per instrument?

Isolates detect_triangle from the gate pipeline (no gate-1 trend dependency) and
tallies, over every H4 window, exactly which sub-test vetoes the pattern:
flat-resistance, rising-lows/falling-highs, apex band, or compression.

Answers the open question in ADR-004: is the XAU/BTC zero-structure wall in the
structure detector itself, or only in the gate-1 conjunction upstream?

Usage:  python scripts/diag_structure_gap.py
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
from lsb.signals import structure as S
from lsb.signals.structure import StructureState, detect_triangle

_CONFIG = ROOT / "config"
_HISTORY = ROOT / "data" / "history"
_INSTRUMENTS = ["EURUSD", "XAUUSD", "BTCUSD"]


def analyze(instrument: str) -> None:
    cfg = load_config(_CONFIG / f"{instrument}.yaml")
    p = cfg.signals
    candles = load_parquet(history_path(_HISTORY, instrument))

    states = Counter()
    # Reason a window failed to reach a CONFIRMED triangle, in detector order.
    fallout = Counter()
    # Diagnostics on the flat-resistance step specifically (the prime suspect).
    flat_ratios = []        # high_range / resistance for every window with >=2 swing highs
    flat_pass = 0
    rising_pass_after_flat = 0

    n = 0
    for i in range(MIN_H1_WINDOW, len(candles)):
        win = candles[i - MIN_H1_WINDOW + 1: i + 1]
        h4 = resample_h1_to_h4(win)
        sub = h4[-p.triangle_max_candles:] if len(h4) > p.triangle_max_candles else h4
        n += 1

        r = detect_triangle(sub, p)
        states[r.state.name] += 1

        # Re-derive the intermediate steps to locate fallout (ascending leg only;
        # mirror logic for descending is symmetric and rarely the binding one).
        if len(sub) < p.triangle_min_candles:
            fallout["too_few_candles"] += 1
            continue
        window = list(sub[-p.triangle_max_candles:])
        highs_idx = S._swing_highs(window, p.swing_lookback)
        lows_idx = S._swing_lows(window, p.swing_lookback)
        if len(highs_idx) < 2 or len(lows_idx) < 2:
            fallout["too_few_swings"] += 1
            continue

        high_vals = [window[k].high for k in highs_idx]
        resistance = sum(high_vals) / len(high_vals)
        high_range = max(high_vals) - min(high_vals)
        if resistance > 0:
            flat_ratios.append(high_range / resistance)

        flat_ok = resistance > 0 and high_range <= resistance * p.triangle_flat_tolerance_pct
        low_vals = [window[k].low for k in lows_idx]
        support = sum(low_vals) / len(low_vals)
        low_range = max(low_vals) - min(low_vals)
        flat_sup_ok = support > 0 and low_range <= support * p.triangle_flat_tolerance_pct

        if not flat_ok and not flat_sup_ok:
            fallout["no_flat_leg"] += 1
            continue
        flat_pass += 1

        if flat_ok:
            rising = S._rising_lows(low_vals, p.triangle_low_step_pct, p.triangle_min_higher_lows)
            if not rising:
                fallout["flat_but_no_rising_lows"] += 1
                continue
            rising_pass_after_flat += 1
            fallout["reached_apex_check"] += 1
        else:
            falling = S._falling_highs(high_vals, p.triangle_low_step_pct, p.triangle_min_higher_lows)
            if not falling:
                fallout["flat_but_no_falling_highs"] += 1
                continue
            rising_pass_after_flat += 1
            fallout["reached_apex_check"] += 1

    print(f"\n=== {instrument} === ({n} H4 windows evaluated)")
    print("  state distribution:")
    for st in ["ASCENDING_TRIANGLE", "DESCENDING_TRIANGLE", "FORMING", "NONE", "INVALIDATED"]:
        print(f"    {st:22s} {states.get(st, 0):>7d}")
    print("  fallout (detector-order, first veto wins):")
    for k in ["too_few_candles", "too_few_swings", "no_flat_leg",
              "flat_but_no_rising_lows", "flat_but_no_falling_highs", "reached_apex_check"]:
        if fallout.get(k):
            print(f"    {k:28s} {fallout[k]:>7d}")
    if flat_ratios:
        flat_ratios.sort()
        m = len(flat_ratios)
        pct = lambda q: flat_ratios[min(m - 1, int(q * m))]
        print(f"  flat-resistance ratio (high_range/resistance) vs tol={p.triangle_flat_tolerance_pct}:")
        print(f"    min={flat_ratios[0]:.5f}  p10={pct(.10):.5f}  median={pct(.50):.5f}  "
              f"p90={pct(.90):.5f}  max={flat_ratios[-1]:.5f}")
        print(f"    windows passing flat leg (asc or desc): {flat_pass}/{m}")


def main():
    for instr in _INSTRUMENTS:
        analyze(instr)


if __name__ == "__main__":
    main()
