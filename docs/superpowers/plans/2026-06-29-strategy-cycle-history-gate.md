# Strategy Cycle History Gate Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a paper-only gate over local Supabase-backed strategy cycle report history so autonomous recommendation stages can block or throttle when scan quality is not healthy enough.

**Architecture:** Keep the gate pure first: consume `PaperStrategyCycleReportHistoryReport`, classify it as pass/watch/blocked, and expose deterministic reason codes plus source metadata. Persist the gate as a separate local Supabase/Postgres artifact only behind an explicit CLI persistence flag, reusing existing DB row/store/psycopg/config patterns. Do not change existing persisted readiness or screening dataclasses in this node; downstream integration can consume this gate as an additive source in a later node.

**Tech Stack:** Python frozen dataclasses, `Decimal`, existing `paper_strategy_cycle_report_history` and `paper_strategy_cycle_report_db_history`, local Supabase/Postgres via psycopg, pytest.

## Global Constraints

- Durable project data must use local Supabase/Postgres only.
- Do not add SQLite, JSONL/file-backed durable substitutes, Redis, Mongo, SQLAlchemy, hosted remote DB assumptions, or a generic DB abstraction layer.
- Existing JSONL/file-backed journals are legacy compatibility surfaces; do not expand them.
- Phase 1 remains paper-only/read-only for market and trading behavior: no live trading, account auth, wallets, private keys, order signing/submission/cancellation/replacement, or exchange mutation.
- Gate persistence may write only the new paper gate report to local Supabase/Postgres when an explicit CLI `--persist` flag is present.
- All DB DSN process boundaries must validate local-only DSNs with `polymarket_alpha_lab.supabase_local_dsn.validate_local_postgres_dsn`.
- CLI configuration must remain env-only; do not add DB DSN/table command-line flags.
- Review gates are read-only through local opencode using model `zhipuai-coding-plan/glm-5.2` and variant `max`.
- Codex worker subagents must use `gpt-5.5` with reasoning effort `xhigh`; fast mode is forbidden.

---

## Parallel Execution Shape

- **Wave 1, parallel-safe:** Task 1 pure gate reducer, Task 2 persistence design/tests, and Task 4 docs can be worked on in separate worktrees. Task 3 CLI can start after Task 1 interfaces are stable.
- **Wave 2:** Integrate Task 2 persistence and Task 3 CLI on main, resolve imports, run focused tests.
- **Wave 3:** Full verification, opencode read-only review, CodeGraph sync, secret scan, push.

## File Structure

- Create `src/polymarket_alpha_lab/paper_strategy_cycle_report_history_gate.py`: pure gate reducer and frozen dataclasses.
- Create `tests/test_paper_strategy_cycle_report_history_gate.py`: reducer behavior, validation, scope tests.
- Create `src/polymarket_alpha_lab/paper_strategy_cycle_report_history_gate_db_row.py`: row codec with canonical payload hash.
- Create `src/polymarket_alpha_lab/paper_strategy_cycle_report_history_gate_store.py`: DB-API insert/load functions.
- Create `src/polymarket_alpha_lab/paper_strategy_cycle_report_history_gate_psycopg.py`: psycopg adapter.
- Create `src/polymarket_alpha_lab/supabase_paper_strategy_cycle_report_history_gate_config.py`: env-only local Supabase config.
- Create `supabase/migrations/20260629000001_paper_strategy_cycle_report_history_gate_reports.sql`: local Postgres schema.
- Create matching tests for row/store/psycopg/config/schema.
- Modify `src/polymarket_alpha_lab/cli.py`: add `strategy-cycle-history-gate` command and optional persistence.
- Modify `tests/test_cli.py` or add focused CLI tests: command behavior, redaction, no DB flags.
- Add `docs/paper-strategy-cycle-report-history-gate.md`: runbook.

---

### Task 1: Pure Strategy Cycle History Gate Reducer

**Files:**
- Create: `src/polymarket_alpha_lab/paper_strategy_cycle_report_history_gate.py`
- Test: `tests/test_paper_strategy_cycle_report_history_gate.py`

