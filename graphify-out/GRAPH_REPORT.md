# Graph Report - .  (2026-06-10)

## Corpus Check
- 28 files · ~6,704 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 116 nodes · 94 edges · 45 communities (33 shown, 12 thin omitted)
- Extraction: 90% EXTRACTED · 10% INFERRED · 0% AMBIGUOUS · INFERRED: 9 edges (avg confidence: 0.87)
- Token cost: 68,867 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Governance & Phase Control|Governance & Phase Control]]
- [[_COMMUNITY_Implementation Playbook & Gates|Implementation Playbook & Gates]]
- [[_COMMUNITY_Advisor Intelligence & Validation|Advisor Intelligence & Validation]]
- [[_COMMUNITY_Deterministic Engine Core|Deterministic Engine Core]]
- [[_COMMUNITY_Decision Capture Schema|Decision Capture Schema]]
- [[_COMMUNITY_Broker Bridge Decision|Broker Bridge Decision]]
- [[_COMMUNITY_Liquidity & Risk Qualification|Liquidity & Risk Qualification]]
- [[_COMMUNITY_State Machine & Risk Protection|State Machine & Risk Protection]]
- [[_COMMUNITY_Liquidity Sweep Scoring|Liquidity Sweep Scoring]]
- [[_COMMUNITY_Volatility & Synthetics Config|Volatility & Synthetics Config]]
- [[_COMMUNITY_Triangle Structure Detection|Triangle Structure Detection]]
- [[_COMMUNITY_Trend & Indicator Engines|Trend & Indicator Engines]]
- [[_COMMUNITY_Advisor Seam|Advisor Seam]]
- [[_COMMUNITY_Blueprint Indicators & Trend|Blueprint Indicators & Trend]]
- [[_COMMUNITY_Spec Conversion Script|Spec Conversion Script]]
- [[_COMMUNITY_M12 Session Filter (Spec)|M12 Session Filter (Spec)]]
- [[_COMMUNITY_M13 Logging (Spec)|M13 Logging (Spec)]]
- [[_COMMUNITY_M1 Data Ingestion (Spec)|M1 Data Ingestion (Spec)]]
- [[_COMMUNITY_M10 Trade Management|M10 Trade Management]]
- [[_COMMUNITY_M12 SessionNews Filter|M12 Session/News Filter]]
- [[_COMMUNITY_M1 Market Data Ingestion|M1 Market Data Ingestion]]
- [[_COMMUNITY_M4 Structure Detection|M4 Structure Detection]]
- [[_COMMUNITY_M6 Volatility Monitor|M6 Volatility Monitor]]
- [[_COMMUNITY_M8 Risk Computation|M8 Risk Computation]]

## God Nodes (most connected - your core abstractions)
1. `LSB Governing Instructions (CLAUDE.md)` - 7 edges
2. `M8 Risk Computation Engine` - 6 edges
3. `LSB Master Blueprint v2.1` - 5 edges
4. `LSB System Requirements v2.0 (Immutable Spec)` - 5 edges
5. `Decision Warehouse (The Moat)` - 5 edges
6. `Stage 3: Bayesian Evidence Engine` - 5 edges
7. `Replay Harness` - 5 edges
8. `market_snapshot Table (Observation Spine)` - 5 edges
9. `Advisor Interface (The Advisor Seam)` - 4 edges
10. `Gate G3: GO/NO-GO at Week 7` - 4 edges

## Surprising Connections (you probably didn't know these)
- `ADR-001: Broker Bridge — Native-Windows MT5 with EA-Socket Fallback` --cites--> `LSB Master Blueprint v2.1`  [EXTRACTED]
  docs/decisions/ADR-001-broker-bridge.md → C:/Dev/work/SSR Holdings/Sampu Dynamics/LSB Strategy Bot/docs/LSB_Master_Blueprint_v2.1.pdf
- `Native PostgreSQL 16 Dev Database (no Docker)` --references--> `LSB Master Blueprint v2.1`  [EXTRACTED]
  docs/PHASE_STATUS.md → C:/Dev/work/SSR Holdings/Sampu Dynamics/LSB Strategy Bot/docs/LSB_Master_Blueprint_v2.1.pdf
- `LSB System Requirements v2.0 (markdown conversion)` --references--> `LSB System Requirements v2.0 (Immutable Spec)`  [EXTRACTED]
  docs/LSB_System_Requirements_v2.0.md → C:/Dev/work/SSR Holdings/Sampu Dynamics/LSB Strategy Bot/docs/LSB_Master_Blueprint_v2.1.pdf
- `Advisor Interface (risk-reduce/veto only)` --semantically_similar_to--> `Bayesian Advisor (Phase 5-8)`  [INFERRED] [semantically similar]
  CLAUDE.md → docs/PHASE_STATUS.md
