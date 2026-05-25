# PM Market Monitor — Implementation Plan
# chinavol.com/predictive-leads
# Generated: 2026-05-25

---

## 1. Tech Stack Decisions

| Decision | Choice | Rationale |
|---|---|---|
| **Backend framework** | Flask 3.x | Lightweight, path-prefix friendly (`APPLICATION_ROOT`), works with Gunicorn behind Traefik |
| **Database** | SQLite via existing `trading_journal.db` | WAL mode, extends existing schema; no Postgres needed at v1 scale |
| **ORM** | Raw sqlite3 with dict rows | No ORM overhead; existing code uses raw SQL |
| **Auth** | Flask-Login + Werkzeug password hashing | Simple session cookies, `approved` flag gates access |
| **Equity data** | yfinance (0.2.x) | Free, 15-min bars, no API key; acceptable for v1 |
| **Charts** | Chart.js (CDN) | No build step, good 15-min timeline support |
| **Job scheduler** | Host cron calling Docker exec scripts | Simpler than APScheduler inside the container |
| **Container** | Python 3.12-slim + Gunicorn (2 workers) | Minimal image; WAL SQLite safe with 2 workers |
| **Proxy** | Traefik via `docker network=gateway` + constraint labels | Existing setup; need `traefik.constraint-label-stack=appwrite` |

### Alternative considered and rejected:
- **FastAPI**: Overkill for read-heavy authenticated pages; Flask templates are simpler for v1
- **PostgreSQL**: Operational overhead; SQLite with WAL handles v1 concurrency fine
- **APScheduler in container**: Cron outside is more reliable for VPS environment

---

## 2. Data Model

### New tables in `trading_journal.db` (with WAL mode):

```sql
-- Enable WAL immediately when this migration runs
PRAGMA journal_mode=WAL;
PRAGMA busy_timeout=5000;

-- ── Users ────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS leads_users (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    username        TEXT    UNIQUE NOT NULL,
    email           TEXT    UNIQUE NOT NULL,
    pw_hash         TEXT    NOT NULL,
    role            TEXT    NOT NULL DEFAULT 'member',  -- 'member' or 'admin'
    approved        INTEGER NOT NULL DEFAULT 0,
    approved_by     TEXT,
    approved_at     TEXT,
    created_at      TEXT    NOT NULL DEFAULT (datetime('now')),
    last_login      TEXT
);

-- ── Monitors ────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS leads_monitors (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    slug            TEXT    UNIQUE NOT NULL,    -- Polymarket slug
    pm_question     TEXT,
    ticker          TEXT    NOT NULL,           -- equity ticker (e.g. FXI)
    description     TEXT,
    signal_thresh_pp    REAL    NOT NULL DEFAULT 2.0,   -- PM move ≥N pp triggers signal
    cooldown_hrs    REAL    NOT NULL DEFAULT 6.0,     -- minimum hours between signals
    active          INTEGER NOT NULL DEFAULT 1,
    created_at      TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- ── Equity bar cache ─────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS leads_equity_bars (
    ticker          TEXT,
    ts              TEXT,      -- UTC, 15-min floor
    open_price      REAL,
    high_price     REAL,
    low_price      REAL,
    close_price    REAL,
    volume          INTEGER,
    fetched_at      TEXT    NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (ticker, ts)
);

-- ── Lead/lag history ──────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS leads_lead_lag_history (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    monitor_id      INTEGER NOT NULL REFERENCES leads_monitors(id),
    computed_at     TEXT    NOT NULL DEFAULT (datetime('now')),
    lookback_days   INTEGER NOT NULL DEFAULT 20,
    -- best lag statistics
    best_lag        INTEGER NOT NULL,     -- -3,-2,-1,0,+1,+2,+3 (bars)
    best_r          REAL    NOT NULL,
    best_p          REAL    NOT NULL,
    n_obs           INTEGER NOT NULL,
    -- full lag table (all 7 lags stored)
    lag_r_neg3      REAL,
    lag_p_neg3      REAL,
    lag_r_neg2      REAL,
    lag_p_neg2      REAL,
    lag_r_neg1      REAL,
    lag_p_neg1      REAL,
    lag_r_zero      REAL,
    lag_p_zero      REAL,
    lag_r_pos1      REAL,
    lag_p_pos1      REAL,
    lag_r_pos2      REAL,
    lag_p_pos2      REAL,
    lag_r_pos3      REAL,
    lag_p_pos3      REAL
);

-- ── Signals ──────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS leads_signals (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    monitor_id      INTEGER NOT NULL REFERENCES leads_monitors(id),
    signal_ts       TEXT    NOT NULL,           -- when PM move triggered
    pm_ts           TEXT    NOT NULL,           -- snapshot timestamp that triggered
    pm_prob_before  REAL    NOT NULL,           -- probability just before
    pm_prob_after   REAL    NOT NULL,           -- probability just after (or at trigger)
    pm_move_pp      REAL    NOT NULL,           -- abs(pm_prob_after - pm_prob_before)*100
    direction       TEXT    NOT NULL,            -- 'UP' or 'DOWN'
    predicted_eq_return_bps REAL NOT NULL,       -- expected equity move sign (not magnitude)
    confidence      TEXT    NOT NULL DEFAULT 'MEDIUM', -- 'HIGH','MEDIUM','LOW'
    status          TEXT    NOT NULL DEFAULT 'active', -- 'active','settling','resolved'
    outcome_at_15m  REAL,   -- equity return bps at 15min
    outcome_at_30m  REAL,
    outcome_at_1h   REAL,
    outcome_at_2h   REAL,
    outcome_at_4h   REAL,
    outcome_at_8h   REAL,
    outcome_at_24h  REAL,
    settled_at      TEXT,
    created_at      TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- ── Indexes ─────────────────────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_leads_signals_monitor ON leads_signals(monitor_id);
CREATE INDEX IF NOT EXISTS idx_leads_signals_status  ON leads_signals(status);
CREATE INDEX IF NOT EXISTS idx_leads_signals_ts       ON leads_signals(signal_ts);
CREATE INDEX IF NOT EXISTS idx_leads_leadlag_monitor ON leads_lead_lag_history(monitor_id);
CREATE INDEX IF NOT EXISTS idx_leads_leadlag_computed ON leads_lead_lag_history(computed_at);
CREATE INDEX IF NOT EXISTS idx_leads_equity_ticker_ts ON leads_equity_bars(ticker, ts);
```

