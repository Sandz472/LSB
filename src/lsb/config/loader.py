"""YAML → frozen dataclass loaders.

All numeric values are coerced to Decimal on load so the hash path
never touches bare float.
"""

from __future__ import annotations
from decimal import Decimal, InvalidOperation
from pathlib import Path

import yaml

from .models import InstrumentConfig, SpecConfig, StrategyParams

_VALID_CLASSES = {"fx_major", "commodity", "crypto"}
_VALID_SESSIONS = {"fx", "24_7"}
_VALID_UNITS = {"pips", "pct"}
_VALID_SOURCES = {"dukascopy", "binance"}
_VALID_TREND_TF = {"D1", "H1"}                                  # ADR-003
_VALID_REJECTION_GEOM = {"section_8_1_mirror", "section_4_3_literal"}  # ADR-004


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

    for unit_field in ("max_spread_unit", "sweep_pen_unit", "block_width_unit",
                       "stop_buffer_unit", "ema_touch_unit"):
        val = str(_require(raw, unit_field))
        if val not in _VALID_UNITS:
            raise ValueError(f"{unit_field} must be one of {_VALID_UNITS}")

    data_source = str(_require(raw, "data_source"))
    if data_source not in _VALID_SOURCES:
        raise ValueError(f"data_source must be one of {_VALID_SOURCES}")

    swing_lookback = int(_require(raw, "swing_lookback"))
    if swing_lookback < 1:
        raise ValueError(f"swing_lookback must be >= 1, got {swing_lookback}")

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
        swing_lookback=swing_lookback,
        ema_touch=_d(_require(raw, "ema_touch"), "ema_touch"),
        ema_touch_unit=str(raw["ema_touch_unit"]),
    )


def load_spec(path: str | Path) -> SpecConfig:
    """Load and validate the spec/GA-threshold YAML file."""
    path = Path(path)
    raw: dict = yaml.safe_load(path.read_text(encoding="utf-8"))

    trend_timeframe = raw.get("trend_timeframe")              # ADR-003
    if trend_timeframe is not None and trend_timeframe not in _VALID_TREND_TF:
        raise ValueError(f"trend_timeframe must be one of {_VALID_TREND_TF}")
    rejection_geometry = raw.get("rejection_geometry")        # ADR-004
    if rejection_geometry is not None and rejection_geometry not in _VALID_REJECTION_GEOM:
        raise ValueError(f"rejection_geometry must be one of {_VALID_REJECTION_GEOM}")

    return SpecConfig(
        min_expectancy_r=_d(_require(raw, "min_expectancy_r"), "min_expectancy_r"),
        max_drawdown_pct=_d(_require(raw, "max_drawdown_pct"), "max_drawdown_pct"),
        min_win_rate_pct=_d(_require(raw, "min_win_rate_pct"), "min_win_rate_pct"),
        min_sharpe=_d(_require(raw, "min_sharpe"), "min_sharpe"),
        min_coverage_years=int(_require(raw, "min_coverage_years")),
        min_coverage_instruments=int(_require(raw, "min_coverage_instruments")),
        min_trade_count=raw.get("min_trade_count"),
        rejection_geometry=rejection_geometry,
        trend_timeframe=trend_timeframe,
    )


