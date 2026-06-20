# Graph Report - LSB Strategy Bot  (2026-06-18)

## Corpus Check
- 60 files · ~43,218 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 770 nodes · 1716 edges · 34 communities (31 shown, 3 thin omitted)
- Extraction: 66% EXTRACTED · 34% INFERRED · 0% AMBIGUOUS · INFERRED: 588 edges (avg confidence: 0.65)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `9dafb158`
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
- [[_COMMUNITY_Community 29|Community 29]]
- [[_COMMUNITY_Community 30|Community 30]]
- [[_COMMUNITY_Community 31|Community 31]]
- [[_COMMUNITY_Community 32|Community 32]]
- [[_COMMUNITY_Community 33|Community 33]]

## God Nodes (most connected - your core abstractions)
1. `SignalParams` - 49 edges
2. `evaluate()` - 36 edges
3. `InstrumentConfig` - 33 edges
4. `_params()` - 27 edges
5. `StructureState` - 26 edges
6. `TestScoreComponents` - 25 edges
7. `_ts()` - 25 edges
8. `load_config()` - 24 edges
9. `ATRState` - 24 edges
10. `Session` - 22 edges

## Surprising Connections (you probably didn't know these)
- `eurusd_config()` --calls--> `load_config()`  [INFERRED]
  tests/integration/test_replay_month.py → src/lsb/data/config.py
- `eurusd()` --calls--> `load_config()`  [INFERRED]
  tests/integration/test_structure_realdata.py → src/lsb/data/config.py
- `TestDetectSweep` --uses--> `BrokerCosts`  [INFERRED]
  tests/unit/test_liquidity.py → src/lsb/data/config.py
- `TestIdentifyBlock` --uses--> `BrokerCosts`  [INFERRED]
  tests/unit/test_liquidity.py → src/lsb/data/config.py
- `TestScoreComponents` --uses--> `BrokerCosts`  [INFERRED]
  tests/unit/test_liquidity.py → src/lsb/data/config.py

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

## Communities (34 total, 3 thin omitted)

### Community 0 - "Gates and Verdicts"
Cohesion: 0.14
Nodes (13): Gate GB — Forward-test verdict (Week 13), LSB Implementation Plan v3.0 — Full Playbook, Part 0 — Operating Doctrine, Part 1 — Phase A: "Prove" (Weeks 1–3, Sessions A0–A11), Part 2 — Phase B: Forward Test + Parallel Hardening (Weeks 4–11, conditional on GO), Part 3 — Phase C: "Scale" (Week 13+, conditional on GB GO), Part 4 — Calendar, Part 5 — Risk Register Deltas (+5 more)

### Community 1 - "Track 2 Hardening and State Machine"
Cohesion: 0.25
Nodes (7): Backtest engine (Session A6), Data pipeline (Sessions A2–A3, combined), Environment decisions, LSB Phase Status, Out of scope for Phase A, Phase A schema, Signal engine (Sessions A4–A5)

### Community 2 - "Phase A Scaffold, Config and Data Pipeline"
Cohesion: 0.50
Nodes (3): ADR-001: Broker Bridge — Native-Windows MT5 with EA-Socket Fallback, Consequences, Decision

