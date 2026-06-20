# ADR-007 — Gate 1 Trend Timeframe: Daily Macro, Not H1

**Date:** 2026-06-19
**Status:** Accepted
**Session:** A6 follow-on (the Gate 1 trend/sweep conflict flagged by ADR-006)

## Context

ADR-006 fixed Gate 3 (sweep target = block level, not extreme wick). Sweeps
became detectable (XAUUSD 4, BTCUSD 1), but a cross-tabulation
(`scripts/diag_sweep_crosstab.py`) showed **100% of detected sweeps were then
vetoed by Gate 1 (trend-not-aligned)**. ADR-006 flagged this as "the next wall"
and a strategy-design decision.

### Root cause — structural trend/structure conflict on H1

The strategy fades counter-trend sweeps: an ascending triangle (rising lows)
→ SHORT; a descending triangle (falling highs) → LONG. Gate 1 requires the
trend to match the trade direction (BEARISH for short, BULLISH for long).

A triangle's sloped leg **is** a counter-trend move: rising lows push H1 EMAs
up (bullish) while the trade is short; falling highs push them down (bearish)
while the trade is long. So on the same timeframe as the structure (H1/H4), the
trend the sloped leg creates is always **opposite** to the trade direction. The
reactive H1 EMA(21/50/89) is captured by the very move being faded.

### Evidence — the macro (daily) trend is the correct filter

`scripts/diag_trend_structure.py` measured trend alignment across all
structure-admitted bars under three timeframes (each EMA 21/50/89):

| Instrument | H1 aligned | H4 aligned | Daily aligned | Daily trend vs trade dir |
|---|---|---|---|---|
| EURUSD | 18.8% | 0% | 0% | shorts in BULLISH, longs in BEARISH (continuation — correctly rejected) |
| XAUUSD | 0% | 0% | 0% | longs in NEUTRAL (no bull trend — correctly rejected) |
| BTCUSD | 9.1% | 9.1% | **85.7%** | shorts in BEARISH (counter-trend rallies — the intended fade) |

The daily trend distinguishes the intended setup (BTC: counter-trend rally to
resistance in a bear market → fade short) from non-setups (EUR: continuation
patterns with the trend; XAU: neutral). H1/H4 cannot, because the triangle's
sloped leg dominates them.

### Decisive test at the actual sweep bar

`scripts/diag_trend_sweep.py` examined the one BTC sweep that could become a
trade (2025-03-19 17:00, short):

| Timeframe | Trend at sweep | Aligned? |
|---|---|---|
| H1 EMA(21/50/89) [old] | BULLISH | ✗ (rejects the short) |
| H4 EMA(21/50/89) | INVALID | ✗ |
| H1 EMA(50/100/200) | INVALID | ✗ |
| **Daily EMA(21/50/89)** | **BEARISH** | **✓ (aligns)** |

The H1 EMAs flipped bullish on the rising-lows rally right at the sweep; the
daily trend preserved the macro bear trend through that rally — exactly the
intended "fade the counter-trend sweep" setup.

## Decision

Gate 1 assesses trend on the **daily** timeframe (EMA 21/50/89, same params),
not H1. Implementation:

- `evaluate()` gains an optional `daily_trend: TrendState | None` parameter.
  When provided, Gate 1 uses it; when `None`, it falls back to the H1 trend
  (backward-compatible path used by unit tests, which test gate *logic* on H1
  fixtures). H1 EMAs (ema21/ema50) and H1 ATR are always taken from the H1
  window — they feed the sweep quality score (Gate 4) and volatility (Gate 6),
  not the trend.
- `run_backtest()` builds complete daily candles incrementally
  (`_DailyAccumulator`) and passes the daily trend to `evaluate()`. Only
  complete days are emitted (the in-progress day is held back), so the daily
  trend never sees a bar whose close is in the future — **no look-ahead**. The
  trend is recomputed only when a new day closes.
- `resample_h1_to_daily()` added to `resample.py` for tests/diagnostics (batch,
  drops the trailing incomplete day, mirroring `resample_h1_to_h4`).
- Daily warm-up: evaluation is skipped until `ema_long_period + 1` (90) complete
  daily bars have elapsed (~2160 H1 bars), analogous to the existing
  `MIN_H1_WINDOW` H1 warm-up.

This is a spec-faithful timeframe correction, same class as ADR-006 (wrong
reference point): H1 was the wrong timeframe for the macro trend filter, because
the triangle's sloped leg structurally dominates H1/H4. The v2.1 spec was not in
the repo to confirm the mandated timeframe; owner sign-off was obtained before
implementing (this is a strategy change per the Phase A immutability rule).

## Consequences

- At the BTC sweep bar, gates 1-4 now pass (was: rejected at Gate 1). Gate 5
  (candle confirmation) then rejects on the confirmation-candle pattern —
  genuine strategy selectivity, not a trend conflict.
- Real-data regression guards in `tests/integration/test_gate1_daily_trend.py`:
  (1) the daily trend unblocks the BTC sweep through gates 1-3; (2) the H1
  fallback still rejects it — proving the daily timeframe is what unblocks.
- Backtest warm-up extended from 300 H1 bars (~12 days) to ~2160 H1 bars
  (~90 days). Integration replay tests updated to pull sufficient warm-up and
  to assert contiguous signal coverage (robust to the warm-up boundary).
- EURUSD/XAUUSD remain at 0 qualified signals: their triangles form with the
  trend (continuation) or in neutral regimes, so the daily filter correctly
  rejects them. This is the filter working, not a bug.

## The next wall — Gate 5 (candle confirmation) and signal rarity

Even with Gate 1 fixed, qualified signals remain very rare: BTC reaches Gate 5
at the one sweep bar and is rejected there (confirmation candle not a
rejection/engulfing pattern); EUR/XAU produce no sweeps that clear the daily
trend. Across 3 years and 3 instruments the strategy has yet to produce a single
fully-qualified signal.

This is now a question of **strategy selectivity vs. statistical sufficiency**
for the walk-forward (A9): too few signals to validate an edge. The binding
constraints are sweep rarity (Gate 3), structure rarity (Gate 2), and
confirmation-candle specificity (Gate 5) — not a single dead gate. This is an
owner decision on whether the apex-proximity / sweep-expiry / confirmation
thresholds warrant a v2.1 sensitivity sweep before A9. Do not relax gates to
manufacture trades without that sign-off.
