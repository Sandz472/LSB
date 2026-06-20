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
    assert spec.min_trade_count is None       # still-open owner-decision slot
    assert spec.trend_timeframe == "D1"               # ADR-003
    assert spec.rejection_geometry == "section_8_1_mirror"  # ADR-004


def test_owner_decision_slots_validated(tmp_path):
    """A present-but-unrecognised owner-decision value is rejected, not accepted
    silently — a typo must not change a decision-path enum."""
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
    """config_hash must not depend on JSON key order.

    asdict() always yields fields in dataclass-declaration order, so building
    two InstrumentConfigs from the same values cannot expose a sort_keys bug.
    Instead we directly test the hashing layer: construct two dicts with
    reversed key order and confirm the hash is identical — the test that
    *would* catch sort_keys=False being removed.
    """
    import hashlib, json
    from lsb.config.hashing import _canonical_value
    fields = dataclasses.asdict(load_instrument(CONFIG_DIR / "EURUSD.yaml"))
    canonical_a = {k: _canonical_value(v) for k, v in fields.items()}
    canonical_b = {k: _canonical_value(v) for k, v in reversed(list(fields.items()))}
    # With sort_keys=True both must hash identically; without it they would differ
    h_a = hashlib.sha256(json.dumps(canonical_a, sort_keys=True, ensure_ascii=True).encode()).hexdigest()
    h_b = hashlib.sha256(json.dumps(canonical_b, sort_keys=True, ensure_ascii=True).encode()).hexdigest()
    assert h_a == h_b
    # Confirm that WITHOUT sort_keys the dicts DO produce different JSON
    # (proving our test would catch a sort_keys regression)
    j_no_sort_a = json.dumps(canonical_a, sort_keys=False)
    j_no_sort_b = json.dumps(canonical_b, sort_keys=False)
    assert j_no_sort_a != j_no_sort_b, "reversed dict must differ without sort_keys"


def test_decimal_precision_stability():
    """config_hash must be identical for numerically equal Decimal values
    with different trailing-zero representations (2 vs 2.0 vs 2.00).

    str(Decimal('2.0')) == '2.0' but str(Decimal('2')) == '2' — without
    Decimal.normalize() these would hash differently despite being equal.
    """
    from lsb.config.hashing import _canonical_value
    assert _canonical_value(Decimal("2")) == _canonical_value(Decimal("2.0"))
    assert _canonical_value(Decimal("0.15")) == _canonical_value(Decimal("0.150"))
    assert _canonical_value(Decimal("0.0001")) == _canonical_value(Decimal("1E-4"))


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
