# Team Memory Readiness Digest Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Summarize team diagnostics snapshot history gates into a Phase 1 pass/watch/blocked digest that tells downstream paper-only research whether long-term team memory can be used.

**Architecture:** Add a pure digest reducer over `TeamMemoryReadinessDigestSource` wrappers, a pure CLI formatter, a pure DB-source composer that runs the existing snapshot-history gate loader per team and wraps each gate report with its `team_id`, and an env-only CLI command. The digest remains report-only evidence: it does not select trades, rank markets, size positions, tune strategies, fetch live data, or perform execution.

**Tech Stack:** Python dataclasses, argparse CLI, existing local Supabase/Postgres snapshot env config, pytest, Decimal-free count/status aggregation.

## Global Constraints

- Phase 1 only: `paper_only=True`, `report_only=True`, `readonly=True`.
- No live trading, auth, wallet/private keys, account reads, order signing/submission/cancel/replace, exchange mutation, recommendation ranking, trade instruction, financial advice, strategy-weight tuning, or position sizing.
- Durable project data uses local Supabase/Postgres only.
- Do not add SQLite, Redis, Mongo, SQLAlchemy, hosted DB assumptions, generic DB layers, or file-journal durable substitutes.
- CLI must not add `--dsn`, `--table`, `--persist`, live/auth/wallet/order/private-key/account flags, or any write flags.
- DB config comes from env modules only.
- DB/CLI errors must redact DSNs, table names, market slugs/questions/payload/hash details where relevant.
- All new behavior is TDD: write failing tests first, run them red, then implement.
- CodeGraph must be used before grep/find/read when locating or understanding repo code.
- Reviews use Claude Code only, model `claude-opus-4-8`, thinking/effort `max`.
- Do not use opencode for review.
- Fast mode is forbidden for main agent and subagents.
- Codex subagents use `gpt-5.5`, reasoning `xhigh`.

---

## Shared Digest Contract

Create module `src/polymarket_alpha_lab/team_memory_readiness_digest.py`.

Exports:

- `DEFAULT_TEAM_MEMORY_READINESS_DIGEST_CONFIG_VERSION = "team-memory-readiness-digest-v0"`
- `TeamMemoryReadinessDigestConfig`
- `TeamMemoryReadinessDigestSource`
- `TeamMemoryReadinessDigestSourceStatus`
- `TeamMemoryReadinessDigestReasonCodeCount`
- `TeamMemoryReadinessDigestReport`
- `build_team_memory_readiness_digest_report`

Digest statuses:

- `pass`
- `watch`
- `blocked`

Recommended next steps:

- `pass` -> `allow_team_memory_readiness_use`
- `watch` -> `throttle_team_memory_readiness_use`
- `blocked` -> `block_team_memory_readiness_use`

Reason codes:

- `team_memory_readiness_digest_passed`
- `team_memory_readiness_digest_watch_sources_present`
- `team_memory_readiness_digest_blocked_sources_present`
- `team_memory_readiness_digest_empty_sources`

Source wrapper fields:

- `team_id: str`
- `gate_report: TeamDiagnosticsSnapshotHistoryGateReport`
- hard flags default True

Source status fields:

- `team_id: str`
- `gate_status: str`
- `recommended_next_step: str`
- `source_config_version: str`
- `latest_snapshot_age_seconds: int | None`
- `source_snapshot_count: int`
- `source_required_snapshot_count: int`
- `source_status: str`
- hard flags default True

Report fields:

- `generated_at: datetime`
- `config_version: str`
- `digest_status: str`
- `recommended_next_step: str`
- `team_count: int`
- `pass_count: int`
- `watch_count: int`
- `blocked_count: int`
- `source_statuses: tuple[TeamMemoryReadinessDigestSourceStatus, ...]`
- `source_config_versions: tuple[tuple[str, str], ...]`
- `reason_code_counts: tuple[TeamMemoryReadinessDigestReasonCodeCount, ...]`
- `reason_codes: tuple[str, ...]`
- hard flags default True

Rules:

- Consume `TeamMemoryReadinessDigestSource` values; gate reports do not carry team identity.
- Reject non-exact `TeamMemoryReadinessDigestSource` inputs and non-exact `TeamDiagnosticsSnapshotHistoryGateReport` values inside `gate_report`.
- Reject non-exact digest config.
- Reject duplicate `team_id` sources.
- Treat `gate_report.config_version` as the gate version; source status `source_config_version` comes from `gate_report.source_config_version`.
- Empty sources produce `blocked` with `team_memory_readiness_digest_empty_sources`.
- `blocked` if any source gate is `blocked`.
- `watch` if no blocked sources and any source gate is `watch`.
- `pass` only if every source gate is `pass`.
- Reason code counts are deterministic and sorted by reason code.
- Direct report construction validates counts, status, next step, source config versions, reason codes, reason counts, and hard flags.

