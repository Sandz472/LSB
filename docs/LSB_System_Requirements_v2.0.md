> Auto-converted from LSB_System_Requirements_v2.0.docx for the graphify corpus. The .docx remains the canonical immutable spec.

LIQUIDITY STRATEGY BOT

System Requirements & Technical Specification

Version 2.0 — Full Build Specification

─────────────────────────────

For Developers, Programmers & System Architects

This document serves as the authoritative specification. No assumptions.

"Protect capital first. Profitability is the outcome of controlled risk."

# SECTION 1 — PURPOSE, SCOPE & DOCUMENT INTENT

## 1.1 Document Purpose

This document is the complete technical and operational specification for the Liquidity Strategy Bot (LSB). It is written to eliminate ambiguity and ensure that every engineer, developer, and programmer working on this system has an unambiguous, machine-actionable reference for all logic, rules, thresholds, behaviors, and decision trees.

This document supersedes all verbal instructions, summaries, or informal descriptions. Where any conflict exists, this document is the authority.

## 1.2 Audience

Audience

Usage of this Document

Backend Engineers

Implement all logic modules, data pipelines, execution handlers, and risk engines as specified

Frontend / Dashboard Developers

Build monitoring UI, alert systems, and configuration interfaces aligned to specified state variables

QA / Testing Engineers

Design test cases for every rule branch, threshold, and state transition defined herein

System Architects

Design infrastructure to support real-time data feeds, latency requirements, and failover logic

AI / Prompt Engineers

Use this specification as the sole context source when prompting LLMs for code generation or logic derivation

## 1.3 Critical Assumptions Forbidden

The bot shall not assume any of the following:

- That a market condition exists unless it is algorithmically confirmed by the precise criteria in this document.

- That a trade is valid unless every single entry condition in Section 6 evaluates to TRUE.

- That risk parameters are acceptable unless explicitly computed against the thresholds in Section 9.

- That a session is active unless validated per the session schedule in Section 5.

- That prior profitable behavior justifies relaxing any rule under any circumstance.

# SECTION 2 — SYSTEM ARCHITECTURE OVERVIEW

## 2.1 Module Map

The LSB is composed of the following logical modules. Each module is independent, testable, and must function correctly in isolation before integration.

ID

Module Name

Responsibility

M1

Market Data Ingestion

Real-time OHLCV feed, tick data, spread, and session time management

M2

Indicator Engine

EMA calculation (21/50/89), ATR, slope computation, candle classification

M3

Trend Analysis Engine

EMA hierarchy validation, slope direction assessment, trend state assignment

M4

Structure Detection Engine

Triangle identification, compression validation, swing point mapping

M5

Liquidity Zone Engine

Resistance / support block identification, sweep detection, zone density scoring

M6

Volatility Monitor

ATR state tracking, candle size analysis, spread and slippage monitoring

M7

Entry Qualification Engine

Sequential evaluation of all entry conditions; returns QUALIFIED / REJECTED

M8

Risk Computation Engine

Position sizing, stop loss calculation, R:R validation, drawdown checks

M9

Order Execution Handler

Broker API interface, order placement, modification, cancellation

M10

Trade Management Engine

Post-entry monitoring, breakeven logic, trailing stop, partial exit

M11

Risk Protection Controller

Global drawdown enforcement, loss streak tracking, emergency halt logic

M12

Session & Market Filter

Active session validation, news event filtering, low-liquidity rejection

M13

Logging & Analytics Engine

Trade journaling, performance metrics, regime tracking, audit trail

M14

Alerting & Notification System

Real-time status, trade alerts, halt notifications, error reporting

## 2.2 Data Flow Sequence

The following describes the mandatory sequence in which modules execute on each new candle close. No step may be skipped. If any module fails to return a valid result, the sequence halts and no trade is executed.

- M1 delivers a new closed candle with OHLCV, timestamp, current spread, and session state.

- M2 recalculates all indicators: EMA21, EMA50, EMA89, ATR(14), candle body/wick ratios.

- M3 evaluates trend state: BULLISH / BEARISH / NEUTRAL / INVALID.

- M4 evaluates structure state: ASCENDING_TRIANGLE / DESCENDING_TRIANGLE / NONE.

- M5 evaluates liquidity zone presence and sweep occurrence.

- M6 evaluates volatility state: NORMAL / ELEVATED / EXTREME.

- M12 evaluates session validity: VALID / INVALID.

- M11 evaluates global risk state: TRADING_ALLOWED / HALT.

- M7 performs full entry qualification only if all upstream modules return acceptable states.

- M8 computes position size and validates R:R only if M7 returns QUALIFIED.

- M9 places order only if M8 returns VALID_RISK.

- M10 takes over post-entry and manages the open trade until closure.

- M13 logs all states and outcomes regardless of whether a trade was executed.

# SECTION 3 — INSTRUMENT & SESSION SPECIFICATIONS

## 3.1 Supported Instruments

