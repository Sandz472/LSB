# Graph Report - LSB Strategy Bot  (2026-06-17)

## Corpus Check
- 39 files · ~27,551 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 443 nodes · 956 edges · 29 communities (26 shown, 3 thin omitted)
- Extraction: 67% EXTRACTED · 33% INFERRED · 0% AMBIGUOUS · INFERRED: 319 edges (avg confidence: 0.65)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `a31ec5a9`
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
- [[_COMMUNITY_Community 10|Community 10]]
- [[_COMMUNITY_Community 12|Community 12]]
- [[_COMMUNITY_Community 14|Community 14]]
- [[_COMMUNITY_Community 15|Community 15]]
- [[_COMMUNITY_Community 16|Community 16]]
- [[_COMMUNITY_Community 17|Community 17]]
- [[_COMMUNITY_Community 18|Community 18]]
- [[_COMMUNITY_Community 19|Community 19]]
- [[_COMMUNITY_Community 20|Community 20]]
- [[_COMMUNITY_Community 21|Community 21]]
- [[_COMMUNITY_Community 22|Community 22]]
- [[_COMMUNITY_Community 23|Community 23]]
- [[_COMMUNITY_Community 24|Community 24]]
- [[_COMMUNITY_Community 25|Community 25]]
- [[_COMMUNITY_Community 26|Community 26]]
- [[_COMMUNITY_Community 27|Community 27]]
- [[_COMMUNITY_Community 28|Community 28]]

## God Nodes (most connected - your core abstractions)
1. `StructureState` - 26 edges
2. `ATRState` - 25 edges
3. `TestScoreComponents` - 25 edges
4. `evaluate()` - 24 edges
5. `SignalParams` - 23 edges
6. `InstrumentConfig` - 23 edges
7. `TrendState` - 23 edges
8. `detect_sweep()` - 20 edges
9. `StructureResult` - 20 edges
10. `trend_state()` - 18 edges

## Surprising Connections (you probably didn't know these)
- `TestDetectSweep` --uses--> `BrokerCosts`  [INFERRED]
  tests/unit/test_liquidity.py → src/lsb/data/config.py
- `TestIdentifyBlock` --uses--> `BrokerCosts`  [INFERRED]
  tests/unit/test_liquidity.py → src/lsb/data/config.py
- `TestScoreComponents` --uses--> `BrokerCosts`  [INFERRED]
  tests/unit/test_liquidity.py → src/lsb/data/config.py
- `TestDetectSweep` --uses--> `WalkForwardWindow`  [INFERRED]
  tests/unit/test_liquidity.py → src/lsb/data/config.py
- `TestIdentifyBlock` --uses--> `WalkForwardWindow`  [INFERRED]
  tests/unit/test_liquidity.py → src/lsb/data/config.py

## Import Cycles
- 1-file cycle: `src/lsb/signals/resample.py -> src/lsb/signals/resample.py`
- 1-file cycle: `tests/unit/test_trend.py -> tests/unit/test_trend.py`

## Hyperedges (group relationships)
- **Phase A Sessions (A0-A11) Forming the Path to Gate GA** — implementation_plan_v3_0_session_a0_scaffold, implementation_plan_v3_0_session_a1_config_schema, implementation_plan_v3_0_session_a2_data_pipeline_1, implementation_plan_v3_0_session_a3_data_pipeline_n, implementation_plan_v3_0_session_a4_a5_signal_engine, implementation_plan_v3_0_session_a6_a7_backtest_engine, implementation_plan_v3_0_session_a8_determinism_gate, implementation_plan_v3_0_session_a9_walkforward_harness, implementation_plan_v3_0_session_a10_verdict_report, implementation_plan_v3_0_session_a11_full_run_gate_ga, implementation_plan_v3_0_gate_ga [EXTRACTED 1.00]
- **Five Core Modules Surviving Phase A (C1-C5)** — implementation_plan_v3_0_c1_data_pipeline, implementation_plan_v3_0_c2_signal_engine, implementation_plan_v3_0_c3_backtest_engine, implementation_plan_v3_0_c4_walkforward_harness, implementation_plan_v3_0_c5_verdict_report [EXTRACTED 1.00]
- **Track 2 Hardening Sessions (B5-B10) Running Parallel to Forward Test** — implementation_plan_v3_0_session_b5_live_tables, implementation_plan_v3_0_session_b6_risk_portfolio, implementation_plan_v3_0_session_b7_monitoring_alerting, implementation_plan_v3_0_session_b8_docker, implementation_plan_v3_0_session_b9_vps_shadow, implementation_plan_v3_0_session_b10_interrogations, implementation_plan_v3_0_track2_hardening [EXTRACTED 1.00]

