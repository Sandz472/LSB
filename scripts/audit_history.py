"""Audit fetched H1 OHLCV data and (optionally) load it into the candle table.

Reads data/history/<INSTRUMENT>_H1.parquet (written by fetch_history.py), runs
a fixed set of data-quality checks, and writes/updates
docs/data_audit_report_<INSTRUMENT>.md with an Anomalies table.

`gap>2` anomalies (gaps larger than 2x the candle interval that aren't an
expected FX weekend closure) require a written disposition in the report's
`## Dispositions` section before `--load` is allowed to proceed. Other
anomaly types (duplicates, weekend bars, DST artifacts, spread outliers) are
informational only.

Usage:
    python scripts/audit_history.py --instrument {EURUSD,XAUUSD,BTCUSD,all} [--load]
"""

import argparse
import json
import re
import sys
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path

import pandas as pd
from psycopg2.extras import execute_values

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lsb.data.config import InstrumentConfig, get_or_create_config_version, load_config  # noqa: E402
from lsb.data.db import apply_migrations, get_connection  # noqa: E402

HISTORY_DIR = ROOT / "data" / "history"
CONFIG_DIR = ROOT / "config"
DOCS_DIR = ROOT / "docs"

DISPOSITION_HEADER = "## Dispositions"
DISPOSITION_PLACEHOLDER = (
    "\n<!-- For every `gap>2` anomaly above, add a line of the form:\n"
    '- GAP-0001: <reason, e.g. "Christmas/New Year close — expected">\n'
    "-->\n"
)


@dataclass
class Anomaly:
    id: str
    check: str
    ts: str
    description: str
    requires_disposition: bool = False


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------

def check_duplicate_timestamps(df: pd.DataFrame) -> list[Anomaly]:
    dup_ts = sorted(df.loc[df["ts"].duplicated(keep=False), "ts"].unique())
    anomalies = []
    for seq, ts in enumerate(dup_ts, start=1):
        count = int((df["ts"] == ts).sum())
        anomalies.append(
            Anomaly(f"DUP-{seq:04d}", "duplicate_timestamp", str(ts), f"{count} rows share timestamp {ts}")
        )
    return anomalies


def _is_expected_fx_closure(prev_ts: pd.Timestamp, ts: pd.Timestamp) -> bool:
    """True if [prev_ts, ts) spans the regular FX weekend closure
    (market closes ~Fri 21:00 UTC, reopens ~Sun 21:00-22:00 UTC)."""
    return prev_ts.weekday() == 4 and prev_ts.hour >= 20 and ts.weekday() in (6, 0)


def check_gaps(df: pd.DataFrame, asset_class: str, timeframe_hours: int = 1) -> list[Anomaly]:
    df = df.sort_values("ts").reset_index(drop=True)
    anomalies = []
    seq = 0
    for i in range(1, len(df)):
        prev_ts, ts = df["ts"].iloc[i - 1], df["ts"].iloc[i]
        gap_hours = (ts - prev_ts).total_seconds() / 3600
        if gap_hours <= 2 * timeframe_hours:
            continue
        if asset_class == "fx" and _is_expected_fx_closure(prev_ts, ts):
            continue
        seq += 1
        anomalies.append(
            Anomaly(
                f"GAP-{seq:04d}",
                "gap>2",
                f"{prev_ts} -> {ts}",
                f"gap of {gap_hours:.1f}h ({gap_hours / timeframe_hours:.0f} candles)",
                requires_disposition=True,
            )
        )
    return anomalies


def check_weekend_bars(df: pd.DataFrame, asset_class: str) -> list[Anomaly]:
    """Flag candles that fall within the FX market's regular weekend closure."""
    if asset_class != "fx":
        return []
    anomalies = []
    seq = 0
    for ts in df["ts"]:
        wd = ts.weekday()
        in_closure = wd == 5 or (wd == 6 and ts.hour < 21) or (wd == 4 and ts.hour >= 21)
        if in_closure:
            seq += 1
            anomalies.append(
                Anomaly(f"WKND-{seq:04d}", "weekend_bar", str(ts), f"candle at {ts} falls within FX weekend closure")
            )
    return anomalies


