# LSB — New-Project Build Playbook & Recursion Loop

- **Version:** v2.0-faithful (new project)
- **Date:** 2026-06-20
- **Universe:** EURUSD, GBPUSD, XAUUSD, BTCUSD
- **Companion:** `GATE_SPECIFICATION.md` (authoritative gate logic, v2.0 §8.1).
- **Governing specs:** System Requirements **v2.0** (immutable source of truth) ·
  Blueprint **v2.1** (sequencing) · Redesign **v3.0** (Phase-A scope cut).
- **Runs in:** Claude Code; graphify is the knowledge base. This document is the
  seed the loop executes against — it is not run from chat.

---

## 0. Goal, termination, and the two rules

**Goal:** reach a defensible **GO / NO-GO** on the four-instrument universe,
**without manufacturing trades**. Terminal states: `GO`, `NO-GO / INSUFFICIENT`,
`HALT-HUMAN`. A NO-GO at week 3 is the plan working as designed (v2.1 Part 18).

**Rule 1 — Spec immutability.** The v2.0 spec is immutable during Phase A.
Implement §8.1 **verbatim** (per `GATE_SPECIFICATION.md`). A deviation is a
written proposal in `docs/decisions/`, parked until after the verdict — *changing
the strategy while validating it invalidates the validation* (v3.0 §2.1).

**Rule 2 — Physics / no autonomous loosening.** The loop may apply **divergence
fixes** (make code match the spec) and **measure** anything. It may **never**
loosen a threshold, alter the gate set, or change the universe — those →
`HALT-HUMAN`. Thresholds live in spec config read by the verdict code; softening
the bar requires a visible diff reviewable as an ADR (v3.0 §1.9).

> **Build spec-faithful from day one — do not inherit the prior build's drift.**
> The §R reconciliation in `GATE_SPECIFICATION.md` lists where the old code
> diverged from v2.0 (ADR-005/006/008, the missing EMA-interaction gate, the
> missing invalidation rule, FX sessions on crypto). The new C2 implements the
> spec, not those divergences. Each old loosening, if wanted, re-enters only as a
> pre-registered proposal.

**Honest heads-up.** The spec *as written* is tighter than the loosened prior
code, so expect very few qualified signals on FX+gold+BTC; GBPUSD correlates with
EURUSD and adds little independent evidence. The loop builds everything correctly
and tells you the truth — which may be INSUFFICIENT. That is a valid result.

---

## 1. Phase structure (v3.0)

- **Phase A — "Prove" (wk 1–3):** 5 modules (C1 Data, C2 Signal Engine = the 8
  §8.1 gates, C3 Backtest, C4 Walk-Forward, C5 Verdict); 4 tables
  (`config_version`, `candle`, `signal`, `wf_run`+`sim_trade`); sessions A0–A11;
  **Gate GA** at end of week 3. No broker, state machine, Docker, or deployment.
- **Phase B (wk 4–13, on GA GO):** MT5 demo bridge, 5-state machine, live loop,
  8-week frozen forward test ∥ Track-2 hardening (remaining v2.1 tables, risk
  modules, monitoring, Docker, VPS shadow, graphify `--postgres` seeding).
- **Phase C (wk 13+, on GB GO):** VPS promotion, 10% review, trade-count-gated
  outcome learning.

`docs/PHASE_STATUS.md` is human-write-only; Claude Code may not cross a locked
phase.

---

## 2. Environment (MT5 + Postgres already installed)

- **Postgres:** create `lsb_dev` + role `lsb`; apply `migrations/001_core.sql`
  (4-table Phase-A schema). MT5 stays **unused in Phase A** — backtest talks only
  to `SimulatedBroker` (v2.1 Part 7.1 pessimistic fills).
- **MT5:** ready for Phase B (native-Windows bridge, ADR-001).
- **graphify (knowledge base):**
  ```
  pip install graphifyy            # double-y
  graphify install --platform claude
  graphify watch                   # live doc-level seeding
  graphify update --postgres       # after 001_core.sql exists
  graphify-mcp --transport stdio   # MCP endpoint for Claude Code
  ```
  Seed `/docs` (manifest §4) first so gate/§/ADR nodes resolve before any code.

---

