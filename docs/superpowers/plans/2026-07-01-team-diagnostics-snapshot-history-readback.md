# Team Diagnostics Snapshot History Readback Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a Phase 1 read-only CLI path that reads persisted team diagnostics snapshots from local Supabase/Postgres and reports history deltas for long-term team memory.

**Architecture:** Reuse the existing local Supabase snapshot env config and psycopg read adapter. Keep the history reducer pure, add a small pure stdout formatter, and let the CLI compose env-gated DB readback with the reducer.

**Tech Stack:** Python dataclasses, argparse CLI, DB-API/psycopg adapter already present, local Supabase/Postgres only, pytest.

## Global Constraints

- Phase 1 only: `paper_only=True`, `report_only=True`, `readonly=True`.
- No live trading, auth, wallet/private keys, account reads, order signing/submission/cancel/replace, or exchange mutation.
- Durable project data uses local Supabase/Postgres only.
- Do not add SQLite, Redis, Mongo, SQLAlchemy, hosted DB assumptions, generic DB layers, or file-journal durable substitutes.
- CLI must not add `--dsn` or `--table` flags.
- DB config comes from env modules only.
- DB/CLI errors must redact DSNs, table names, market slugs/questions/payload details where relevant.
- All new behavior is TDD: write failing tests first, run them red, then implement.
- CodeGraph must be used before grep/find/read when locating or understanding repo code.
- Reviews use Claude Code only, model `claude-opus-4-8`, thinking/effort `max`.
- Do not use opencode for review.
- Fast mode is forbidden for main agent and subagents.
- Codex subagents use `gpt-5.5`, reasoning `xhigh`.

---

### Task 1: Pure History Formatter

**Files:**
- Create: `src/polymarket_alpha_lab/team_diagnostics_snapshot_history_cli_format.py`
- Create: `tests/test_team_diagnostics_snapshot_history_cli_format.py`

**Interfaces:**
- Consumes: `TeamDiagnosticsSnapshotHistoryReport`-like object fields: `status`, `snapshot_count`, `required_snapshot_count`, `earliest_generated_at`, `latest_generated_at`, `span_seconds`, `status_counts`, `evidence_quality_average_delta`, `memory_eligible_delta`, `settled_calibration_delta`, `duplicate_latest_generated_at`, `reason_codes`, hard flags.
- Produces: `format_team_diagnostics_snapshot_history_cli_stdout(report: object) -> str`.

- [ ] **Step 1: Write failing formatter tests**

Create tests that verify:
- output starts with `team-diagnostics-snapshot-history:`
- includes status, snapshot count, required count, span seconds, deltas, duplicate latest flag, hard flags
- includes compact `status_counts=pass:1,watch:2`
- includes `reason_codes=insufficient_history,duplicate_latest_generated_at`
- empty reason codes print `reason_codes=none`
- values are taken from real object attributes and no DB/env imports are needed

Run:

```bash
python3 -m pytest -q tests/test_team_diagnostics_snapshot_history_cli_format.py
```

Expected: FAIL because the module/function does not exist.

- [ ] **Step 2: Implement minimal formatter**

Create a pure module with no psycopg/env imports. Format one line plus trailing newline. Use `str()` for values and ISO timestamps for datetimes.

- [ ] **Step 3: Verify green**

Run:

```bash
python3 -m pytest -q tests/test_team_diagnostics_snapshot_history_cli_format.py
```

Expected: PASS.

### Task 2: DB History Source Composer

**Files:**
- Create: `src/polymarket_alpha_lab/team_diagnostics_snapshot_history_db_source.py`
- Create: `tests/test_team_diagnostics_snapshot_history_db_source.py`

**Interfaces:**
- Consumes: caller-owned loader callable returning newest-first or arbitrary persisted `TeamDiagnosticsSnapshotReport` values.
- Produces: `load_team_diagnostics_snapshot_history_report(*, load_snapshots, history_builder, config, generated_at, team_id=None, market_slug=None, forecast_id=None, config_version=None, limit=None) -> object`.

- [ ] **Step 1: Write failing source-composer tests**

Tests must assert:
- passes filter kwargs to `load_snapshots`
- reverses persisted newest-first rows into chronological order before building history
- preserves input position for duplicate timestamps
- accepts empty history and still calls builder
- rejects non-callable loader/builder and non-exact config
- does not open cursors, commit, rollback, close, or write
- requires returned report hard flags if present

Run:

```bash
python3 -m pytest -q tests/test_team_diagnostics_snapshot_history_db_source.py
```

Expected: FAIL because module/function does not exist.

- [ ] **Step 2: Implement minimal composer**

Create a pure composition module that does not import psycopg and does not manage connection lifecycle. It may import `TeamDiagnosticsSnapshotHistoryConfig` for exact type validation.

- [ ] **Step 3: Verify green**

Run:

```bash
python3 -m pytest -q tests/test_team_diagnostics_snapshot_history_db_source.py
```

Expected: PASS.

