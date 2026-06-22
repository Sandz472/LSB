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

Why it is not cosmetic: on a clean 2× spike, including the current bar pulls its
own baseline up by 1/20, so the realised ratio reads ≈1.9× — **ELEVATED instead
of EXTREME**. EXTREME is not a label; it is a hard trading halt (§4.2.2 / §9.3
risk tier 0%) and the §11 in-trade full-exit trigger. Inclusion would therefore
make a genuine 2× spike *fail to halt* — exactly backwards for a volatility
safety gate. Excluding the current bar makes the 1.25 / 2.0 multiples behave as
the true deviation thresholds they are meant to be.

### Scope — governs *all* "20-period avg" baselines, not just M6

This exclude-current convention is **not local to the M6 classifier**. The v2.0
spec reuses the same "20-period average" baseline in at least two other places,
and they must read it identically or a single bar could be EXTREME to the state
engine yet not to the exit rule — a silent inconsistency:

- **§11 — in-trade full-exit:** `ATR > 20-period avg × 2.0`. Same baseline, same
  exclude-current convention. (Phase B; **LOCKED** — not yet built. This ADR
  binds the convention forward so it is built correct, not retrofitted.)
- **§13 — spread baseline:** `2.0× the 20-period rolling average spread` (and the
  `3× normal baseline` rule). Same exclude-current convention on the rolling
  average. (Phase B; **LOCKED**.)

**ADR-011 governs every 20-period-avg baseline in the system.** Any Phase-B code
that computes one excludes the current bar, period.

### Boundary is CI-guarded (golden fixture)

The 2.0 (EXTREME) edge is pinned by a constructed-bar fixture in
`tests/test_atr_state.py` so it cannot drift: with flat closes and constant range
C, ATR(14) == C across the baseline window; a final bar with TR == 15C gives
current ATR == 2C → ratio **exactly 2.0 → EXTREME**, and TR == 14.3C gives ratio
**exactly 1.95 → ELEVATED** (not EXTREME). Both ratios are exact in Decimal.

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
