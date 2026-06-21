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
    swing_lookback: int            # ADR-005: fractal pivot half-width (2 = classic 5-bar fractal)
    ema_touch: Decimal             # Gate 4 EMA-interaction tolerance §8.1#4
    ema_touch_unit: str            # "pips" | "pct"


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
    min_trade_count: int | None       # §17.1 gap; pin before A11 — STILL OPEN
    rejection_geometry: str | None    # ADR-004: "section_8_1_mirror" (bull = lower-wick)
    trend_timeframe: str | None       # ADR-003: "D1" (Gate 1 macro trend on Daily)


@dataclass(frozen=True, slots=True)
class StrategyParams:
    """Universal strategy constants from §5.1 / §6.1.1 / §7.2 / §8.1.

    All thresholds live here — never hard-coded in gate functions (CLAUDE.md rule 1).
    Folded into config_hash alongside InstrumentConfig.
    """
    # EMA periods (§5.1)
    ema_fast: int                       # 21
    ema_mid: int                        # 50
    ema_slow: int                       # 89
    atr_period: int                     # 14 — D1 for Gate 1 (ADR-006); H1 for exec-scale gates
    # Gate 1 — macro-trend, D1 ATR-relative (§4.1.2, §5.2, ADR-006)
    ema_compression_atr_mult: Decimal   # 0.10  |EMA21−EMA89| < ATR×0.10 → INVALID
    ema_slope_atr_mult: Decimal         # 0.05  per-bar slope threshold
    slope_lookback: int                 # 3     bars over which slope is measured (§4.1.2)
    ema_cross_lookback: int             # 3     recent-cross blocker window
    # Gate 2 — structure / ascending triangle (§6.1.1)
    resistance_min_touches: int         # 2     ≥2 swing highs within ±flat_tolerance
    rising_low_min_pct: Decimal         # 0.20  each higher low ≥0.20% above prior
    triangle_min_candles: int           # 8     duration floor (H4 bars)
    triangle_max_candles: int           # 60    duration cap
    compression_max_ratio: Decimal      # 0.60  last range / first range
    apex_proximity_lo: Decimal          # 0.75
    apex_proximity_hi: Decimal          # 0.95
    invalidation_break_pct: Decimal     # 0.30  close beyond level → INVALIDATED
    # Gate 3 — liquidity sweep (§7.1.1, §7.2)
    block_min_touches: int              # 2     ≥2 touches to form the block
    sweep_expiry_candles: int           # 3     sweep must be within last N H1 candles
    # Gate 5 — rejection candle (§8.1#5, §4.3, ADR-004 mirror)
    rejection_wick_body_mult: Decimal   # 2.0   dominant wick ≥ 2×body
    rejection_opp_wick_body_max: Decimal  # 0.30 opposite wick ≤ 0.30×body (rejection case)
    # Gate 6 — session (§3.3)
    session_edge_buffer_min: int        # 30    BLOCKED within N min of a session open/close
    news_buffer_min: int                # 60    BLOCKED within N min of a Tier-1 event (Phase-A stub)
    # Gate 7 — risk:reward (§9.1, §9.4)
    rr_min: Decimal                     # 2.5   PASS iff R:R ≥ 2.5
    atr_target_mult: Decimal            # 3.0   ATR×3 structural target candidate (§9.4)
    # Sweep-probability score (NOT a gate; §7.3 → §9.3 risk tier) — formula: ADR-007
    sweep_w_density: Decimal            # 30    factor weights, sum to 100 (§7.3)
    sweep_w_wick: Decimal               # 20
    sweep_w_close: Decimal              # 20
    sweep_w_ema: Decimal                # 15
    sweep_w_atr: Decimal                # 15
    risk_tier_high_min: Decimal         # 80    score ≥80 → 1.0% (§9.3)
    risk_tier_mid_min: Decimal          # 50    score ≥50 → 0.5%; <50 → 0.25% or skip
    skip_below_50: bool                 # False discretionary "skip <50" — OFF keeps score non-gating
