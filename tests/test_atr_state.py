"""ATR-state classifier reference tests (§4.2.2 / §15.1 — ADR-011).

Two layers:
  - state_for_ratio: the pure threshold rule, hand-verified at and around each
    boundary (0.75 / 1.25 / 2.0).
  - classify: ratio = current ATR(14) / 20-bar SMA-of-ATR baseline, on
    constructed candle series with a hand-computed expected regime.
"""

from __future__ import annotations
from decimal import Decimal as D
from datetime import datetime, timezone, timedelta
from pathlib import Path

from lsb.config import load_strategy
from lsb.signal import atr_state
from lsb.signal.indicators import atr
from lsb.signal.types import AtrState

CONFIG = Path(__file__).parent.parent / "config"


def _sp():
    return load_strategy(CONFIG / "strategy.yaml")


# ---------------------------------------------------------------------------
# Pinned thresholds are exactly the §4.2.2 / §15.1 values
# ---------------------------------------------------------------------------

def test_pinned_thresholds():
    sp = _sp()
    assert sp.atr_period == 14
    assert sp.atr_baseline_window == 20
    assert sp.atr_compressed_mult == D("0.75")
    assert sp.atr_elevated_mult == D("1.25")
    assert sp.atr_extreme_mult == D("2.0")


# ---------------------------------------------------------------------------
# state_for_ratio — hand-verified boundary behaviour
# ---------------------------------------------------------------------------

def test_state_for_ratio_bands():
    sp = _sp()
    f = atr_state.state_for_ratio
    assert f(D("0.50"), sp) is AtrState.COMPRESSED
    assert f(D("0.74"), sp) is AtrState.COMPRESSED
    assert f(D("0.75"), sp) is AtrState.NORMAL      # boundary → NORMAL (not compressed)
    assert f(D("1.00"), sp) is AtrState.NORMAL
    assert f(D("1.24"), sp) is AtrState.NORMAL
    assert f(D("1.25"), sp) is AtrState.ELEVATED    # boundary → ELEVATED
    assert f(D("1.99"), sp) is AtrState.ELEVATED
    assert f(D("2.00"), sp) is AtrState.EXTREME     # boundary → EXTREME
    assert f(D("5.00"), sp) is AtrState.EXTREME


# ---------------------------------------------------------------------------
# classify — on constructed series
# ---------------------------------------------------------------------------

def _series(ranges: list[str]) -> list[dict]:
    """Build candles with given high-low ranges, centred on 1.3000 (close flat).

    Flat closes → TR ≈ the bar range, so ATR(14) tracks the range directly,
    which makes the current/baseline ratio easy to reason about.
    """
    base = datetime(2024, 3, 1, tzinfo=timezone.utc)
    out = []
    for i, r in enumerate(ranges):
        half = D(r) / 2
        out.append({"ts": base + timedelta(hours=i),
                    "open": D("1.3000"), "high": D("1.3000") + half,
                    "low": D("1.3000") - half, "close": D("1.3000"),
                    "volume": D("500")})
    return out


def test_classify_constant_is_normal():
    """Constant range → current ATR == baseline → ratio 1.0 → NORMAL."""
    c = _series(["0.0010"] * 60)
    assert atr_state.classify(c, _sp()) is AtrState.NORMAL


def test_classify_insufficient_history_defaults_normal():
    c = _series(["0.0010"] * 10)              # < atr_period + window + 1
    assert atr_state.classify(c, _sp()) is AtrState.NORMAL


def test_classify_sustained_spike_is_extreme():
    """Calm baseline, volatility spike concentrated in the last few bars → EXTREME.

    60 calm bars (10-pip range) seat ATR≈baseline≈10 pips; a 5-bar 1000-pip-range
    burst lifts current ATR far above 2× the (still-calm) 20-bar baseline.  The
    burst is kept short so it does not contaminate the baseline window."""
    c = _series(["0.0010"] * 60 + ["0.1000"] * 5)
    sp = _sp()
    state = atr_state.classify(c, sp)
    # sanity: the realised ratio truly clears the EXTREME multiple (≈ 7.4×)
    series = atr(c, sp.atr_period)
    baseline = sum(series[-1 - sp.atr_baseline_window:-1], D("0")) / D(str(sp.atr_baseline_window))
    assert series[-1] / baseline >= sp.atr_extreme_mult
    assert state is AtrState.EXTREME


def test_classify_compressed():
    """Volatile baseline then a calm tail → current ATR < 0.75× baseline → COMPRESSED."""
    c = _series(["0.1000"] * 60 + ["0.0010"] * 10)
    sp = _sp()
    state = atr_state.classify(c, sp)
    series = atr(c, sp.atr_period)
    baseline = sum(series[-1 - sp.atr_baseline_window:-1], D("0")) / D(str(sp.atr_baseline_window))
    assert series[-1] / baseline < sp.atr_compressed_mult     # ≈ 0.56×
    assert state is AtrState.COMPRESSED


def test_classify_determinism():
    c = _series(["0.0010"] * 30 + ["0.0030"] * 30)
    sp = _sp()
    assert atr_state.classify(c, sp) == atr_state.classify(c, sp)
