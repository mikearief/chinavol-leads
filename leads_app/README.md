# PM Market Monitor (leads_app)

Phase 1 of the ChinaVol Pro PM Market Monitor.

## Stack
- Flask 3.x + Gunicorn
- SQLite (WAL) via existing `trading_journal.db`
- AppWrite Auth (REST API) for users
- Flask-Login for sessions

## Folder layout
```
leads_app/
├── migrations/          # SQL schema + seed
├── scripts/             # CLI helpers
├── app/                 # Flask app
│   ├── routes/          # pages, api, auth
│   └── templates/leads/ # Jinja2 templates
├── static/              # CSS + JS
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

## Setup
```bash
cd /mnt/c/OneDrive/Hermes/Projects/chinavol/leads_app
python3 scripts/init_db.py --check
python3 scripts/seed_monitors.py --check
python3 scripts/init_db.py
```

## Run locally
```bash
python -m flask --app app run
```

## Deploy
```bash
docker compose up -d --build
```

## Auth flow
1. Register → AppWrite account created + local `leads_users` row (approved=0)
2. Admin runs `python3 scripts/approve_user.py <username>`
3. Login → AppWrite session → local session cookie → dashboard access

## Health check
`GET /leads/health` and `GET /health` return `OK` (no auth required)

## Routes
- `/leads/` — Dashboard (approved users only)
- `/leads/login` — Login form
- `/leads/register` — Registration form
- `/leads/auth/login` — Login POST target
- `/leads/auth/register` — Register POST target
- `/leads/auth/logout` — Logout
- `/leads/health` — Health check
- `/leads/api/monitors` — JSON monitor list
- `/leads/api/monitor/<id>` — JSON monitor detail
