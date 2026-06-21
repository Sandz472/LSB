# LSB — Canonical Gate Specification (the original strategy)

- **Version:** v2.0-faithful (new project)
- **Date:** 2026-06-20
- **Universe:** EURUSD, GBPUSD, XAUUSD, BTCUSD
- **Source of truth:** **LSB System Requirements v2.0**, the immutable spec. Gate
  definitions are §8.1; parameters from §3–§9. Where the v2.1 blueprint or the
  prior code restated a gate differently, **v2.0 governs** and the divergence is
  recorded in §R below.

> All eight §8.1 conditions must be TRUE on the same H1 bar. A single FALSE
> disqualifies. Conditions below are the **bearish (short)** setup; the
> **bullish (long)** setup is the exact mirror (§8.1 footnote).

---

## Gate 1 — Trend State Confirmed  (§8.1#1 · §5.1 · §3.2)

M3 trend = **BEARISH**: `EMA21 < EMA50 < EMA89` AND slope(EMA21) NEGATIVE AND
slope(EMA50) NEGATIVE. NEUTRAL and INVALID are hard blockers (§5.1).
INVALID when EMA compression `|EMA21−EMA89| < ATR×0.10` (§5.2) or an EMA21/EMA50
cross within the last 3 candles. Slope threshold = ATR×0.05 over 3 candles (§4.1.2).
**The ATR in both thresholds is D1 ATR(14)** (ADR-006).

**Timeframe:** Gate 1 macro trend is evaluated on **Daily (D1)** — owner-resolved
in **ADR-003** (`spec.trend_timeframe = "D1"`), faithful to §3.2 "Macro Context:
Daily." §4.1 computes the EMAs on H1 for the indicator engine; those H1 EMAs are
consumed by Gate 4 (EMA-Interaction), not Gate 1. **ADR-006** extends this: Gate 1's
ATR-relative thresholds (slope §4.1.2, compression §5.2) use **D1 ATR(14)** — same
timeframe as the series they scale — while H1 ATR is retained for execution-scale
uses (Gate 6 ATR-state, §7.3 sweep factor, §9.1 stop buffer, §9.4 R:R ATR×3). The
D1-vs-H1 wording was a spec ambiguity, now closed.

Bull mirror: BULLISH.

---

## Gate 2 — Structure Confirmed  (§8.1#2 · §6.1.1)

M4 = `ASCENDING_TRIANGLE` on **H4**, with **all** §6.1.1 parameters:

| Parameter | Spec value |
|---|---|
| Resistance level | ≥2 swing highs within **±0.15%** of each other (configurable); 3+ preferred |
| Rising lows | ≥2 higher lows, each **≥0.20%** above the prior low |
| Duration | 8–60 H4 candles |
| Compression | current candle range ≤ **60%** of first candle range |
| Apex proximity | **75%–95%** of the way to the convergence apex |
| **Invalidation** | pattern invalidated if price **closes >0.30% above resistance** without returning below → `INVALIDATED` → `NONE` |

Bull mirror: `DESCENDING_TRIANGLE` (§6.1.2), invalidation on a close >0.30% below
support.

---

## Gate 3 — Liquidity Sweep Detected  (§8.1#3 · §7.2 · §7.1.1)

**Block (§7.1.1):** zone between the **lowest swing-high close** and the
**highest swing-high wick**; width = highest swing-high wick − lowest swing-high
close; min width **5 pips (fx) / 0.05% (crypto)**; **≥2 touches**.

**Sweep (§7.2):**
- wick extends **ABOVE the resistance block HIGH** (= highest swing-high wick) by **≥2 pips / 0.02%**, AND
- candle **closes below the block high** (inside or below the block), AND
- within the last **3 H1 candles** (sweep expiry), AND
- false-sweep filter: invalid if price later closes **beyond the block in the sweep direction**.

> **Sweep target is the block HIGH, not a mean level.** (See §R: ADR-006 diverged.)