### Seed monitors (Phase 2):

```sql
INSERT OR IGNORE INTO leads_monitors (slug, pm_question, ticker, description, signal_thresh_pp, cooldown_hrs)
VALUES
  ('will-china-invade-taiwan-before-2027',
   'Will China invade Taiwan by end of 2026?',
   'FXI',
   'China large-cap ETF (FXI). Taiwan tension is primary China risk-off driver. Known lead-lag: PM→FXI at 45min, r=−0.151, p=0.0003.',
   1.5, 4.0),

  ('will-china-invade-taiwan-before-2027',
   'Will China invade Taiwan by end of 2026?',
   'KWEB',
   'KraneShares CSI China Internet ETF. Tech-heavy China exposure. Known lead-lag: PM→KWEB at 45min, r=−0.160, p=0.0001.',
   1.5, 4.0),

  ('us-x-iran-permanent-peace-deal-by-may-31-2026-333-871-241-192-799-449-125',
   'US x Iran permanent peace deal by May 31, 2026?',
   'OIH',
   'VanEck Oil Service ETF (OIH). Iran peace → supply chain risk-off for energy. Known lead-lag: PM→OIH at 45min, r=−0.247, p=0.029.',
   2.0, 6.0);
```

---

## 3. API Design

### Authentication
| Method | Path | Description |
|---|---|---|
| POST | `/leads/auth/login` | `{"username": "", "password": ""}` → session cookie |
| POST | `/leads/auth/register` | `{"username": "", "email": "", "password": ""}` → pending approval |
| POST | `/leads/auth/logout` | clears session |