The LSB is initially designed for the following instrument classes. Each instrument must have its own configuration file specifying pip value, spread threshold, ATR baseline, and session validity.

Instrument Class

Examples

Pip / Tick Size

Spread Max (pips)

ATR Baseline

Forex Majors

EURUSD, GBPUSD, USDJPY

0.0001 / 0.01

1.5

Configurable per pair

Forex Minors

EURGBP, AUDCAD

0.0001

2.0

Configurable per pair

Indices (CFDs)

US30, SPX500, NAS100

1.0 / 0.1

Instrument-specific

Configurable

Crypto (spot/perp)

BTCUSDT, ETHUSDT

0.01 / 0.1

0.05%

Configurable

⚠  Each instrument's thresholds MUST be configured before the bot operates on that instrument. The bot shall refuse to execute on any instrument without a complete configuration file.

## 3.2 Timeframe Specification

The LSB operates on a primary execution timeframe and references higher timeframes for structural confirmation.

Timeframe Role

Timeframe

Purpose

Macro Context

Daily (D1)

Macro trend direction; EMA hierarchy for overall bias

Structural Context

4-Hour (H4)

Triangle formation confirmation; key liquidity zone mapping

Primary Execution

1-Hour (H1)

Entry qualification, EMA interaction, candle confirmation

Entry Refinement (Optional)

15-Minute (M15)

Entry precision refinement only; not used for structure decisions

⚠  All entry conditions are evaluated on the primary execution timeframe (H1) unless explicitly stated otherwise. Higher timeframe alignment is a prerequisite, not a suggestion.

## 3.3 Approved Trading Sessions

The bot shall only execute trades during the following approved sessions (all times in UTC):

Session

Open (UTC)

Close (UTC)

Instrument Priority

London

07:00

16:00

Forex Majors/Minors, Indices

New York

13:00

21:00

Forex Majors, US Indices

London–NY Overlap

13:00

16:00

Highest priority — all instruments

Asia (Forex only)

00:00

09:00

JPY pairs only; reduced risk

Crypto

24/7

24/7

Restricted hours configurable per exchange

⚠  The bot shall NOT execute entries in the 30 minutes immediately before or after a major session open or close unless configured to allow this. Default: BLOCKED.

⚠  No trades shall be entered within 60 minutes of a Tier-1 economic news event (NFP, CPI, FOMC, central bank rate decisions). The news filter module (M12) is responsible for this check.

# SECTION 4 — INDICATOR ENGINE SPECIFICATIONS (M2)

## 4.1 Exponential Moving Averages

The bot uses three Exponential Moving Averages calculated on closing prices of the primary execution timeframe (H1). The calculations below are definitive.

### 4.1.1 EMA Calculation Formula

EMA(current) = Close(current) × K + EMA(previous) × (1 − K)

Where K = 2 / (Period + 1)

EMA

Period

Smoothing K

Role

EMA21

21

0.0909

Short-term momentum; primary EMA interaction zone

EMA50

50

0.0392

Intermediate control; secondary interaction zone

EMA89

89

0.0222

Macro trend authority; directional bias filter

### 4.1.2 EMA Slope Calculation

Slope is calculated as the directional change between the current EMA value and the EMA value N candles prior, where N = 3 (configurable, default 3).

Slope(EMA) = EMA(current) − EMA(current − N)

Slope Classification:

- POSITIVE: Slope value > +threshold (default: instrument ATR × 0.05)

- NEGATIVE: Slope value < −threshold (default: instrument ATR × 0.05)

- NEUTRAL: Slope value between −threshold and +threshold

⚠  The threshold multiplier (0.05 × ATR) is configurable per instrument. Neutral slopes disqualify trend state and prevent trade entry.

## 4.2 Average True Range (ATR)

### 4.2.1 ATR Calculation

ATR Period: 14 (fixed, not configurable)

True Range(n) = MAX of:

- High(n) − Low(n)

- ABS( High(n) − Close(n−1) )

- ABS( Low(n) − Close(n−1) )

ATR(14) = Wilder's Smoothed Average of TR over 14 periods

### 4.2.2 ATR State Classification

ATR State

Condition

Bot Behavior

COMPRESSED

ATR(current) < ATR(20-period avg) × 0.75

Favorable for setup qualification

NORMAL

ATR within 0.75× to 1.25× of 20-period avg

Standard operation

ELEVATED

ATR(current) > ATR(20-period avg) × 1.25

Reduce risk to 0.25%; tighten filters

EXTREME

ATR(current) > ATR(20-period avg) × 2.0

Trading HALTED; no entries permitted

## 4.3 Candle Classification

Every closed candle shall be classified according to the following rules. These classifications are used by M4, M5, and M7.

Candle Type

Classification Criteria

BULLISH

Close > Open; body size > 0

BEARISH

Close < Open; body size > 0

DOJI

ABS(Close − Open) ≤ ATR × 0.05; nearly equal open and close

REJECTION_BULL

Upper wick ≥ 2× body AND lower wick ≤ 0.3× body AND close bullish