**Interfaces:**
- Consumes: `polymarket_alpha_lab.paper_strategy_cycle_report_history.PaperStrategyCycleReportHistoryReport`
- Produces:
  - `DEFAULT_PAPER_STRATEGY_CYCLE_REPORT_HISTORY_GATE_CONFIG_VERSION = "paper-strategy-cycle-report-history-gate-v0"`
  - `PaperStrategyCycleReportHistoryGateConfig`
  - `PaperStrategyCycleReportHistoryGateReasonCodeCount`
  - `PaperStrategyCycleReportHistoryGateReport`
  - `build_paper_strategy_cycle_report_history_gate_report(history_report, *, config, generated_at)`

- [ ] **Step 1: Write failing reducer tests**

Test requirements:
- A source history report with `history_status="pass"` and a fresh `latest_report_generated_at` produces `gate_status="pass"` and reason code `paper_strategy_cycle_report_history_gate_passed`.
- `history_status="blocked"` produces `gate_status="blocked"` with `source_strategy_cycle_report_history_blocked`.
- `history_status="watch"` produces `gate_status="watch"` with `source_strategy_cycle_report_history_watch`.
- A stale latest source timestamp produces `gate_status="watch"` with `stale_strategy_cycle_report_history`.
- Missing `latest_report_generated_at` produces `gate_status="blocked"` with `missing_latest_strategy_cycle_report_history_timestamp`.
- Exact type checks reject subclasses for config, report, reason row, and source history.
- Source and result hard flags are `paper_only=True`, `report_only=True`, `readonly=True`.
- Counts and rates are copied from the source report without float conversion.

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:src python3 -m pytest -q tests/test_paper_strategy_cycle_report_history_gate.py
```

Expected before implementation: import failure for `paper_strategy_cycle_report_history_gate`.

- [ ] **Step 2: Implement reducer**

Implement these exact public shapes:

```python
@dataclass(frozen=True)
class PaperStrategyCycleReportHistoryGateConfig:
    config_version: str = DEFAULT_PAPER_STRATEGY_CYCLE_REPORT_HISTORY_GATE_CONFIG_VERSION
    max_latest_age_seconds: int = 86_400
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


@dataclass(frozen=True)
class PaperStrategyCycleReportHistoryGateReasonCodeCount:
    reason_code: str
    report_count: int
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


@dataclass(frozen=True)
class PaperStrategyCycleReportHistoryGateReport:
    generated_at: datetime
    config_version: str
    source_config_version: str
    source_generated_at: datetime
    gate_status: str
    recommended_next_step: str
    reason_code_counts: tuple[PaperStrategyCycleReportHistoryGateReasonCodeCount, ...]
    source_history_status: str
    source_report_count: int
    latest_source_generated_at: datetime | None
    latest_source_age_seconds: int | None
    latest_snapshot_ready_share: Decimal
    blocked_market_share: Decimal
    latest_snapshot_ready_count: int
    latest_considered_count: int
    total_blocked_market_count: int
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
```

Reducer rules:
- `NEXT_STEP_BY_STATUS = {"pass": "allow_strategy_cycle_history_gate", "watch": "throttle_strategy_cycle_history_gate", "blocked": "block_strategy_cycle_history_gate"}`
- Pass reason: `paper_strategy_cycle_report_history_gate_passed`
- Block reasons: `source_strategy_cycle_report_history_blocked`, `missing_latest_strategy_cycle_report_history_timestamp`
- Watch reasons: `source_strategy_cycle_report_history_watch`, `stale_strategy_cycle_report_history`
- Status priority is blocked over watch over pass.
- `latest_source_age_seconds = int((generated_at - latest_report_generated_at).total_seconds())`, reject future source timestamps.
- Reason codes are sorted unique values; reason counts are presence counts with `report_count=1`.

- [ ] **Step 3: Verify and commit**

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:src python3 -m pytest -q tests/test_paper_strategy_cycle_report_history_gate.py tests/test_paper_strategy_cycle_report_history.py
PYTHONDONTWRITEBYTECODE=1 python3 -m compileall -q src tests
git diff --check
git add src/polymarket_alpha_lab/paper_strategy_cycle_report_history_gate.py tests/test_paper_strategy_cycle_report_history_gate.py
git commit -m "feat: add strategy cycle history gate reducer"
```

