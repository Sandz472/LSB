# Graph Report - .  (2026-06-12)

## Corpus Check
- Corpus is ~2,754 words - fits in a single context window. You may not need a graph.

## Summary
- 64 nodes · 88 edges · 9 communities (7 shown, 2 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 3 edges (avg confidence: 0.85)
- Token cost: 71,954 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Gates and Verdicts|Gates and Verdicts]]
- [[_COMMUNITY_Track 2 Hardening and State Machine|Track 2 Hardening and State Machine]]
- [[_COMMUNITY_Phase A Scaffold, Config and Data Pipeline|Phase A Scaffold, Config and Data Pipeline]]
- [[_COMMUNITY_Signal and Backtest Engine|Signal and Backtest Engine]]
- [[_COMMUNITY_Determinism and Walk-Forward|Determinism and Walk-Forward]]
- [[_COMMUNITY_Source Docs and Phase A Doctrine|Source Docs and Phase A Doctrine]]
- [[_COMMUNITY_Musk Rule and Module Cuts|Musk Rule and Module Cuts]]
- [[_COMMUNITY_Claude Settings Permissions|Claude Settings Permissions]]
- [[_COMMUNITY_Claude Settings Root Node|Claude Settings Root Node]]

## God Nodes (most connected - your core abstractions)
1. `Module Cut: M1-M14 to Five Core Modules` - 7 edges
2. `LSB Implementation Plan v3.0` - 6 edges
3. `Phase A Schema (migration 001_core.sql)` - 6 edges
4. `Track 2: Hardening (Sessions B5-B10)` - 6 edges
5. `Sessions A4-A5: Signal Engine (Eight Gates)` - 5 edges
6. `Sessions A6-A7: Backtest Engine + SimulatedBroker` - 5 edges
7. `Session A9: Walk-Forward Harness` - 5 edges
8. `Physics Rule (Launch Windows)` - 4 edges
9. `Config Hash / config_version System` - 4 edges
10. `wf_run table` - 4 edges

## Surprising Connections (you probably didn't know these)
- `LSB v3.0 Spec and Playbook (PDF)` --semantically_similar_to--> `LSB Implementation Plan v3.0`  [INFERRED] [semantically similar]
  LSB_v3.0_Spec_and_Playbook.pdf → LSB_Implementation_Plan_v3.0.md
- `LSB v3.0 Spec and Playbook (PDF)` --references--> `LSB Master Blueprint v2.1`  [EXTRACTED]
  LSB_v3.0_Spec_and_Playbook.pdf → LSB_Implementation_Plan_v3.0.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Phase A Sessions (A0-A11) Forming the Path to Gate GA** — implementation_plan_v3_0_session_a0_scaffold, implementation_plan_v3_0_session_a1_config_schema, implementation_plan_v3_0_session_a2_data_pipeline_1, implementation_plan_v3_0_session_a3_data_pipeline_n, implementation_plan_v3_0_session_a4_a5_signal_engine, implementation_plan_v3_0_session_a6_a7_backtest_engine, implementation_plan_v3_0_session_a8_determinism_gate, implementation_plan_v3_0_session_a9_walkforward_harness, implementation_plan_v3_0_session_a10_verdict_report, implementation_plan_v3_0_session_a11_full_run_gate_ga, implementation_plan_v3_0_gate_ga [EXTRACTED 1.00]
- **Five Core Modules Surviving Phase A (C1-C5)** — implementation_plan_v3_0_c1_data_pipeline, implementation_plan_v3_0_c2_signal_engine, implementation_plan_v3_0_c3_backtest_engine, implementation_plan_v3_0_c4_walkforward_harness, implementation_plan_v3_0_c5_verdict_report [EXTRACTED 1.00]
- **Track 2 Hardening Sessions (B5-B10) Running Parallel to Forward Test** — implementation_plan_v3_0_session_b5_live_tables, implementation_plan_v3_0_session_b6_risk_portfolio, implementation_plan_v3_0_session_b7_monitoring_alerting, implementation_plan_v3_0_session_b8_docker, implementation_plan_v3_0_session_b9_vps_shadow, implementation_plan_v3_0_session_b10_interrogations, implementation_plan_v3_0_track2_hardening [EXTRACTED 1.00]

