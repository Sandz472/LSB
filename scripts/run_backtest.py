"""CLI entry point for the Phase A backtest engine.

Usage:
    python scripts/run_backtest.py EURUSD
    python scripts/run_backtest.py EURUSD --db          # persist signals to DB
    python scripts/run_backtest.py EURUSD --from 2024-01-01 --to 2024-06-30
    python scripts/run_backtest.py --all                # run all three instruments
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from lsb.data.config import load_config, config_hash as compute_hash
from lsb.backtest.data import load_parquet, history_path
from lsb.backtest.loop import run_backtest
from lsb.backtest.sink import DbSink, NullSink

_CONFIG_DIR = ROOT / "config"
_DATA_DIR = ROOT / "data" / "history"
_INSTRUMENTS = ["EURUSD", "XAUUSD", "BTCUSD"]


def _parse_args():
    p = argparse.ArgumentParser(description="LSB Strategy Bot — Phase A backtest")
    p.add_argument("instrument", nargs="?", choices=_INSTRUMENTS, help="Instrument to run")
    p.add_argument("--all", action="store_true", help="Run all instruments")
    p.add_argument("--db", action="store_true", help="Persist qualified signals to DB")
    p.add_argument("--from", dest="from_date", metavar="YYYY-MM-DD",
                   help="Start date (inclusive, UTC)")
    p.add_argument("--to", dest="to_date", metavar="YYYY-MM-DD",
                   help="End date (inclusive, UTC)")
    return p.parse_args()


def _run_instrument(instr: str, args) -> None:
    cfg = load_config(_CONFIG_DIR / f"{instr}.yaml")
    h = compute_hash(cfg)
    candles = load_parquet(history_path(_DATA_DIR, instr))

    if args.from_date or args.to_date:
        import pandas as pd
        from_ts = pd.Timestamp(args.from_date, tz="UTC") if args.from_date else None
        to_ts = pd.Timestamp(args.to_date, tz="UTC") if args.to_date else None
        if from_ts:
            candles = [c for c in candles if c.ts >= from_ts]
        if to_ts:
            candles = [c for c in candles if c.ts <= to_ts]

    print(f"\n[{instr}] {len(candles):,} candles | config_hash={h[:12]}...")

    if args.db:
        from lsb.data.db import apply_migrations, get_connection
        conn = get_connection()
        apply_migrations(conn)
        sink = DbSink(conn)
    else:
        sink = NullSink()

    book, sink = run_backtest(candles, cfg, h, sink=sink)

    closed = book.closed_legs()
    active = book.active_legs()
    n_signals = len(sink.results) if hasattr(sink, "results") else "N/A (DbSink)"
    n_qualified = (
        len(sink.qualified()) if hasattr(sink, "qualified") else "N/A (DbSink)"
    )

    print(f"  Signal rows : {n_signals}")
    print(f"  Qualified   : {n_qualified}")
    print(f"  Closed legs : {len(closed)}")
    print(f"  Active legs : {len(active)}")

    if closed:
        r_values = [l.r_at_close for l in closed if l.r_at_close is not None]
        if r_values:
            wins = sum(1 for r in r_values if r > 0)
            avg_r = sum(r_values) / len(r_values)
            print(f"  Win rate    : {wins}/{len(r_values)} "
                  f"({100*wins/len(r_values):.1f}%)")
            print(f"  Avg R       : {avg_r:.2f}")

    if args.db:
        conn.close()


def main():
    args = _parse_args()

    if not args.instrument and not args.all:
        print("Specify an instrument (e.g. EURUSD) or --all")
        sys.exit(1)

    instruments = _INSTRUMENTS if args.all else [args.instrument]
    for instr in instruments:
        _run_instrument(instr, args)

    print("\nDone.")


if __name__ == "__main__":
    main()
