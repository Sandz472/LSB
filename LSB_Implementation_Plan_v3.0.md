# LSB Implementation Plan v3.0 — Full Playbook

**Companion to:** LSB Redesign Spec v3.0 ("Prove One Thing")
**Inherits unchanged from Master Blueprint v2.1:** the eight entry gates and all strategy logic, all risk parameters, the pessimistic fill model (Part 7.1), the seven-table DDL (Part 5), GO/NO-GO thresholds (Part 14), ADR-001 broker-bridge decision, the honest risk register, and the instrument list (Appendix A).
**Changes from v2.1:** sequencing, scope-per-phase, and session structure only. 29 serialized sessions become **12 sessions to GO/NO-GO**, then two parallel tracks of ~10 sessions, then 3 promotion sessions. The bar at every gate is bit-identical to v2.1.

---

## Part 0 — Operating Doctrine

Three rules govern every decision below:

1. **Jobs rule (scope):** Phase A builds only what answers the question *"does the liquidity sweep edge survive walk-forward validation?"* Anything else is deferred, however cheap it looks.
2. **Musk rule (sequence):** requirements interrogated → deleted → simplified → accelerated → automated, in that order. Everything that can run parallel to calendar time, does.
3. **Physics rule (gates):** the 8-week forward test and trade-count-gated outcome learning are launch windows. No early exit on good results, no extension-as-rescue on bad ones, no parameter changes mid-window. Schedule aggression lands on build scope and sequencing only.

**Working agreements (all phases):**
- Determinism is enforced in CI from session A6 onward: the golden-fixture replay runs twice per commit and both runs must produce identical output hashes.
- Every config is a YAML file per instrument, loaded into a frozen dataclass, canonicalised, sha256-hashed to `config_hash`, and insert-or-get into `config_version`. Identical configs must always produce identical hashes. Every result row references the `config_hash` that produced it — walk-forward results are meaningless without this.
- The v2.1 spec is immutable during Phase A. Any proposed strategy change is written to `docs/decisions/` and parked until after the GO/NO-GO verdict. Changing the strategy while validating it invalidates the validation.
- Each session ends with green CI and a commit. No session's "accept when" criteria, no merge.

---

## Part 1 — Phase A: "Prove" (Weeks 1–3, Sessions A0–A11)

**Single deliverable: the Verdict Report. Gate GA (GO/NO-GO) at end of week 3.**

### Phase A schema (migration `001_core.sql` — 4 tables)

`config_version` (config_hash PK, canonical YAML, created_at) · `candle` (instrument, timeframe, ts, OHLCV, spread; unique on instrument+timeframe+ts) · `signal` (per-candle gate evaluation: which of the 8 gates passed/failed, with reasons, FK to config_version) · `wf_run` (one row per walk-forward window: instrument, train span, test span, config_hash, metrics JSONB) with child table `sim_trade` (entry/exit, prices, slippage applied, R-multiple, FK to wf_run).

The three live-trading tables from v2.1 Part 5 are restored **verbatim** in Phase B Track 2 — their DDL already exists; deferral costs nothing.

### Sessions

**SESSION A0 · Scaffold (Week 1, Day 1).**
Prompt: *"Create the reduced repository structure: `src/lsb/{data,signals,backtest,walkforward,report}/`, `config/`, `migrations/`, `tests/`, `docs/decisions/`, `scripts/`. Write `docs/PHASE_STATUS.md` marking Phase A active and Phases B/C locked. Carry forward `docs/decisions/ADR-001-broker-bridge.md` (native-Windows MT5, EA-socket fallback, status: accepted — implementation deferred to B1). Set up pytest and CI running unit tests on every commit. Do NOT create broker, state-machine, Docker, or deployment directories — they do not exist in Phase A."*
Accept when: tree matches; CI green (zero tests is fine today); PHASE_STATUS explicitly locks B/C.

**SESSION A1 · Config system + schema (Week 1).**
Prompt: *"Implement the config system: YAML per instrument in `config/`, frozen dataclass, canonicalisation, sha256 `config_hash`, insert-or-get into `config_version`. Write `migrations/001_core.sql` with the four Phase-A tables above, apply to the dev database, write round-trip tests."*
Accept when: identical configs → identical hashes, always; four tables exist; round-trip tests green.

