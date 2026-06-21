"""A1/A4 config system tests.

Covers: load, determinism, key-order invariance, float stability,
round-trip equality, frozen immutability, multi-instrument loading,
StrategyParams loading, and combined config_hash.
"""

from __future__ import annotations
import dataclasses
import pytest
from decimal import Decimal
from pathlib import Path

from lsb.config import load_instrument, load_spec, load_strategy, config_hash
from lsb.config.models import InstrumentConfig, SpecConfig, StrategyParams

CONFIG_DIR = Path(__file__).parent.parent / "config"
INSTRUMENTS = ["EURUSD", "GBPUSD", "BTCUSD", "XAUUSD"]


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------

def test_all_instruments_load():
    for sym in INSTRUMENTS:
        cfg = load_instrument(CONFIG_DIR / f"{sym}.yaml")
        assert cfg.instrument == sym
        assert cfg.swing_lookback == 2          # ADR-005
        assert cfg.ema_touch_unit in ("pips", "pct")

def test_btcusd_ema_touch_is_pct():
    cfg = load_instrument(CONFIG_DIR / "BTCUSD.yaml")
    assert cfg.ema_touch_unit == "pct"
    assert cfg.ema_touch == Decimal("0.03")

def test_fx_ema_touch_is_pips():
    cfg = load_instrument(CONFIG_DIR / "EURUSD.yaml")
    assert cfg.ema_touch_unit == "pips"
    assert cfg.ema_touch == Decimal("3")

def test_xauusd_loads_with_owner_values():
    cfg = load_instrument(CONFIG_DIR / "XAUUSD.yaml")
    assert cfg.instrument == "XAUUSD"
    assert cfg.pip_size == Decimal("0.01")
    assert cfg.max_spread == Decimal("30")

def test_spec_loads():
    spec = load_spec(CONFIG_DIR / "spec.yaml")
    assert isinstance(spec, SpecConfig)
    assert spec.min_expectancy_r == Decimal("0.3")
    assert spec.min_trade_count is None
    assert spec.trend_timeframe == "D1"
    assert spec.rejection_geometry == "section_8_1_mirror"

def test_strategy_loads():
    strat = load_strategy(CONFIG_DIR / "strategy.yaml")
    assert isinstance(strat, StrategyParams)
    assert strat.ema_fast == 21
    assert strat.ema_slow == 89
    assert strat.atr_period == 14
    assert strat.ema_compression_atr_mult == Decimal("0.10")
    assert strat.slope_lookback == 3
    assert strat.triangle_min_candles == 8
    assert strat.triangle_max_candles == 60
    assert strat.apex_proximity_lo == Decimal("0.75")
    assert strat.invalidation_break_pct == Decimal("0.30")
    assert strat.sweep_expiry_candles == 3

def test_strategy_frozen():
    strat = load_strategy(CONFIG_DIR / "strategy.yaml")
    with pytest.raises((dataclasses.FrozenInstanceError, AttributeError)):
        strat.ema_fast = 99  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def test_owner_decision_slots_validated(tmp_path):
    base = (CONFIG_DIR / "spec.yaml").read_text(encoding="utf-8")

    bad_tf = base.replace('trend_timeframe: "D1"', 'trend_timeframe: "M15"')
    p1 = tmp_path / "bad_tf.yaml"
    p1.write_text(bad_tf, encoding="utf-8")
    with pytest.raises(ValueError, match="trend_timeframe"):
        load_spec(p1)

    bad_rg = base.replace(
        'rejection_geometry: "section_8_1_mirror"', 'rejection_geometry: "upper_wick"'
    )
    p2 = tmp_path / "bad_rg.yaml"
    p2.write_text(bad_rg, encoding="utf-8")
    with pytest.raises(ValueError, match="rejection_geometry"):
        load_spec(p2)

def test_swing_lookback_minimum(tmp_path):
    base = (CONFIG_DIR / "EURUSD.yaml").read_text(encoding="utf-8")
    bad = base.replace("swing_lookback: 2", "swing_lookback: 0")
    p = tmp_path / "bad.yaml"
    p.write_text(bad, encoding="utf-8")
    with pytest.raises(ValueError, match="swing_lookback"):
        load_instrument(p)


# ---------------------------------------------------------------------------
# Immutability
# ---------------------------------------------------------------------------

