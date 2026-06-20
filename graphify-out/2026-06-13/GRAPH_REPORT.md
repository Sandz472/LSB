# Graph Report - LSB Strategy Bot  (2026-06-12)

## Corpus Check
- 16 files · ~6,088 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 64 nodes · 76 edges · 14 communities (12 shown, 2 thin omitted)
- Extraction: 82% EXTRACTED · 18% INFERRED · 0% AMBIGUOUS · INFERRED: 14 edges (avg confidence: 0.8)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `314d3c7d`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- [[_COMMUNITY_Gates and Verdicts|Gates and Verdicts]]
- [[_COMMUNITY_Track 2 Hardening and State Machine|Track 2 Hardening and State Machine]]
- [[_COMMUNITY_Phase A Scaffold, Config and Data Pipeline|Phase A Scaffold, Config and Data Pipeline]]
- [[_COMMUNITY_Signal and Backtest Engine|Signal and Backtest Engine]]
- [[_COMMUNITY_Determinism and Walk-Forward|Determinism and Walk-Forward]]
- [[_COMMUNITY_Claude Settings Permissions|Claude Settings Permissions]]
- [[_COMMUNITY_Claude Settings Root Node|Claude Settings Root Node]]
- [[_COMMUNITY_Community 12|Community 12]]

## God Nodes (most connected - your core abstractions)
1. `load_config()` - 9 edges
2. `config_hash()` - 8 edges
3. `LSB Implementation Plan v3.0 — Full Playbook` - 8 edges
4. `InstrumentConfig` - 7 edges
5. `get_or_create_config_version()` - 6 edges
6. `apply_migrations()` - 6 edges
7. `canonical_yaml()` - 5 edges
8. `test_insert_or_get_is_idempotent()` - 5 edges
9. `LSB Phase Status` - 4 edges
10. `canonical_dict()` - 4 edges

## Surprising Connections (you probably didn't know these)
- `test_insert_or_get_is_idempotent()` --calls--> `canonical_yaml()`  [INFERRED]
  tests/unit/test_config.py → src/lsb/data/config.py
- `test_insert_or_get_is_idempotent()` --calls--> `get_or_create_config_version()`  [INFERRED]
  tests/unit/test_config.py → src/lsb/data/config.py
- `main()` --calls--> `apply_migrations()`  [INFERRED]
  scripts/apply_migrations.py → src/lsb/data/db.py
- `main()` --calls--> `get_connection()`  [INFERRED]
  scripts/apply_migrations.py → src/lsb/data/db.py
- `test_config_hash_is_sha256_hex()` --calls--> `load_config()`  [INFERRED]
  tests/unit/test_config.py → src/lsb/data/config.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Phase A Sessions (A0-A11) Forming the Path to Gate GA** — implementation_plan_v3_0_session_a0_scaffold, implementation_plan_v3_0_session_a1_config_schema, implementation_plan_v3_0_session_a2_data_pipeline_1, implementation_plan_v3_0_session_a3_data_pipeline_n, implementation_plan_v3_0_session_a4_a5_signal_engine, implementation_plan_v3_0_session_a6_a7_backtest_engine, implementation_plan_v3_0_session_a8_determinism_gate, implementation_plan_v3_0_session_a9_walkforward_harness, implementation_plan_v3_0_session_a10_verdict_report, implementation_plan_v3_0_session_a11_full_run_gate_ga, implementation_plan_v3_0_gate_ga [EXTRACTED 1.00]
- **Five Core Modules Surviving Phase A (C1-C5)** — implementation_plan_v3_0_c1_data_pipeline, implementation_plan_v3_0_c2_signal_engine, implementation_plan_v3_0_c3_backtest_engine, implementation_plan_v3_0_c4_walkforward_harness, implementation_plan_v3_0_c5_verdict_report [EXTRACTED 1.00]
- **Track 2 Hardening Sessions (B5-B10) Running Parallel to Forward Test** — implementation_plan_v3_0_session_b5_live_tables, implementation_plan_v3_0_session_b6_risk_portfolio, implementation_plan_v3_0_session_b7_monitoring_alerting, implementation_plan_v3_0_session_b8_docker, implementation_plan_v3_0_session_b9_vps_shadow, implementation_plan_v3_0_session_b10_interrogations, implementation_plan_v3_0_track2_hardening [EXTRACTED 1.00]

## Communities (14 total, 2 thin omitted)

### Community 0 - "Gates and Verdicts"
Cohesion: 0.14
Nodes (13): Gate GB — Forward-test verdict (Week 13), LSB Implementation Plan v3.0 — Full Playbook, Part 0 — Operating Doctrine, Part 1 — Phase A: "Prove" (Weeks 1–3, Sessions A0–A11), Part 2 — Phase B: Forward Test + Parallel Hardening (Weeks 4–11, conditional on GO), Part 3 — Phase C: "Scale" (Week 13+, conditional on GB GO), Part 4 — Calendar, Part 5 — Risk Register Deltas (+5 more)

### Community 1 - "Track 2 Hardening and State Machine"
Cohesion: 0.40
Nodes (4): Environment decisions, LSB Phase Status, Out of scope for Phase A, Phase A schema

### Community 2 - "Phase A Scaffold, Config and Data Pipeline"
Cohesion: 0.50
Nodes (3): ADR-001: Broker Bridge — Native-Windows MT5 with EA-Socket Fallback, Consequences, Decision

### Community 3 - "Signal and Backtest Engine"
Cohesion: 0.19
Nodes (10): connection, _applied_migrations(), apply_migrations(), get_connection(), Database connection helper and migration runner.  Connection parameters come fro, Apply any migrations/*.sql files not yet recorded in schema_migrations.      Ret, main(), Apply any migrations/*.sql files not yet recorded in schema_migrations.  Usage: (+2 more)

### Community 4 - "Determinism and Walk-Forward"
Cohesion: 0.33
Nodes (9): BrokerCosts, config_hash(), load_config(), WalkForwardWindow, Path, test_config_hash_is_sha256_hex(), test_different_configs_hash_differently(), test_identical_configs_hash_identically() (+1 more)

### Community 12 - "Community 12"
Cohesion: 0.50
Nodes (7): canonical_dict(), canonical_json(), canonical_yaml(), get_or_create_config_version(), InstrumentConfig, Instrument config: YAML -> frozen dataclass -> canonical form -> config_hash.  I, Insert-or-get this config's row in config_version. Returns config_hash.

## Knowledge Gaps
- **20 isolated node(s):** `Phase A schema`, `Out of scope for Phase A`, `Environment decisions`, `Path`, `connection` (+15 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **2 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `load_config()` connect `Determinism and Walk-Forward` to `Community 12`?**
  _High betweenness centrality (0.020) - this node is a cross-community bridge._
- **Are the 4 inferred relationships involving `load_config()` (e.g. with `test_config_hash_is_sha256_hex()` and `test_different_configs_hash_differently()`) actually correct?**
  _`load_config()` has 4 INFERRED edges - model-reasoned connections that need verification._
- **Are the 4 inferred relationships involving `config_hash()` (e.g. with `test_config_hash_is_sha256_hex()` and `test_different_configs_hash_differently()`) actually correct?**
  _`config_hash()` has 4 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Phase A schema`, `Out of scope for Phase A`, `Environment decisions` to the rest of the system?**
  _25 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Gates and Verdicts` be split into smaller, more focused modules?**
  _Cohesion score 0.14285714285714285 - nodes in this community are weakly interconnected._