Bull mirror: wick below the support block LOW, close above it.

---

## Gate 4 — EMA Interaction Confirmed  (§8.1#4)

The **sweep candle or the confirmation candle HIGH** touches/penetrates EMA21 or
EMA50 — candle high within **3 pips / 0.03%** of the EMA value. Bull mirror:
candle LOW within range of an EMA.

> This is a **hard gate** in §8.1. The prior build dropped it and instead used the
> sweep-probability score as gate 4 (see §R).

---

## Gate 5 — Rejection Candle Confirmed  (§8.1#5 · §4.3)

Candle type = `REJECTION_BEAR` **or** `ENGULFING_BEAR`; close is bearish; candle
**closes below the sweep high**; **upper wick ≥ 2× body**.

§4.3 definitions: `REJECTION_BEAR` = upper wick ≥2×body AND lower wick ≤0.3×body
AND close bearish. `ENGULFING_BEAR` = body engulfs prior body AND close < prior
open. (The upper-wick ≥2×body requirement in §8.1 applies even to the engulfing
case — engulfing alone does not exempt it.)

> **Spec-internal inconsistency — RESOLVED (ADR-004).** The bull mirror in §8.1
> ("lower wick ≥ 2× body") and the glossary ("rejection by wick direction") say a
> **bull** rejection is a **lower-wick** candle, while §4.3 defined
> `REJECTION_BULL` by an **upper** wick. Owner ruling: the **§8.1 mirror governs** —
> `REJECTION_BULL` = lower wick ≥ 2×body AND upper wick ≤ 0.3×body AND close bullish
> (exact mirror of `REJECTION_BEAR`); §4.3's upper-wick definition is the defect,
> amended by ADR-004 (`spec.rejection_geometry = "section_8_1_mirror"`). The short
> side is unchanged.

---

## Gate 6 — Session Active  (§8.1#6 · §3.3)

Session VALID per §3.3 (UTC): London 07:00–16:00; New York 13:00–21:00; Overlap
13:00–16:00; Asia 00:00–09:00 (**JPY pairs only**); **Crypto 24/7**. Not within
**30 min** of a session open/close (default BLOCKED). Not within **60 min** of a
Tier-1 news event (M12 — Phase-A stub).

> Crypto is 24/7 in the spec; the prior build applied FX session bands uniformly
> to BTC (see §R).

---

## Gate 7 — Risk:Reward Minimum  (§8.1#7 · §9.1 · §9.4)

Structural stop (§9.1): bear → **rejection-candle wick high + 2 pip / 0.02%
buffer** (4 pip / 0.04% if ATR ELEVATED). Target hierarchy (§9.4): 2.5R floor /
next liquidity pool / ATR×3 — closest candidate not below 2.5R. **PASS iff
R:R ≥ 2.5.**

---

## Gate 8 — Global Risk State Clear  (§8.1#8 · §9.3 · §12)

M11 = `TRADING_ALLOWED`: daily/weekly drawdown not breached; consecutive-loss
limit not hit. **Phase-A:** documented stub-pass (no live account). The
**ATR EXTREME → no trade** rule (§4.2.2 / §9.3 risk tier = 0%) is an active
pre-filter regardless.

---

## Not a gate — Sweep Probability Score  (§7.3 → §9.3 risk tier)

The 5-factor 0–100 score (density 30 / wick 20 / close 20 / EMA 15 / ATR 15)
**sets the risk tier, it does not qualify the trade**: 80–100 → 1.0%, 50–79 →
0.5%, <50 → 0.25% **or skip** (§9.3). ATR EXTREME / drawdown breach → 0%.
In a Phase-A backtest with no sizing, record the score; the only
qualification-relevant use is the discretionary "skip <50."

> The prior build promoted "score ≥ 50" to a **hard gate 4** — not what §7.3/§8.1
> say (see §R).

---

## Per-instrument configuration (4 instruments)

