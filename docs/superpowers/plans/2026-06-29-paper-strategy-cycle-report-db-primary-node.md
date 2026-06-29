# Paper Strategy Cycle Report DB-Primary Node Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add local Supabase/Postgres persistence primitives for the full `PaperStrategyCycleReport`, then wire runner and CLI optional DB sinks so `strategy-cycle` / `run` can persist complete cycle reports without treating JSONL as the only durable path.

**Architecture:** Existing `paper_recommendation_cycle_snapshot_*` storage is not a full replacement for `PaperStrategyCycleLog`: it stores a derived recommendation snapshot, not the full `PaperStrategyCycleReport` tree. This node adds a dedicated full-report DB row/store/psycopg/config family following the existing paper trade journal and NAV snapshot patterns, then adds injected sink hooks at runner/CLI boundaries. JSONL remains legacy compatibility during this node; later nodes can remove file defaults after DB sinks are available and tested.

**Tech Stack:** Python 3 dataclasses, `Decimal`, stdlib JSON, DB-API store modules, optional `psycopg`, local Supabase/Postgres DSN validation through `validate_local_postgres_dsn`, pytest.

## Global Constraints

- Durable project data must use local Supabase/Postgres only.
- Do not add SQLite, JSONL/file-backed durable substitutes, Redis, Mongo, SQLAlchemy, hosted remote DB assumptions, or a generic DB abstraction layer.
- Existing JSONL/file-backed journals are legacy compatibility surfaces; do not expand them.
- Phase 1 remains paper-only/read-only: no live trading, account auth, wallets, private keys, order signing/submission/cancellation/replacement, or exchange mutation.
- All DB DSN process boundaries must validate local-only DSNs with `polymarket_alpha_lab.supabase_local_dsn.validate_local_postgres_dsn`.
- Keep review gates read-only through local opencode using model `zhipuai-coding-plan/glm-5.2` and variant `max`.
- Codex worker subagents must use `gpt-5.5` with reasoning effort `xhigh`; fast mode is forbidden.

---

## File Structure

- Create `src/polymarket_alpha_lab/paper_strategy_cycle_report_db_row.py`: pure row codec for full `PaperStrategyCycleReport` payloads.
- Create `src/polymarket_alpha_lab/paper_strategy_cycle_report_store.py`: DB-API insert/load repository for full cycle reports.
- Create `src/polymarket_alpha_lab/paper_strategy_cycle_report_psycopg.py`: optional psycopg adapter with owned connection lifecycle.
- Create `src/polymarket_alpha_lab/supabase_paper_strategy_cycle_report_config.py`: environment config boundary for local Supabase/Postgres full cycle-report persistence.
- Modify `src/polymarket_alpha_lab/runner.py`: add optional `cycle_report_sink` callable and count persisted full cycle reports without removing existing JSONL compatibility yet.
- Modify `src/polymarket_alpha_lab/cli.py`: add optional DB sink wiring for `strategy-cycle` and `run` when `POLYMARKET_ALPHA_LAB_PAPER_STRATEGY_CYCLE_REPORT_DB_ENABLED=true`.
- Modify `src/polymarket_alpha_lab/__init__.py` only if existing export conventions require exporting new public row/config helpers; otherwise keep module-level `__all__` only.
- Add tests:
  - `tests/test_paper_strategy_cycle_report_db_row.py`
  - `tests/test_paper_strategy_cycle_report_store.py`
  - `tests/test_paper_strategy_cycle_report_psycopg.py`
  - `tests/test_supabase_paper_strategy_cycle_report_config.py`
  - Extend `tests/test_runner.py`, `tests/test_runner_scope.py`, `tests/test_cli.py`, and add/extend a CLI scope test only if imports require allow-list updates.

---

### Task 1: Full Cycle Report DB Row Codec

**Files:**
- Create: `src/polymarket_alpha_lab/paper_strategy_cycle_report_db_row.py`
- Test: `tests/test_paper_strategy_cycle_report_db_row.py`

