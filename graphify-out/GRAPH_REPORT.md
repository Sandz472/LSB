# Graph Report - .  (2026-06-10)

## Corpus Check
- Corpus is ~34 words - fits in a single context window. You may not need a graph.

## Summary
- 56 nodes · 56 edges · 14 communities (6 shown, 8 thin omitted)
- Extraction: 95% EXTRACTED · 5% INFERRED · 0% AMBIGUOUS · INFERRED: 3 edges (avg confidence: 0.85)
- Token cost: 81,514 input · 9,200 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Advisor Seam & Determinism|Advisor Seam & Determinism]]
- [[_COMMUNITY_Backtest & Execution Path|Backtest & Execution Path]]
- [[_COMMUNITY_Engine & Decision Logging|Engine & Decision Logging]]
- [[_COMMUNITY_Decision Warehouse Schema|Decision Warehouse Schema]]
- [[_COMMUNITY_Blueprint & Tooling Docs|Blueprint & Tooling Docs]]
- [[_COMMUNITY_Liquidity Sweep Strategy|Liquidity Sweep Strategy]]
- [[_COMMUNITY_Claude Code Settings|Claude Code Settings]]
- [[_COMMUNITY_Indicators & Trend|Indicators & Trend]]
- [[_COMMUNITY_Trade Management|Trade Management]]
- [[_COMMUNITY_Session & News Filter|Session & News Filter]]
- [[_COMMUNITY_Market Data Ingestion|Market Data Ingestion]]
- [[_COMMUNITY_Structure Detection|Structure Detection]]
- [[_COMMUNITY_Volatility Monitor|Volatility Monitor]]
- [[_COMMUNITY_Risk Computation|Risk Computation]]

## God Nodes (most connected - your core abstractions)
1. `Decision Warehouse (The Moat)` - 5 edges
2. `Stage 3: Bayesian Evidence Engine` - 5 edges
3. `Replay Harness` - 5 edges
4. `market_snapshot Table (Observation Spine)` - 5 edges
5. `Advisor Interface (The Advisor Seam)` - 4 edges
6. `Gate G3: GO/NO-GO at Week 7` - 4 edges
7. `trade_signal Table` - 4 edges
8. `LSB System Requirements v2.0 (Immutable Spec)` - 3 edges
9. `Stage 1: Deterministic Engine` - 3 edges
10. `Stage 4: Quantum-Inspired Hypothesis Engine` - 3 edges

## Surprising Connections (you probably didn't know these)
- `Claude Code Local Permission Allowlist (graphify tooling)` --references--> `Graphify Knowledge Layer`  [INFERRED]
  .claude/settings.local.json → LSB_Master_Blueprint_v2.1.pdf

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Per-Candle Evaluation Sequence (M1 -> M13)** — lsb_master_blueprint_v2_1_m1_market_data_ingestion, lsb_master_blueprint_v2_1_m2_indicator_engine, lsb_master_blueprint_v2_1_m3_trend_analysis, lsb_master_blueprint_v2_1_m4_structure_detection, lsb_master_blueprint_v2_1_m5_liquidity_zone_engine, lsb_master_blueprint_v2_1_m6_volatility_monitor, lsb_master_blueprint_v2_1_m12_session_news_filter, lsb_master_blueprint_v2_1_m7_entry_qualification, lsb_master_blueprint_v2_1_m8_risk_computation, lsb_master_blueprint_v2_1_m9_order_execution, lsb_master_blueprint_v2_1_m13_logging_analytics [EXTRACTED 1.00]
- **Seven Warehouse Tables Form the Decision Warehouse** — lsb_master_blueprint_v2_1_market_snapshot, lsb_master_blueprint_v2_1_trade_signal, lsb_master_blueprint_v2_1_trade_execution, lsb_master_blueprint_v2_1_trade_outcome, lsb_master_blueprint_v2_1_hypothesis_snapshot, lsb_master_blueprint_v2_1_state_transition, lsb_master_blueprint_v2_1_config_version, lsb_master_blueprint_v2_1_decision_warehouse [EXTRACTED 1.00]
- **Intelligence Rail: Implementations of the Advisor Interface** — lsb_master_blueprint_v2_1_advisor_interface, lsb_master_blueprint_v2_1_nulladvisor, lsb_master_blueprint_v2_1_bayesian_evidence_engine, lsb_master_blueprint_v2_1_hypothesis_engine [EXTRACTED 1.00]

