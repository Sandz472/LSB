# ADR-006 — Macro-trend gate ATR timeframe = D1 (extends ADR-003)

- **Status:** Accepted (owner decision, 2026-06-21)
- **Date:** 2026-06-21
- **Phase:** A (in force from session A4)
- **Extends:** **ADR-003** (Gate 1 macro trend = D1). ADR-003 settled the *EMA*
  timeframe; this ADR settles the **ATR timeframe** for Gate 1's ATR-relative
  thresholds, which ADR-003 did not address.
- **Resolves:** `plan-a4-c2-gates-1-4.html` open question 2; closes the residual
  §3.2-vs-§4.1 ambiguity for the ATR term specifically.

## Context

ADR-003 placed the Gate 1 macro trend on **D1** (`spec.trend_timeframe = "D1"`),
using D1 EMA(21/50/89), and scoped §4.1's **H1** EMAs to Gate 4 (EMA-Interaction).
It did **not** state which timeframe's ATR feeds Gate 1's ATR-relative thresholds:

- **Slope threshold** = `ATR × 0.05` over 3 candles (§4.1.2).
- **EMA-compression INVALID** = `|EMA21 − EMA89| < ATR × 0.10` (§5.2).

A threshold must live on the **same timeframe as the series it scales**. D1 EMA
moves scaled by **H1** ATR (≈ 1/5 the magnitude of a D1 move) would make the slope
threshold effectively unreachable (trend almost never NEUTRAL) and EMA-compression
essentially never fire — a dimensional mismatch that silently loosens Gate 1.

## Decision

- **Gate 1 (M3 trend) uses D1 EMA(21/50/89) and D1 ATR(14).** The slope (§4.1.2)
  and EMA-compression (§5.2) thresholds are scaled by **D1 ATR**.
- **H1 ATR is retained for every execution-scale use — these do NOT move to D1:**
  Gate 6 ATR-state, the §7.3 sweep-probability ATR factor, the §9.1
  structural-stop buffer, and the §9.4 R:R `ATR × 3` target.
- §4.1's H1 EMAs remain scoped to the indicator engine (Gate 4), unchanged from
  ADR-003.
- D1 bars are built from **complete days only** (no look-ahead). Mirrors the prior
  project's ADR-007 conclusion, re-decided cleanly for this rebuild.

## Consequences

1. A4 Gate 1 computes the EMA stack/slope and the compression check on **D1**
   candles with **D1 ATR(14)** — both timeframe choices read from config, never
   hard-coded.
2. All other ATR consumers (Gates 6–8 build, §7.3 score, §9 stops/targets) stay on
   **H1 ATR**; A4/A5 must not switch them.
3. Trend classification is dimensionally consistent: with-trend continuation
   patterns and neutral regimes are correctly rejected rather than waved through
   by an undersized threshold.
4. `GATE_SPECIFICATION.md` Gate 1 ATR references are annotated "(D1 ATR per
   ADR-006)". The immutable v2.0 Requirements text is not edited.
5. Revisited only via a superseding ADR if R-DECIDE selects `RESOLVE_SPEC_DEFECT`.