### Monitor data
| Method | Path | Description |
|---|---|---|
| GET | `/leads/api/monitors` | All monitors with latest status + lead/lag |
| GET | `/leads/api/monitor/<id>` | Single monitor detail |
| GET | `/leads/api/monitor/<id>/pm-history` | Last 100 PM snapshots as JSON |
| GET | `/leads/api/monitor/<id>/eq-history` | Last 100 equity bars as JSON |
| GET | `/leads/api/monitor/<id>/lead-lag-history` | Last 30 lead/lag history entries |

### Signals
| Method | Path | Description |
|---|---|---|
| GET | `/leads/api/signals` | All signals, filterable by `?monitor_id=X&status=active` |
| GET | `/leads/api/signals/performance` | Aggregated win rate + PnL by monitor and horizon |

### Response shapes:

```json
// GET /leads/api/monitors
{
  "monitors": [
    {
      "id": 1,
      "slug": "will-china-invade-taiwan-before-2027",
      "ticker": "FXI",
      "pm_current_prob": 0.0675,
      "pm_volume": 23400000,
      "latest_lead_lag": {
        "best_lag": -3,
        "best_r": -0.151,
        "best_p": 0.0003,
        "n_obs": 564,
        "computed_at": "2026-05-25T11:00:00"
      },
      "active_signals": 0,
      "signal_thresh_pp": 1.5,
      "cooldown_hrs": 4.0
    }
  ]
}

// GET /leads/api/signals/performance
{
  "by_monitor": [
    {
      "monitor_id": 1,
      "ticker": "FXI",
      "horizon": "1h",
      "n_signals": 12,
      "win_rate": 0.58,
      "avg_return_bps": 8.3,
      "gross_pnl_bps": 99.6,
      "net_pnl_bps": 83.2
    }
  ],
  "by_horizon": {
    "15m":  { "n": 12, "win_rate": 0.67, "net_pnl_bps": 41.2 },
    "30m":  { "n": 12, "win_rate": 0.62, "net_pnl_bps": 58.7 },
    "1h":   { "n": 12, "win_rate": 0.58, "net_pnl_bps": 83.2 },
    "2h":   { "n": 11, "win_rate": 0.55, "net_pnl_bps": 61.9 },
    "4h":   { "n": 10, "win_rate": 0.50, "net_pnl_bps": 22.1 },
    "8h":   { "n": 8,  "win_rate": 0.50, "net_pnl_bps": 15.0 },
    "24h":  { "n": 5,  "win_rate": 0.40, "net_pnl_bps": -31.0 }
  }
}
```

---

## 4. Frontend Design

### `/leads/` — Monitor Dashboard
- **Grid of monitor cards** (3 across desktop, 1 on mobile)
- Each card shows:
  - PM market name + Polymarket link
  - Current probability (large, color-coded)
  - 24h probability sparkline (Chart.js line)
  - Lead/lag gauge: arrow + lag value + r + p + sample size
  - Active signal count / last signal time
  - Signal stats: win rate @ 1h, net PnL @ 1h
- Header: "ChinaVol Pro | PM Market Monitor" + user badge + logout
- Footer: methodology link

### `/leads/monitor/<id>/` — Per-Monitor Detail
- **Two-panel layout**:
  - Left: PM probability timeline (Chart.js line, 15-min candles)
  - Right: Equity price timeline (same x-axis, synced)
- **Lead/lag section**:
  - Heatmap showing correlation at all 7 lags (−3 to +3)
  - Highlighted cell for best_lag
- **Signal table**: last 20 signals for this monitor
  - Columns: timestamp, direction, PM move (pp), predicted return, actual returns at each horizon, win/loss
  - Color-coded: green = win, red = loss
- **Outcome heatmap**: grid of win rates by horizon × direction

### `/leads/signals/` — Signal History & Performance
- **Summary cards** at top: total signals, overall win rate, avg PnL by horizon
- **Filter bar**: monitor dropdown, direction dropdown, date range
- **Table**: all signals paginated
  - Columns: monitor, timestamp, PM move, direction, confidence, outcomes at each horizon, settled?
- **Performance panel**:
  - Bar chart: win rate by monitor
  - Line chart: cumulative PnL (bps) over time, by monitor

