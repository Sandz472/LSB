"""The single persistence boundary for the C2 signal engine (A5).

Every evaluated H1 candle produces exactly one `signal` row — QUALIFIED,
REJECTED, or INVALIDATED (A5 acceptance: a row for 100% of evaluated candles).
This is the ONLY module in C2 that writes to the database; the gates and the
conjunction are pure functions.  An injectable executor (psycopg cursor in
production, FakeExecutor in tests) keeps it unit-testable, mirroring data/load.py.

Idempotent: ON CONFLICT (config_hash, instrument, ts) DO NOTHING matches the
UNIQUE in migrations/001_core.sql, so the A8 determinism replay does not
accumulate duplicate rows.

Gate-column semantics (ADR-002): NULL = not evaluated (a dependency short-circuit,
state DEP_UNMET); TRUE/FALSE = evaluated and passed/failed.
"""

from __future__ import annotations
from decimal import Decimal
from typing import Protocol, Sequence

from .types import SignalResult, GateResult

_INSERT = """
INSERT INTO signal (
    config_hash, instrument, ts,
    gate1, gate2, gate3, gate4, gate5, gate6, gate7, gate8,
    all_gates, sweep_score, risk_tier, verdict, reasons
)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
ON CONFLICT (config_hash, instrument, ts) DO NOTHING
"""


class Executor(Protocol):
    def execute(self, sql: str, params: tuple) -> None: ...
    def executemany(self, sql: str, params_seq: list[tuple]) -> None: ...


def _gate_cell(g: GateResult) -> bool | None:
    """NULL for a dependency short-circuit (ADR-002 'not evaluated'); else pass/fail."""
    if g.state == "DEP_UNMET":
        return None
    return g.passed


def to_row(config_hash: str, result: SignalResult) -> tuple:
    """Map a SignalResult to the signal-table parameter tuple (deterministic order)."""
    g = result.gates
    return (
        config_hash,
        result.instrument,
        result.ts,
        _gate_cell(g[0]), _gate_cell(g[1]), _gate_cell(g[2]), _gate_cell(g[3]),
        _gate_cell(g[4]), _gate_cell(g[5]), _gate_cell(g[6]), _gate_cell(g[7]),
        result.all_gates,
        result.sweep_score if isinstance(result.sweep_score, Decimal) else None,
        result.risk_tier.value if result.risk_tier is not None else None,
        result.verdict.value,
        ";".join(result.reasons) if result.reasons else None,
    )


def persist_signals(
    executor: Executor,
    config_hash: str,
    results: Sequence[SignalResult],
) -> int:
    """Write one signal row per result.  Returns the number of rows submitted.

    Duplicates (same config_hash, instrument, ts) are skipped by ON CONFLICT.
    """
    params_seq = [to_row(config_hash, r) for r in results]
    executor.executemany(_INSERT, params_seq)
    return len(params_seq)
