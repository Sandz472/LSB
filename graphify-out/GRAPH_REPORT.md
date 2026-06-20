# Graph Report - .  (2026-06-20)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 64 nodes · 99 edges · 9 communities
- Extraction: 0% EXTRACTED · 0% INFERRED · 0% AMBIGUOUS
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Governing Specs, Rules & Tooling|Governing Specs, Rules & Tooling]]
- [[_COMMUNITY_Phase Progression & Live Path|Phase Progression & Live Path]]
- [[_COMMUNITY_Market Data & Instruments|Market Data & Instruments]]
- [[_COMMUNITY_Failure & Owner Escalation|Failure & Owner Escalation]]
- [[_COMMUNITY_Gate Specification & Conjunction|Gate Specification & Conjunction]]
- [[_COMMUNITY_SignalBacktest Build & Reconciliation|Signal/Backtest Build & Reconciliation]]
- [[_COMMUNITY_SweepEMA Gates & Prior-Build Drift|Sweep/EMA Gates & Prior-Build Drift]]
- [[_COMMUNITY_Determinism & Config Hashing|Determinism & Config Hashing]]
- [[_COMMUNITY_Global-Risk Gate & Sweep Score|Global-Risk Gate & Sweep Score]]

## God Nodes (most connected - your core abstractions)

## Surprising Connections (you probably didn't know these)
- `BUILD_PLAYBOOK.md` --references_companion--> `GATE_SPECIFICATION.md`  [1.0]
   →   _Bridges community 0 → community 4_
- `GATE_SPECIFICATION.md` --defines--> `Gate 2 — Structure`  [1.0]
   →   _Bridges community 4 → community 7_
- `GATE_SPECIFICATION.md` --defines--> `Gate 6 — Session Active`  [1.0]
   →   _Bridges community 4 → community 1_
- `GATE_SPECIFICATION.md` --defines--> `Gate 8 — Global Risk Clear`  [1.0]
   →   _Bridges community 4 → community 11_
- `§17.1 GA Threshold Bar` --derives_from--> `System Requirements v2.0`  [1.0]
   →   _Bridges community 0 → community 3_

## Import Cycles
- None detected.

## Communities (9 total, 0 thin omitted)

### Community 0 - "Governing Specs, Rules & Tooling"
Cohesion: 0.32
Nodes (8): Master Blueprint v2.1, BUILD_PLAYBOOK.md, CLAUDE.md (governing), .claude/settings.local.json, graphify knowledge base, Redesign v3.0, Rule 1 — Spec Immutability, System Requirements v2.0

### Community 1 - "Phase Progression & Live Path"
Cohesion: 0.67
Nodes (3): Gate 6 — Session Active, BTCUSD, Binance

### Community 2 - "Market Data & Instruments"
Cohesion: 0.70
Nodes (5): EURUSD, GBPUSD, XAUUSD, C1 Data, Dukascopy

### Community 3 - "Failure & Owner Escalation"
Cohesion: 0.24
Nodes (10): ADR-002 go/no-go, Spec Defect: §17.1 minimum trade count undefined, §17.1 GA Threshold Bar, Gate GA, HALT-HUMAN, C5 Verdict, R-DECIDE (owner gate), Rule 2 — Physics / No Loosening (+2 more)

### Community 4 - "Gate Specification & Conjunction"
Cohesion: 0.36
Nodes (8): Spec Defect: §4.3 vs §8.1 rejection geometry, Spec Ambiguity: D1 vs H1 trend timeframe, Gate 1 — Trend State, Gate 4 — EMA Interaction, Gate 5 — Rejection Candle, Gate 7 — Risk:Reward Minimum, §8.1 Gate Conjunction, GATE_SPECIFICATION.md

### Community 5 - "Signal/Backtest Build & Reconciliation"
Cohesion: 0.20
Nodes (11): ADR-001 broker bridge, C2 Signal Engine, C3 Backtest, Phase A — Prove (wk 1–3), Phase B (wk 4–13), Phase C (wk 13+), PHASE_STATUS.md, §R Reconciliation (+3 more)

### Community 7 - "Sweep/EMA Gates & Prior-Build Drift"
Cohesion: 0.40
Nodes (6): Block HIGH (sweep target), Flat Tolerance 0.15%, Gate 2 — Structure, Gate 3 — Liquidity Sweep, Invalidation Rule (§6.1.1/.2), Prior-Build Drift

### Community 8 - "Determinism & Config Hashing"
Cohesion: 0.25
Nodes (9): config_hash, Determinism Law, GA-1 Determinism Gate (A8 CI), 001_core.sql, C4 Walk-Forward, candle table, config_version table, signal table (+1 more)

### Community 11 - "Global-Risk Gate & Sweep Score"
Cohesion: 0.50
Nodes (4): ATR EXTREME → No-Trade Pre-filter (§4.2.2/§9.3), Gate 8 — Global Risk Clear, Risk Tier (§9.3 position sizing), Sweep Probability Score (not a gate)

## Suggested Questions
_Not enough signal to generate questions. This usually means the corpus has no AMBIGUOUS edges, no bridge nodes, no INFERRED relationships, and all communities are tightly cohesive. Add more files or run with --mode deep to extract richer edges._