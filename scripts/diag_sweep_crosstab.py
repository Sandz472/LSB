"""Cross-tabulate sweep occurrence against gate-1 (trend) and gate-2 (structure).

Computes every component independently (no short-circuit) so we can see, of the
bars where a sweep IS detectable (vs the resistance/support level), how many also
have an aligned trend and a confirmed matching structure — i.e. which gate is the
binding filter that stops sweeps from producing qualified signals.

Usage:  python scripts/diag_sweep_crosstab.py
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
from lsb.signals.liquidity import identify_block, detect_sweep

_CONFIG = ROOT / "config"
_HISTORY = ROOT / "data" / "history"
_INSTRUMENTS = ["EURUSD", "XAUUSD", "BTCUSD"]


def analyze(instrument: str) -> None:
    cfg = load_config(_CONFIG / f"{instrument}.yaml")
    p = cfg.signals
    candles = load_parquet(history_path(_HISTORY, instrument))

    sweep_bars = 0
    sweep_and_trend = 0
    sweep_and_structure = 0
    sweep_and_trend_and_structure = 0
    # When a sweep occurs but the full conjunction fails, which gate vetoes?
    veto = Counter()
    n = 0
    detail_lines = []
    detail_shown = 0

    for i in range(MIN_H1_WINDOW, len(candles)):
        win = candles[i - MIN_H1_WINDOW + 1: i + 1]
        n += 1

        # --- Structure (independent of trend) ---
        h4 = resample_h1_to_h4(win)
        sub = h4[-p.triangle_max_candles:] if len(h4) > p.triangle_max_candles else h4
        structure = detect_triangle(sub, p)
        if structure.state not in (StructureState.ASCENDING_TRIANGLE,
                                   StructureState.DESCENDING_TRIANGLE):
            continue

        # --- Block ---
        block = identify_block(structure, h4, cfg)
        if block is None or not block.valid:
            continue

        # --- Sweep (independent of trend; uses fixed level logic) ---
        ema21, ema50, _ = current_emas(win, p)
        atr_st = current_atr_state(win, p)
        sweep = detect_sweep(win, block, structure, cfg, ema21, ema50, atr_st)
        if not sweep.detected:
            continue

        sweep_bars += 1

        # --- Trend (independent) ---
        t_state = trend_state(win, p)
        struct_dir = "short" if structure.state == StructureState.ASCENDING_TRIANGLE else "long"
        trend_aligned = (
            (struct_dir == "short" and t_state == TrendState.BEARISH)
            or (struct_dir == "long" and t_state == TrendState.BULLISH)
        )
        if trend_aligned:
            sweep_and_trend += 1
        else:
            veto["trend_not_aligned"] += 1

        # Structure matching direction is already guaranteed (we only kept
        # ASCENDING/DESCENDING). The real question is trend alignment.
        if trend_aligned:
            sweep_and_trend_and_structure += 1

        if detail_shown < 10:
            last = win[-1]
            detail_lines.append(
                f"    ts={last.ts} struct_dir={struct_dir} sweep_dir={sweep.direction} "
                f"trend={t_state.name} level={block.level:.5f} "
                f"lastH={last.high:.5f} lastL={last.low:.5f} lastC={last.close:.5f} "
                f"apex={structure.apex_proximity:.2f}"
            )
            detail_shown += 1

    print(f"\n=== {instrument} === ({n} bars)")
    print(f"  bars with a confirmed structure + valid block + SWEEP: {sweep_bars}")
    print(f"    of those, also trend-aligned (gate 1): {sweep_and_trend}")
    print(f"    of those, full gate 1+2+3 conjunction: {sweep_and_trend_and_structure}")
    if sweep_bars:
        print(f"  veto when sweep present but conjunction fails:")
        for k, v in veto.items():
            print(f"    {k}: {v} ({100*v/sweep_bars:.0f}%)")
    if detail_lines:
        print("  sweep-bar details:")
        for ln in detail_lines:
            print(ln)


def main():
    for instr in _INSTRUMENTS:
        analyze(instr)


if __name__ == "__main__":
    main()
