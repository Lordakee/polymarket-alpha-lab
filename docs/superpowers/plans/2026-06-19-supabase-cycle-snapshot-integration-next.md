# Supabase Cycle Snapshot Integration Next Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** After the current cycle snapshot row/store node lands, wire paper recommendation cycle snapshots into Supabase/Postgres as the primary persistence path while preserving readonly paper observability.

**Architecture:** Keep the existing pure snapshot reducer, row codec, and DB-API store as the core contract. Add thin configuration, psycopg connection, runner/CLI wiring, and DB-backed trend-read layers around that contract; all live database work is opt-in by explicit env/config and remains append/read report storage only. JSONL can remain local debug/export evidence, but Supabase/Postgres becomes the DB-first snapshot source for integration and trends.

**Tech Stack:** Python stdlib, `psycopg[binary]`, DB-API store functions, pytest with env-gated integration smoke tests, Supabase local stack, SQL migrations, CodeGraph-first navigation.

---

## Current Preconditions

- Start only after the row/store node lands with these contracts available:
  - `src/polymarket_alpha_lab/paper_recommendation_cycle_snapshot.py`
  - `src/polymarket_alpha_lab/paper_recommendation_cycle_snapshot_db_row.py`
  - `src/polymarket_alpha_lab/paper_recommendation_cycle_snapshot_store.py`
  - `src/polymarket_alpha_lab/paper_recommendation_cycle_snapshot_trend.py`
  - `supabase/migrations/20260619000000_paper_recommendation_cycle_snapshots.sql`
- The DB-API store is the abstraction boundary:
  - `insert_paper_recommendation_cycle_snapshot(connection, report, table_name=...)`
  - `load_paper_recommendation_cycle_snapshots(connection, config_version=None, limit=None, table_name=...)`
- Transaction ownership stays with the caller/adapter. The store should not silently commit.

## Strict Phase Boundary

This node remains paper-only, report-only, and readonly.

Forbidden in every task:

- live trading
- authenticated exchange flows
- wallet or private-key access
- account reads or account mutation
- real order construction, signing, submission, cancellation, replacement, or status reconciliation
- relayer, exchange, or client mutation
- service-role key handling in code, tests, docs, or logs

Allowed in this node:

- local env/config parsing for database connection settings
- applying local Supabase migrations
- inserting already-built paper cycle snapshot reports into Postgres
- reading paper cycle snapshots back from Postgres
- building readonly trend reports over DB-loaded snapshots
- env-gated local smoke tests against the existing Supabase dev stack

## Local Runtime Facts

Observed on June 19, 2026:

- Local Supabase containers are running and healthy via `sudo -n docker ps`.
- Container psql is available via `sudo -n docker exec supabase-db psql`.
- `sudo -n docker exec supabase-db psql --version` reported PostgreSQL `17.6`.
- Supabase CLI is available at `/home/ubuntu/supabase/node_modules/.bin/supabase`.
- `/home/ubuntu/supabase/node_modules/.bin/supabase --version` reported `2.76.14`.
- Do not record database passwords, access tokens, JWTs, service-role keys, wallet material, or private keys in this plan, tests, fixtures, docs, command output, or logs.

## Parallel Development Structure

### Node A: CLI Config And Env Loader

**Purpose:** Add an explicit local configuration boundary for DB-first snapshot persistence without teaching core reducers about env vars.

**Likely files:**

- Create: `src/polymarket_alpha_lab/supabase_cycle_snapshot_config.py`
- Test: `tests/test_supabase_cycle_snapshot_config.py`
- Modify later: `src/polymarket_alpha_lab/cli.py`
- Modify later: `tests/test_cli.py`

**Implementation shape:**

- Define a frozen config such as `PaperRecommendationCycleSnapshotDbConfig`.
- Read only non-secret booleans/table names from flags/config and read the database DSN from an explicit env variable at process edge.
- Suggested env/flag names:
  - `POLYMARKET_ALPHA_LAB_CYCLE_SNAPSHOT_DB_DSN`
  - `POLYMARKET_ALPHA_LAB_CYCLE_SNAPSHOT_DB_TABLE`
  - `POLYMARKET_ALPHA_LAB_CYCLE_SNAPSHOT_DB_ENABLED`
- Require DB persistence to be explicitly enabled; missing DSN should disable DB writes or raise a clear config error only when DB writes are requested.
- Validate table names with the same simple lowercase identifier rule as the current store.
- Never print DSNs or secrets. Error messages may say an env var is missing, never echo its value.

