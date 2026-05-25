# ChinaVol Leads App — Flask → Next.js Refactor Spec

## Goal

Refactor the existing Flask leads dashboard (`chinavol.com/predictive-leads`) into **Next.js 15 with TypeScript**, deployable on **AppWrite Sites** with SSR. The app must remain functionally identical while switching the stack to JS/TS.

## Why Next.js

AppWrite Sites supports: Next.js, Nuxt, SvelteKit, Angular, Astro, Remix. Next.js was chosen because:
- Best SSR support out of the box
- AppWrite Auth SDK works natively with Next.js
- Mike's eventual cloud migration path (Vercel/Cloudflare) also uses Next.js

## Tech Stack

| Layer | Current | Target |
|---|---|---|
| Framework | Flask 3 + Gunicorn | Next.js 15 (App Router, SSR) |
| Language | Python 3.12 | TypeScript 5 |
| Auth | Flask-Login + AppWrite REST | NextAuth.js + AppWrite Auth SDK |
| Database | SQLite file | AppWrite Databases (move data) |
| Templates | Jinja2 | React 18 + TypeScript |
| Charts | Chart.js (vanilla) | Recharts |
| Styling | Custom CSS | Tailwind CSS |
| Data fetch | yfinance (Python) | yfinance (Next.js API routes) |

## AppWrite Configuration

- **Project ID**: `6a14aeb7001912f0717c`
- **AppWrite URL**: `https://aw.smartpiggies.cloud`
- **Auth**: Email+Password via AppWrite Auth
- **Database**: AppWrite Databases — replace SQLite file

### AppWrite Environment Variables (injected automatically by AppWrite Sites)
```
NEXT_PUBLIC_APPWRITE_ENDPOINT=https://aw.smartpiggies.cloud
NEXT_PUBLIC_APPWRITE_PROJECT_ID=6a14aeb7001912f0717c
APPWRITE_API_KEY=<admin key from /mnt/c/OneDrive/Hermes/Keys/Appwrite Hostinger ChinaVol.txt>
```

## Database Schema

Existing tables to replicate in AppWrite Databases:

### `leads_users`
| Column | Type | Notes |
|---|---|---|
| $id | string | AppWrite user UID |
| username | string | |
| email | string | |
| role | string | 'admin' or 'member' |
| approved | boolean | default false; admin sets true |
| last_login | datetime | nullable |

### `leads_monitors`
| Column | Type | Notes |
|---|---|---|
| $id | string | |
| slug | string | unique |
| pm_question | string | Polymarket question text |
| ticker | string | equity ticker |
| description | string | nullable |
| signal_thresh_pp | float | probability move threshold |
| cooldown_hrs | float | cooldown after signal |
| active | boolean | |

### `leads_signals`
| Column | Type | Notes |
|---|---|---|
| $id | string | |
| monitor_id | string | ref to leads_monitors |
| signal_ts | datetime | when signal fired |
| pm_ts | datetime | Polymarket event time |
| pm_prob_before | float | |
| pm_prob_after | float | |
| pm_move_pp | float | |
| direction | string | 'UP' or 'DOWN' |
| predicted_eq_return_bps | float | |
| confidence | string | LOW/MEDIUM/HIGH |
| status | string | active/pending/resolved |
| outcome_at_1h | float | nullable; resolved才有 |
| outcome_at_4h | float | nullable |
| created_at | datetime | |

### `leads_lead_lag_history`
| Column | Type | Notes |
|---|---|---|
| $id | string | |
| monitor_id | string | ref |
| lead_seconds | int | seconds equity leads Polymarket |
| lag_seconds | int | seconds Polymarket leads equity |
| correlation | float | rolling correlation |
| computed_at | datetime | |

## Existing Users

Already created in AppWrite Auth:
- Mike: `mikea_43fe80dfd9274`, `mike@chinavol.com`, admin, approved=1
- Di: `di_4123945bdaac4`, `xiaodi334@126.com`, member, approved=1

## Page Routes (SSR)

All pages server-side rendered with AppWrite session cookie.

| Route | Description |
|---|---|
| `/` | Redirect to `/dashboard` |
| `/dashboard` | Monitor list with latest lead/lag stats |
| `/monitor/[id]` | Monitor detail with lead/lag history chart + signals |
| `/signals` | All signals table with filters |
| `/login` | Email+password login via AppWrite Auth |
| `/pending` | Shown when user is authenticated but approved=0 |
| `/admin` | User management — approve/revoke members (admin only) |

## API Routes (Next.js Route Handlers)

