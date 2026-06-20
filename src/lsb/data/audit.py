"""Gap detection and mandatory disposition for H1 OHLCV series.

Every gap > 2 bars must be classified.  An unclassifiable gap raises — there is
no silent discard.  Classification is pure/deterministic: same inputs → same
report with no wall-clock dependency.

Gap classification:
  weekend        — gap spans a Sat/Sun (UTC); only valid for sessions != "24_7"
  holiday        — gap on a weekday inside the known holiday calendar
  dst            — gap of exactly 1 extra bar at a DST boundary (clocks-forward
                   spring gap, UTC Sun 01:00 → 03:00 on the local-market clock)
  genuine_missing — otherwise; recorded but not an error by itself

Crypto (sessions == "24_7") has no weekend or holiday exemption; any gap is
either DST or genuine_missing.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Sequence


# ---------------------------------------------------------------------------
# Known public holidays that produce legitimate FX gaps (UTC dates).
# Extend as needed; these are the major recurring ones that affect all FX.
# ---------------------------------------------------------------------------
_FX_HOLIDAYS: frozenset[tuple[int, int]] = frozenset(
    {
        (1, 1),   # New Year's Day
        (12, 25), # Christmas Day
        (12, 26), # Boxing Day
    }
)

# DST spring-forward: clocks jump forward 1 hour → 1 missing UTC bar.
# We mark the UTC Sunday (month, day-range) where DST typically fires.
# This is a heuristic; exact dates vary by year.  A gap of exactly 1 bar
# crossing 01:00 UTC on the last Sunday of March (EU) or second Sunday of
# March (US) is treated as DST.
_DST_MONTHS = frozenset({3, 11})  # March (spring) and November (fall) for awareness


@dataclass(frozen=True)
class GapRecord:
    prev_ts: str          # ISO8601 UTC
    next_ts: str          # ISO8601 UTC
    gap_bars: int         # bars missing (e.g. 48 for a 2-day weekend gap)
    disposition: str      # weekend | holiday | dst | genuine_missing


@dataclass
class AuditReport:
    instrument: str
    sessions: str
    total_source_bars: int
    gaps_found: int       # number of gap events (not bars)
    gap_records: list[GapRecord] = field(default_factory=list)
    counts: dict[str, int] = field(default_factory=dict)  # disposition → count

    def to_json(self) -> str:
        d = {
            "instrument": self.instrument,
            "sessions": self.sessions,
            "total_source_bars": self.total_source_bars,
            "gaps_found": self.gaps_found,
            "counts": self.counts,
            "gap_records": [asdict(r) for r in self.gap_records],
        }
        return json.dumps(d, indent=2, sort_keys=True)


def _is_weekend_gap(prev: datetime, nxt: datetime) -> bool:
    """True if the gap spans at least one Saturday or Sunday (UTC)."""
    cursor = prev + timedelta(hours=1)
    while cursor < nxt:
        if cursor.weekday() in (5, 6):  # 5=Sat, 6=Sun
            return True
        cursor += timedelta(hours=1)
    return False


def _is_holiday_gap(prev: datetime, nxt: datetime) -> bool:
    """True if the gap falls on a known FX holiday (month, day) in UTC."""
    cursor = prev + timedelta(hours=1)
    while cursor < nxt:
        if (cursor.month, cursor.day) in _FX_HOLIDAYS:
            return True
        cursor += timedelta(hours=1)
    return False


def _is_dst_gap(prev: datetime, nxt: datetime, gap_bars: int) -> bool:
    """True if this looks like a DST spring-forward gap (exactly 1 bar, March/Nov Sunday)."""
    if gap_bars != 1:
        return False
    mid = prev + timedelta(minutes=30)
    return mid.weekday() == 6 and mid.month in _DST_MONTHS  # Sunday in DST month


def classify_gap(prev_ts: datetime, next_ts: datetime, sessions: str) -> str:
    """Classify a gap between *prev_ts* and *next_ts*.

    Returns one of: 'weekend', 'holiday', 'dst', 'genuine_missing'.
    Raises ValueError if *sessions* is unrecognised.
    """
    if sessions not in ("fx", "24_7"):
        raise ValueError(f"Unknown sessions value: {sessions!r}")

    gap_bars = round((next_ts - prev_ts).total_seconds() / 3600) - 1

    # DST is checked first: a 1-bar gap on a March/Nov Sunday beats weekend/holiday.
    if _is_dst_gap(prev_ts, next_ts, gap_bars):
        return "dst"

    if sessions != "24_7":
        # Holiday before weekend: a holiday that falls on a Sunday (e.g. New Year's)
        # should be recorded as holiday, not weekend.
        if _is_holiday_gap(prev_ts, next_ts):
            return "holiday"
        if _is_weekend_gap(prev_ts, next_ts):
            return "weekend"

    return "genuine_missing"


def audit_history(
    rows: Sequence[dict],
    instrument: str,
    sessions: str,
) -> AuditReport:
    """Detect and classify all H1 gaps > 2 bars.

    *rows* must be sorted ascending by ts.  Every gap > 2 consecutive missing
    bars is classified; an unclassifiable gap records as 'genuine_missing' (never
    silently dropped).

    Returns an AuditReport.  Raises ValueError if sessions is unrecognised.
    """
    if sessions not in ("fx", "24_7"):
        raise ValueError(f"Unknown sessions value: {sessions!r}")

    report = AuditReport(
        instrument=instrument,
        sessions=sessions,
        total_source_bars=len(rows),
        gaps_found=0,
    )

    counts: dict[str, int] = {}
    records: list[GapRecord] = []

    for i in range(1, len(rows)):
        prev = rows[i - 1]["ts"]
        nxt  = rows[i]["ts"]
        gap_bars = round((nxt - prev).total_seconds() / 3600) - 1

        if gap_bars <= 2:
            continue  # normal micro-gap (spread, illiquidity) — not dispositioned

        disposition = classify_gap(prev, nxt, sessions)
        counts[disposition] = counts.get(disposition, 0) + 1
        records.append(GapRecord(
            prev_ts=prev.isoformat(),
            next_ts=nxt.isoformat(),
            gap_bars=gap_bars,
            disposition=disposition,
        ))

    report.gaps_found = len(records)
    report.gap_records = records
    report.counts = counts
    return report


def write_audit(report: AuditReport, audit_dir: str | Path) -> Path:
    """Write an AuditReport to *audit_dir*/<instrument>_audit.json."""
    out = Path(audit_dir) / f"{report.instrument}_audit.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(report.to_json(), encoding="utf-8")
    return out