---

### Task 1: Pure Team Memory Readiness Digest Reducer

**Files:**
- Create: `src/polymarket_alpha_lab/team_memory_readiness_digest.py`
- Create: `tests/test_team_memory_readiness_digest.py`

**Interfaces:**
- Consumes: exact `TeamMemoryReadinessDigestSource` values containing exact `TeamDiagnosticsSnapshotHistoryGateReport` values.
- Produces: digest dataclasses and `build_team_memory_readiness_digest_report(sources, *, config, generated_at)`.

- [ ] **Step 1: Write failing reducer tests**

Tests must cover:
- expected exports
- all-pass sources produce pass
- any watch source produces watch
- any blocked source produces blocked
- empty sources block
- duplicate `team_id` rejects
- exact config and source type validation
- direct report constructor consistency
- hard flags on config/source/report/reason counts/source statuses
- frozen dataclasses
- no float literals and no DB/env/CLI/psycopg imports

Run:

```bash
python3 -m pytest -q tests/test_team_memory_readiness_digest.py
```

Expected: FAIL because the module does not exist.

- [ ] **Step 2: Implement minimal reducer**

Implement the shared digest contract exactly. Import only standard library modules plus `TeamDiagnosticsSnapshotHistoryGateReport` and existing team-id validation helpers if needed. Do not infer `team_id` from a gate report or its `config_version`. Do not import DB, env, CLI, psycopg, or live trading modules.

- [ ] **Step 3: Verify green**

Run:

```bash
python3 -m pytest -q tests/test_team_memory_readiness_digest.py
```

Expected: PASS.

### Task 2: Pure Digest Formatter

**Files:**
- Create: `src/polymarket_alpha_lab/team_memory_readiness_digest_cli_format.py`
- Create: `tests/test_team_memory_readiness_digest_cli_format.py`

**Interfaces:**
- Consumes: `TeamMemoryReadinessDigestReport`-like object fields from the shared contract.
- Produces: `format_team_memory_readiness_digest_cli_stdout(report: object) -> str`.

- [ ] **Step 1: Write failing formatter tests**

Tests must verify output starts with `team-memory-readiness-digest:` and includes:
- `digest_status=`
- `recommended_next_step=`
- `team_count=`
- `pass_count=`
- `watch_count=`
- `blocked_count=`
- `source_statuses=team:status:age:snapshot_count/required_count`
- `source_config_versions=team:version`
- `reason_code_counts=reason:1`
- `reason_codes=`
- hard flags
- `none` for empty/None collections
- no DB/env/network/filesystem imports except harmless stdlib typing/date support

Run:

```bash
python3 -m pytest -q tests/test_team_memory_readiness_digest_cli_format.py
```

Expected: FAIL because the module/function does not exist.

- [ ] **Step 2: Implement minimal formatter**

Pure string formatter only. No DB/env/psycopg imports. Use deterministic comma-separated rows.

- [ ] **Step 3: Verify green**

Run:

```bash
python3 -m pytest -q tests/test_team_memory_readiness_digest_cli_format.py
```

Expected: PASS.

### Task 3: Digest DB Source Composer

**Files:**
- Create: `src/polymarket_alpha_lab/team_memory_readiness_digest_db_source.py`
- Create: `tests/test_team_memory_readiness_digest_db_source.py`

**Interfaces:**
- Consumes injected per-team gate loader and injected digest builder.
- Produces: `load_team_memory_readiness_digest_report(*, team_ids, gate_loader, digest_builder, digest_config, history_config, gate_config, generated_at, config_version=None, limit=None) -> object`.

- [ ] **Step 1: Write failing source-composer tests**

Tests must assert:
- rejects empty `team_ids`
- rejects duplicate team ids
- forwards each team id to `gate_loader`
- passes `history_config`, `gate_config`, `config_version`, `limit`, and `generated_at`
- preserves team id order
- wraps each returned gate report as `TeamMemoryReadinessDigestSource(team_id=team_id, gate_report=gate_report)`
- passes the wrapped sources into `digest_builder`
- rejects non-callable loader/builder
- rejects non-exact digest/history/gate configs
- requires returned digest report hard flags
- does not import psycopg/env/CLI/store and does not open cursor/commit/rollback/close/write

Run:

```bash
python3 -m pytest -q tests/test_team_memory_readiness_digest_db_source.py
```

Expected: FAIL because the module/function does not exist.

- [ ] **Step 2: Implement minimal composer**