| Route | Method | Description |
|---|---|---|
| `/api/auth/[...nextauth]` | * | NextAuth.js handlers |
| `/api/monitors` | GET | List active monitors |
| `/api/monitors/[id]` | GET | Monitor detail + lead_lag_history |
| `/api/signals` | GET | Signals list with optional filter params |
| `/api/signals/performance` | GET | Aggregated win/loss stats by monitor |
| `/api/admin/users` | GET | List all users (admin only) |
| `/api/admin/users/[id]/approve` | POST | Approve a user (admin only) |

## Auth Flow

1. User visits `/dashboard` → middleware checks for AppWrite session cookie
2. If no session → redirect to `/login`
3. Login form submits to NextAuth credentials provider
4. NextAuth calls AppWrite `/v1/account/sessions/email` to verify credentials
5. On success → set NextAuth JWT session, redirect to `/dashboard`
6. `leads_users` table in AppWrite DB tracks `role` + `approved`
7. `approved=false` users → redirect to `/pending`
8. Session includes: `userId`, `email`, `role`, `approved`

## Design

- Dark theme (matches existing `leads.css`)
- Font: system-ui / Inter
- Layout: sidebar nav + main content area
- Charts: Recharts LineChart for lead/lag history
- Responsive: mobile-friendly
- No Tailwind (unless you want it) — use existing CSS as base

## Deployment on AppWrite Sites

1. Push code to GitHub repo `chinavol/leads-app`
2. Create Site in AppWrite Console → Connect GitHub repo
3. Framework: **Next.js** (auto-detected)
4. Root directory: `./`
5. Build command: `npm run build`
6. Output directory: `.next`
7. Environment variables (from AppWrite Console):
   - `NEXT_PUBLIC_APPWRITE_ENDPOINT=https://aw.smartpiggies.cloud`
   - `NEXT_PUBLIC_APPWRITE_PROJECT_ID=6a14aeb7001912f0717c`
   - `APPWRITE_API_KEY=<from key file>`
8. Set `APPWRITE_SITE_URL` for OAuth callback
9. Deploy

## Directory Structure (target)

```
leads-app/
├── app/
│   ├── layout.tsx          # Root layout with sidebar
│   ├── page.tsx            # Redirect to /dashboard
│   ├── globals.css
│   ├── dashboard/
│   │   └── page.tsx
│   ├── monitor/[id]/
│   │   └── page.tsx
│   ├── signals/
│   │   └── page.tsx
│   ├── login/
│   │   └── page.tsx
│   ├── pending/
│   │   └── page.tsx
│   ├── admin/
│   │   └── page.tsx
│   └── api/
│       ├── auth/[...nextauth]/route.ts
│       ├── monitors/route.ts
│       ├── monitors/[id]/route.ts
│       ├── signals/route.ts
│       └── admin/...
├── components/
│   ├── MonitorCard.tsx
│   ├── SignalTable.tsx
│   ├── LeadLagChart.tsx
│   ├── Sidebar.tsx
│   └── LoginForm.tsx
├── lib/
│   ├── appwrite.ts         # AppWrite client config
│   ├── auth.ts             # NextAuth config
│   └── db.ts               # AppWrite DB queries
├── types/
│   └── index.ts            # Monitor, Signal, User types
├── next.config.js
├── package.json
└── .env.local              # gitignored; AppWrite injects vars
```

## Migration Priority

1. **Phase 1**: Scaffold Next.js app, set up AppWrite Auth (NextAuth), replicate login + dashboard pages
2. **Phase 2**: Move SQLite data to AppWrite Databases, replicate remaining pages
3. **Phase 3**: Polish charts, admin panel, deploy

## Known Risks / Constraints

- AppWrite Auth session cookies must be readable by both Next.js and AppWrite Sites SSR runtime
- AppWrite Databases requires `$id` fields — use `ID.unique()` when inserting
- The `APPWRITE_API_KEY` admin key must never be exposed client-side — only use in API routes / server components
- `APPWRITE_SITE_URL` must be set for OAuth redirects to work correctly

## Acceptance Criteria

- [ ] Login with `mike@chinavol.com` / `Ch1n@Vol2026!` → lands on dashboard
- [ ] Unapproved user → lands on `/pending`
- [ ] Dashboard shows all active monitors with latest lead/lag data
- [ ] Monitor detail page shows lead/lag chart + signal history
- [ ] Signals page shows filterable signal table
- [ ] Admin page lists users and allows approving/revoking
- [ ] AppWrite Sites deploys and serves at `chinavol.com/predictive-leads` (or configured URL)
- [ ] No hardcoded credentials — all from env vars