**SESSION A2 · Data pipeline, instrument #1 (Week 1). ∥ lane 1**
Prompt: *"Write `scripts/fetch_history.py` pulling ≥3 years of H1 OHLCV for the first Appendix-A instrument (broker export or Dukascopy) into Parquet under `data/history/`, then `scripts/audit_history.py` reporting gaps, duplicate timestamps, weekend bars, DST anomalies, and spread outliers. Fail the audit on any unexplained gap >2 candles. Produce `docs/data_audit_report.md`. Load audited data into `candle`."*
Accept when: audit report exists and every flagged anomaly has a written disposition.

**SESSION A3 · Data pipeline, instruments #2–#n (Week 1). ∥ lane 1**
Prompt: *"Extend fetch/audit/load to the full Appendix-A list (≥3 instruments per the walk-forward requirement). One audit report per instrument, same dispositions rule."*
Accept when: ≥3 instruments fully audited and loaded; per-instrument candle counts reconcile with expected trading hours.

**SESSIONS A4–A5 · Signal engine: the eight gates (Week 1–2). ∥ lane 2 — runs parallel to A2–A3; no shared code.**
Prompt (A4): *"Implement entry gates 1–4 exactly per Blueprint v2.1, as pure functions over candle windows: no broker awareness, no side effects, no clock. Build each gate test-driven against hand-labeled fixture examples — for every gate, at least one fixture that should pass and two near-misses that should fail, labeled by hand from real chart data before the gate is coded. Every evaluation writes a `signal` row with per-gate pass/fail and reasons."*
Prompt (A5): *"Gates 5–8, same discipline. Then the conjunction: a setup qualifies only when all eight gates pass on the same evaluation, per v2.1. Add property tests: shuffled candle history must never qualify at a rate comparable to real history."*
Accept when: all 8 gates green against hand-labeled fixtures; near-misses correctly rejected; conjunction logic matches the v2.1 spec verbatim; the shuffle property test passes.

**SESSIONS A6–A7 · Backtest engine (Week 2).**
Prompt (A6): *"Implement the event-driven backtest core: injectable Clock (replay mode), per-candle evaluation loop streaming Parquet history through the signal engine, position lifecycle (pending → filled → managed → closed) per v2.1 trade-management rules."*
Prompt (A7): *"Implement `SimulatedBroker` with the v2.1 Part 7.1 pessimistic fill model in full: spread costs, ATR-scaled slippage, gap-through-stop fills at the gapped price, commission and swap. Unit-test from worked examples — each cost component verified against a hand-computed expected fill."*
Accept when: a sample month replays end-to-end producing `signal` rows for 100% of candles; every fill in the test set matches its hand-computed value; no fill is ever better than the pessimistic model allows.

**SESSION A8 · Determinism gate — Gate GA-1 (Week 2).**
Prompt: *"Wire the golden-fixture replay into CI: replay a fixed sample month twice per commit; both runs must produce identical output hashes (signals, trades, equity). Any nondeterminism (dict ordering, float accumulation order, timestamps in output) is a build failure. Document the determinism contract in `docs/determinism.md`."*
Accept when (**Gate GA-1**): two consecutive CI runs, identical hashes; an intentionally injected nondeterminism is caught by the gate.

**SESSION A9 · Walk-forward harness (Week 3).**
Prompt: *"Implement `src/lsb/walkforward/`: rolling 18-month train / 6-month test windows per v2.1, orchestrated across all loaded instruments. Each window runs the deterministic engine, persists one `wf_run` row with full metrics and child `sim_trade` rows, keyed to `config_hash`. Windows are independent — run them in parallel processes."*
Accept when: full window set completes for ≥3 instruments; every wf_run is reproducible (re-run → identical metrics); no window's test span overlaps its own train span.

**SESSION A10 · Verdict report (Week 3).**
Prompt: *"Implement `src/lsb/report/`: per-window and aggregate metrics, equity curves, drawdown profiles, per-window stability analysis (sign and dispersion of results across windows and instruments), and a machine-rendered GO/NO-GO verdict evaluated strictly against the Blueprint v2.1 Part 14 thresholds — the thresholds are read from the spec config, not re-typed. Output: `docs/verdict_report.md` plus rendered charts."*
Accept when: report renders from a real run; verdict logic unit-tested against synthetic pass/fail metric sets; no threshold is hard-coded outside the spec config.

**SESSION A11 · Full run + Gate GA (Week 3, final).**
Prompt: *"Execute the complete walk-forward across all instruments on audited data. Review every anomaly in `docs/anomaly_review.md`: outlier windows, suspicious fills, gate-pass-rate drift across time. Render the Verdict Report. Record the verdict in `docs/decisions/ADR-002-go-no-go.md`."*
**Gate GA — GO/NO-GO. Criteria: Blueprint v2.1 Part 14, unchanged.** Multi-instrument requirement, per-window stability tests, aggregate thresholds — the gate moved from week 7 to week 3; the bar did not move.