### `/leads/auth/login/` and `/leads/register/`
- Minimal forms matching ChinaVol dark theme
- "Pending approval" page after registration with explanation

### Chart types:
| Chart | Type | Use case |
|---|---|---|
| Probability sparkline | Line (15-min) | Card header, monitor detail |
| Equity price timeline | Line (15-min) | Monitor detail, synced x-axis |
| Lead/lag heatmap | Color-coded table | Monitor detail lag display |
| Outcome heatmap | Color-coded table | Signal history |
| Win rate bar chart | Vertical bars | Performance page |
| Cumulative PnL line | Line | Performance page |

---

## 5. Signal Generation Logic

### Trigger conditions (ALL must be true):
1. `|pm_diff| ≥ monitor.signal_thresh_pp` (default 2.0pp for Iran, 1.5pp for Taiwan)
2. Monitor is `active = 1`
3. No unresolved signal for this monitor with `status = 'active'` or `'settling'`
4. Last resolved signal for this monitor was ≥ `monitor.cooldown_hrs` ago
5. Both PM and equity data available at signal time

### Direction determination:
- `direction = 'UP'` if `pm_diff > 0` (Polymarket probability rose → equity should sell off because risk-on)
- `predicted_eq_return_bps = sign(pm_diff) × |r| × 100` (scaled, not magnitude)
- Sign convention: **negative correlation** (r < 0) means PM up → equity down

### Signal confidence:
| Confidence | Criteria |
|---|---|
| **HIGH** | `p < 0.01` AND `|r| > 0.15` AND `n_obs > 200` |
| **MEDIUM** | `p < 0.05` AND `|r| > 0.08` AND `n_obs > 100` |
| **LOW** | all other triggered signals |

### Noise filtering (what we DON'T signal on):
- PM move below threshold (even if statistically notable)
- PM move during equity market closed hours (no equity confirmation possible)
- Market with insufficient correlation history (< 50 aligned obs)
- Equity data gap > 2 bars at trigger time (data quality)

### Dedup:
- Composite key: `(monitor_id, signal_ts_bucket)` where bucket = 15-min floor of signal_ts
- Only one signal per monitor per 15-min bucket, even if multiple threshold crossings occur

---

## 6. Tracking and PnL Estimation

### Outcome fill rules:
- Outcome targets: `[15m, 30m, 1h, 2h, 4h, 8h, 24h]` measured from `signal_ts`
- Equity return computed as: `(close_at_target - close_at_signal) / close_at_signal × 10000` (bps)
- If target timestamp falls outside US equity market hours → roll forward to next available bar
- If equity data is missing at target → leave that outcome field `NULL`
- Status transitions: `active → settling → resolved`

### Settling:
- A signal reaches `status = 'settling'` when ALL outcomes at or before 4h are either filled or market-closed
- A signal reaches `status = 'resolved'` when all 7 horizons are filled or market has been closed for 24h

### PnL calculation:
- **Direction correctness**: `correct = (predicted_direction == 'UP' and actual_return > 0) or (predicted_direction == 'DOWN' and actual_return < 0)`
- **Gross PnL (bps)**: `actual_return_bps × sign(predicted_direction)` → positive = winner, negative = loser
- **Net PnL (bps)**: Gross minus 5bps spread estimate (realistic execution friction)
- **Win rate**: % of signals where `correct = True`
- **Cumulative PnL**: sum of net_pnl_bps over time window

### What "profitable" means:
- Monitor is **signal-profitable** if cumulative net_pnl_bps > 0 over the tracked period
- Monitor is **signal-accurate** if win rate > 50% at the 1h horizon
- Both metrics must hold for the monitor to be considered actionable

---

## 7. Auth Design

### User model:
- `username` + `email` + `pw_hash` (bcrypt via Werkzeug)
- `approved = 0/1` — all new registrations start unapproved
- `role = 'member'` or `'admin'` — admin bypasses approval check
- `last_login` updated on each login

### Access control:
- `/leads/` and all sub-routes: requires `approved = 1` AND `role = 'admin' OR 'member'`
- `/leads/auth/login` + `/leads/auth/register`: public
- Admin endpoints (future): require `role = 'admin'`

