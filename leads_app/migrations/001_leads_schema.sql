PRAGMA journal_mode=WAL;
PRAGMA busy_timeout=5000;

-- Users (managed via AppWrite Auth, but we track access + approval locally)
CREATE TABLE IF NOT EXISTS leads_users (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    appwrite_uid    TEXT    UNIQUE,          -- AppWrite user UID
    username        TEXT    UNIQUE NOT NULL,
    email           TEXT    UNIQUE NOT NULL,
    role            TEXT    NOT NULL DEFAULT 'member',  -- 'member' or 'admin'
    approved        INTEGER NOT NULL DEFAULT 0,
    approved_by     TEXT,
    approved_at     TEXT,
    created_at      TEXT    NOT NULL DEFAULT (datetime('now')),
    last_login      TEXT
);

-- Monitors: each PM→Equity pair
CREATE TABLE IF NOT EXISTS leads_monitors (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    slug            TEXT    NOT NULL,    -- Polymarket slug
    pm_question     TEXT,
    ticker          TEXT    NOT NULL,           -- equity ticker (e.g. FXI)
    description     TEXT,
    signal_thresh_pp    REAL    NOT NULL DEFAULT 2.0,
    cooldown_hrs    REAL    NOT NULL DEFAULT 6.0,
    active          INTEGER NOT NULL DEFAULT 1,
    created_at      TEXT    NOT NULL DEFAULT (datetime('now')),
    UNIQUE(slug, ticker)
);

-- Equity bar cache
CREATE TABLE IF NOT EXISTS leads_equity_bars (
    ticker  TEXT,
    ts      TEXT,       -- UTC 15-min floor
    open_price  REAL,
    high_price  REAL,
    low_price   REAL,
    close_price REAL,
    volume      INTEGER,
    fetched_at  TEXT    NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (ticker, ts)
);

-- Lead/lag history
CREATE TABLE IF NOT EXISTS leads_lead_lag_history (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    monitor_id      INTEGER NOT NULL REFERENCES leads_monitors(id),
    computed_at     TEXT    NOT NULL DEFAULT (datetime('now')),
    lookback_days   INTEGER NOT NULL DEFAULT 20,
    best_lag        INTEGER NOT NULL,
    best_r          REAL    NOT NULL,
    best_p          REAL    NOT NULL,
    n_obs           INTEGER NOT NULL,
    lag_r_neg3 REAL, lag_p_neg3 REAL,
    lag_r_neg2 REAL, lag_p_neg2 REAL,
    lag_r_neg1 REAL, lag_p_neg1 REAL,
    lag_r_zero  REAL, lag_p_zero  REAL,
    lag_r_pos1  REAL, lag_p_pos1  REAL,
    lag_r_pos2  REAL, lag_p_pos2  REAL,
    lag_r_pos3  REAL, lag_p_pos3  REAL
);

-- Signals
CREATE TABLE IF NOT EXISTS leads_signals (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    monitor_id      INTEGER NOT NULL REFERENCES leads_monitors(id),
    signal_ts       TEXT    NOT NULL,
    pm_ts           TEXT    NOT NULL,
    pm_prob_before  REAL    NOT NULL,
    pm_prob_after   REAL    NOT NULL,
    pm_move_pp      REAL    NOT NULL,
    direction       TEXT    NOT NULL,
    predicted_eq_return_bps REAL NOT NULL,
    confidence      TEXT    NOT NULL DEFAULT 'MEDIUM',
    status          TEXT    NOT NULL DEFAULT 'active',
    outcome_at_15m  REAL,
    outcome_at_30m  REAL,
    outcome_at_1h   REAL,
    outcome_at_2h   REAL,
    outcome_at_4h   REAL,
    outcome_at_8h   REAL,
    outcome_at_24h  REAL,
    settled_at      TEXT,
    created_at      TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_leads_signals_monitor ON leads_signals(monitor_id);
CREATE INDEX IF NOT EXISTS idx_leads_signals_status  ON leads_signals(status);
CREATE INDEX IF NOT EXISTS idx_leads_signals_ts       ON leads_signals(signal_ts);
CREATE INDEX IF NOT EXISTS idx_leads_leadlag_monitor ON leads_lead_lag_history(monitor_id);
CREATE INDEX IF NOT EXISTS idx_leads_leadlag_computed ON leads_lead_lag_history(computed_at);
CREATE INDEX IF NOT EXISTS idx_leads_equity_ticker_ts ON leads_equity_bars(ticker, ts);
