# Deployment

## Railway (production target)

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