### Manual approval flow:
```sql
UPDATE leads_users SET approved = 1, approved_by = 'mike', approved_at = datetime('now')
WHERE username = 'reader';
```

### Future Stripe integration:
- Add `stripe_customer_id`, `subscription_status`, `subscription_current_period_end` to `leads_users`
- Change access check from `approved` only to `approved AND active_subscription`

---

## 8. Deployment Plan

### Folder structure:
```
/opt/chinavol/leads_app/
├── app/
│   ├── __init__.py          # Flask app factory
│   ├── config.py
│   ├── db.py                # SQLite helpers
│   ├── auth.py              # Flask-Login user loader
│   ├── models.py            # Row dict helpers
│   ├── market_data.py       # yfinance fetch + cache
│   ├── correlations.py      # Lead/lag math
│   ├── signals.py           # Signal logic
│   ├── outcomes.py          # Outcome tracking
│   ├── pnl.py              # Performance calculations
│   ├── routes/
│   │   ├── pages.py
│   │   ├── api.py
│   │   └── auth.py
│   └── templates/leads/
├── scripts/
│   ├── init_db.py
│   ├── create_user.py
│   ├── approve_user.py
│   ├── seed_monitors.py
│   ├── refresh_equity_bars.py
│   ├── compute_lead_lag.py
│   ├── generate_signals.py
│   └── track_outcomes.py
├── migrations/
│   ├── 001_leads_schema.sql
│   └── 002_seed_monitors.sql
├── static/leads.css
├── static/leads.js
├── static/charts.js
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
└── README.md
```

### Docker + Traefik labels:
```yaml
services:
  chinavol-leads:
    build: ./leads_app
    restart: unless-stopped
    env_file:
      - ./leads_app/.env
    volumes:
      - /mnt/c/OneDrive/Hermes/trading_journal.db:/data/trading_journal.db
    labels:
      - traefik.enable=true
      - traefik.constraint-label-stack=appwrite
      - traefik.docker.network=gateway
      - traefik.http.routers.chinavol-leads.rule=Host(`chinavol.com`) && PathPrefix(`/leads`)
      - traefik.http.routers.chinavol-leads.entrypoints=appwrite_websecure
      - traefik.http.routers.chinavol-leads.tls=true
      - traefik.http.services.chinavol-leads.loadbalancer.server.port=8000
    networks:
      - gateway

networks:
  gateway:
    external: true
```

### Environment variables:
```text
FLASK_ENV=production
SECRET_KEY=<long-random-secret>
DATABASE_PATH=/data/trading_journal.db
APPLICATION_ROOT=/leads
SESSION_COOKIE_SECURE=true
YFINANCE_CACHE_TTL_SECONDS=600
```

### Cron jobs (host cron):
```cron
*/15 * * * * cd /opt/chinavol/leads_app && docker compose exec -T chinavol-leads python scripts/refresh_equity_bars.py
*/15 * * * * cd /opt/chinavol/leads_app && docker compose exec -T chinavol-leads python scripts/compute_lead_lag.py
*/15 * * * * cd /opt/chinavol/leads_app && docker compose exec -T chinavol-leads python scripts/generate_signals.py
*/15 * * * * cd /opt/chinavol/leads_app && docker compose exec -T chinavol-leads python scripts/track_outcomes.py
```

---

## 9. Implementation Phases

### Phase 1: Schema + Seed
- `001_leads_schema.sql` + `002_seed_monitors.sql`
- Run against copy of `trading_journal.db`
- Validate: existing `polymarket_snapshots_v2` data untouched

### Phase 2: Flask Skeleton + Auth
- Flask app factory + auth routes + templates
- User creation/approval scripts
- Validate: pending user cannot access dashboard; approved user can

### Phase 3: Equity Bar Cache
- yfinance fetcher + `leads_equity_bars` upsert
- Validate: FXI/KWEB/OIH bars populated for last 30 days; no duplicate bars

### Phase 4: Lead/Lag Computation
- PM snapshot loader + equity return alignment + lag correlation
- `leads_lead_lag_history` writer
- Validate: Taiwan/FXI result consistent with known r=−0.151

