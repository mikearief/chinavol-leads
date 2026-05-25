# ChinaVol Leads App

Next.js 15 + TypeScript refactor of the ChinaVol Pro leads dashboard.

## Stack

- Next.js 15 App Router
- TypeScript
- NextAuth credentials provider backed by Appwrite Auth
- Appwrite Databases for leads users, monitors, signals, and lead/lag history
- Recharts for lead/lag charts
- Dark custom CSS based on the previous Flask app

## Setup

Install dependencies:

```bash
npm install
```

Create `.env.local`:

```env
NEXT_PUBLIC_APPWRITE_ENDPOINT=https://aw.smartpiggies.cloud
NEXT_PUBLIC_APPWRITE_PROJECT_ID=6a14aeb7001912f0717c
APPWRITE_DATABASE_ID=<database-id>
APPWRITE_API_KEY=<server-api-key>
NEXTAUTH_SECRET=<generate-with-openssl-rand-base64-32>
NEXTAUTH_URL=http://localhost:3000
```

The Appwrite API key is stored outside the repo at:

```text
/mnt/c/OneDrive/Hermes/Keys/Appwrite Hostinger ChinaVol.txt
```

Do not commit real secrets. `.env.local` is ignored by git.

## Appwrite Schema

Create the database and collections documented in [appwrite-setup.md](./appwrite-setup.md).

## Development

```bash
npm run dev
```

Open `http://localhost:3000`.

Expected flow:

- `/` redirects to `/dashboard`
- Unauthenticated users are redirected to `/login`
- Authenticated unapproved users are redirected to `/pending`
- Approved users can access dashboard, monitor detail, and signals
- Admin users can access `/admin`

## Production

For Appwrite Sites:

- Framework: Next.js
- Build command: `npm run build`
- Output directory: `.next`
- Required env vars: same as `.env.local`, with `NEXTAUTH_URL` set to the deployed URL

## Scripts

```bash
npm run dev
npm run build
npm run start
npm run lint
```
