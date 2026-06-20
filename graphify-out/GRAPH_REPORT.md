# Graph Report - LSB Strategy Bot  (2026-06-19)

## Corpus Check
- 66 files · ~50,043 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 866 nodes · 1883 edges · 52 communities (50 shown, 2 thin omitted)
- Extraction: 66% EXTRACTED · 34% INFERRED · 0% AMBIGUOUS · INFERRED: 631 edges (avg confidence: 0.66)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `3e2a8b76`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- [[_COMMUNITY_Implementation Plan v3.0|Implementation Plan v3.0]]
- [[_COMMUNITY_Phase A Status Tracker|Phase A Status Tracker]]
- [[_COMMUNITY_ADR-001 Broker Bridge|ADR-001 Broker Bridge]]
- [[_COMMUNITY_Database & Migrations|Database & Migrations]]
- [[_COMMUNITY_Config & Calibration Scripts|Config & Calibration Scripts]]
- [[_COMMUNITY_Claude Settings Permissions|Claude Settings Permissions]]
- [[_COMMUNITY_Claude Settings Node|Claude Settings Node]]
- [[_COMMUNITY_Candle Type Definition|Candle Type Definition]]
- [[_COMMUNITY_Data Audit & Anomalies|Data Audit & Anomalies]]
- [[_COMMUNITY_History Fetching & Sources|History Fetching & Sources]]
- [[_COMMUNITY_Triangle Detection (M4)|Triangle Detection (M4)]]
- [[_COMMUNITY_ADR-002 BTCUSD Substitution|ADR-002 BTCUSD Substitution]]
- [[_COMMUNITY_EURUSD Audit Report|EURUSD Audit Report]]
- [[_COMMUNITY_XAUUSD Audit Report|XAUUSD Audit Report]]
- [[_COMMUNITY_BTCUSD Audit Report|BTCUSD Audit Report]]
- [[_COMMUNITY_Structure Engine & Gates 1,3,4|Structure Engine & Gates 1,3,4]]
- [[_COMMUNITY_Indicator Engine (M2)|Indicator Engine (M2)]]
- [[_COMMUNITY_Signal Engine & Gates 2,5-8|Signal Engine & Gates 2,5-8]]
- [[_COMMUNITY_Position Book & Broker|Position Book & Broker]]
- [[_COMMUNITY_H1 to H4 Resampling|H1 to H4 Resampling]]
- [[_COMMUNITY_Trade Management (Sec 11)|Trade Management (Sec 11)]]
- [[_COMMUNITY_Session Classifier|Session Classifier]]
- [[_COMMUNITY_Risk & RR (Gate 8)|Risk & R:R (Gate 8)]]
- [[_COMMUNITY_Backtest Runner & Data Load|Backtest Runner & Data Load]]
- [[_COMMUNITY_Trend State (M3)|Trend State (M3)]]
- [[_COMMUNITY_Pyramiding Policy Tests|Pyramiding Policy Tests]]
- [[_COMMUNITY_ADR-003 Pyramiding|ADR-003 Pyramiding]]
- [[_COMMUNITY_Structure Real-Data Guard|Structure Real-Data Guard]]
- [[_COMMUNITY_ADR-004 Rising-Lows Fix|ADR-004 Rising-Lows Fix]]
- [[_COMMUNITY_Signal Persistence|Signal Persistence]]
- [[_COMMUNITY_ADR-005 Flat-Leg Calibration|ADR-005 Flat-Leg Calibration]]
- [[_COMMUNITY_Community 36|Community 36]]
- [[_COMMUNITY_Community 37|Community 37]]
- [[_COMMUNITY_Community 38|Community 38]]
- [[_COMMUNITY_Community 39|Community 39]]
- [[_COMMUNITY_Community 40|Community 40]]
- [[_COMMUNITY_Community 41|Community 41]]
- [[_COMMUNITY_Community 42|Community 42]]
- [[_COMMUNITY_Community 43|Community 43]]
- [[_COMMUNITY_Community 44|Community 44]]
- [[_COMMUNITY_Community 45|Community 45]]
- [[_COMMUNITY_Community 46|Community 46]]
- [[_COMMUNITY_Community 47|Community 47]]
- [[_COMMUNITY_Community 48|Community 48]]
- [[_COMMUNITY_Community 49|Community 49]]
- [[_COMMUNITY_Community 50|Community 50]]
- [[_COMMUNITY_Community 51|Community 51]]

