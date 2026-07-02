# Team Research Assignment Persistence And History Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Persist generated team research assignment reports to local Supabase/Postgres and expose a Phase 1 report-only history summary for long-term team memory.

**Architecture:** Follow the existing team diagnostics snapshot pattern: pure report-to-row codec, DB-API repository, env-only local Supabase/Postgres psycopg adapter, migration, optional CLI sink, and a pure history reducer over recovered assignment reports. The history reducer is independent from the DB writer and can be built in parallel because it only consumes `TeamResearchAssignmentReport` values.

**Tech Stack:** Python dataclasses, Decimal-only numeric values, DB-API cursor contract, optional psycopg JSONB adapter, local Supabase/Postgres migrations, pytest.

## Global Constraints

- Phase 1 only: `paper_only=True`, `report_only=True`, and `readonly=True` on configs, rows, reports, and recovered payloads.
- No live trading, no auth, no wallet/account/private key reads, no order signing/submission/cancel/replace, no exchange mutation.
- No investment recommendation, ranking, trade instruction, position sizing, or strategy-weight tuning.
- Durable project data uses local Supabase/Postgres only. No SQLite, Redis, Mongo, SQLAlchemy, hosted DB assumptions, or file-backed durable substitute.
- CLI configuration stays env-only. Do not add `--dsn`, `--table`, `--persist`, live/auth/wallet/order/trade/execute/submit flags.
- DB and CLI errors must redact DSNs, hosts, table names, market slugs/questions, payloads, hashes, credentials, account/wallet/auth/key fields, and order-like fields.
- Use TDD for behavior changes: write a failing focused test, verify it fails, implement, then verify green.
- Use CodeGraph before grep/find/raw reads when locating or understanding indexed code.
- Review uses Claude Code only, model `claude-opus-4-8`, thinking `max`.

---

### Task 1: Assignment Report DB Row Codec

**Files:**
- Create: `src/polymarket_alpha_lab/team_research_assignment_db_row.py`
- Create: `tests/test_team_research_assignment_db_row.py`

**Interfaces:**
- Consumes: `TeamResearchAssignmentReport` from `src/polymarket_alpha_lab/team_research_assignment.py`.
- Produces:
  - `TeamResearchAssignmentDbRow`
  - `team_research_assignment_report_to_db_row(report)`
  - `team_research_assignment_report_from_db_row(row)`
  - aliases `to_db_row` and `from_db_row`

- [x] **Step 1: Write failing tests**

Create tests covering:
- canonical payload hash round trip
- UTC normalization
- materialized row fields:
  - `report_sha256`
  - `generated_at`
  - `config_version`
  - `source_queue_config_version`
  - `source_route_config_version`
  - `source_memory_config_version`
  - `assignment_status`
  - `assignment_count`
  - `assigned_count`
  - `watch_count`
  - `blocked_count`
  - `reason_codes_json`
  - `payload_json`
  - `paper_only`
  - `report_only`
  - `readonly`
- mutable JSON inputs are copied
- false hard flags in report or payload are rejected
- payload changes to materialized fields are rejected
- floats and Decimals inside JSON payload inputs are rejected unless produced by the codec as strings

Run: `pytest tests/test_team_research_assignment_db_row.py -q`
Expected: fail with missing module or missing symbols.

- [x] **Step 2: Implement pure codec**

Implement the row module by mirroring the validation shape of `team_diagnostics_snapshot_db_row.py`, adjusted to assignment fields. Use `dataclasses.asdict`, canonical JSON with `sort_keys=True`, `allow_nan=False`, `separators=(",", ":")`, and `json_recovery.from_jsonable` for recovery.

- [x] **Step 3: Verify focused tests**

Run: `pytest tests/test_team_research_assignment_db_row.py -q`
Expected: pass.

### Task 2: Assignment Report DB Store, Env Config, Psycopg Adapter, And Migration

**Files:**
- Create: `src/polymarket_alpha_lab/team_research_assignment_store.py`
- Create: `src/polymarket_alpha_lab/supabase_team_research_assignment_config.py`
- Create: `src/polymarket_alpha_lab/team_research_assignment_psycopg.py`
- Create: `supabase/migrations/20260702000000_team_research_assignment_reports.sql`
- Create: `tests/test_team_research_assignment_store.py`
- Create: `tests/test_team_research_assignment_config.py`
- Create: `tests/test_team_research_assignment_psycopg.py`
- Create: `tests/test_team_research_assignment_schema.py`

**Interfaces:**
- Consumes Task 1 codec symbols.
- Produces:
  - default table `team_research_assignment_reports`
  - env vars:
    - `POLYMARKET_ALPHA_LAB_TEAM_RESEARCH_ASSIGNMENT_DB_ENABLED`
    - `POLYMARKET_ALPHA_LAB_TEAM_RESEARCH_ASSIGNMENT_DB_DSN`
    - `POLYMARKET_ALPHA_LAB_TEAM_RESEARCH_ASSIGNMENT_DB_TABLE`
  - `insert_team_research_assignment_report`
  - `insert_team_research_assignment_report_with_result`
  - `load_team_research_assignment_reports`
  - `insert_team_research_assignment_report_from_env`
  - `load_team_research_assignment_reports_from_env`

- [x] **Step 1: Write failing store/config/adapter/schema tests**