### Phase 5: Signal Generation
- Threshold-based detector + dedupe + confidence scoring
- Validate: no duplicate signals on re-run; small moves don't trigger

### Phase 6: Outcome Tracking + PnL
- Outcome fill script + horizon returns + performance aggregates
- Validate: outcomes fill only when data exists; net PnL sign correct for DOWN signals

### Phase 7: Dashboard UI
- All pages + Chart.js + polling
- Validate: charts render with real data; empty/stale states readable

### Phase 8: Deployment
- Dockerfile + compose + Traefik labels + cron + health check
- Validate: `/leads/health` returns OK through Traefik; login works; jobs read/write DB

---

## 10. Code Files

### Core app
- `app/__init__.py` — Flask app factory
- `app/config.py` — env-driven config
- `app/db.py` — SQLite helpers + WAL
- `app/auth.py` — Flask-Login + decorators
- `app/models.py` — typed row helpers
- `app/market_data.py` — yfinance fetch/cache
- `app/correlations.py` — lead/lag math
- `app/signals.py` — signal logic
- `app/outcomes.py` — outcome tracking
- `app/pnl.py` — performance calc

### Routes
- `app/routes/pages.py` — dashboard + detail + signals
- `app/routes/api.py` — JSON REST API
- `app/routes/auth.py` — login/register/logout

### Templates (Flask Jinja2)
- `app/templates/leads/base.html` — shared shell
- `app/templates/leads/dashboard.html`
- `app/templates/leads/monitor.html`
- `app/templates/leads/signals.html`
- `app/templates/leads/login.html`
- `app/templates/leads/register.html`
- `app/templates/leads/pending.html`

### Scripts
- `scripts/init_db.py` — run migrations
- `scripts/create_user.py` — create admin/member
- `scripts/approve_user.py` — approve pending user
- `scripts/seed_monitors.py` — idempotent monitor seed
- `scripts/refresh_equity_bars.py` — yfinance fetch
- `scripts/compute_lead_lag.py` — correlation history
- `scripts/generate_signals.py` — signal detector
- `scripts/track_outcomes.py` — outcome fill

### Deployment
- `Dockerfile`, `docker-compose.yml`, `requirements.txt`, `.env.example`, `README.md`

---

## 11. Key Risks

| Risk | Impact | Mitigation |
|---|---|---|
| **yfinance intraday limits** | Bars may be unavailable for long backfill | Cache locally every 15 min; don't rely on yfinance for history beyond 30 days |
| **SQLite concurrent writes** | Cron + requests simultaneously writing | WAL mode + `busy_timeout=5000` + 2 gunicorn workers + short writes only |
| **Slug ambiguity** | Iran monitor slug may differ from task description | Keep seed SQL editable; store `pm_question` for verification |
| **Statistical overfitting** | Dashboard implies more predictive power than exists | Show p-value + sample size + n_obs alongside every gauge; distinguish "research correlation" from "live signal performance" |
| **Path-prefix bugs** | Flask under `/leads` misconfigures asset URLs | Blueprint prefix + `url_for()` everywhere; test through Traefik, not local |
| **Auth security** | Simple auth handling real payments later | bcrypt hashing from start; rate limit login; keep manual approval gate |

---

## 12. V1 Acceptance Criteria

- [ ] Approved user can log into `/leads/`
- [ ] Dashboard shows Taiwan/FXI, Taiwan/KWEB, Iran/OIH monitor cards
- [ ] Each monitor shows latest PM probability + volume from `polymarket_snapshots_v2`
- [ ] FXI, KWEB, OIH 15-min bars cached locally in `leads_equity_bars`
- [ ] Lead/lag history computed and visible (including −3 lag)
- [ ] Signal generation respects thresholds + cooldown + dedup
- [ ] Outcomes fill for all 7 horizons as data becomes available
- [ ] Signals page reports win rate + net PnL by monitor and horizon
- [ ] Pending users cannot access paid pages
- [ ] Deployment works behind Traefik at `https://chinavol.com/leads/`