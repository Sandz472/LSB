"""Golden gate-fixtures for Gate 5 — Rejection Candle Confirmed (§8.1#5 · §4.3 · ADR-004).

Pass-path  : bear rejection candle (upper wick ≥2×body, tiny lower wick, bearish
             close, closes below sweep high) → REJECTION_BEAR
Near-miss 1: upper wick too small (< 2×body) → NO_REJECTION
Near-miss 2: close not below the sweep high → NO_REJECTION
Engulfing  : bearish engulfing with a big upper wick → ENGULFING_BEAR
Bull mirror: lower wick ≥2×body, closes above sweep low → REJECTION_BULL (ADR-004)
"""

from __future__ import annotations
from decimal import Decimal
from datetime import datetime, timezone, timedelta
from pathlib import Path

from lsb.config import load_strategy, load_instrument
from lsb.signal import gate5_rejection
from lsb.signal.types import Side

D = Decimal
CONFIG = Path(__file__).parent.parent / "config"


def _sp():
    return load_strategy(CONFIG / "strategy.yaml")


def _ic():
    return load_instrument(CONFIG / "EURUSD.yaml")


def _bar(o, h, l, c, hour=10):
    return {"ts": datetime(2024, 3, 1, hour, tzinfo=timezone.utc),
            "open": D(o), "high": D(h), "low": D(l), "close": D(c), "volume": D("500")}


def test_gate5_bear_rejection_pass():
    """Upper wick 30 pips = 3×body, lower wick 1 pip, bearish, closes below sweep high."""
    prev = _bar("1.3000", "1.3005", "1.2995", "1.3000")
    # body = 1.3000-1.2990 = 10 pips; upper wick = 1.3030-1.3000 = 30 pips (3×) ; lower 1 pip
    rej = _bar("1.3000", "1.3030", "1.2989", "1.2990")
    res = gate5_rejection.evaluate([prev, rej], _sp(), _ic(), Side.BEAR,
                                   sweep_high=D("1.3025"))
    assert res.passed, res
    assert res.state == "REJECTION_BEAR"


def test_gate5_wick_too_small():
    prev = _bar("1.3000", "1.3005", "1.2995", "1.3000")
    # upper wick = 5 pips = 0.5×body → fails the ≥2×body requirement
    rej = _bar("1.3000", "1.3005", "1.2989", "1.2990")
    res = gate5_rejection.evaluate([prev, rej], _sp(), _ic(), Side.BEAR,
                                   sweep_high=D("1.3025"))
    assert not res.passed
    assert res.state == "NO_REJECTION"
    assert res.detail["reason"] == "dominant_wick_too_small"


def test_gate5_close_not_past_sweep():
    prev = _bar("1.3000", "1.3005", "1.2995", "1.3000")
    rej = _bar("1.3000", "1.3030", "1.2989", "1.2990")
    # sweep high BELOW the close → close is not below the sweep high
    res = gate5_rejection.evaluate([prev, rej], _sp(), _ic(), Side.BEAR,
                                   sweep_high=D("1.2980"))
    assert not res.passed
    assert res.detail["reason"] == "close_not_past_sweep"


def test_gate5_engulfing_bear_pass():
    """Bearish engulfing with a large upper wick and a NON-tiny lower wick.

    Lower wick > 0.3×body disqualifies the pure-rejection path, so this must
    pass via the engulfing branch (and still satisfies upper wick ≥2×body)."""
    prev = _bar("1.2995", "1.3001", "1.2993", "1.3000")          # small bullish body
    # body = 11 pips; upper wick 23 pips (≥2×); lower wick 10 pips (> 0.3×body)
    rej = _bar("1.3001", "1.3024", "1.2980", "1.2990")
    res = gate5_rejection.evaluate([prev, rej], _sp(), _ic(), Side.BEAR,
                                   sweep_high=D("1.3020"))
    assert res.passed, res
    assert res.state == "ENGULFING_BEAR"


def test_gate5_bull_rejection_pass():
    """ADR-004 mirror: lower wick ≥2×body, tiny upper wick, bullish, closes above sweep low."""
    prev = _bar("1.3000", "1.3005", "1.2995", "1.3000")
    # body = 1.3010-1.3000 = 10 pips; lower wick = 1.3000-1.2970 = 30 pips (3×); upper 1 pip
    rej = _bar("1.3000", "1.3011", "1.2970", "1.3010")
    res = gate5_rejection.evaluate([prev, rej], _sp(), _ic(), Side.BULL,
                                   sweep_low=D("1.2975"))
    assert res.passed, res
    assert res.state == "REJECTION_BULL"


def test_gate5_doji_no_rejection():
    prev = _bar("1.3000", "1.3005", "1.2995", "1.3000")
    rej = _bar("1.3000", "1.3030", "1.2970", "1.3000")  # body == 0
    res = gate5_rejection.evaluate([prev, rej], _sp(), _ic(), Side.BEAR,
                                   sweep_high=D("1.3025"))
    assert not res.passed
    assert res.detail["reason"] == "doji_zero_body"


def test_gate5_determinism():
    prev = _bar("1.3000", "1.3005", "1.2995", "1.3000")
    rej = _bar("1.3000", "1.3030", "1.2989", "1.2990")
    sp, ic = _sp(), _ic()
    r1 = gate5_rejection.evaluate([prev, rej], sp, ic, Side.BEAR, sweep_high=D("1.3025"))
    r2 = gate5_rejection.evaluate([prev, rej], sp, ic, Side.BEAR, sweep_high=D("1.3025"))
    assert r1 == r2
