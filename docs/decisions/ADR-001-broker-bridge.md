# ADR-001: Broker Bridge — Native-Windows MT5 with EA-Socket Fallback

- **Status:** Accepted
- **Date:** 2026-06-10
- **Source:** Master Blueprint v2.1 Part 4.1 (page 9); carried forward
  unchanged by Implementation Plan v3.0 (inherited decisions list)

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

- Implementation is **Session B1 work** (Phase B Track 1, "MT5 demo
  bridge"), conditional on a Gate GA GO. Until then, the backtest engine
  (Sessions A6–A7) talks only to `SimulatedBroker`, which implements the
  v2.1 Part 7.1 pessimistic fill model and the same broker interface the
  real bridge must conform to — a conformance test suite (Session B1)
  proves both brokers satisfy it identically.
- Session B1 acceptance must satisfy the reliability contract (Blueprint
  Part 4.2): heartbeat → ORDER-SAFE on connectivity loss, restart
  reconciliation against the DB, idempotent client order IDs.
- Deriv synthetics (Boom/Crash) get per-instrument configs and distinct
  ATR-EXTREME thresholds (Appendix A); never share parameters across
  synthetic and conventional instruments.
