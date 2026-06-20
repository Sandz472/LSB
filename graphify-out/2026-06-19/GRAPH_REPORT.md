# Graph Report - .  (2026-06-19)

## Corpus Check
- 63 files · ~0 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 800 nodes · 1754 edges · 36 communities (33 shown, 3 thin omitted)
- Extraction: 66% EXTRACTED · 34% INFERRED · 0% AMBIGUOUS · INFERRED: 593 edges (avg confidence: 0.65)
- Token cost: 71,954 input · 0 output

## Graph Freshness
- Built from commit: `7e543f8c`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- [[_COMMUNITY_ADR-004 Rising-Lows Fix|ADR-004 Rising-Lows Fix]]
- [[_COMMUNITY_ADR-005 Flat-Leg Calibration|ADR-005 Flat-Leg Calibration]]
- [[_COMMUNITY_Config & Calibration Scripts|Config & Calibration Scripts]]
- [[_COMMUNITY_Structure Engine & Gates 1,3,4|Structure Engine & Gates 1,3,4]]
- [[_COMMUNITY_Structure Real-Data Guard|Structure Real-Data Guard]]
- [[_COMMUNITY_Phase A Status Tracker|Phase A Status Tracker]]
- [[_COMMUNITY_Triangle Detection (M4)|Triangle Detection (M4)]]
- [[_COMMUNITY_Position Book & Broker|Position Book & Broker]]
- [[_COMMUNITY_ADR-003 Pyramiding|ADR-003 Pyramiding]]
- [[_COMMUNITY_Backtest Runner & Data Load|Backtest Runner & Data Load]]
- [[_COMMUNITY_Trade Management (Sec 11)|Trade Management (Sec 11)]]
- [[_COMMUNITY_Pyramiding Policy Tests|Pyramiding Policy Tests]]
- [[_COMMUNITY_Signal Engine & Gates 2,5-8|Signal Engine & Gates 2,5-8]]
- [[_COMMUNITY_History Fetching & Sources|History Fetching & Sources]]
- [[_COMMUNITY_Risk & RR (Gate 8)|Risk & R:R (Gate 8)]]
- [[_COMMUNITY_Session Classifier|Session Classifier]]
- [[_COMMUNITY_Trend State (M3)|Trend State (M3)]]
- [[_COMMUNITY_Candle Type Definition|Candle Type Definition]]
- [[_COMMUNITY_Indicator Engine (M2)|Indicator Engine (M2)]]
- [[_COMMUNITY_Signal Persistence|Signal Persistence]]
- [[_COMMUNITY_H1 to H4 Resampling|H1 to H4 Resampling]]
- [[_COMMUNITY_BTCUSD Audit Report|BTCUSD Audit Report]]
- [[_COMMUNITY_ADR-002 BTCUSD Substitution|ADR-002 BTCUSD Substitution]]
- [[_COMMUNITY_Data Audit & Anomalies|Data Audit & Anomalies]]
- [[_COMMUNITY_EURUSD Audit Report|EURUSD Audit Report]]
- [[_COMMUNITY_XAUUSD Audit Report|XAUUSD Audit Report]]
- [[_COMMUNITY_Database & Migrations|Database & Migrations]]
- [[_COMMUNITY_Implementation Plan v3.0|Implementation Plan v3.0]]
- [[_COMMUNITY_ADR-001 Broker Bridge|ADR-001 Broker Bridge]]
- [[_COMMUNITY_Claude Settings Permissions|Claude Settings Permissions]]
- [[_COMMUNITY_Claude Settings Node|Claude Settings Node]]

## God Nodes (most connected - your core abstractions)
1. `SignalParams` - 49 edges
2. `evaluate()` - 36 edges
3. `InstrumentConfig` - 33 edges
4. `load_config()` - 29 edges
5. `_params()` - 27 edges
6. `StructureState` - 26 edges
7. `TestScoreComponents` - 25 edges
8. `_ts()` - 25 edges
9. `ATRState` - 24 edges
10. `Session` - 22 edges

## Surprising Connections (you probably didn't know these)
- `load_config()` --calls--> `eurusd_config()`  [INFERRED]
  src/lsb/data/config.py → tests/integration/test_replay_month.py
- `load_config()` --calls--> `btcusd()`  [INFERRED]
  src/lsb/data/config.py → tests/integration/test_structure_realdata.py
- `load_config()` --calls--> `eurusd()`  [INFERRED]
  src/lsb/data/config.py → tests/integration/test_structure_realdata.py
- `load_config()` --calls--> `xauusd()`  [INFERRED]
  src/lsb/data/config.py → tests/integration/test_structure_realdata.py