Tests must prove:
- parameterized SQL for insert and select
- `ON CONFLICT (report_sha256) DO NOTHING`
- newest-first load ordering by `generated_at DESC, inserted_at DESC, report_sha256 DESC`
- filters: `assignment_status`, `config_version`, `limit`
- safe table-name validation before cursor creation
- disabled env returns `None` and does not connect
- enabled env requires local DSN and redacts remote/secret DSNs
- default insert uses the `with_result` store function
- schema creates `public.team_research_assignment_reports`
- schema has JSONB `reason_codes_json` and `payload_json`
- schema has indexes for generated_at, assignment_status, config_version, reason_codes, and payload

Run:
`pytest tests/test_team_research_assignment_store.py tests/test_team_research_assignment_config.py tests/test_team_research_assignment_psycopg.py tests/test_team_research_assignment_schema.py -q`
Expected: fail with missing modules or migration.

- [x] **Step 2: Implement store/config/adapter/migration**

Keep store DB-API only and keep psycopg optional at import time. The adapter owns connection lifecycle and uses local DSN validation. JSON dict/list params must be adapted through psycopg `Jsonb` only inside the psycopg adapter.

- [x] **Step 3: Verify focused tests**

Run:
`pytest tests/test_team_research_assignment_store.py tests/test_team_research_assignment_config.py tests/test_team_research_assignment_psycopg.py tests/test_team_research_assignment_schema.py -q`
Expected: pass.

### Task 3: Assignment History Pure Reducer

**Files:**
- Create: `src/polymarket_alpha_lab/team_research_assignment_history.py`
- Create: `src/polymarket_alpha_lab/team_research_assignment_history_cli_format.py`
- Create: `tests/test_team_research_assignment_history.py`
- Create: `tests/test_team_research_assignment_history_cli_format.py`

**Interfaces:**
- Consumes: tuple/list of `TeamResearchAssignmentReport`.
- Produces:
  - `TeamResearchAssignmentHistoryConfig`
  - `TeamResearchAssignmentHistoryStatusRow`
  - `TeamResearchAssignmentHistoryReport`
  - `build_team_research_assignment_history_report`
  - `format_team_research_assignment_history_cli_stdout`

- [x] **Step 1: Write failing history reducer and formatter tests**

Tests must prove:
- empty history is blocked with `insufficient_history`
- fewer than `min_report_count` reports is blocked
- duplicate latest `generated_at` is blocked
- enough reports with latest assignment status `ready` yields `observed`
- status rows count `ready`, `watch`, and `blocked`
- latest counts and deltas are included:
  - `latest_assignment_status`
  - `latest_assignment_count`
  - `latest_assigned_count`
  - `latest_watch_count`
  - `latest_blocked_count`
  - `assignment_count_delta`
  - `assigned_count_delta`
  - `watch_count_delta`
  - `blocked_count_delta`
- output includes hard flags and does not print market questions or slugs

Run:
`pytest tests/test_team_research_assignment_history.py tests/test_team_research_assignment_history_cli_format.py -q`
Expected: fail with missing modules.

- [x] **Step 2: Implement pure reducer and formatter**

Follow the style of `team_diagnostics_snapshot_history.py` and existing formatter modules. Do not add rankings, recommendations, trade sizing, or live actions.

- [x] **Step 3: Verify focused tests**

Run:
`pytest tests/test_team_research_assignment_history.py tests/test_team_research_assignment_history_cli_format.py -q`
Expected: pass.

### Task 4: CLI Wiring And Docs

**Files:**
- Modify: `src/polymarket_alpha_lab/cli.py`
- Modify: `tests/test_cli_team_research_assignment.py`
- Create: `tests/test_cli_team_research_assignment_history.py`
- Modify: `README.md`
- Modify: `docs/team-research-assignment.md`
- Modify: `.superpowers/sdd/progress.md`

**Interfaces:**
- Consumes Tasks 1, 2, and 3.
- Produces:
  - optional DB sink in `team-research-assignment` using env-only assignment DB config
  - new CLI command `team-research-assignment-history`

- [x] **Step 1: Write failing CLI tests**

Tests must prove:
- `team-research-assignment` writes the generated report to DB when the assignment DB env is enabled
- disabled assignment DB env does not write and does not connect
- DB write errors redact DSN/table/market/question/payload/hash/secrets/order-like fields
- no `--dsn`, `--table`, `--persist`, live/auth/wallet/order/trade/execute/submit option is accepted
- `team-research-assignment-history` reads assignment reports from env-only local Supabase/Postgres config
- history read errors redact DSN/table and sensitive values

Run:
`pytest tests/test_cli_team_research_assignment.py tests/test_cli_team_research_assignment_history.py -q`
Expected: fail until CLI wiring exists.

- [x] **Step 2: Implement CLI wiring**

Add env-only persistence and readback. Do not change the existing queue/route/snapshot source env rules. Do not expose DSN/table/persist flags.

- [x] **Step 3: Update docs**

Document env vars, table name, Phase 1 boundary, sample commands, and the difference between current assignment generation and persisted history.

- [x] **Step 4: Verify node**

Run focused tests, adjacent tests, full suite, compileall, `git diff --check`, secret scan, and `codegraph sync`.

### Task 5: Claude Review, Fixes, Commit, Push

**Files:**
- Modify only files required by Critical or Important review findings.

- [ ] **Step 1: Run Claude Code review**

Run Claude Code only:
`claude -p --model claude-opus-4-8 --effort max "<review prompt>"`

- [ ] **Step 2: Fix Critical and Important findings**

Use TDD for behavior fixes. Re-run focused tests and re-review if needed.

- [ ] **Step 3: Commit and push**

Update `.superpowers/sdd/progress.md`, commit, and push to GitHub.
