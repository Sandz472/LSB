# ADR-011 — ATR-state classification (NORMAL / ELEVATED / EXTREME)

- **Status:** Proposed (deferred — pin before backtest integration A6–A7)
- **Date:** 2026-06-21
- **Phase:** A (raised in session A5)

> **Numbering note.** Starts at 011 — see ADR-010 for why 007–009 are reserved by
> §R prior-build citations (memory `lsb-adr-numbering`).

## Context

Two §8.1 gates depend on a volatility regime:

- **Gate 7 (R:R, §9.1):** the structural stop buffer is `stop_buffer` normally and
  `stop_buffer_elev` when **ATR ELEVATED** ("4 pip if ATR ELEVATED").
- **Gate 8 (Global Risk, §4.2.2 / §9.3):** **ATR EXTREME → no trade** (risk tier 0%)
  is an active pre-filter.

The sweep score's ATR factor also reads the regime.

`GATE_SPECIFICATION.md` names the states **ELEVATED** and **EXTREME** but pins **no
numeric thresholds** — there is no definition of *how* current ATR maps to a state
(e.g. ATR vs a rolling baseline, and at what multiples). Inventing those numbers in
the gate decision path would be a silent spec deviation (CLAUDE.md rule 1) and
exactly the kind of "manufacturing" Phase A exists to prevent.

## Decision

**A5 keeps the classifier out of the decision path.** `AtrState` is an **explicit
input** to `gate7_rr.evaluate(...)`, `gate8_global_risk.evaluate(...)`, and the
conjunction (default `AtrState.NORMAL`). The gates' *logic* (buffer selection,
EXTREME no-trade) is fully built and tested against each state; only the
*derivation* of the state from an ATR series is deferred.

The numeric classifier — its baseline (proposed: a rolling mean/percentile of H1
ATR(14)) and its ELEVATED / EXTREME multiples — is an **owner decision pinned
before A6–A7**, when the backtest event loop first needs to assign a state per bar.
It will land as config fields (`atr_elevated_*`, `atr_extreme_*`) + a small pure
`classify_atr_state(...)` helper, with hand-verified reference values.

## Consequences

1. A5 is fully spec-faithful: gates 7/8 are complete and reachable for every state
   via explicit fixtures; **no threshold is invented**.
2. The §8.1 conjunction currently runs with `NORMAL` unless a caller supplies a
   state, so A5 fixtures exercise ELEVATED/EXTREME explicitly.
3. **Open item for the owner:** define the ATR-state baseline and multiples (this
   ADR moves to *Accepted* once pinned). Until then the backtest must pass `NORMAL`
   or an explicit per-bar state; it must not guess.
