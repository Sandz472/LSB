-- migrations/001_core.sql
-- LSB Phase-A core schema — 4 tables.
-- Design rationale: docs/decisions/ADR-002-phase-a-schema.md
-- Apply against database lsb_dev (role lsb) per docs/BUILD_PLAYBOOK.md §2.

-- ---------------------------------------------------------------------------
-- config_version
-- One row per (instrument, config_hash). Anchors every downstream row.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS config_version (
    config_hash   TEXT        NOT NULL,
    instrument    TEXT        NOT NULL,
    yaml_snapshot TEXT        NOT NULL,  -- full YAML text at time of hashing
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (config_hash, instrument)
);

-- ---------------------------------------------------------------------------
-- candle
-- Raw OHLCV candles; one row per (config, instrument, timeframe, bar).
-- Timeframe values: 'H1', 'H4', 'D1' (Phase A uses all three).
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS candle (
    id            BIGSERIAL   PRIMARY KEY,
    config_hash   TEXT        NOT NULL,
    instrument    TEXT        NOT NULL,
    timeframe     TEXT        NOT NULL,
    ts            TIMESTAMPTZ NOT NULL,
    open          NUMERIC     NOT NULL,
    high          NUMERIC     NOT NULL,
    low           NUMERIC     NOT NULL,
    close         NUMERIC     NOT NULL,
    volume        NUMERIC,
    FOREIGN KEY (config_hash, instrument)
        REFERENCES config_version (config_hash, instrument),
    UNIQUE (config_hash, instrument, timeframe, ts)
);

-- ---------------------------------------------------------------------------
-- signal
-- One row per H1 bar evaluated by the §8.1 gate conjunction.
-- gate1-8: NULL = not evaluated; FALSE = failed; TRUE = passed.
-- sweep_score: 0-100 risk-tier selector (not a gate; §7.3).
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS signal (
    id            BIGSERIAL   PRIMARY KEY,
    config_hash   TEXT        NOT NULL,
    instrument    TEXT        NOT NULL,
    ts            TIMESTAMPTZ NOT NULL,
    gate1         BOOL,   -- Trend State Confirmed        §8.1#1
    gate2         BOOL,   -- Structure Confirmed          §8.1#2
    gate3         BOOL,   -- Liquidity Sweep Detected     §8.1#3
    gate4         BOOL,   -- EMA Interaction Confirmed    §8.1#4
    gate5         BOOL,   -- Rejection Candle Confirmed   §8.1#5
    gate6         BOOL,   -- Session Active               §8.1#6
    gate7         BOOL,   -- Risk:Reward Minimum          §8.1#7
    gate8         BOOL,   -- Global Risk State Clear      §8.1#8
    all_gates     BOOL,   -- TRUE iff gate1-8 all TRUE
    sweep_score   NUMERIC,
    risk_tier     TEXT,   -- '1.0pct' | '0.5pct' | '0.25pct' | 'skip'
    verdict       TEXT,   -- 'QUALIFIED' | 'REJECTED' | 'INVALIDATED'
    FOREIGN KEY (config_hash, instrument)
        REFERENCES config_version (config_hash, instrument),
    -- Idempotent re-runs (A8 determinism check) must not accumulate duplicates
    UNIQUE (config_hash, instrument, ts)
);

-- ---------------------------------------------------------------------------
-- wf_run
-- One row per walk-forward window (18m train / 6m test, roll 3m; §A9).
-- CHECK enforces no test span overlaps its train span.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS wf_run (
    id            BIGSERIAL   PRIMARY KEY,
    config_hash   TEXT        NOT NULL,
    instrument    TEXT        NOT NULL,
    train_start   DATE        NOT NULL,
    train_end     DATE        NOT NULL,
    test_start    DATE        NOT NULL,
    test_end      DATE        NOT NULL,
    FOREIGN KEY (config_hash, instrument)
        REFERENCES config_version (config_hash, instrument),
    CONSTRAINT no_overlap CHECK (train_end < test_start),
    UNIQUE (config_hash, instrument, train_start, test_start)
);

-- ---------------------------------------------------------------------------
-- sim_trade
-- Simulated fills produced by SimulatedBroker (Blueprint v2.1 Part 7.1).
-- Linked to both the walk-forward window and the qualifying signal.
-- r_multiple: positive = profit, negative = loss (in units of initial risk).
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS sim_trade (
    id            BIGSERIAL   PRIMARY KEY,
    wf_run_id     BIGINT      NOT NULL REFERENCES wf_run (id),
    signal_id     BIGINT      NOT NULL REFERENCES signal (id),
    entry_ts      TIMESTAMPTZ NOT NULL,
    exit_ts       TIMESTAMPTZ,
    entry_price   NUMERIC     NOT NULL,
    exit_price    NUMERIC,
    stop_price    NUMERIC     NOT NULL,
    target_price  NUMERIC     NOT NULL,
    r_multiple    NUMERIC,
    outcome       TEXT        -- 'WIN' | 'LOSS' | 'SCRATCH' | 'OPEN'
);
