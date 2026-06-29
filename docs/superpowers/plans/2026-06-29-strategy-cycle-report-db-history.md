# Strategy Cycle Report DB History Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a read-only, local Supabase/Postgres-backed history report for persisted full `PaperStrategyCycleReport` rows so the strategy engine can evaluate cycle quality from DB history instead of relying on JSONL compatibility logs.

**Architecture:** Keep the new node DB-primary and read-only. A pure reducer summarizes chronological `PaperStrategyCycleReport` objects into a frozen report with Decimal-only rates, status, and blocked-reason aggregates. A DB helper loads newest-first rows from `paper_strategy_cycle_reports`, reverses them to chronological order, and feeds the reducer. A CLI command reads from the existing `POLYMARKET_ALPHA_LAB_PAPER_STRATEGY_CYCLE_REPORT_DB_*` env config and prints a compact summary without adding DSN flags or writing files.

**Tech Stack:** Python frozen dataclasses, `Decimal`, existing `paper_strategy_cycle_report_store` / `paper_strategy_cycle_report_psycopg`, local Supabase/Postgres DSN config, pytest.

## Global Constraints

- Durable project data must use local Supabase/Postgres only.
- Do not add SQLite, JSONL/file-backed durable substitutes, Redis, Mongo, SQLAlchemy, hosted remote DB assumptions, or a generic DB abstraction layer.
- Existing JSONL/file-backed journals are legacy compatibility surfaces; do not expand them.
- Phase 1 remains paper-only/read-only: no live trading, account auth, wallets, private keys, order signing/submission/cancellation/replacement, or exchange mutation.
- All DB DSN process boundaries must validate local-only DSNs with `polymarket_alpha_lab.supabase_local_dsn.validate_local_postgres_dsn`.
- This node reads the existing `paper_strategy_cycle_reports` table; it must not create a second table for derived history output.
- CLI configuration must remain env-only; do not add DB DSN/table command-line flags.
- Review gates are read-only through local opencode using model `zhipuai-coding-plan/glm-5.2` and variant `max`.
- Codex worker subagents must use `gpt-5.5` with reasoning effort `xhigh`; fast mode is forbidden.

---

## Parallel Execution Shape

- **Wave 1, parallel-safe:** Task 1 pure reducer can be implemented while a read-only explorer prepares Task 3 CLI line locations and tests. A docs worker may draft runbook wording after Task 1 interfaces are accepted.
- **Wave 2:** Task 2 DB loader depends on Task 1 public types.
- **Wave 3:** Task 3 CLI command depends on Task 1 and Task 2.
- **Wave 4:** Full verification, opencode review, CodeGraph sync, secret scan, push.

## File Structure

- Create `src/polymarket_alpha_lab/paper_strategy_cycle_report_history.py`: pure reducer and frozen dataclasses for strategy-cycle DB history.
- Create `tests/test_paper_strategy_cycle_report_history.py`: reducer tests, validation tests, scope tests.
- Create `src/polymarket_alpha_lab/paper_strategy_cycle_report_db_history.py`: read-only DB-API loader from `paper_strategy_cycle_reports`.
- Create `tests/test_paper_strategy_cycle_report_db_history.py`: loader delegation, newest-first reversal, empty history, safety flags, scope tests.
- Modify `src/polymarket_alpha_lab/cli.py`: add `strategy-cycle-db-history` command, injected runner, summary printing, and read error redaction.
- Modify `tests/test_cli.py`: CLI env, injected runner, default load path, redaction, and no-DSN-flag coverage.
- Add `docs/paper-strategy-cycle-report-db-history.md`: short runbook for env config and command usage.

---

### Task 1: Pure Strategy Cycle Report History Reducer

**Files:**
- Create: `src/polymarket_alpha_lab/paper_strategy_cycle_report_history.py`
- Test: `tests/test_paper_strategy_cycle_report_history.py`

**Interfaces:**
- Consumes: `polymarket_alpha_lab.strategy_cycle.PaperStrategyCycleReport`
- Produces:
  - `DEFAULT_PAPER_STRATEGY_CYCLE_REPORT_HISTORY_CONFIG_VERSION = "paper-strategy-cycle-report-history-v0"`
  - `PaperStrategyCycleReportHistoryConfig`
  - `PaperStrategyCycleReportHistoryBlockedReasonRow`
  - `PaperStrategyCycleReportHistoryReport`
  - `build_paper_strategy_cycle_report_history_report(reports, *, config, generated_at)`

- [ ] **Step 1: Write failing reducer tests**