**Interfaces:**
- Consumes: `polymarket_alpha_lab.strategy_cycle.PaperStrategyCycleReport`, `json_recovery.from_jsonable`.
- Produces:
  - `PaperStrategyCycleReportDbRow`
  - `paper_strategy_cycle_report_to_db_row(report: PaperStrategyCycleReport) -> PaperStrategyCycleReportDbRow`
  - `paper_strategy_cycle_report_from_db_row(row: PaperStrategyCycleReportDbRow) -> PaperStrategyCycleReport`

- [ ] **Step 1: Write failing row-codec tests**

Test requirements:
- A full `PaperStrategyCycleReport` with a populated `screening_report`, nested cost-aware reports, `Decimal`, and `datetime` fields round-trips through row conversion.
- A report without `screening_report` round-trips.
- `report_sha256` is deterministic for equivalent canonical payloads.
- Wrong object types and subclasses are rejected.
- `paper_only is True` and `report_only is True` are hard-enforced.
- `payload_json` must be a JSON object, must not contain floats/Decimals/raw datetimes, and must recover a compatible `PaperStrategyCycleReport`.
- Materialized columns must match `payload_json`: `report_sha256`, `generated_at`, `config_version`, `scan_market_count`, `considered_count`, `snapshot_ready_count`, `cost_aware_report_count`, `blocked_counts`, `paper_only`, `report_only`.

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:src python3 -m pytest -q tests/test_paper_strategy_cycle_report_db_row.py
```

Expected before implementation: import failure for `paper_strategy_cycle_report_db_row`.

- [ ] **Step 2: Implement row codec**

Implementation pattern:
- Mirror `paper_nav_snapshot_db_row.py` and `paper_trade_journal_db_row.py`.
- Use canonical JSON from `asdict(report)` with:
  - `Decimal` serialized to canonical string with the same no-float discipline as existing DB row codecs.
  - `datetime` serialized as UTC ISO string.
  - tuples/lists serialized as JSON arrays.
  - no Python `float`, raw `Decimal`, raw `datetime`, or non-string JSON object keys inside `payload_json`.
- Hash with `json.dumps(payload_json, allow_nan=False, separators=(",", ":"), sort_keys=True)` and SHA-256.
- Suggested row fields:
  - `report_sha256: str`
  - `generated_at: datetime`
  - `config_version: str`
  - `scan_market_count: int`
  - `considered_count: int`
  - `snapshot_ready_count: int`
  - `cost_aware_report_count: int`
  - `blocked_counts_json: list[list[object]]`, mirroring the canonical
    source shape `tuple[tuple[str, int], ...]` as JSON arrays
  - `payload_json: dict[str, object]`
  - `paper_only: bool = True`
  - `report_only: bool = True`
- Keep the exact `blocked_counts_json` shape stable and test it.

- [ ] **Step 3: Verify**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:src python3 -m pytest -q tests/test_paper_strategy_cycle_report_db_row.py tests/test_json_recovery.py tests/test_strategy_cycle.py
PYTHONDONTWRITEBYTECODE=1 python3 -m compileall -q src tests
git diff --check
```

- [ ] **Step 4: Commit**

```bash
git add src/polymarket_alpha_lab/paper_strategy_cycle_report_db_row.py tests/test_paper_strategy_cycle_report_db_row.py
git commit -m "feat: add strategy cycle report db row"
```

---

### Task 2: Full Cycle Report DB Store And Psycopg Adapter

**Files:**
- Create: `src/polymarket_alpha_lab/paper_strategy_cycle_report_store.py`
- Create: `src/polymarket_alpha_lab/paper_strategy_cycle_report_psycopg.py`
- Test: `tests/test_paper_strategy_cycle_report_store.py`
- Test: `tests/test_paper_strategy_cycle_report_psycopg.py`

