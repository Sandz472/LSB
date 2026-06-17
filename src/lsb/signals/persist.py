"""Persist SignalResult to the `signal` table.

This is the only module with I/O in the signals package. The engine is pure;
this thin writer maps the result to a DB row. Insert-or-get on the UNIQUE
constraint (config_hash, instrument, timeframe, ts).
"""

from __future__ import annotations

import json

from lsb.signals.engine import SignalResult


def _gate_results_json(result: SignalResult) -> str:
    """Serialise the gate evaluation as the JSONB gate_results payload."""
    payload: dict = {
        'direction': result.direction,
        'qualified': result.qualified,
        'gates': [
            {
                'n': g.gate,
                'name': g.name,
                'passed': g.passed,
                'reason': g.reason,
                **(({'detail': g.detail}) if g.detail else {}),
            }
            for g in result.gates
        ],
    }
    if result.rejected_at_gate is not None:
        payload['rejected_at_gate'] = result.rejected_at_gate
    return json.dumps(payload, separators=(',', ':'))


def write_signal_row(conn, result: SignalResult) -> int | None:
    """Insert a signal row for `result`. Returns the row id (or None on conflict).

    Uses ON CONFLICT DO NOTHING on the unique key
    (config_hash, instrument, timeframe, ts).
    """
    gate_json = _gate_results_json(result)
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO signal
                (config_hash, instrument, timeframe, ts, gate_results, qualified)
            VALUES (%s, %s, %s, %s, %s::jsonb, %s)
            ON CONFLICT (config_hash, instrument, timeframe, ts) DO NOTHING
            RETURNING id
            """,
            (
                result.config_hash,
                result.instrument,
                result.timeframe,
                result.ts,
                gate_json,
                result.qualified,
            ),
        )
        row = cur.fetchone()
    conn.commit()
    return row[0] if row else None
