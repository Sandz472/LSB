# LSB — Phase Status

> **HUMAN-WRITE-ONLY.** Claude Code may read this file but must never edit it or
> cross a locked phase boundary (CLAUDE.md rule 8; playbook §1). A phase is
> unlocked only by a human editing the status below.

| Phase | Scope | Status |
|---|---|---|
| **A — Prove** (wk 1–3) | C1 Data, C2 Signal Engine (8 §8.1 gates), C3 Backtest, C4 Walk-Forward, C5 Verdict; 4 tables; sessions A0–A11; Gate GA | **ACTIVE** |
| **B — Forward** (wk 4–13, on GA GO) | MT5 demo bridge, 5-state machine, live loop, 8-week frozen forward test ∥ Track-2 hardening | **LOCKED** |
| **C — Promote** (wk 13+, on GB GO) | VPS promotion, 10% review, trade-count-gated outcome learning | **LOCKED** |

## Current session pointer

- **Phase A — session A0 (scaffold).** No broker, state machine, Docker, or
  deployment exists or may be created. Phases B and C are locked.