REJECTION_BEAR

Upper wick ≥ 2× body AND lower wick ≤ 0.3× body AND close bearish

ENGULFING_BULL

Current body fully engulfs prior candle body; close > prior open

ENGULFING_BEAR

Current body fully engulfs prior candle body; close < prior open

PIN_BAR

Total wick (upper+lower) ≥ 3× body size in either direction

# SECTION 5 — TREND ANALYSIS ENGINE (M3)

## 5.1 Trend State Definitions

M3 outputs exactly one of four trend states on each candle close. No other states are valid.

Trend State

Required Conditions (ALL must be true)

BULLISH

EMA21 > EMA50 > EMA89 AND Slope(EMA21) = POSITIVE AND Slope(EMA50) = POSITIVE

BEARISH

EMA21 < EMA50 < EMA89 AND Slope(EMA21) = NEGATIVE AND Slope(EMA50) = NEGATIVE

NEUTRAL

EMA hierarchy is not fully bullish or bearish; OR any required slope is NEUTRAL

INVALID

EMAs are crossing (order changed within last 3 candles); or EMAs are compressed (spread < ATR × 0.1)

⚠  The bot shall NOT enter any trade when Trend State is NEUTRAL or INVALID. These states must be treated as hard blockers, not advisory warnings.

## 5.2 EMA Compression Detection

EMA Compression is defined as the condition where the distance between EMA21 and EMA89 is less than a defined threshold. This represents indecision and must block all entries.

EMA Compression = TRUE when: ABS(EMA21 − EMA89) < ATR(14) × 0.10

When EMA Compression = TRUE, Trend State is automatically set to INVALID regardless of EMA order.

## 5.3 Distance from EMA89

Overextension from the macro EMA89 creates reversion risk. The bot shall classify EMA89 distance as follows:

Distance State

Condition

Impact on Risk

CLOSE

Price within 1× ATR of EMA89

Not applicable — trend proximity

MODERATE

Price between 1× and 3× ATR from EMA89

Normal risk allocation

EXTENDED

Price between 3× and 5× ATR from EMA89

Reduce confidence score; moderate risk only

OVEREXTENDED

Price > 5× ATR from EMA89

No new entries until price retraces to EXTENDED or closer

# SECTION 6 — STRUCTURE DETECTION ENGINE (M4)

## 6.1 Triangle Pattern Requirements

The bot recognizes exactly two compression structures. Any other pattern must be rejected. Pattern recognition is performed on the H4 timeframe; the outcome is passed to H1 for entry execution.

### 6.1.1 Ascending Triangle — Bearish Setup

An ascending triangle signals that buyers are pushing higher lows into a fixed resistance ceiling, creating liquidity above the resistance for a potential bearish sweep.

Parameter

Specification

Resistance Level

Minimum 2 swing highs within ±0.15% of each other (configurable); 3+ preferred

Rising Lows

Minimum 2 higher lows, each at least 0.20% above the prior low

Formation Duration

Minimum 8 H4 candles; maximum 60 H4 candles

Compression Ratio

Current candle range ≤ 60% of first candle range within the pattern

Apex Proximity

Price must be within 75% to 95% of the way to the convergence apex

Invalidation

Pattern invalidated if price closes > 0.30% above resistance without returning below

### 6.1.2 Descending Triangle — Bullish Setup

A descending triangle signals that sellers are pushing lower highs into a fixed support floor, creating liquidity below the support for a potential bullish sweep.

Parameter

Specification

Support Level

Minimum 2 swing lows within ±0.15% of each other (configurable); 3+ preferred

Falling Highs

Minimum 2 lower highs, each at least 0.20% below the prior high

Formation Duration

Minimum 8 H4 candles; maximum 60 H4 candles

Compression Ratio

Current candle range ≤ 60% of first candle range within the pattern

Apex Proximity

Price must be within 75% to 95% of the way to the convergence apex

Invalidation

Pattern invalidated if price closes > 0.30% below support without returning above

## 6.2 Structure State Output

M4 outputs exactly one of the following states per evaluation cycle:

- ASCENDING_TRIANGLE: Valid ascending triangle confirmed with all parameters met.

- DESCENDING_TRIANGLE: Valid descending triangle confirmed with all parameters met.

- FORMING: Pattern is developing but apex proximity or candle count not yet met. Monitor only; no entries.

- NONE: No qualifying structure present. No entries permitted.

- INVALIDATED: Previously valid pattern has been broken. Reset state to NONE.

# SECTION 7 — LIQUIDITY ZONE ENGINE (M5)

## 7.1 Liquidity Zone Identification

Liquidity zones represent price levels where orders from losing traders accumulate. The bot targets these zones for entry after a sweep event confirms institutional participation.

### 7.1.1 Resistance Block (Bearish Setup)

Parameter

Specification

Block Definition

Price zone between the lowest swing high close and the highest swing high wick within the triangle's resistance level

Block Width

