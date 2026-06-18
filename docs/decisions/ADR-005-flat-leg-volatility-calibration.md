# ADR-005 — Flat-Leg Tolerance: Per-Instrument Calibration

**Date:** 2026-06-18
**Status:** Accepted
**Session:** A6 follow-on (discovered during XAU/BTC structure-gap investigation)

## Context

ADR-004 fixed the rising-lows leg and revived Gate 2 for EURUSD (0 → 16 confirmed
triangles). A post-fix sweep (`scripts/sweep_apex.py`) then showed XAUUSD and BTCUSD
still admitted **zero structure bars** even with apex widened to `[0, 1]`. A standalone
diagnostic (`scripts/diag_structure_gap.py`) isolated the exact veto:

| Instrument | Windows | Flat-leg pass (tol=0.5%) | Confirmed triangles |
|---|---|---|---|
| EURUSD  | 18,401 | 1,413 (7.7%) | 16 |
| XAUUSD  | 17,466 | 8 (0.05%)    | **0** |
| BTCUSD  | 26,022 | 4 (0.02%)    | **0** |

The flat-leg test (`high_range <= resistance × 0.005`) was calibrated against EURUSD
volatility. The empirical dispersion of swing-high clusters (measured as
`high_range / resistance`) differs by asset class:

| Instrument | Median dispersion | p10 |
|---|---|---|
| EURUSD | 1.06% | 0.62% |
| XAUUSD | 3.02% | 1.40% |
| BTCUSD | 5.85% | 2.88% |

Gold and BTC move more per H4 bar in percentage terms. A single 0.5% threshold that
is calibrated for EURUSD is 3–6× too tight for gold/BTC.

### Why ATR-relative normalization was rejected

An ATR-relative approach (`high_range ≤ k × ATR`) was explored as a way to share one
multiplier across all instruments. Empirically, the per-instrument `high_range/ATR`
distributions ARE nearly identical (p10 ≈ 2.2–2.6 for all three). However, ascending
triangles form during **volatility compression** — and during compression the current
ATR (and even the 20-period ATR baseline) shrinks alongside the pattern. A known-good
EURUSD ascending window shows ATR = 0.0016 (compressed from a typical 0.005), making
`k=2.3 × 0.0016 = 0.0036` strictly tighter than the old threshold of `0.005 × 1.09 =
0.0055`. The ATR-relative test is strictest exactly when it should be most lenient, so
it produced 0 confirmed EURUSD triangles — worse than the old code.

## Decision

Keep the existing `high_range ≤ resistance × triangle_flat_tolerance_pct` logic.
Calibrate `triangle_flat_tolerance_pct` per-instrument so that all three instruments
reach a comparable flat-leg admit rate (~7–10% of 60-bar H4 windows).

**Calibration** (`scripts/calibrate_flat_atr.py` + inline empirical sweep):

| Instrument | `triangle_flat_tolerance_pct` | Flat-leg admit | Confirmed (step-5 sampled) |
|---|---|---|---|
| EURUSD | 0.005 (unchanged) | ~7.7% | ~16 per 3 yr |
| XAUUSD | **0.010** (raised from 0.005) | ~7–8% | ~6 per sampled pass |
| BTCUSD | **0.020** (raised from 0.005) | ~8% | ~8 per sampled pass |

The values match the ~p7–p8 of each instrument's flat-dispersion distribution and
are derivable from first principles: XAU's inherent H4 swing-high dispersion is ~2×
EURUSD's; BTC's is ~4–6×.

### Why per-instrument is appropriate

The flat-leg tolerance encodes "how tight must a horizontal resistance look on the
chart." This is inherently instrument-relative — gold and BTC simply have wider
typical price swings, so "flat" on a gold chart spans more pips in absolute terms.
Per-instrument values are transparent, tunable via the v2.1 sensitivity-sweep
protocol, and do not require code changes to adjust.

### New config (schema_version 6 → 7)

No field renames. `triangle_flat_tolerance_pct` keeps the same name; the values
for XAUUSD and BTCUSD are raised. schema_version bumped to 7 to mark this
calibration event.

| Config | Old value | New value |
|---|---|---|
| EURUSD | 0.005 | 0.005 (unchanged) |
| XAUUSD | 0.005 | **0.010** |
| BTCUSD | 0.005 | **0.020** |

## Consequences

- XAUUSD and BTCUSD are no longer silently dead at the flat-leg step of Gate 2.
- EURUSD behavior is unchanged.
- **Gate 3 is still the next wall**: the ADR-004 apex-sweep finding (gate 3 liquidity
  sweep rejects 100% of EURUSD structure-admitted setups) still applies. Reviving XAU/
  BTC at the flat-leg does not guarantee they clear gate 3. That is a separate
  investigation.
- Regression guards added in `tests/integration/test_structure_realdata.py` assert
  each instrument produces at least one confirmed triangle in a sampled history sweep.
- `triangle_flat_tolerance_pct` values are Phase A starting points. The v2.1
  sensitivity-sweep protocol governs per-instrument tuning; do not tighten without
  walk-forward sign-off.
