"""Session classifier — pure UTC-band derivation, no clock reads.

Standard FX windows (UTC):
  ASIA    22:00 – 07:00  (wraps midnight)
  LONDON  07:00 – 12:00  (London-only; before NY opens)
  OVERLAP 12:00 – 16:00  (London + NY both open)
  NY      16:00 – 21:00  (NY-only; after London closes)
  OFF     21:00 – 22:00  (gap between NY close and Asia open)

Spec: LSB_System_Requirements_v2.0.md §8 cond 6.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum, auto


class Session(Enum):
    ASIA    = auto()
    LONDON  = auto()
    OVERLAP = auto()
    NY      = auto()
    OFF     = auto()


# (start_min, end_min) in minutes-since-midnight UTC — half-open [start, end).
# ASIA wraps midnight and is handled specially.
_WINDOWS: dict[Session, tuple[int, int]] = {
    Session.ASIA:    (22 * 60, 7 * 60),
    Session.LONDON:  (7 * 60, 12 * 60),
    Session.OVERLAP: (12 * 60, 16 * 60),
    Session.NY:      (16 * 60, 21 * 60),
    Session.OFF:     (21 * 60, 22 * 60),
}


def session_of(ts: datetime) -> Session:
    """Classify a UTC timestamp into an FX trading session."""
    h = ts.hour
    if 12 <= h < 16:
        return Session.OVERLAP
    if 7 <= h < 12:
        return Session.LONDON
    if 16 <= h < 21:
        return Session.NY
    if h >= 22 or h < 7:
        return Session.ASIA
    return Session.OFF   # h == 21


def minutes_to_edge(ts: datetime) -> int:
    """Minutes to the nearest boundary of the current session (open or close).

    Returns 0 for OFF session (no valid trading window).
    Assumes ts is UTC.
    """
    s = session_of(ts)
    if s == Session.OFF:
        return 0

    total = ts.hour * 60 + ts.minute
    start, end = _WINDOWS[s]

    if s == Session.ASIA:
        if total >= start:
            since = total - start
            to_end = 24 * 60 - total + end
        else:  # past midnight, before 07:00
            since = 24 * 60 - start + total
            to_end = end - total
    else:
        since = total - start
        to_end = end - total

    return min(since, to_end)
