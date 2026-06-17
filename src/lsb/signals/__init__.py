from typing import NamedTuple


class Candle(NamedTuple):
    ts: object          # datetime; engine is type-agnostic
    open: float
    high: float
    low: float
    close: float
    volume: float
    spread: float | None = None
