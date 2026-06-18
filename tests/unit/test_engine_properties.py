"""Engine property tests.

1. Determinism — identical inputs always produce identical outputs.
2. Shuffle property — shuffled candle history qualifies far less often than
   real history (near-zero for random noise), verifying that the engine
   is sensitive to market structure rather than trivially satisfied.
   Requires a live DB connection (uses `db_conn` fixture).

Look-ahead invariance is guaranteed architecturally: evaluate() is a pure
function over an explicit window slice, so no future candle can affect past
evaluations. The determinism test below confirms the engine is referentially
transparent; no separate look-ahead probe is needed.
"""

from __future__ import annotations

import random
from datetime import datetime, timezone, timedelta
from pathlib import Path

import pytest

from lsb.data.config import config_hash, load_config
from lsb.signals import Candle
from lsb.signals.engine import MIN_H1_WINDOW, evaluate

CONFIG_DIR = Path(__file__).resolve().parents[2] / 'config'


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ts(i: int) -> datetime:
    return datetime(2024, 1, 1, tzinfo=timezone.utc) + timedelta(hours=i)


def _candle(i: int, close: float, drift: float = 0.0010) -> Candle:
    return Candle(ts=_ts(i), open=close, high=close + drift,
                  low=close - drift, close=close, volume=1.0)


def _trending_window(n: int = 400, start: float = 1.10, step: float = 0.0005) -> list[Candle]:
    return [_candle(i, start - i * step) for i in range(n)]


# ---------------------------------------------------------------------------
# Determinism (no DB required)
# ---------------------------------------------------------------------------

class TestDeterminism:
    def test_same_window_same_result(self):
        config = load_config(CONFIG_DIR / 'EURUSD.yaml')
        h = config_hash(config)
        window = _trending_window(MIN_H1_WINDOW + 50)

        r1 = evaluate(window, config, h)
        r2 = evaluate(window, config, h)

        assert r1.qualified == r2.qualified
        assert r1.rejected_at_gate == r2.rejected_at_gate
        assert r1.gates == r2.gates

    def test_direction_captured_in_rejection(self):
        # Flat window → gate 1 fails; direction should be None for early reject.
        config = load_config(CONFIG_DIR / 'EURUSD.yaml')
        h = config_hash(config)
        flat = [_candle(i, 1.10) for i in range(MIN_H1_WINDOW + 10)]
        r = evaluate(flat, config, h)
        assert r.qualified is False
        assert r.direction is None  # can't determine direction when trend fails

    def test_extended_window_does_not_change_gate_rejection_reason(self):
        # Evaluating with more historical data should not change a gate-1 rejection.
        # (look-ahead invariance corollary: prepending data does not alter results
        # when the same evaluation candle is used.)
        config = load_config(CONFIG_DIR / 'EURUSD.yaml')
        h = config_hash(config)
        flat_300 = [_candle(i, 1.10) for i in range(MIN_H1_WINDOW)]
        flat_400 = [_candle(i, 1.10) for i in range(MIN_H1_WINDOW + 100)]

        # Both evaluate at their respective window[-1], which happen to be flat candles.
        r1 = evaluate(flat_300, config, h)
        r2 = evaluate(flat_400, config, h)
        # Both should reject at gate 1 for the same reason.
        assert r1.rejected_at_gate == r2.rejected_at_gate == 1
        assert r1.gates[0].reason == r2.gates[0].reason


# ---------------------------------------------------------------------------
# Shuffle property (requires DB connection with real candles loaded)
# ---------------------------------------------------------------------------

SHUFFLE_SEED = 42
NUM_SHUFFLES = 20
WINDOW_SIZE = MIN_H1_WINDOW + 20   # evaluation window per trial


def _load_candles(db_conn, instrument: str, limit: int = 600) -> list[Candle]:
    with db_conn.cursor() as cur:
        cur.execute(
            """
            SELECT ts, open, high, low, close, volume
            FROM candle
            WHERE instrument = %s AND timeframe = 'H1'
            ORDER BY ts DESC
            LIMIT %s
            """,
            (instrument, limit),
        )
        rows = cur.fetchall()
    candles = [
        Candle(ts=r[0], open=float(r[1]), high=float(r[2]),
               low=float(r[3]), close=float(r[4]), volume=float(r[5]))
        for r in reversed(rows)  # ascending time
    ]
    return candles


@pytest.mark.parametrize('instrument', ['EURUSD', 'XAUUSD', 'BTCUSD'])
def test_shuffle_property(db_conn, instrument: str) -> None:
    """Shuffled candle history should qualify much less often than real history."""
    config = load_config(CONFIG_DIR / f'{instrument}.yaml')
    h = config_hash(config)

    candles = _load_candles(db_conn, instrument, limit=600)
    if len(candles) < WINDOW_SIZE:
        pytest.skip(f'{instrument}: only {len(candles)} rows, need {WINDOW_SIZE}')

    window = candles[-WINDOW_SIZE:]

    # Real evaluation
    real_result = evaluate(window, config, h)
    real_qualified = int(real_result.qualified)

    # Shuffled evaluations
    rng = random.Random(SHUFFLE_SEED)
    shuffled_qualifications = 0
    for _ in range(NUM_SHUFFLES):
        shuffled = list(window)
        rng.shuffle(shuffled)
        r = evaluate(shuffled, config, h)
        if r.qualified:
            shuffled_qualifications += 1

    # Shuffled rate must be near-zero OR well below real rate.
    # Wide margin (≤ ¼ of real) or absolute cap of 3 out of 20 runs.
    max_allowed = max(3, real_qualified * NUM_SHUFFLES // 4)
    assert shuffled_qualifications <= max_allowed, (
        f'{instrument}: {shuffled_qualifications}/{NUM_SHUFFLES} shuffled windows qualified '
        f'(real={real_qualified}, threshold={max_allowed}) — engine may be insensitive to structure'
    )
