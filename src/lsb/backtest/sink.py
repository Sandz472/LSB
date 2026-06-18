"""Signal sinks: NullSink (in-memory, CI-safe) and DbSink (wraps persist.py).

The loop depends only on the Sink protocol, so tests use NullSink with
zero DB setup and production runs swap in DbSink with a live connection.
"""

from __future__ import annotations

from typing import Protocol

from lsb.signals.engine import SignalResult


class Sink(Protocol):
    def write(self, result: SignalResult) -> None: ...


class NullSink:
    """In-memory sink — accumulates results for inspection; no DB required."""

    def __init__(self) -> None:
        self.results: list[SignalResult] = []

    def write(self, result: SignalResult) -> None:
        self.results.append(result)

    def qualified(self) -> list[SignalResult]:
        return [r for r in self.results if r.qualified]


class DbSink:
    """Persists qualified signals to the `signal` table via persist.write_signal_row."""

    def __init__(self, conn) -> None:
        self._conn = conn

    def write(self, result: SignalResult) -> None:
        if not result.qualified:
            return
        from lsb.signals.persist import write_signal_row
        write_signal_row(self._conn, result)