## Communities (29 total, 3 thin omitted)

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
Cohesion: 0.11
Nodes (32): BrokerCosts, canonical_dict(), canonical_json(), canonical_yaml(), config_hash(), get_or_create_config_version(), InstrumentConfig, load_config() (+24 more)

### Community 12 - "Community 12"
Cohesion: 0.12
Nodes (40): Path, Anomaly, audit_instrument(), check_dst_anomalies(), check_duplicate_timestamps(), check_gaps(), check_spread_outliers(), check_weekend_bars() (+32 more)

### Community 14 - "Community 14"
Cohesion: 0.18
Nodes (22): date, _deriv_candles_batch(), _dukascopy_day_url(), fetch_binance_h1(), fetch_deriv_h1(), _fetch_dukascopy_day(), fetch_dukascopy_h1(), fetch_ohlcv() (+14 more)

### Community 15 - "Community 15"
Cohesion: 0.08
Nodes (49): Gate/indicator parameters for the M7 entry qualifier (Sessions A4–A5).      All, SignalParams, Enum, atr_baseline(), ATRState, M2 — Indicator Engine.  EMA (21/50/89), ATR(14), EMA slope, ATR-state classifica, 20-period SMA of ATR values. Returns None if not enough data., SlopeState (+41 more)

### Community 16 - "Community 16"
Cohesion: 0.29
Nodes (6): ADR-002: Instrument Substitution — BTCUSD replaces BOOM500, BOOM500 disposition, Consequences, Context, Decision, Options considered

### Community 17 - "Community 17"
Cohesion: 0.50
Nodes (3): Anomalies, Data Audit Report — EURUSD, Dispositions

### Community 18 - "Community 18"
Cohesion: 0.50
Nodes (3): Anomalies, Data Audit Report — XAUUSD, Dispositions

### Community 19 - "Community 19"
Cohesion: 0.50
Nodes (3): Anomalies, Data Audit Report — BTCUSD, Dispositions

### Community 20 - "Community 20"
Cohesion: 0.08
Nodes (29): _atr_state_component(), _block_min_width(), BlockResult, _close_quality_component(), _density_component(), detect_sweep(), _ema_proximity_component(), identify_block() (+21 more)

