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

## Data pipeline (Sessions A2–A3, combined)

Fetch → audit → load pipeline complete. `scripts/fetch_history.py` pulls
H1 OHLCV (Dukascopy for EURUSD/XAUUSD with a Stooq fallback, Deriv
`ticks_history` for BOOM500) into `data/history/` (gitignored, derived
cache). `scripts/audit_history.py` runs five checks (duplicate
timestamps, gaps >2x interval, FX weekend bars, DST-transition
anomalies, spread outliers), writes
`docs/data_audit_report_<INSTRUMENT>.md`, and `--load`s into `candle`
once every `gap>2` anomaly has a written disposition.

All three instruments are loaded into the dev `candle` table:

| Instrument | Rows (H1) | Coverage | Source |
|---|---|---|---|
| EURUSD | 18,701 | 2023-06-12 .. 2026-06-11 (~3y) | dukascopy |
| XAUUSD | 17,766 | 2023-06-12 .. 2026-06-11 (~3y) | dukascopy |
| BOOM500 | 8,761 | ~2025-06-12 .. 2026-06-11 (~1y) | deriv |

**Constraint for human review:** Deriv's `ticks_history` only serves
~1 year of BOOM500 candle history (verified via direct pagination
debugging, not a pipeline bug). `config/BOOM500.yaml`'s walk-forward
window (`train_months: 18` + `test_months: 6` = 24 months) needs more
history than is currently available — Sessions A4–A9 will need either a
reduced BOOM500 walk-forward window or an alternate BOOM500 history
source before its walk-forward can run end-to-end.

## Out of scope for Phase A

Per Implementation Plan v3.0, Session A0: no broker, state-machine,
Docker, or deployment directories exist yet. These are Phase B work
(`src/lsb/broker/` — Session B1, operating-machine module — Session B2,
`docker/` — Session B8).

## Environment decisions

- **Dev database:** native PostgreSQL on Windows — *no Docker locally*
  (low-spec workstation). Installed at Session A1 as a portable binary
  distribution under `%LOCALAPPDATA%\PostgreSQL\17` (no admin rights, no
  Windows service); start/stop via `scripts/start_postgres.ps1`. Dev
  database `lsb_dev` and role `lsb` created per `.env.example`. Docker
  arrives only at Session B8.
- **CI:** `.github/workflows/ci.yml` runs `pytest` on every commit
  (zero tests collected is acceptable until Session A4). The
  golden-fixture determinism replay (Gate GA-1) is wired in at
  Session A8.