| Param | EURUSD | GBPUSD | XAUUSD | BTCUSD | Spec |
|---|---|---|---|---|---|
| class | FX major | FX major | commodity | crypto | §3.1 |
| pip_size | 0.0001 | 0.0001 | per config | 0.01 | §3.1 |
| max_spread | 1.5 pips | 1.5 pips | per config | 0.05% | §3.1 |
| sessions | FX (§3.3) | FX (§3.3) | FX (§3.3) | **24/7** | §3.3 |
| flat tolerance | 0.15% | 0.15% | 0.15% | 0.15% | §6.1.1 (configurable) |
| sweep penetration | 2 pips | 2 pips | 2 pips | 0.02% | §7.2 |
| block min width | 5 pips | 5 pips | 5 pips | 0.05% | §7.1.1 |
| stop buffer | 2 pip (4 elev.) | 2 pip (4 elev.) | 2 pip (4 elev.) | 0.02% (0.04% elev.) | §9.1 |
| source | dukascopy | dukascopy | dukascopy | binance | — |

**GBPUSD is a natively-supported instrument** (§3.1 lists EURUSD, GBPUSD, USDJPY
as Forex Majors) — no Appendix-A-change ADR is needed; it simply needs its config
file and a 3y Dukascopy audit. XAUUSD is not enumerated in §3.1's classes; treat
it as a configured commodity and record that choice. The **0.15% flat tolerance
is the spec baseline for all four** — it is "configurable," but the validation
baseline is 0.15%.

---

## §R — Reconciliation: prior build vs. the immutable spec

| Item | Spec says | Prior build | Verdict |
|---|---|---|---|
| Gate 1 timeframe (ADR-007→**ADR-003**) | Macro = Daily (§3.2) | Daily | **Faithful** — owner-confirmed D1 (ADR-003) |
| Rising lows (ADR-004) | ≥2 higher lows ≥0.20% (§6.1.1) | noise-tolerant climb, 2 points | **Faithful** (confirm "2 lows" = 2 events vs 2 points) |
| Rejection geometry (ADR-009→**ADR-004**) | §8.1 mirror: bull = lower wick | code matched §4.3 (upper) | **Resolved (ADR-004)** — §8.1 mirror governs; §4.3 bull def is the defect |
| Gate set | §8.1 = {Trend, Structure, Sweep, **EMA-Interaction**, Rejection, Session, **R:R**, **Global-Risk**} | {…, **Sweep-score**, …, **Volatility**, …}; EMA-interaction gate **missing** | **Divergent** — restore §8.1 gate set |
| Sweep score | risk-tier selector (§7.3) | hard gate 4 (≥50) | **Divergent** |
| Flat tolerance (ADR-005) | **0.15%** (§6.1.1) | 0.5% / 1.0% / 2.0% | **Divergent** (3–13× loose) — baseline must be 0.15%; looser only as a pre-registered sweep variable |
| Sweep target (ADR-006) | **block HIGH** (§7.2) | mean-of-wicks "level" | **Divergent** — revert; if ~0 sweeps result, that is the finding |
| Approach-from-below (ADR-008) | not in §7.2; mechanism is the §6.1.1 **Invalidation rule** | added a non-spec rule; invalidation rule **omitted** | **Divergent** — implement invalidation; reconsider ADR-008 |
| Sessions | §3.3 bands; Crypto 24/7; Asia JPY-only | uniform FX bands incl. BTC | **Divergent** — align to §3.3 |

**Implication.** The strategy *as written* is **tighter** than the loosened code
(0.15% flatness, sweep vs the block high, a hard EMA-interaction gate, the
invalidation rule). The prior build's loosenings drift away from the immutable
spec toward manufacturing trades — the exact contamination Phase A exists to
prevent. A clean validation implements §8.1 **verbatim**, measures the funnel, and
accepts the verdict (which may well be INSUFFICIENT). Any loosening is a
pre-registered, owner-signed proposal in `docs/decisions/` — never a silent
baseline.
