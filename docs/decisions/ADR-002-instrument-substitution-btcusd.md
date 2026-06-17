# ADR-002: Instrument Substitution — BTCUSD replaces BOOM500

- **Status:** Accepted
- **Date:** 2026-06-17
- **Approved by:** user (explicit instruction, session A3b)

## Context

The Phase-A instrument list is **Appendix A** of Master Blueprint v2.1, inherited
unchanged by Implementation Plan v3.0. The plan requires ≥3 fully audited instruments
with enough history to complete the 18-month train + 6-month test walk-forward window
(24 months minimum).

BOOM500 was the third instrument. Its only history source is the Deriv
`ticks_history` WebSocket API, which caps at approximately 1 year of candle history
(verified empirically during Session A2/A3: earliest candle returned was 2025-06-12
against a request for 2023-06-12). It cannot satisfy the 24-month depth requirement
and therefore cannot complete an end-to-end walk-forward.

## Options considered

| Option | Depth | New pipeline code? | Asset-class diversity |
|---|---|---|---|
| Another Deriv synthetic (V75, Crash 500, Step) | Same ~1yr API ceiling | No | Yes, but same data-source constraint |
| Second FX major (GBPUSD, USDJPY) | 3y+ (Dukascopy) | No | Low — correlated with EURUSD |
| **BTCUSD** | 3y+ (Binance) | Yes — Binance klines fetcher | High — 24/7, fat-tailed, uncorrelated |
| Equity index (US500, GER40) | 3y+ (Dukascopy) | No | Medium — session gaps differ from FX, not purely 24/7 |

## Decision

Substitute **BTCUSD** as the third instrument.

- Sourced from **Binance public klines API** (BTC/USDT spot, no auth required).
  Dukascopy was initially considered but empirically only returned ~15 months of
  BTCUSD H1 history (earliest candle 2025-03-27), insufficient for the 24-month
  window. Binance covers 3+ years with zero gaps (26,322 H1 candles,
  2023-06-17 to 2026-06-17, zero audit anomalies).
- `asset_class: crypto` — the audit script's three FX-only checks
  (`check_gaps` weekend-closure exemption, `check_weekend_bars`,
  `check_dst_anomalies`) all guard on `asset_class == "fx"` and return early for
  any other value, which is correct behaviour for a 24/7 instrument.
- Walk-forward window (18 train + 6 test) is unchanged — Binance depth covers it.

## BOOM500 disposition

BOOM500 is **retired** from the active instrument set. `config/BOOM500.yaml` is
deleted; the previously loaded `candle` rows are deleted from the dev database.
BOOM500 does not appear in the `"all"` default of either pipeline script.

The Deriv data-source constraint is not a bug in the pipeline — the Deriv API simply
does not expose more than ~1 year of history. No Phase-A work is lost.

## Consequences

- The active Phase-A walk-forward instrument set is: **EURUSD, XAUUSD, BTCUSD**.
- `broker_costs` for BTCUSD in `config/BTCUSD.yaml` are first-pass estimates
  (spread 30 points, 0 commission). These are inputs to the Session A7 pessimistic
  fill model and will be verified against the broker's published cost schedule at
  that session before any backtest result is considered meaningful.
- The v2.1 spec is otherwise unchanged. This ADR constitutes the written record
  required by the Phase-A working agreement for any Appendix-A change.
