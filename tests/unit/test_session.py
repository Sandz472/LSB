"""Session classifier unit tests — hand-labeled UTC boundary cases."""

from datetime import datetime, timezone

import pytest

from lsb.signals.session import Session, minutes_to_edge, session_of


def _ts(h: int, m: int = 0) -> datetime:
    return datetime(2024, 1, 15, h, m, tzinfo=timezone.utc)


# ---------------------------------------------------------------------------
# session_of — classification
# ---------------------------------------------------------------------------

class TestSessionOf:
    def test_london_open(self):
        assert session_of(_ts(7)) == Session.LONDON

    def test_london_mid(self):
        assert session_of(_ts(10, 30)) == Session.LONDON

    def test_london_last_minute(self):
        assert session_of(_ts(11, 59)) == Session.LONDON

    def test_overlap_start(self):
        assert session_of(_ts(12)) == Session.OVERLAP

    def test_overlap_mid(self):
        assert session_of(_ts(14)) == Session.OVERLAP

    def test_overlap_last_minute(self):
        assert session_of(_ts(15, 59)) == Session.OVERLAP

    def test_ny_open(self):
        assert session_of(_ts(16)) == Session.NY

    def test_ny_mid(self):
        assert session_of(_ts(18)) == Session.NY

    def test_ny_last_minute(self):
        assert session_of(_ts(20, 59)) == Session.NY

    def test_off(self):
        assert session_of(_ts(21)) == Session.OFF
        assert session_of(_ts(21, 45)) == Session.OFF

    def test_asia_post_midnight(self):
        assert session_of(_ts(22)) == Session.ASIA
        assert session_of(_ts(23)) == Session.ASIA

    def test_asia_before_midnight_wraps(self):
        assert session_of(_ts(0)) == Session.ASIA
        assert session_of(_ts(3, 30)) == Session.ASIA

    def test_asia_last_minute(self):
        assert session_of(_ts(6, 59)) == Session.ASIA


# ---------------------------------------------------------------------------
# minutes_to_edge — distance to nearest session boundary
# ---------------------------------------------------------------------------

class TestMinutesToEdge:
    def test_off_returns_zero(self):
        assert minutes_to_edge(_ts(21)) == 0
        assert minutes_to_edge(_ts(21, 30)) == 0

    def test_london_open_boundary(self):
        # 07:00 is the London open → 0 min from start
        assert minutes_to_edge(_ts(7, 0)) == 0

    def test_london_just_inside_open(self):
        # 07:05 → 5 min from open, 355 min to 12:00 → min = 5
        assert minutes_to_edge(_ts(7, 5)) == 5

    def test_london_mid(self):
        # 09:30 → 150 min from 07:00, 150 min to 12:00 → min = 150
        assert minutes_to_edge(_ts(9, 30)) == 150

    def test_london_near_close(self):
        # 11:40 → 100 min from 07:00, 20 min to 12:00 → min = 20
        assert minutes_to_edge(_ts(11, 40)) == 20

    def test_overlap_mid(self):
        # 14:00 → 120 min from 12:00, 120 min to 16:00 → min = 120
        assert minutes_to_edge(_ts(14, 0)) == 120

    def test_ny_just_inside_close(self):
        # 20:45 → 285 min from 16:00, 15 min to 21:00 → min = 15
        assert minutes_to_edge(_ts(20, 45)) == 15

    def test_asia_after_midnight_start_boundary(self):
        # 22:00 → 0 min from 22:00 start
        assert minutes_to_edge(_ts(22, 0)) == 0

    def test_asia_after_midnight_just_inside(self):
        # 22:10 → 10 min since 22:00; to end = (24-22)*60 + 7*60 = 120+420 = 540 → min = 10
        assert minutes_to_edge(_ts(22, 10)) == 10

    def test_asia_before_07_near_close(self):
        # 06:45 → since start = (24-22)*60 + 6*60+45 = 525; to end = 7*60 - (6*60+45) = 15
        assert minutes_to_edge(_ts(6, 45)) == 15