**Interfaces:**
- Consumes Task 1:
  - `PaperStrategyCycleReportDbRow`
  - `paper_strategy_cycle_report_to_db_row`
  - `paper_strategy_cycle_report_from_db_row`
- Produces:
  - `insert_paper_strategy_cycle_report(connection, report, *, table_name="paper_strategy_cycle_reports") -> PaperStrategyCycleReportDbRow`
  - `load_paper_strategy_cycle_reports(connection, *, config_version: str | None = None, limit: int | None = None, table_name="paper_strategy_cycle_reports") -> tuple[PaperStrategyCycleReport, ...]`
  - `insert_paper_strategy_cycle_report_with_psycopg(dsn, report, *, table_name="paper_strategy_cycle_reports")`
  - `load_paper_strategy_cycle_reports_with_psycopg(dsn, *, config_version=None, limit=None, table_name="paper_strategy_cycle_reports")`

- [ ] **Step 1: Write failing store and adapter tests**

Store tests:
- `insert_paper_strategy_cycle_report` emits a parameterized `INSERT INTO {table_name}` with `ON CONFLICT (report_sha256) DO NOTHING`.
- `load_paper_strategy_cycle_reports` emits a parameterized `SELECT`, supports optional `config_version` and positive `limit`, orders by `generated_at DESC, inserted_at DESC, report_sha256 DESC`, and maps dict/tuple/namedtuple rows through the DB row codec.
- Invalid table names and invalid limits are rejected before cursor work.

Psycopg tests:
- Adapter owns commit/rollback/close and wraps JSON params with `Jsonb`.
- Missing psycopg raises a clean optional-extra message without leaking DSN.
- Connect failure raises a clean redacted message.
- Insert/load pass `table_name`, `config_version`, and `limit` to store functions.

- [ ] **Step 2: Implement store**

Use the same DB-API style as `paper_trade_journal_store.py`:
- `_IDENTIFIER_PATTERN = re.compile(r"^[a-z][a-z0-9_]*[a-z0-9]$")`
- `_DEFAULT_TABLE_NAME = "paper_strategy_cycle_reports"`
- `_SELECT_COLUMNS` must match row constructor order.
- No SQLAlchemy or generic abstraction.
- All table names validated before interpolation.

- [ ] **Step 3: Implement psycopg adapter**

Use the same owned-connection and JSONB adaptation pattern as `paper_nav_snapshot_psycopg.py`.

