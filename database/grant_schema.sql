-- Run after connecting to seagulls_crm:
--   psql -U postgres -d seagulls_crm -f database/grant_schema.sql

GRANT ALL ON SCHEMA public TO seagulls;
ALTER SCHEMA public OWNER TO seagulls;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO seagulls;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO seagulls;
