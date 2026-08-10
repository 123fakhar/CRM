# Database setup — PostgreSQL

## Primary database

The CRM uses **PostgreSQL** as its primary database.

Default connection (local Scoop / Docker Compose):

```text
postgresql+psycopg2://seagulls:seagulls_crm_dev@127.0.0.1:5432/seagulls_crm
```

## Tables

### users
Primary identity for login. Roles: `admin`, `agent`, `closer`.

### agents
Sales agent directory. Optional `user_id` link for Agent-role accounts.

### closers
Closer directory. Optional `user_id` link for Closer-role accounts (required for form auto-fill).

### campaigns
Campaign directory used by the sales form dropdown.

### leads
Core sales records. Separate status fields:
- `initial_status` (always Pending on create)
- `buyer_response`
- `final_status` (Pending / Accepted / Rejected)

Foreign keys: `agent_id`, `closer_id`, `campaign_id`, `created_by`, `updated_by`.

### audit_logs
Append-only change history. Agents/Closers cannot modify via API (Admin read-only endpoint).

## Relationships

```
User 1—0..1 Agent
User 1—0..1 Closer
Agent 1—* Lead
Closer 1—* Lead
Campaign 1—* Lead
User 1—* Lead (created_by / updated_by)
User 1—* AuditLog
```

## Bootstrap (local Scoop PostgreSQL)

```powershell
# Start server
pg_ctl -D "$env:USERPROFILE\scoop\apps\postgresql\current\data" -l "$env:USERPROFILE\scoop\apps\postgresql\current\logfile.log" start

# Create role + database
psql -U postgres -f database\init_postgres.sql
```

Tables are created automatically on API startup (`Base.metadata.create_all`).

## Migrate from SQLite

If you already have `backend/seagulls_crm.db`:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
$env:PYTHONPATH=(Get-Location)
$env:SQLITE_SOURCE_URL="sqlite:///./seagulls_crm.db"
python -m app.scripts.migrate_sqlite_to_postgres
```

## Docker alternative

```powershell
docker compose up -d db
```
