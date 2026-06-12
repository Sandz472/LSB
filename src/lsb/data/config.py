"""Instrument config: YAML -> frozen dataclass -> canonical form -> config_hash.

Identical configs must always produce identical config_hash values. The hash
is computed from a canonical JSON serialisation of the dataclass (sorted
keys, fixed separators); the canonical YAML form is stored alongside it in
config_version for human review, per the Phase A schema.
"""

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path

import yaml


@dataclass(frozen=True)
class BrokerCosts:
    spread_points: float
    slippage_atr_mult: float
    commission_per_lot: float
    swap_long_points: float
    swap_short_points: float


@dataclass(frozen=True)
class WalkForwardWindow:
    train_months: int
    test_months: int


@dataclass(frozen=True)
class InstrumentConfig:
    schema_version: int
    instrument: str
    display_name: str
    asset_class: str
    timeframes: tuple[str, ...]
    pip_size: float
    contract_size: float
    broker_costs: BrokerCosts
    walkforward: WalkForwardWindow


def load_config(path: Path) -> InstrumentConfig:
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    return InstrumentConfig(
        schema_version=raw["schema_version"],
        instrument=raw["instrument"],
        display_name=raw["display_name"],
        asset_class=raw["asset_class"],
        timeframes=tuple(raw["timeframes"]),
        pip_size=raw["pip_size"],
        contract_size=raw["contract_size"],
        broker_costs=BrokerCosts(**raw["broker_costs"]),
        walkforward=WalkForwardWindow(**raw["walkforward"]),
    )


def canonical_dict(config: InstrumentConfig) -> dict:
    # Round-trip through JSON to normalise tuples to lists and nested
    # dataclasses to plain dicts before sorting/serialising.
    return json.loads(json.dumps(asdict(config)))


def canonical_json(config: InstrumentConfig) -> str:
    return json.dumps(canonical_dict(config), sort_keys=True, separators=(",", ":"))


def canonical_yaml(config: InstrumentConfig) -> str:
    return yaml.safe_dump(canonical_dict(config), sort_keys=True)


def config_hash(config: InstrumentConfig) -> str:
    return hashlib.sha256(canonical_json(config).encode("utf-8")).hexdigest()


def get_or_create_config_version(conn, config: InstrumentConfig) -> str:
    """Insert-or-get this config's row in config_version. Returns config_hash."""
    h = config_hash(config)
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO config_version (config_hash, instrument, canonical_yaml)
            VALUES (%s, %s, %s)
            ON CONFLICT (config_hash) DO NOTHING
            """,
            (h, config.instrument, canonical_yaml(config)),
        )
    conn.commit()
    return h
