# LSB Phase Status

> Only a human edits this file. Claude Code may not cross a locked phase
> (Implementation Plan v3.0, Part 0 — Physics rule).

| Phase | Scope | Status |
|---|---|---|
| Phase A | "Prove" — scaffold, config/schema, data audit, signal engine, backtest, determinism, walk-forward, verdict (Sessions A0–A11, Gate GA) | **ACTIVE** |
| Phase B | Forward test + parallel hardening — broker bridge, 5-state machine, live loop, monitoring, Docker, VPS shadow (Sessions B1–B10, Gate GB) | **LOCKED — human unlock only, after a Gate GA GO** |
| Phase C | "Scale" — VPS promotion, 10% review, outcome learning activation (Sessions C1–C3) | **LOCKED — human unlock only, after a Gate GB GO** |

## Phase A schema

Migration `001_core.sql` (Session A1) — four tables: `config_version`,
`candle`, `signal`, `wf_run` (+ child `sim_trade`). The seven-table v2.1
schema is restored verbatim in Phase B Track 2 (Session B5); its DDL
already exists and deferring it costs nothing.

## Out of scope for Phase A

Per Implementation Plan v3.0, Session A0: no broker, state-machine,
Docker, or deployment directories exist yet. These are Phase B work
(`src/lsb/broker/` — Session B1, operating-machine module — Session B2,
`docker/` — Session B8).

## Environment decisions

- **Dev database:** native PostgreSQL on Windows — *no Docker locally*
  (low-spec workstation). Installation is due at Session A1, the first
  session that touches the database. Docker arrives only at Session B8.
- **CI:** `.github/workflows/ci.yml` runs `pytest` on every commit
  (zero tests collected is acceptable until Session A4). The
  golden-fixture determinism replay (Gate GA-1) is wired in at
  Session A8.
