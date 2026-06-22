# Graph Report - .  (2026-06-22)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 782 nodes · 1848 edges · 37 communities (31 shown, 6 thin omitted)
- Extraction: 66% EXTRACTED · 29% INFERRED · 0% AMBIGUOUS · INFERRED: 530 edges (avg confidence: 0.63)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `f54e5854`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- [[_COMMUNITY_Configuration Subsystem|Configuration Subsystem]]
- [[_COMMUNITY_Project Architecture and Specs|Project Architecture and Specs]]
- [[_COMMUNITY_CLI and Data Fetching|CLI and Data Fetching]]
- [[_COMMUNITY_Strategy Constants and Gates|Strategy Constants and Gates]]
- [[_COMMUNITY_Gap Detection and Audit|Gap Detection and Audit]]
- [[_COMMUNITY_Asset Configuration ADRs|Asset Configuration ADRs]]
- [[_COMMUNITY_Liquidity Sweep Logic|Liquidity Sweep Logic]]
- [[_COMMUNITY_Schema Design ADRs|Schema Design ADRs]]
- [[_COMMUNITY_Smoke Tests|Smoke Tests]]
- [[_COMMUNITY_Package Metadata|Package Metadata]]
- [[_COMMUNITY_CI Workflow|CI Workflow]]
- [[_COMMUNITY_Project Identity|Project Identity]]
- [[_COMMUNITY_Timeframe Resampling|Timeframe Resampling]]
- [[_COMMUNITY_Database Persistence|Database Persistence]]
- [[_COMMUNITY_Trend Validation Tests|Trend Validation Tests]]
- [[_COMMUNITY_Signal Conjunction Tests|Signal Conjunction Tests]]
- [[_COMMUNITY_Risk and Reward Gates|Risk and Reward Gates]]
- [[_COMMUNITY_Gate Specifications|Gate Specifications]]
- [[_COMMUNITY_Build Playbook|Build Playbook]]
- [[_COMMUNITY_ATR Volatility Analysis|ATR Volatility Analysis]]
- [[_COMMUNITY_Trading Session Tests|Trading Session Tests]]
- [[_COMMUNITY_Rejection Geometry ADRs|Rejection Geometry ADRs]]
- [[_COMMUNITY_Swing Window ADRs|Swing Window ADRs]]
- [[_COMMUNITY_Macro Trend ADRs|Macro Trend ADRs]]
- [[_COMMUNITY_Phase Status Tracking|Phase Status Tracking]]
- [[_COMMUNITY_Governing Instructions|Governing Instructions]]
- [[_COMMUNITY_Signal Persistence|Signal Persistence]]
- [[_COMMUNITY_Core Strategy Gates|Core Strategy Gates]]
- [[_COMMUNITY_Sweep Score ADRs|Sweep Score ADRs]]
- [[_COMMUNITY_Volatility Regime ADRs|Volatility Regime ADRs]]
- [[_COMMUNITY_Signal Evaluation Engine|Signal Evaluation Engine]]
- [[_COMMUNITY_Risk Tier Scoring|Risk Tier Scoring]]
- [[_COMMUNITY_Global Risk Tests|Global Risk Tests]]
- [[_COMMUNITY_Session Validation|Session Validation]]
- [[_COMMUNITY_Market Structure Analysis|Market Structure Analysis]]
- [[_COMMUNITY_Rejection Candle Tests|Rejection Candle Tests]]
- [[_COMMUNITY_ATR State Classification|ATR State Classification]]

## God Nodes (most connected - your core abstractions)
1. `D()` - 81 edges
2. `StrategyParams` - 72 edges
3. `GateResult` - 70 edges
4. `Side` - 67 edges
5. `InstrumentConfig` - 64 edges
6. `AtrState` - 34 edges
7. `load_instrument()` - 28 edges
8. `fetch_history()` - 23 edges
9. `load_strategy()` - 22 edges
10. `audit_history()` - 21 edges

## Surprising Connections (you probably didn't know these)
- `ADR-002 — Phase-A core schema design` --references--> `001_core.sql DDL`  [EXTRACTED]
  docs/decisions/ADR-002-phase-a-schema.md → migrations/001_core.sql
- `Implementation Plan — A1: Config System + Core Schema` --references--> `config_hash function`  [EXTRACTED]
  plan-a1-config-schema.html → src/lsb/config/hashing.py
- `Implementation Plan — A1: Config System + Core Schema` --references--> `InstrumentConfig Dataclass`  [EXTRACTED]
  plan-a1-config-schema.html → src/lsb/config/models.py
