# ADR-010 — Sweep-probability score: sub-factor formulas

- **Status:** Proposed (parked — Playbook Rule 1; owner review before A6–A7)
- **Date:** 2026-06-21
- **Phase:** A (introduced in session A5)

> **Numbering note.** Local ADR files run 001–006. Numbers **007, 008, 009 are
> reserved**: `GATE_SPECIFICATION.md` §R cites them as *prior-build* ADR numbers
> (007→trend timeframe, 008→approach-from-below, 009→rejection geometry) that map
> onto current ADR-003/004. New local ADRs therefore start at **010** to avoid the
> collision trap. See memory `lsb-adr-numbering`.

## Context

§7.3 defines the sweep-probability score as a 5-factor, 0–100 number with fixed
weights — **density 30 · wick 20 · close 20 · EMA 15 · ATR 15** — that selects the
§9.3 position-size *risk tier*. It is **not a gate** (the prior build wrongly
promoted "score ≥ 50" to a hard gate — §R). The spec pins the **weights** but does
**not** specify how each factor is normalised to [0, 1]. A5 needs a concrete,
deterministic formula to populate `signal.sweep_score` / `signal.risk_tier`.

## Decision (proposed)

Implement the score in `src/lsb/signal/sweep_score.py` with the §7.3 weights read
from `StrategyParams` (loader enforces Σ = 100) and the following factor
normalisations, each clamped to [0, 1]:

| Factor | Weight | Normalisation (this ADR) |
|---|---|---|
| density | 30 | `min(block_touches / 4, 1)` — block touch count vs a saturation target of 4 |
| wick | 20 | `clamp(penetration / ref, 0, 1)` — sweep-wick depth beyond the block edge, `ref` = H1 ATR (or block width if ATR absent) |
| close | 20 | dominant-wick fraction of the sweep candle range (`(high−close)/range` bear; mirror bull) — rejection strength |
| EMA | 15 | `clamp(1 − ema_delta / ema_tol, 0, 1)` — proximity of the Gate-4 probe to the nearest EMA |
| ATR | 15 | regime factor: COMPRESSED → 1.0, NORMAL → 1.0, ELEVATED → 0.5, EXTREME → 0.0 (regimes per ADR-011) |

`score = Σ weightᵢ · factorᵢ ∈ [0, 100]`.

Tier mapping is **spec-pinned** (not part of this ADR): ≥80 → 1.0% · ≥50 → 0.5% ·
<50 → 0.25% (or skip if `skip_below_50`); ATR EXTREME / drawdown breach → 0%.

## Why this is safe to build now (not a HALT)

The score **never gates qualification** in the validation baseline:
`skip_below_50 = false`, so a <50 score maps to the 0.25% tier, never to a
rejection. Phase-A backtests carry no position sizing, so the tier is recorded but
unused. The §8.1 conjunction does not read the score. Therefore the formula choice
**cannot contaminate the qualification funnel** — it only colours a currently
unused field. The weights are spec-faithful; only the normalisation is this ADR's.

## Consequences

1. Owner reviews the five normalisations before sizing matters (Phase B). A change
   re-enters as a new config/ADR; it does not touch the gate set.
2. The saturation target (4 touches) and the ATR regime factors (1.0 / 0.5 / 0.0)
   are this ADR's parameters; if pinned differently they move to config.
3. If §7.3 of the v2.0 doc later specifies exact factor formulas, this ADR is
   superseded and the code reconciled — no silent change.