def test_instrument_config_frozen():
    cfg = load_instrument(CONFIG_DIR / "EURUSD.yaml")
    with pytest.raises((dataclasses.FrozenInstanceError, AttributeError)):
        cfg.pip_size = Decimal("1")  # type: ignore[misc]

def test_spec_config_frozen():
    spec = load_spec(CONFIG_DIR / "spec.yaml")
    with pytest.raises((dataclasses.FrozenInstanceError, AttributeError)):
        spec.min_sharpe = Decimal("99")  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------------

def test_instrument_determinism():
    h1 = config_hash(load_instrument(CONFIG_DIR / "EURUSD.yaml"))
    h2 = config_hash(load_instrument(CONFIG_DIR / "EURUSD.yaml"))
    assert h1 == h2

def test_combined_determinism():
    instr = load_instrument(CONFIG_DIR / "EURUSD.yaml")
    strat = load_strategy(CONFIG_DIR / "strategy.yaml")
    h1 = config_hash(instr, strat)
    h2 = config_hash(instr, strat)
    assert h1 == h2

def test_different_instruments_differ():
    h_eur = config_hash(load_instrument(CONFIG_DIR / "EURUSD.yaml"))
    h_btc = config_hash(load_instrument(CONFIG_DIR / "BTCUSD.yaml"))
    assert h_eur != h_btc

def test_instrument_hash_differs_from_combined():
    instr = load_instrument(CONFIG_DIR / "EURUSD.yaml")
    strat = load_strategy(CONFIG_DIR / "strategy.yaml")
    assert config_hash(instr) != config_hash(instr, strat)

def test_key_order_invariance():
    import hashlib, json
    from lsb.config.hashing import _canonical_value
    fields = dataclasses.asdict(load_instrument(CONFIG_DIR / "EURUSD.yaml"))
    canonical_a = {k: _canonical_value(v) for k, v in fields.items()}
    canonical_b = {k: _canonical_value(v) for k, v in reversed(list(fields.items()))}
    h_a = hashlib.sha256(json.dumps({"InstrumentConfig": canonical_a}, sort_keys=True, ensure_ascii=True).encode()).hexdigest()
    h_b = hashlib.sha256(json.dumps({"InstrumentConfig": canonical_b}, sort_keys=True, ensure_ascii=True).encode()).hexdigest()
    assert h_a == h_b
    j_no_sort_a = json.dumps(canonical_a, sort_keys=False)
    j_no_sort_b = json.dumps(canonical_b, sort_keys=False)
    assert j_no_sort_a != j_no_sort_b

def test_decimal_precision_stability():
    from lsb.config.hashing import _canonical_value
    assert _canonical_value(Decimal("2")) == _canonical_value(Decimal("2.0"))
    assert _canonical_value(Decimal("0.15")) == _canonical_value(Decimal("0.150"))
    assert _canonical_value(Decimal("0.0001")) == _canonical_value(Decimal("1E-4"))


# ---------------------------------------------------------------------------
# Round-trip
# ---------------------------------------------------------------------------

def test_round_trip():
    cfg1 = load_instrument(CONFIG_DIR / "EURUSD.yaml")
    fields = dataclasses.asdict(cfg1)
    decimal_fields = {
        "pip_size", "max_spread", "flat_tolerance", "sweep_penetration",
        "block_min_width", "stop_buffer", "stop_buffer_elev", "ema_touch",
    }
    rebuilt = {
        k: Decimal(str(v)) if k in decimal_fields else v
        for k, v in fields.items()
    }
    cfg2 = InstrumentConfig(**rebuilt)
    assert cfg1 == cfg2
    assert config_hash(cfg1) == config_hash(cfg2)

def test_strategy_round_trip():
    strat1 = load_strategy(CONFIG_DIR / "strategy.yaml")
    fields = dataclasses.asdict(strat1)
    decimal_fields = {
        "ema_compression_atr_mult", "ema_slope_atr_mult", "rising_low_min_pct",
        "compression_max_ratio", "apex_proximity_lo", "apex_proximity_hi",
        "invalidation_break_pct",
    }
    rebuilt = {
        k: Decimal(str(v)) if k in decimal_fields else v
        for k, v in fields.items()
    }
    strat2 = StrategyParams(**rebuilt)
    assert strat1 == strat2
    assert config_hash(strat1) == config_hash(strat2)