- `Implementation Plan — A1: Config System + Core Schema` --references--> `SpecConfig Dataclass`  [EXTRACTED]
  plan-a1-config-schema.html → src/lsb/config/models.py
- `Implementation Plan — A1: Config System + Core Schema` --references--> `001_core.sql DDL`  [EXTRACTED]
  plan-a1-config-schema.html → migrations/001_core.sql

## Import Cycles
- 1-file cycle: `src/lsb/config/loader.py -> src/lsb/config/loader.py`
- 1-file cycle: `src/lsb/data/audit.py -> src/lsb/data/audit.py`
- 1-file cycle: `src/lsb/data/resample.py -> src/lsb/data/resample.py`
- 1-file cycle: `src/lsb/signal/conjunction.py -> src/lsb/signal/conjunction.py`
- 1-file cycle: `src/lsb/signal/__init__.py -> src/lsb/signal/__init__.py`
- 1-file cycle: `src/lsb/signal/atr_state.py -> src/lsb/signal/atr_state.py`
- 1-file cycle: `src/lsb/signal/gate2_structure.py -> src/lsb/signal/gate2_structure.py`
- 1-file cycle: `src/lsb/signal/gate3_sweep.py -> src/lsb/signal/gate3_sweep.py`
- 1-file cycle: `src/lsb/signal/gate5_rejection.py -> src/lsb/signal/gate5_rejection.py`
- 1-file cycle: `src/lsb/signal/gate6_session.py -> src/lsb/signal/gate6_session.py`
- 1-file cycle: `src/lsb/signal/gate7_rr.py -> src/lsb/signal/gate7_rr.py`
- 1-file cycle: `src/lsb/signal/indicators.py -> src/lsb/signal/indicators.py`
- 1-file cycle: `src/lsb/signal/sweep_score.py -> src/lsb/signal/sweep_score.py`
- 1-file cycle: `tests/test_audit.py -> tests/test_audit.py`
- 1-file cycle: `tests/test_gate4_ema.py -> tests/test_gate4_ema.py`
- 1-file cycle: `tests/test_indicators.py -> tests/test_indicators.py`
- 1-file cycle: `tests/test_load.py -> tests/test_load.py`
- 1-file cycle: `tests/test_resample.py -> tests/test_resample.py`

## Communities (37 total, 6 thin omitted)

### Community 0 - "Configuration Subsystem"
Cohesion: 0.09
Nodes (42): _canonical_value(), config_hash(), Deterministic sha256 config_hash.  Invariant: same field values → same hex diges, Return sha256 of the canonical combined JSON of all *cfgs*.      Each config is, LSB config subsystem — public re-exports., _d(), load_instrument(), load_spec() (+34 more)

### Community 1 - "Project Architecture and Specs"
Cohesion: 0.05
Nodes (63): ADR-001 broker bridge, ADR-002 go/no-go, ATR EXTREME → No-Trade Pre-filter (§4.2.2/§9.3), Block HIGH (sweep target), Master Blueprint v2.1, BUILD_PLAYBOOK.md, CLAUDE.md (governing), .claude/settings.local.json (+55 more)

### Community 2 - "CLI and Data Fetching"
Cohesion: 0.08
Nodes (40): cmd_fetch_audit_load(), _default_path(), main(), CLI entry point: fetch → audit → load for a single instrument.  Usage:     pytho, Resolve *relative* against the repo root (3 levels up from this file)., CachedSeries, _csv_to_rows(), fetch_history() (+32 more)

### Community 3 - "Strategy Constants and Gates"
Cohesion: 0.12
Nodes (51): InstrumentConfig, Universal strategy constants from §5.1 / §6.1.1 / §7.2 / §8.1.      All threshol, StrategyParams, evaluate(), Return Gate 1 result for the LAST bar in *candles_d1*.      candles_d1 must be s, evaluate(), Return Gate 4 result for the LAST bar of *candles_h1*.      sweep_bar: index of, _anatomy() (+43 more)

### Community 4 - "Gap Detection and Audit"
Cohesion: 0.07
Nodes (57): audit_history(), AuditReport, classify_gap(), GapRecord, _is_dst_gap(), _is_holiday_gap(), _is_weekend_gap(), Gap detection and mandatory disposition for H1 OHLCV series.  Every gap > 2 bars (+49 more)