---

### Task 2: Gate Persistence

**Files:**
- Create: `src/polymarket_alpha_lab/paper_strategy_cycle_report_history_gate_db_row.py`
- Create: `src/polymarket_alpha_lab/paper_strategy_cycle_report_history_gate_store.py`
- Create: `src/polymarket_alpha_lab/paper_strategy_cycle_report_history_gate_psycopg.py`
- Create: `src/polymarket_alpha_lab/supabase_paper_strategy_cycle_report_history_gate_config.py`
- Create: `supabase/migrations/20260629000001_paper_strategy_cycle_report_history_gate_reports.sql`
- Test: matching `tests/test_*` files

**Interfaces:**
- Consumes: `PaperStrategyCycleReportHistoryGateReport`
- Produces:
  - `paper_strategy_cycle_report_history_gate_report_to_db_row(report)`
  - `paper_strategy_cycle_report_history_gate_report_from_db_row(row)`
  - `insert_paper_strategy_cycle_report_history_gate_report(...)`
  - `insert_paper_strategy_cycle_report_history_gate_report_with_result(...)`
  - `load_paper_strategy_cycle_report_history_gate_reports(...)`
  - `insert_paper_strategy_cycle_report_history_gate_report_with_psycopg(...)`
  - `load_paper_strategy_cycle_report_history_gate_reports_with_psycopg(...)`
  - `from_paper_strategy_cycle_report_history_gate_db_env(...)`

- [ ] **Step 1: Write failing persistence tests**

Test requirements:
- DB row codec round-trips pass/watch/blocked reports and rejects corrupted hash, materialized field mismatches, JSON floats, false top-level flags, and wrong types.
- Store inserts with parameterized SQL only and loads newest-first by `generated_at desc, inserted_at desc, report_sha256 desc`.
- Store validates table names and rejects schema-qualified/injection table names.
- Psycopg adapter imports psycopg lazily and delegates to store functions.
- Env config uses:
  - `POLYMARKET_ALPHA_LAB_STRATEGY_CYCLE_HISTORY_GATE_DB_ENABLED`
  - `POLYMARKET_ALPHA_LAB_STRATEGY_CYCLE_HISTORY_GATE_DB_DSN`
  - `POLYMARKET_ALPHA_LAB_STRATEGY_CYCLE_HISTORY_GATE_DB_TABLE`
- Default table: `paper_strategy_cycle_report_history_gate_reports`.
- Migration creates `public.paper_strategy_cycle_report_history_gate_reports` with materialized gate fields, JSON payload, SHA primary key, hard-flag checks, and useful indexes.

- [ ] **Step 2: Implement persistence using existing local patterns**

Implementation guidance:
- Mirror the structure of `paper_autonomous_readiness_gate_db_row.py`, `paper_autonomous_readiness_gate_store.py`, `paper_autonomous_readiness_gate_psycopg.py`, and `supabase_paper_autonomous_readiness_gate_config.py`.
- Keep table names unqualified at runtime; migration owns the `public.` schema.
- Use canonical JSON payload and SHA-256 hash.
- Use `from_jsonable` for payload recovery and reject non-canonical payloads.

- [ ] **Step 3: Verify and commit**

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:src python3 -m pytest -q \
  tests/test_paper_strategy_cycle_report_history_gate.py \
  tests/test_paper_strategy_cycle_report_history_gate_db_row.py \
  tests/test_paper_strategy_cycle_report_history_gate_store.py \
  tests/test_paper_strategy_cycle_report_history_gate_psycopg.py \
  tests/test_supabase_paper_strategy_cycle_report_history_gate_config.py \
  tests/test_paper_strategy_cycle_report_history_gate_schema.py
