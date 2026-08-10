-- Seagulls Communications CRM — PostgreSQL bootstrap (local Scoop / manual install)
-- Run as a superuser (e.g. postgres):
--   psql -U postgres -f database/init_postgres.sql
--
-- Note: Docker Compose already creates the seagulls user/db via environment variables.

DO $$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'seagulls') THEN
    CREATE ROLE seagulls LOGIN PASSWORD 'seagulls_crm_dev';
  END IF;
END
$$;

SELECT 'CREATE DATABASE seagulls_crm OWNER seagulls'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'seagulls_crm')\gexec

GRANT ALL PRIVILEGES ON DATABASE seagulls_crm TO seagulls;
