# Graph Report - LSB Strategy Bot  (2026-06-13)

## Corpus Check
- 22 files · ~13,352 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 140 nodes · 228 edges · 19 communities (17 shown, 2 thin omitted)
- Extraction: 88% EXTRACTED · 12% INFERRED · 0% AMBIGUOUS · INFERRED: 27 edges (avg confidence: 0.8)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `f37eb7f7`
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
- [[_COMMUNITY_Community 14|Community 14]]
- [[_COMMUNITY_Community 15|Community 15]]
- [[_COMMUNITY_Community 16|Community 16]]
- [[_COMMUNITY_Community 17|Community 17]]
- [[_COMMUNITY_Community 18|Community 18]]

## God Nodes (most connected - your core abstractions)
1. `_candles()` - 13 edges
2. `check_dst_anomalies()` - 10 edges
3. `run_audit()` - 10 edges
4. `fetch_ohlcv()` - 9 edges
5. `_hourly_range()` - 9 edges
6. `load_config()` - 9 edges
7. `Anomaly` - 8 edges
8. `DataFrame` - 8 edges
9. `check_gaps()` - 8 edges
10. `date` - 8 edges

## Surprising Connections (you probably didn't know these)
- `test_check_duplicate_timestamps_clean()` --calls--> `check_duplicate_timestamps()`  [INFERRED]
  tests/unit/test_audit_history.py → scripts/audit_history.py
- `test_check_duplicate_timestamps_flags_repeats()` --calls--> `check_duplicate_timestamps()`  [INFERRED]
  tests/unit/test_audit_history.py → scripts/audit_history.py
- `test_check_gaps_flags_midweek_gap()` --calls--> `check_gaps()`  [INFERRED]
  tests/unit/test_audit_history.py → scripts/audit_history.py
- `test_check_gaps_flags_synthetic_weekend_gap()` --calls--> `check_gaps()`  [INFERRED]
  tests/unit/test_audit_history.py → scripts/audit_history.py
- `test_check_gaps_ignores_fx_weekend_closure()` --calls--> `check_gaps()`  [INFERRED]
  tests/unit/test_audit_history.py → scripts/audit_history.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Phase A Sessions (A0-A11) Forming the Path to Gate GA** — implementation_plan_v3_0_session_a0_scaffold, implementation_plan_v3_0_session_a1_config_schema, implementation_plan_v3_0_session_a2_data_pipeline_1, implementation_plan_v3_0_session_a3_data_pipeline_n, implementation_plan_v3_0_session_a4_a5_signal_engine, implementation_plan_v3_0_session_a6_a7_backtest_engine, implementation_plan_v3_0_session_a8_determinism_gate, implementation_plan_v3_0_session_a9_walkforward_harness, implementation_plan_v3_0_session_a10_verdict_report, implementation_plan_v3_0_session_a11_full_run_gate_ga, implementation_plan_v3_0_gate_ga [EXTRACTED 1.00]
- **Five Core Modules Surviving Phase A (C1-C5)** — implementation_plan_v3_0_c1_data_pipeline, implementation_plan_v3_0_c2_signal_engine, implementation_plan_v3_0_c3_backtest_engine, implementation_plan_v3_0_c4_walkforward_harness, implementation_plan_v3_0_c5_verdict_report [EXTRACTED 1.00]
- **Track 2 Hardening Sessions (B5-B10) Running Parallel to Forward Test** — implementation_plan_v3_0_session_b5_live_tables, implementation_plan_v3_0_session_b6_risk_portfolio, implementation_plan_v3_0_session_b7_monitoring_alerting, implementation_plan_v3_0_session_b8_docker, implementation_plan_v3_0_session_b9_vps_shadow, implementation_plan_v3_0_session_b10_interrogations, implementation_plan_v3_0_track2_hardening [EXTRACTED 1.00]

## Communities (19 total, 2 thin omitted)

### Community 0 - "Gates and Verdicts"
Cohesion: 0.14
Nodes (13): Gate GB — Forward-test verdict (Week 13), LSB Implementation Plan v3.0 — Full Playbook, Part 0 — Operating Doctrine, Part 1 — Phase A: "Prove" (Weeks 1–3, Sessions A0–A11), Part 2 — Phase B: Forward Test + Parallel Hardening (Weeks 4–11, conditional on GO), Part 3 — Phase C: "Scale" (Week 13+, conditional on GB GO), Part 4 — Calendar, Part 5 — Risk Register Deltas (+5 more)

