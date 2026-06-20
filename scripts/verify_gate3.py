"""Verify Gate 3 + Gate 1 fixes: run the real engine.evaluate() over all history
with the daily macro trend (ADR-007 production path) and report per-gate
rejection counts + qualified signals per instrument.

Usage:  python scripts/verify_gate3.py
"""

from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from lsb.data.config import load_config, config_hash as compute_hash
from lsb.backtest.data import load_parquet, history_path
from lsb.signals.engine import evaluate, MIN_H1_WINDOW
from lsb.signals.resample import resample_h1_to_daily
from lsb.signals.trend import TrendState, trend_state

_CONFIG = ROOT / "config"
_HISTORY = ROOT / "data" / "history"
_INSTRUMENTS = ["EURUSD", "XAUUSD", "BTCUSD"]


def analyze(instrument: str) -> None:
    cfg = load_config(_CONFIG / f"{instrument}.yaml")
    h = compute_hash(cfg)
    p = cfg.signals
    candles = load_parquet(history_path(_HISTORY, instrument))

    # Precompute the daily series once; map each H1 bar to the last complete
    # daily bar at or before it (no look-ahead — batch resample drops the
    # trailing incomplete day, and we slice daily[:k] by H1 index).
    daily_all = resample_h1_to_daily(candles)
    min_daily = p.ema_long_period + 1

    reject = Counter()
    qualified = 0
    gate3_pass = 0
    n = 0
    g3_details = []
    g3_shown = 0
    daily_idx = -1  # pointer into daily_all; -1 = no complete daily bar yet
    cached_daily_trend = None

    for i in range(MIN_H1_WINDOW, len(candles)):
        win = candles[i - MIN_H1_WINDOW + 1: i + 1]
        n += 1
        # Advance daily pointer to the last complete daily bar ending <= candles[i].
        cur_ts = candles[i].ts
        while (daily_idx + 1 < len(daily_all)
               and daily_all[daily_idx + 1].ts <= cur_ts):
            daily_idx += 1
            # Recompute trend only when a new daily bar closes.
            if daily_idx + 1 >= min_daily:
                cached_daily_trend = trend_state(daily_all[: daily_idx + 1], p)
            else:
                cached_daily_trend = None
        daily_trend = cached_daily_trend
        result = evaluate(win, cfg, h, daily_trend=daily_trend)
        if result.qualified:
            qualified += 1
        else:
            reject[result.rejected_at_gate] += 1
        if result.rejected_at_gate is None or result.rejected_at_gate >= 4:
            gate3_pass += 1

        if result.rejected_at_gate == 3 and g3_shown < 8:
            g3 = result.gates[2]
            last = win[-1]
            g3_details.append(
                f"    ts={last.ts} dir={result.direction} "
                f"daily={daily_trend.name if daily_trend else 'None'} "
                f"g3_reason='{g3.reason}'"
            )
            g3_shown += 1

    print(f"\n=== {instrument} === ({n} bars evaluated)")
    print(f"  qualified (all 8 gates): {qualified}")
    print(f"  gate 3 passed: {gate3_pass}")
    print("  rejection by gate:")
    for g in range(1, 9):
        print(f"    gate {g}: {reject.get(g, 0)}")
    if g3_details:
        print("  gate-3 rejection details (sample):")
        for ln in g3_details:
            print(ln)


def main():
    for instr in _INSTRUMENTS:
        analyze(instr)


if __name__ == "__main__":
    main()



def main():
    for instr in _INSTRUMENTS:
        analyze(instr)


if __name__ == "__main__":
    main()