**Tests:**

- Env loader returns disabled config when no DB env is set.
- Enabled config requires a nonblank DSN.
- Table name rejects schema-qualified names, punctuation, uppercase, blanks, and SQL fragments.
- CLI/config errors redact DSN values.

### Node B: Real Psycopg Adapter And Env-Gated Smoke Test

**Purpose:** Add the first real database adapter around the DB-API store using `psycopg`, with deterministic local integration coverage gated by env.

**Likely files:**

- Create: `src/polymarket_alpha_lab/paper_recommendation_cycle_snapshot_psycopg.py`
- Test: `tests/test_paper_recommendation_cycle_snapshot_psycopg.py`
- Integration test: `tests/test_paper_recommendation_cycle_snapshot_supabase_smoke.py`

**Implementation shape:**

- Use `psycopg.connect(dsn)` only inside the adapter/smoke path.
- Provide small functions such as:
  - `open_cycle_snapshot_connection(config)`
  - `insert_cycle_snapshot_with_commit(dsn, report, table_name=...)`
  - `load_cycle_snapshots_from_dsn(dsn, config_version=None, limit=None, table_name=...)`
- Let the existing store continue to own SQL shape and row recovery.
- Commit only after a successful insert when the adapter owns the connection.
- Roll back and close on exceptions.
- Keep tests using fake connection objects for unit coverage.

**Smoke test gate:**

- Skip unless both are set:
  - `POLYMARKET_ALPHA_LAB_CYCLE_SNAPSHOT_DB_DSN`
  - `POLYMARKET_ALPHA_LAB_RUN_SUPABASE_SMOKE=1`
- The smoke test should:
  - apply or assume the migration exists
  - insert one fully typed `PaperRecommendationCycleSnapshotReport`
  - read it back through `load_paper_recommendation_cycle_snapshots`
  - assert hard flags are `True`
  - assert duplicate insert is idempotent through `ON CONFLICT DO NOTHING`
- The smoke test must not use service-role keys, API auth, wallets, exchange clients, or order paths.

### Node C: Runner And Cycle Wiring

**Purpose:** Persist a recommendation cycle snapshot after a cycle/report bundle is already built, without changing cycle semantics or promoting anything to trading.

**Likely files:**

- Modify: `src/polymarket_alpha_lab/runner.py`
- Modify: `src/polymarket_alpha_lab/cli.py`
- Test: `tests/test_runner.py`
- Test: `tests/test_cli.py`
- Scope test: existing runner/CLI scope tests if present.

**Implementation shape:**

- Add optional DB snapshot sink parameters to runner/CLI, default disabled.
- Keep current `PaperStrategyCycleLog` JSONL behavior unless a later plan removes it.
- When a cycle snapshot is available from the recommendation bundle path:
  - build the snapshot using `build_paper_recommendation_cycle_snapshot_report`
  - insert it through the DB adapter only when DB persistence is enabled
  - continue returning paper-only `RunLoopSummary`
- Add a count field only if needed, for example `cycle_snapshots_persisted`, and keep it report-only/readonly.
- A failed optional DB write should follow an explicit policy:
  - default: fail the iteration if DB-first persistence was requested
  - optional later: `log_and_continue` only if the operator explicitly requests degraded local output
- Do not create authenticated clients, wallet clients, order clients, or exchange mutation paths.

**Tests:**

- Disabled DB config does not call the DB adapter.
- Enabled DB config calls the adapter once per completed snapshot.
- DB adapter exception is handled according to the configured policy.
- CLI flags/env config wire into the runner without printing secrets.
- Existing non-DB runner tests continue to pass unchanged in behavior.

### Node D: Trend Reads From DB Store

**Purpose:** Build trend reports from snapshots loaded from Postgres, not from JSONL-primary logs.

**Likely files:**

- Create: `src/polymarket_alpha_lab/paper_recommendation_cycle_snapshot_db_trend.py`
- Test: `tests/test_paper_recommendation_cycle_snapshot_db_trend.py`
- Modify later: `src/polymarket_alpha_lab/cli.py`
- Modify later: `tests/test_cli.py`

**Implementation shape:**

- Load snapshots with `load_paper_recommendation_cycle_snapshots(connection, config_version=..., limit=...)`.
- The store orders rows by `generated_at DESC`; reverse to chronological order before passing into `build_paper_recommendation_cycle_snapshot_trend_report` if the trend builder expects source chronology for tie/latest behavior.
- Preserve trend report flags:
  - `paper_only is True`
  - `report_only is True`
  - `readonly is True`
