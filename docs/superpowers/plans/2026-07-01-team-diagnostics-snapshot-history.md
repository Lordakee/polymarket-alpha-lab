# Team Diagnostics Snapshot History Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Persist compact team diagnostics snapshots and expose snapshot history/trends from local Supabase/Postgres so specialist teams accumulate durable operational memory.

**Architecture:** Keep diagnostics computation pure, then add a DB row/store/psycopg/env boundary that writes only internal report artifacts. CLI integration remains read-only against Polymarket/exchange surfaces and writes only local diagnostics snapshot records when the snapshot DB env is enabled.

**Tech Stack:** Python frozen dataclasses, Decimal-safe JSON helpers, DB-API store layer, psycopg adapter layer, local Supabase/Postgres migrations, pytest, CodeGraph.

## Global Constraints

- All reviews use Claude Code only, model `claude-opus-4-8`, thinking/effort `max`; do not use opencode.
- Fast mode is forbidden for main agent and subagents.
- Codex subagents use `gpt-5.5`, reasoning `xhigh`.
- Phase 1 boundary is strict: paper-only/report-only/readonly; no live trading, no auth, no wallet/private keys, no account reads, no order signing/submission/cancel/replace, no exchange mutation.
- Durable project data must use local Supabase/Postgres only; no new SQLite, Redis, Mongo, SQLAlchemy, or file-journal durable substitutes.
- CodeGraph must be used before grep/find/read when locating or understanding code because `.codegraph/` exists.
- TDD is required: write focused failing tests before production code.
- CLI must not add `--dsn` or `--table` flags; DB configuration comes from env modules.
- DB errors surfaced by CLI must redact DSNs and table names.
- Snapshot persistence is an internal local DB artifact; it does not change the exchange boundary.

---

### Task 1: Pure Snapshot Reducer

**Files:**
- Create: `src/polymarket_alpha_lab/team_diagnostics_snapshot.py`
- Test: `tests/test_team_diagnostics_snapshot.py`

**Interfaces:**
- Consumes: `TeamDiagnosticsBundleReport` from `team_diagnostics_bundle.py`.
- Produces:
  - `DEFAULT_TEAM_DIAGNOSTICS_SNAPSHOT_CONFIG_VERSION: str`
  - `TeamDiagnosticsSnapshotConfig`
  - `TeamDiagnosticsSnapshotReport`
  - `build_team_diagnostics_snapshot_report(bundle_report, *, config, team_id=None, market_slug=None, forecast_id=None) -> TeamDiagnosticsSnapshotReport`

- [ ] Write failing tests for frozen dataclasses, UTC normalization, hard flags, filter validation, and a representative bundle-to-snapshot reduction.
- [ ] Run: `python3 -m pytest tests/test_team_diagnostics_snapshot.py -q`; expected failure is missing module/symbols.
- [ ] Implement the pure reducer with no DB/env/psycopg/file/network imports.
- [ ] Include compact fields: generated_at, config_version, source_config_version, filters, forecast/evidence/outcome counts, memory eligible count, calibration status/settled/group counts, event template row count/status, source reliability row/missing-source counts, evidence quality status/pass/watch/blocked/average quality, reason_codes.
- [ ] Run: `python3 -m pytest tests/test_team_diagnostics_snapshot.py -q`; expected pass.

### Task 2: Snapshot DB Row and DB-API Store

**Files:**
- Create: `src/polymarket_alpha_lab/team_diagnostics_snapshot_db_row.py`
- Create: `src/polymarket_alpha_lab/team_diagnostics_snapshot_store.py`
- Test: `tests/test_team_diagnostics_snapshot_db_row.py`
- Test: `tests/test_team_diagnostics_snapshot_store.py`

**Interfaces:**
- Consumes: `TeamDiagnosticsSnapshotReport` from Task 1.
- Produces:
  - `TeamDiagnosticsSnapshotDbRow`
  - `team_diagnostics_snapshot_report_to_db_row(report) -> TeamDiagnosticsSnapshotDbRow`
  - `team_diagnostics_snapshot_report_from_db_row(row) -> TeamDiagnosticsSnapshotReport`
  - `TeamDiagnosticsSnapshotInsertResult`
  - `insert_team_diagnostics_snapshot_report(connection, report, *, table_name=...)`
  - `insert_team_diagnostics_snapshot_report_with_result(connection, report, *, table_name=...)`
  - `load_team_diagnostics_snapshot_reports(connection, *, team_id=None, market_slug=None, forecast_id=None, config_version=None, limit=None, table_name=...)`

- [ ] Write failing DB row tests for payload hash round-trip, JSON immutability, hard-flag validation, and value-changing payload rejection.
- [ ] Write failing store tests with fake DB-API connection/cursor for insert, conflict no-op, filtered load, limit validation, and table-name validation.
- [ ] Run focused tests; expected failure is missing modules/symbols.
- [ ] Implement conversion/store using safe lowercase identifier table validation, `ON CONFLICT (report_sha256) DO NOTHING`, and `ORDER BY generated_at DESC, inserted_at DESC, report_sha256 DESC`.
- [ ] Keep psycopg imports out of the store.
- [ ] Run focused tests; expected pass.

### Task 3: Snapshot Supabase Config and psycopg Adapter

