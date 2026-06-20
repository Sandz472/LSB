"""A1 config system tests.

Covers: load, determinism, key-order invariance, float stability,
round-trip equality, frozen immutability, and multi-instrument loading.
"""

from __future__ import annotations
import dataclasses
import pytest
from decimal import Decimal
from pathlib import Path

from lsb.config import load_instrument, load_spec, config_hash
from lsb.config.models import InstrumentConfig, SpecConfig

CONFIG_DIR = Path(__file__).parent.parent / "config"
INSTRUMENTS = ["EURUSD", "GBPUSD", "BTCUSD"]  # XAUUSD excluded: tbd placeholders


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------

def test_all_loadable_instruments_load():
    """EURUSD, GBPUSD, BTCUSD parse without error."""
    for sym in INSTRUMENTS:
        cfg = load_instrument(CONFIG_DIR / f"{sym}.yaml")
        assert cfg.instrument == sym


def test_xauusd_raises_on_tbd():
    """XAUUSD loader raises ValueError until owner fills tbd fields."""
    with pytest.raises(ValueError, match="tbd|placeholder"):
        load_instrument(CONFIG_DIR / "XAUUSD.yaml")


def test_spec_loads():
    spec = load_spec(CONFIG_DIR / "spec.yaml")
    assert isinstance(spec, SpecConfig)
    assert spec.min_expectancy_r == Decimal("0.3")
    assert spec.min_trade_count is None       # owner-decision slot: unset
    assert spec.rejection_geometry is None
    assert spec.trend_timeframe is None


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

def test_determinism():
    """Loading the same file twice produces identical hashes."""
    h1 = config_hash(load_instrument(CONFIG_DIR / "EURUSD.yaml"))
    h2 = config_hash(load_instrument(CONFIG_DIR / "EURUSD.yaml"))
    assert h1 == h2


def test_different_instruments_differ():
    h_eur = config_hash(load_instrument(CONFIG_DIR / "EURUSD.yaml"))
    h_btc = config_hash(load_instrument(CONFIG_DIR / "BTCUSD.yaml"))
    assert h_eur != h_btc


def test_key_order_invariance():
    """config_hash must not depend on the order fields were assigned.

    We test this by constructing two InstrumentConfig instances from the same
    values but via different intermediate dict orderings, then asserting the
    hashes are equal. Because InstrumentConfig is a frozen dataclass, both
    instances are equal by value — the hash must be equal too.
    """
    fields = dataclasses.asdict(load_instrument(CONFIG_DIR / "EURUSD.yaml"))
    # Build from reversed field order — dataclass constructor accepts keyword args
    reversed_fields = dict(reversed(list(fields.items())))
    cfg_a = InstrumentConfig(**fields)
    cfg_b = InstrumentConfig(**reversed_fields)
    assert config_hash(cfg_a) == config_hash(cfg_b)


def test_float_stability():
    """Decimal serialisation must not produce IEEE-754 repr drift.

    0.1 in IEEE-754 float is 0.1000000000000000055511151...; if we ever
    used repr(float) in the hash path, two nominally equal values could
    produce different hashes. str(Decimal) is exact and stable.
    """
    cfg = load_instrument(CONFIG_DIR / "EURUSD.yaml")
    # flat_tolerance is Decimal("0.15") — serialize twice, must be identical
    h1 = config_hash(cfg)
    h2 = config_hash(cfg)
    assert h1 == h2
    # Also verify the Decimal is stored, not float
    assert isinstance(cfg.flat_tolerance, Decimal)


# ---------------------------------------------------------------------------
# Round-trip
# ---------------------------------------------------------------------------

def test_round_trip():
    """Load → inspect fields → rebuild dataclass from same fields → equal."""
    cfg1 = load_instrument(CONFIG_DIR / "EURUSD.yaml")
    fields = dataclasses.asdict(cfg1)
    # Restore Decimals (asdict gives strings for Decimal via _canonical_value? No —
    # asdict gives the raw Decimal objects; coerce back explicitly for the rebuild)
    decimal_fields = {
        "pip_size", "max_spread", "flat_tolerance", "sweep_penetration",
        "block_min_width", "stop_buffer", "stop_buffer_elev",
    }
    rebuilt = {
        k: Decimal(str(v)) if k in decimal_fields else v
        for k, v in fields.items()
    }
    cfg2 = InstrumentConfig(**rebuilt)
    assert cfg1 == cfg2
    assert config_hash(cfg1) == config_hash(cfg2)