### Task 3: CLI Readback Command

**Files:**
- Modify: `src/polymarket_alpha_lab/cli.py`
- Create: `tests/test_cli_team_diagnostics_snapshot_history.py`
- Modify: `tests/test_cli_phase1_persistence_boundary.py` only if the new injected kwarg needs allowlisting.

**Interfaces:**
- Adds command: `team-diagnostics-snapshot-history`.
- Adds filters: `--team-id`, `--market-slug`, `--forecast-id`, `--config-version`, `--limit`.
- No `--dsn`, `--table`, `--live`, `--auth`, `--wallet`, `--order`, `--private-key`, or `--account`.
- Adds injectable `team_diagnostics_snapshot_history_runner` kwarg for tests.

- [ ] **Step 1: Write failing CLI tests**

Tests must assert:
- root help lists `team-diagnostics-snapshot-history`
- command help declares read-only/report-only/local Supabase/Postgres surface and excludes forbidden flags
- disabled snapshot DB fails closed before loader/client/side effects
- injected runner receives filters and prints formatter output
- runner failure redacts DSN, table, market slug, question, payload/hash details

Run:

```bash
python3 -m pytest -q tests/test_cli_team_diagnostics_snapshot_history.py
```

Expected: FAIL because command is missing.

- [ ] **Step 2: Implement CLI path**

Add a helper `_run_team_diagnostics_snapshot_history(...) -> str` that:
- validates positive `limit`
- reads `from_team_diagnostics_snapshot_db_env()`
- fails closed when disabled or missing DSN
- calls an injected runner if provided, otherwise loads snapshots with `load_team_diagnostics_snapshot_reports_from_env`
- builds `TeamDiagnosticsSnapshotHistoryReport` with `TeamDiagnosticsSnapshotHistoryConfig()`
- formats via `format_team_diagnostics_snapshot_history_cli_stdout`
- uses existing sensitive-field redaction helper and DB/table redaction for errors

- [ ] **Step 3: Verify green**

Run:

```bash
python3 -m pytest -q tests/test_cli_team_diagnostics_snapshot_history.py tests/test_cli_phase1_persistence_boundary.py
```

Expected: PASS.

### Task 4: Docs And Scope Contracts

**Files:**
- Modify: `README.md`
- Modify: `docs/team-diagnostics-readonly.md`
- Modify: `tests/test_team_diagnostics_docs.py`
- Modify: `tests/test_team_framework_scope.py` only if static team-module allowlists require it.

**Interfaces:**
- Document that `team-diagnostics-snapshot-history` reads persisted local Supabase snapshot rows and reports long-term team-memory history deltas.
- Keep all examples env-based. Do not document DSN/table flags.
- Mention Phase 1 read-only/report-only and no live trading/order path.

- [ ] **Step 1: Write or update failing docs tests**

Run:

```bash
python3 -m pytest -q tests/test_team_diagnostics_docs.py tests/test_team_framework_scope.py
```

Expected: FAIL if docs do not yet mention the new command/constraints.

- [ ] **Step 2: Update docs minimally**

Update docs to include the command, required env vars already introduced for snapshots, and sample output fields.

- [ ] **Step 3: Verify green**

Run:

```bash
python3 -m pytest -q tests/test_team_diagnostics_docs.py tests/test_team_framework_scope.py
```

Expected: PASS.

### Task 5: Integration, Review, Commit, Push

**Files:**
- Update: `.superpowers/sdd/progress.md`

**Interfaces:**
- No new durable data store beyond local Supabase/Postgres.
- No live-trading surface.

- [ ] **Step 1: Run focused tests**

Run:

```bash
python3 -m pytest -q \
  tests/test_team_diagnostics_snapshot_history.py \
  tests/test_team_diagnostics_snapshot_history_cli_format.py \
  tests/test_team_diagnostics_snapshot_history_db_source.py \
  tests/test_cli_team_diagnostics_snapshot_history.py \
  tests/test_cli_phase1_persistence_boundary.py \
  tests/test_team_diagnostics_docs.py \
  tests/test_team_framework_scope.py
```

- [ ] **Step 2: Run full verification**

Run:

```bash
python3 -m compileall -q src/polymarket_alpha_lab tests
python3 -m pytest -q
git diff --check
codegraph sync
```

- [ ] **Step 3: Secret scan staged diff**

Scan staged changes for DSNs, GitHub tokens, private keys, wallet secrets, and API keys before commit.

- [ ] **Step 4: Claude Code review**

Use Claude Code only:

```bash
claude --print --model claude-opus-4-8 --effort max
```

Prompt must include the plan, git diff, Phase 1 boundary, local Supabase-only persistence, and request Critical/Important findings. Fix all Critical/Important findings and re-review.

- [ ] **Step 5: Commit and push**

Commit with:

```bash
git commit -m "feat: add team diagnostics snapshot history readback"
git push origin main
```

Append the completed node and verification summary to `.superpowers/sdd/progress.md`.
