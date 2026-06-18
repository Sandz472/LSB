"""Injectable replay clock for deterministic backtesting.

ReplayClock emits candle-close timestamps in lock-step with the candle list.
No wall-clock reads — prerequisite for the A8 determinism gate.
"""

from __future__ import annotations

from typing import Iterator

from lsb.signals import Candle


class ReplayClock:
    """Iterates over a candle list, exposing the current timestamp via .now.

    Usage::

        clock = ReplayClock(candles)
        for bar_idx in clock:
            ts = clock.now
            candle = candles[bar_idx]
    """

    def __init__(self, candles: list[Candle]) -> None:
        self._candles = candles
        self._idx = 0

    @property
    def now(self):
        """Timestamp of the current bar (candles[_idx].ts)."""
        return self._candles[self._idx].ts

    def __iter__(self) -> Iterator[int]:
        for i in range(len(self._candles)):
            self._idx = i
            yield i

    def __len__(self) -> int:
        return len(self._candles)