- [ ] **Step 4: Verify**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:src python3 -m pytest -q tests/test_paper_strategy_cycle_report_db_row.py tests/test_paper_strategy_cycle_report_store.py tests/test_paper_strategy_cycle_report_psycopg.py tests/test_psycopg_adapter_cleanup.py
PYTHONDONTWRITEBYTECODE=1 python3 -m compileall -q src tests
git diff --check
```

- [ ] **Step 5: Commit**

```bash
git add src/polymarket_alpha_lab/paper_strategy_cycle_report_store.py src/polymarket_alpha_lab/paper_strategy_cycle_report_psycopg.py tests/test_paper_strategy_cycle_report_store.py tests/test_paper_strategy_cycle_report_psycopg.py
git commit -m "feat: add strategy cycle report db store"
```

---

### Task 3: Local Supabase Config Boundary

**Files:**
- Create: `src/polymarket_alpha_lab/supabase_paper_strategy_cycle_report_config.py`
- Test: `tests/test_supabase_paper_strategy_cycle_report_config.py`

**Interfaces:**
- Produces:
  - `PAPER_STRATEGY_CYCLE_REPORT_DB_ENABLED_ENV_VAR = "POLYMARKET_ALPHA_LAB_PAPER_STRATEGY_CYCLE_REPORT_DB_ENABLED"`
  - `PAPER_STRATEGY_CYCLE_REPORT_DB_DSN_ENV_VAR = "POLYMARKET_ALPHA_LAB_PAPER_STRATEGY_CYCLE_REPORT_DB_DSN"`
  - `PAPER_STRATEGY_CYCLE_REPORT_DB_TABLE_ENV_VAR = "POLYMARKET_ALPHA_LAB_PAPER_STRATEGY_CYCLE_REPORT_DB_TABLE"`
  - `DEFAULT_PAPER_STRATEGY_CYCLE_REPORT_DB_TABLE = "paper_strategy_cycle_reports"`
  - `SupabasePaperStrategyCycleReportConfig`
  - `from_paper_strategy_cycle_report_db_env(env: Mapping[str, str] | None = None)`

- [ ] **Step 1: Write failing config tests**

Test requirements:
- Disabled env returns `enabled=False`, `dsn=None`, default table.
- Enabled env requires a DSN.
- Local URI DSNs and Unix socket keyword DSNs are accepted.
- Remote DSNs are rejected without echoing the full DSN or credential token.
- Whitespace-padded DSNs normalize to `None` and therefore trigger the enabled-requires-DSN error when enabled.
- Invalid table names are rejected with the table env var name.
- `repr(config)` redacts DSN.
- The module scope does not import live API/auth/order modules.

- [ ] **Step 2: Implement config module**

Use the same structure as `supabase_paper_trade_journal_config.py`, but with the exact constants above and mandatory `validate_local_postgres_dsn(self.dsn, env_var_name=PAPER_STRATEGY_CYCLE_REPORT_DB_DSN_ENV_VAR)`.

- [ ] **Step 3: Verify**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:src python3 -m pytest -q tests/test_supabase_paper_strategy_cycle_report_config.py tests/test_supabase_local_dsn.py
PYTHONDONTWRITEBYTECODE=1 python3 -m compileall -q src tests
git diff --check
```

- [ ] **Step 4: Commit**

```bash
git add src/polymarket_alpha_lab/supabase_paper_strategy_cycle_report_config.py tests/test_supabase_paper_strategy_cycle_report_config.py
git commit -m "feat: add strategy cycle report db config"
```

---

### Task 4: Runner Optional Full Cycle Report Sink

**Files:**
- Modify: `src/polymarket_alpha_lab/runner.py`
- Modify: `tests/test_runner.py`
- Modify: `tests/test_runner_scope.py`

**Interfaces:**
- Consumes: none from Task 1/2/3; this task only adds a callable injection point.
- Produces:
  - New `run_strategy_loop(..., cycle_report_sink: object | None = None, ...)` keyword argument.
  - New `RunLoopSummary.cycle_reports_persisted: int = 0`.

- [ ] **Step 1: Write failing runner tests**

Add tests:
- `cycle_report_sink` receives each successfully generated `PaperStrategyCycleReport`.
- Sink failure counts as an iteration failure under `on_cycle_error="log_and_continue"`.
- Sink failure propagates under `on_cycle_error="raise"`.
- Invalid non-callable `cycle_report_sink` is rejected before client work.
- Existing `PaperStrategyCycleLog(cycle_report_log_path).append(report)` behavior remains unchanged in this node.

- [ ] **Step 2: Implement runner changes**

Implementation constraints:
- Add `cycle_reports_persisted` to `RunLoopSummary` and validate it with `_require_nonnegative_int`.
- Add `cycle_report_sink` parameter to `run_strategy_loop` and `_validate_loop_params`.
- After the existing JSONL append succeeds, call `cycle_report_sink(report)` when not `None`, then increment `cycle_reports_persisted`.
- Add a short runner docstring note that, during this transition node, the DB
  sink intentionally runs after the legacy JSONL append. A DB sink failure can
  therefore leave the compatibility JSONL row present while the DB row is
  missing; later DB-primary default work can reverse or remove that asymmetry.
- Do not import DB config or psycopg modules into `runner.py`.

- [ ] **Step 3: Update scope test narrowly**

Allow only new public parameter/name additions. Do not allow DB imports in `runner.py`.