Test requirements:
- A chronological tuple of three `PaperStrategyCycleReport` values produces a `pass` report when `report_count >= min_report_count`, latest snapshot-ready share meets the threshold, and blocked-market share is under the configured cap.
- The reducer aggregates `blocked_counts` by reason code across all reports into sorted `PaperStrategyCycleReportHistoryBlockedReasonRow` rows.
- `blocked` status is returned with reason code `insufficient_strategy_cycle_report_history` when `report_count < min_report_count`.
- `blocked` status is returned with reason code `latest_snapshot_ready_share_below_minimum` when latest `snapshot_ready_count / considered_count` is below `min_latest_snapshot_ready_share`.
- `watch` status is returned with reason code `blocked_market_share_above_limit` when aggregate blocked-market share exceeds `max_blocked_market_share` but no blocked rule fired.
- Empty input, subclasses, unsafe `paper_only`/`report_only`, floats, non-finite Decimals, and noncanonical config versions are rejected.
- The report and nested rows are frozen, normalize datetimes to UTC, quantize rates to `Decimal("0.000001")`, and expose `paper_only=True`, `report_only=True`, `readonly=True`.

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:src python3 -m pytest -q tests/test_paper_strategy_cycle_report_history.py
```

Expected before implementation: import failure for `paper_strategy_cycle_report_history`.

- [ ] **Step 2: Implement reducer dataclasses**

Implement these exact shapes:

```python
@dataclass(frozen=True)
class PaperStrategyCycleReportHistoryConfig:
    config_version: str = DEFAULT_PAPER_STRATEGY_CYCLE_REPORT_HISTORY_CONFIG_VERSION
    min_report_count: int = 3
    min_latest_snapshot_ready_share: Decimal = Decimal("0.100000")
    max_blocked_market_share: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


@dataclass(frozen=True)
class PaperStrategyCycleReportHistoryBlockedReasonRow:
    reason_code: str
    blocked_market_count: int
    report_count: int


