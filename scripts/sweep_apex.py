"""Sensitivity sweep over the apex-proximity thresholds (Requirements v2.1 protocol).

Apex proximity only gates ENTRY into the gate pipeline — it never changes a
downstream gate result. So we run the full engine ONCE per instrument with apex
wide open ([0.0, 1.0]), record every structure-admitted bar's apex value and its
eventual 8-gate outcome, then apply each candidate [min, max] window as an instant
post-filter. One expensive pass per instrument; the whole grid is then analytical.

Output: for each (apex_min, apex_max), the count of bars whose structure gate would
pass (gate-2-admitted) and the count that fully qualify (all 8 gates), per instrument.

Usage:  python scripts/sweep_apex.py
"""

from __future__ import annotations

import dataclasses
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from lsb.data.config import load_config, config_hash as compute_hash
from lsb.backtest.data import load_parquet, history_path
from lsb.signals.engine import evaluate, MIN_H1_WINDOW
from lsb.signals.resample import resample_h1_to_h4
from lsb.signals.structure import detect_triangle

_CONFIG = ROOT / "config"
_HISTORY = ROOT / "data" / "history"
_INSTRUMENTS = ["EURUSD", "XAUUSD", "BTCUSD"]

# Candidate threshold grid (current production = min 0.75, max 0.95).
MINS = [0.50, 0.60, 0.65, 0.70, 0.75, 0.80]
MAXS = [0.90, 0.95, 0.98, 1.00]


def collect(instrument: str) -> list[tuple[float, bool]]:
    """One permissive pass. Returns (apex_proximity, qualified) for every
    structure-admitted bar (gate 1 + gate 2 pass under apex=[0,1])."""
    cfg = load_config(_CONFIG / f"{instrument}.yaml")
    # Widen apex to admit all proximities; everything else unchanged.
    perm_signals = dataclasses.replace(
        cfg.signals, apex_proximity_min=0.0, apex_proximity_max=1.0
    )
    cfg = dataclasses.replace(cfg, signals=perm_signals)
    p = cfg.signals
    h = compute_hash(cfg)
    candles = load_parquet(history_path(_HISTORY, instrument))

    records: list[tuple[float, bool]] = []
    for i in range(MIN_H1_WINDOW, len(candles)):
        win = candles[i - MIN_H1_WINDOW + 1: i + 1]
        r = evaluate(win, cfg, h)
        # Captured iff gate 2 passed (qualified, or rejected at gate >= 3).
        if r.rejected_at_gate is not None and r.rejected_at_gate < 3:
            continue
        # Re-extract apex proximity for this window (cheap; only the rare admitted bars).
        h4 = resample_h1_to_h4(win)
        sub = h4[-p.triangle_max_candles:] if len(h4) > p.triangle_max_candles else h4
        prox = detect_triangle(sub, p).apex_proximity
        records.append((prox, r.qualified))
    return records


def main():
    print("Collecting permissive-apex passes (one per instrument)...\n")
    data: dict[str, list[tuple[float, bool]]] = {}
    for instr in _INSTRUMENTS:
        recs = collect(instr)
        data[instr] = recs
        admitted = len(recs)
        qual = sum(1 for _, q in recs if q)
        print(f"  {instr}: {admitted} structure-admitted bars (apex 0–1), "
              f"{qual} fully-qualified")
    print()

    # Header
    print("Sensitivity grid — cells show: gate2-admitted / fully-qualified (all instruments summed)")
    print("(current production threshold = min 0.75, max 0.95)\n")
    header = "  min\\max " + "".join(f"{m:>14.2f}" for m in MAXS)
    print(header)
    for lo in MINS:
        cells = []
        for hi in MAXS:
            adm = qual = 0
            for recs in data.values():
                for prox, q in recs:
                    if lo <= prox <= hi and prox > 0.0:
                        adm += 1
                        if q:
                            qual += 1
            marker = "*" if (abs(lo - 0.75) < 1e-9 and abs(hi - 0.95) < 1e-9) else " "
            cells.append(f"{adm:>6d}/{qual:<4d}{marker}  ")
        print(f"  {lo:>5.2f}  " + "".join(cells))

    # Per-instrument qualified breakdown at a few representative settings
    print("\nFully-qualified signals by instrument at representative thresholds:")
    for lo, hi in [(0.75, 0.95), (0.70, 0.98), (0.60, 1.00), (0.50, 1.00)]:
        parts = []
        for instr, recs in data.items():
            q = sum(1 for prox, qq in recs if lo <= prox <= hi and prox > 0.0 and qq)
            parts.append(f"{instr}={q}")
        print(f"  apex[{lo:.2f},{hi:.2f}]: " + "  ".join(parts))


if __name__ == "__main__":
    main()
