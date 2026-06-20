"""Shared pytest fixtures."""

from __future__ import annotations
import pytest


class FakeExecutor:
    """In-memory DB executor that simulates ON CONFLICT DO NOTHING."""

    def __init__(self):
        self.rows: list[tuple] = []

    def execute(self, sql: str, params: tuple) -> None:
        self.rows.append(params)

    def executemany(self, sql: str, params_seq: list[tuple]) -> None:
        existing = {(r[0], r[1], r[2], r[3]) for r in self.rows}
        for p in params_seq:
            key = (p[0], p[1], p[2], p[3])
            if key not in existing:
                self.rows.append(p)
                existing.add(key)


@pytest.fixture
def fake_executor():
    return FakeExecutor()