Pure composition only. It should call the injected gate loader once per team id, wrap each returned gate report with the requested `team_id`, then pass the tuple of sources to the digest builder. No DB/env/psycopg import.

- [ ] **Step 3: Verify green**

Run:

```bash
python3 -m pytest -q tests/test_team_memory_readiness_digest_db_source.py
```

Expected: PASS.

### Task 4: CLI Digest Command

**Files:**
- Modify: `src/polymarket_alpha_lab/cli.py`
- Create: `tests/test_cli_team_memory_readiness_digest.py`
- Modify: `tests/test_cli_phase1_persistence_boundary.py` only if needed.

**Interfaces:**
- Adds command: `team-memory-readiness-digest`.
- Adds flags only: `--team-id`, `--config-version`, `--limit`.
- `--team-id` may be repeated; if omitted, use all known team ids from `polymarket_alpha_lab.team_taxonomy.TEAM_IDS`.
- Adds injectable `team_memory_readiness_digest_runner` kwarg for tests.

- [ ] **Step 1: Write failing CLI tests**

Tests must assert:
- root help lists command
- command help declares read-only/report-only/local Supabase/Postgres surface and excludes forbidden flags
- disabled snapshot DB fails closed before runner/client/psycopg
- enabled-without-DSN fails closed before runner/client/psycopg
- non-positive limits fail before runner/client/psycopg
- injected runner receives env-derived DSN/table, team ids, exact configs, config_version, limit, and generated_at
- runner output is formatted and hides DSN/table
- runner failure redacts DSN/table/market slug/question/payload/hash
- false or missing hard flags on injected report are rejected
- default path composes per-team history gate loading through existing gate composer and digest DB-source composer

Run:

```bash
python3 -m pytest -q tests/test_cli_team_memory_readiness_digest.py
```

Expected: FAIL because the command is missing.

- [ ] **Step 2: Implement CLI path**

Add `_run_team_memory_readiness_digest(...) -> str` that:
- validates positive `limit` before env reads
- reads `from_team_diagnostics_snapshot_db_env()`
- fails closed when disabled or missing DSN
- resolves team ids from repeated `--team-id` or all known `TEAM_IDS`
- creates `TeamDiagnosticsSnapshotHistoryConfig()`, `TeamDiagnosticsSnapshotHistoryGateConfig()`, and `TeamMemoryReadinessDigestConfig()`
- if injected runner exists, calls it with `dsn`, `table_name`, `team_ids`, `config_version`, `limit`, all configs, and `generated_at`
- otherwise composes wrapped per-team gate-report sources using existing snapshot-history source and gate builder through `load_team_memory_readiness_digest_report(...)`
- validates hard flags on the digest report
- formats with `format_team_memory_readiness_digest_cli_stdout`
- uses existing sensitive-field redaction helpers

- [ ] **Step 3: Verify green**

Run:

```bash
python3 -m pytest -q tests/test_cli_team_memory_readiness_digest.py tests/test_cli_phase1_persistence_boundary.py
```

Expected: PASS.

### Task 5: Docs And Scope Contracts

**Files:**
- Modify: `README.md`
- Modify: `docs/team-diagnostics-readonly.md`
- Modify: `tests/test_team_diagnostics_docs.py`
- Modify: `tests/test_team_framework_scope.py` only if needed.

**Interfaces:**
- Document `team-memory-readiness-digest` as local Supabase/Postgres readback plus pass/watch/blocked digest over per-team `TeamMemoryReadinessDigestSource` wrappers backed by diagnostics snapshot history gate results.
- Do not document DSN/table CLI flags.
- Mention Phase 1 read-only/report-only and no live trading/order path.

- [ ] **Step 1: Write or update failing docs tests**

Run:

```bash
python3 -m pytest -q tests/test_team_diagnostics_docs.py tests/test_team_framework_scope.py
```

Expected: FAIL until docs cover the new digest command.

- [ ] **Step 2: Update docs minimally**

Include command, existing env vars, sample output fields, and digest status semantics.

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
  tests/test_team_memory_readiness_digest.py \
  tests/test_team_memory_readiness_digest_cli_format.py \
  tests/test_team_memory_readiness_digest_db_source.py \
  tests/test_cli_team_memory_readiness_digest.py \
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

Scan staged changes for real tokens, URI-form DSNs, private keys, wallet secrets, API keys, and non-local DB connection strings.

- [ ] **Step 4: Claude Code review**

Use Claude Code only:

```bash
claude --print --model claude-opus-4-8 --effort max
```

Fix all Critical/Important findings and re-review until Critical 0 and Important 0.

- [ ] **Step 5: Commit and push**

Commit with:

```bash
git commit -m "feat: add team memory readiness digest"
git push origin main
```
