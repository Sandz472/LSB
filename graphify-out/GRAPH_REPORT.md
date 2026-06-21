# Graph Report - LSB  (2026-06-21)

## Corpus Check
- 65 files · ~39,192 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 747 nodes · 1760 edges · 30 communities (24 shown, 6 thin omitted)
- Extraction: 65% EXTRACTED · 29% INFERRED · 0% AMBIGUOUS · INFERRED: 512 edges (avg confidence: 0.63)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `ad686b2a`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- [[_COMMUNITY_Config Hashing & Tests|Config Hashing & Tests]]
- [[_COMMUNITY_§8.1 Gate Logic|§8.1 Gate Logic]]
- [[_COMMUNITY_Phase-A Data & Modules|Phase-A Data & Modules]]
- [[_COMMUNITY_Config Loader & Models|Config Loader & Models]]
- [[_COMMUNITY_Verdict & Phase Gating|Verdict & Phase Gating]]
- [[_COMMUNITY_Project Docs & ADRs|Project Docs & ADRs]]
- [[_COMMUNITY_Governing Specs & Rules|Governing Specs & Rules]]
- [[_COMMUNITY_A1 Schema Design|A1 Schema Design]]
- [[_COMMUNITY_Smoke Test|Smoke Test]]
- [[_COMMUNITY_Package Init|Package Init]]
- [[_COMMUNITY_CI Workflow|CI Workflow]]
- [[_COMMUNITY_LSB Package Root|LSB Package Root]]
- [[_COMMUNITY_Community 12|Community 12]]
- [[_COMMUNITY_Community 13|Community 13]]
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

## God Nodes (most connected - your core abstractions)
1. `D()` - 73 edges
2. `GateResult` - 70 edges
3. `StrategyParams` - 69 edges
4. `Side` - 67 edges
5. `InstrumentConfig` - 64 edges
6. `AtrState` - 30 edges
7. `load_instrument()` - 28 edges
8. `fetch_history()` - 23 edges
9. `load_strategy()` - 21 edges
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

## Communities (30 total, 6 thin omitted)

### Community 0 - "Config Hashing & Tests"
Cohesion: 0.09
Nodes (42): _canonical_value(), config_hash(), Deterministic sha256 config_hash.  Invariant: same field values → same hex diges, Return sha256 of the canonical combined JSON of all *cfgs*.      Each config is, LSB config subsystem — public re-exports., _d(), load_instrument(), load_spec() (+34 more)

### Community 1 - "§8.1 Gate Logic"
Cohesion: 0.05
Nodes (63): ADR-001 broker bridge, ADR-002 go/no-go, ATR EXTREME → No-Trade Pre-filter (§4.2.2/§9.3), Block HIGH (sweep target), Master Blueprint v2.1, BUILD_PLAYBOOK.md, CLAUDE.md (governing), .claude/settings.local.json (+55 more)

### Community 2 - "Phase-A Data & Modules"
Cohesion: 0.08
Nodes (40): cmd_fetch_audit_load(), _default_path(), main(), CLI entry point: fetch → audit → load for a single instrument.  Usage:     pytho, Resolve *relative* against the repo root (3 levels up from this file)., CachedSeries, _csv_to_rows(), fetch_history() (+32 more)

### Community 3 - "Config Loader & Models"
Cohesion: 0.05
Nodes (126): InstrumentConfig, Universal strategy constants from §5.1 / §6.1.1 / §7.2 / §8.1.      All threshol, StrategyParams, Enum, RiskTier, evaluate(), §8.1 conjunction — evaluate all 8 gates on one H1 bar → SignalResult.  §8.1: all, Best-effort §7.3 score when a block+sweep exist; else None (ADR-007 formulas). (+118 more)

### Community 4 - "Verdict & Phase Gating"
Cohesion: 0.07
Nodes (57): audit_history(), AuditReport, classify_gap(), GapRecord, _is_dst_gap(), _is_holiday_gap(), _is_weekend_gap(), Gap detection and mandatory disposition for H1 OHLCV series.  Every gap > 2 bars (+49 more)

### Community 5 - "Project Docs & ADRs"
Cohesion: 0.11
Nodes (18): ADR-004 — Bull rejection geometry: lower-wick hammer, BTCUSD Configuration, LSB Build Playbook, LSB Governing Instructions, ADR-001 — Broker Bridge: native-Windows MT5, Consequences, Context, Decision (+10 more)