## God Nodes (most connected - your core abstractions)
1. `SignalParams` - 49 edges
2. `evaluate()` - 36 edges
3. `InstrumentConfig` - 31 edges
4. `load_config()` - 29 edges
5. `_params()` - 27 edges
6. `StructureState` - 26 edges
7. `TestScoreComponents` - 25 edges
8. `_ts()` - 25 edges
9. `ATRState` - 24 edges
10. `SimulatedBroker` - 23 edges

## Surprising Connections (you probably didn't know these)
- `naive()` --calls--> `NaiveBroker`  [INFERRED]
  tests/unit/test_simulated_broker.py → src/lsb/backtest/broker.py
- `broker()` --calls--> `SimulatedBroker`  [INFERRED]
  tests/unit/test_simulated_broker.py → src/lsb/backtest/broker.py
- `load_config()` --calls--> `eurusd_config()`  [INFERRED]
  src/lsb/data/config.py → tests/integration/test_replay_month.py
- `load_config()` --calls--> `btcusd()`  [INFERRED]
  src/lsb/data/config.py → tests/integration/test_structure_realdata.py
- `load_config()` --calls--> `eurusd()`  [INFERRED]
  src/lsb/data/config.py → tests/integration/test_structure_realdata.py

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

## Communities (52 total, 2 thin omitted)

### Community 0 - "Implementation Plan v3.0"
Cohesion: 0.14
Nodes (13): Gate GB — Forward-test verdict (Week 13), LSB Implementation Plan v3.0 — Full Playbook, Part 0 — Operating Doctrine, Part 1 — Phase A: "Prove" (Weeks 1–3, Sessions A0–A11), Part 2 — Phase B: Forward Test + Parallel Hardening (Weeks 4–11, conditional on GO), Part 3 — Phase C: "Scale" (Week 13+, conditional on GB GO), Part 4 — Calendar, Part 5 — Risk Register Deltas (+5 more)

### Community 1 - "Phase A Status Tracker"
Cohesion: 0.25
Nodes (7): Backtest engine (Sessions A6–A7), Data pipeline (Sessions A2–A3, combined), Environment decisions, LSB Phase Status, Out of scope for Phase A, Phase A schema, Signal engine (Sessions A4–A5)

### Community 2 - "ADR-001 Broker Bridge"
Cohesion: 0.50
Nodes (3): ADR-001: Broker Bridge — Native-Windows MT5 with EA-Socket Fallback, Consequences, Decision

