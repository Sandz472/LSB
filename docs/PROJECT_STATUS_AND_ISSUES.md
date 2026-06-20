# LSB Strategy Bot — Project Status & Issues Brief

**Date:** 2026-06-19
**Purpose:** Self-contained brief of all issues found thus far and the current
project state, for a strategy review to decide whether the strategy logic needs
tweaking before the walk-forward (Session A9).

---

## 1. What this project is

A liquidity-sweep reversal trading strategy ("LSB") for H1 charts on three
instruments: **EURUSD, XAUUSD, BTCUSD**. The strategy detects ascending/descending
triangles, waits for a liquidity sweep of the triangle's resistance/support level,
then fades the sweep in the direction of the macro trend.

The entry qualifier is an **eight-gate conjunction** — all eight must pass on the
same bar for a setup to qualify:

| Gate | Name | What it checks |
|---|---|---|
| 1 | Trend alignment | Macro trend matches trade direction (BEARISH→short, BULLISH→long) |
| 2 | Structure present | Confirmed ascending/descending triangle on H4, apex in [0.75, 0.95] |
| 3 | Liquidity sweep | Price pierced the block *level* and closed back inside, within last 3 bars |
| 4 | Sweep quality | 5-factor score (density, wick, close, EMA proximity, ATR) ≥ 50 |
| 5 | Candle confirmation | Confirmation candle is rejection/engulfing in trade dir, closes beyond level, wick/body ≥ 2.0 |
| 6 | Volatility acceptable | ATR state in {NORMAL, ELEVATED}; spread within cap |
| 7 | Session clear | Active session, not within 30 min of a session boundary |
| 8 | Risk viable | Structural stop placeable; R:R ≥ 2.5 |

Trade direction is fixed by the triangle type: **ascending → SHORT** (fade
resistance sweep), **descending → LONG** (fade support sweep). This is a
contrarian/reversal philosophy.

## 2. Where we are in the build plan

The Implementation Plan v3.0 sequences 12 sessions to a GO/NO-GO verdict:

- **A0–A3:** Scaffold, config/schema, data pipeline audited ✅
- **A4–A5:** Signal engine, gates 1–8, fixture-tested ✅
- **A6:** Backtest event loop + pyramiding (ADR-003) ✅
- **A7:** SimulatedBroker, pessimistic fill model ✅
- **A6 follow-on (current):** Debugging why zero signals qualify. Four ADRs
  (004–007) fixed dead gates. Still zero qualified signals.
- **A8:** Determinism gate (not started)
- **A9:** Walk-forward (not started)
- **A10–A11:** Verdict report, GO/NO-GO

**The blocker:** the strategy has produced **zero fully-qualified signals** across
3 years × 3 instruments. The walk-forward (A9) cannot validate an edge with no
trades. The spec's GO/NO-GO criteria include a minimum trade count; zero trades
would force an INSUFFICIENT verdict.

## 3. The dead-gate pattern — issues found and fixed

A recurring pattern: each gate, when first exercised on real data, was **silently
dead** (rejected 100% of setups) due to a spec divergence. Hand-built unit fixtures
encoded the bug rather than catching it. Four gates were fixed in sequence:

### ADR-004 — Gate 2: rising-lows leg (fixed)
The sloped-leg test required *every* swing pivot to be strictly monotonic. A single
noisy lower-low vetoed the whole pattern → 0 confirmed triangles ever. Spec §6.1.1
only requires "≥2 higher lows, each ≥0.20% above the prior" + a compression ratio.
Fixed to spec-faithful noise-tolerant climb. EURUSD triangles: 0 → 16.

### ADR-005 — Gate 2: flat-leg tolerance (fixed)
The flat-resistance tolerance (0.5%) was calibrated for EURUSD volatility. Gold and
BTC move 3–6× more per H4 bar, so 0% of their triangles passed the flat-leg test.
Calibrated per-instrument: EURUSD 0.5%, XAUUSD 1.0%, BTCUSD 2.0%. XAU/BTC structure
now reachable.

### ADR-006 — Gate 3: sweep target (fixed)
`detect_sweep` measured penetration against `block.upper`/`block.lower` — the
**extreme swing wick**, an outlier price almost never reaches. The sweep target
should be `block.level` (the horizontal resistance/support line where resting
liquidity sits). Fixed. Sweeps now detectable: XAUUSD 4, BTCUSD 1 (was 0).

