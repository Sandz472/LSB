# ADR-001 — Broker Bridge: native-Windows MT5

- **Status:** Accepted (carried from the prior build; unchanged for the rebuild)
- **Date:** 2026-06-20
- **Phase:** B (the bridge is inert in Phase A)

## Context

LSB must place orders on MetaTrader 5 in Phase B. MT5's Python integration is a
native-Windows library; there is no first-class Linux/container binding without a
Wine/RPC shim that adds a non-deterministic failure surface to a decision path.

## Decision

Run the live broker bridge as a **native-Windows** process talking to a locally
installed MT5 terminal. Phase A never touches it: the backtest talks only to the
in-process `SimulatedBroker` (Blueprint v2.1 Part 7.1 pessimistic fills). The MT5
bridge is built and exercised only after Gate GA passes and Phase B is unlocked
in `PHASE_STATUS.md`.

## Consequences

- Phase A is fully OS-portable; only Phase B pins to Windows.
- No broker/live code path may exist in the repo until Phase B is unlocked
  (CLAUDE.md rule 8).
- Revisit only via a superseding ADR if a supported cross-platform MT5 binding
  becomes available.
