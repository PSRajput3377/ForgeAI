-- Postgres bootstrap. Runs once on first container start (empty data volume).
-- The schema itself is managed by Alembic migrations from Phase 3 onward;
-- this only ensures extensions we rely on are present.
CREATE EXTENSION IF NOT EXISTS "pgcrypto";   -- gen_random_uuid()
