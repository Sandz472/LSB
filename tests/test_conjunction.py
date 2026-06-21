"""A5 conjunction tests — §8.1 verbatim composition → SignalResult.

Covers:
  - a genuine all-8 QUALIFIED setup (the conjunction's TRUE path is reachable)
  - the §8.1 AND invariant + verdict mapping (QUALIFIED / REJECTED / INVALIDATED)
  - Gate-3-dependent gates recorded DEP_UNMET when no sweep (row still complete)
  - sweep score is None when no block/sweep; risk tier SKIP
  - determinism and a shuffled-history property test (no order leak)
"""

from __future__ import annotations
from decimal import Decimal as D
from datetime import datetime, timezone, timedelta

from lsb.config import load_strategy, load_instrument
from lsb.signal import conjunction, atr_state
from lsb.signal.types import Side, Verdict, RiskTier, AtrState

from test_gate1_trend import _d1_candles, _bear_closes, _bull_closes
from test_gate2_structure import _build_triangle

from pathlib import Path
CONFIG = Path(__file__).parent.parent / "config"


def _sp():
    return load_strategy(CONFIG / "strategy.yaml")


def _ic():
    return load_instrument(CONFIG / "EURUSD.yaml")


_BASE = datetime(2024, 3, 4, tzinfo=timezone.utc)


def _bar(i, o, h, l, c):
    return {"ts": _BASE + timedelta(hours=i), "open": D(str(o)), "high": D(str(h)),
            "low": D(str(l)), "close": D(str(c)), "volume": D("500")}


def build_qualified_h1(B="1.2830") -> list[dict]:
    """H1 series whose LAST bar is a confirmed BEAR rejection on a swept block.

    50-bar declining leg seats EMA21 just above the block; the block (two swing
    highs at the tail) is swept 2 pips above its high on bar 59; bar 60 is a small
    rejection candle.  Gate 4 is satisfied via the SWEEP bar (its high sits within
    3 pips of EMA21) — which frees the rejection candle to keep risk small so Gate
    7 clears 2.5R.  Verified all-8 green (see test_conjunction_qualified)."""
    B = D(B)
    cl = []
    price, step = D("1.3200"), D("0.0008")
    L = 50
    for i in range(L):
        c = price - step * i
        cl.append(_bar(i, c, c + D("0.0003"), c - D("0.0003"), c))
    flat = B - D("0.0050")
    sweep_high = B + D("0.0002")

    def f(i):
        return _bar(i, flat, flat + D("0.0003"), flat - D("0.0003"), flat)

    tail = [
        f(L + 0), f(L + 1),
        _bar(L + 2, B - D("0.0005"), B - D("0.0002"), B - D("0.0010"), B - D("0.0005")),  # swing high 1
        f(L + 3), f(L + 4), f(L + 5),
        _bar(L + 6, B - D("0.0005"), B, B - D("0.0010"), B - D("0.0004")),                # swing high 2 (block high)
        f(L + 7), f(L + 8),
        _bar(L + 9, B - D("0.0010"), sweep_high, B - D("0.0015"), B - D("0.0006")),       # sweep bar
        _bar(L + 10, "1.2818", "1.2822", "1.28155", "1.2816"),                            # rejection (confirmation)
    ]
    return cl + tail


def _d1():
    return _d1_candles(_bear_closes())


def _h4():
    return _build_triangle(40)


# ---------------------------------------------------------------------------
# QUALIFIED — the conjunction's TRUE path is reachable (no silent dead gate)
# ---------------------------------------------------------------------------

def test_conjunction_qualified():
    # Pin NORMAL so this composition fixture is decoupled from classifier tuning
    # (the ADR-011 classifier has its own reference tests in test_atr_state.py).
    r = conjunction.evaluate("EURUSD", Side.BEAR, _d1(), _h4(), build_qualified_h1(),
                             _sp(), _ic(), atr_state=AtrState.NORMAL)
    assert len(r.gates) == 8
    assert all(g.passed for g in r.gates), [(i + 1, g.state) for i, g in enumerate(r.gates) if not g.passed]
    assert r.all_gates is True
    assert r.verdict is Verdict.QUALIFIED
    assert r.reasons == ()
    # sweep score recorded (NOT a gate); tier derived from it
    assert r.sweep_score is not None
    assert r.risk_tier in (RiskTier.HIGH, RiskTier.MID, RiskTier.LOW)


