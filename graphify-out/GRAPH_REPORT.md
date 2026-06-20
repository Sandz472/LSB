# Graph Report - .  (2026-06-20)

## Corpus Check
- 25 files · ~9,124 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 132 nodes · 210 edges · 12 communities (8 shown, 4 thin omitted)
- Extraction: 40% EXTRACTED · 14% INFERRED · 0% AMBIGUOUS · INFERRED: 29 edges (avg confidence: 0.72)
- Token cost: 19,280 input · 2,723 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Config Hashing & Tests|Config Hashing & Tests]]
- [[_COMMUNITY_§8.1 Gate Logic|§8.1 Gate Logic]]
- [[_COMMUNITY_Phase-A Data & Modules|Phase-A Data & Modules]]
- [[_COMMUNITY_Config Loader & Models|Config Loader & Models]]
- [[_COMMUNITY_Verdict & Phase Gating|Verdict & Phase Gating]]
- [[_COMMUNITY_Project Docs & ADRs|Project Docs & ADRs]]
- [[_COMMUNITY_Governing Specs & Rules|Governing Specs & Rules]]
- [[_COMMUNITY_A1 Schema Design|A1 Schema Design]]
- [[_COMMUNITY_Smoke Test|Smoke Test]]
- [[_COMMUNITY_Package Init|Package Init]]
- [[_COMMUNITY_CI Workflow|CI Workflow]]
- [[_COMMUNITY_LSB Package Root|LSB Package Root]]

## God Nodes (most connected - your core abstractions)
1. `load_instrument()` - 15 edges
2. `Decimal` - 12 edges
3. `load_spec()` - 11 edges
4. `InstrumentConfig` - 8 edges
5. `SpecConfig` - 8 edges
6. `LSB Canonical Gate Specification` - 8 edges
7. `config_hash()` - 7 edges
8. `_d()` - 5 edges
9. `test_round_trip()` - 5 edges
10. `Implementation Plan — A1: Config System + Core Schema` - 5 edges

## Surprising Connections (you probably didn't know these)
- `Implementation Plan — A1: Config System + Core Schema` --references--> `config_hash function`  [EXTRACTED]
  plan-a1-config-schema.html → src/lsb/config/hashing.py
- `Implementation Plan — A1: Config System + Core Schema` --references--> `InstrumentConfig Dataclass`  [EXTRACTED]
  plan-a1-config-schema.html → src/lsb/config/models.py
- `Implementation Plan — A1: Config System + Core Schema` --references--> `SpecConfig Dataclass`  [EXTRACTED]
  plan-a1-config-schema.html → src/lsb/config/models.py
- `Implementation Plan — A1: Config System + Core Schema` --references--> `001_core.sql DDL`  [EXTRACTED]
  plan-a1-config-schema.html → migrations/001_core.sql
- `test_all_loadable_instruments_load()` --calls--> `load_instrument()`  [INFERRED]
  tests/test_config.py → src/lsb/config/loader.py

## Import Cycles
- 1-file cycle: `src/lsb/config/loader.py -> src/lsb/config/loader.py`
- 2-file cycle: `src/lsb/config/loader.py -> src/lsb/config/models.py -> src/lsb/config/loader.py`

## Communities (12 total, 4 thin omitted)

### Community 0 - "Config Hashing & Tests"
Cohesion: 0.11
Nodes (24): _canonical_value(), config_hash(), Deterministic sha256 config_hash.  Invariant: same field values → same hex diges, Return the sha256 hex digest of the canonical JSON of *cfg*., Decimal, A1 config system tests.  Covers: load, determinism, key-order invariance, float, config_hash must not depend on JSON key order.      asdict() always yields field, config_hash must be identical for numerically equal Decimal values     with diff (+16 more)

### Community 1 - "§8.1 Gate Logic"
Cohesion: 0.14
Nodes (22): ATR EXTREME → No-Trade Pre-filter (§4.2.2/§9.3), Block HIGH (sweep target), Spec Defect: §4.3 vs §8.1 rejection geometry, Spec Ambiguity: D1 vs H1 trend timeframe, Flat Tolerance 0.15%, Gate 1 — Trend State, Gate 2 — Structure, Gate 3 — Liquidity Sweep (+14 more)

