"""Integration test: one-month H1 replay through the full backtest loop.

Verifies:
- run_backtest completes without error on real Parquet data
- NullSink accumulates signal rows
- All positions are either still active or closed (no leaked state)
- Closed positions have valid R-at-close values
- With pyramiding enabled, a book can hold multiple concurrent legs
"""

from pathlib import Path

import pytest

from lsb.data.config import load_config
from lsb.data.config import config_hash as compute_hash
from lsb.backtest.data import load_parquet
from lsb.backtest.loop import run_backtest
from lsb.backtest.position import PosState
from lsb.backtest.sink import NullSink

_HISTORY = Path("data/history")
_CONFIG_DIR = Path("config")


def _slice_month(candles, year, month):
    """Return candles for a single calendar month (timezone-aware ts)."""
    return [
        c for c in candles
        if c.ts.year == year and c.ts.month == month
    ]


# ---------------------------------------------------------------------------
# EURUSD — single month, pyramiding disabled (spec default)
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def eurusd_config():
    return load_config(_CONFIG_DIR / "EURUSD.yaml")


@pytest.fixture(scope="module")
def eurusd_candles():
    return load_parquet(_HISTORY / "EURUSD_H1.parquet")


def test_replay_eurusd_completes(eurusd_candles, eurusd_config):
    # Use a recent month from the available history
    month_candles = _slice_month(eurusd_candles, 2024, 6)
    # Need surrounding context; grab warm-up bars before the month. The daily
    # macro-trend filter (Gate 1, ADR-007) needs ~90 daily bars (~2160 H1) of
    # warm-up, so pull enough history for the daily EMA(89) to seed.
    month_start = month_candles[0].ts if month_candles else None
    assert month_start is not None, "No June 2024 candles in EURUSD history"

    idx_start = next(i for i, c in enumerate(eurusd_candles) if c.ts == month_start)
    warm_up = max(0, idx_start - 2400)
    slice_ = eurusd_candles[warm_up: idx_start + len(month_candles)]

    h = compute_hash(eurusd_config)
    book, sink = run_backtest(slice_, eurusd_config, h)
    assert isinstance(sink, NullSink)
    assert len(sink.results) > 0, "Expected at least some signal evaluations"


def test_positions_valid_state(eurusd_candles, eurusd_config):
    month_candles = _slice_month(eurusd_candles, 2024, 6)
    idx_start = next(i for i, c in enumerate(eurusd_candles) if c.ts == month_candles[0].ts)
    warm_up = max(0, idx_start - 2400)
    slice_ = eurusd_candles[warm_up: idx_start + len(month_candles)]

    h = compute_hash(eurusd_config)
    book, _ = run_backtest(slice_, eurusd_config, h)

    valid_states = {PosState.FILLED, PosState.MANAGED, PosState.CLOSED}
    for leg in book.all_legs():
        assert leg.state in valid_states
        if leg.state == PosState.CLOSED:
            assert leg.r_at_close is not None
            assert leg.close_reason is not None


# ---------------------------------------------------------------------------
# Pyramiding integration: book can hold multiple legs simultaneously
# ---------------------------------------------------------------------------

def test_pyramiding_multiple_legs(eurusd_candles, eurusd_config):
    """With pyramiding enabled, inject a synthetic second signal and verify
    PositionBook can hold two concurrent legs when policy conditions are met."""
    from lsb.backtest.book import PositionBook
    from lsb.backtest.position import Position, PosState
    import dataclasses

    # Enable pyramiding in a modified config
    new_signals = dataclasses.replace(
        eurusd_config.signals,
        pyramid_enabled=True,
        pyramid_max_legs=3,
        pyramid_add_at_r=1.0,
    )
    cfg_pyr = dataclasses.replace(eurusd_config, signals=new_signals)

    book = PositionBook(cfg_pyr.signals)

    def _make_leg(entry, stop, direction='long'):
        risk = abs(entry - stop)
        return Position(
            instrument='EURUSD', direction=direction,
            entry_price=entry, stop=stop, target=entry + 3 * risk,
            risk=risk, config_hash='x', state=PosState.FILLED,
        )

    leg1 = _make_leg(1.10, 1.09)
    book.add(leg1)

    # Simulate leg1 running to +1.0R so may_add passes
    current_price = 1.11  # r=1.0 for leg1 (risk=0.01)
    assert book.may_add('long', current_price)

    leg2 = _make_leg(1.11, 1.10)
    book.add(leg2)
    assert len(book.active_legs()) == 2

    # With leg2 just placed (r=0 at 1.11), may_add should be blocked (winner-only)
    assert not book.may_add('long', current_price=1.11)

    # Once leg2 is at +1R: may_add opens again
    assert book.may_add('long', current_price=1.12)  # leg2 r = (1.12-1.11)/0.01 = 1.0
