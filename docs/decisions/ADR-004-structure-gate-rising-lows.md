# ADR-004 — Structure Gate: Rising-Lows Leg Correction

**Date:** 2026-06-18
**Status:** Accepted
**Session:** A6 (found while validating the backtest core)

## Context

While running the A6 backtest, **zero** signals qualified over three years of
EURUSD data. Investigation showed every bar was rejected at gate 1 or gate 2 —
`detect_triangle` returned a CONFIRMED triangle **exactly zero times** across the
entire history of all three instruments. Gate 2 (structure present) was
effectively dead, so the backtest engine never had a single setup to act on.

### Root cause

The rising-lows (ascending) and falling-highs (descending) legs used a strict
all-pivot monotonicity test:

```python
rising = all(low_vals[j] > low_vals[j - 1] for j in range(1, len(low_vals)))
```

With `swing_lookback=2` over 60 H4 bars, ~8–15 swing-low pivots are detected.
Requiring **every** pivot to be strictly above its predecessor means a single
noisy lower-low anywhere in the sequence vetoes the whole pattern — which always
happens in real price action. Of 257 windows with a valid flat resistance, **0**
passed this test; 146 had a genuine ≥0.20% net climb.

The 178 pre-existing tests passed because the A4 fixtures were hand-built with
perfectly monotonic pivots — the tests encoded the bug rather than catching it.

### Spec divergence

Requirements v2.0 §6.1.1 specifies *"Minimum 2 higher lows, each at least 0.20%
above the prior low"* plus a *compression ratio* (current candle range ≤ 60% of
the pattern-start range). The old code was **stricter** than spec (all pivots vs.
2) and **omitted** both the 0.20% step and the compression check entirely.

## Decision

Replace the strict monotonicity test with a spec-faithful, noise-tolerant climb:

- `_rising_lows(lows, step_pct, min_points)` — greedily anchors on the first low
  and counts each subsequent low ≥ `step_pct` above the last confirmed low;
  requires ≥ `min_points` points on the ascending line. `_falling_highs` mirrors it.
- Added the §6.1.1 **compression-ratio** check (`_compression_ok`); a pattern that
  passes apex proximity but fails compression is downgraded to `FORMING`, not confirmed.

### Interpretation of "minimum 2 higher lows"

Read as **2 swing-low points forming the rising line** (the conventional TA
definition: two points define a trendline), symmetric with the existing
resistance rule which already implements "minimum 2 swing highs" as ≥2 pivots.
The literal alternative (2 *transitions* = 3 points) yields only 17 candidates
over 3 years — statistically too sparse for Phase A to prove an edge. The count
is configurable (`triangle_min_higher_lows`) so the owner can tighten it via the
v2.1 sensitivity-sweep protocol.

### New config (schema_version 5 → 6)

| Field | Default | Spec |
|---|---|---|
| `triangle_min_higher_lows` | 2 | §6.1.1 "minimum 2 higher lows" |
| `triangle_low_step_pct` | 0.002 | §6.1.1 "each at least 0.20% above the prior" |
| `triangle_compression_ratio` | 0.60 | §6.1.1 "≤ 60% of first candle range" |

## Consequences

- Confirmed triangles over EURUSD history: **0 → 16**. Gate 2 is live.
- A real-data regression test (`tests/integration/test_structure_realdata.py`)
  now asserts the confirmed path is reachable, so a silently-dead gate cannot
  pass CI again.
- **Follow-on finding (not a bug):** the next-tightest constraint is now apex
  proximity [0.75, 0.95] — only 14 of 254 forming triangles reach that band — and
  the gate-1 conjunction (trend must align *and* match the triangle direction).
  End-to-end qualified signals remain very rare (EURUSD reached gate 3 only 3×;
  XAUUSD/BTCUSD 0×). This is genuine strategy selectivity, but it may be **too**
  selective for a statistically meaningful walk-forward (A9). Flagged for an owner
  decision on whether the apex-proximity / step thresholds warrant a sensitivity
  sweep before A9. Do not tune thresholds to manufacture trades without that sign-off.

## Update (2026-06-18) — apex sweep result

The apex-proximity sensitivity sweep (`scripts/sweep_apex.py`) **falsified** the
hypothesis above that apex is the next-tightest constraint. Widening apex from
[0.75, 0.95] to [0.50, 1.00] raises EURUSD structure-admitted bars 3 → 51 but
fully-qualified stays **0 at every setting**; XAUUSD/BTCUSD admit 0 structure bars
even at apex [0, 1]. **Decision: leave apex thresholds unchanged.** The real wall is
downstream — **gate 3 (liquidity sweep) rejects 100%** of the 116 EURUSD
structure-admitted setups and has never passed in 3 years. That is the next
investigation (tracked separately), same dead-gate pattern as this ADR.