def load_strategy(path: str | Path) -> StrategyParams:
    """Load and validate the universal strategy-parameter YAML file."""
    path = Path(path)
    raw: dict = yaml.safe_load(path.read_text(encoding="utf-8"))

    triangle_min = int(_require(raw, "triangle_min_candles"))
    triangle_max = int(_require(raw, "triangle_max_candles"))
    if triangle_min >= triangle_max:
        raise ValueError(
            f"triangle_min_candles ({triangle_min}) must be < triangle_max_candles ({triangle_max})"
        )

    slope_lookback = int(_require(raw, "slope_lookback"))
    if slope_lookback < 1:
        raise ValueError(f"slope_lookback must be >= 1, got {slope_lookback}")

    # Sweep-score weights must sum to 100 (§7.3) — guard against a typo that would
    # silently rescale the score and drift the risk tier.
    sweep_weights = {
        "sweep_w_density": _d(_require(raw, "sweep_w_density"), "sweep_w_density"),
        "sweep_w_wick": _d(_require(raw, "sweep_w_wick"), "sweep_w_wick"),
        "sweep_w_close": _d(_require(raw, "sweep_w_close"), "sweep_w_close"),
        "sweep_w_ema": _d(_require(raw, "sweep_w_ema"), "sweep_w_ema"),
        "sweep_w_atr": _d(_require(raw, "sweep_w_atr"), "sweep_w_atr"),
    }
    weight_sum = sum(sweep_weights.values(), Decimal("0"))
    if weight_sum != Decimal("100"):
        raise ValueError(f"sweep-score weights must sum to 100, got {weight_sum}")

    # ATR-state classifier (ADR-011): boundaries must be strictly ordered and
    # straddle the baseline (compressed < 1 ≤ elevated < extreme).
    atr_baseline_window = int(_require(raw, "atr_baseline_window"))
    if atr_baseline_window < 1:
        raise ValueError(f"atr_baseline_window must be >= 1, got {atr_baseline_window}")
    atr_compressed_mult = _d(_require(raw, "atr_compressed_mult"), "atr_compressed_mult")
    atr_elevated_mult = _d(_require(raw, "atr_elevated_mult"), "atr_elevated_mult")
    atr_extreme_mult = _d(_require(raw, "atr_extreme_mult"), "atr_extreme_mult")
    if not (Decimal("0") < atr_compressed_mult < atr_elevated_mult < atr_extreme_mult):
        raise ValueError(
            "ATR-state multiples must satisfy 0 < compressed < elevated < extreme; "
            f"got {atr_compressed_mult}, {atr_elevated_mult}, {atr_extreme_mult}"
        )

    return StrategyParams(
        ema_fast=int(_require(raw, "ema_fast")),
        ema_mid=int(_require(raw, "ema_mid")),
        ema_slow=int(_require(raw, "ema_slow")),
        atr_period=int(_require(raw, "atr_period")),
        atr_baseline_window=atr_baseline_window,
        atr_compressed_mult=atr_compressed_mult,
        atr_elevated_mult=atr_elevated_mult,
        atr_extreme_mult=atr_extreme_mult,
        ema_compression_atr_mult=_d(_require(raw, "ema_compression_atr_mult"), "ema_compression_atr_mult"),
        ema_slope_atr_mult=_d(_require(raw, "ema_slope_atr_mult"), "ema_slope_atr_mult"),
        slope_lookback=slope_lookback,
        ema_cross_lookback=int(_require(raw, "ema_cross_lookback")),
        resistance_min_touches=int(_require(raw, "resistance_min_touches")),
        rising_low_min_pct=_d(_require(raw, "rising_low_min_pct"), "rising_low_min_pct"),
        triangle_min_candles=triangle_min,
        triangle_max_candles=triangle_max,
        compression_max_ratio=_d(_require(raw, "compression_max_ratio"), "compression_max_ratio"),
        apex_proximity_lo=_d(_require(raw, "apex_proximity_lo"), "apex_proximity_lo"),
        apex_proximity_hi=_d(_require(raw, "apex_proximity_hi"), "apex_proximity_hi"),
        invalidation_break_pct=_d(_require(raw, "invalidation_break_pct"), "invalidation_break_pct"),
        block_min_touches=int(_require(raw, "block_min_touches")),
        sweep_expiry_candles=int(_require(raw, "sweep_expiry_candles")),
        rejection_wick_body_mult=_d(_require(raw, "rejection_wick_body_mult"), "rejection_wick_body_mult"),
        rejection_opp_wick_body_max=_d(_require(raw, "rejection_opp_wick_body_max"), "rejection_opp_wick_body_max"),
        session_edge_buffer_min=int(_require(raw, "session_edge_buffer_min")),
        news_buffer_min=int(_require(raw, "news_buffer_min")),
        rr_min=_d(_require(raw, "rr_min"), "rr_min"),
        atr_target_mult=_d(_require(raw, "atr_target_mult"), "atr_target_mult"),
        sweep_w_density=sweep_weights["sweep_w_density"],
        sweep_w_wick=sweep_weights["sweep_w_wick"],
        sweep_w_close=sweep_weights["sweep_w_close"],
        sweep_w_ema=sweep_weights["sweep_w_ema"],
        sweep_w_atr=sweep_weights["sweep_w_atr"],
        risk_tier_high_min=_d(_require(raw, "risk_tier_high_min"), "risk_tier_high_min"),
        risk_tier_mid_min=_d(_require(raw, "risk_tier_mid_min"), "risk_tier_mid_min"),
        skip_below_50=bool(raw.get("skip_below_50", False)),
    )
