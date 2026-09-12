"""Closed bootstrap and checksum-locked migration scripts for a private cluster."""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import re

from .files import Layout, fail, no_links

DATABASE = 'polymarket_alpha_lab'
ADMIN = 'pal_owner'
APPLICATION = 'pal_app'


def literal(value: str) -> str:
    if type(value) is not str or '\0' in value:
        fail('project_postgres_invalid_sql_value')
    return "'" + value.replace("'", "''") + "'"


def server_configuration(port: int) -> str:
    if type(port) is not int or not 1024 <= port <= 65535:
        fail('project_postgres_invalid_port')
    return f"""# Managed exclusively by polymarket-alpha-lab; no external includes.
listen_addresses = '127.0.0.1'
port = {port}
unix_socket_directories = ''
password_encryption = 'scram-sha-256'
ssl = off
shared_buffers = '64MB'
max_connections = 30
fsync = on
full_page_writes = on
synchronous_commit = on
timezone = 'UTC'
log_statement = 'none'
log_min_messages = 'fatal'
log_min_error_statement = 'panic'
log_error_verbosity = 'terse'
logging_collector = off
shared_preload_libraries = ''
session_preload_libraries = ''
local_preload_libraries = ''
"""


def authentication_configuration() -> str:
    return f"""# Only this project's dedicated roles and database, loopback, SCRAM.
host {DATABASE} {ADMIN},{APPLICATION} 127.0.0.1/32 scram-sha-256
host postgres {ADMIN} 127.0.0.1/32 scram-sha-256
host all all 0.0.0.0/0 reject
host all all ::0/0 reject
local all all reject
"""


def create_database_sql(password: str) -> str:
    if not re.fullmatch(r'[0-9a-f]{64}', password):
        fail('project_postgres_invalid_generated_password')
    return f"""
CREATE ROLE {APPLICATION} LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE
  NOREPLICATION NOBYPASSRLS NOINHERIT PASSWORD {literal(password)};
CREATE DATABASE {DATABASE} OWNER {ADMIN} TEMPLATE template0 ENCODING 'UTF8';
REVOKE ALL ON DATABASE postgres FROM PUBLIC;
REVOKE ALL ON DATABASE template0 FROM PUBLIC;
REVOKE ALL ON DATABASE template1 FROM PUBLIC;
REVOKE ALL ON DATABASE {DATABASE} FROM PUBLIC;
GRANT CONNECT ON DATABASE {DATABASE} TO {APPLICATION};
"""


def bootstrap_sql(instance_id: str, root_hash: str, system_id: str) -> str:
    return f"""
BEGIN;
REVOKE ALL ON SCHEMA public FROM PUBLIC;
CREATE SCHEMA project_private;
REVOKE ALL ON SCHEMA project_private FROM PUBLIC;
CREATE TABLE project_private.instance (
 singleton boolean PRIMARY KEY CHECK(singleton), instance_id text NOT NULL,
 root_sha256 text NOT NULL, system_identifier text NOT NULL);
INSERT INTO project_private.instance VALUES(true,{literal(instance_id)},{literal(root_hash)},{literal(system_id)});
CREATE TABLE project_private.migrations (
 name text PRIMARY KEY, sha256 text NOT NULL, applied_at timestamptz NOT NULL DEFAULT clock_timestamp());
REVOKE ALL ON ALL TABLES IN SCHEMA project_private FROM PUBLIC;
GRANT USAGE ON SCHEMA project_private TO {APPLICATION};
GRANT SELECT ON project_private.instance TO {APPLICATION};
ALTER DEFAULT PRIVILEGES FOR ROLE {ADMIN} REVOKE EXECUTE ON FUNCTIONS FROM PUBLIC;
COMMIT;
"""


