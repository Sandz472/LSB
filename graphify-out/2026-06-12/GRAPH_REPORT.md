# Graph Report - LSB Strategy Bot  (2026-06-12)

## Corpus Check
- 9 files · ~3,334 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 32 nodes · 22 edges · 12 communities (10 shown, 2 thin omitted)
- Extraction: 100% EXTRACTED · 0% INFERRED · 0% AMBIGUOUS
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `912beefa`
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

## God Nodes (most connected - your core abstractions)
1. `LSB Implementation Plan v3.0 — Full Playbook` - 8 edges
2. `Part 2 — Phase B: Forward Test + Parallel Hardening (Weeks 4–11, conditional on GO)` - 4 edges
3. `LSB Phase Status` - 4 edges
4. `Part 1 — Phase A: "Prove" (Weeks 1–3, Sessions A0–A11)` - 3 edges
5. `ADR-001: Broker Bridge — Native-Windows MT5 with EA-Socket Fallback` - 3 edges
6. `permissions` - 2 edges
7. `Part 0 — Operating Doctrine` - 1 edges
8. `Phase A schema (migration `001_core.sql` — 4 tables)` - 1 edges
9. `Sessions` - 1 edges
10. `Track 1 — Forward Test (Sessions B1–B4, then 8 weeks of market time)` - 1 edges

## Surprising Connections (you probably didn't know these)
- None detected - all connections are within the same source files.

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Phase A Sessions (A0-A11) Forming the Path to Gate GA** — implementation_plan_v3_0_session_a0_scaffold, implementation_plan_v3_0_session_a1_config_schema, implementation_plan_v3_0_session_a2_data_pipeline_1, implementation_plan_v3_0_session_a3_data_pipeline_n, implementation_plan_v3_0_session_a4_a5_signal_engine, implementation_plan_v3_0_session_a6_a7_backtest_engine, implementation_plan_v3_0_session_a8_determinism_gate, implementation_plan_v3_0_session_a9_walkforward_harness, implementation_plan_v3_0_session_a10_verdict_report, implementation_plan_v3_0_session_a11_full_run_gate_ga, implementation_plan_v3_0_gate_ga [EXTRACTED 1.00]
- **Five Core Modules Surviving Phase A (C1-C5)** — implementation_plan_v3_0_c1_data_pipeline, implementation_plan_v3_0_c2_signal_engine, implementation_plan_v3_0_c3_backtest_engine, implementation_plan_v3_0_c4_walkforward_harness, implementation_plan_v3_0_c5_verdict_report [EXTRACTED 1.00]
- **Track 2 Hardening Sessions (B5-B10) Running Parallel to Forward Test** — implementation_plan_v3_0_session_b5_live_tables, implementation_plan_v3_0_session_b6_risk_portfolio, implementation_plan_v3_0_session_b7_monitoring_alerting, implementation_plan_v3_0_session_b8_docker, implementation_plan_v3_0_session_b9_vps_shadow, implementation_plan_v3_0_session_b10_interrogations, implementation_plan_v3_0_track2_hardening [EXTRACTED 1.00]

## Communities (12 total, 2 thin omitted)

### Community 0 - "Gates and Verdicts"
Cohesion: 0.29
Nodes (6): LSB Implementation Plan v3.0 — Full Playbook, Part 0 — Operating Doctrine, Part 3 — Phase C: "Scale" (Week 13+, conditional on GB GO), Part 4 — Calendar, Part 5 — Risk Register Deltas, Part 6 — Definition of Done, per phase

### Community 1 - "Track 2 Hardening and State Machine"
Cohesion: 0.40
Nodes (4): Environment decisions, LSB Phase Status, Out of scope for Phase A, Phase A schema

### Community 2 - "Phase A Scaffold, Config and Data Pipeline"
Cohesion: 0.50
Nodes (3): ADR-001: Broker Bridge — Native-Windows MT5 with EA-Socket Fallback, Consequences, Decision

### Community 3 - "Signal and Backtest Engine"
Cohesion: 0.50
Nodes (4): Gate GB — Forward-test verdict (Week 13), Part 2 — Phase B: Forward Test + Parallel Hardening (Weeks 4–11, conditional on GO), Track 1 — Forward Test (Sessions B1–B4, then 8 weeks of market time), Track 2 — Hardening (Sessions B5–B10, Weeks 5–11, parallel)

### Community 4 - "Determinism and Walk-Forward"
Cohesion: 0.67
Nodes (3): Part 1 — Phase A: "Prove" (Weeks 1–3, Sessions A0–A11), Phase A schema (migration `001_core.sql` — 4 tables), Sessions

## Knowledge Gaps
- **17 isolated node(s):** `Part 0 — Operating Doctrine`, `Phase A schema (migration `001_core.sql` — 4 tables)`, `Sessions`, `Track 1 — Forward Test (Sessions B1–B4, then 8 weeks of market time)`, `Track 2 — Hardening (Sessions B5–B10, Weeks 5–11, parallel)` (+12 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **2 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `LSB Implementation Plan v3.0 — Full Playbook` connect `Gates and Verdicts` to `Signal and Backtest Engine`, `Determinism and Walk-Forward`?**
  _High betweenness centrality (0.148) - this node is a cross-community bridge._
- **Why does `Part 2 — Phase B: Forward Test + Parallel Hardening (Weeks 4–11, conditional on GO)` connect `Signal and Backtest Engine` to `Gates and Verdicts`?**
  _High betweenness centrality (0.071) - this node is a cross-community bridge._
- **Why does `Part 1 — Phase A: "Prove" (Weeks 1–3, Sessions A0–A11)` connect `Determinism and Walk-Forward` to `Gates and Verdicts`?**
  _High betweenness centrality (0.049) - this node is a cross-community bridge._
- **What connects `Part 0 — Operating Doctrine`, `Phase A schema (migration `001_core.sql` — 4 tables)`, `Sessions` to the rest of the system?**
  _17 weakly-connected nodes found - possible documentation gaps or missing edges._