- `LSB Phase Status` --cites--> `LSB Master Blueprint v2.1`  [EXTRACTED]
  docs/PHASE_STATUS.md → C:/Dev/work/SSR Holdings/Sampu Dynamics/LSB Strategy Bot/docs/LSB_Master_Blueprint_v2.1.pdf

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Per-Candle Evaluation Sequence (M1 -> M13)** — lsb_master_blueprint_v2_1_m1_market_data_ingestion, lsb_master_blueprint_v2_1_m2_indicator_engine, lsb_master_blueprint_v2_1_m3_trend_analysis, lsb_master_blueprint_v2_1_m4_structure_detection, lsb_master_blueprint_v2_1_m5_liquidity_zone_engine, lsb_master_blueprint_v2_1_m6_volatility_monitor, lsb_master_blueprint_v2_1_m12_session_news_filter, lsb_master_blueprint_v2_1_m7_entry_qualification, lsb_master_blueprint_v2_1_m8_risk_computation, lsb_master_blueprint_v2_1_m9_order_execution, lsb_master_blueprint_v2_1_m13_logging_analytics [EXTRACTED 1.00]
- **Seven Warehouse Tables Form the Decision Warehouse** — lsb_master_blueprint_v2_1_market_snapshot, lsb_master_blueprint_v2_1_trade_signal, lsb_master_blueprint_v2_1_trade_execution, lsb_master_blueprint_v2_1_trade_outcome, lsb_master_blueprint_v2_1_hypothesis_snapshot, lsb_master_blueprint_v2_1_state_transition, lsb_master_blueprint_v2_1_config_version, lsb_master_blueprint_v2_1_decision_warehouse [EXTRACTED 1.00]
- **Intelligence Rail: Implementations of the Advisor Interface** — lsb_master_blueprint_v2_1_advisor_interface, lsb_master_blueprint_v2_1_nulladvisor, lsb_master_blueprint_v2_1_bayesian_evidence_engine, lsb_master_blueprint_v2_1_hypothesis_engine [EXTRACTED 1.00]
- **Mandatory Per-Candle Data Flow Sequence (Section 2.2)** — docs_lsb_system_requirements_v2_0_m1_market_data_ingestion, docs_lsb_system_requirements_v2_0_m2_indicator_engine, docs_lsb_system_requirements_v2_0_m3_trend_analysis_engine, docs_lsb_system_requirements_v2_0_m4_structure_detection_engine, docs_lsb_system_requirements_v2_0_m5_liquidity_zone_engine, docs_lsb_system_requirements_v2_0_m6_volatility_monitor, docs_lsb_system_requirements_v2_0_m12_session_market_filter, docs_lsb_system_requirements_v2_0_m11_risk_protection_controller, docs_lsb_system_requirements_v2_0_m7_entry_qualification_engine, docs_lsb_system_requirements_v2_0_m8_risk_computation_engine, docs_lsb_system_requirements_v2_0_m9_order_execution_handler, docs_lsb_system_requirements_v2_0_m10_trade_management_engine, docs_lsb_system_requirements_v2_0_m13_logging_analytics_engine [EXTRACTED 1.00]
- **Capital Protection Stack (protect capital first)** — docs_lsb_system_requirements_v2_0_m8_risk_computation_engine, docs_lsb_system_requirements_v2_0_m11_risk_protection_controller, docs_lsb_system_requirements_v2_0_risk_tier_matrix, docs_lsb_system_requirements_v2_0_drawdown_thresholds, docs_lsb_system_requirements_v2_0_structural_stop_loss, docs_lsb_system_requirements_v2_0_atr_state_classification [INFERRED 0.75]
- **Broker Bridge Decision Space for the M9 Interface (ADR-001)** — decisions_adr_001_broker_bridge_native_windows_mt5, decisions_adr_001_broker_bridge_ea_socket_bridge, decisions_adr_001_broker_bridge_wine_on_linux, decisions_adr_001_broker_bridge_simulatedbroker, docs_lsb_system_requirements_v2_0_m9_order_execution_handler [EXTRACTED 1.00]

## Communities (45 total, 12 thin omitted)

### Community 0 - "Governance & Phase Control"
Cohesion: 0.23
Nodes (12): Determinism Law, LSB Governing Instructions (CLAUDE.md), ADR-001: Broker Bridge — Native-Windows MT5 with EA-Socket Fallback, LSB System Requirements v2.0 (markdown conversion), LSB Phase Status, Native PostgreSQL 16 Dev Database (no Docker), Phase 4 — Live Infrastructure (human unlock only), LSB Master Blueprint v2.0 (Superseded) (+4 more)

