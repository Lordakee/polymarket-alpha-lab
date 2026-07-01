# Team Diagnostics Snapshot History Gate Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert persisted team diagnostics snapshot history into a Phase 1 pass/watch/blocked gate that decides whether a team's long-term memory is safe to use for downstream paper recommendations.

**Architecture:** Add a pure gate reducer over `TeamDiagnosticsSnapshotHistoryReport`, a pure CLI formatter, a pure DB-source composer that combines snapshot-history readback with the gate reducer, and an env-only CLI command that reads local Supabase/Postgres snapshots and prints the gate summary.

**Tech Stack:** Python dataclasses, Decimal-only thresholds, argparse CLI, existing local Supabase/Postgres snapshot env config, pytest.

## Global Constraints

- Phase 1 only: `paper_only=True`, `report_only=True`, `readonly=True`.
- No live trading, auth, wallet/private keys, account reads, order signing/submission/cancel/replace, or exchange mutation.
- Durable project data uses local Supabase/Postgres only.
- Do not add SQLite, Redis, Mongo, SQLAlchemy, hosted DB assumptions, generic DB layers, or file-journal durable substitutes.
- CLI must not add `--dsn` or `--table` flags.
- DB config comes from env modules only.
- DB/CLI errors must redact DSNs, table names, market slugs/questions/payload/hash details where relevant.
- All new behavior is TDD: write failing tests first, run them red, then implement.
- CodeGraph must be used before grep/find/read when locating or understanding repo code.
- Reviews use Claude Code only, model `claude-opus-4-8`, thinking/effort `max`.
- Do not use opencode for review.
- Fast mode is forbidden for main agent and subagents.
- Codex subagents use `gpt-5.5`, reasoning `xhigh`.

---

## Shared Gate Contract

Create module `src/polymarket_alpha_lab/team_diagnostics_snapshot_history_gate.py`.

Exports:

- `DEFAULT_TEAM_DIAGNOSTICS_SNAPSHOT_HISTORY_GATE_CONFIG_VERSION = "team-diagnostics-snapshot-history-gate-v0"`
- `TeamDiagnosticsSnapshotHistoryGateConfig`
- `TeamDiagnosticsSnapshotHistoryGateReasonCodeCount`
- `TeamDiagnosticsSnapshotHistoryGateReport`
- `build_team_diagnostics_snapshot_history_gate_report`

Gate statuses:

- `pass`
- `watch`
- `blocked`

Recommended next steps:

- `pass` -> `allow_team_diagnostics_snapshot_history_memory_use`
- `watch` -> `throttle_team_diagnostics_snapshot_history_memory_use`
- `blocked` -> `block_team_diagnostics_snapshot_history_memory_use`

Reason codes:

- Pass: `team_diagnostics_snapshot_history_gate_passed`
- Blocked:
  - `insufficient_team_diagnostics_snapshot_history_samples`
  - `stale_team_diagnostics_snapshot_history`
  - `duplicate_latest_team_diagnostics_snapshot_history_generated_at`
- Watch:
  - `team_diagnostics_snapshot_history_evidence_quality_deteriorated`
  - `team_diagnostics_snapshot_history_memory_coverage_deteriorated`
  - `team_diagnostics_snapshot_history_settled_calibration_deteriorated`
  - `team_diagnostics_snapshot_history_source_reason_codes_present`

Default config values:

- `min_source_snapshot_count: int = 3`
- `max_latest_snapshot_age_seconds: int = 86_400`
- `min_evidence_quality_average_delta: Decimal = Decimal("-0.050000")`
- `min_memory_eligible_delta: int = 0`
- `min_settled_calibration_delta: int = 0`
- hard flags default True

Report fields:

- `generated_at: datetime`
- `config_version: str`
- `source_config_version: str`
- `source_generated_at: datetime | None`
- `latest_snapshot_age_seconds: int | None`
- `gate_status: str`
- `recommended_next_step: str`
- `reason_code_counts: tuple[TeamDiagnosticsSnapshotHistoryGateReasonCodeCount, ...]`
- `source_snapshot_count: int`
- `source_required_snapshot_count: int`
- `source_status: str`
- `source_span_seconds: int`
- `source_status_counts: tuple[tuple[str, int], ...]`
- `source_reason_codes: tuple[str, ...]`
- `evidence_quality_average_delta: Decimal`
- `memory_eligible_delta: int`
- `settled_calibration_delta: int`
- `duplicate_latest_generated_at: bool`
- `reason_codes: tuple[str, ...]`
- hard flags default True

Rules:

- Reject non-exact `TeamDiagnosticsSnapshotHistoryReport` source reports.
- Reject non-exact gate config.
- Block when source `snapshot_count < min_source_snapshot_count`.
- Block when source `status == "insufficient_history"`.
- Block when `source.latest_generated_at is None`.
- Block when latest snapshot age exceeds `max_latest_snapshot_age_seconds`.
- Block when `duplicate_latest_generated_at is True`.
- Watch when `evidence_quality_average_delta < min_evidence_quality_average_delta`.
- Watch when `memory_eligible_delta < min_memory_eligible_delta`.
- Watch when `settled_calibration_delta < min_settled_calibration_delta`.
- Watch when `source.reason_codes` is nonempty and no blocked reason has already captured the issue.
- If no reasons, use the single pass reason.
- Gate status is `blocked` if any blocked reason appears, else `watch` if any watch reason appears, else `pass`.
- Reason code counts are one count per reason code in report order.

---

### Task 1: Pure Gate Reducer

**Files:**
- Create: `src/polymarket_alpha_lab/team_diagnostics_snapshot_history_gate.py`
- Create: `tests/test_team_diagnostics_snapshot_history_gate.py`

**Interfaces:**
- Consumes: exact `TeamDiagnosticsSnapshotHistoryReport`.
- Produces: gate dataclasses and `build_team_diagnostics_snapshot_history_gate_report(source_report, *, config, generated_at)`.

- [ ] **Step 1: Write failing reducer tests**

Tests must cover:
- expected exports
- stable source passes
- insufficient history blocks
- stale/missing latest blocks
- duplicate latest generated_at blocks
- negative evidence quality / memory / settled calibration deltas watch
- source reason codes watch when not blocked
- exact config/source type validation
- hard flags on config/source/report/reason counts
- frozen dataclasses
- Decimal-only threshold validation and no float literals in module
- direct report constructor consistency validation

Run:

```bash
python3 -m pytest -q tests/test_team_diagnostics_snapshot_history_gate.py
```

Expected: FAIL because the module does not exist.

- [ ] **Step 2: Implement minimal reducer**

Implement the shared gate contract exactly. Use `Decimal("0.000001")` quantization for Decimal fields and thresholds. Do not import DB, env, CLI, psycopg, or live trading modules.

- [ ] **Step 3: Verify green**

Run:

```bash
python3 -m pytest -q tests/test_team_diagnostics_snapshot_history_gate.py
```

Expected: PASS.

### Task 2: Pure Gate Formatter

**Files:**
- Create: `src/polymarket_alpha_lab/team_diagnostics_snapshot_history_gate_cli_format.py`
- Create: `tests/test_team_diagnostics_snapshot_history_gate_cli_format.py`

**Interfaces:**
- Consumes: `TeamDiagnosticsSnapshotHistoryGateReport`-like object fields from the shared contract.
- Produces: `format_team_diagnostics_snapshot_history_gate_cli_stdout(report: object) -> str`.

- [ ] **Step 1: Write failing formatter tests**

Tests must verify output starts with `team-diagnostics-snapshot-history-gate:` and includes:
- `gate_status=`
- `recommended_next_step=`
- `source_snapshot_count=`
- `source_required_snapshot_count=`
- `source_status=`
- `latest_snapshot_age_seconds=`
- `reason_code_counts=reason:1,reason2:1`
- `evidence_quality_average_delta=`
- `memory_eligible_delta=`
- `settled_calibration_delta=`
- `duplicate_latest_generated_at=`
- `reason_codes=`
- hard flags
- `none` for empty/None reason collections
- no DB/env/network/filesystem imports

Run:

```bash
python3 -m pytest -q tests/test_team_diagnostics_snapshot_history_gate_cli_format.py
```

Expected: FAIL because the module/function does not exist.

- [ ] **Step 2: Implement minimal formatter**

Pure string formatter only. No DB/env/psycopg imports.

- [ ] **Step 3: Verify green**

Run:

```bash
python3 -m pytest -q tests/test_team_diagnostics_snapshot_history_gate_cli_format.py
```

Expected: PASS.

### Task 3: Gate DB Source Composer

**Files:**
- Create: `src/polymarket_alpha_lab/team_diagnostics_snapshot_history_gate_db_source.py`
- Create: `tests/test_team_diagnostics_snapshot_history_gate_db_source.py`

**Interfaces:**
- Consumes injected snapshot-history loader/composer and injected gate builder.
- Produces: `load_team_diagnostics_snapshot_history_gate_report(*, history_loader, gate_builder, history_config, gate_config, generated_at, team_id=None, market_slug=None, forecast_id=None, config_version=None, limit=None) -> object`.

- [ ] **Step 1: Write failing source-composer tests**

Tests must assert:
- forwards filters to `history_loader`
- passes `history_config`, `generated_at`, and `limit`
- passes returned history report into `gate_builder`
- rejects non-callable loader/builder
- rejects non-exact `TeamDiagnosticsSnapshotHistoryConfig` and `TeamDiagnosticsSnapshotHistoryGateConfig`
- requires returned gate report hard flags if present
- does not import psycopg/env/CLI/store and does not open cursor/commit/rollback/close/write

Run:

```bash
python3 -m pytest -q tests/test_team_diagnostics_snapshot_history_gate_db_source.py
```

Expected: FAIL because module/function does not exist.

- [ ] **Step 2: Implement minimal composer**