### Community 6 - "Governing Specs & Rules"
Cohesion: 0.07
Nodes (60): ema(), EMA with SMA seed.  Returns None for the first period-1 positions.      Seed  =, _build_bear_sweep_series(), _default_ic(), _default_sp(), _h1(), Golden gate-fixtures for Gate 3 — Liquidity Sweep Detected (§8.1#3).  Pass-path, Pass-path: block established, sweep 20 pips above block HIGH, close below → SWEE (+52 more)

### Community 7 - "A1 Schema Design"
Cohesion: 0.22
Nodes (10): ADR-002 — Phase-A core schema design, Consequences, Context, Decision, Key design choices, config_hash function, InstrumentConfig Dataclass, SpecConfig Dataclass (+2 more)

### Community 12 - "Community 12"
Cohesion: 0.10
Nodes (31): _aggregate(), _d1_bucket(), _expected_d1_bars_approx(), _expected_h4_bars(), _h4_bucket(), Pure, deterministic H1-to-H4/D1 resampler.  Input rows are dicts with keys: ts (, Return the H4 bucket open timestamp for *ts* (00:00/04:00/…/20:00 UTC)., Return the D1 bucket open timestamp for *ts* (midnight UTC). (+23 more)

### Community 13 - "Community 13"
Cohesion: 0.12
Nodes (22): Executor, load_candles(), Candle-table loader.  Writes normalized OHLCV rows into the candle table using a, Minimal protocol for a DB cursor or test fake., Insert *rows* into the candle table via *executor*.      Returns the number of r, fake_executor(), FakeExecutor, Shared pytest fixtures. (+14 more)

### Community 14 - "Community 14"
Cohesion: 0.17
Nodes (25): _bear_closes(), _bull_closes(), _d1_candles(), _default_ic(), _default_sp(), Golden gate-fixtures for Gate 1 — Trend State Confirmed (§8.1#1).  Each fixture, Near-miss 1: flat closes (EMAs converge) → compression → INVALID., Near-miss 2: long downtrend then a moderate reversal → recent EMA cross → INVALI (+17 more)

### Community 15 - "Community 15"
Cohesion: 0.10
Nodes (46): _bar(), build_qualified_h1(), _d1(), _flat_h1(), _h4(), _ic(), A5 conjunction tests — §8.1 verbatim composition → SignalResult.  Covers:   - a, all_gates is exactly the AND of the 8 gate.passed flags (§8.1 verbatim). (+38 more)

### Community 16 - "Community 16"
Cohesion: 0.24
Nodes (19): _default_ic(), _default_sp(), _find_ema21_at_bar(), _h1_series(), Decimal, Golden gate-fixtures for Gate 4 — EMA Interaction Confirmed (§8.1#4).  Gate 4 is, Near-miss 1: bar high is 20 pips above EMA21/50 → NO_EMA_TOUCH., Near-miss 2: sweep_bar and eval bar both far from EMAs → NO_EMA_TOUCH. (+11 more)

### Community 17 - "Community 17"
Cohesion: 0.15
Nodes (12): Gate 1 — Trend State Confirmed  (§8.1#1 · §5.1 · §3.2), Gate 2 — Structure Confirmed  (§8.1#2 · §6.1.1), Gate 3 — Liquidity Sweep Detected  (§8.1#3 · §7.2 · §7.1.1), Gate 4 — EMA Interaction Confirmed  (§8.1#4), Gate 5 — Rejection Candle Confirmed  (§8.1#5 · §4.3), Gate 6 — Session Active  (§8.1#6 · §3.3), Gate 7 — Risk:Reward Minimum  (§8.1#7 · §9.1 · §9.4), Gate 8 — Global Risk State Clear  (§8.1#8 · §9.3 · §12) (+4 more)

### Community 18 - "Community 18"
Cohesion: 0.18
Nodes (10): 0. Goal, termination, and the two rules, 1. Phase structure (v3.0), 2. Environment (MT5 + Postgres already installed), 3. CLAUDE.md (governing file — create before any code; blueprint 15.2), 4. Doc manifest (all provided — seed into graphify), 5. The recursive build-and-validate loop (Phase A, A0–A11), 6. R-DECIDE — owner gate (human only), 7. Gate GA criteria (spec §17.1, tested out-of-sample per v2.1 Part 7.2) (+2 more)

### Community 19 - "Community 19"
Cohesion: 0.10
Nodes (20): evaluate(), _find_block_bear(), _find_block_bull(), Gate 3 — Liquidity Sweep Detected (§8.1#3 · §7.1.1 · §7.2).  Block (§7.1.1):   z, Return (block_low, block_high, touch_count) for the most recent valid BEAR block, Bull mirror: block_high = highest swing-low CLOSE, block_low = lowest swing-low, Return Gate 3 result for the LAST bar of *candles_h1*., True iff candle i has strictly the lowest `low` in [i-lookback, i+lookback]. (+12 more)

### Community 20 - "Community 20"
Cohesion: 0.35
Nodes (14): _bar(), _btc(), _fx(), Golden gate-fixtures for Gate 6 — Session Active (§8.1#6 · §3.3).  Pass-path  :, 13:15 UTC: NY just opened (within edge buffer) but London is mid-session → valid, _sp(), test_session_crypto_24_7(), test_session_determinism() (+6 more)

### Community 21 - "Community 21"
Cohesion: 0.40
Nodes (4): ADR-004 — Bull rejection geometry: lower-wick hammer (§8.1 mirror), Consequences, Context, Decision

### Community 22 - "Community 22"
Cohesion: 0.40
Nodes (4): ADR-005 — Swing-window half-width (spec-silent default), Consequences, Context, Decision

### Community 23 - "Community 23"
Cohesion: 0.40
Nodes (4): ADR-006 — Macro-trend gate ATR timeframe = D1 (extends ADR-003), Consequences, Context, Decision

### Community 26 - "Community 26"
Cohesion: 0.20
Nodes (10): Protocol, Executor, _gate_cell(), persist_signals(), NULL for a dependency short-circuit (ADR-002 'not evaluated'); else pass/fail., Map a SignalResult to the signal-table parameter tuple (deterministic order)., Write one signal row per result.  Returns the number of rows submitted.      Dup, to_row() (+2 more)

### Community 27 - "Community 27"
Cohesion: 0.50
Nodes (8): _ic(), Golden gate-fixtures for Gate 8 — Global Risk State Clear (§8.1#8 · §9.3 · §12)., _sp(), test_gate8_atr_extreme_no_trade(), test_gate8_determinism(), test_gate8_elevated_still_passes(), test_gate8_stub_pass_normal(), test_gate8_trading_halted()

### Community 28 - "Community 28"
Cohesion: 0.33
Nodes (5): ADR-010 — Sweep-probability score: sub-factor formulas, Consequences, Context, Decision (proposed), Why this is safe to build now (not a HALT)

### Community 29 - "Community 29"
Cohesion: 0.40
Nodes (4): ADR-011 — ATR-state classification (NORMAL / ELEVATED / EXTREME), Consequences, Context, Decision

## Knowledge Gaps
- **57 isolated node(s):** `lsb`, `Path`, `Namespace`, `LSB — Governing Instructions`, `Current session pointer` (+52 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **6 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `load_instrument()` connect `Config Hashing & Tests` to `Phase-A Data & Modules`, `Config Loader & Models`, `Governing Specs & Rules`, `Community 15`, `Community 20`, `Community 27`?**
  _High betweenness centrality (0.276) - this node is a cross-community bridge._
- **Why does `cmd_fetch_audit_load()` connect `Phase-A Data & Modules` to `Config Hashing & Tests`, `Community 12`, `Verdict & Phase Gating`, `Community 13`?**
  _High betweenness centrality (0.251) - this node is a cross-community bridge._
- **Why does `InstrumentConfig` connect `Config Loader & Models` to `Config Hashing & Tests`, `Community 16`, `Community 19`?**
  _High betweenness centrality (0.167) - this node is a cross-community bridge._
- **Are the 59 inferred relationships involving `D()` (e.g. with `_bar()` and `build_qualified_h1()`) actually correct?**
  _`D()` has 59 INFERRED edges - model-reasoned connections that need verification._
- **Are the 49 inferred relationships involving `GateResult` (e.g. with `Executor` and `AtrState`) actually correct?**
  _`GateResult` has 49 INFERRED edges - model-reasoned connections that need verification._
- **Are the 64 inferred relationships involving `StrategyParams` (e.g. with `RiskTier` and `SpecConfig`) actually correct?**
  _`StrategyParams` has 64 INFERRED edges - model-reasoned connections that need verification._
- **Are the 55 inferred relationships involving `Side` (e.g. with `AtrState` and `Decimal`) actually correct?**
  _`Side` has 55 INFERRED edges - model-reasoned connections that need verification._