### Community 1 - "Implementation Playbook & Gates"
Cohesion: 0.22
Nodes (11): ADR-001 Broker Bridge Decision (MT5 Native Windows), Backtest-First Sequencing, Claude Code Implementation Playbook (Part 15), Gate G3: GO/NO-GO at Week 7, Graphify Knowledge Layer, Human Approval Gate (Enforced in Code), M9 Order Execution, Replay Harness (+3 more)

### Community 2 - "Advisor Intelligence & Validation"
Cohesion: 0.25
Nodes (9): Advisor Interface (The Advisor Seam), Stage 3: Bayesian Evidence Engine, Determinism Invariant, 8-Week Demo Forward Test (Non-Compressible), Golden Fixtures (Determinism in CI), Stage 4: Quantum-Inspired Hypothesis Engine, hypothesis_snapshot Table, MarketStateVector (Regime Belief State) (+1 more)

### Community 3 - "Deterministic Engine Core"
Cohesion: 0.22
Nodes (9): Stage 2: Analytics & the Data Asset, Decision Warehouse (The Moat), Stage 1: Deterministic Engine, Eight Entry Gates, M11 Risk Protection, M14 Alerting, M7 Entry Qualification, Nine-State Operating Machine (+1 more)

### Community 4 - "Decision Capture Schema"
Cohesion: 0.29
Nodes (8): config_hash (Reproducibility Stamp), config_version Table, M13 Logging & Analytics, market_snapshot Table (Observation Spine), R-multiple (The One Normalised Number), trade_execution Table, trade_outcome Table (Append-Only), trade_signal Table

### Community 5 - "Broker Bridge Decision"
Cohesion: 0.29
Nodes (7): EA Socket Bridge (Fallback), Native-Windows MT5 Bridge, SimulatedBroker, Wine-on-Linux Bridge (Rejected), M10 Trade Management Engine, M9 Order Execution Handler, Replay Harness

### Community 6 - "Liquidity & Risk Qualification"
Cohesion: 0.29
Nodes (7): Liquidity Sweep, M5 Liquidity Zone Engine, M7 Entry Qualification Engine, M8 Risk Computation Engine, Risk Tier Matrix (1.0% / 0.5% / 0.25% / 0%), Structural Stop Loss Placement, Sweep Probability Score (0-100)

### Community 7 - "State Machine & Risk Protection"
Cohesion: 0.67
Nodes (4): Drawdown Thresholds (daily 3% / weekly 6%), M11 Risk Protection Controller, M14 Alerting & Notification System, Bot Operating State Machine

### Community 8 - "Liquidity Sweep Scoring"
Cohesion: 0.50
Nodes (4): Liquidity Sweep, Liquidity Strategy Bot (LSB), M5 Liquidity Zone Engine, Five-Factor Sweep Probability Score (0-100)

### Community 9 - "Volatility & Synthetics Config"
Cohesion: 0.67
Nodes (3): Deriv Synthetics Per-Instrument Config, ATR State Classification (COMPRESSED/NORMAL/ELEVATED/EXTREME), M6 Volatility Monitor

### Community 10 - "Triangle Structure Detection"
Cohesion: 0.67
Nodes (3): Ascending Triangle (Bearish Setup), Descending Triangle (Bullish Setup), M4 Structure Detection Engine

### Community 11 - "Trend & Indicator Engines"
Cohesion: 0.67
Nodes (3): EMA Hierarchy (21/50/89), M2 Indicator Engine, M3 Trend Analysis Engine

## Knowledge Gaps
- **33 isolated node(s):** `LSB Master Blueprint v2.0 (Superseded)`, `Liquidity Strategy Bot (LSB)`, `Stage 2: Analytics & the Data Asset`, `8-Week Demo Forward Test (Non-Compressible)`, `ADR-001 Broker Bridge Decision (MT5 Native Windows)` (+28 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **12 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `LSB System Requirements v2.0 (Immutable Spec)` connect `Governance & Phase Control` to `Implementation Playbook & Gates`, `Deterministic Engine Core`?**
  _High betweenness centrality (0.176) - this node is a cross-community bridge._
- **Why does `LSB Governing Instructions (CLAUDE.md)` connect `Governance & Phase Control` to `Liquidity & Risk Qualification`, `State Machine & Risk Protection`?**
  _High betweenness centrality (0.161) - this node is a cross-community bridge._
- **Why does `M8 Risk Computation Engine` connect `Liquidity & Risk Qualification` to `Governance & Phase Control`, `Broker Bridge Decision`?**
  _High betweenness centrality (0.100) - this node is a cross-community bridge._
- **What connects `Convert docs/LSB_System_Requirements_v2.0.docx to a markdown sidecar.  graphify`, `LSB Master Blueprint v2.0 (Superseded)`, `Liquidity Strategy Bot (LSB)` to the rest of the system?**
  _40 weakly-connected nodes found - possible documentation gaps or missing edges._