## 3. CLAUDE.md (governing file — create before any code; blueprint 15.2)

```
# LSB — Governing Instructions
1. docs/LSB_System_Requirements_v2.0 is IMMUTABLE. Implement §8.1 literally per
   GATE_SPECIFICATION.md. Any deviation is a written proposal in docs/decisions/,
   never silent code.
2. Before reading source, query the graph: graphify query / graphify affected.
3. Every module is built independently with unit tests against hand-verified
   reference values BEFORE integration.
4. Determinism is law: same candles + config -> byte-identical decisions. No
   wall-clock, randomness, dict-order, or float-order in a decision path.
5. Risk code gets adversarial tests. Build the FULL §8.1 gate set: do not drop
   the EMA-Interaction gate; do not promote the sweep score to a gate; implement
   the §6.1.1/.2 Invalidation rule; sweep target = block HIGH (§7.2); flat
   tolerance baseline = 0.15% (§6.1.1); crypto sessions = 24/7 (§3.3).
6. pytest -q and the golden-fixture replay must be green before any task is done.
7. After each task: graphify update . ; commit including graphify-out/.
8. Never touch broker/live paths before Phase B is unlocked in PHASE_STATUS.md.
```

---

## 4. Doc manifest (all provided — seed into graphify)

| Doc | Role |
|---|---|
| `LSB_System_Requirements_v2.0.docx` | **immutable spec** (source of truth) |
| `LSB_Master_Blueprint_v2.1.pdf` | sequencing, replay/walk-forward, Part 15 playbook |
| `LSB_v3.0_Spec_and_Playbook.pdf` | Phase-A scope cut, A0–A11 sessions |
| `GATE_SPECIFICATION.md` | authoritative §8.1 gate logic (this build) |
| `BUILD_PLAYBOOK.md` (this) | scaffold + recursion loop |
| `ADR-001-broker-bridge.md` | inherited (native-Windows MT5) |

No blocking gaps remain — the spec PDF/docx that the prior plan was missing is
now in hand.

---

## 5. The recursive build-and-validate loop (Phase A, A0–A11)

`RECURSION_STATE.md` holds the step pointer and human-write-only fields
(`fair_universe`, `human_decision`, any approved proposals). Each Claude Code run:
read state → execute the current step → write evidence → advance / halt /
terminate. Every step builds a module, then its regression guard, then verifies.

| Step | Build (v3.0 session) | Accept-when |
|---|---|---|
| **A0** | scaffold; `PHASE_STATUS.md` (A active, B/C locked); CLAUDE.md; carry ADR-001; CI | tree matches; CI green-on-empty; B/C locked |
| **A1** | config system (YAML→frozen dataclass→sha256 `config_hash`) + `001_core.sql` (4 tables) | identical configs→identical hashes; 4 tables; round-trip tests |
| **A2–A3** | `fetch_history` + `audit_history` + load for all 4 | EUR/GBP/XAU 3y Dukascopy, BTC 3y Binance; every `gap>2` dispositioned; **GBPUSD audit generated**; counts reconcile |
| **A4** | C2 gates **1–4** per §8.1 (Trend D1, Structure incl. **Invalidation**, Sweep vs **block high**, **EMA-Interaction**) | each gate's pass-path reachable on a hand-labelled fixture + ≥2 near-miss rejects; **no silent dead gate** |
| **A5** | C2 gates **5–8** (Rejection §4.3/§8.1, Session §3.3 incl. crypto 24/7, R:R §9.4, Global-Risk stub) + the conjunction; sweep score as **risk-tier**, not a gate | all 8 green on fixtures; conjunction matches §8.1 verbatim; shuffled-history property test passes |
| **A6–A7** | C3 backtest: event loop, position lifecycle, `SimulatedBroker` (Part 7.1 pessimistic fills) | sample month → signal rows for 100% candles; every fill matches hand-computed; no fill kinder than the model |
| **A8** | determinism gate in CI (replay ×2, identical hashes) | **GA-1:** identical hashes; injected nondeterminism is caught |
| **A9** | C4 walk-forward: 18m train / 6m test, roll 3m, all 4 instruments; `wf_run`+`sim_trade` keyed to `config_hash` | full window set reproducible; no test span overlaps its train span |
| **A10** | C5 verdict report: OOS metrics, equity/DD, per-window stability; verdict vs **spec §17.1 thresholds read from config, never re-typed** | renders from a real run; verdict logic unit-tested; no hard-coded threshold |
| **A11** | full run; `docs/anomaly_review.md`; record verdict in `ADR-002-go-no-go.md` | **Gate GA** rendered honestly |

