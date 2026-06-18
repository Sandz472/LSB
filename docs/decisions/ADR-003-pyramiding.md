# ADR-003 — Pyramiding as a Core Strategy Feature

**Date:** 2026-06-18  
**Status:** Accepted  
**Session:** A6 (backtest core)

## Context

LSB_System_Requirements_v2.0.md §10–§11 and Blueprint v2.1 §6.1 assume a single
open position per instrument at all times. They contain no pyramiding rules.

The owner decided during A6 planning that pyramiding (adding legs to a winning
position) should be built in from the beginning rather than retrofitted in Phase B.

## Decision

A `PositionBook` (`list[Position]`) replaces the single-position assumption in the
backtest loop. Multiple concurrent legs per instrument are supported. The policy
that gates whether a new leg may be added is defined here as ADR-003 defaults.

### ADR-003 Default Policy

| Parameter | Default | Meaning |
|---|---|---|
| `pyramid_enabled` | `false` | Off by default; opt-in per config |
| `pyramid_max_legs` | 3 | Maximum concurrent active legs |
| `pyramid_add_at_r` | 1.0 | Newest active leg must be ≥ 1.0R before adding |
| `pyramid_same_direction_only` | `true` | No hedging — all legs must share direction |

### Winner-only rule

A new leg is only permitted when the **newest currently active leg** has
achieved at least `pyramid_add_at_r` floating R. This prevents pyramiding
into a position that is not yet in profit (i.e., no averaging down).

### Per-leg management

Each leg is independently managed by the §11 rules (breakeven at +1R, EMA21
trail at +1.5R, defensive exits). There is no aggregate stop or aggregate
target across legs.

### Book-wide exits (§11.4)

When a book-wide §11.4 trigger fires (opposing sweep, structure break), it
applies to **all active legs**:

- Opposing sweep → `record_partial_exit()` on each leg (50% partial, sizing deferred to A10)
- Structure break → `book.close_all()` (full close all legs)

### Partial exits and P&L

§11.4 specifies "close 50%" on an opposing sweep, but A6 has no position-sizing
or equity model. The partial exit is recorded as a `PartialExitEvent` on the leg
(price, timestamp, R-multiple at event). Fractional P&L calculation is deferred
to the A10 equity/stats layer.

## Consequences

- `SignalParams` gains four new fields (`pyramid_*`); schema_version bumped 4 → 5.
- All three YAML configs updated with ADR-003 defaults.
- The walk-forward (A9) and GO/NO-GO verdict (A10) results will be influenced by
  whether pyramiding is enabled. Run with `pyramid_enabled: false` first (baseline)
  and with `true` as a sensitivity sweep.
- This feature is **not derived from the spec**. It is an owner decision and must be
  clearly labelled as such in all reporting and comparisons to Blueprint benchmarks.