= Highest swing high wick − Lowest swing high close. Minimum width: 5 pips (forex) or 0.05% (index/crypto)

Block Validation

Minimum 2 touches required to confirm block; each touch = price enters and rejects the zone

Liquidity Density Score

Score = (Number of rejected touches × 10) + (Age of zone in candles × 0.5). Higher = stronger.

Block Age Limit

Blocks older than 80 H4 candles are deprioritized (score penalty: ×0.5)

### 7.1.2 Support Block (Bullish Setup)

Mirror specification of 7.1.1 applied to the descending triangle support level. All parameters are symmetric.

## 7.2 Liquidity Sweep Detection

A liquidity sweep is the core trigger event that initiates entry qualification. The bot does not attempt to predict sweeps — it detects them after they occur.

Sweep Parameter

Specification

Sweep Definition (Bear)

Candle wick extends ABOVE the resistance block high by minimum 2 pips / 0.02%

Sweep Definition (Bull)

Candle wick extends BELOW the support block low by minimum 2 pips / 0.02%

Close Requirement (Bear)

Candle that sweeps must CLOSE below the resistance block high (close inside or below block)

Close Requirement (Bull)

Candle that sweeps must CLOSE above the support block low (close inside or above block)

Sweep Expiry

A detected sweep is valid for the next 3 H1 candles only. If no rejection candle follows, sweep is discarded.

False Sweep Filter

If price subsequently closes beyond the block in the sweep direction, the sweep event is invalidated.

## 7.3 Sweep Probability Scoring

The bot assigns a Sweep Probability Score (0–100) to each detected sweep. This score influences risk tier selection (Section 9).

Factor

Score Weight

Measurement

Liquidity Density Score of Zone

+30 max

Normalized zone density (Section 7.1)

Wick Extension Beyond Block

+20 max

0–5 pts per pip/0.01% extension, capped at 20

Candle Close Quality

+20 max

Close in lower 25% of candle body (bear) = +20; 25–50% = +10

EMA Proximity of Sweep Candle

+15 max

Sweep candle touches EMA21 = +15; EMA50 = +10; neither = +0

ATR State at Sweep

+15 max

COMPRESSED = +15; NORMAL = +8; ELEVATED = +0

Score Interpretation:

- 80–100: HIGH CONFIDENCE — Full risk allocation (1.0%)

- 50–79: MODERATE CONFIDENCE — Reduced risk (0.5%)

- Below 50: LOW CONFIDENCE — Minimum risk (0.25%) or skip

# SECTION 8 — ENTRY QUALIFICATION ENGINE (M7)

## 8.1 Entry Condition Checklist — Bearish (Short) Setup

ALL conditions below must evaluate to TRUE. A single FALSE disqualifies the setup. There are no partial qualifications.

#

Condition Name

Precise Specification

Status

1

Trend State Confirmed

M3 Trend State = BEARISH (EMA21 < EMA50 < EMA89; slopes negative)

REQUIRED

2

Ascending Triangle Confirmed

M4 Structure State = ASCENDING_TRIANGLE on H4; all parameters in Section 6.1.1 met

REQUIRED

3

Liquidity Sweep Detected

M5 Sweep Event active (within last 3 H1 candles); candle wick above resistance block AND close inside/below block

REQUIRED

4

EMA Interaction Confirmed

Sweep candle or confirmation candle HIGH touches or penetrates EMA21 or EMA50 (candle high within 3 pips / 0.03% of EMA value)

REQUIRED

5

Rejection Candle Confirmed

Candle type = REJECTION_BEAR or BEARISH ENGULFING; close is bearish; candle closes below sweep high; upper wick ≥ 2× body

REQUIRED

6

Session Active

M12 Session State = VALID; not within 30 min of session open/close; not within 60 min of Tier-1 news

REQUIRED

7

Risk:Reward Minimum Met

M8 computes R:R ≥ 2.5:1; distance from entry to target ÷ distance from entry to stop ≥ 2.5

REQUIRED

8

Global Risk State Clear

M11 Risk State = TRADING_ALLOWED; daily/weekly drawdown not breached; consecutive loss limit not hit

REQUIRED

⚠  Bullish (long) entry conditions are the exact mirror of the above with all directions reversed. Confirmation candle closes bullish; lower wick ≥ 2× body; sweep is below support block.

# SECTION 9 — RISK COMPUTATION ENGINE (M8)

## 9.1 Stop Loss Calculation

The stop loss is structural, not distance-based. It is placed at the point where the trade thesis is definitively invalidated.

Setup

Stop Loss Placement Rule

Bearish (Short)

SL = High of the rejection candle's wick + 2 pips buffer (forex) / 0.02% buffer (index/crypto)

Bullish (Long)

SL = Low of the rejection candle's wick − 2 pips buffer (forex) / 0.02% buffer (index/crypto)

⚠  The 2-pip buffer is the minimum. If the ATR is ELEVATED, the buffer increases to 4 pips / 0.04% to account for higher volatility.

## 9.2 Position Sizing Formula

