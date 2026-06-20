# ADR-003 — Gate 1 macro-trend timeframe: Daily (D1)

- **Status:** Accepted (owner decision, 2026-06-20)
- **Date:** 2026-06-20
- **Phase:** A (in force from session A4)
- **Resolves:** `BUILD_PLAYBOOK.md` §8 item 3; `GATE_SPECIFICATION.md` Gate 1
  timeframe callout. Supersedes the prior build's ADR-007 (same conclusion,
  re-decided cleanly for this rebuild rather than inherited).

## Context

The v2.0 spec describes the trend filter on two timeframes and never states
which one Gate 1 (§8.1#1) evaluates:

- **§3.2** — "Macro Context: **Daily**." Gate 1 is the macro-trend filter
  (EMA21 < EMA50 < EMA89 + negative slopes for a bearish stack).
- **§4.1** — computes the EMA indicator engine on **H1**.

Read as "one timeframe must serve every EMA use," these conflict. But the two
clauses describe **different gates**:

- **Gate 1 (Trend State)** is the *macro* filter — §3.2 explicitly names it Daily.
- **Gate 4 (EMA-Interaction, §8.1#4)** checks whether the H1 sweep/confirmation
  candle touches EMA21/EMA50. Those candles are H1, so the EMAs it consumes are
  the §4.1 **H1** EMAs.

So §3.2 and §4.1 are both satisfied without contradiction once the timeframe is
assigned per gate rather than globally.

This is the single highest-leverage strategy question: D1 trend is far more
restrictive than H1, so it materially lowers qualified-signal count. The looser
H1 reading manufactures more setups — the exact contamination Phase A exists to
prevent (`BUILD_PLAYBOOK.md` Rule 2).

## Decision

- **Gate 1 macro trend is evaluated on D1.** `spec.trend_timeframe = "D1"`.
- **Gate 4 EMA-Interaction continues to use H1 EMAs** (§4.1), unchanged — this
  ADR does not move it.

This is faithful to §3.2 and matches the prior build's resolution (§R: ADR-007
verdict **Faithful**). It is the tighter reading, consistent with building the
spec as written and accepting whatever signal count results.

## Consequences

1. `config/spec.yaml` pins `trend_timeframe: "D1"`; the loader validates it
   against `{"D1", "H1"}` and `SpecConfig.trend_timeframe` is no longer `None`.
2. A4 Gate 1 reads the timeframe from config — never hard-codes it — and computes
   the EMA stack/slope on D1 candles. The `candle` table already stores D1 bars
   (ADR-002).
3. Expect **few** qualified signals; a low count is a finding, not a defect, and
   must not be used to argue for relaxing to H1 without a pre-registered proposal
   (Rule 2 → `HALT-HUMAN`).
4. Revisited only via a superseding ADR if R-DECIDE selects `RESOLVE_SPEC_DEFECT`
   (playbook §6).
