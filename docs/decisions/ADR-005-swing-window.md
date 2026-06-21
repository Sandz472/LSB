# ADR-005 — Swing-window half-width (spec-silent default)

- **Status:** Accepted (owner decision, 2026-06-21)
- **Date:** 2026-06-21
- **Phase:** A (in force from session A4)
- **Resolves:** `plan-a4-c2-gates-1-4.html` open question 1 — the fractal
  half-width left unspecified by §6.1.1 / §7.1.1.

## Context

§6.1.1 (triangle legs — swing highs for the resistance level, higher lows for the
rising-low leg) and §7.1.1 (block identification — swing-high closes and wicks)
both require **swing highs/lows**, but neither the spec nor
`GATE_SPECIFICATION.md` pins the fractal **half-width N** used to detect a pivot.

N is not cosmetic: it sits **upstream** of the §6.1.1 "≥2 swing highs within
±0.15%" resistance rule and of block detection, so it directly shapes which bars
count as pivots and therefore **which setups qualify**. A spec-silent parameter
that moves qualification must be made explicit, auditable, and swept — not buried
as an implementation constant (CLAUDE.md rule 1: never silent code).

## Decision

- **N = `swing_lookback` = 2** — the classic **5-bar fractal**: a pivot requires
  **2 strictly-bracketing bars on each side**.
- This is a **per-instrument config field**, hashed into `config_hash`. Because
  `config_hash` is computed over the frozen `InstrumentConfig` dataclass
  (`asdict`), not the raw YAML text, the value enters the hash only once it is a
  real dataclass field — so A4 adds `swing_lookback: int` to `InstrumentConfig`
  and the loader, alongside `swing_lookback: 2` in all four instrument YAMLs.
- Recorded as a **deliberate spec-silent default**, not a spec value.

## Consequences

1. `config/{EURUSD,GBPUSD,XAUUSD,BTCUSD}.yaml` gain `swing_lookback: 2`;
   `InstrumentConfig` gains `swing_lookback: int` (validated `≥ 1`); the loader
   reads it. The four `config_hash` values change accordingly — expected and
   recorded.
2. Both the §6.1.1 triangle-pivot detection and the §7.1.1 block detection read
   `swing_lookback` from config; the fractal half-width is **never hard-coded**.
3. **Sensitivity:** N ∈ {1, 2, 3} is added to the A9/A10 sensitivity-sweep set. A
   verdict that **flips on N** is treated as non-robust and **fails the §17.1
   sensitivity check** (a setup whose existence depends on the pivot half-width is
   not a durable edge).
4. Revisited only via a superseding ADR if R-DECIDE selects a different default.
