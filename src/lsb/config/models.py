"""Frozen dataclasses for LSB configuration.

All numeric fields use Decimal — never bare float — so the hash path
has no IEEE-754 repr ambiguity across processes or Python versions.
"""

from __future__ import annotations
from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class InstrumentConfig:
    instrument: str
    instrument_class: str          # "fx_major" | "commodity" | "crypto"
    pip_size: Decimal
    max_spread: Decimal
    max_spread_unit: str           # "pips" | "pct"
    sessions: str                  # "fx" | "24_7"
    flat_tolerance: Decimal        # pct baseline §6.1.1
    sweep_penetration: Decimal
    sweep_pen_unit: str            # "pips" | "pct"
    block_min_width: Decimal
    block_width_unit: str          # "pips" | "pct"
    stop_buffer: Decimal           # normal ATR state
    stop_buffer_elev: Decimal      # elevated ATR state
    stop_buffer_unit: str          # "pips" | "pct"
    data_source: str               # "dukascopy" | "binance"


@dataclass(frozen=True, slots=True)
class SpecConfig:
    # §17.1 OOS thresholds — read by verdict code, never re-typed elsewhere
    min_expectancy_r: Decimal         # > 0.3
    max_drawdown_pct: Decimal         # < 15.0
    min_win_rate_pct: Decimal         # > 40.0
    min_sharpe: Decimal               # > 1.0
    min_coverage_years: int           # >= 3
    min_coverage_instruments: int     # >= 3
    # Owner-decision slots — None until pinned via ADR (HALT-HUMAN items)
    min_trade_count: int | None       # §17.1 gap; pin before A11
    rejection_geometry: str | None    # §4.3 vs §8.1 conflict; resolve before A5
    trend_timeframe: str | None       # D1 vs H1 ambiguity; resolve before A4