- Add a readonly CLI report command only after the reducer helper is tested.
- The CLI should print summary fields only, not DSNs or raw payload JSON.

**Tests:**

- DB trend helper calls the store with config version and limit.
- Loaded descending snapshots are normalized into the expected trend input order.
- Empty DB result produces a clear no-data error if the current trend builder requires at least one snapshot.
- Unsafe loaded snapshots are rejected by the existing trend builder/store recovery path.

### Node E: Supabase Migration Application Instructions

**Purpose:** Make local migration application repeatable for developers and smoke tests without embedding secrets.

**Likely files:**

- Create or update a narrow runbook only if approved by the owning plan; otherwise keep instructions in implementation handoff.
- Do not edit migrations in this node unless the smoke test proves the current migration is incompatible with the row/store contract.

**Local commands:**

```bash
sudo -n docker ps
sudo -n docker exec supabase-db psql --version
/home/ubuntu/supabase/node_modules/.bin/supabase --version
```

Apply migration with a local operator-supplied connection target. Do not paste secrets into shell history or docs.

Preferred local-container path when the Supabase CLI project link is not configured:

```bash
sudo -n docker exec -i supabase-db psql -v ON_ERROR_STOP=1 -U postgres -d postgres \
  < supabase/migrations/20260619000000_paper_recommendation_cycle_snapshots.sql
```

Supabase CLI path, if the local self-hosted project is configured for migration workflows:

```bash
/home/ubuntu/supabase/node_modules/.bin/supabase migration list
/home/ubuntu/supabase/node_modules/.bin/supabase db push
```

Verification queries through the container:

```bash
sudo -n docker exec supabase-db psql -U postgres -d postgres -c \
  "\\d+ public.paper_recommendation_cycle_snapshots"
sudo -n docker exec supabase-db psql -U postgres -d postgres -c \
  "select count(*) from public.paper_recommendation_cycle_snapshots;"
```

## Recommended Execution Order

- [ ] Node E first: verify the migration is applied locally and the table exists.
- [ ] Node A and Node B in parallel: config/env loader and psycopg adapter do not need runner wiring.
- [ ] Node D in parallel after Node B store contract is stable: DB trend reads can use fake connections before real smoke coverage.
- [ ] Node C last: wire CLI/runner only after config, adapter, and trend helper interfaces are stable.
- [ ] Run smoke tests only after migration verification and explicit env gate setup.

## Verification Gates

Focused unit gate:

```bash
.venv/bin/python -m pytest \
  tests/test_supabase_cycle_snapshot_config.py \
  tests/test_paper_recommendation_cycle_snapshot_psycopg.py \
  tests/test_paper_recommendation_cycle_snapshot_db_trend.py \
  tests/test_runner.py \
  tests/test_cli.py -q
```

Env-gated local smoke gate:

```bash
POLYMARKET_ALPHA_LAB_RUN_SUPABASE_SMOKE=1 \
POLYMARKET_ALPHA_LAB_CYCLE_SNAPSHOT_DB_DSN="$POLYMARKET_ALPHA_LAB_CYCLE_SNAPSHOT_DB_DSN" \
.venv/bin/python -m pytest tests/test_paper_recommendation_cycle_snapshot_supabase_smoke.py -q
```

Repository gate:

```bash
.venv/bin/python -m pytest -q
.venv/bin/python -m compileall -q src tests
git diff --check
codegraph status .
```

Boundary scan:

```bash
rg -n "private.?key|wallet|sign|submit|cancel|order|auth|service.?role|secret|token" \
  src/polymarket_alpha_lab tests docs/superpowers/plans
```

Findings from the boundary scan are not automatically failures because existing docs/tests may mention forbidden terms. They are failures if this node introduces a live trading, auth, wallet, order, signing, credential, or secret-handling surface.

## Handoff Notes

- Treat Supabase/Postgres as the primary snapshot persistence path once enabled.
- Keep JSONL as compatibility/debug output until a later cleanup plan explicitly demotes or removes it.
- Keep DSN handling at the process edge and redact it from every error/log path.
- Use CodeGraph before code discovery in this indexed repository.
- Do not touch source, tests, migrations, pyproject, or existing docs from this planning node; those belong to future implementation nodes.