PYTHONDONTWRITEBYTECODE=1 python3 -m compileall -q src tests
git diff --check
git add src tests supabase/migrations/20260629000001_paper_strategy_cycle_report_history_gate_reports.sql
git commit -m "feat: persist strategy cycle history gate reports"
```

---

### Task 3: CLI Command

**Files:**
- Modify: `src/polymarket_alpha_lab/cli.py`
- Test: `tests/test_cli.py` or focused `tests/test_cli_strategy_cycle_history_gate.py`

**Interfaces:**
- Consumes:
  - `from_paper_strategy_cycle_report_db_env`
  - `load_paper_strategy_cycle_reports_with_psycopg`
  - `PaperStrategyCycleReportHistoryConfig`
  - `build_paper_strategy_cycle_report_history_report`
  - `PaperStrategyCycleReportHistoryGateConfig`
  - `build_paper_strategy_cycle_report_history_gate_report`
  - optional gate DB sink from Task 2
- Produces CLI command: `strategy-cycle-history-gate`

- [ ] **Step 1: Write failing CLI tests**

Test requirements:
- Command fails before DB work when source strategy-cycle report DB env is disabled.
- Command fails before DB work when source DB is enabled but DSN is missing.
- Command accepts only `--source-config-version`, `--limit`, and `--persist`; no DSN/table flags.
- Default command reads newest-first source reports, reverses for history reduction, builds the gate, and prints:

```text
strategy-cycle-history-gate: status=<status> source_history_status=<status> reports=<count> latest_snapshot_ready_share=<rate> blocked_market_share=<rate> persisted=<true|false>
```

- `--persist` requires gate DB env enabled and gate DB DSN present.
- Source DB read failures and gate DB write failures redact DSNs and table names.

- [ ] **Step 2: Implement CLI**

Implementation guidance:
- Reuse existing `strategy-cycle-db-history` command patterns.
- Do not add source or sink DSN/table command-line flags.
- Persist only after gate report builds successfully.
- Default `persisted=False`.

- [ ] **Step 3: Verify and commit**

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:src python3 -m pytest -q tests/test_cli.py tests/test_paper_strategy_cycle_report_history_gate.py
PYTHONDONTWRITEBYTECODE=1 python3 -m compileall -q src tests
git diff --check
git add src/polymarket_alpha_lab/cli.py tests
git commit -m "feat: add strategy cycle history gate cli"
```

---

### Task 4: Documentation And Exports

**Files:**
- Modify: `src/polymarket_alpha_lab/__init__.py`
- Add: `docs/paper-strategy-cycle-report-history-gate.md`
- Test: `tests/test_init.py` and docs/scope tests if needed

**Interfaces:**
- Consumes: public reducer and persistence symbols from Tasks 1-3.
- Produces: importable public API and runbook.

- [ ] **Step 1: Write failing export/doc tests**

Test requirements:
- `polymarket_alpha_lab.__all__` exposes the pure gate reducer types and builder.
- Runbook mentions local Supabase env names and `strategy-cycle-history-gate --persist`.
- Runbook explicitly states no live trading/auth/wallet/order submission is performed.

- [ ] **Step 2: Implement docs and exports**

Add a short runbook with:
- Required source DB env.
- Optional gate DB persistence env.
- Example commands.
- Summary output format.
- Phase 1 safety boundary.

- [ ] **Step 3: Verify and commit**

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:src python3 -m pytest -q tests/test_init.py
PYTHONDONTWRITEBYTECODE=1 python3 -m compileall -q src tests
git diff --check
git add src/polymarket_alpha_lab/__init__.py docs/paper-strategy-cycle-report-history-gate.md tests
git commit -m "docs: add strategy cycle history gate runbook"
```

---

## Final Verification

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' PYTHONPATH=.:src python3 -m pytest -q
PYTHONDONTWRITEBYTECODE=1 python3 -m compileall -q src tests
git diff --check
codegraph sync
git grep -n -E '(ghp_[A-Za-z0-9]{36,}|github_pat_[A-Za-z0-9_]{20,}|sk-proj-[A-Za-z0-9_-]{20,}|sk-live-[A-Za-z0-9_-]{20,}|-----BEGIN (RSA |OPENSSH |EC |DSA |)PRIVATE KEY-----)' HEAD || true
opencode run -m zhipuai-coding-plan/glm-5.2 --variant max --dir /home/ubuntu/polymarket-alpha-lab "<read-only review prompt>"
git push origin main
```
