"""Signal persistence tests — DB round-trip for signal rows.

Requires Postgres running (start with scripts/start_postgres.ps1).
Uses the session-scoped db_conn fixture from conftest.py.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from lsb.data.config import config_hash, load_config
from lsb.signals.engine import MIN_H1_WINDOW, evaluate
from lsb.signals import Candle
from lsb.signals.persist import write_signal_row

CONFIG_DIR = Path(__file__).resolve().parents[2] / 'config'


def _candle(i, close):
    from datetime import timedelta
    ts = datetime(2024, 1, 1, tzinfo=timezone.utc) + timedelta(hours=i)
    return Candle(ts=ts, open=close, high=close + 0.001, low=close - 0.001,
                  close=close, volume=1.0)


def _build_result():
    config = load_config(CONFIG_DIR / 'EURUSD.yaml')
    h = config_hash(config)
    window = [_candle(i, 1.10 - i * 0.0005) for i in range(MIN_H1_WINDOW + 50)]
    return evaluate(window, config, h)


class TestSignalPersist:
    def test_write_and_read_back(self, db_conn):
        result = _build_result()
        row_id = write_signal_row(db_conn, result)
        # Row ID is returned (new insert) or None (duplicate).
        assert row_id is None or isinstance(row_id, int)

        with db_conn.cursor() as cur:
            cur.execute(
                "SELECT instrument, qualified, gate_results FROM signal "
                "WHERE config_hash = %s AND ts = %s",
                (result.config_hash, result.ts),
            )
            rows = cur.fetchall()

        assert len(rows) == 1
        instrument, qualified, gate_results_raw = rows[0]
        assert instrument == result.instrument
        assert qualified == result.qualified
        payload = gate_results_raw if isinstance(gate_results_raw, dict) else json.loads(gate_results_raw)
        assert 'gates' in payload
        assert isinstance(payload['gates'], list)

    def test_idempotent_write(self, db_conn):
        """Writing the same result twice must not raise or create a duplicate row."""
        result = _build_result()
        write_signal_row(db_conn, result)
        write_signal_row(db_conn, result)

        with db_conn.cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) FROM signal WHERE config_hash = %s AND ts = %s",
                (result.config_hash, result.ts),
            )
            count = cur.fetchone()[0]

        assert count == 1

    def test_gate_results_json_has_required_keys(self, db_conn):
        result = _build_result()
        write_signal_row(db_conn, result)

        with db_conn.cursor() as cur:
            cur.execute(
                "SELECT gate_results FROM signal WHERE config_hash = %s AND ts = %s",
                (result.config_hash, result.ts),
            )
            row = cur.fetchone()

        payload = row[0] if isinstance(row[0], dict) else json.loads(row[0])
        assert 'direction' in payload
        assert 'qualified' in payload
        assert 'gates' in payload
        for gate in payload['gates']:
            assert {'n', 'name', 'passed', 'reason'}.issubset(gate.keys())