### Community 3 - "Database & Migrations"
Cohesion: 0.19
Nodes (10): connection, _applied_migrations(), apply_migrations(), get_connection(), Database connection helper and migration runner.  Connection parameters come fro, Apply any migrations/*.sql files not yet recorded in schema_migrations.      Ret, main(), Apply any migrations/*.sql files not yet recorded in schema_migrations.  Usage: (+2 more)

### Community 4 - "Config & Calibration Scripts"
Cohesion: 0.16
Nodes (12): Signal engine — evaluates all eight M7 entry gates for a candle window.  Accepts, SignalResult, _candle(), Signal engine integration tests.  Tests the full gate-1–4 pipeline end-to-end on, Downward-trending window: forces EMA21 < EMA50 < EMA89 (bearish)., Strong downtrend passes Gate 1; subsequent gates may still fail., TestEngineConfigHash, TestEngineGateProgression (+4 more)

### Community 10 - "Candle Type Definition"
Cohesion: 0.07
Nodes (40): BrokerCosts, NamedTuple, Candle, broker(), _Candle, costs(), naive(), _order() (+32 more)

### Community 12 - "Data Audit & Anomalies"
Cohesion: 0.12
Nodes (39): Anomaly, audit_instrument(), check_dst_anomalies(), check_duplicate_timestamps(), check_gaps(), check_spread_outliers(), check_weekend_bars(), _dst_transition_dates() (+31 more)

### Community 14 - "History Fetching & Sources"
Cohesion: 0.18
Nodes (22): date, _deriv_candles_batch(), _dukascopy_day_url(), fetch_binance_h1(), fetch_deriv_h1(), _fetch_dukascopy_day(), fetch_dukascopy_h1(), fetch_ohlcv() (+14 more)

### Community 15 - "Triangle Detection (M4)"
Cohesion: 0.07
Nodes (31): Candle, _apex_proximity(), _compression_ok(), detect_triangle(), _falling_highs(), _linear_regression(), §6.1.2 falling-highs leg: mirror of _rising_lows for descending triangles., §6.1.1 compression: current candle range ≤ ratio × pattern-start candle range. (+23 more)

### Community 16 - "ADR-002 BTCUSD Substitution"
Cohesion: 0.29
Nodes (6): ADR-002: Instrument Substitution — BTCUSD replaces BOOM500, BOOM500 disposition, Consequences, Context, Decision, Options considered

### Community 17 - "EURUSD Audit Report"
Cohesion: 0.50
Nodes (3): Anomalies, Data Audit Report — EURUSD, Dispositions

### Community 18 - "XAUUSD Audit Report"
Cohesion: 0.50
Nodes (3): Anomalies, Data Audit Report — XAUUSD, Dispositions

### Community 19 - "BTCUSD Audit Report"
Cohesion: 0.50
Nodes (3): Anomalies, Data Audit Report — BTCUSD, Dispositions

### Community 20 - "Structure Engine & Gates 1,3,4"
Cohesion: 0.08
Nodes (38): ATRState, _atr_state_component(), _block_min_width(), BlockResult, _close_quality_component(), _density_component(), detect_sweep(), _ema_proximity_component() (+30 more)

### Community 21 - "Indicator Engine (M2)"
Cohesion: 0.23
Nodes (9): Enum, atr_baseline(), CandleType, M2 — Indicator Engine.  EMA (21/50/89), ATR(14), EMA slope, ATR-state classifica, 20-period SMA of ATR values. Returns None if not enough data., Slope direction from `lookback` bars ago to the last value.      abs(delta) < th, slope_state(), SlopeState (+1 more)

### Community 22 - "Signal Engine & Gates 2,5-8"
Cohesion: 0.06
Nodes (43): CandleType, Gate/indicator parameters for the M7 entry qualifier (Sessions A4–A5).      All, SignalParams, gate_1_trend_alignment(), gate_2_structure_present(), gate_3_liquidity_sweep(), gate_4_sweep_quality(), gate_5_candle_confirmation() (+35 more)

### Community 23 - "Position Book & Broker"
Cohesion: 0.13
Nodes (12): DbSink, NullSink, Signal sinks: NullSink (in-memory, CI-safe) and DbSink (wraps persist.py).  The, In-memory sink — accumulates results for inspection; no DB required., Persists qualified signals to the `signal` table via persist.write_signal_row., Sink, Protocol, main() (+4 more)

### Community 24 - "H1 to H4 Resampling"
Cohesion: 0.17
Nodes (11): _h4_bar_start(), H1 → H4 OHLCV resampling.  H4 boundaries are pinned to fixed UTC hours: 00, 04,, Return the UTC start of the H4 bar that contains `ts`., Aggregate H1 candles into complete H4 candles.      OHLC aggregation: O = first,, resample_h1_to_h4(), Candle, datetime, _h1() (+3 more)

### Community 25 - "Trade Management (Sec 11)"
Cohesion: 0.10
Nodes (39): apply_breakeven(), apply_ema_trail(), nearest_swing_stop(), order_expired(), Trade management — §11 pure functions.  All functions take a Position and return, Record a §11.4 50%-partial-exit event on the leg.      The leg continues; fracti, §10.3: True if the pending order has been open ≥ EXPIRY_BARS without fill., Return the nearest swing pivot on the protective side of entry.      Long: neare (+31 more)

### Community 26 - "Session Classifier"
Cohesion: 0.13
Nodes (11): minutes_to_edge(), Session classifier — pure UTC-band derivation, no clock reads.  Standard FX wind, Classify a UTC timestamp into an FX trading session., Minutes to the nearest boundary of the current session (open or close).      Ret, session_of(), datetime, datetime, Session classifier unit tests — hand-labeled UTC boundary cases. (+3 more)

### Community 27 - "Risk & R:R (Gate 8)"
Cohesion: 0.15
Nodes (17): _nearest_liquidity_pool(), Pure R:R and structural-stop helpers for Gate 8.  No position sizing, no account, Structural stop level per §9.1.      Bear (short): stop = rejection_candle.high, Adaptive target price and R:R ratio per §9.4.      Candidate hierarchy: 2.5R flo, Nearest swing extreme that is ≥ min_dist beyond entry in trade direction.      S, rr_target(), structural_stop(), ATRState (+9 more)

### Community 28 - "Backtest Runner & Data Load"
Cohesion: 0.11
Nodes (21): history_path(), load_parquet(), Parquet history loader for the backtest engine.  Reads data/history/<INSTR>_H1.p, Load a history Parquet file and return ascending-sorted Candle list.      Valida, eurusd_candles(), eurusd_config(), Integration test: one-month H1 replay through the full backtest loop.  Verifies:, Return candles for a single calendar month (timezone-aware ts). (+13 more)

### Community 29 - "Trend State (M3)"
Cohesion: 0.15
Nodes (13): datetime, _candle(), _candles_flat(), _candles_trending_down(), _candles_trending_up(), M3 trend state tests — all four states + EMA compression + crossing.  Fixtures a, Candle with close=open=close (doji-like body) for controlled EMA forcing., Ascending sequence: each close 0.001 higher — forces EMA21>EMA50>EMA89. (+5 more)

### Community 30 - "Pyramiding Policy Tests"
Cohesion: 0.37
Nodes (12): _params(), _pos(), Tests for backtest/book.py — PositionBook and ADR-003 pyramiding policy., test_active_legs_excludes_closed(), test_close_all_flattens_active_legs(), test_first_leg_always_allowed(), test_max_legs_cap(), test_same_direction_blocks_opposing() (+4 more)

### Community 31 - "ADR-003 Pyramiding"
Cohesion: 0.20
Nodes (9): ADR-003 Default Policy, ADR-003 — Pyramiding as a Core Strategy Feature, Book-wide exits (§11.4), Consequences, Context, Decision, Partial exits and P&L, Per-leg management (+1 more)

### Community 32 - "Structure Real-Data Guard"
Cohesion: 0.18
Nodes (15): btcusd(), _confirmed_in_history(), _detect_at(), eurusd(), Real-data regression guard: Gate 2 (structure) must not be silently dead.  Befor, XAU/BTC gate was dead (0 confirmed) before the ATR-relative flat-leg fix.      T, Gate was dead (0 confirmed) for BTC before the ATR-relative flat-leg fix., Sampled sweep: count confirmed triangles over the full history. (+7 more)

### Community 33 - "ADR-004 Rising-Lows Fix"
Cohesion: 0.20
Nodes (9): ADR-004 — Structure Gate: Rising-Lows Leg Correction, Consequences, Context, Decision, Interpretation of "minimum 2 higher lows", New config (schema_version 5 → 6), Root cause, Spec divergence (+1 more)

### Community 34 - "Signal Persistence"
Cohesion: 0.20
Nodes (10): _gate_results_json(), Persist SignalResult to the `signal` table.  This is the only module with I/O in, Serialise the gate evaluation as the JSONB gate_results payload., Insert a signal row for `result`. Returns the row id (or None on conflict)., write_signal_row(), _build_result(), _candle(), Signal persistence tests — DB round-trip for signal rows.  Requires Postgres run (+2 more)

### Community 35 - "ADR-005 Flat-Leg Calibration"
Cohesion: 0.25
Nodes (7): ADR-005 — Flat-Leg Tolerance: Per-Instrument Calibration, Consequences, Context, Decision, New config (schema_version 6 → 7), Why ATR-relative normalization was rejected, Why per-instrument is appropriate

### Community 36 - "Community 36"
Cohesion: 0.20
Nodes (18): Broker, Fill, NaiveBroker, PendingOrder, Broker protocol seam: order submission and fill simulation.  NaiveBroker is the, Honest stop-exit price including gap-through-stop (D1)., Attempt to fill order against candle. Returns Fill or None., Optimistic fill: triggers on first bar the price touches the level.      Long (B (+10 more)

### Community 37 - "Community 37"
Cohesion: 0.25
Nodes (16): BrokerCosts, canonical_dict(), canonical_json(), canonical_yaml(), config_hash(), get_or_create_config_version(), InstrumentConfig, load_config() (+8 more)

### Community 38 - "Community 38"
Cohesion: 0.26
Nodes (16): _defensive_exits(), _manage_book(), _maybe_stage_order(), _process_pending(), Backtest event loop — per-candle replay driver.  run_backtest() streams a pre-lo, Attempt fills; expire stale orders. Returns remaining pending list., Record commission and swap on the leg (D3). Does not affect r_at_close., Apply per-candle management to every active leg. (+8 more)

### Community 39 - "Community 39"
Cohesion: 0.17
Nodes (13): Integration test: SimulatedBroker replays a sample month end-to-end.  Verifies:, Closed legs must have commission ≥ 0 and swap field set (may be 0 for same-day)., r_at_close must equal r_now(close_price) regardless of commission/swap (D3)., Return warm_up bars + all bars for (year, month)., run_backtest with SimulatedBroker must complete without error., Every candle past the warm-up window must produce a signal row., At least one closed leg must have a worse (more costly) entry than NaiveBroker., test_costs_do_not_change_r_at_close() (+5 more)

### Community 40 - "Community 40"
Cohesion: 0.22
Nodes (12): evaluate(), Evaluate all eight M7 gates for the last candle in h1_window.      h1_window mus, Candle, datetime, _candle(), _load_candles(), Engine property tests.  1. Determinism — identical inputs always produce identic, Shuffled candle history should qualify much less often than real history. (+4 more)

### Community 41 - "Community 41"
Cohesion: 0.19
Nodes (7): PositionBook, PositionBook — manages concurrent legs per instrument.  Implements the ADR-003 p, Return True if another leg may be opened per ADR-003 policy., Flatten all active legs (book-wide defensive exit)., Legs that are filled or in managed state (not pending or closed)., Legs that were just filled this bar (state == FILLED, fill_bar == current)., Position

### Community 42 - "Community 42"
Cohesion: 0.20
Nodes (14): current_atr_state(), current_emas(), _ema_order_bearish(), _ema_order_bullish(), _has_recent_crossing(), M3 — Trend Analysis Engine.  Outputs exactly one of four trend states on each ca, Return (EMA21, EMA50, EMA89) for the last candle, or None if insufficient data., ATR state for the last candle, or None if insufficient data. (+6 more)

### Community 43 - "Community 43"
Cohesion: 0.37
Nodes (3): classify_candle(), 8-way candle classifier per spec §4.3.      Classification priority (first match, TestClassifyCandle

### Community 44 - "Community 44"
Cohesion: 0.27
Nodes (7): atr_series(), Wilder-smoothed ATR series.      Requires len(candles) ≥ period + 1.     Result, Candle, _make_candles(), M2 indicator tests — verified against hand-computed reference values.  Spec test, Helper: ohlcv is a list of (o, h, l, c) tuples., TestAtrSeries

### Community 45 - "Community 45"
Cohesion: 0.20
Nodes (5): Injectable replay clock for deterministic backtesting.  ReplayClock emits candle, Iterates over a candle list, exposing the current timestamp via .now.      Usage, Timestamp of the current bar (candles[_idx].ts)., ReplayClock, Candle

### Community 46 - "Community 46"
Cohesion: 0.25
Nodes (5): Any, Position, Position lifecycle: pending → filled → managed → closed.  Each Position is one l, Current floating R-multiple at given price (1 notional unit)., SignalParams

### Community 47 - "Community 47"
Cohesion: 0.36
Nodes (3): classify_atr_state(), Classify ATR state relative to the 20-period baseline (spec §4.2.2)., TestClassifyAtrState

### Community 48 - "Community 48"
Cohesion: 0.39
Nodes (3): ema_series(), EMA series seeded with SMA of the first `period` values.      Returns a list ali, TestEmaSeries

### Community 49 - "Community 49"
Cohesion: 0.50
Nodes (4): collect(), main(), Sensitivity sweep over the apex-proximity thresholds (Requirements v2.1 protocol, One permissive pass. Returns (apex_proximity, qualified) for every     structure

### Community 50 - "Community 50"
Cohesion: 0.67
Nodes (3): collect(), main(), Calibration: pick a single shared k_atr for the ATR-relative flat leg.  Pre-comp

### Community 51 - "Community 51"
Cohesion: 0.67
Nodes (3): analyze(), main(), Diagnostic: where does the structure detector fall out, per instrument?  Isolate

## Knowledge Gaps
- **57 isolated node(s):** `Phase A schema`, `Signal engine (Sessions A4–A5)`, `Backtest engine (Sessions A6–A7)`, `Data pipeline (Sessions A2–A3, combined)`, `Out of scope for Phase A` (+52 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **2 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `evaluate()` connect `Community 40` to `Signal Persistence`, `Config & Calibration Scripts`, `Community 38`, `Community 42`, `Triangle Detection (M4)`, `Structure Engine & Gates 1,3,4`, `Signal Engine & Gates 2,5-8`, `H1 to H4 Resampling`, `Session Classifier`, `Risk & R:R (Gate 8)`?**
  _High betweenness centrality (0.214) - this node is a cross-community bridge._
- **Why does `SignalParams` connect `Signal Engine & Gates 2,5-8` to `Community 37`, `Community 41`, `Community 42`, `Community 46`, `History Fetching & Sources`, `Triangle Detection (M4)`, `Structure Engine & Gates 1,3,4`, `Risk & R:R (Gate 8)`, `Trend State (M3)`?**
  _High betweenness centrality (0.162) - this node is a cross-community bridge._
- **Why does `InstrumentConfig` connect `Community 38` to `Community 36`, `Community 37`, `Community 40`, `Community 41`, `Community 45`, `Community 46`, `Signal Engine & Gates 2,5-8`, `Position Book & Broker`?**
  _High betweenness centrality (0.133) - this node is a cross-community bridge._
- **Are the 46 inferred relationships involving `SignalParams` (e.g. with `PositionBook` and `Candle`) actually correct?**
  _`SignalParams` has 46 INFERRED edges - model-reasoned connections that need verification._
- **Are the 31 inferred relationships involving `evaluate()` (e.g. with `gate_1_trend_alignment()` and `gate_2_structure_present()`) actually correct?**
  _`evaluate()` has 31 INFERRED edges - model-reasoned connections that need verification._
- **Are the 24 inferred relationships involving `InstrumentConfig` (e.g. with `Broker` and `CandleType`) actually correct?**
  _`InstrumentConfig` has 24 INFERRED edges - model-reasoned connections that need verification._
- **Are the 23 inferred relationships involving `load_config()` (e.g. with `eurusd_config()` and `btcusd()`) actually correct?**
  _`load_config()` has 23 INFERRED edges - model-reasoned connections that need verification._