def test_and_invariant_holds():
    """all_gates is exactly the AND of the 8 gate.passed flags (§8.1 verbatim)."""
    r = conjunction.evaluate("EURUSD", Side.BEAR, _d1(), _h4(), build_qualified_h1(),
                             _sp(), _ic(), atr_state=AtrState.NORMAL)
    assert r.all_gates == all(g.passed for g in r.gates)


# ---------------------------------------------------------------------------
# REJECTED + DEP_UNMET — flat H1 → no sweep → gates 4/5/7 not evaluated
# ---------------------------------------------------------------------------

def _flat_h1(n=60, val="1.3000"):
    v = D(val)
    return [_bar(i, v, v + D("0.0002"), v - D("0.0002"), v) for i in range(n)]


def test_conjunction_dep_unmet_when_no_sweep():
    r = conjunction.evaluate("EURUSD", Side.BEAR, _d1(), _h4(), _flat_h1(), _sp(), _ic())
    g3, g4, g5, g7 = r.gates[2], r.gates[3], r.gates[4], r.gates[6]
    assert not g3.passed                       # no sweep on a flat series
    assert g4.state == "DEP_UNMET"
    assert g5.state == "DEP_UNMET"
    assert g7.state == "DEP_UNMET"
    assert r.verdict is Verdict.REJECTED
    assert r.all_gates is False
    # No block/sweep → score not computed → SKIP tier
    assert r.sweep_score is None
    assert r.risk_tier is RiskTier.SKIP
    # reasons name the failing gates
    assert any(x.startswith("gate3:") for x in r.reasons)


# ---------------------------------------------------------------------------
# INVALIDATED — structure (Gate 2) invalidation drives the verdict
# ---------------------------------------------------------------------------

def test_conjunction_invalidated():
    h4 = _build_triangle(40)
    res = D("1.3050")
    break_close = res * (D("100") + D("0.31")) / D("100")
    last = h4[-1]
    h4[-1] = {**last, "close": break_close, "high": break_close + D("0.0005")}
    r = conjunction.evaluate("EURUSD", Side.BEAR, _d1(), h4, _flat_h1(), _sp(), _ic())
    assert r.gates[1].state == "INVALIDATED"
    assert r.verdict is Verdict.INVALIDATED


# ---------------------------------------------------------------------------
# Determinism + shuffled-history property
# ---------------------------------------------------------------------------

def test_conjunction_determinism():
    args = ("EURUSD", Side.BEAR, _d1(), _h4(), build_qualified_h1(), _sp(), _ic())
    assert conjunction.evaluate(*args) == conjunction.evaluate(*args)


def test_shuffled_history_property():
    """Shuffling then re-sorting the H1 history by ts must not change the result.

    Guards against any hidden reliance on input list identity / arrival order:
    the decision is a pure function of the chronological candle sequence only.
    """
    import random
    h1 = build_qualified_h1()
    shuffled = h1[:]
    random.Random(12345).shuffle(shuffled)
    shuffled.sort(key=lambda c: c["ts"])
    r1 = conjunction.evaluate("EURUSD", Side.BEAR, _d1(), _h4(), h1, _sp(), _ic())
    r2 = conjunction.evaluate("EURUSD", Side.BEAR, _d1(), _h4(), shuffled, _sp(), _ic())
    assert r1 == r2


def test_atr_state_classifier_is_wired():
    """Default (atr_state=None) derives the regime via the ADR-011 classifier.

    The qualified fixture classifies ELEVATED; passing that state explicitly must
    reproduce the default-path result exactly — proving the conjunction uses the
    classifier rather than a hard-coded NORMAL."""
    h1, sp, ic = build_qualified_h1(), _sp(), _ic()
    derived = atr_state.classify(h1, sp)
    assert derived is AtrState.ELEVATED
    r_default = conjunction.evaluate("EURUSD", Side.BEAR, _d1(), _h4(), h1, sp, ic)
    r_explicit = conjunction.evaluate("EURUSD", Side.BEAR, _d1(), _h4(), h1, sp, ic,
                                      atr_state=derived)
    assert r_default == r_explicit
