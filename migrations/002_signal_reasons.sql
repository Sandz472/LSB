-- migrations/002_signal_reasons.sql
-- A5 delta: persist per-gate miss reasons on the signal row.
-- Authored per ADR-002 consequence #1 ("no silent schema change" — use a delta
-- migration rather than editing 001_core.sql).
--
-- The §8.1 conjunction records every evaluated candle (A5 acceptance: a signal
-- row for 100% of evaluated candles).  gate1..gate8 carry per-gate pass/fail
-- (NULL = not evaluated / dependency short-circuit, per ADR-002); `reasons`
-- carries the human-readable miss states (e.g. "gate3:NO_SWEEP;gate6:SESSION_CLOSED")
-- for the A10 verdict report.

ALTER TABLE signal ADD COLUMN IF NOT EXISTS reasons TEXT;
