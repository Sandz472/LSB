-- Phase A schema (Session A1)
-- Four tables per LSB_Implementation_Plan_v3.0.md "Phase A schema":
--   config_version, candle, signal, wf_run (+ child sim_trade)
-- The seven-table v2.1 schema is restored verbatim in Phase B (migrations/002_live.sql).

CREATE TABLE IF NOT EXISTS schema_migrations (
    filename   TEXT PRIMARY KEY,
    applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Every result row downstream references config_hash. Identical canonical
-- configs always hash identically (src/lsb/data/config.py); insert-or-get
-- here is the only writer.
CREATE TABLE config_version (
    config_hash    CHAR(64) PRIMARY KEY,
    instrument     TEXT NOT NULL,
    canonical_yaml TEXT NOT NULL,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE candle (
    id         BIGSERIAL PRIMARY KEY,
    instrument TEXT NOT NULL,
    timeframe  TEXT NOT NULL,
    ts         TIMESTAMPTZ NOT NULL,
    open       DOUBLE PRECISION NOT NULL,
    high       DOUBLE PRECISION NOT NULL,
    low        DOUBLE PRECISION NOT NULL,
    close      DOUBLE PRECISION NOT NULL,
    volume     DOUBLE PRECISION NOT NULL,
    spread     DOUBLE PRECISION,
    UNIQUE (instrument, timeframe, ts)
);

CREATE INDEX idx_candle_instrument_timeframe_ts ON candle (instrument, timeframe, ts);

-- gate_results holds the per-gate pass/fail + reason payload. The shape is
-- defined by the signal engine (Sessions A4-A5), not fixed here, since the
-- v2.1 gate definitions are not yet re-specified in this repo.
CREATE TABLE signal (
    id           BIGSERIAL PRIMARY KEY,
    config_hash  CHAR(64) NOT NULL REFERENCES config_version(config_hash),
    instrument   TEXT NOT NULL,
    timeframe    TEXT NOT NULL,
    ts           TIMESTAMPTZ NOT NULL,
    gate_results JSONB NOT NULL,
    qualified    BOOLEAN NOT NULL,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (config_hash, instrument, timeframe, ts)
);

CREATE INDEX idx_signal_config_hash ON signal (config_hash);

CREATE TABLE wf_run (
    id          BIGSERIAL PRIMARY KEY,
    config_hash CHAR(64) NOT NULL REFERENCES config_version(config_hash),
    instrument  TEXT NOT NULL,
    train_start TIMESTAMPTZ NOT NULL,
    train_end   TIMESTAMPTZ NOT NULL,
    test_start  TIMESTAMPTZ NOT NULL,
    test_end    TIMESTAMPTZ NOT NULL,
    metrics     JSONB NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_wf_run_config_hash_instrument ON wf_run (config_hash, instrument);

CREATE TABLE sim_trade (
    id               BIGSERIAL PRIMARY KEY,
    wf_run_id        BIGINT NOT NULL REFERENCES wf_run(id) ON DELETE CASCADE,
    direction        TEXT NOT NULL CHECK (direction IN ('long', 'short')),
    entry_ts         TIMESTAMPTZ NOT NULL,
    entry_price      DOUBLE PRECISION NOT NULL,
    exit_ts          TIMESTAMPTZ,
    exit_price       DOUBLE PRECISION,
    slippage_applied DOUBLE PRECISION NOT NULL DEFAULT 0,
    r_multiple       DOUBLE PRECISION,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_sim_trade_wf_run_id ON sim_trade (wf_run_id);