### Community 21 - "Community 21"
Cohesion: 0.12
Nodes (14): atr_series(), CandleType, classify_candle(), 8-way candle classifier per spec §4.3.      Classification priority (first match, Wilder-smoothed ATR series.      Requires len(candles) ≥ period + 1.     Result, Slope direction from `lookback` bars ago to the last value.      abs(delta) < th, slope_state(), Candle (+6 more)

### Community 22 - "Community 22"
Cohesion: 0.10
Nodes (23): _apex_proximity(), detect_triangle(), _linear_regression(), Fractional progress from pattern_start to the apex (triangle convergence point)., Detect ascending or descending triangle on H4 candles (spec §6).      Evaluates, Indices of swing highs (bar.high ≥ all neighbors within lookback)., Indices of swing lows (bar.low ≤ all neighbors within lookback)., Returns (slope, intercept) of the least-squares line through (xs, ys). (+15 more)

### Community 23 - "Community 23"
Cohesion: 0.13
Nodes (13): gate_2_structure_present(), gate_3_liquidity_sweep(), gate_4_sweep_quality(), Gates 1–4 of the M7 entry qualifier.  Each gate is a pure predicate returning a, Gate 4 — Sweep quality (5-factor score ≥ sweep_score_min).      Spec §7.3: score, Gate 2 — Structure present (M4).      Pass: M4 reports a confirmed triangle on H, Gate 3 — Liquidity sweep confirmed (M5).      Pass: M5 detects an active sweep e, Gates 1–4 unit tests — 1 pass + ≥2 near-misses per gate.  Fixtures are hand-labe (+5 more)

### Community 24 - "Community 24"
Cohesion: 0.17
Nodes (11): _h4_bar_start(), H1 → H4 OHLCV resampling.  H4 boundaries are pinned to fixed UTC hours: 00, 04,, Return the UTC start of the H4 bar that contains `ts`., Aggregate H1 candles into complete H4 candles.      OHLC aggregation: O = first,, resample_h1_to_h4(), Candle, datetime, _h1() (+3 more)

### Community 25 - "Community 25"
Cohesion: 0.19
Nodes (11): SignalResult, _gate_results_json(), Persist SignalResult to the `signal` table.  This is the only module with I/O in, Serialise the gate evaluation as the JSONB gate_results payload., Insert a signal row for `result`. Returns the row id (or None on conflict)., write_signal_row(), _build_result(), _candle() (+3 more)

### Community 26 - "Community 26"
Cohesion: 0.36
Nodes (3): classify_atr_state(), Classify ATR state relative to the 20-period baseline (spec §4.2.2)., TestClassifyAtrState

### Community 27 - "Community 27"
Cohesion: 0.39
Nodes (3): gate_1_trend_alignment(), Gate 1 — Trend alignment (M3).      Pass: M3 trend state is BULLISH (long setup), TestGate1

### Community 28 - "Community 28"
Cohesion: 0.39
Nodes (3): ema_series(), EMA series seeded with SMA of the first `period` values.      Returns a list ali, TestEmaSeries

## Knowledge Gaps
- **34 isolated node(s):** `Candle`, `Anomalies`, `Dispositions`, `Context`, `Options considered` (+29 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **3 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `load_config()` connect `Determinism and Walk-Forward` to `Community 25`, `Community 12`, `Community 15`?**
  _High betweenness centrality (0.227) - this node is a cross-community bridge._
- **Why does `evaluate()` connect `Determinism and Walk-Forward` to `Community 15`, `Community 20`, `Community 22`, `Community 23`, `Community 24`, `Community 25`, `Community 27`?**
  _High betweenness centrality (0.206) - this node is a cross-community bridge._
- **Why does `Path` connect `Community 12` to `Determinism and Walk-Forward`?**
  _High betweenness centrality (0.204) - this node is a cross-community bridge._
- **Are the 24 inferred relationships involving `StructureState` (e.g. with `SignalResult` and `GateResult`) actually correct?**
  _`StructureState` has 24 INFERRED edges - model-reasoned connections that need verification._
- **Are the 22 inferred relationships involving `ATRState` (e.g. with `GateResult` and `BlockResult`) actually correct?**
  _`ATRState` has 22 INFERRED edges - model-reasoned connections that need verification._
- **Are the 9 inferred relationships involving `TestScoreComponents` (e.g. with `BrokerCosts` and `InstrumentConfig`) actually correct?**
  _`TestScoreComponents` has 9 INFERRED edges - model-reasoned connections that need verification._
- **Are the 19 inferred relationships involving `evaluate()` (e.g. with `gate_1_trend_alignment()` and `gate_2_structure_present()`) actually correct?**
  _`evaluate()` has 19 INFERRED edges - model-reasoned connections that need verification._