- [ ] **Step 4: Verify**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:src python3 -m pytest -q tests/test_runner.py tests/test_runner_scope.py
PYTHONDONTWRITEBYTECODE=1 python3 -m compileall -q src tests
git diff --check
```

- [ ] **Step 5: Commit**

```bash
git add src/polymarket_alpha_lab/runner.py tests/test_runner.py tests/test_runner_scope.py
git commit -m "feat: add cycle report sink to runner"
```

---

### Task 5: CLI Optional Full Cycle Report DB Sink

**Files:**
- Modify: `src/polymarket_alpha_lab/cli.py`
- Modify: `tests/test_cli.py`
- Add or modify CLI scope tests only if needed.

**Interfaces:**
- Consumes Task 2:
  - `insert_paper_strategy_cycle_report_with_psycopg`
- Consumes Task 3:
  - `from_paper_strategy_cycle_report_db_env`
- Consumes Task 4:
  - `cycle_report_sink` runner keyword

- [ ] **Step 1: Write failing CLI tests**

Add/modify tests:
- `strategy-cycle` wires `cycle_report_sink` to local DB when `POLYMARKET_ALPHA_LAB_PAPER_STRATEGY_CYCLE_REPORT_DB_ENABLED=true`.
- `strategy-cycle` redacts DSN on sink failure.
- `run` passes `cycle_report_sink` to `run_strategy_loop` when the DB env is enabled.
- `run` redacts DSN on sink failure through loop runner error output.
- Disabled DB env keeps the new sink `None`.
- Success-path test DSNs must be local, for example `postgresql://cycle-report:secret@localhost:54322/db`.

- [ ] **Step 2: Implement CLI wiring**

Implementation constraints:
- Import config and psycopg adapter at the CLI process boundary only.
- Build a sink function that calls `insert_paper_strategy_cycle_report_with_psycopg(dsn, report, table_name=config.table_name)`.
- If config is enabled but invalid/missing DSN, fail before running strategy cycle or run loop.
- Use `_raise_redacted_db_sink_error` for DB write/sink failures. Reserve
  `_raise_redacted_db_read_error` for future read-back paths.
- Do not make JSONL defaults worse in this node; do not remove file args yet.
- Expect a CLI scope-test allow-list update for the new config/adapter imports;
  keep that allowance as narrow as the existing paper-trade and NAV DB wiring.

- [ ] **Step 3: Verify**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:src python3 -m pytest -q tests/test_cli.py tests/test_supabase_paper_strategy_cycle_report_config.py tests/test_paper_strategy_cycle_report_psycopg.py
PYTHONDONTWRITEBYTECODE=1 python3 -m compileall -q src tests
git diff --check
```

- [ ] **Step 4: Commit**

```bash
git add src/polymarket_alpha_lab/cli.py tests/test_cli.py
git commit -m "feat: wire strategy cycle report db sink"
```

---

## Cross-Task Verification

After all tasks merge:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' PYTHONPATH=.:src python3 -m pytest -q \
  tests/test_paper_strategy_cycle_report_db_row.py \
  tests/test_paper_strategy_cycle_report_store.py \
  tests/test_paper_strategy_cycle_report_psycopg.py \
  tests/test_supabase_paper_strategy_cycle_report_config.py \
  tests/test_runner.py \
  tests/test_runner_scope.py \
  tests/test_cli.py \
  tests/test_supabase_local_dsn.py
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

- Spec coverage: The plan adds full cycle report DB persistence without pretending the existing recommendation snapshot table is equivalent. It keeps Phase 1 paper-only/read-only and local Supabase-only boundaries.
- Placeholder scan: No task uses TBD/TODO/fill-later language; every task has exact file paths, constants, interfaces, tests, and commands.
- Type consistency: `cycle_report_sink` receives a `PaperStrategyCycleReport`; DB row/store/psycopg names all use `paper_strategy_cycle_report`; config env vars use `POLYMARKET_ALPHA_LAB_PAPER_STRATEGY_CYCLE_REPORT_DB_*`.