Position size is computed from the defined risk percentage of account equity:

Risk Amount = Account Equity × Risk Percentage

Stop Distance = ABS(Entry Price − Stop Loss Price) in pips / points

Pip Value = (contract size × pip size) / current price  [varies by instrument — must be pre-configured]

Position Size (lots) = Risk Amount ÷ (Stop Distance × Pip Value)

⚠  Position size must be rounded DOWN to the nearest valid lot increment (0.01 for forex, 1 for indices, as applicable). Never round up.

## 9.3 Risk Tier Matrix

Condition

Risk %

Position Sizing Rule

Sweep Probability Score 80–100 + ATR NORMAL + no consecutive losses

1.0%

Full risk; standard position size formula

Sweep Probability Score 50–79 OR ATR ELEVATED OR 1–2 consecutive losses

0.5%

Halved position; all other parameters unchanged

Sweep Probability Score <50 OR ATR approaching EXTREME OR 3 consecutive losses

0.25%

Minimum position; highly defensive mode

ATR = EXTREME OR Daily Drawdown Breached OR Weekly Drawdown Breached

0% — NO TRADE

Trading suspended; see Section 11

## 9.4 Profit Target Calculation

Default minimum target: 2.5R from entry.

Target Price (Bear) = Entry Price − (Stop Distance × 2.5)

Target Price (Bull) = Entry Price + (Stop Distance × 2.5)

Adaptive Target Hierarchy (M8 evaluates in order):

- Primary: 2.5R minimum target computed from stop distance.

- Secondary: Next identifiable liquidity pool (equal lows/highs) in the direction of trade.

- Tertiary: ATR-based extension target = Entry ± (ATR × 3.0).

The bot uses whichever target is CLOSEST to entry without being below 2.5R. If all adaptive targets are below 2.5R, the 2.5R target is used.

# SECTION 10 — ORDER EXECUTION HANDLER (M9)

## 10.1 Order Types

Order Type

Used For

Specification

Sell Stop

Bearish entry

Placed at: Low of rejection candle − 1 pip. Triggered when price breaks below entry trigger level.

Buy Stop

Bullish entry

Placed at: High of rejection candle + 1 pip. Triggered when price breaks above entry trigger level.

Stop Loss (attached)

All trades

Placed simultaneously with entry order. Calculated per Section 9.1.

Take Profit (attached)

All trades

Placed simultaneously with entry order. Calculated per Section 9.4.

## 10.2 Pre-Execution Final Validation Checklist

Immediately before order submission, M9 performs the following checks. ANY failure = order cancelled.

Check

Pass Condition

Fail Action

Spread Check

Current spread ≤ configured max spread for instrument

Cancel order; log reason

Slippage Check

Expected slippage ≤ 2 pips / 0.02%

Cancel order; log reason

ATR Safety Check

ATR State ≠ EXTREME

Cancel order; trigger HALT

Session Validity

M12 Session = VALID

Cancel order; do not retry

Consecutive Loss Filter

Consecutive losses < MAX threshold (default: 4)

Cancel; reduce risk tier

Correlation Exposure

No correlated instrument trade already open (threshold: >0.80 correlation)

Cancel; log correlation conflict

Daily Drawdown Gate

Daily drawdown < configured max (default: 3% of equity)

Cancel; trigger daily HALT

Weekly Drawdown Gate

Weekly drawdown < configured max (default: 6% of equity)

Cancel; trigger weekly HALT

R:R Confirmation

Computed R:R ≥ 2.5 at current market price

Cancel if R:R degraded since qualification

## 10.3 Order Expiry

Pending stop orders expire under the following conditions:

- Order has not been triggered within 4 H1 candles of placement.

- The qualifying sweep event has expired (> 3 H1 candles since sweep detection).

- The structure (triangle) has been invalidated after order placement.

- ATR state changes to EXTREME after order placement but before fill.

⚠  Expired orders must be cancelled via broker API and logged with expiry reason code. The system must not leave un-managed pending orders.

# SECTION 11 — TRADE MANAGEMENT ENGINE (M10)

## 11.1 Post-Entry Monitoring Frequency

After a trade is filled, M10 evaluates the open position on every new H1 candle close. Intra-candle monitoring (tick-based) is used only for emergency stop enforcement.

## 11.2 Breakeven Logic (Stage 1)

Parameter

Specification

Breakeven Trigger

Trade reaches +1.0R profit (price has moved 1× the initial stop distance in the trade direction)

Stop Adjustment

Stop loss moved to entry price + 1 pip (long) or entry price − 1 pip (short) to account for spread

Execution

Stop loss modification submitted to broker API immediately upon trigger. Confirmed before next candle.

Irreversibility

Once breakeven is set, stop loss shall NEVER be moved back below entry. This is a one-way operation.

## 11.3 Trailing Stop Logic (Stage 2)

Parameter

Specification

Trailing Trigger

Trade reaches +1.5R profit

Trail Method