### ADR-007 — Gate 1: trend timeframe (fixed)
Gate 1 assessed trend on H1 EMA(21/50/89). But a triangle's sloped leg (rising
lows / falling highs) **is** a counter-trend move that dominates the reactive H1
EMAs — so at the sweep, H1 always reflected the move being faded, opposite to the
trade direction. 100% of detected sweeps were vetoed at Gate 1. Fixed: Gate 1 now
uses the **daily** macro trend, which preserves the macro direction through the
counter-trend pullback. Evidence: daily trend aligned 85.7% on BTC structure bars
(vs 9.1% on H1) and at the one BTC sweep bar (daily BEARISH vs H1 BULLISH).

**All four were logic/reference corrections (spec divergences), not threshold
tuning.** Each was a case of the code being stricter or wrong-referenced vs the
spec, masked by hand-built fixtures.

## 4. The current wall — Gate 5 and signal rarity (NOT a bug)

After ADR-007, the one BTC sweep that clears gates 1–4 reaches Gate 5 and fails.
**Investigation confirms Gate 5 is working as designed** — this is genuine
selectivity, not another dead gate:

### The BTC signal funnel (3 years, 26,022 bars)

| Gate | Rejected here | Cumulative pass |
|---|---|---|
| 1 (trend) | 12,239 | 13,783 |
| 2 (structure) | 13,759 | 24 |
| 3 (sweep) | 23 | **1** |
| 4 (quality) | 0 | 1 |
| 5 (confirmation) | 1 | **0** |
| 6–8 | 0 | 0 |

Only **24 bars in 3 years** have a qualifying structure (Gate 2). Only **1** of
those has a sweep (Gate 3). The binding constraint is structure + sweep rarity, not
Gate 5.

### The one setup that reaches Gate 5 (BTC, 2025-03-19 17:00)

- Gates 1–4 pass (daily BEARISH, ascending triangle apex 0.86, sweep score 58).
- Gate 5 fails: the sweep candle is a bearish **momentum** bar (body 344, lower
  wick 477, upper wick 131), not a rejection pin. `classify_candle` = BEARISH;
  `upwick/body = 0.38` vs required `2.0`.
- The sweep is a **1-bar event**: the next bar (15402) closed back *above* the
  level, so the false-sweep filter invalidates it. No "next bar" confirmation
  opportunity exists — the sweep didn't hold.
- **Possible concern:** price was already trading *above* the 84483 resistance for
  bars 15399–15400, then broke down through it. This looks like a breakdown from
  above, not a true liquidity sweep (which approaches the level from below, spikes
  through, and rejects). The sweep detection does not require approaching from
  below — it only checks high > level + threshold AND close < level. This may be
  letting non-sweep events through, but it is not the Gate 5 blocker.

### EURUSD / XAUUSD

- **EURUSD:** 0 sweeps detected even vs the level. When the triangle is confirmed
  (apex ∈ [0.75, 0.95]) price sits below resistance and hasn't reached it; the
  pierce occurs nearer apex ~1.0 where the structure downgrades to FORMING. An
  apex/timing interaction.
- **XAUUSD:** 4 sweeps detected, but all in NEUTRAL daily trend (no bull trend to
  buy against) → correctly rejected at Gate 1.

## 5. Key configuration (BTCUSD shown; EUR/XAU differ only in volatility params)

```yaml
# Trend (Gate 1) — now assessed on DAILY, EMA 21/50/89
ema_short_period: 21
ema_mid_period: 50
ema_long_period: 89

# Structure (Gate 2)
triangle_min_candles: 8
triangle_max_candles: 60          # H4 bars scanned
triangle_flat_tolerance_pct: 0.020  # BTC; EURUSD 0.005, XAUUSD 0.010
triangle_min_higher_lows: 2
triangle_low_step_pct: 0.002      # 0.20% per step
triangle_compression_ratio: 0.60
apex_proximity_min: 0.75
apex_proximity_max: 0.95
swing_lookback: 2

# Sweep (Gate 3)
block_min_touches: 2
sweep_penetration_pips: 0.02      # 0.02% for crypto
sweep_expiry_candles: 3           # sweep valid for 3 H1 bars
sweep_score_min: 50

# Confirmation (Gate 5)
rejection_wick_body_mult: 2.0     # upper wick must be ≥ 2× body

# Risk (Gates 6/8)
allowed_atr_states: [NORMAL, ELEVATED]
min_rr_ratio: 2.5
```