**A4/A5 spec-faithfulness checks (the divergence fixes, applied as build correctness):**
implement the §6.1.1/.2 **Invalidation rule** (`INVALIDATED` is reachable);
sweep detection targets the **block high** (§7.2); the **EMA-Interaction** hard
gate exists (§8.1#4); the sweep-probability score sets **risk tier** only
(§7.3/§9.3); session bands and **crypto 24/7** match §3.3; flat-tolerance baseline
is **0.15%** (§6.1.1). None of these are threshold relaxations — they make the
code match the spec.

**Branch at GA.** `qualified ≥` the owner-set trade-count floor and the §17.1 OOS thresholds met → **GO**.
Otherwise → **R-DECIDE** (do **not** loop back to loosen a gate).

---

## 6. R-DECIDE — owner gate (human only)

If GA is short of the §17.1 OOS bar or the trade-count floor, the loop writes `HALT-HUMAN` with
the funnel + sweep surface and the menu:

- `RESOLVE_SPEC_DEFECT` — amend the §4.3-vs-§8.1 rejection-geometry conflict (and
  the D1-vs-H1 trend-timeframe ambiguity) via an owner ADR, then re-enter A4.
- `EXPAND_UNIVERSE` — prefer an **uncorrelated** instrument over a fifth FX major
  (GBPUSD↔EURUSD correlation adds little independent evidence).
- `PREREGISTER_PROPOSAL: <ADR>` — e.g. flat tolerance >0.15%, sweep vs a level
  instead of the block high — committed **before** seeing in-sample yield, run as
  a sensitivity variable, never as the baseline.
- `REDESIGN` — the deepest question: whether macro-trend alignment belongs on a
  reversal entry at all.
- `ACCEPT_INSUFFICIENT` — terminal `INSUFFICIENT`; archive, post-mortem, treat
  parked proposals as hypotheses for a new ~3-week Phase-A cycle, or retire.

---

## 7. Gate GA criteria (spec §17.1, tested out-of-sample per v2.1 Part 7.2)

The numeric bar is **§17.1** (the blueprint's "§13" is a mis-citation — v2.0 §13
is the session filter). Read these from spec config, never re-typed:

| Criterion | §17.1 bar |
|---|---|
| Positive expectancy | **> 0.3R per trade** |
| Max historical drawdown | **< 15%** of starting equity |
| Win rate (at 2.5R) | **> 40%** |
| Sharpe ratio | **> 1.0** |
| Coverage | **≥ 3 years**, **≥ 3 instruments** (1 FX major, 1 index, 1 other) |

v2.1 Part 7.2 changes only *how* these are tested: out-of-sample, rolling
(18m/6m/3m), cost-loaded, with a ±20% sensitivity sweep that must not flip the
verdict. The gate moved from week 7 to week 3 (v3.0); the bar did not move.

> **The one genuine gap:** §17.1 defines no **minimum trade count**. The
> INSUFFICIENT boundary therefore needs an owner number (or a stated statistical
> convention, e.g. ≥30 OOS trades per instrument) recorded in spec config before
> A11 — otherwise "enough trades for the verdict to mean something" is undefined.

---

## 8. What still needs an owner decision (the loop HALTs here, by design)

1. **Minimum trade count** for the INSUFFICIENT boundary — §17.1 omits it (see §7).
   Pin a number in spec config before A11.
2. **Rejection geometry** — the §4.3 (`REJECTION_BULL` = upper wick) vs §8.1/glossary
   (bull = lower wick) conflict. Resolve before A5; the long side is unbuildable
   until then.
3. **Trend timeframe** — §3.2 (Daily macro) vs §4.1 (EMAs on H1). Resolve before A4.

Items 2–3 are spec defects; record each as an owner ADR in `docs/decisions/`.
Everything else needed for a faithful from-scratch rebuild is in the corpus.
