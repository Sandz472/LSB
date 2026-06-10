# ADR-001: Broker Bridge — Native-Windows MT5 with EA-Socket Fallback

- **Status:** Accepted
- **Date:** 2026-06-10
- **Source:** Blueprint Part 4.1 (page 9); week-1 decision per Fix F4

## Decision

Use the **native Windows** bridge pattern: the Windows VPS runs the MT5
terminal with the official `MetaTrader5` Python package in-process. This
is the blueprint's recommended pattern — most reliable, best-documented
path, at a modest extra VPS cost.

**Fallback:** the EA socket bridge (a thin MQL5 Expert Advisor exposing a
socket/REST bridge, core stays on Linux). Adopt only if Windows licensing
becomes a constraint. The Wine-on-Linux pattern is rejected for live
capital (fragile under terminal updates).

## Consequences

- Implementation is **Phase-4 work**, after a G3 GO. Until then M9 talks
  to the replay harness's `SimulatedBroker`, which implements the same
  M9 interface — the core never knows which bridge it's talking to.
- Phase-4 acceptance must satisfy the reliability contract (Part 4.2):
  heartbeat → ORDER-SAFE on connectivity loss, restart reconciliation
  against the DB, idempotent client order IDs.
- Deriv synthetics (Boom/Crash) get per-instrument configs and distinct
  ATR-EXTREME thresholds (Appendix A); never share parameters across
  synthetic and conventional instruments.