- `BrokerCosts` --uses--> `TestDetectSweep`  [INFERRED]
  src/lsb/data/config.py → tests/unit/test_liquidity.py

## Import Cycles
- 1-file cycle: `src/lsb/signals/session.py -> src/lsb/signals/session.py`
- 1-file cycle: `tests/unit/test_engine_properties.py -> tests/unit/test_engine_properties.py`
- 1-file cycle: `tests/unit/test_session.py -> tests/unit/test_session.py`
- 1-file cycle: `tests/unit/test_trend.py -> tests/unit/test_trend.py`
- 1-file cycle: `src/lsb/signals/resample.py -> src/lsb/signals/resample.py`

## Hyperedges (group relationships)
- **Phase A Sessions (A0-A11) Forming the Path to Gate GA** — implementation_plan_v3_0_session_a0_scaffold, implementation_plan_v3_0_session_a1_config_schema, implementation_plan_v3_0_session_a2_data_pipeline_1, implementation_plan_v3_0_session_a3_data_pipeline_n, implementation_plan_v3_0_session_a4_a5_signal_engine, implementation_plan_v3_0_session_a6_a7_backtest_engine, implementation_plan_v3_0_session_a8_determinism_gate, implementation_plan_v3_0_session_a9_walkforward_harness, implementation_plan_v3_0_session_a10_verdict_report, implementation_plan_v3_0_session_a11_full_run_gate_ga, implementation_plan_v3_0_gate_ga [EXTRACTED 1.00]
- **Five Core Modules Surviving Phase A (C1-C5)** — implementation_plan_v3_0_c1_data_pipeline, implementation_plan_v3_0_c2_signal_engine, implementation_plan_v3_0_c3_backtest_engine, implementation_plan_v3_0_c4_walkforward_harness, implementation_plan_v3_0_c5_verdict_report [EXTRACTED 1.00]
- **Track 2 Hardening Sessions (B5-B10) Running Parallel to Forward Test** — implementation_plan_v3_0_session_b5_live_tables, implementation_plan_v3_0_session_b6_risk_portfolio, implementation_plan_v3_0_session_b7_monitoring_alerting, implementation_plan_v3_0_session_b8_docker, implementation_plan_v3_0_session_b9_vps_shadow, implementation_plan_v3_0_session_b10_interrogations, implementation_plan_v3_0_track2_hardening [EXTRACTED 1.00]

## Communities (36 total, 3 thin omitted)

### Community 33 - "ADR-004 Rising-Lows Fix"
Cohesion: 0.20
Nodes (9): ADR-004 — Structure Gate: Rising-Lows Leg Correction, Context, Root cause, Spec divergence, Decision, Interpretation of "minimum 2 higher lows", New config (schema_version 5 → 6), Consequences (+1 more)

### Community 35 - "ADR-005 Flat-Leg Calibration"
Cohesion: 0.25
Nodes (7): ADR-005 — Flat-Leg Tolerance: Per-Instrument Calibration, Context, Why ATR-relative normalization was rejected, Decision, Why per-instrument is appropriate, New config (schema_version 6 → 7), Consequences

### Community 4 - "Config & Calibration Scripts"
Cohesion: 0.06
Nodes (48): collect(), main(), Calibration: pick a single shared k_atr for the ATR-relative flat leg.  Pre-comp, analyze(), main(), Diagnostic: where does the structure detector fall out, per instrument?  Isolate, collect(), main() (+40 more)

### Community 20 - "Structure Engine & Gates 1,3,4"
Cohesion: 0.06
Nodes (55): InstrumentConfig, StructureState, Enum, StructureResult, M4 — Structure Detection Engine.  Detects ascending and descending triangles on, SignalResult, Candle, GateResult (+47 more)

### Community 32 - "Structure Real-Data Guard"
Cohesion: 0.18
Nodes (15): eurusd(), xauusd(), btcusd(), _detect_at(), _confirmed_in_history(), test_ascending_triangle_reachable(), test_descending_triangle_reachable(), test_confirmed_triangles_exist_in_history() (+7 more)

### Community 1 - "Phase A Status Tracker"
Cohesion: 0.25
Nodes (7): LSB Phase Status, Phase A schema, Signal engine (Sessions A4–A5), Backtest engine (Session A6), Data pipeline (Sessions A2–A3, combined), Out of scope for Phase A, Environment decisions

### Community 15 - "Triangle Detection (M4)"
Cohesion: 0.07
Nodes (31): _swing_highs(), Candle, _swing_lows(), _rising_lows(), _falling_highs(), _compression_ok(), _linear_regression(), _apex_proximity() (+23 more)

