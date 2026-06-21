"""Golden gate-fixtures for Gate 6 — Session Active (§8.1#6 · §3.3).

Pass-path  : FX bar mid-London (10:00 UTC) → SESSION_ACTIVE
Near-miss 1: FX bar within 30 min of London open (07:15) → SESSION_EDGE
Near-miss 2: FX bar outside all bands (23:00) → SESSION_CLOSED
Overlap    : 13:15 UTC — NY just opened (edge) but London is mid-session → SESSION_ACTIVE
Crypto     : BTC any hour → SESSION_24_7 (prior build wrongly applied FX bands — §R)
News stub  : event window blocks even crypto → NEWS_BLOCKED
"""

from __future__ import annotations
from datetime import datetime, timezone, timedelta
from pathlib import Path

from lsb.config import load_strategy, load_instrument
from lsb.signal import gate6_session
from lsb.signal.types import Side

CONFIG = Path(__file__).parent.parent / "config"


def _sp():
    return load_strategy(CONFIG / "strategy.yaml")


def _fx():
    return load_instrument(CONFIG / "EURUSD.yaml")


def _btc():
    return load_instrument(CONFIG / "BTCUSD.yaml")


def _bar(hour, minute=0):
    return {"ts": datetime(2024, 3, 4, hour, minute, tzinfo=timezone.utc)}  # Mon


def test_session_fx_active():
    res = gate6_session.evaluate(_bar(10), _sp(), _fx(), Side.BEAR)
    assert res.passed and res.state == "SESSION_ACTIVE"


def test_session_fx_edge_london_open():
    res = gate6_session.evaluate(_bar(7, 15), _sp(), _fx(), Side.BEAR)
    assert not res.passed and res.state == "SESSION_EDGE"


def test_session_fx_closed():
    res = gate6_session.evaluate(_bar(23), _sp(), _fx(), Side.BEAR)
    assert not res.passed and res.state == "SESSION_CLOSED"


def test_session_overlap_ny_open_but_london_active():
    """13:15 UTC: NY just opened (within edge buffer) but London is mid-session → valid."""
    res = gate6_session.evaluate(_bar(13, 15), _sp(), _fx(), Side.BEAR)
    assert res.passed and res.state == "SESSION_ACTIVE"


def test_session_crypto_24_7():
    for hour in (0, 3, 12, 23):
        res = gate6_session.evaluate(_bar(hour), _sp(), _btc(), Side.BEAR)
        assert res.passed and res.state == "SESSION_24_7", hour


def test_session_news_blocks_crypto():
    bar = _bar(12)
    ts = bar["ts"]
    windows = [(ts - timedelta(minutes=10), ts + timedelta(minutes=10))]
    res = gate6_session.evaluate(bar, _sp(), _btc(), Side.BEAR, news_windows=windows)
    assert not res.passed and res.state == "NEWS_BLOCKED"


def test_session_naive_ts_rejected():
    res = gate6_session.evaluate({"ts": datetime(2024, 3, 4, 10)}, _sp(), _fx(), Side.BEAR)
    assert not res.passed and res.state == "NO_TZ"


def test_session_determinism():
    sp, ic = _sp(), _fx()
    r1 = gate6_session.evaluate(_bar(10), sp, ic, Side.BEAR)
    r2 = gate6_session.evaluate(_bar(10), sp, ic, Side.BEAR)
    assert r1 == r2
