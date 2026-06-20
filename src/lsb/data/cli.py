"""CLI entry point: fetch → audit → load for a single instrument.

Usage:
    python -m lsb.data.cli fetch-audit-load \
        --instrument GBPUSD \
        --years 3 \
        [--config-dir config/] \
        [--cache-dir data/raw/] \
        [--audit-dir audit/] \
        [--db-url postgresql://lsb@localhost/lsb_dev]

The --db-url flag is optional; omit it to run fetch+audit+dry-run-load
(counts are printed but no DB writes occur).  This allows CI to verify
reconciliation without a live database.
"""

from __future__ import annotations

import argparse
import sys
from datetime import date, timedelta
from pathlib import Path


def _default_path(relative: str) -> Path:
    """Resolve *relative* against the repo root (3 levels up from this file)."""
    return Path(__file__).parents[3] / relative


def cmd_fetch_audit_load(args: argparse.Namespace) -> int:
    from lsb.config import load_instrument, config_hash
    from lsb.data.fetch import fetch_history
    from lsb.data.resample import resample_h1
    from lsb.data.audit import audit_history, write_audit
    from lsb.data.load import load_candles

    config_dir = Path(args.config_dir)
    cache_root = Path(args.cache_dir)
    audit_dir  = Path(args.audit_dir)
    audit_dir.mkdir(parents=True, exist_ok=True)

    cfg = load_instrument(config_dir / f"{args.instrument}.yaml")
    cfg_hash = config_hash(cfg)

    end   = date.today()
    start = date(end.year - args.years, end.month, end.day)

    # ------ fetch -------------------------------------------------------
    series = fetch_history(cfg.instrument, cfg.data_source, start, end, cache_root,
                           progress=True)
    source_count = len(series.rows)
    print(f"[fetch ] {cfg.instrument}  {cfg.data_source}  H1  "
          f"{start} → {end}  {source_count} bars")

    # ------ resample ----------------------------------------------------
    h4_rows = resample_h1(series.rows, "H4")
    d1_rows = resample_h1(series.rows, "D1")
    print(f"[resamp] {cfg.instrument}  H1→H4 {len(h4_rows)} bars  H1→D1 {len(d1_rows)} bars")

    # ------ audit -------------------------------------------------------
    report = audit_history(series.rows, cfg.instrument, cfg.sessions)
    audit_path = write_audit(report, audit_dir)
    disp_summary = "  ".join(f"{k} {v}" for k, v in sorted(report.counts.items()))
    print(f"[audit ] {cfg.instrument}  gaps>2: {report.gaps_found}  →  {disp_summary or 'none'}")
    print(f"[audit ] wrote {audit_path}")

    # ------ reconcile ---------------------------------------------------
    audited_count = report.total_source_bars
    if audited_count != source_count:
        print(f"[ERROR ] count mismatch: source={source_count}  audited={audited_count}",
              file=sys.stderr)
        return 1
    print(f"[reconcile] source={source_count}  audited={audited_count}  ✓")

    # ------ load --------------------------------------------------------
    if args.db_url:
        import psycopg2
        conn = psycopg2.connect(args.db_url)
        cur = conn.cursor()
        try:
            n_h1 = load_candles(cur, cfg_hash, cfg.instrument, "H1", series.rows)
            n_h4 = load_candles(cur, cfg_hash, cfg.instrument, "H4", h4_rows)
            n_d1 = load_candles(cur, cfg_hash, cfg.instrument, "D1", d1_rows)
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cur.close()
            conn.close()
        print(f"[load  ] {cfg.instrument}  H1 {n_h1} · H4 {n_h4} · D1 {n_d1}  inserted")
    else:
        print(f"[load  ] dry-run (no --db-url)  H1 {source_count} · H4 {len(h4_rows)} · D1 {len(d1_rows)}")

    print(f"DONE  {cfg.instrument}  source={source_count}  audited={audited_count}  ✓")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m lsb.data.cli")
    sub = parser.add_subparsers(dest="command")

    p = sub.add_parser("fetch-audit-load", help="Fetch, audit, and load one instrument")
    p.add_argument("--instrument", required=True)
    p.add_argument("--years", type=int, default=3)
    p.add_argument("--config-dir", default=str(_default_path("config")))
    p.add_argument("--cache-dir",  default=str(_default_path("data/raw")))
    p.add_argument("--audit-dir",  default=str(_default_path("audit")))
    p.add_argument("--db-url", default=None, help="psycopg2 DSN; omit for dry-run")

    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help()
        return 1
    return cmd_fetch_audit_load(args)


if __name__ == "__main__":
    sys.exit(main())