**On NO-GO:** stop. No Phase B work begins. The playbook's NO-GO branch: archive the run, write the post-mortem, and apply the parked `docs/decisions/` strategy ideas as *hypotheses for a new Phase A cycle* (another ~3 weeks each), or retire the strategy. A NO-GO at week 3 having cost zero infrastructure is this plan working exactly as designed.

---

## Part 2 — Phase B: Forward Test + Parallel Hardening (Weeks 4–11, conditional on GO)

Two tracks. Track 1 is the launch window; Track 2 is everything the calendar would otherwise waste.

### Track 1 — Forward Test (Sessions B1–B4, then 8 weeks of market time)

**SESSION B1 · MT5 demo bridge (Week 4).**
Prompt: *"Implement the broker bridge per ADR-001: native-Windows MT5, EA-socket fallback. It must conform to the same broker interface `SimulatedBroker` implements — write a conformance test suite that both brokers pass identically. Demo account only; the live-account code path does not exist yet."*
Accept when: conformance suite green on both brokers; order round-trip verified on demo.

**SESSION B2 · Five-state operating machine (Week 4).**
Prompt: *"Implement the reduced operating machine: `IDLE → SCANNING → PENDING_ENTRY → IN_TRADE → HALTED`. Every transition writes a `state_transition` row with reason. HALTED is reachable from every state on: data integrity failure, broker disconnect, daily-loss limit per v2.1 risk parameters, or manual command — and requires manual acknowledgment to exit. Unit-test all legal and illegal transitions."*
Accept when: full transition matrix tested; HALTED behavior verified for all four trigger classes.

**SESSION B3 · Live loop wiring (Week 5).**
Prompt: *"Wire the (unchanged) signal engine and trade management into the live evaluation loop with the Clock in live mode and the MT5 demo bridge. Snapshot logging for 100% of evaluated candles, same `signal` schema as backtest — forward-test data must be directly comparable to walk-forward data. Add a daily integrity audit job (gaps, spread anomalies, clock drift) that transitions to HALTED on failure."*
Accept when: 48-hour dry run on demo completes with 100% candle coverage, zero unexplained gaps, zero unhandled exceptions.

**SESSION B4 · Forward test launch (end of Week 5).**
Launch checklist: config_hash frozen and recorded; thresholds for the week-13 gate written down *before* the test starts; daily audit green for the prior 48h. Then start the clock.

**The freeze rule (weeks 5–13):** no parameter changes, no gate logic changes, no "small fixes" to strategy code for the duration. Defect fixes to infrastructure (logging, reconnects) are allowed with a written entry in `docs/forward_test_log.md`; anything touching signal or trade-management logic restarts the 8-week window. Weekly review is observation only.

### Track 2 — Hardening (Sessions B5–B10, Weeks 5–11, parallel)

Built alongside the running forward test; deployed only after Gate GB. None of this touches the forward-test process.

**SESSION B5 ·** Restore the remaining v2.1 Part 5 tables verbatim (`migrations/002_live.sql`); round-trip tests.
**SESSION B6 ·** Risk and portfolio modules per the v2.1 module spec (the deferred M-modules), test-driven against the v2.1 risk parameters — position sizing, exposure caps, daily-loss enforcement feeding the HALTED trigger.
**SESSION B7 ·** Monitoring and alerting: heartbeats, state-transition alerts, daily digest. Alert on silence, not just on errors.
**SESSION B8 ·** Docker images for the full system; compose file; image build in CI.
**SESSION B9 ·** VPS provisioned and security-hardened — *provisioned, not promoted*. The forward test stays where it is; the VPS runs a shadow deployment against demo to burn in.
**SESSION B10 ·** Two interrogations: (a) the four deleted v2.1 states — each returns only with a written concrete failure scenario it uniquely handles, recorded as an ADR, else it stays deleted; (b) Graphify seeding: `pip install graphifyy` (double y), `graphify install --platform claude`, `/graphify .` at repo root with `/docs` holding the v2.1 blueprint, the v3.0 spec, and this plan; `--postgres` introspection now that the full schema exists; commit `graphify-out/`. From here, `graphify update .` after merges and `graphify affected` before any risk-math change.

### Gate GB — Forward-test verdict (Week 13)

Criteria per v2.1: the forward-test trade distribution compared against walk-forward expectations — distribution comparison, not cherry-picked headline metrics. Trade-count sufficiency applies: if the 8 weeks produced fewer trades than the v2.1 minimum, the verdict is **INSUFFICIENT — extend in whole-week increments until the count gate is met.** Trade count is physics; the calendar serves it, not the reverse.

