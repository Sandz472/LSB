"""Diagnostic: which detect_sweep() condition vetoes 100% of Gate-3 setups?

Replicates the engine gate pipeline (gates 1→3) over real history and, for every
setup that reaches Gate 3 with a valid block, instruments the three sweep
conditions to find the binding veto:

  (a) penetration  — candle wick must extend past block.upper by >= threshold
  (b) close_inside  — sweep candle must close back inside/below block.upper
  (c) false_sweep   — no subsequent candle may close beyond block.upper

Also reports how far block.upper (max swing-high wick) sits above the resistance
*level* (mean of swing highs), and the penetration distribution relative to the
threshold — to test the hypothesis that block.upper is an outlier wick that
recent compressed candles can never reach.

Usage:  python scripts/diag_sweep_gap.py
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
from lsb.signals.trend import TrendState, trend_state, current_emas, current_atr_state
from lsb.signals.structure import StructureState, detect_triangle
from lsb.signals.liquidity import identify_block, _penetration_threshold

_CONFIG = ROOT / "config"
_HISTORY = ROOT / "data" / "history"
_INSTRUMENTS = ["EURUSD", "XAUUSD", "BTCUSD"]


def analyze(instrument: str) -> None:
    cfg = load_config(_CONFIG / f"{instrument}.yaml")
    p = cfg.signals
    is_crypto = cfg.asset_class == "crypto"
    candles = load_parquet(history_path(_HISTORY, instrument))

    reached_gate3 = 0          # block valid, sweep about to be evaluated
    sweeps_detected = 0
    veto = Counter()           # penetration_fail | close_inside_fail | false_sweep_fail

    # Penetration (in threshold-multiples) measured against THREE reference points,
    # over the best candidate candle per setup, to find which reference is reachable:
    #   ref_maxwick  = block.upper (ascending) / block.lower (descending)  [current code]
    #   ref_level    = resistance_level / support_level (mean of swing wicks)
    #   ref_minclose = block.lower (ascending) / block.upper (descending)  [min swing close]
    pen_vs_maxwick = []
    pen_vs_level = []
    pen_vs_minclose = []
    detail_lines = []
    detail_shown = 0

    n = 0
    for i in range(MIN_H1_WINDOW, len(candles)):
        win = candles[i - MIN_H1_WINDOW + 1: i + 1]
        n += 1

        # --- Gate 2: structure (skip gate-1 trend conjunction to maximise setups) ---
        h4 = resample_h1_to_h4(win)
        sub = h4[-p.triangle_max_candles:] if len(h4) > p.triangle_max_candles else h4
        structure = detect_triangle(sub, p)
        if structure.state == StructureState.ASCENDING_TRIANGLE:
            direction = "short"
        elif structure.state == StructureState.DESCENDING_TRIANGLE:
            direction = "long"
        else:
            continue

        # --- Block ---
        block = identify_block(structure, h4, cfg)
        if block is None or not block.valid:
            continue

        reached_gate3 += 1

        # Threshold in price units (mirror detect_sweep).
        threshold = _penetration_threshold(cfg)
        ref_price = (block.upper + block.lower) / 2.0
        if is_crypto:
            threshold = p.sweep_penetration_pips / 100.0 * ref_price
        if threshold <= 0:
            threshold = 1e-12

        bearish = direction == "short"
        # The three reference points for the sweep target.
        if bearish:
            ref_maxwick = block.upper            # max swing-high wick (current code)
            ref_level = structure.resistance_level
            ref_minclose = block.lower           # min swing-high close
        else:
            ref_maxwick = block.lower            # min swing-low wick (current code)
            ref_level = structure.support_level
            ref_minclose = block.upper           # max swing-low close

        expiry = p.sweep_expiry_candles
        h1 = win
        m = len(h1)

        # Best (max) penetration across the expiry window, per reference.
        best_maxwick = best_level = best_minclose = None
        found = False
        for bars_ago in range(1, min(expiry + 1, m + 1)):
            sidx = m - bars_ago
            candle = h1[sidx]
            if bearish:
                pen_mw = candle.high - ref_maxwick
                pen_lv = candle.high - ref_level if ref_level else None
                pen_mc = candle.high - ref_minclose
                close_inside = candle.close <= ref_maxwick
            else:
                pen_mw = ref_maxwick - candle.low
                pen_lv = (ref_level - candle.low) if ref_level else None
                pen_mc = ref_minclose - candle.low
                close_inside = candle.close >= ref_maxwick

            if best_maxwick is None or pen_mw > best_maxwick:
                best_maxwick = pen_mw
            if pen_lv is not None and (best_level is None or pen_lv > best_level):
                best_level = pen_lv
            if best_minclose is None or pen_mc > best_minclose:
                best_minclose = pen_mc

            # Replicate the real veto logic (against max-wick, the current code).
            if pen_mw < threshold:
                continue
            if not close_inside:
                veto["close_inside_fail"] += 1
                break
            false_sweep = False
            for post_idx in range(sidx + 1, m):
                post = h1[post_idx]
                if bearish and post.close > ref_maxwick:
                    false_sweep = True
                    break
                if (not bearish) and post.close < ref_maxwick:
                    false_sweep = True
                    break
            if false_sweep:
                veto["false_sweep_fail"] += 1
                break
            found = True
            break
        else:
            veto["penetration_fail"] += 1

        if best_maxwick is not None:
            pen_vs_maxwick.append(best_maxwick / threshold)
        if best_level is not None:
            pen_vs_level.append(best_level / threshold)
        if best_minclose is not None:
            pen_vs_minclose.append(best_minclose / threshold)

        if found:
            sweeps_detected += 1

        # Dump the first few setups in full so we can see actual price levels.
        if detail_shown < 5 and best_maxwick is not None:
            last = h1[-1]
            lv = ref_level if ref_level else 0.0
            plv = (best_level / threshold) if best_level is not None else 0.0
            detail_lines.append(
                f"    setup #{reached_gate3} dir={direction} "
                f"maxwick={ref_maxwick:.5f} level={lv:.5f} "
                f"minclose={ref_minclose:.5f} | lastH={last.high:.5f} lastL={last.low:.5f} "
                f"lastC={last.close:.5f} | pen/maxwick={best_maxwick/threshold:.2f} "
                f"pen/level={plv:.2f} pen/minclose={best_minclose/threshold:.2f}"
            )
            detail_shown += 1

    print(f"\n=== {instrument} === ({n} H1 bars scanned, {reached_gate3} structure+block setups)")
    print(f"  sweeps detected (vs max-wick, current code): {sweeps_detected}")
    print("  veto breakdown (first binding condition per setup):")
    for k in ["penetration_fail", "close_inside_fail", "false_sweep_fail"]:
        print(f"    {k:22s} {veto.get(k, 0):>7d}")

    def report(name, vals):
        if not vals:
            print(f"  best penetration / threshold vs {name}: (no data)")
            return
        vals = sorted(vals)
        m2 = len(vals)
        pct = lambda q: vals[min(m2 - 1, int(q * m2))]
        print(f"  best penetration / threshold vs {name}:")
        print(f"    min={vals[0]:.3f}  p10={pct(.10):.3f}  p50={pct(.50):.3f}  "
              f"p90={pct(.90):.3f}  max={vals[-1]:.3f}   (>=1.0 = sweep achievable)")
        print(f"    setups with penetration >= threshold: "
              f"{sum(1 for x in vals if x >= 1.0)}/{m2}")

    report("MAX-WICK (current)", pen_vs_maxwick)
    report("LEVEL (mean wick)", pen_vs_level)
    report("MIN-CLOSE", pen_vs_minclose)
    if detail_lines:
        print("  sample setups:")
        for ln in detail_lines:
            print(ln)


def main():
    for instr in _INSTRUMENTS:
        analyze(instr)


if __name__ == "__main__":
    main()