def _dst_transition_dates(year: int) -> tuple:
    """Last Sunday of March and October (EU DST convention)."""
    march_sundays = [d for d in range(25, 32) if date(year, 3, d).weekday() == 6]
    october_sundays = [d for d in range(25, 32) if date(year, 10, d).weekday() == 6]
    return date(year, 3, march_sundays[0]), date(year, 10, october_sundays[0])


def check_dst_anomalies(df: pd.DataFrame, asset_class: str) -> list[Anomaly]:
    """Flag mid-week days with 23 or 25 H1 candles within 2 days of a DST
    transition (clock-shift artifact).

    Mon/Fri are excluded since the FX weekly open/close already gives them a
    naturally shorter count. Days far from any transition with 23/25 candles
    are a recurring market-structure feature (e.g. a daily settlement gap),
    not a DST artifact, and are left to check_gaps."""
    if asset_class != "fx":
        return []
    anomalies = []
    seq = 0
    counts = df.groupby(df["ts"].dt.date).size()
    for day, count in counts.items():
        ts_day = pd.Timestamp(day)
        if ts_day.weekday() not in (1, 2, 3) or count not in (23, 25):
            continue
        transitions = _dst_transition_dates(ts_day.year)
        if any(abs((ts_day.date() - t).days) <= 2 for t in transitions):
            seq += 1
            anomalies.append(
                Anomaly(f"DST-{seq:04d}", "dst_anomaly", str(day), f"{day} has {count} H1 candles (expected 24)")
            )
    return anomalies


def check_spread_outliers(df: pd.DataFrame) -> list[Anomaly]:
    """IQR-based outlier check on the `spread` column. No-op if spread is absent/all-null."""
    spreads = df["spread"].dropna()
    if len(spreads) < 4:
        return []
    q1, q3 = spreads.quantile([0.25, 0.75])
    iqr = q3 - q1
    lower, upper = q1 - 3 * iqr, q3 + 3 * iqr
    outliers = df[df["spread"].notna() & ((df["spread"] < lower) | (df["spread"] > upper))]
    anomalies = []
    for seq, (_, row) in enumerate(outliers.iterrows(), start=1):
        anomalies.append(
            Anomaly(
                f"SPRD-{seq:04d}",
                "spread_outlier",
                str(row["ts"]),
                f"spread {row['spread']} outside [{lower:.4f}, {upper:.4f}]",
            )
        )
    return anomalies


CHECKS = [
    check_duplicate_timestamps,
    check_gaps,
    check_weekend_bars,
    check_dst_anomalies,
    check_spread_outliers,
]


def run_audit(df: pd.DataFrame, config: InstrumentConfig) -> list[Anomaly]:
    anomalies: list[Anomaly] = []
    anomalies += check_duplicate_timestamps(df)
    anomalies += check_gaps(df, config.asset_class)
    anomalies += check_weekend_bars(df, config.asset_class)
    anomalies += check_dst_anomalies(df, config.asset_class)
    anomalies += check_spread_outliers(df)
    return anomalies


# ---------------------------------------------------------------------------
# Report read/write
# ---------------------------------------------------------------------------

def _existing_dispositions_tail(path: Path) -> str:
    if not path.exists():
        return DISPOSITION_PLACEHOLDER
    text = path.read_text(encoding="utf-8")
    idx = text.find(DISPOSITION_HEADER)
    if idx == -1:
        return DISPOSITION_PLACEHOLDER
    return text[idx + len(DISPOSITION_HEADER):]