@dataclass(frozen=True)
class PaperStrategyCycleReportHistoryReport:
    generated_at: datetime
    config_version: str
    history_status: str
    report_count: int
    first_report_generated_at: datetime
    latest_report_generated_at: datetime
    total_scan_market_count: int
    total_considered_count: int
    total_snapshot_ready_count: int
    total_cost_aware_report_count: int
    total_blocked_market_count: int
    latest_scan_market_count: int
    latest_considered_count: int
    latest_snapshot_ready_count: int
    latest_cost_aware_report_count: int
    latest_blocked_market_count: int
    overall_snapshot_ready_share: Decimal
    latest_snapshot_ready_share: Decimal
    blocked_market_share: Decimal
    blocked_reason_rows: tuple[PaperStrategyCycleReportHistoryBlockedReasonRow, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
```

Reducer rules:
- Require `type(config) is PaperStrategyCycleReportHistoryConfig`.
- Require every report is exactly `PaperStrategyCycleReport`, not a subclass.
- Require every source report has `paper_only is True` and `report_only is True`.
- Compute rates as `Decimal(numerator) / Decimal(denominator)` quantized to `Decimal("0.000001")`; return `Decimal("0.000000")` when denominator is zero.
- Status priority:
  - `blocked` if `report_count < config.min_report_count`, reason `insufficient_strategy_cycle_report_history`.
  - `blocked` if `latest_snapshot_ready_share < config.min_latest_snapshot_ready_share`, reason `latest_snapshot_ready_share_below_minimum`.
  - `watch` if `blocked_market_share > config.max_blocked_market_share`, reason `blocked_market_share_above_limit`.
  - otherwise `pass`, reason_codes `()`.

- [ ] **Step 3: Verify**

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:src python3 -m pytest -q tests/test_paper_strategy_cycle_report_history.py
PYTHONDONTWRITEBYTECODE=1 python3 -m compileall -q src tests
git diff --check
```

- [ ] **Step 4: Commit**

```bash
git add src/polymarket_alpha_lab/paper_strategy_cycle_report_history.py tests/test_paper_strategy_cycle_report_history.py
git commit -m "feat: add strategy cycle report history reducer"
```

---

### Task 2: DB Loader For Strategy Cycle Report History

**Files:**
- Create: `src/polymarket_alpha_lab/paper_strategy_cycle_report_db_history.py`
- Test: `tests/test_paper_strategy_cycle_report_db_history.py`

**Interfaces:**
- Consumes:
  - `PaperStrategyCycleReportHistoryConfig`
  - `build_paper_strategy_cycle_report_history_report`
  - `paper_strategy_cycle_report_store.load_paper_strategy_cycle_reports`
- Produces:
  - `load_paper_strategy_cycle_report_history_report(*, generated_at, config, connection, source_config_version=None, limit=None, table_name="paper_strategy_cycle_reports")`

- [ ] **Step 1: Write failing DB loader tests**

Test requirements:
- Loader passes `connection`, `source_config_version`, `limit`, and `table_name` to `load_paper_strategy_cycle_reports`.
- Store returns newest-first reports; loader reverses them before reducer so `first_report_generated_at` and `latest_report_generated_at` are chronological.
- Empty store result raises `ValueError("no paper strategy cycle reports found")`.
- Unsafe loaded report flags (`paper_only=False` or `report_only=False`) are rejected by the reducer path.
- Module scope imports no live driver/network modules: `psycopg`, `requests`, `httpx`, `aiohttp`, `socket`, `urllib`, `websocket`, `websockets`, `eth_account`.

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:src python3 -m pytest -q tests/test_paper_strategy_cycle_report_db_history.py
```

Expected before implementation: import failure for `paper_strategy_cycle_report_db_history`.

- [ ] **Step 2: Implement loader**

Implementation:

```python
def load_paper_strategy_cycle_report_history_report(
    *,
    generated_at: datetime,
    config: PaperStrategyCycleReportHistoryConfig,
    connection: Any,
    source_config_version: str | None = None,
    limit: int | None = None,
    table_name: str = "paper_strategy_cycle_reports",
) -> PaperStrategyCycleReportHistoryReport:
    reports = paper_strategy_cycle_report_store.load_paper_strategy_cycle_reports(
        connection,
        config_version=source_config_version,
        limit=limit,
        table_name=table_name,
    )
    if not reports:
        raise ValueError("no paper strategy cycle reports found")
    return build_paper_strategy_cycle_report_history_report(
        tuple(reversed(reports)),
        config=config,
        generated_at=generated_at,
    )
```

- [ ] **Step 3: Verify**

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:src python3 -m pytest -q tests/test_paper_strategy_cycle_report_db_history.py tests/test_paper_strategy_cycle_report_history.py tests/test_paper_strategy_cycle_report_store.py
PYTHONDONTWRITEBYTECODE=1 python3 -m compileall -q src tests
git diff --check
```

- [ ] **Step 4: Commit**

```bash
git add src/polymarket_alpha_lab/paper_strategy_cycle_report_db_history.py tests/test_paper_strategy_cycle_report_db_history.py
git commit -m "feat: add strategy cycle report db history loader"
```

---

### Task 3: CLI Command For DB History

**Files:**
- Modify: `src/polymarket_alpha_lab/cli.py`
- Modify: `tests/test_cli.py`

**Interfaces:**
- Consumes:
  - `PaperStrategyCycleReportHistoryConfig`
  - `build_paper_strategy_cycle_report_history_report`
  - `load_paper_strategy_cycle_reports_with_psycopg`
  - `from_paper_strategy_cycle_report_db_env`
- Produces:
  - CLI command `strategy-cycle-db-history`
  - Injectable `strategy_cycle_report_db_history_runner: Callable[..., object] | None`

- [ ] **Step 1: Write failing CLI tests**

Test requirements:
- Command fails before work when `POLYMARKET_ALPHA_LAB_PAPER_STRATEGY_CYCLE_REPORT_DB_ENABLED` is not true.
- Command fails before work when enabled but DSN is missing.
- Injected runner receives `dsn`, `generated_at`, `config`, `source_config_version`, `limit`, and `table_name`.
- Default load path uses `load_paper_strategy_cycle_reports_with_psycopg`, reverses newest-first reports, builds the history report, and prints `strategy-cycle-db-history: status=... reports=... latest_snapshot_ready_share=... blocked_market_share=...`.
- Runner/load failures redact the DSN and table name using a new local helper.
- The parser adds no DB DSN/table command-line flags. Allowed args are `--source-config-version` and `--limit`.

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:src python3 -m pytest -q tests/test_cli.py -k "strategy_cycle_db_history"
```

Expected before implementation: unknown command or missing injection failures.

- [ ] **Step 2: Implement CLI wiring**

Implementation constraints:
- Add imports for `PaperStrategyCycleReportHistoryConfig`, `build_paper_strategy_cycle_report_history_report`, and `load_paper_strategy_cycle_reports_with_psycopg`.
- Add `StrategyCycleReportDbHistoryRunner = Callable[..., object]`.
- Add optional `strategy_cycle_report_db_history_runner` keyword to `main()`.
- Add parser:

```python
strategy_cycle_db_history = subparsers.add_parser("strategy-cycle-db-history")
strategy_cycle_db_history.add_argument("--source-config-version", default=None)
strategy_cycle_db_history.add_argument("--limit", type=int, default=50)
```

- Reject `limit < 1` or bool with `ValueError("strategy-cycle-db-history limit must be positive")`.
- Use `from_paper_strategy_cycle_report_db_env()` and require `enabled` and non-`None` `dsn`.
- If injected runner is provided, call it with `dsn`, `generated_at=datetime.now(UTC)`, `config=PaperStrategyCycleReportHistoryConfig()`, `source_config_version`, `limit`, `table_name`.
- Default path loads with `load_paper_strategy_cycle_reports_with_psycopg(dsn, config_version=source_config_version, limit=limit, table_name=table_name)`, rejects empty history, and builds from `tuple(reversed(reports))`.
- Add `_raise_redacted_strategy_cycle_report_db_history_error(exc, *, dsn, table_name)` that redacts both DSN and table name.
- Print with `_print_strategy_cycle_report_db_history_summary(report)`.

- [ ] **Step 3: Verify**

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:src python3 -m pytest -q tests/test_cli.py tests/test_paper_strategy_cycle_report_history.py tests/test_paper_strategy_cycle_report_db_history.py tests/test_supabase_paper_strategy_cycle_report_config.py
PYTHONDONTWRITEBYTECODE=1 python3 -m compileall -q src tests
git diff --check
```

- [ ] **Step 4: Commit**

```bash
git add src/polymarket_alpha_lab/cli.py tests/test_cli.py
git commit -m "feat: add strategy cycle db history cli"
```

---

### Task 4: DB History Runbook

**Files:**
- Create: `docs/paper-strategy-cycle-report-db-history.md`

**Interfaces:**
- Consumes: CLI command `strategy-cycle-db-history`
- Produces: Operator-facing runbook text only; no code imports.

- [ ] **Step 1: Write the doc**

Required sections:
- Purpose: read-only history summary from `paper_strategy_cycle_reports`.
- Required env vars: `POLYMARKET_ALPHA_LAB_PAPER_STRATEGY_CYCLE_REPORT_DB_ENABLED=true`, `POLYMARKET_ALPHA_LAB_PAPER_STRATEGY_CYCLE_REPORT_DB_DSN`, optional table env var.
- Example command: `polymarket-alpha-lab strategy-cycle-db-history --limit 50`.
- Safety: local Supabase/Postgres only; no live trading, wallet, auth, private keys, order submission, cancellation, replacement, or exchange mutation.
- Interpretation: `blocked` means history is too sparse or latest snapshot readiness is below threshold; `watch` means blocked-market share is high; `pass` means history is currently usable for downstream paper-only selection signals.

- [ ] **Step 2: Verify doc has no secret/live-order guidance**

```bash
rg -n -i "private key|wallet|submit order|cancel order|live trading|hosted postgres" docs/paper-strategy-cycle-report-db-history.md && exit 1 || true
git diff --check
```

- [ ] **Step 3: Commit**

```bash
git add docs/paper-strategy-cycle-report-db-history.md
git commit -m "docs: add strategy cycle db history runbook"
```

---

## Cross-Task Verification

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' PYTHONPATH=.:src python3 -m pytest -q \
  tests/test_paper_strategy_cycle_report_history.py \
  tests/test_paper_strategy_cycle_report_db_history.py \
  tests/test_paper_strategy_cycle_report_store.py \
  tests/test_paper_strategy_cycle_report_psycopg.py \
  tests/test_supabase_paper_strategy_cycle_report_config.py \
  tests/test_cli.py
PYTHONDONTWRITEBYTECODE=1 python3 -m compileall -q src tests
git diff --check
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' PYTHONPATH=.:src python3 -m pytest -q
```

Post-node review:

```bash
opencode run -m zhipuai-coding-plan/glm-5.2 --variant max --dir /home/ubuntu/polymarket-alpha-lab "<read-only review prompt>"
```

Push gate:

```bash
codegraph sync
git grep -n -E '(ghp_[A-Za-z0-9]{36,}|github_pat_[A-Za-z0-9_]{20,}|sk-proj-[A-Za-z0-9_-]{20,}|sk-live-[A-Za-z0-9_-]{20,}|-----BEGIN (RSA |OPENSSH |EC |DSA |)PRIVATE KEY-----)' HEAD || true
git push origin main
```

## Self-Review

- Spec coverage: The plan adds read-only DB history on top of the full cycle report table, keeps local Supabase/Postgres as the only durable source, and does not add live-trading or mutation surfaces.
- Placeholder scan: No TBD/TODO/fill-later placeholders remain; each task has exact files, interfaces, test commands, and commit commands.
- Type consistency: The reducer, DB loader, and CLI all use `PaperStrategyCycleReportHistoryConfig` and `PaperStrategyCycleReportHistoryReport`; the CLI reads from the existing `paper_strategy_cycle_reports` table via existing env config.
