-- Retinue — provision a database and role inside your EXISTING PostgreSQL.
--
-- Run once as a superuser:
--     psql -U postgres -f deploy/postgres-setup.sql
-- or, if Postgres runs in a container:
--     docker exec -i <postgres-container> psql -U postgres < deploy/postgres-setup.sql
--
-- Requires PostgreSQL 13 or newer.
-- Change the password below before running, and use the same value in
-- DATABASE_URL in .env.production.

-- Dedicated role, scoped to this application only.
CREATE ROLE retinue WITH LOGIN PASSWORD 'CHANGE_ME_DB_PASSWORD';

-- Dedicated database owned by that role, isolated from your other apps.
CREATE DATABASE retinue OWNER retinue;

-- Keep the role out of other databases on this instance.
REVOKE ALL ON DATABASE retinue FROM PUBLIC;
GRANT CONNECT ON DATABASE retinue TO retinue;

\connect retinue

-- Alembic creates tables in the public schema; the owner needs to manage it.
ALTER SCHEMA public OWNER TO retinue;
GRANT ALL ON SCHEMA public TO retinue;

-- ---------------------------------------------------------------------------
-- Allowing connections from Docker containers
-- ---------------------------------------------------------------------------
-- If PostgreSQL runs on the HOST, it must accept connections from the Docker
-- bridge. This is the most common cause of "connection refused" on first deploy.
--
--   1. postgresql.conf — listen on the bridge as well as localhost:
--        listen_addresses = 'localhost,172.17.0.1'
--
--   2. pg_hba.conf — allow the docker subnet, scoped to this database/role:
--        host    retinue    retinue    172.16.0.0/12    scram-sha-256
--
--   3. Reload:
--        sudo systemctl reload postgresql
--
-- Do NOT open Postgres to 0.0.0.0, and keep port 5432 closed in the Hetzner
-- Cloud Firewall — only local containers should ever reach it.
--
-- Verify the docker bridge address with:
--        ip addr show docker0