GRANTS = f"""
BEGIN;
REVOKE ALL ON SCHEMA public, research_capture FROM PUBLIC;
GRANT USAGE ON SCHEMA public, research_capture TO {APPLICATION};
GRANT SELECT, INSERT ON ALL TABLES IN SCHEMA public, research_capture TO {APPLICATION};
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public, research_capture TO {APPLICATION};
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA research_capture TO {APPLICATION};
-- Preserve the original table's RLS instead of giving the app BYPASSRLS.
DO $policy$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname='public'
      AND tablename='team_research_assignment_reports' AND policyname='pal_project_read') THEN
    CREATE POLICY pal_project_read ON public.team_research_assignment_reports
      FOR SELECT TO {APPLICATION} USING (true);
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname='public'
      AND tablename='team_research_assignment_reports' AND policyname='pal_project_insert') THEN
    CREATE POLICY pal_project_insert ON public.team_research_assignment_reports
      FOR INSERT TO {APPLICATION} WITH CHECK (true);
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname='public'
      AND tablename='team_research_assignment_reports' AND policyname='pal_project_read'
      AND roles=ARRAY['{APPLICATION}']::name[] AND cmd='SELECT' AND permissive='PERMISSIVE'
      AND qual='true' AND with_check IS NULL)
     OR NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname='public'
      AND tablename='team_research_assignment_reports' AND policyname='pal_project_insert'
      AND roles=ARRAY['{APPLICATION}']::name[] AND cmd='INSERT' AND permissive='PERMISSIVE'
      AND qual IS NULL AND with_check='true') THEN
    RAISE EXCEPTION 'project_postgres_policy_conflict';
  END IF;
END $policy$;
COMMIT;
"""


def migration_catalog(layout: Layout) -> tuple[tuple[str, str, str], ...]:
    """Preserve original names/bytes; no Supabase service is used by these SQLs."""
    path = layout.root / 'database/migrations.lock.json'
    no_links(path)
    if path.stat().st_size > 262144:
        fail('project_postgres_invalid_migration_manifest')
    try:
        catalog = json.loads(path.read_text(encoding='utf-8'))
        if set(catalog) != {'format', 'migrations'} or catalog['format'] != 'native-postgres-migrations-v1':
            raise ValueError
        entries = catalog['migrations']
        if type(entries) is not list or not 1 <= len(entries) <= 1000:
            raise ValueError
        rows = []
        for item in entries:
            if set(item) != {'name', 'sha256', 'transaction_wrapper'}:
                raise ValueError
            name, digest = item['name'], item['sha256']
            if (not re.fullmatch(r'[0-9]{14}_[a-z0-9_]+\.sql', name)
                    or not re.fullmatch(r'[a-f0-9]{64}', digest)
                    or type(item['transaction_wrapper']) is not bool):
                raise ValueError
            source = layout.root / 'supabase/migrations' / name
            no_links(source)
            if source.stat().st_size > 2097152:
                raise ValueError
            raw = source.read_bytes()
            if sha256(raw).hexdigest() != digest:
                fail('project_postgres_migration_changed')
            body = raw.decode('utf-8')
            if item['transaction_wrapper']:
                body, start_count = re.subn(r'\A(?:\s|--[^\n]*\n)*begin;', '', body, count=1, flags=re.I)
                body, end_count = re.subn(r'commit;\s*\Z', '', body, count=1, flags=re.I)
                if (start_count, end_count) != (1, 1):
                    raise ValueError
            # These are fixed, reviewed scripts, NOT an arbitrary SQL executor.
            if re.search(r'(?im)^\s*\\|\b(?:commit|begin|rollback)\s*;', body):
                raise ValueError
            rows.append((name, digest, body))
        names = [row[0] for row in rows]
        actual = sorted(p.name for p in (layout.root / 'supabase/migrations').glob('*.sql'))
        if names != sorted(set(names)) or names != actual:
            fail('project_postgres_migration_inventory_mismatch')
        return tuple(rows)
    except (OSError, ValueError, KeyError, TypeError):
        fail('project_postgres_invalid_migration_manifest')


def pending_migrations(catalog, applied):
    if type(applied) is not list or len(applied) > len(catalog):
        fail('project_postgres_migration_history_conflict')
    expected = [{'name': name, 'sha256': digest} for name, digest, _ in catalog]
    if applied != expected[:len(applied)]:
        fail('project_postgres_migration_history_conflict')
    return catalog[len(applied):]


def migration_sql(name: str, digest: str, body: str) -> str:
    # DDL and its receipt commit atomically. Previously committed migrations
    # survive a later failed one; retries resume only the verified pending tail.
    return ("BEGIN;\nSELECT pg_advisory_xact_lock(73198642);\n" + body +
        f"\nINSERT INTO project_private.migrations(name,sha256) VALUES({literal(name)},{literal(digest)});\nCOMMIT;\n")