## Communities (9 total, 2 thin omitted)

### Community 0 - "Gates and Verdicts"
Cohesion: 0.17
Nodes (15): ADR-002: Go/No-Go Decision, C5: Verdict Report, Config Hash / config_version System, The Freeze Rule (Weeks 5-13), Gate GA: GO/NO-GO (End of Week 3), Gate GB: Forward-Test Verdict (Week 13), GO/NO-GO Thresholds (Blueprint v2.1 Part 14), Phase B: Forward Test + Parallel Hardening (Weeks 4-13) (+7 more)

### Community 1 - "Track 2 Hardening and State Machine"
Cohesion: 0.22
Nodes (11): State Machine Cut: 9 -> 0 (Phase A) -> 5 (Phase B), Session B10: Two Interrogations (Deleted States + Graphify Seeding), Session B2: Five-State Operating Machine, Session B5: Restore Remaining v2.1 Tables (002_live.sql), Session B6: Risk and Portfolio Modules, Session B7: Monitoring and Alerting, Session B8: Docker Images, Session B9: VPS Provisioning + Shadow Deployment (+3 more)

### Community 2 - "Phase A Scaffold, Config and Data Pipeline"
Cohesion: 0.31
Nodes (9): ADR-001: Broker Bridge Decision, candle table, config_version table, Phase A Schema (migration 001_core.sql), Session A0: Scaffold, Session A1: Config System + Schema, Session A2: Data Pipeline, Instrument #1, Session A3: Data Pipeline, Instruments #2-#n (+1 more)

### Community 3 - "Signal and Backtest Engine"
Cohesion: 0.32
Nodes (8): C2: Signal Engine, C3: Backtest Engine, Eight Entry Gates (Strategy Logic), Pessimistic Fill Model (Blueprint v2.1 Part 7.1), Sessions A4-A5: Signal Engine (Eight Gates), Sessions A6-A7: Backtest Engine + SimulatedBroker, Session B1: MT5 Demo Bridge, Session B3: Live Loop Wiring

### Community 4 - "Determinism and Walk-Forward"
Cohesion: 0.40
Nodes (6): Determinism Contract (Golden-Fixture Replay), Gate GA-1: Determinism in CI, Session A8: Determinism Gate (Gate GA-1), Session A9: Walk-Forward Harness, sim_trade table, wf_run table

### Community 5 - "Source Docs and Phase A Doctrine"
Cohesion: 0.40
Nodes (6): Jobs Rule (Scope Deletion), LSB Implementation Plan v3.0, LSB Master Blueprint v2.1, Phase A: Prove (Weeks 1-3), LSB v3.0 Spec and Playbook (PDF), Spec Immutability During Phase A

### Community 6 - "Musk Rule and Module Cuts"
Cohesion: 0.50
Nodes (5): C1: Data Pipeline, C4: Walk-Forward Harness, Module Cut: M1-M14 to Five Core Modules, Musk Rule (Sequencing), Session C2: The 10% Review

## Knowledge Gaps
- **8 isolated node(s):** `allow`, `Claude Settings Local Permissions`, `Phase C: Scale (Week 13+)`, `Session B7: Monitoring and Alerting`, `Session B8: Docker Images` (+3 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **2 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `LSB Implementation Plan v3.0` connect `Source Docs and Phase A Doctrine` to `Gates and Verdicts`, `Determinism and Walk-Forward`, `Musk Rule and Module Cuts`?**
  _High betweenness centrality (0.198) - this node is a cross-community bridge._
- **Why does `Module Cut: M1-M14 to Five Core Modules` connect `Musk Rule and Module Cuts` to `Gates and Verdicts`, `Signal and Backtest Engine`?**
  _High betweenness centrality (0.153) - this node is a cross-community bridge._
- **Why does `Session A9: Walk-Forward Harness` connect `Determinism and Walk-Forward` to `Gates and Verdicts`, `Musk Rule and Module Cuts`?**
  _High betweenness centrality (0.145) - this node is a cross-community bridge._
- **What connects `allow`, `Claude Settings Local Permissions`, `Phase C: Scale (Week 13+)` to the rest of the system?**
  _8 weakly-connected nodes found - possible documentation gaps or missing edges._