def write_report(path: Path, instrument: str, meta: dict, df: pd.DataFrame, anomalies: list[Anomaly]) -> None:
    tail = _existing_dispositions_tail(path)
    lines = [
        f"# Data Audit Report — {instrument}",
        "",
        f"- Generated: {datetime.now(timezone.utc).isoformat()}",
        f"- Source: {meta.get('source', 'unknown')}",
        f"- Fetched at: {meta.get('fetched_at', 'unknown')}",
        f"- Range: {df['ts'].min()} .. {df['ts'].max()}",
        f"- Rows: {len(df)}",
        "",
    ]
    requested_start = meta.get("requested_start")
    if requested_start and str(df["ts"].min().date()) > requested_start:
        lines += [
            f"**Coverage note:** requested data from {requested_start}, but the earliest "
            f"candle returned is {df['ts'].min()} — the source has no earlier history "
            "for this instrument.",
            "",
        ]
    lines += [
        "## Anomalies",
        "",
    ]
    if anomalies:
        lines += ["| ID | Check | Timestamp | Description |", "|---|---|---|---|"]
        for a in anomalies:
            lines.append(f"| {a.id} | {a.check} | {a.ts} | {a.description} |")
    else:
        lines.append("None.")
    lines.append("")
    lines.append(DISPOSITION_HEADER)
    path.write_text("\n".join(lines) + tail, encoding="utf-8")


def parse_dispositions(path: Path) -> set[str]:
    if not path.exists():
        return set()
    text = path.read_text(encoding="utf-8")
    idx = text.find(DISPOSITION_HEADER)
    if idx == -1:
        return set()
    return set(re.findall(r"\b([A-Z]+-\d{4})\b", text[idx + len(DISPOSITION_HEADER):]))


# ---------------------------------------------------------------------------
# Load
# ---------------------------------------------------------------------------

def load_candles(conn, instrument: str, timeframe: str, df: pd.DataFrame) -> int:
    records = [
        (instrument, timeframe, row.ts.to_pydatetime(), row.open, row.high, row.low, row.close, row.volume, row.spread)
        for row in df.itertuples(index=False)
    ]
    with conn.cursor() as cur:
        execute_values(
            cur,
            """
            INSERT INTO candle (instrument, timeframe, ts, open, high, low, close, volume, spread)
            VALUES %s
            ON CONFLICT (instrument, timeframe, ts)
            DO UPDATE SET open = EXCLUDED.open, high = EXCLUDED.high, low = EXCLUDED.low,
                           close = EXCLUDED.close, volume = EXCLUDED.volume, spread = EXCLUDED.spread
            """,
            records,
        )
    conn.commit()
    return len(records)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def audit_instrument(instrument: str, do_load: bool) -> bool:
    """Returns True on success, False if --load was requested but blocked."""
    config = load_config(CONFIG_DIR / f"{instrument}.yaml")
    parquet_path = HISTORY_DIR / f"{instrument}_H1.parquet"
    if not parquet_path.exists():
        print(f"{instrument}: no {parquet_path} — run fetch_history.py first")
        return False

    df = pd.read_parquet(parquet_path)
    meta_path = HISTORY_DIR / f"{instrument}_H1.meta.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {}

    anomalies = run_audit(df, config)
    report_path = DOCS_DIR / f"data_audit_report_{instrument}.md"
    write_report(report_path, instrument, meta, df, anomalies)
    print(f"{instrument}: {len(df)} rows, {len(anomalies)} anomalies -> {report_path}")

    if not do_load:
        return True

    required = {a.id for a in anomalies if a.requires_disposition}
    disposed = parse_dispositions(report_path)
    missing = sorted(required - disposed)
    if missing:
        print(f"{instrument}: missing dispositions for {missing} in {report_path}; load aborted")
        return False

    conn = get_connection()
    apply_migrations(conn)
    config_hash = get_or_create_config_version(conn, config)
    n = load_candles(conn, instrument, "H1", df)
    print(f"{instrument}: loaded/updated {n} candle rows (config_hash={config_hash[:8]}...)")
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--instrument", required=True, choices=["EURUSD", "XAUUSD", "BTCUSD", "all"])
    parser.add_argument("--load", action="store_true")
    args = parser.parse_args()

    instruments = ["EURUSD", "XAUUSD", "BTCUSD"] if args.instrument == "all" else [args.instrument]
    ok = True
    for instrument in instruments:
        if not audit_instrument(instrument, args.load):
            ok = False
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
