# ADR-006 — Gate 3 Sweep Target: Level, Not Extreme Wick

**Date:** 2026-06-19
**Status:** Accepted
**Session:** A6 follow-on (the "next investigation" flagged by ADR-004 / ADR-005)

## Context

ADR-004 and ADR-005 revived Gate 2 (structure) for all three instruments but
left Gate 3 (liquidity sweep) rejecting **100%** of structure-admitted setups —
zero sweeps detected across 3 years on any instrument. ADR-004's apex sweep
explicitly named this "the next investigation, same dead-gate pattern."

### Root cause

`detect_sweep` measured wick penetration against `block.upper` (bearish) /
`block.lower` (bullish) — the **extreme swing-high/low wick** of the pattern:

```python
# ascending triangle → bearish sweep
penetration = candle.high - block.upper      # block.upper = max swing-high wick
close_inside = candle.close <= block.upper
```

The extreme wick is an outlier. A diagnostic (`scripts/diag_sweep_gap.py`)
measured best penetration (in threshold-multiples) against three reference points
over every structure+block setup:

| Instrument | vs MAX-WICK (old) | vs LEVEL (mean wick) | vs MIN-CLOSE |
|---|---|---|---|
| EURUSD | 0/16 reachable | 0/16 | 16/16 (trivial) |
| XAUUSD | 1/27 reachable | **25/27** | 27/27 (trivial) |
| BTCUSD | 9/44 reachable | 12/44 | 44/44 (trivial) |

`block.upper` sat **18–50+ thresholds above the resistance *level*** (mean of
swing wicks). Recent compressed candles trade near the level, not the extreme
wick, so penetration was massively negative (EURUSD best ≈ −21 thresholds;
BTCUSD ≈ −165). The max-wick is unreachable; the min-close is trivially below
price. The **level** — the horizontal resistance/support line where resting
liquidity actually sits — is the correct sweep target.

The hand-built unit fixtures masked this: they set `res_high == res_level`
(`1.2000`), so the extreme wick coincided with the level and sweeps passed. The
tests encoded the bug, exactly as ADR-004 found for the rising-lows leg.

## Decision

Add a `level` field to `BlockResult` carrying the resistance/support **level**
(mean of swing wicks, already computed by `detect_triangle` as
`resistance_level` / `support_level`). Use `block.level` — not the extreme wick —
as the sweep target in `detect_sweep` (penetration, close-inside, false-sweep
filter) and in Gate 5's re-entry check (`closes_beyond`).

The extreme-wick boundaries (`block.upper` / `block.lower`) are retained for
block width and density scoring — they still describe the full liquidity zone.

```python
sweep_level = block.level                      # was block.upper / block.lower
penetration = candle.high - sweep_level        # bearish
close_inside = candle.close <= sweep_level
# false-sweep: no subsequent close beyond sweep_level
```

No config changes, no threshold tuning. This is a logic correction, not a
calibration — the same class of fix as ADR-004 (spec-faithful reference point
replacing an over-strict surrogate).

## Consequences

- Sweeps are now detectable on real data: **XAUUSD 4, BTCUSD 1** (was 0 for
  both). EURUSD remains 0 — price never reaches the resistance level while the
  triangle is confirmed (an apex/timing interaction, see below).
- Real-data regression guards added in `tests/integration/test_sweep_realdata.py`
  assert the sweep path is reachable (pinned known-good windows + full-history
  early-exit scan), so a silently-dead Gate 3 cannot pass CI again.
- `BlockResult` gains a `level` field (default `0.0`); `identify_block` populates
  it from the structure's resistance/support level.

## The next wall — Gate 1 trend/sweep conflict (NOT a Gate 3 bug)

A cross-tabulation (`scripts/diag_sweep_crosstab.py`) computed every component
independently (no gate short-circuit). Of the bars where a sweep **is** detected,
**100% are vetoed by Gate 1 (trend-not-aligned)**:

| Instrument | sweep bars | also trend-aligned |
|---|---|---|
| XAUUSD | 4 | 0 |
| BTCUSD | 1 | 0 |

The sweep bars show the pattern directly:

| ts | struct dir | sweep dir | trend | apex |
|---|---|---|---|---|
| 2024-02-12 07:00 | long | bullish | BEARISH | 0.80 |
| 2024-02-13 06:00 | long | bullish | NEUTRAL | 0.93 |
| 2025-03-19 17:00 | short | bearish | BULLISH | 0.86 |

This is **fundamental to a reversal strategy requiring trend alignment**: the
sweep is the reversal candle — it occurs at the *end* of a move in the direction
*opposite* to the trade. The EMA(21/50/89) trend lags that reversal, so at the
sweep it still reflects the prior move (BEARISH for a long, BULLISH for a short)
— exactly opposite to the required direction. By the time the EMAs confirm the
new direction, the sweep is long expired (`sweep_expiry_candles = 3`).

Gate 3 is fixed. Gate 1's trend-alignment requirement is now the binding
constraint and is in tension with the sweep-reversal thesis. This is a strategy-
design decision (trend definition / time-frame / whether trend alignment is
appropriate for a reversal entry), not a code bug, and is deferred to an owner
decision per the v2.1 sensitivity-sweep protocol. Do not relax Gate 1 to
manufacture trades without that sign-off.

### EURUSD note

EURUSD detects 0 sweeps even vs the level: when the triangle is confirmed
(apex ∈ [0.75, 0.95]) price sits below the resistance and has not yet reached
it; the pierce occurs nearer the apex (~1.0) where the structure downgrades to
FORMING. This is the same apex/timing interaction ADR-004 probed — re-evaluate
only after the Gate 1 question is resolved, since widening apex under a dead
Gate 1 would still yield zero qualified signals.
