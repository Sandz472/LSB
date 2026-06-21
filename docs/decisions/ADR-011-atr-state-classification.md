# ADR-011 — ATR-state classification (COMPRESSED / NORMAL / ELEVATED / EXTREME)

- **Status:** **Accepted** (owner-pinned 2026-06-21; in force from A5)
- **Date:** 2026-06-21
- **Phase:** A (raised and resolved in session A5)

> **Numbering note.** Starts at 011 — see ADR-010 for why 007–009 are reserved by
> §R prior-build citations (memory `lsb-adr-numbering`).

## Context

Three places need a volatility regime:

- **Gate 7 (R:R, §9.1):** the stop buffer is `stop_buffer` normally and
  `stop_buffer_elev` when ATR **ELEVATED** ("4 pip if ATR ELEVATED").
- **Gate 8 (Global Risk, §4.2.2 / §9.3):** ATR **EXTREME → no trade** (risk tier 0%).
- The sweep score's ATR factor (ADR-010) reads the regime.

`GATE_SPECIFICATION.md` named ELEVATED/EXTREME but pinned no numeric thresholds.
A5 originally deferred the classifier (kept `atr_state` an explicit gate input,
default NORMAL). The owner has now **pinned the thresholds from the v2.0 spec**
(§4.2.2 baseline + COMPRESSED; §15.1 ELEVATED/EXTREME defaults), adding a fourth
state — **COMPRESSED** — that the A5 enum did not yet have.

## Decision (pinned values)

Classify the regime at the current H1 bar from `r = ATR(14) / baseline`, where

    baseline = simple mean of the `atr_baseline_window` ATR(14) values immediately
               PRECEDING the current bar (current bar excluded, so "is now unusual
               vs recent history" is measured against an established baseline).

| Field | Value | Source |
|---|---|---|
| `atr_period` | 14 | §15.1 — fixed, "do not change" |
| `atr_baseline_window` | 20 | §4.2.2 — 20-period SMA of ATR(14) |
| `atr_compressed_mult` | 0.75 | §4.2.2 — fixed, not a tuning surface |
| `atr_elevated_mult` | 1.25 | §15.1 default |
| `atr_extreme_mult` | 2.0 | §15.1 default |

Bands (upper boundary inclusive):

    r < 0.75              → COMPRESSED
    0.75 ≤ r < 1.25       → NORMAL
    1.25 ≤ r < 2.0        → ELEVATED
    r ≥ 2.0               → EXTREME

**Baseline excludes the current bar** — this is the one wording choice §4.2.2 left
open ("20-period SMA"); excluding the current bar makes a genuine spike read as a
deviation rather than being damped by its own inclusion. Recorded here explicitly.

### Implementation

- `src/lsb/signal/atr_state.py`: `state_for_ratio(ratio, sp)` (pure threshold rule)
  and `classify(candles_h1, sp)` (ratio + classify). Pure, deterministic.
- Insufficient warm-up (< `atr_period + atr_baseline_window + 1` bars) or a zero
  baseline → **NORMAL** (the safe regime: neither widens the stop nor blocks).
- `conjunction.evaluate(...)` derives `atr_state` from the H1 series by default;
  callers may pass an explicit `AtrState` to override.
- **Gate 7 buffer:** elevated buffer iff ELEVATED or EXTREME; COMPRESSED and
  NORMAL use the normal buffer.
- **Gate 8:** only EXTREME forces no-trade; COMPRESSED passes.

Reference tests (`tests/test_atr_state.py`) hand-verify the boundary behaviour
(0.75 / 1.25 / 2.0) and the COMPRESSED / NORMAL / EXTREME paths on constructed
series with the realised ratio asserted.

## Consequences

1. The classifier is live in the §8.1 conjunction; the volatility guards now
   actually engage off real ATR.
2. `atr_period`, `atr_baseline_window`, `atr_compressed_mult` are **fixed** (spec,
   not tuning surfaces). `atr_elevated_mult` / `atr_extreme_mult` are §15.1
   *defaults* — any change re-enters as a pre-registered ADR, never a silent edit.
3. Multiples are universal across the 4 instruments: the baseline is self-relative
   (each instrument vs its own rolling ATR), so a single set of multiples travels.
