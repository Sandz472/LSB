# ADR-004 — Bull rejection geometry: lower-wick hammer (§8.1 mirror)

- **Status:** Accepted (owner decision, 2026-06-20)
- **Date:** 2026-06-20
- **Phase:** A (in force from session A5)
- **Resolves:** `BUILD_PLAYBOOK.md` §8 item 2; `GATE_SPECIFICATION.md` Gate 5
  spec-inconsistency callout. Replaces the prior build's **retracted** ADR-009
  (§R: ADR-009 retracted — the real issue is a §4.3-vs-§8.1 spec conflict, not a
  code choice).

## Context

Gate 5 (§8.1#5, §4.3) requires a rejection candle. The **short** side is
unambiguous across the spec:

- `REJECTION_BEAR` = **upper** wick ≥ 2×body AND lower wick ≤ 0.3×body AND close
  bearish.

The conflict is confined to the **bull (long) mirror**:

- **§8.1 bull mirror** + **glossary** ("rejection by wick direction"): bull
  rejection = **lower** wick ≥ 2×body (a hammer).
- **§4.3** literal: `REJECTION_BULL` is defined by an **upper** wick.

These cannot both hold. Taken literally, §4.3 makes long-side Gate 5 effectively
unsatisfiable, because a bull setup fires only **after a liquidity sweep below
support** (Gate 3 bull mirror: wick below the block low, close above it). A candle
that sweeps the lows and closes bullish is a **hammer — long lower wick, small
body near the top**. An upper-wick candle closing bullish would indicate
rejection from *above* (sellers), which contradicts the setup. The §8.1 mirror +
glossary are therefore internally coherent with the strategy mechanics; §4.3's
`REJECTION_BULL = upper wick` is the **defect**.

## Decision

Resolve the conflict in favour of the **§8.1 mirror + glossary**:

- `REJECTION_BULL` = **lower** wick ≥ 2×body AND **upper** wick ≤ 0.3×body AND
  close bullish — the exact mirror of `REJECTION_BEAR`.
- `ENGULFING_BULL` mirrors `ENGULFING_BEAR` (body engulfs prior body, close > prior
  open), with the same wick requirement applying to the engulfing case.
- §4.3's `REJECTION_BULL = upper wick` is treated as a **spec defect, amended by
  this ADR**. The immutable v2.0 Requirements text is not edited; the amendment is
  recorded here and reflected in `GATE_SPECIFICATION.md`.
- `spec.rejection_geometry = "section_8_1_mirror"`.

The short side is unchanged.

## Consequences

1. `config/spec.yaml` pins `rejection_geometry: "section_8_1_mirror"`; the loader
   validates it against `{"section_8_1_mirror", "section_4_3_literal"}` and
   `SpecConfig.rejection_geometry` is no longer `None`.
2. The long side stays buildable; A5 Gate 5 implements bull = lower-wick keyed on
   `spec.rejection_geometry`, never a hard-coded wick direction.
3. `GATE_SPECIFICATION.md` Gate 5 is updated: the "owner amendment required"
   warning is replaced by the resolved definition citing this ADR.
4. If R-DECIDE later prefers the literal §4.3 reading, it re-enters via a
   superseding ADR setting `rejection_geometry: "section_4_3_literal"` — a visible
   config diff, never a silent change.