### Community 23 - "Position Book & Broker"
Cohesion: 0.06
Nodes (52): SignalParams, PositionBook, Position, PositionBook — manages concurrent legs per instrument.  Implements the ADR-003 p, Return True if another leg may be opened per ADR-003 policy., Flatten all active legs (book-wide defensive exit)., Legs that are filled or in managed state (not pending or closed)., Legs that were just filled this bar (state == FILLED, fill_bar == current). (+44 more)

### Community 31 - "ADR-003 Pyramiding"
Cohesion: 0.20
Nodes (9): ADR-003 — Pyramiding as a Core Strategy Feature, Context, Decision, ADR-003 Default Policy, Winner-only rule, Per-leg management, Book-wide exits (§11.4), Partial exits and P&L (+1 more)

### Community 28 - "Backtest Runner & Data Load"
Cohesion: 0.09
Nodes (25): _parse_args(), _run_instrument(), main(), CLI entry point for the Phase A backtest engine.  Usage:     python scripts/run_, load_parquet(), Path, Candle, history_path() (+17 more)

### Community 25 - "Trade Management (Sec 11)"
Cohesion: 0.10
Nodes (39): stop_hit(), Position, Candle, target_hit(), apply_breakeven(), apply_ema_trail(), record_partial_exit(), order_expired() (+31 more)

### Community 30 - "Pyramiding Policy Tests"
Cohesion: 0.37
Nodes (12): _params(), _pos(), test_first_leg_always_allowed(), test_second_leg_blocked_when_disabled(), test_max_legs_cap(), test_same_direction_blocks_opposing(), test_same_direction_disabled_allows_opposing(), test_winner_only_blocked_when_not_in_profit() (+4 more)

### Community 22 - "Signal Engine & Gates 2,5-8"
Cohesion: 0.07
Nodes (25): Signal engine — evaluates all eight M7 entry gates for a candle window.  Accepts, gate_2_structure_present(), StructureResult, gate_5_candle_confirmation(), CandleType, SignalParams, gate_6_volatility_acceptable(), ATRState (+17 more)

### Community 14 - "History Fetching & Sources"
Cohesion: 0.18
Nodes (22): Session, _dukascopy_day_url(), date, _parse_dukascopy_day(), _fetch_dukascopy_day(), fetch_dukascopy_h1(), DataFrame, _solve_stooq_pow() (+14 more)

### Community 27 - "Risk & R:R (Gate 8)"
Cohesion: 0.15
Nodes (17): structural_stop(), Candle, ATRState, SignalParams, rr_target(), _nearest_liquidity_pool(), Pure R:R and structural-stop helpers for Gate 8.  No position sizing, no account, Structural stop level per §9.1.      Bear (short): stop = rejection_candle.high (+9 more)

### Community 26 - "Session Classifier"
Cohesion: 0.13
Nodes (12): Session, session_of(), datetime, minutes_to_edge(), Session classifier — pure UTC-band derivation, no clock reads.  Standard FX wind, Classify a UTC timestamp into an FX trading session., Minutes to the nearest boundary of the current session (open or close).      Ret, _ts() (+4 more)

### Community 29 - "Trend State (M3)"
Cohesion: 0.11
Nodes (23): _ts(), datetime, _candle(), _candles_trending_up(), _candles_trending_down(), _candles_flat(), TestTrendStateBullish, TestTrendStateBearish (+15 more)

### Community 21 - "Indicator Engine (M2)"
Cohesion: 0.06
Nodes (31): SlopeState, CandleType, ema_series(), atr_series(), Candle, slope_state(), atr_baseline(), classify_atr_state() (+23 more)

### Community 34 - "Signal Persistence"
Cohesion: 0.19
Nodes (11): _gate_results_json(), SignalResult, write_signal_row(), Persist SignalResult to the `signal` table.  This is the only module with I/O in, Serialise the gate evaluation as the JSONB gate_results payload., Insert a signal row for `result`. Returns the row id (or None on conflict)., _candle(), _build_result() (+3 more)

### Community 24 - "H1 to H4 Resampling"
Cohesion: 0.17
Nodes (11): _h4_bar_start(), datetime, resample_h1_to_h4(), Candle, H1 → H4 OHLCV resampling.  H4 boundaries are pinned to fixed UTC hours: 00, 04,, Return the UTC start of the H4 bar that contains `ts`., Aggregate H1 candles into complete H4 candles.      OHLC aggregation: O = first,, _h1() (+3 more)