Stop trails behind EMA21 on H1. On each candle close, stop = EMA21 value − 5 pips (long) or EMA21 + 5 pips (short)

Trail Frequency

Updated on every H1 candle close while in TRAILING state

Trail Direction

Trail only moves in the direction of the trade (ratchet mechanic). Never moves against the trade.

EMA21 Fallback

If EMA21 is not available (early in instrument history), trail behind most recent swing low/high + 5 pips buffer

## 11.4 Defensive Exit Logic (Stage 3)

The bot may exit a trade before the stop or target is hit under the following conditions. Each condition is evaluated independently on every H1 candle close.

Exit Condition

Trigger

Exit Type

ATR spikes to EXTREME state

ATR > 20-period avg × 2.0

Full immediate market exit

EMA21 reversal against trade

EMA21 slope flips against trade direction for 2 consecutive candles

Partial exit (50%) then trail tighter

Structure invalidation

Triangle pattern invalidated (price closes beyond pattern boundary)

Full immediate market exit

Momentum exhaustion

3 consecutive doji or pin bar candles while in trade > 2.0R profit

Partial exit 50%; hold remainder to target

Opposing sweep detected

New sweep in opposite direction to open trade detected

Full exit at market; log opposing signal

# SECTION 12 — RISK PROTECTION CONTROLLER (M11)

## 12.1 Drawdown Thresholds

All drawdown measurements use the following definitions:

- Daily Drawdown: Calculated from the account equity at 00:00 UTC each day. Resets at 00:00 UTC.

- Weekly Drawdown: Calculated from the account equity at 00:00 UTC Monday. Resets Monday 00:00 UTC.

- Floating drawdown includes open unrealized losses.

Threshold Type

Default Value

Configurable?

Action on Breach

Daily Drawdown Maximum

3.0% of equity

Yes (1% – 5%)

HALT all trading for remainder of day

Weekly Drawdown Maximum

6.0% of equity

Yes (3% – 10%)

HALT all trading for remainder of week

Consecutive Loss Maximum

4 trades

Yes (2 – 6)

Switch to 0.25% risk; alert operator

Maximum Correlated Exposure

2 instruments with >0.80 correlation

Yes

Block new entries on correlated pairs

Maximum Open Trades

3 simultaneous (default)

Yes (1 – 5)

Block new entries when limit reached

## 12.2 Emergency Suspension Triggers

The following conditions trigger an immediate trading suspension. All pending orders are cancelled. Open trades remain managed by M10 but no new entries are permitted.

Trigger

Description & Response

Broker API connectivity failure

Detect via heartbeat check every 60 seconds. If 3 consecutive failures: suspend trading; alert operator; attempt reconnect every 30s.

Abnormal spread expansion

Spread > 3× normal baseline for > 2 consecutive minutes: suspend instrument; log; alert.

ATR EXTREME state

Immediate halt on all instruments. Resume only when ATR returns to NORMAL state for minimum 3 H1 candles.

Execution failure / partial fill

If order partially filled: cancel remaining portion; assess risk of partial position; exit if risk > configured maximum.

Data integrity failure

If OHLCV data contains gaps > 2 candles or anomalous values: suspend instrument; alert; await data recovery.

Account equity drop > 10% intraday

Hard emergency stop: close ALL positions immediately at market; halt all instruments; require manual operator restart.

# SECTION 13 — SESSION & MARKET FILTER (M12)

## 13.1 Economic News Filter

The bot must integrate with a Tier-1 economic calendar data feed. The following event categories are classified as Tier-1 and trigger a trading block:

Event Category

Examples

Central Bank Rate Decisions

Federal Reserve (FOMC), ECB, BOE, BOJ, RBA, SNB announcements

Non-Farm Payroll (NFP)

US monthly employment report — first Friday each month

Consumer Price Index (CPI)

US, EU, UK, AU CPI releases

Gross Domestic Product (GDP)

Major economy quarterly GDP releases

Central Bank Chair Speeches

Fed Chair, ECB President live scheduled speeches

Geopolitical Emergency Events

Detected via volatility spike > 3× ATR baseline; auto-detect only

News Block Window: From 60 minutes before event until 30 minutes after event conclusion.

Implementation: Bot must query news feed API at minimum every 15 minutes during active sessions. Recommended data sources: ForexFactory JSON API, Investing.com economic calendar API, or equivalent.

## 13.2 Low Liquidity Rejection

The bot rejects trade entries during the following low-liquidity conditions:

- Friday after 20:00 UTC (pre-weekend liquidity drain)

- Sunday before 21:00 UTC (pre-market open; incomplete liquidity)

- Public holidays of the instrument's primary exchange (e.g. US markets on US federal holidays)

- Any session where the bid-ask spread exceeds 2.0× the instrument's 20-period rolling average spread

# SECTION 14 — LOGGING & ANALYTICS ENGINE (M13)

## 14.1 Trade Journal Record Schema

Every trade — executed, rejected, or expired — shall generate a complete journal record. The following fields are mandatory:

Field Name

Data Type

Description

trade_id

UUID

Unique identifier for each trade attempt

timestamp_signal

ISO 8601 UTC

Time of initial entry qualification signal

timestamp_entry

ISO 8601 UTC

Time of actual order fill (null if not executed)

instrument

String

e.g. EURUSD, US30

direction

LONG / SHORT

Trade direction

trend_state

Enum

BULLISH / BEARISH at signal time

structure_type

Enum

ASCENDING_TRIANGLE / DESCENDING_TRIANGLE

sweep_probability_score

Integer 0–100

Score from M5 at signal time

entry_price

Decimal

Actual fill price

stop_loss_price

Decimal

Stop loss at entry

take_profit_price

Decimal

Primary take profit at entry

position_size_lots

Decimal

Lot size executed

risk_percentage

Decimal

Risk tier applied (0.25 / 0.5 / 1.0)

risk_amount_usd

Decimal

Dollar amount at risk

rr_ratio_planned

Decimal

Planned R:R at entry

atr_state_at_entry

Enum

ATR state classification at entry

session_at_entry

Enum

London / New York / Asia / Overlap

exit_price

Decimal

Final close price

exit_type

Enum

TAKE_PROFIT / STOP_LOSS / TRAILING / DEFENSIVE / EXPIRED / MANUAL

pnl_pips

Decimal

Profit/loss in pips

pnl_r

Decimal

Profit/loss expressed in R multiples

pnl_currency

Decimal

Profit/loss in account currency

breakeven_triggered

Boolean

Whether breakeven was activated

trail_triggered

Boolean

Whether trailing stop was activated

rejection_reason

String / null

If not executed: reason code from M7/M8/M9

## 14.2 Performance Metrics (Computed Daily/Weekly)

The analytics engine shall compute and store the following metrics on a rolling basis:

- Win Rate: Winning trades ÷ total closed trades (excludes expired orders)

- Average R per trade: Sum of R outcomes ÷ total closed trades

- Expectancy: (Win Rate × Average Win R) − (Loss Rate × Average Loss R)

- Consecutive win/loss streaks: Maximum and current

- Win rate by session (London, NY, Overlap, Asia)

- Win rate by ATR state at entry

- Win rate by Sweep Probability Score tier (<50, 50–79, 80+)

- Average hold time (candles to close)

- Slippage per trade: Actual fill vs. expected entry

# SECTION 15 — CONFIGURATION PARAMETERS REFERENCE

## 15.1 Global Configuration File

The following parameters must be present in a global configuration file (JSON/YAML). The bot shall not start if any required parameter is missing or outside valid range.

Parameter Key

Default Value

Valid Range

Description

ema_short_period

21

10–30

Short EMA period

ema_mid_period

50

40–70

Mid EMA period

ema_long_period

89

80–120

Long EMA period

ema_slope_lookback

3

2–6

Candles back for slope calc

atr_period

14

14 (fixed)

ATR period — do not change

atr_elevated_multiplier

1.25

1.1–1.5

Threshold for ELEVATED ATR

atr_extreme_multiplier

2.0

1.8–3.0

Threshold for EXTREME ATR

triangle_min_candles

8

6–16

Min H4 candles for triangle

triangle_max_candles

60

30–100

Max H4 candles for triangle

sweep_expiry_candles

3

2–5

H1 candles before sweep expires

min_rr_ratio

2.5

2.0–5.0

Minimum required R:R

breakeven_trigger_r

1.0

0.5–1.5

R-level to move stop to breakeven

trail_trigger_r

1.5

1.0–2.5

R-level to activate trailing stop

trail_ema_buffer_pips

5

2–10

Pips behind EMA21 for trail

risk_high_pct

1.0

0.5–2.0

Full confidence risk %

risk_moderate_pct

0.5

0.25–1.0

Moderate confidence risk %

risk_low_pct

0.25

0.1–0.5

Low confidence/defensive risk %

daily_drawdown_max_pct

3.0

1.0–5.0

Daily drawdown halt threshold

weekly_drawdown_max_pct

6.0

3.0–10.0

Weekly drawdown halt threshold

max_consecutive_losses

4

2–6

Consecutive losses before risk reduction

max_open_trades

3

1–5

Maximum simultaneous open positions

news_block_before_mins

60

30–120

Minutes before Tier-1 news to block

news_block_after_mins

30

15–60

Minutes after Tier-1 news to block

order_expiry_candles

4

2–8

H1 candles before pending order expires

# SECTION 16 — SYSTEM STATE MACHINE

## 16.1 Bot Operating States

The LSB operates in exactly one of the following states at any time. All state transitions must be logged with timestamp, reason, and prior state.

State

Description

Transitions To

INITIALIZING

Bot starting; loading config; connecting to broker API and data feed; validating all modules

SCANNING or HALTED

SCANNING

All systems healthy; monitoring market data; evaluating conditions each candle; no open trade

QUALIFYING, HALTED

QUALIFYING

