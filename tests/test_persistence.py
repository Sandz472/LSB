"""A5 persistence-boundary tests — one signal row per evaluated candle.

The conjunction is pure; this is the single place C2 writes.  Acceptance:
a signal row for 100% of evaluated candles, with per-gate pass/fail + reasons,
and idempotent re-runs (ON CONFLICT DO NOTHING).
"""

from __future__ import annotations
from decimal import Decimal as D

from lsb.config import load_strategy, load_instrument, config_hash
from lsb.signal import conjunction, persistence
from lsb.signal.types import Side, Verdict, AtrState

from test_conjunction import build_qualified_h1, _flat_h1, _d1, _h4

from pathlib import Path
CONFIG = Path(__file__).parent.parent / "config"


def _sp():
    return load_strategy(CONFIG / "strategy.yaml")


def _ic():
    return load_instrument(CONFIG / "EURUSD.yaml")


def _hash():
    return config_hash(_ic(), _sp())


def _eval(h1):
    # NORMAL pinned: these tests assert row shape/idempotency, not regime behaviour.
    return conjunction.evaluate("EURUSD", Side.BEAR, _d1(), _h4(), h1, _sp(), _ic(),
                                atr_state=AtrState.NORMAL)


def test_to_row_qualified_shape(fake_executor):
    r = _eval(build_qualified_h1())
    row = persistence.to_row(_hash(), r)
    # config_hash, instrument, ts, g1..g8, all_gates, sweep_score, risk_tier, verdict, reasons
    assert len(row) == 16
    assert row[1] == "EURUSD"
    assert row[3:11] == (True,) * 8           # all 8 gates passed
    assert row[11] is True                     # all_gates
    assert row[14] == Verdict.QUALIFIED.value
    assert row[15] is None                     # no reasons when qualified


def test_dep_unmet_serialised_as_null():
    """ADR-002: a dependency short-circuit (DEP_UNMET) persists as NULL, not FALSE."""
    r = _eval(_flat_h1())
    row = persistence.to_row(_hash(), r)
    # gate3 evaluated+failed → False; gates 4/5/7 DEP_UNMET → None
    assert row[5] is False                      # gate3
    assert row[6] is None                       # gate4
    assert row[7] is None                       # gate5
    assert row[9] is None                       # gate7
    assert row[14] == Verdict.REJECTED.value
    assert row[15] and "gate3:" in row[15]


def test_persist_writes_one_row_per_candle(fake_executor):
    results = [_eval(build_qualified_h1()), _eval(_flat_h1())]
    n = persistence.persist_signals(fake_executor, _hash(), results)
    assert n == 2
    assert len(fake_executor.rows) == 2


def test_persist_idempotent(fake_executor):
    r = _eval(build_qualified_h1())
    persistence.persist_signals(fake_executor, _hash(), [r])
    persistence.persist_signals(fake_executor, _hash(), [r])   # replay (A8 determinism)
    # ON CONFLICT DO NOTHING — the same (config_hash, instrument, ts) is not duplicated
    assert len(fake_executor.rows) == 1
