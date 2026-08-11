# Deployment

## Vercel (frontend) + Railway (API / Postgres)

Vercel hosts the React SPA. FastAPI + PostgreSQL stay on Railway (Vercel does not run long-lived FastAPI/Postgres well).

```text
Browser → Vercel (SPA) → VITE_API_BASE_URL → Railway FastAPI → Railway PostgreSQL
```

**Live frontend:** https://seagulls-crm.vercel.app  
(also https://frontend-eta-virid-53.vercel.app)

### 1. Deploy frontend to Vercel

From `frontend/` (uses `frontend/vercel.json`):

```powershell
cd frontend
npx vercel@latest --prod --yes
```

Or connect the GitHub repo in the Vercel dashboard with **Root Directory = `frontend`**.

### 2. Vercel environment variable

| Variable | Value |
|---|---|
| `VITE_API_BASE_URL` | Public Railway API origin, no trailing slash (e.g. `https://your-service.up.railway.app`) |

Rebuild after changing `VITE_*` vars (they are baked in at build time).

### 3. Railway CORS

On the Railway web service, set `CORS_ORIGINS` to include your Vercel URL(s), e.g.:

```text
https://seagulls-crm.vercel.app,https://frontend-eta-virid-53.vercel.app
```

Or temporarily `*` while validating.

### 4. Postgres

Reuse the existing Railway PostgreSQL `DATABASE_URL` on the Railway API service. Do not create a new DB unless Railway Postgres is unavailable (then Neon/Supabase + update Railway `DATABASE_URL`).

## Railway (API + optional all-in-one Docker)

Architecture:

```text
Internet → Railway HTTPS URL → FastAPI (UI + /api) → Railway PostgreSQL
```

### 1. Push this repo to GitHub

```powershell
git push -u origin main
```

### 2. Create the Railway project (browser)

1. Open https://railway.app and sign in (GitHub login recommended)
2. **New Project** → **Deploy from GitHub repo** → select `123fakhar/CRM`
3. **Add Plugin / Database** → **PostgreSQL**
4. Open the **web service** → **Variables** and set:

| Variable | Value |
|---|---|
| `ENVIRONMENT` | `production` |
| `SECRET_KEY` | strong random string (Railway can generate) |
| `DATABASE_URL` | reference the Postgres variable `${{Postgres.DATABASE_URL}}` |
| `STATIC_DIR` | `/app/static` |
| `BOOTSTRAP_ADMIN_EMAIL` | your real admin email |
| `BOOTSTRAP_ADMIN_PASSWORD` | strong password (min 8 chars) |
| `BOOTSTRAP_ADMIN_NAME` | optional display name |

Do **not** set `SEED_DEMO_DATA` / do not rely on demo accounts in production.

5. Ensure the service uses the root `Dockerfile` (Railway detects `railway.toml`)
6. Deploy / wait for build success
7. Open the generated `*.up.railway.app` URL

### 3. Health check

```text
GET https://<your-service>.up.railway.app/api/health
```

### Notes

- Frontend and API are same-origin (no localhost, no separate API URL required)
- Demo users (`@seagullsdemo.com`) are **not** created when `ENVIRONMENT=production`
- Local development remains unchanged (`ENVIRONMENT=development` + local Postgres)

## Docker Compose (local/VPS alternative)

```powershell
docker compose up -d --build
```