### Community 19 - "BTCUSD Audit Report"
Cohesion: 0.50
Nodes (3): Data Audit Report — BTCUSD, Anomalies, Dispositions

### Community 16 - "ADR-002 BTCUSD Substitution"
Cohesion: 0.29
Nodes (6): ADR-002: Instrument Substitution — BTCUSD replaces BOOM500, Context, Options considered, Decision, BOOM500 disposition, Consequences

### Community 12 - "Data Audit & Anomalies"
Cohesion: 0.12
Nodes (39): Anomaly, check_duplicate_timestamps(), DataFrame, _is_expected_fx_closure(), Timestamp, check_gaps(), check_weekend_bars(), _dst_transition_dates() (+31 more)

### Community 17 - "EURUSD Audit Report"
Cohesion: 0.50
Nodes (3): Data Audit Report — EURUSD, Anomalies, Dispositions

### Community 18 - "XAUUSD Audit Report"
Cohesion: 0.50
Nodes (3): Data Audit Report — XAUUSD, Anomalies, Dispositions

### Community 3 - "Database & Migrations"
Cohesion: 0.19
Nodes (10): main(), Apply any migrations/*.sql files not yet recorded in schema_migrations.  Usage:, get_connection(), connection, _applied_migrations(), apply_migrations(), Path, Database connection helper and migration runner.  Connection parameters come fro (+2 more)

### Community 0 - "Implementation Plan v3.0"
Cohesion: 0.14
Nodes (13): LSB Implementation Plan v3.0 — Full Playbook, Part 0 — Operating Doctrine, Part 1 — Phase A: "Prove" (Weeks 1–3, Sessions A0–A11), Phase A schema (migration `001_core.sql` — 4 tables), Sessions, Part 2 — Phase B: Forward Test + Parallel Hardening (Weeks 4–11, conditional on GO), Track 1 — Forward Test (Sessions B1–B4, then 8 weeks of market time), Track 2 — Hardening (Sessions B5–B10, Weeks 5–11, parallel) (+5 more)

### Community 2 - "ADR-001 Broker Bridge"
Cohesion: 0.50
Nodes (3): ADR-001: Broker Bridge — Native-Windows MT5 with EA-Socket Fallback, Decision, Consequences

## Knowledge Gaps
- **57 isolated node(s):** `Root cause`, `Spec divergence`, `Interpretation of "minimum 2 higher lows"`, `New config (schema_version 5 → 6)`, `Consequences` (+52 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **3 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `evaluate()` connect `Config & Calibration Scripts` to `Signal Persistence`, `Triangle Detection (M4)`, `Structure Engine & Gates 1,3,4`, `Indicator Engine (M2)`, `Signal Engine & Gates 2,5-8`, `Position Book & Broker`, `H1 to H4 Resampling`, `Session Classifier`, `Risk & R:R (Gate 8)`, `Trend State (M3)`?**
  _High betweenness centrality (0.218) - this node is a cross-community bridge._
- **Why does `SignalParams` connect `Config & Calibration Scripts` to `History Fetching & Sources`, `Triangle Detection (M4)`, `Structure Engine & Gates 1,3,4`, `Indicator Engine (M2)`, `Signal Engine & Gates 2,5-8`, `Position Book & Broker`, `Risk & R:R (Gate 8)`, `Trend State (M3)`?**
  _High betweenness centrality (0.176) - this node is a cross-community bridge._
- **Why does `Session` connect `History Fetching & Sources` to `Session Classifier`, `Config & Calibration Scripts`, `Structure Engine & Gates 1,3,4`, `Signal Engine & Gates 2,5-8`?**
  _High betweenness centrality (0.124) - this node is a cross-community bridge._
- **Are the 46 inferred relationships involving `SignalParams` (e.g. with `PositionBook` and `Candle`) actually correct?**
  _`SignalParams` has 46 INFERRED edges - model-reasoned connections that need verification._
- **Are the 31 inferred relationships involving `evaluate()` (e.g. with `detect_triangle()` and `gate_1_trend_alignment()`) actually correct?**
  _`evaluate()` has 31 INFERRED edges - model-reasoned connections that need verification._
- **Are the 26 inferred relationships involving `InstrumentConfig` (e.g. with `Broker` and `CandleType`) actually correct?**
  _`InstrumentConfig` has 26 INFERRED edges - model-reasoned connections that need verification._
- **Are the 23 inferred relationships involving `load_config()` (e.g. with `collect()` and `analyze()`) actually correct?**
  _`load_config()` has 23 INFERRED edges - model-reasoned connections that need verification._