### Community 5 - "Asset Configuration ADRs"
Cohesion: 0.11
Nodes (18): ADR-004 — Bull rejection geometry: lower-wick hammer, BTCUSD Configuration, LSB Build Playbook, LSB Governing Instructions, ADR-001 — Broker Bridge: native-Windows MT5, Consequences, Context, Decision (+10 more)

### Community 6 - "Liquidity Sweep Logic"
Cohesion: 0.07
Nodes (67): ema(), EMA with SMA seed.  Returns None for the first period-1 positions.      Seed  =, _build_bear_sweep_series(), _default_ic(), _default_sp(), _h1(), Golden gate-fixtures for Gate 3 — Liquidity Sweep Detected (§8.1#3).  Pass-path, Pass-path: block established, sweep 20 pips above block HIGH, close below → SWEE (+59 more)

### Community 7 - "Schema Design ADRs"
Cohesion: 0.22
Nodes (10): ADR-002 — Phase-A core schema design, Consequences, Context, Decision, Key design choices, config_hash function, InstrumentConfig Dataclass, SpecConfig Dataclass (+2 more)

### Community 12 - "Timeframe Resampling"
Cohesion: 0.10
Nodes (31): _aggregate(), _d1_bucket(), _expected_d1_bars_approx(), _expected_h4_bars(), _h4_bucket(), Pure, deterministic H1-to-H4/D1 resampler.  Input rows are dicts with keys: ts (, Return the H4 bucket open timestamp for *ts* (00:00/04:00/…/20:00 UTC)., Return the D1 bucket open timestamp for *ts* (midnight UTC). (+23 more)

### Community 13 - "Database Persistence"
Cohesion: 0.12
Nodes (22): Executor, load_candles(), Candle-table loader.  Writes normalized OHLCV rows into the candle table using a, Minimal protocol for a DB cursor or test fake., Insert *rows* into the candle table via *executor*.      Returns the number of r, fake_executor(), FakeExecutor, Shared pytest fixtures. (+14 more)

### Community 14 - "Trend Validation Tests"
Cohesion: 0.17
Nodes (25): _bear_closes(), _bull_closes(), _d1_candles(), _default_ic(), _default_sp(), Golden gate-fixtures for Gate 1 — Trend State Confirmed (§8.1#1).  Each fixture, Near-miss 1: flat closes (EMAs converge) → compression → INVALID., Near-miss 2: long downtrend then a moderate reversal → recent EMA cross → INVALI (+17 more)

### Community 15 - "Signal Conjunction Tests"
Cohesion: 0.10
Nodes (48): _bar(), build_qualified_h1(), _d1(), _flat_h1(), _h4(), _ic(), A5 conjunction tests — §8.1 verbatim composition → SignalResult.  Covers:   - a, all_gates is exactly the AND of the 8 gate.passed flags (§8.1 verbatim). (+40 more)

### Community 16 - "Risk and Reward Gates"
Cohesion: 0.16
Nodes (17): evaluate(), Gate 7 — Risk:Reward Minimum (§8.1#7 · §9.1 · §9.4).  Structural stop (§9.1):, Return Gate 7 result for the LAST bar of *candles_h1* (the entry candle).      r, evaluate(), Gate 8 — Global Risk State Clear (§8.1#8 · §9.3 · §12).  M11 = TRADING_ALLOWED:, Return Gate 8 result.      atr_state:        ATR EXTREME forces no-trade (§4.2.2, AtrState, Volatility regime (§4.2.2 / §9.3 / §15.1).      Derived from current H1 ATR(14) (+9 more)

### Community 17 - "Gate Specifications"
Cohesion: 0.15
Nodes (12): Gate 1 — Trend State Confirmed  (§8.1#1 · §5.1 · §3.2), Gate 2 — Structure Confirmed  (§8.1#2 · §6.1.1), Gate 3 — Liquidity Sweep Detected  (§8.1#3 · §7.2 · §7.1.1), Gate 4 — EMA Interaction Confirmed  (§8.1#4), Gate 5 — Rejection Candle Confirmed  (§8.1#5 · §4.3), Gate 6 — Session Active  (§8.1#6 · §3.3), Gate 7 — Risk:Reward Minimum  (§8.1#7 · §9.1 · §9.4), Gate 8 — Global Risk State Clear  (§8.1#8 · §9.3 · §12) (+4 more)

### Community 18 - "Build Playbook"
Cohesion: 0.18
Nodes (10): 0. Goal, termination, and the two rules, 1. Phase structure (v3.0), 2. Environment (MT5 + Postgres already installed), 3. CLAUDE.md (governing file — create before any code; blueprint 15.2), 4. Doc manifest (all provided — seed into graphify), 5. The recursive build-and-validate loop (Phase A, A0–A11), 6. R-DECIDE — owner gate (human only), 7. Gate GA criteria (spec §17.1, tested out-of-sample per v2.1 Part 7.2) (+2 more)

### Community 19 - "ATR Volatility Analysis"
Cohesion: 0.13
Nodes (24): atr(), Wilder's ATR.  Candles are dicts with Decimal keys high, low, close.      TR[0], _ratio(), ATR-state classifier reference tests (§4.2.2 / §15.1 — ADR-011).  Two layers:, Volatile baseline then a calm tail → current ATR < 0.75× baseline → COMPRESSED., Realised current-ATR / prior-20-mean ratio (current bar excluded)., A bar at EXACTLY 2.0× the prior-20 mean lands on EXTREME., A bar at EXACTLY 1.95× the prior-20 mean stays ELEVATED — does NOT trip EXTREME. (+16 more)

### Community 20 - "Trading Session Tests"
Cohesion: 0.35
Nodes (14): _bar(), _btc(), _fx(), Golden gate-fixtures for Gate 6 — Session Active (§8.1#6 · §3.3).  Pass-path  :, 13:15 UTC: NY just opened (within edge buffer) but London is mid-session → valid, _sp(), test_session_crypto_24_7(), test_session_determinism() (+6 more)

### Community 21 - "Rejection Geometry ADRs"
Cohesion: 0.40
Nodes (4): ADR-004 — Bull rejection geometry: lower-wick hammer (§8.1 mirror), Consequences, Context, Decision

### Community 22 - "Swing Window ADRs"
Cohesion: 0.40
Nodes (4): ADR-005 — Swing-window half-width (spec-silent default), Consequences, Context, Decision

### Community 23 - "Macro Trend ADRs"
Cohesion: 0.40
Nodes (4): ADR-006 — Macro-trend gate ATR timeframe = D1 (extends ADR-003), Consequences, Context, Decision

### Community 26 - "Signal Persistence"
Cohesion: 0.22
Nodes (10): Protocol, Executor, _gate_cell(), persist_signals(), The single persistence boundary for the C2 signal engine (A5).  Every evaluated, NULL for a dependency short-circuit (ADR-002 'not evaluated'); else pass/fail., Map a SignalResult to the signal-table parameter tuple (deterministic order)., Write one signal row per result.  Returns the number of rows submitted.      Dup (+2 more)

### Community 27 - "Core Strategy Gates"
Cohesion: 0.14
Nodes (16): Gate 1 — Trend State Confirmed (§8.1#1 · §5.1 · §3.2 · ADR-003 · ADR-006).  Eval, evaluate(), _find_block_bear(), _find_block_bull(), Gate 3 — Liquidity Sweep Detected (§8.1#3 · §7.1.1 · §7.2).  Block (§7.1.1):   z, Return (block_low, block_high, touch_count) for the most recent valid BEAR block, Bull mirror: block_high = highest swing-low CLOSE, block_low = lowest swing-low, Return Gate 3 result for the LAST bar of *candles_h1*. (+8 more)

### Community 28 - "Sweep Score ADRs"
Cohesion: 0.33
Nodes (5): ADR-010 — Sweep-probability score: sub-factor formulas, Consequences, Context, Decision (proposed), Why this is safe to build now (not a HALT)

### Community 29 - "Volatility Regime ADRs"
Cohesion: 0.25
Nodes (7): ADR-011 — ATR-state classification (COMPRESSED / NORMAL / ELEVATED / EXTREME), Boundary is CI-guarded (golden fixture), Consequences, Context, Decision (pinned values), Implementation, Scope — governs *all* "20-period avg" baselines, not just M6

### Community 30 - "Signal Evaluation Engine"
Cohesion: 0.24
Nodes (20): Enum, evaluate(), §8.1 conjunction — evaluate all 8 gates on one H1 bar → SignalResult.  §8.1: all, Evaluate the §8.1 conjunction for the LAST H1 bar.  Returns a SignalResult., Best-effort §7.3 score when a block+sweep exist; else None (ADR-007 formulas)., _sweep_score_for(), Shared types for the C2 signal engine., Terminal classification of an evaluated candle (A5 persistence boundary). (+12 more)

### Community 31 - "Risk Tier Scoring"
Cohesion: 0.29
Nodes (10): RiskTier, _clamp01(), Sweep Probability Score — NOT a gate (§7.3 → §9.3 risk tier).  The 5-factor 0–10, Return the 0–100 sweep-probability score (Decimal).  ADR-007 formulas.      bloc, Map a sweep score to a §9.3 risk tier.      ATR EXTREME or a drawdown breach for, risk_tier_for(), score(), AtrState (+2 more)

### Community 32 - "Global Risk Tests"
Cohesion: 0.50
Nodes (8): _ic(), Golden gate-fixtures for Gate 8 — Global Risk State Clear (§8.1#8 · §9.3 · §12)., _sp(), test_gate8_atr_extreme_no_trade(), test_gate8_determinism(), test_gate8_elevated_still_passes(), test_gate8_stub_pass_normal(), test_gate8_trading_halted()

### Community 33 - "Session Validation"
Cohesion: 0.47
Nodes (5): evaluate(), _fx_bands(), Gate 6 — Session Active (§8.1#6 · §3.3).  Session VALID per §3.3 (all times UTC), Return Gate 6 result for a single H1 *candle* (uses candle['ts']).      *side* i, datetime

### Community 34 - "Market Structure Analysis"
Cohesion: 0.14
Nodes (21): _apex_proximity(), evaluate(), _find_declining_highs(), _find_resistance(), _find_rising_lows(), _find_support(), _pct_diff(), Gate 2 — Structure Confirmed (§8.1#2 · §6.1.1).  Evaluates the LAST bar of *cand (+13 more)

### Community 37 - "Rejection Candle Tests"
Cohesion: 0.33
Nodes (14): _bar(), _ic(), Golden gate-fixtures for Gate 5 — Rejection Candle Confirmed (§8.1#5 · §4.3 · AD, Upper wick 30 pips = 3×body, lower wick 1 pip, bearish, closes below sweep high., Bearish engulfing with a large upper wick and a NON-tiny lower wick.      Lower, ADR-004 mirror: lower wick ≥2×body, tiny upper wick, bullish, closes above sweep, _sp(), test_gate5_bear_rejection_pass() (+6 more)

### Community 39 - "ATR State Classification"
Cohesion: 0.36
Nodes (8): classify(), ATR-state classifier (§4.2.2 / §15.1 — ADR-011, Accepted).  Volatility regime fr, Map an ATR/baseline ratio to a regime (the pure threshold rule)., Classify the volatility regime at the LAST H1 bar.  Defaults to NORMAL on     in, state_for_ratio(), AtrState, Decimal, StrategyParams

## Knowledge Gaps
- **59 isolated node(s):** `lsb`, `Path`, `Namespace`, `LSB — Governing Instructions`, `Current session pointer` (+54 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **6 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `load_instrument()` connect `Configuration Subsystem` to `Global Risk Tests`, `CLI and Data Fetching`, `Strategy Constants and Gates`, `Rejection Candle Tests`, `Liquidity Sweep Logic`, `Signal Conjunction Tests`, `Trading Session Tests`?**
  _High betweenness centrality (0.268) - this node is a cross-community bridge._
- **Why does `cmd_fetch_audit_load()` connect `CLI and Data Fetching` to `Configuration Subsystem`, `Timeframe Resampling`, `Gap Detection and Audit`, `Database Persistence`?**
  _High betweenness centrality (0.246) - this node is a cross-community bridge._
- **Why does `InstrumentConfig` connect `Strategy Constants and Gates` to `Configuration Subsystem`, `Session Validation`, `Market Structure Analysis`, `Liquidity Sweep Logic`, `Risk and Reward Gates`, `Core Strategy Gates`, `Signal Evaluation Engine`?**
  _High betweenness centrality (0.154) - this node is a cross-community bridge._
- **Are the 67 inferred relationships involving `D()` (e.g. with `_ratio()` and `_series()`) actually correct?**
  _`D()` has 67 INFERRED edges - model-reasoned connections that need verification._
- **Are the 67 inferred relationships involving `StrategyParams` (e.g. with `RiskTier` and `SpecConfig`) actually correct?**
  _`StrategyParams` has 67 INFERRED edges - model-reasoned connections that need verification._
- **Are the 49 inferred relationships involving `GateResult` (e.g. with `Executor` and `AtrState`) actually correct?**
  _`GateResult` has 49 INFERRED edges - model-reasoned connections that need verification._
- **Are the 55 inferred relationships involving `Side` (e.g. with `AtrState` and `Decimal`) actually correct?**
  _`Side` has 55 INFERRED edges - model-reasoned connections that need verification._