### Community 3 - "Signal and Backtest Engine"
Cohesion: 0.19
Nodes (10): connection, _applied_migrations(), apply_migrations(), get_connection(), Database connection helper and migration runner.  Connection parameters come fro, Apply any migrations/*.sql files not yet recorded in schema_migrations.      Ret, main(), Apply any migrations/*.sql files not yet recorded in schema_migrations.  Usage: (+2 more)

### Community 4 - "Determinism and Walk-Forward"
Cohesion: 0.06
Nodes (47): BrokerCosts, canonical_dict(), canonical_json(), canonical_yaml(), config_hash(), get_or_create_config_version(), load_config(), Instrument config: YAML -> frozen dataclass -> canonical form -> config_hash.  I (+39 more)

### Community 12 - "Community 12"
Cohesion: 0.12
Nodes (39): Anomaly, audit_instrument(), check_dst_anomalies(), check_duplicate_timestamps(), check_gaps(), check_spread_outliers(), check_weekend_bars(), _dst_transition_dates() (+31 more)

### Community 14 - "Community 14"
Cohesion: 0.18
Nodes (22): date, _deriv_candles_batch(), _dukascopy_day_url(), fetch_binance_h1(), fetch_deriv_h1(), _fetch_dukascopy_day(), fetch_dukascopy_h1(), fetch_ohlcv() (+14 more)

### Community 15 - "Community 15"
Cohesion: 0.06
Nodes (38): Candle, _detect_at(), eurusd(), Real-data regression guard: Gate 2 (structure) must not be silently dead.  Befor, Sampled sweep: at least a handful of confirmed triangles over the history., test_ascending_triangle_reachable(), test_confirmed_triangles_exist_in_history(), test_descending_triangle_reachable() (+30 more)

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
Cohesion: 0.06
Nodes (31): atr_baseline(), atr_series(), CandleType, classify_atr_state(), classify_candle(), ema_series(), M2 — Indicator Engine.  EMA (21/50/89), ATR(14), EMA slope, ATR-state classifica, 20-period SMA of ATR values. Returns None if not enough data. (+23 more)

### Community 22 - "Community 22"
Cohesion: 0.11
Nodes (14): gate_5_candle_confirmation(), gate_6_volatility_acceptable(), gate_7_session_clear(), gate_8_risk_viable(), Gate 5 — Candle confirmation (§8 cond 5).      Pass: confirmation candle is REJE, Gate 6 — Volatility acceptable (§9.3).      Blocks EXTREME ATR (§9.3 "ATR=EXTREM, Gate 7 — Session & news clear (§8 cond 6).      Deterministic part: session must, Gate 8 — Risk viable (§9.1 + §9.4).      Deterministic part: structural stop mus (+6 more)

### Community 23 - "Community 23"
Cohesion: 0.06
Nodes (55): Any, PositionBook, PositionBook — manages concurrent legs per instrument.  Implements the ADR-003 p, Return True if another leg may be opened per ADR-003 policy., Flatten all active legs (book-wide defensive exit)., Legs that are filled or in managed state (not pending or closed)., Legs that were just filled this bar (state == FILLED, fill_bar == current)., Broker (+47 more)

### Community 24 - "Community 24"
Cohesion: 0.17
Nodes (11): _h4_bar_start(), H1 → H4 OHLCV resampling.  H4 boundaries are pinned to fixed UTC hours: 00, 04,, Return the UTC start of the H4 bar that contains `ts`., Aggregate H1 candles into complete H4 candles.      OHLC aggregation: O = first,, resample_h1_to_h4(), Candle, datetime, _h1() (+3 more)

### Community 25 - "Community 25"
Cohesion: 0.11
Nodes (36): apply_breakeven(), apply_ema_trail(), order_expired(), Trade management — §11 pure functions.  All functions take a Position and return, Record a §11.4 50%-partial-exit event on the leg.      The leg continues; fracti, §10.3: True if the pending order has been open ≥ EXPIRY_BARS without fill., True if the candle's range reached the current stop., True if the candle's range reached the target. (+28 more)

### Community 26 - "Community 26"
Cohesion: 0.13
Nodes (11): minutes_to_edge(), Session classifier — pure UTC-band derivation, no clock reads.  Standard FX wind, Classify a UTC timestamp into an FX trading session., Minutes to the nearest boundary of the current session (open or close).      Ret, session_of(), datetime, datetime, Session classifier unit tests — hand-labeled UTC boundary cases. (+3 more)

### Community 27 - "Community 27"
Cohesion: 0.15
Nodes (17): _nearest_liquidity_pool(), Pure R:R and structural-stop helpers for Gate 8.  No position sizing, no account, Structural stop level per §9.1.      Bear (short): stop = rejection_candle.high, Adaptive target price and R:R ratio per §9.4.      Candidate hierarchy: 2.5R flo, Nearest swing extreme that is ≥ min_dist beyond entry in trade direction.      S, rr_target(), structural_stop(), ATRState (+9 more)

### Community 28 - "Community 28"
Cohesion: 0.09
Nodes (25): history_path(), load_parquet(), Parquet history loader for the backtest engine.  Reads data/history/<INSTR>_H1.p, Load a history Parquet file and return ascending-sorted Candle list.      Valida, eurusd_candles(), eurusd_config(), Integration test: one-month H1 replay through the full backtest loop.  Verifies:, Return candles for a single calendar month (timezone-aware ts). (+17 more)

### Community 29 - "Community 29"
Cohesion: 0.12
Nodes (20): _ema_order_bearish(), _ema_order_bullish(), _has_recent_crossing(), M3 — Trend Analysis Engine.  Outputs exactly one of four trend states on each ca, True if EMA21/EMA50 relative ordering changed within the last `lookback` bars., Compute M3 trend state for the last candle in `candles`.      Requires sufficien, trend_state(), datetime (+12 more)

### Community 30 - "Community 30"
Cohesion: 0.37
Nodes (12): _params(), _pos(), Tests for backtest/book.py — PositionBook and ADR-003 pyramiding policy., test_active_legs_excludes_closed(), test_close_all_flattens_active_legs(), test_first_leg_always_allowed(), test_max_legs_cap(), test_same_direction_blocks_opposing() (+4 more)

### Community 31 - "Community 31"
Cohesion: 0.20
Nodes (9): ADR-003 Default Policy, ADR-003 — Pyramiding as a Core Strategy Feature, Book-wide exits (§11.4), Consequences, Context, Decision, Partial exits and P&L, Per-leg management (+1 more)

### Community 32 - "Community 32"
Cohesion: 0.09
Nodes (43): CandleType, InstrumentConfig, Gate/indicator parameters for the M7 entry qualifier (Sessions A4–A5).      All, SignalParams, Enum, Signal engine — evaluates all eight M7 entry gates for a candle window.  Accepts, SignalResult, gate_1_trend_alignment() (+35 more)

### Community 33 - "Community 33"
Cohesion: 0.22
Nodes (8): ADR-004 — Structure Gate: Rising-Lows Leg Correction, Consequences, Context, Decision, Interpretation of "minimum 2 higher lows", New config (schema_version 5 → 6), Root cause, Spec divergence

## Knowledge Gaps
- **52 isolated node(s):** `Phase A schema`, `Signal engine (Sessions A4–A5)`, `Backtest engine (Session A6)`, `Data pipeline (Sessions A2–A3, combined)`, `Out of scope for Phase A` (+47 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **3 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `evaluate()` connect `Determinism and Walk-Forward` to `Community 32`, `Community 15`, `Community 20`, `Community 21`, `Community 22`, `Community 23`, `Community 24`, `Community 26`, `Community 27`, `Community 29`?**
  _High betweenness centrality (0.226) - this node is a cross-community bridge._
- **Why does `SignalParams` connect `Community 32` to `Determinism and Walk-Forward`, `Community 14`, `Community 15`, `Community 20`, `Community 21`, `Community 22`, `Community 23`, `Community 27`, `Community 29`?**
  _High betweenness centrality (0.175) - this node is a cross-community bridge._
- **Why does `Session` connect `Community 14` to `Community 32`, `Community 22`?**
  _High betweenness centrality (0.130) - this node is a cross-community bridge._
- **Are the 46 inferred relationships involving `SignalParams` (e.g. with `PositionBook` and `Candle`) actually correct?**
  _`SignalParams` has 46 INFERRED edges - model-reasoned connections that need verification._
- **Are the 31 inferred relationships involving `evaluate()` (e.g. with `gate_1_trend_alignment()` and `gate_2_structure_present()`) actually correct?**
  _`evaluate()` has 31 INFERRED edges - model-reasoned connections that need verification._
- **Are the 26 inferred relationships involving `InstrumentConfig` (e.g. with `Broker` and `CandleType`) actually correct?**
  _`InstrumentConfig` has 26 INFERRED edges - model-reasoned connections that need verification._
- **Are the 24 inferred relationships involving `StructureState` (e.g. with `SignalResult` and `GateResult`) actually correct?**
  _`StructureState` has 24 INFERRED edges - model-reasoned connections that need verification._