### Community 2 - "Phase-A Data & Modules"
Cohesion: 0.18
Nodes (18): config_hash, Determinism Law, GA-1 Determinism Gate (A8 CI), EURUSD, GBPUSD, XAUUSD, 001_core.sql, C1 Data (+10 more)

### Community 3 - "Config Loader & Models"
Cohesion: 0.24
Nodes (15): LSB config subsystem — public re-exports., _d(), load_instrument(), load_spec(), YAML → frozen dataclass loaders.  All numeric values are coerced to Decimal on l, Parse *raw* as Decimal; raise ValueError with a helpful message on failure., Load and validate a per-instrument YAML file., Load and validate the spec/GA-threshold YAML file. (+7 more)

### Community 4 - "Verdict & Phase Gating"
Cohesion: 0.15
Nodes (15): ADR-001 broker bridge, ADR-002 go/no-go, Spec Defect: §17.1 minimum trade count undefined, §17.1 GA Threshold Bar, Gate GA, HALT-HUMAN, C5 Verdict, Phase B (wk 4–13) (+7 more)

### Community 5 - "Project Docs & ADRs"
Cohesion: 0.18
Nodes (12): ADR-001 — Broker Bridge: native-Windows MT5, ADR-003 — Gate 1 macro-trend timeframe: Daily (D1), ADR-004 — Bull rejection geometry: lower-wick hammer, BTCUSD Configuration, LSB Build Playbook, LSB Governing Instructions, EURUSD Configuration, LSB Canonical Gate Specification (+4 more)

### Community 6 - "Governing Specs & Rules"
Cohesion: 0.32
Nodes (8): Master Blueprint v2.1, BUILD_PLAYBOOK.md, CLAUDE.md (governing), .claude/settings.local.json, graphify knowledge base, Redesign v3.0, Rule 1 — Spec Immutability, System Requirements v2.0

### Community 7 - "A1 Schema Design"
Cohesion: 0.47
Nodes (6): ADR-002 — Phase-A core schema design, config_hash function, InstrumentConfig Dataclass, SpecConfig Dataclass, Implementation Plan — A1: Config System + Core Schema, 001_core.sql DDL

## Knowledge Gaps
- **9 isolated node(s):** `lsb`, `LSB Phase Status`, `CI Workflow`, `BTCUSD Configuration`, `EURUSD Configuration` (+4 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **4 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `load_instrument()` connect `Config Loader & Models` to `Config Hashing & Tests`?**
  _High betweenness centrality (0.031) - this node is a cross-community bridge._
- **Why does `Decimal` connect `Config Hashing & Tests` to `Config Loader & Models`?**
  _High betweenness centrality (0.017) - this node is a cross-community bridge._
- **Why does `load_spec()` connect `Config Loader & Models` to `Config Hashing & Tests`?**
  _High betweenness centrality (0.013) - this node is a cross-community bridge._
- **Are the 7 inferred relationships involving `load_instrument()` (e.g. with `test_all_loadable_instruments_load()` and `test_determinism()`) actually correct?**
  _`load_instrument()` has 7 INFERRED edges - model-reasoned connections that need verification._
- **Are the 7 inferred relationships involving `Decimal` (e.g. with `InstrumentConfig` and `SpecConfig`) actually correct?**
  _`Decimal` has 7 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `load_spec()` (e.g. with `test_owner_decision_slots_validated()` and `test_spec_config_frozen()`) actually correct?**
  _`load_spec()` has 3 INFERRED edges - model-reasoned connections that need verification._
- **What connects `lsb`, `LSB — spec-faithful trading-strategy validation system (Phase A scaffold).  Stra`, `LSB config subsystem — public re-exports.` to the rest of the system?**
  _27 weakly-connected nodes found - possible documentation gaps or missing edges._