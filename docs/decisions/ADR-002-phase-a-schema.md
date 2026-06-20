# ADR-002 — Phase-A core schema design

- **Status:** Accepted
- **Date:** 2026-06-20
- **Phase:** A (in force from session A1)

## Context

The LSB System Requirements v2.0 document is the immutable spec for gate logic
and GA thresholds (§8.1, §17.1), but it was not available in the local corpus at
the time `migrations/001_core.sql` was authored. The companion documents
(`BUILD_PLAYBOOK.md`, `GATE_SPECIFICATION.md`) establish *what* Phase A must
compute but do not specify column-level table schemas.

## Decision

Design a minimal Phase-A schema from first principles, sufficient to support the
A2–A11 sessions without over-engineering. Four tables:

| Table | Purpose |
|---|---|
| `config_version` | One row per `(config_hash, instrument)`; anchors every downstream row to a frozen config identity. |
| `candle` | Raw OHLCV bars at H1/H4/D1; foreign-keyed to `config_version`. |
| `signal` | Per-H1-bar §8.1 gate evaluation results + sweep score + verdict. |
| `wf_run` + `sim_trade` | Walk-forward windows (18m/6m/3m roll) and their simulated fills (SimulatedBroker, Blueprint v2.1 Part 7.1). |

### Key design choices

**`config_version` composite PK `(config_hash, instrument)`** — a single
config file produces one hash per instrument load; using a composite PK
avoids a cross-instrument hash collision being treated as a shared config.

**`NUMERIC` for all prices/scores** — exact arithmetic; no floating-point
accumulation error over 3 years of candles.

**`CHECK (train_end < test_start)` on `wf_run`** — enforces the A9 invariant
at the DB level; no test span can overlap its train span.

**Gate columns nullable** — `NULL` means "not evaluated" (a short-circuit
at an early gate); `FALSE` means evaluated and failed. This is preferable to
a sentinel value.

## Consequences

1. **If the v2.0 Requirements doc is later supplied** and its column-level
   schema differs from this design, a `migrations/002_delta.sql` is authored
   to reconcile. No silent schema change.
2. **XAUUSD `pip_size`/`max_spread`** are `tbd` placeholders in
   `config/XAUUSD.yaml`; the loader raises `ValueError` on load until the
   owner supplies concrete values. The A2 data fetch for XAUUSD is blocked
   until then.
3. **Owner-decision slots** (`min_trade_count`, `rejection_geometry`,
   `trend_timeframe`) are absent from `config/spec.yaml` and resolve to
   `None` in `SpecConfig`. They must be pinned via owner ADR before A11.