**On NO-GO at GB:** the VPS is not promoted, no live account is opened, and the divergence analysis (where did live demo behavior depart from the walk-forward distribution — fills? regime? gate pass rates?) becomes the input to a new Phase A cycle. Track 2 work is retained — it was built against the immutable interface and is strategy-agnostic.

---

## Part 3 — Phase C: "Scale" (Week 13+, conditional on GB GO)

**SESSION C1 · Promotion.** Cutover checklist: VPS shadow deployment has ≥2 weeks clean burn-in; monitoring alert paths verified end-to-end (kill the process, confirm the alert arrives); HALTED→manual-acknowledge flow drilled once deliberately. Promote to VPS, still on demo, for one final week. Then — and only on explicit manual decision, never automated — minimum-size live per the v2.1 capital schedule.

**SESSION C2 · The 10% review.** Walk the full §2 delete list from the v3.0 spec. Each candidate returns only with a written justification ADR. Expected returns: possibly some of the four deleted states, possibly nothing. If nothing returns, the deletions were correct; if more than ~10% returns, the Phase A cuts were too shallow — record that for the next project.

**SESSION C3 · Outcome learning activation.** Trade-count-gated exactly per v2.1: the learning loop activates only when live trade count crosses the v2.1 minimum, and updates are batched per the spec, never per-trade. Hiring triggers remain tied to the v2.1 revenue milestones.

---

## Part 4 — Calendar

| Week | Track | Milestone |
|---|---|---|
| 1 | A0–A3 ∥ A4–A5 | Scaffold, config/schema, data audited (≥3 instruments) ∥ gates 1–8 fixture-tested |
| 2 | A6–A8 | Backtest engine, pessimistic fills, **Gate GA-1: determinism in CI** |
| 3 | A9–A11 | Walk-forward, Verdict Report, **Gate GA: GO/NO-GO** |
| 4 | B1–B2 | MT5 demo bridge, 5-state machine |
| 5 | B3–B4 | Live loop, 48h dry run, **forward test launch + freeze** |
| 5–11 | T1: market time ∥ T2: B5–B10 | Forward test running ∥ live tables, risk modules, monitoring, Docker, VPS shadow, state interrogation, Graphify |
| 12–13 | T1 concludes | 8 full weeks of market time complete |
| 13 | — | **Gate GB: forward-test verdict** (extend by whole weeks if trade count insufficient) |
| 13+ | C1–C3 | VPS promotion, 10% review, trade-count-gated learning |

v2.1 reached this point at roughly week 20+. v3.0 reaches it at week 13. The reclaimed ~7–8 weeks came from scope deletion (weeks 1–3 vs 1–7) and parallelization (weeks 5–11 doing double duty). **Weeks taken from validation: zero.**

---

## Part 5 — Risk Register Deltas

The v2.1 register carries forward in full. Three entries are updated or added:

1. **Schedule pressure eroding validation gates** (existing, top risk): mitigation strengthened — both gates' criteria now live in spec config read by the verdict code, so "softening the bar" requires a visible diff to a protected file, reviewable as an ADR.
2. **Parallel-track contamination** (new): Track 2 work accidentally touching the frozen forward-test deployment. Mitigation: forward test runs from a tagged release on isolated infrastructure; Track 2 develops on main; nothing deploys to the forward-test host during the window.
3. **Compression spillover** (new): the momentum of a 3-week GO tempting compression of Phase B's market time. Mitigation: the freeze rule and the trade-count extension rule are written into the gate definition itself, and the launch checklist requires GB thresholds recorded *before* the test starts — pre-registration, so the bar cannot drift after seeing results.

Standing disclaimers unchanged: most retail algorithmic strategies lack durable edge; a GO at either gate is evidence, not a guarantee; nothing here is investment advice; "quantum-inspired" means classical Bayesian belief-state mechanics throughout.

---

## Part 6 — Definition of Done, per phase

**Phase A done:** Verdict Report rendered from a deterministic, multi-instrument walk-forward on audited data, verdict recorded as ADR-002. **Phase B done:** 8+ weeks of frozen forward test meeting the trade-count gate, GB verdict recorded, hardened stack burned in on VPS shadow. **Phase C done:** promoted system live at minimum size per the v2.1 capital schedule, 10% review complete, outcome learning armed behind its trade-count gate.

One sentence to keep on the wall: *the plan gets to every answer faster, and to no answer early.*