Active setup detected; full qualification sequence running (M3–M8); no order placed yet

ORDER_PENDING, SCANNING

ORDER_PENDING

Stop order placed at broker; awaiting trigger; M9 monitoring for fill or expiry

IN_TRADE, SCANNING (expiry)

IN_TRADE

Position is open; M10 managing stop, target, and defensive exits; M11 monitoring risk

SCANNING (closed), HALTED

DAILY_HALT

Daily drawdown breached; all entries blocked; existing trades managed; resets at 00:00 UTC

SCANNING (on reset)

WEEKLY_HALT

Weekly drawdown breached; all entries blocked; resets Monday 00:00 UTC; operator alert required

SCANNING (on reset)

EMERGENCY_HALT

Critical error, connectivity failure, or extreme market event; all entries blocked; operator must manually restart

INITIALIZING (manual)

OFFLINE

Bot stopped, config invalid, or broker disconnected; no market evaluation occurring

INITIALIZING (manual)

# SECTION 17 — TESTING & VALIDATION REQUIREMENTS

## 17.1 Backtesting Requirements

Before any live deployment, the bot must pass the following backtesting criteria:

Test Requirement

Minimum Standard

Notes

Historical data period

Minimum 3 years H1 OHLCV

Must include bull, bear, and ranging markets

Instruments tested

Minimum 3 instruments

At least 1 forex major, 1 index, 1 other

Positive expectancy

> 0.3R per trade

Measured across full test period

Maximum historical drawdown

< 15% of starting equity

Must hold across all test periods

Win rate

> 40%

At 2.5R target; consistent with positive expectancy

Sharpe Ratio

> 1.0

Risk-adjusted return quality

## 17.2 Unit Test Requirements

Each module must have unit tests covering the following minimum cases:

- M2: EMA calculation accuracy vs. reference values; ATR calculation on known data; candle classification for all 8 types.

- M3: Correct trend state assignment for all 4 states; EMA compression detection; slope threshold at boundary values.

- M4: Triangle detection on synthetic data with valid and invalid patterns; apex proximity calculation; invalidation logic.

- M5: Sweep detection with wick above/below block; close-inside requirement; sweep expiry timing.

- M7: All 8 entry conditions evaluated individually and in combination; correct QUALIFIED/REJECTED output.

- M8: Position sizing accuracy to 0.01 lot precision; stop loss placement; R:R calculation; risk tier assignment.

- M10: Breakeven trigger at exactly 1.0R; trail activation at 1.5R; trail ratchet (cannot move against trade).

- M11: Daily drawdown halt triggers at configured threshold; consecutive loss counter resets on win.

# SECTION 18 — GLOSSARY OF TERMS

Term

Definition

R (Risk Unit)

The monetary value of 1× the initial risk on a trade. E.g. if stop = 20 pips and 1 pip = $10, then 1R = $200.

Liquidity Sweep

A price move that extends beyond a key technical level (triggering stop orders there) and then reverses back inside the level on the same candle close.

EMA Hierarchy

The ordered stacking of EMA21, EMA50, EMA89 in a consistent directional sequence (bull: 21>50>89; bear: 21<50<89).

ATR (Average True Range)

A volatility measure representing the average range of price movement over N periods. Used to classify market conditions and size buffers.

Ascending Triangle

A compression price pattern with relatively equal highs (resistance) and rising lows, signaling buyer accumulation into resistance.

Descending Triangle

A compression price pattern with relatively equal lows (support) and falling highs, signaling seller accumulation into support.

Rejection Candle

A candle with an extended wick showing that price was rejected from a level; classified as REJECTION_BULL or REJECTION_BEAR based on wick direction and close.

Sweep Probability Score

A composite score (0–100) computed by M5 representing the quality of a liquidity sweep event based on 5 weighted factors.

Breakeven

Moving the stop loss to the entry price, eliminating monetary risk on the open trade.

Daily Drawdown

The decline in account equity from the opening balance of the current trading day, including open unrealized losses.

Consecutive Loss State

A bot condition activated when the number of sequential losing trades meets or exceeds the configured threshold.

HALT State

A bot operating state where new trade entries are completely blocked due to a risk protection trigger.

Pip

The fourth decimal place of a forex price (0.0001). For JPY pairs, the second decimal place (0.01). Index/crypto equivalents are instrument-specific.

# SECTION 19 — DOCUMENT REVISION HISTORY

Version

Date

Author

Summary of Changes

1.0

—

LSB Team

Initial white paper — strategic overview and high-level framework

2.0

—

LSB Team

Full system requirements specification — all modules, thresholds, formulas, state machine, test requirements

Document Status: ACTIVE — All developers must use v2.0 as the sole specification reference.

LIQUIDITY STRATEGY BOT — SYSTEM REQUIREMENTS v2.0

This document is the complete and authoritative specification.

No rule herein may be overridden by assumption, convenience, or performance pressure.

"Protect capital first. Profitability is the outcome of controlled risk."
