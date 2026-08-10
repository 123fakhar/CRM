# Seagulls Communications — Inhouse Sales CRM

Production-quality internal CRM for tracking leads submitted by Closers and attributing accepted sales to Agents.

## Stack

- **Frontend:** React + Vite + TypeScript + Tailwind CSS
- **Backend:** FastAPI + SQLAlchemy + Pydantic + JWT
- **Database:** PostgreSQL (primary)
- **Reports:** Pandas + OpenPyXL (CSV / Excel export)

## Prerequisites

- Python 3.11+
- Node.js 20+
- PostgreSQL 16+ running locally (or Docker)

### Local PostgreSQL (Scoop — already used on this machine)

```powershell
# Ensure Scoop PostgreSQL is on PATH, then:
pg_ctl -D "$env:USERPROFILE\scoop\apps\postgresql\current\data" -l "$env:USERPROFILE\scoop\apps\postgresql\current\logfile.log" start
pg_isready
```

Bootstrap DB/role (once):

```powershell
psql -U postgres -f database\init_postgres.sql
```

### Docker alternative

```powershell
docker compose up -d db
```

## Quick Start

### 1. Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload --port 8000
```

API docs: http://127.0.0.1:8000/docs

Default `DATABASE_URL`:

```text
postgresql+psycopg2://seagulls:seagulls_crm_dev@127.0.0.1:5432/seagulls_crm
```

### 2. Frontend

```powershell
cd frontend
npm install
npm run dev
```

App: http://localhost:5173

### TEST seed accounts (development only)

| Role   | Email                    | Password   |
|--------|--------------------------|------------|
| Admin  | admin@seagullsdemo.com   | Admin123!  |
| Agent  | agent@seagullsdemo.com   | Agent123!  |
| Closer | closer@seagullsdemo.com  | Closer123! |

Seed agents/closers/campaigns are labeled `(TEST)` and are not real company data.

### Migrate existing SQLite data (optional)

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
$env:PYTHONPATH=(Get-Location)
$env:SQLITE_SOURCE_URL="sqlite:///./seagulls_crm.db"
python -m app.scripts.migrate_sqlite_to_postgres
```

## Roles

| Capability | Admin | Agent | Closer |
|---|---|---|---|
| View dashboard / reports | Yes | Own scope | Own scope |
| Submit sales form | If closer profile | No | Yes |
| Edit / delete leads | Yes | No | No |
| Manage users/agents/closers/campaigns | Yes | No | No |
| Export reports | Yes | No | No |
| View audit log | Yes | No | No |

## Sales workflow

1. Closer submits **Seagulls Communications Inhouse Sales Sheet**
2. Lead created with Initial/Buyer/Final = Pending
3. Record locked for Agent & Closer
4. Admin enters Buyer Response + Final Status (+ rejection reason if Rejected)
5. Dashboard / reports recalculate from the database

## Google Form

External Google Forms API credentials were **not** available. The CRM sales form implements the required fields. See `docs/GOOGLE_FORM.md` for what remains to connect an external Google Form.

## Tests

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
$env:PYTHONPATH=(Get-Location)
pytest -q
```

Unit tests use an isolated SQLite file; the running application uses PostgreSQL.