## 6. Open questions for the strategy review

1. **Is the strategy too selective by design, or are there more spec divergences?**
   Four gates were dead due to bugs. Gate 5 appears correct, but the overall
   funnel (1 candidate in 3 years) is too narrow to validate an edge. Is this the
   intended selectivity, or do the structure/sweep/confirmation thresholds need a
   sensitivity sweep?

2. **Sweep semantics (Gate 3):** should a bearish sweep require price to
   *approach the level from below*? The one detected BTC "sweep" was a breakdown
   from above (price already above resistance, then fell through). A true liquidity
   sweep spikes through a level from the approach side and rejects. The current
   detection only checks high > level + threshold AND close < level, which admits
   breakdown candles. Is this a spec divergence or intended?

3. **Confirmation timing (Gate 5):** the confirmation candle is the most recent
   bar, which can be the sweep bar itself (when sweep is bars_ago=1). The spec
   requires a rejection/engulfing pin (wick/body ≥ 2.0). A sweep that closes back
   inside via *momentum* (big body, small wick) is rejected. Should momentum closes
   qualify, or is the rejection-pin requirement correct?

4. **Apex/timing interaction (EURUSD):** sweeps only occur near apex ~1.0 where the
   structure downgrades to FORMING. The confirmed-structure window (apex 0.75–0.95)
   may be too early relative to when sweeps actually happen. Is the apex band or
   the FORMING-vs-confirmed distinction correct?

5. **Trend timeframe (Gate 1, post-ADR-007):** the daily trend fix is implemented
   but the v2.1 spec (now available as `LSB_Master_Blueprint_v2.1.pdf`) should be
   checked to confirm whether it mandates H1, H4, or daily for the trend filter.

## 7. What is fixed vs. what is open

**Fixed (spec divergences, ADR-004–007):**
- Gate 2 rising-lows monotonicity → spec-faithful climb
- Gate 2 flat-leg tolerance → per-instrument calibration
- Gate 3 sweep target → block level, not extreme wick
- Gate 1 trend timeframe → daily macro, not H1

**Open / owner decisions:**
- Gate 5 confirmation: working as designed; no bug found. Whether to relax
  (momentum closes, lower wick/body mult) is a strategy change requiring sign-off.
- Gate 3 sweep semantics: possible divergence (breakdown-from-above admitted as
  sweep). Needs spec check.
- EURUSD apex/timing: 0 sweeps; needs re-evaluation after sweep-semantics decision.
- Overall trade count: 0 qualified signals in 3 years. The walk-forward (A9) will
  fail the spec's minimum-trade-count gate unless more setups qualify.

## 8. Constraints on changes

- The **Master Blueprint v2.1 is immutable during Phase A.** Only fixes for spec
  *divergences* (code stricter/wrong vs spec) are allowed without process. The
  v2.1 spec is now in the repo as `LSB_Master_Blueprint_v2.1.pdf`.
- **Threshold tuning** (apex band, sweep expiry, rejection wick/body, etc.) is a
  strategy change requiring owner sign-off and must go through the v2.1
  sensitivity-sweep protocol. Do not relax gates to manufacture trades without
  sign-off.
- All changes are covered by real-data regression guards so a silently-dead gate
  cannot pass CI again.

## 9. Repository state

- **Branch:** main
- **Modified (uncommitted):** `loop.py`, `engine.py`, `liquidity.py`, `resample.py`
  (ADR-006 + ADR-007 fixes), test files, graphify output.
- **Untracked:** ADR-006, ADR-007, diagnostic scripts, the v2.1 spec PDF, this
  status doc.
- **Last commit:** `3e2a8b7 Session A7: SimulatedBroker — §7.1 pessimistic fill model`
- **Test suite:** all green (unit + integration).
- **Diagnostic scripts** (in `scripts/`): `verify_gate3.py` (per-gate rejection
  counts with daily trend), `diag_sweep_crosstab.py`, `diag_trend_structure.py`,
  `diag_trend_sweep.py`, `diag_sweep_gap.py`.