Pure composition only. It should call existing history readback/composer through injection, then gate through injection. No DB/env/psycopg import.

- [ ] **Step 3: Verify green**

Run:

```bash
python3 -m pytest -q tests/test_team_diagnostics_snapshot_history_gate_db_source.py
```

Expected: PASS.

### Task 4: CLI Gate Command

**Files:**
- Modify: `src/polymarket_alpha_lab/cli.py`
- Create: `tests/test_cli_team_diagnostics_snapshot_history_gate.py`
- Modify: `tests/test_cli_phase1_persistence_boundary.py` only if needed.

**Interfaces:**
- Adds command: `team-diagnostics-snapshot-history-gate`.
- Adds filters: `--team-id`, `--market-slug`, `--forecast-id`, `--config-version`, `--limit`.
- No `--dsn`, `--table`, `--persist`, `--live`, `--auth`, `--wallet`, `--order`, `--private-key`, or `--account`.
- Adds injectable `team_diagnostics_snapshot_history_gate_runner` kwarg for tests.

- [ ] **Step 1: Write failing CLI tests**

Tests must assert:
- root help lists command
- command help declares read-only/report-only/local Supabase/Postgres surface and excludes forbidden flags
- disabled snapshot DB fails closed before runner/client/psycopg
- enabled-without-DSN fails closed before runner/client/psycopg
- non-positive limits fail before runner/client/psycopg
- injected runner receives env-derived DSN/table and filters plus exact history/gate configs
- injected runner output is formatted and hides DSN/table
- runner failure redacts DSN/table/market slug/question/payload/hash
- false hard flags on injected report are rejected

Run:

```bash
python3 -m pytest -q tests/test_cli_team_diagnostics_snapshot_history_gate.py
```

Expected: FAIL because the command is missing.

- [ ] **Step 2: Implement CLI path**

Add `_run_team_diagnostics_snapshot_history_gate(...) -> str` that:
- validates positive `limit` before env reads
- reads `from_team_diagnostics_snapshot_db_env()`
- fails closed when disabled or missing DSN
- creates `TeamDiagnosticsSnapshotHistoryConfig()` and `TeamDiagnosticsSnapshotHistoryGateConfig()`
- if injected runner exists, calls it with `dsn`, `table_name`, filters, `history_config`, `gate_config`, and `generated_at`
- otherwise composes `load_team_diagnostics_snapshot_history_gate_report(...)` using existing snapshot-history source and gate builder
- validates hard flags on the gate report
- formats with `format_team_diagnostics_snapshot_history_gate_cli_stdout`
- uses existing sensitive-field redaction helpers

- [ ] **Step 3: Verify green**

Run:

```bash
python3 -m pytest -q tests/test_cli_team_diagnostics_snapshot_history_gate.py tests/test_cli_phase1_persistence_boundary.py
```

Expected: PASS.

### Task 5: Docs And Scope Contracts

**Files:**
- Modify: `README.md`
- Modify: `docs/team-diagnostics-readonly.md`
- Modify: `tests/test_team_diagnostics_docs.py`
- Modify: `tests/test_team_framework_scope.py` only if needed.

**Interfaces:**
- Document `team-diagnostics-snapshot-history-gate` as local Supabase/Postgres readback plus pass/watch/blocked gate over persisted diagnostics snapshot history.
- Do not document DSN/table CLI flags.
- Mention Phase 1 read-only/report-only and no live trading/order path.

- [ ] **Step 1: Write or update failing docs tests**

Run:

```bash
python3 -m pytest -q tests/test_team_diagnostics_docs.py tests/test_team_framework_scope.py
```

Expected: FAIL until docs cover the new gate command.

- [ ] **Step 2: Update docs minimally**

Include command, existing env vars, sample output fields, and gate status semantics.

- [ ] **Step 3: Verify green**

Run:

```bash
python3 -m pytest -q tests/test_team_diagnostics_docs.py tests/test_team_framework_scope.py
```

Expected: PASS.

### Task 6: Integration, Review, Commit, Push

**Files:**
- Update local `.superpowers/sdd/progress.md` after commit.

- [ ] **Step 1: Run focused tests**

Run:

```bash
python3 -m pytest -q \
  tests/test_team_diagnostics_snapshot_history_gate.py \
  tests/test_team_diagnostics_snapshot_history_gate_cli_format.py \
  tests/test_team_diagnostics_snapshot_history_gate_db_source.py \
  tests/test_cli_team_diagnostics_snapshot_history_gate.py \
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

Scan staged changes for real tokens, URI-form DSNs, private keys, wallet secrets, and API keys.

- [ ] **Step 4: Claude Code review**

Use Claude Code only:

```bash
claude --print --model claude-opus-4-8 --effort max
```

Fix all Critical/Important findings and re-review until Critical 0 and Important 0.

- [ ] **Step 5: Commit and push**

Commit with:

```bash
git commit -m "feat: add team diagnostics snapshot history gate"
git push origin main
```