## Communities (14 total, 8 thin omitted)

### Community 0 - "Advisor Seam & Determinism"
Cohesion: 0.22
Nodes (10): Advisor Interface (The Advisor Seam), Stage 3: Bayesian Evidence Engine, Determinism Invariant, Eight Entry Gates, 8-Week Demo Forward Test (Non-Compressible), Golden Fixtures (Determinism in CI), Stage 4: Quantum-Inspired Hypothesis Engine, M7 Entry Qualification (+2 more)

### Community 1 - "Backtest & Execution Path"
Cohesion: 0.28
Nodes (9): ADR-001 Broker Bridge Decision (MT5 Native Windows), Backtest-First Sequencing, Gate G3: GO/NO-GO at Week 7, Human Approval Gate (Enforced in Code), M9 Order Execution, Replay Harness, Stage 5: ResearchAgent (Autonomous Research Layer), SimulatedBroker (Pessimistic Fill Model) (+1 more)

### Community 2 - "Engine & Decision Logging"
Cohesion: 0.25
Nodes (8): Stage 2: Analytics & the Data Asset, Decision Warehouse (The Moat), Stage 1: Deterministic Engine, M11 Risk Protection, M13 Logging & Analytics, M14 Alerting, Nine-State Operating Machine, state_transition Table (Audit Trail)

### Community 3 - "Decision Warehouse Schema"
Cohesion: 0.29
Nodes (8): config_hash (Reproducibility Stamp), config_version Table, hypothesis_snapshot Table, market_snapshot Table (Observation Spine), R-multiple (The One Normalised Number), trade_execution Table, trade_outcome Table (Append-Only), trade_signal Table

### Community 4 - "Blueprint & Tooling Docs"
Cohesion: 0.33
Nodes (6): Claude Code Local Permission Allowlist (graphify tooling), LSB Master Blueprint v2.0 (Superseded), Claude Code Implementation Playbook (Part 15), LSB Master Blueprint v2.1, Graphify Knowledge Layer, LSB System Requirements v2.0 (Immutable Spec)

### Community 5 - "Liquidity Sweep Strategy"
Cohesion: 0.50
Nodes (4): Liquidity Sweep, Liquidity Strategy Bot (LSB), M5 Liquidity Zone Engine, Five-Factor Sweep Probability Score (0-100)

## Knowledge Gaps
- **19 isolated node(s):** `allow`, `LSB Master Blueprint v2.0 (Superseded)`, `Liquidity Strategy Bot (LSB)`, `Stage 2: Analytics & the Data Asset`, `8-Week Demo Forward Test (Non-Compressible)` (+14 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **8 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Decision Warehouse (The Moat)` connect `Engine & Decision Logging` to `Advisor Seam & Determinism`, `Backtest & Execution Path`?**
  _High betweenness centrality (0.163) - this node is a cross-community bridge._
- **Why does `Replay Harness` connect `Backtest & Execution Path` to `Advisor Seam & Determinism`, `Decision Warehouse Schema`?**
  _High betweenness centrality (0.161) - this node is a cross-community bridge._
- **Why does `market_snapshot Table (Observation Spine)` connect `Decision Warehouse Schema` to `Backtest & Execution Path`, `Engine & Decision Logging`?**
  _High betweenness centrality (0.142) - this node is a cross-community bridge._
- **What connects `allow`, `LSB Master Blueprint v2.0 (Superseded)`, `Liquidity Strategy Bot (LSB)` to the rest of the system?**
  _19 weakly-connected nodes found - possible documentation gaps or missing edges._