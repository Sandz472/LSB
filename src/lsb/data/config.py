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
class SignalParams:
    """Gate/indicator parameters for the M7 entry qualifier (Sessions A4–A5).

    All defaults match LSB_System_Requirements_v2.0.md §16 / Appendix A.
    block_min_width_pips and sweep_penetration_pips are in instrument pip units;
    for crypto/index the engine interprets these as percentage × price / pip_size
    (handled in signals/liquidity.py based on asset_class).
    """
    ema_short_period: int          # 21
    ema_mid_period: int            # 50
    ema_long_period: int           # 89
    ema_slope_lookback: int        # 3 candles back for slope
    atr_period: int                # 14 (spec: do not change)
    atr_elevated_multiplier: float # 1.25× baseline ATR → ELEVATED
    atr_extreme_multiplier: float  # 2.0× baseline ATR → EXTREME
    ema_compression_atr_mult: float  # |EMA21−EMA89| < ATR×mult → INVALID
    slope_threshold_atr_mult: float  # slope abs < ATR×mult → NEUTRAL
    triangle_min_candles: int      # 8 H4 candles minimum for triangle
    triangle_max_candles: int      # 60 H4 candles maximum
    triangle_flat_tolerance_pct: float  # flat-leg: swing range ≤ pct × level (per-instrument calibrated)
    swing_lookback: int            # 2 — N bars each side for swing pivot detection
    apex_proximity_min: float      # 0.75 — price must be ≥75% to apex
    apex_proximity_max: float      # 0.95 — price must be ≤95% to apex
    block_min_touches: int         # 2 touches to confirm a block
    block_min_width_pips: float    # 5 pips (FX) / see docstring for crypto
    sweep_penetration_pips: float  # 2 pips wick extension to qualify
    sweep_expiry_candles: int      # 3 H1 candles before sweep expires
    sweep_score_min: int           # Gate-4 threshold (0–100)
    # Gate 5 — candle confirmation (§8 cond 5)
    rejection_wick_body_mult: float    # directional wick ≥ N× body; spec default 2.0
    # Gate 6 — volatility acceptable (§9.3)
    allowed_atr_states: tuple[str, ...]  # ATRState names that pass; default NORMAL + ELEVATED
    max_spread_pips: float               # per-bar spread cap in pip units
    # Gate 7 — session & news (§8 cond 6)
    session_edge_buffer_min: int         # minutes buffer from session boundary
    # Gate 8 — risk viable (§9.1, §9.4)
    min_rr_ratio: float                  # minimum R:R ratio; spec default 2.5
    sl_buffer_pips: float                # stop buffer above rejection wick, NORMAL ATR (§9.1)
    sl_buffer_pips_elevated: float       # stop buffer, ELEVATED ATR (§9.1; default 4.0)
    # §6.1.1/§6.1.2 rising-lows / falling-highs sloped leg + compression ratio.
    # Defaults match spec §6.1.1 (0.20% step, 60% compression, minimum 2 sloped pivots).
    triangle_min_higher_lows: int = 2       # min swing lows (asc) / highs (desc) forming the sloped leg
    triangle_low_step_pct: float = 0.002    # each higher low ≥ this fraction above the prior (§6.1.1)
    triangle_compression_ratio: float = 0.60  # current candle range ≤ this × pattern-start range (§6.1.1)
    # Pyramiding — ADR-003 (owner decision; NOT in Requirements v2.0 or Blueprint v2.1)
    pyramid_enabled: bool = False
    pyramid_max_legs: int = 3
    pyramid_add_at_r: float = 1.0        # newest leg must be ≥ this R before adding another
    pyramid_same_direction_only: bool = True


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
    signals: SignalParams


def load_config(path: Path) -> InstrumentConfig:
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    sig_raw = dict(raw["signals"])
    if "allowed_atr_states" in sig_raw:
        sig_raw["allowed_atr_states"] = tuple(sig_raw["allowed_atr_states"])
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
        signals=SignalParams(**sig_raw),
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