### Community 1 - "Track 2 Hardening and State Machine"
Cohesion: 0.33
Nodes (5): Data pipeline (Sessions A2–A3, combined), Environment decisions, LSB Phase Status, Out of scope for Phase A, Phase A schema

### Community 2 - "Phase A Scaffold, Config and Data Pipeline"
Cohesion: 0.50
Nodes (3): ADR-001: Broker Bridge — Native-Windows MT5 with EA-Socket Fallback, Consequences, Decision

### Community 3 - "Signal and Backtest Engine"
Cohesion: 0.19
Nodes (10): connection, _applied_migrations(), apply_migrations(), get_connection(), Database connection helper and migration runner.  Connection parameters come fro, Apply any migrations/*.sql files not yet recorded in schema_migrations.      Ret, main(), Apply any migrations/*.sql files not yet recorded in schema_migrations.  Usage: (+2 more)

### Community 4 - "Determinism and Walk-Forward"
Cohesion: 0.25
Nodes (16): BrokerCosts, canonical_dict(), canonical_json(), canonical_yaml(), config_hash(), get_or_create_config_version(), InstrumentConfig, load_config() (+8 more)

### Community 12 - "Community 12"
Cohesion: 0.16
Nodes (26): Path, Anomaly, audit_instrument(), check_dst_anomalies(), check_duplicate_timestamps(), check_gaps(), check_spread_outliers(), check_weekend_bars() (+18 more)

### Community 14 - "Community 14"
Cohesion: 0.19
Nodes (20): date, _deriv_candles_batch(), _dukascopy_day_url(), fetch_deriv_h1(), _fetch_dukascopy_day(), fetch_dukascopy_h1(), fetch_ohlcv(), fetch_stooq_h1() (+12 more)

### Community 15 - "Community 15"
Cohesion: 0.32
Nodes (14): _candles(), _hourly_range(), test_check_dst_anomalies_flags_short_midweek_day_near_transition(), test_check_dst_anomalies_ignores_recurring_gap_away_from_transition(), test_check_dst_anomalies_skips_full_day(), test_check_duplicate_timestamps_clean(), test_check_duplicate_timestamps_flags_repeats(), test_check_gaps_flags_midweek_gap() (+6 more)

### Community 16 - "Community 16"
Cohesion: 0.50
Nodes (3): Anomalies, Data Audit Report — BOOM500, Dispositions

### Community 17 - "Community 17"
Cohesion: 0.50
Nodes (3): Anomalies, Data Audit Report — EURUSD, Dispositions

### Community 18 - "Community 18"
Cohesion: 0.50
Nodes (3): Anomalies, Data Audit Report — XAUUSD, Dispositions

## Knowledge Gaps
- **29 isolated node(s):** `Phase A schema`, `Data pipeline (Sessions A2–A3, combined)`, `Out of scope for Phase A`, `Environment decisions`, `Anomalies` (+24 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **2 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `_dst_transition_dates()` connect `Community 12` to `Community 14`?**
  _High betweenness centrality (0.094) - this node is a cross-community bridge._
- **Why does `date` connect `Community 14` to `Community 12`?**
  _High betweenness centrality (0.090) - this node is a cross-community bridge._
- **Why does `check_dst_anomalies()` connect `Community 12` to `Community 15`?**
  _High betweenness centrality (0.039) - this node is a cross-community bridge._
- **Are the 3 inferred relationships involving `check_dst_anomalies()` (e.g. with `test_check_dst_anomalies_flags_short_midweek_day_near_transition()` and `test_check_dst_anomalies_ignores_recurring_gap_away_from_transition()`) actually correct?**
  _`check_dst_anomalies()` has 3 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Phase A schema`, `Data pipeline (Sessions A2–A3, combined)`, `Out of scope for Phase A` to the rest of the system?**
  _47 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Gates and Verdicts` be split into smaller, more focused modules?**
  _Cohesion score 0.14285714285714285 - nodes in this community are weakly interconnected._