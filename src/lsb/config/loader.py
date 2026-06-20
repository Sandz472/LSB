"""YAML → frozen dataclass loaders.

All numeric values are coerced to Decimal on load so the hash path
never touches bare float.
"""

from __future__ import annotations
from decimal import Decimal, InvalidOperation
from pathlib import Path

import yaml

from .models import InstrumentConfig, SpecConfig

_VALID_CLASSES = {"fx_major", "commodity", "crypto"}
_VALID_SESSIONS = {"fx", "24_7"}
_VALID_UNITS = {"pips", "pct"}
_VALID_SOURCES = {"dukascopy", "binance"}


def _d(raw: object, field: str) -> Decimal:
    """Parse *raw* as Decimal; raise ValueError with a helpful message on failure."""
    if raw is None or str(raw).strip().lower() in ("tbd", ""):
        raise ValueError(
            f"Field '{field}' has no value yet (placeholder). "
            "Supply a concrete value before using this config."
        )
    try:
        return Decimal(str(raw))
    except InvalidOperation:
        raise ValueError(f"Field '{field}': cannot convert {raw!r} to Decimal")


def _require(raw: dict, key: str) -> object:
    if key not in raw:
        raise ValueError(f"Missing required field '{key}'")
    return raw[key]


def load_instrument(path: str | Path) -> InstrumentConfig:
    """Load and validate a per-instrument YAML file."""
    path = Path(path)
    raw: dict = yaml.safe_load(path.read_text(encoding="utf-8"))

    instrument = str(_require(raw, "instrument"))
    instrument_class = str(_require(raw, "instrument_class"))
    if instrument_class not in _VALID_CLASSES:
        raise ValueError(f"instrument_class must be one of {_VALID_CLASSES}")

    sessions = str(_require(raw, "sessions"))
    if sessions not in _VALID_SESSIONS:
        raise ValueError(f"sessions must be one of {_VALID_SESSIONS}")

    for unit_field in ("max_spread_unit", "sweep_pen_unit", "block_width_unit", "stop_buffer_unit"):
        val = str(_require(raw, unit_field))
        if val not in _VALID_UNITS:
            raise ValueError(f"{unit_field} must be one of {_VALID_UNITS}")

    data_source = str(_require(raw, "data_source"))
    if data_source not in _VALID_SOURCES:
        raise ValueError(f"data_source must be one of {_VALID_SOURCES}")

    return InstrumentConfig(
        instrument=instrument,
        instrument_class=instrument_class,
        pip_size=_d(_require(raw, "pip_size"), "pip_size"),
        max_spread=_d(_require(raw, "max_spread"), "max_spread"),
        max_spread_unit=str(raw["max_spread_unit"]),
        sessions=sessions,
        flat_tolerance=_d(_require(raw, "flat_tolerance"), "flat_tolerance"),
        sweep_penetration=_d(_require(raw, "sweep_penetration"), "sweep_penetration"),
        sweep_pen_unit=str(raw["sweep_pen_unit"]),
        block_min_width=_d(_require(raw, "block_min_width"), "block_min_width"),
        block_width_unit=str(raw["block_width_unit"]),
        stop_buffer=_d(_require(raw, "stop_buffer"), "stop_buffer"),
        stop_buffer_elev=_d(_require(raw, "stop_buffer_elev"), "stop_buffer_elev"),
        stop_buffer_unit=str(raw["stop_buffer_unit"]),
        data_source=data_source,
    )


def load_spec(path: str | Path) -> SpecConfig:
    """Load and validate the spec/GA-threshold YAML file."""
    path = Path(path)
    raw: dict = yaml.safe_load(path.read_text(encoding="utf-8"))

    return SpecConfig(
        min_expectancy_r=_d(_require(raw, "min_expectancy_r"), "min_expectancy_r"),
        max_drawdown_pct=_d(_require(raw, "max_drawdown_pct"), "max_drawdown_pct"),
        min_win_rate_pct=_d(_require(raw, "min_win_rate_pct"), "min_win_rate_pct"),
        min_sharpe=_d(_require(raw, "min_sharpe"), "min_sharpe"),
        min_coverage_years=int(_require(raw, "min_coverage_years")),
        min_coverage_instruments=int(_require(raw, "min_coverage_instruments")),
        min_trade_count=raw.get("min_trade_count"),           # None until owner pins
        rejection_geometry=raw.get("rejection_geometry"),     # None until §4.3 resolved
        trend_timeframe=raw.get("trend_timeframe"),           # None until D1/H1 resolved
    )