**Files:**
- Create: `src/polymarket_alpha_lab/supabase_team_diagnostics_snapshot_config.py`
- Create: `src/polymarket_alpha_lab/team_diagnostics_snapshot_psycopg.py`
- Test: `tests/test_team_diagnostics_snapshot_config.py`
- Test: `tests/test_team_diagnostics_snapshot_psycopg.py`

**Interfaces:**
- Consumes: Task 2 store functions.
- Produces:
  - Env vars: `POLYMARKET_ALPHA_LAB_TEAM_DIAGNOSTICS_SNAPSHOT_DB_ENABLED`, `_DSN`, `_TABLE`
  - Default table: `team_diagnostics_snapshots`
  - `SupabaseTeamDiagnosticsSnapshotConfig`
  - `from_team_diagnostics_snapshot_db_env(env=None)`
  - `insert_team_diagnostics_snapshot_report_from_env(report)`
  - `load_team_diagnostics_snapshot_reports_from_env(...)`

- [ ] Write failing config tests for disabled default, enabled-without-DSN failure, local DSN validation, table validation, and repr DSN redaction.
- [ ] Write failing psycopg tests by stubbing connector/store calls so disabled config does not connect and enabled config validates DSN before connection.
- [ ] Run focused tests; expected failure is missing modules/symbols.
- [ ] Implement env and psycopg wrappers, preserving caller-owned redaction and local Supabase/Postgres-only DSN validation.
- [ ] Run focused tests; expected pass.

### Task 4: Snapshot History Reducer

**Files:**
- Create: `src/polymarket_alpha_lab/team_diagnostics_snapshot_history.py`
- Test: `tests/test_team_diagnostics_snapshot_history.py`

**Interfaces:**
- Consumes: `TeamDiagnosticsSnapshotReport`.
- Produces:
  - `TeamDiagnosticsSnapshotHistoryConfig`
  - `TeamDiagnosticsSnapshotHistoryReport`
  - `build_team_diagnostics_snapshot_history_report(snapshots, *, config, generated_at) -> TeamDiagnosticsSnapshotHistoryReport`

- [ ] Write failing tests for insufficient history, status counts, latest snapshot, span seconds, evidence quality delta, memory eligible delta, settled calibration delta, and duplicate latest generated_at detection.
- [ ] Run focused tests; expected failure is missing module/symbols.
- [ ] Implement pure history reducer with no DB/env/psycopg imports.
- [ ] Run focused tests; expected pass.

### Task 5: Migration and Docs

**Files:**
- Create: migration SQL in the repository's existing migration directory using the next timestamped filename.
- Modify: `docs/team-diagnostics-readonly.md`
- Modify: `README.md`
- Modify: `.env.example` if present.
- Test: add or update docs/migration contract tests if the repo has existing migration/docs test patterns.

**Interfaces:**
- Consumes: Task 2 selected DB columns and Task 3 env names.
- Produces: local Supabase/Postgres table `team_diagnostics_snapshots`.

- [ ] Locate existing migration/docs patterns with CodeGraph or repo file listing.
- [ ] Write failing migration/docs contract tests if existing tests cover migration/env docs.
- [ ] Add table with report hash, generated/filter fields, source counts, compact diagnostic fields, reason code JSONB, payload JSONB, `inserted_at`, and indexes for team/filter/history reads.
- [ ] Document local Supabase setup and clarify this is internal report persistence, not live trading.
- [ ] Run focused tests or docs contract checks.

### Task 6: CLI Integration

**Files:**
- Modify: `src/polymarket_alpha_lab/cli.py`
- Test: `tests/test_cli_team_diagnostics_snapshot.py`
- Add tests to existing CLI scope tests if needed.

**Interfaces:**
- Consumes: Tasks 1-4.
- Produces:
  - Command: `team-diagnostics-snapshot`
  - Filters: `--team-id`, `--market-slug`, `--forecast-id`, `--limit`
  - Optional readback/history flag only if simple and DB-backed; no `--dsn`, `--table`, live/auth/wallet/order/private-key/account flags.

- [ ] Write failing CLI tests for disabled snapshot DB fail-closed behavior, successful snapshot persistence with injected/stubbed rows and sink, redacted DB write failures, and help text scope.
- [ ] Run focused CLI tests; expected failure is missing command.
- [ ] Implement command by reusing the existing team diagnostics row loader and bundle builder, then building/persisting the snapshot through the snapshot env adapter.
- [ ] Format compact stdout with report hash/status/counts so automation can inspect a one-shot run.
- [ ] Run focused CLI tests; expected pass.

### Task 7: Integration, Review, Push

**Files:**
- Update: `src/polymarket_alpha_lab/__init__.py` only for public exports that tests require.
- Update: `.superpowers/sdd/progress.md`.

- [ ] Run focused tests for all new modules.
- [ ] Run: `python3 -m compileall -q src/polymarket_alpha_lab tests`.
- [ ] Run: `python3 -m pytest -q`.
- [ ] Run: `git diff --check`.
- [ ] Run: `codegraph sync`.
- [ ] Run secret scan over staged diff.
- [ ] Request Claude Code review only with model `claude-opus-4-8` and thinking `max`.
- [ ] Fix Critical/Important review findings and re-review until clean or only accepted Minor findings remain.
- [ ] Commit and push to `origin/main`.
- [ ] Write final handoff summary with repo status, verified commands, uncommitted files, and next step.
