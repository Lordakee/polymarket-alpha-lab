# Paper Autonomous Allocation Proposal DB History Health Persistence Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Persist paper-only/report-only/readonly `PaperAutonomousAllocationProposalDbHistoryHealthReport` snapshots to local Supabase/Postgres as durable append-only audit evidence.

**Architecture:** Keep the existing health reducer and health/trend/gate loaders pure/read-only. Add a persistence boundary around already-built health reports: a deterministic DB row codec, DB-API store, optional psycopg adapter, env-only Supabase config, and SQL migration. This node does not add CLI/runtime persistence wiring; that remains a later node after the health snapshot table exists.

**Tech Stack:** Python 3.12 frozen dataclasses, `datetime.UTC`, `Decimal`, canonical JSON with SHA-256 identity, DB-API cursor connections, optional lazy `psycopg` adapter with `Jsonb`, Supabase/Postgres SQL migrations, pytest fake connections, CodeGraph, local OpenCode review using `zhipuai-coding-plan/glm-5.2 --variant max`.

## Global Constraints

- Preserve Phase 1 boundary: no live trading, no automatic live investing, no auth, no key handling, no wallet handling, no account handling, no account reads, no order instruction, no order construction, no order signing, no order submission, no order cancellation, no order replacement, no execution authorization, no approval workflow, no live-execution signal, no exchange mutation, no investment ranking, and no financial advice.
- Persisted health rows are audit evidence only. They are not approval workflow records, order intents, execution requests, strategy promotion signals, trade instructions, recommendations, rankings, or financial advice.
- This node stores only caller-supplied `PaperAutonomousAllocationProposalDbHistoryHealthReport` values. It must not read proposal tables, recompute history prefixes, run reducers, run trend/gate logic, fetch market data, read files, connect to exchange APIs, or mutate exchange state.
- The DB row codec must be pure: no `psycopg`, Supabase clients, env reads, filesystem writes, network clients, CLI imports, printing, or live/auth/order/account/wallet terms beyond negative scope tests.
- The DB-API store may open cursors and execute parameterized SQL only. It must not commit, rollback, connect, close caller-owned connections, create tables, or manage transactions.
- The psycopg adapter is the only new module that may import `psycopg`, and it must do so lazily inside functions. It owns connect/commit/rollback/close and must not leak DSNs in errors.
- All new public row/config dataclasses must preserve `paper_only=True`, `report_only=True`, and `readonly=True`, and enforce hard flags.
- Decimal values must stay `Decimal` in Python scalars, `numeric(38, 6)` in SQL scalar columns, and strings in JSON payloads. Do not introduce floats.
- Env config is default-off and env-only. There must be no CLI `--dsn`, `--table`, `--persist`, auth, wallet, account, order, trade, execute, submit, or approve surface in this node.
- Do not modify `src/polymarket_alpha_lab/cli.py` in this node. CLI/runtime wiring is a later reviewed node.
- Use `.venv/bin/python -m pytest`, not bare `pytest`.
- Use CodeGraph before grep/find/manual reads when locating code in this repo.
- Do not commit `.superpowers/`.
- Review gates for this node use local OpenCode directly, read-only, with `zhipuai-coding-plan/glm-5.2` and `--variant max`; do not route reviews to Claude Code unless the user explicitly changes AGENTS.md again.
- After implementation, run focused tests, full tests, `compileall`, `git diff --check`, strict tracked secret scan, CodeGraph sync, and post-node OpenCode review before committing and pushing.

---

## File Structure

- Create `src/polymarket_alpha_lab/paper_autonomous_allocation_proposal_db_history_health_db_row.py`
  - Pure row codec for health reports.
  - Exports only the row dataclass and conversion helpers.
- Create `src/polymarket_alpha_lab/paper_autonomous_allocation_proposal_db_history_health_store.py`
  - DB-API insert/load repository.
  - Exports table constant, insert result, insert helpers, load helper.
- Create `src/polymarket_alpha_lab/paper_autonomous_allocation_proposal_db_history_health_psycopg.py`
  - Optional psycopg adapter for insert/load with owned connection lifecycle.
- Create `src/polymarket_alpha_lab/supabase_paper_autonomous_allocation_proposal_db_history_health_config.py`
  - Default-off env config with DSN redaction and table-name validation.
- Create `supabase/migrations/20260624000001_paper_autonomous_allocation_proposal_db_history_health_reports.sql`
  - Health report table, scalar consistency checks, indexes.
- Create tests:
  - `tests/test_paper_autonomous_allocation_proposal_db_history_health_db_row.py`
  - `tests/test_paper_autonomous_allocation_proposal_db_history_health_store.py`
  - `tests/test_paper_autonomous_allocation_proposal_db_history_health_psycopg.py`
  - `tests/test_supabase_paper_autonomous_allocation_proposal_db_history_health_config.py`
  - `tests/test_paper_autonomous_allocation_proposal_db_history_health_schema.py`
  - `tests/test_paper_autonomous_allocation_proposal_db_history_health_db_scope.py`
- Modify docs/tests:
  - `README.md`
  - `docs/paper-autonomous-allocation-proposal.md`
  - `tests/test_docs_paper_autonomous_allocation_proposal_scope.py`

## Interfaces

DB row module:

```python
@dataclass(frozen=True)
class PaperAutonomousAllocationProposalDbHistoryHealthDbRow:
    report_sha256: str
    generated_at: datetime
    config_version: str
    health_status: str
    recommended_next_step: str
    history_report_count: int
    pass_report_count: int
    watch_report_count: int
    blocked_report_count: int
    latest_history_status: str | None
    latest_proposal_status: str | None
    latest_allocated_count: int | None
    latest_total_allocated_paper_notional: Decimal | None
    max_source_age_seconds: int | None
    latest_source_age_seconds: int | None
    duplicate_latest_report_generated_at_count: int
    reason_code_counts_json: list[dict[str, object]]
    reason_codes_json: list[str]
    payload_json: dict[str, object]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

def paper_autonomous_allocation_proposal_db_history_health_report_to_db_row(
    report: object,
) -> PaperAutonomousAllocationProposalDbHistoryHealthDbRow: ...

def paper_autonomous_allocation_proposal_db_history_health_report_from_db_row(
    row: PaperAutonomousAllocationProposalDbHistoryHealthDbRow,
) -> PaperAutonomousAllocationProposalDbHistoryHealthReport: ...
```

Store module:

```python
DEFAULT_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_HEALTH_REPORTS_TABLE = (
    "paper_autonomous_allocation_proposal_db_history_health_reports"
)

@dataclass(frozen=True)
class PaperAutonomousAllocationProposalDbHistoryHealthInsertResult:
    row: PaperAutonomousAllocationProposalDbHistoryHealthDbRow
    inserted: bool

def insert_paper_autonomous_allocation_proposal_db_history_health_report(
    connection: object,
    report: object,
    *,
    table_name: str = DEFAULT_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_HEALTH_REPORTS_TABLE,
) -> PaperAutonomousAllocationProposalDbHistoryHealthDbRow: ...

def insert_paper_autonomous_allocation_proposal_db_history_health_report_with_result(
    connection: object,
    report: object,
    *,
    table_name: str = DEFAULT_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_HEALTH_REPORTS_TABLE,
) -> PaperAutonomousAllocationProposalDbHistoryHealthInsertResult: ...

def load_paper_autonomous_allocation_proposal_db_history_health_reports(
    connection: object,
    *,
    config_version: str | None = None,
    health_status: str | None = None,
    latest_history_status: str | None = None,
    limit: int | None = None,
    table_name: str = DEFAULT_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_HEALTH_REPORTS_TABLE,
) -> tuple[PaperAutonomousAllocationProposalDbHistoryHealthReport, ...]: ...
```

Psycopg adapter:

```python
def insert_paper_autonomous_allocation_proposal_db_history_health_report_with_psycopg(
    dsn: str,
    report: object,
    *,
    table_name: str = DEFAULT_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_HEALTH_REPORTS_TABLE,
) -> PaperAutonomousAllocationProposalDbHistoryHealthInsertResult: ...

def load_paper_autonomous_allocation_proposal_db_history_health_reports_with_psycopg(
    dsn: str,
    *,
    config_version: str | None = None,
    health_status: str | None = None,
    latest_history_status: str | None = None,
    limit: int | None = None,
    table_name: str = DEFAULT_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_HEALTH_REPORTS_TABLE,
) -> tuple[PaperAutonomousAllocationProposalDbHistoryHealthReport, ...]: ...
```

Env config:

```python
PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_HEALTH_DB_ENABLED_ENV_VAR = (
    "POLYMARKET_ALPHA_LAB_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_HEALTH_DB_ENABLED"
)
PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_HEALTH_DB_DSN_ENV_VAR = (
    "POLYMARKET_ALPHA_LAB_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_HEALTH_DB_DSN"
)
PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_HEALTH_DB_TABLE_ENV_VAR = (
    "POLYMARKET_ALPHA_LAB_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_HEALTH_DB_TABLE"
)

@dataclass(frozen=True)
class SupabasePaperAutonomousAllocationProposalDbHistoryHealthConfig:
    enabled: bool
    dsn: str | None
    table_name: str = DEFAULT_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_HEALTH_DB_TABLE

def from_paper_autonomous_allocation_proposal_db_history_health_db_env(
    env: Mapping[str, str] | None = None,
) -> SupabasePaperAutonomousAllocationProposalDbHistoryHealthConfig: ...
```

## Parallel Development Lanes

- **Lane A, DB row codec:** Own only `paper_autonomous_allocation_proposal_db_history_health_db_row.py`, `tests/test_paper_autonomous_allocation_proposal_db_history_health_db_row.py`, and `tests/test_paper_autonomous_allocation_proposal_db_history_health_db_scope.py`.
- **Lane B, DB-API store:** Own only `paper_autonomous_allocation_proposal_db_history_health_store.py` and `tests/test_paper_autonomous_allocation_proposal_db_history_health_store.py`. Depend on Lane A names exactly.
- **Lane C, psycopg/env/schema:** Own only `paper_autonomous_allocation_proposal_db_history_health_psycopg.py`, `supabase_paper_autonomous_allocation_proposal_db_history_health_config.py`, the migration, and their focused tests.
- **Lane D, docs/scope cleanup:** Own only README/docs and docs scope tests, including the small README Phase 1 scope cleanup to mention health-trend gate artifacts.
- **Lane E, integration/review:** Own verification, CodeGraph sync, secret scan, OpenCode reviews, commit/push, and Handoff Summary. It must not edit source unless a review finding requires a focused fix.

Avoid overlapping file edits. Do not assign two agents to edit `README.md`, docs scope tests, `cli.py`, `__init__.py`, or `tests/test_init.py` concurrently. This node does not require package-root exports because DB row/store/psycopg/config helpers remain module-local.

---

### Task 1: Pure Health DB Row Codec

**Files:**
- Create: `src/polymarket_alpha_lab/paper_autonomous_allocation_proposal_db_history_health_db_row.py`
- Test: `tests/test_paper_autonomous_allocation_proposal_db_history_health_db_row.py`
- Test: `tests/test_paper_autonomous_allocation_proposal_db_history_health_db_scope.py`

**Interfaces:**
- Consumes exact `PaperAutonomousAllocationProposalDbHistoryHealthReport`.
- Produces exact `PaperAutonomousAllocationProposalDbHistoryHealthDbRow`.
- Provides deterministic conversion helpers listed above.

- [ ] **Step 1: Write failing row codec tests**

Use real `PaperAutonomousAllocationProposalDbHistoryHealthReport` fixtures from `tests/test_paper_autonomous_allocation_proposal_db_history_health.py` patterns.

Cover:
- `paper_autonomous_allocation_proposal_db_history_health_report_to_db_row(report)` requires exact report type and rejects subclasses.
- False nested or top-level hard flags are rejected.
- `report_sha256` is deterministic across repeated conversions and matches canonical JSON payload.
- `payload_json` stores datetimes as UTC ISO strings and Decimals as strings.
- No floats are accepted anywhere in `payload_json`, `reason_code_counts_json`, or row construction.
- Materialized scalar fields match payload fields on round trip.
- `reason_codes_json` equals payload `reason_codes`.
- `reason_code_counts_json` equals payload `reason_code_counts`.
- `latest_total_allocated_paper_notional` stays `Decimal | None`.
- Empty-health reports with nullable latest fields round-trip.
- Row dataclass normalizes aware datetimes to UTC and validates `report_sha256` shape, statuses, nonnegative counts, nullable nonnegative fields, JSON arrays/objects, and hard flags.

Run before implementation:

```bash
.venv/bin/python -m pytest -q tests/test_paper_autonomous_allocation_proposal_db_history_health_db_row.py
```

Expected: import failure for missing module.

- [ ] **Step 2: Implement the row codec**

Implementation rules:
- Use `dataclasses.asdict` for payload construction.
- Convert `Decimal` to string in JSON.
- Convert `datetime` to UTC ISO string in JSON.
- Reject floats recursively.
- Hash canonical JSON with `json.dumps(..., allow_nan=False, sort_keys=True, separators=(",", ":"))`.
- Recover reports with existing `json_recovery.from_jsonable`.
- Validate recovered report is exact `PaperAutonomousAllocationProposalDbHistoryHealthReport`.
- Compare all materialized fields after recovering payload.

- [ ] **Step 3: Add row module scope tests**

AST/string checks must prove the row codec has no DB/env/network/execution surfaces:
- no `psycopg`
- no `supabase`
- no `environ`
- no `requests`
- no `httpx`
- no `urllib`
- no `client`
- no `exchange`
- no `auth`
- no `wallet`
- no `account`
- no `order`
- no `trade`
- no `execute`
- no `submit`
- no `approve`
- no `commit`
- no `rollback`
- no `cursor`
- no `print`
- no `open`

Run:

```bash
.venv/bin/python -m pytest -q \
  tests/test_paper_autonomous_allocation_proposal_db_history_health_db_row.py \
  tests/test_paper_autonomous_allocation_proposal_db_history_health_db_scope.py
```

---

### Task 2: DB-API Store

**Files:**
- Create: `src/polymarket_alpha_lab/paper_autonomous_allocation_proposal_db_history_health_store.py`
- Test: `tests/test_paper_autonomous_allocation_proposal_db_history_health_store.py`

**Interfaces:**
- Consumes row codec from Task 1.
- Produces DB-API insert/load helpers listed above.

- [ ] **Step 1: Write failing store tests**

Cover:
- Insert validates table name before `connection.cursor()`.
- Insert uses parameterized SQL and `ON CONFLICT (report_sha256) DO NOTHING`.
- Insert cursor is closed in success and failure paths.
- Insert does not commit, rollback, or close the caller-owned connection.
- Insert returns `PaperAutonomousAllocationProposalDbHistoryHealthInsertResult(row, inserted=True|False)` based on `rowcount in (1, 0)` and rejects other rowcounts.
- Load validates table name and optional filters before cursor creation.
- Load supports filters `config_version`, `health_status`, `latest_history_status`, and `limit`.
- Load rejects invalid statuses and non-positive/bool limits.
- Load orders by `generated_at DESC, inserted_at DESC, report_sha256 DESC`.
- Load supports dict records, namedtuple-like records, positional rows, and already-built DB row records.

Run before implementation:

```bash
.venv/bin/python -m pytest -q tests/test_paper_autonomous_allocation_proposal_db_history_health_store.py
```

Expected: import failure for missing module.

- [ ] **Step 2: Implement the DB-API store**

Implementation rules:
- `_SELECT_COLUMNS` must not include `inserted_at`.
- Table names accept lowercase identifier with optional schema prefix; each part max 63 UTF-8 bytes.
- SQL uses `%s` placeholders only for values.
- `WHERE` clauses are assembled only from validated optional filters.
- Cursor close is best-effort in `finally`.
- No transaction lifecycle operations.

Run:

```bash
.venv/bin/python -m pytest -q \
  tests/test_paper_autonomous_allocation_proposal_db_history_health_db_row.py \
  tests/test_paper_autonomous_allocation_proposal_db_history_health_store.py
```

---

### Task 3: Psycopg Adapter, Env Config, And Migration

**Files:**
- Create: `src/polymarket_alpha_lab/paper_autonomous_allocation_proposal_db_history_health_psycopg.py`
- Create: `src/polymarket_alpha_lab/supabase_paper_autonomous_allocation_proposal_db_history_health_config.py`
- Create: `supabase/migrations/20260624000001_paper_autonomous_allocation_proposal_db_history_health_reports.sql`
- Test: `tests/test_paper_autonomous_allocation_proposal_db_history_health_psycopg.py`
- Test: `tests/test_supabase_paper_autonomous_allocation_proposal_db_history_health_config.py`
- Test: `tests/test_paper_autonomous_allocation_proposal_db_history_health_schema.py`

**Interfaces:**
- Consumes store helpers from Task 2.
- Produces optional psycopg insert/load helpers and default-off env config.

- [ ] **Step 1: Write failing env config tests**

Cover:
- Disabled by default.
- Enabled requires DSN.
- Padded/blank DSN normalizes to disabled missing DSN and does not echo the DSN.
- Accepted enabled values are exactly `""`, `"0"`, `"false"`, `"1"`, `"true"` after stripping/lowercasing.
- Invalid enabled values are rejected.
- Default table is `paper_autonomous_allocation_proposal_db_history_health_reports`.
- Lowercase optional schema-prefix table names are accepted.
- Unsafe table names are rejected with env-var-specific errors.
- `repr(config)` redacts DSN.

- [ ] **Step 2: Write failing psycopg adapter tests**

Cover:
- Importing the module does not import `psycopg`.
- Missing `psycopg` raises an install-extra message and does not include DSN.
- Connect failure raises a redacted connection message and does not include DSN.
- Successful insert/load commits and closes once.
- Failure during store call rolls back and closes once.
- Dict/list params are wrapped with `psycopg.types.json.Jsonb`.
- The adapter delegates exact `table_name`, filters, and reports to store helpers.

- [ ] **Step 3: Write failing migration tests**

Cover the migration text includes:
- `create table if not exists public.paper_autonomous_allocation_proposal_db_history_health_reports`
- `report_sha256 text primary key`
- `health_status text not null`
- `recommended_next_step text not null`
- `latest_total_allocated_paper_notional numeric(38, 6)`
- `reason_code_counts_json jsonb not null`
- `reason_codes_json jsonb not null`
- `payload_json jsonb not null`
- hard flag columns and true checks
- status/next-step pairing check
- count consistency check `history_report_count = pass_report_count + watch_report_count + blocked_report_count`
- payload/scalar consistency checks
- indexes for generated_at, health_status, config_version, latest_history_status, and GIN JSON columns
- no `private_key`, `wallet`, `account`, `order`, `trade`, `execute`, `submit`, `approve`, `cancel`, or `live_trading` tokens.

- [ ] **Step 4: Implement env config, adapter, and migration**

Adapter follows `paper_autonomous_allocation_proposal_psycopg.py`:
- `_with_owned_connection(dsn, operation)`
- `_connect(dsn)` with lazy import.
- `_jsonb_adapter()` with lazy import.
- `_PsycopgJsonConnection` and `_PsycopgJsonCursor` wrappers.
- Commit on success; rollback on `BaseException`; close in `finally`.

Migration must use SQL checks that allow nullable latest fields for empty histories and enforce nonnegative nullable latest fields when present.

Run:

```bash
.venv/bin/python -m pytest -q \
  tests/test_paper_autonomous_allocation_proposal_db_history_health_psycopg.py \
  tests/test_supabase_paper_autonomous_allocation_proposal_db_history_health_config.py \
  tests/test_paper_autonomous_allocation_proposal_db_history_health_schema.py
```

---

### Task 4: Documentation And Scope Updates

**Files:**
- Modify: `README.md`
- Modify: `docs/paper-autonomous-allocation-proposal.md`
- Modify: `tests/test_docs_paper_autonomous_allocation_proposal_scope.py`

**Interfaces:**
- Documents only; no package-root exports in this node.

- [ ] **Step 1: Write failing docs tests**

Update docs scope tests to require:
- README Phase 1 scope mentions DB-history health-trend gate artifacts.
- README allocation section documents local DB persistence for DB-history health reports.
- `docs/paper-autonomous-allocation-proposal.md` has a `DB History Health Persistence` section after `DB History Health` and before `DB History Health Trend`.
- Docs state the persisted health rows are paper-only/report-only/readonly audit evidence only.
- Docs state persistence is default-off and env-driven.
- Docs state no live trading/auth/key/wallet/account/order/exchange mutation, no approval workflow, no investment ranking, no financial advice.
- Docs do not include sample DSNs, private keys, wallet addresses, account IDs, or order payloads.

- [ ] **Step 2: Update README and allocation proposal docs**

Add a concise section:

```markdown
DB History Health Persistence:

Optional local Supabase/Postgres persistence for DB-history health reports is
available as a default-off, env-driven audit foundation. It stores canonical
payload JSON plus aggregate health scalars for already-built
PaperAutonomousAllocationProposalDbHistoryHealthReport values.

Persisted health rows remain paper-only/report-only/readonly audit evidence.
They are not approval workflow records, live-execution signals, investment
rankings, trade recommendations, order intents, account actions, wallet
interactions, or financial advice.
```

Run:

```bash
.venv/bin/python -m pytest -q tests/test_docs_paper_autonomous_allocation_proposal_scope.py
```

---

### Task 5: Integration Verification And Review

**Files:**
- No new source ownership unless prior tasks need focused fixes.

- [ ] **Step 1: Run focused persistence tests**

```bash
.venv/bin/python -m pytest -q \
  tests/test_paper_autonomous_allocation_proposal_db_history_health_db_row.py \
  tests/test_paper_autonomous_allocation_proposal_db_history_health_db_scope.py \
  tests/test_paper_autonomous_allocation_proposal_db_history_health_store.py \
  tests/test_paper_autonomous_allocation_proposal_db_history_health_psycopg.py \
  tests/test_supabase_paper_autonomous_allocation_proposal_db_history_health_config.py \
  tests/test_paper_autonomous_allocation_proposal_db_history_health_schema.py \
  tests/test_docs_paper_autonomous_allocation_proposal_scope.py
```

- [ ] **Step 2: Run full verification gates**

```bash
.venv/bin/python -m pytest -q
.venv/bin/python -m compileall src/polymarket_alpha_lab
git diff --check
git grep -n -I -E '(ghp_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,}|sk-[A-Za-z0-9_-]{32,}|AKIA[0-9A-Z]{16}|PRIVATE KEY|BEGIN RSA|BEGIN OPENSSH|POLYMARKET_.*(KEY|SECRET|TOKEN)|SUPABASE_.*(KEY|SECRET|TOKEN))' -- ':!docs/superpowers/plans/*.md' || test $? -eq 1
codegraph sync .
```

- [ ] **Step 3: Run post-node OpenCode review**

Use:

```bash
opencode run -m zhipuai-coding-plan/glm-5.2 --variant max <review-package>
```

Review package must include:
- this plan
- staged diff/stat
- verification command results
- explicit Phase 1 boundary checklist
- note that no CLI/runtime persistence wiring was added in this node.

- [ ] **Step 4: Commit, push, and handoff**

If all gates pass:

```bash
git add README.md docs src tests supabase
git commit -m "Add allocation proposal DB history health persistence"
git push origin main
```

Final handoff must include repo status, branch, HEAD/origin SHA, verification commands/results, OpenCode approval, uncommitted files, and next recommended node.

---

## Self-Review

- Spec coverage: The plan adds durable local DB persistence for health snapshots, which advances the user's database-first requirement without live execution or approval semantics.
- Scope check: CLI/runtime wiring and persisted trend/gate readers are intentionally out of scope to keep this node focused and parallel-safe.
- Placeholder scan: No TBD/TODO/fill-in-later placeholders remain.
- Type consistency: Function, class, env var, table, and test names consistently use `paper_autonomous_allocation_proposal_db_history_health`.
- Phase boundary: The plan contains no live/auth/key/wallet/account/order/execution behavior and adds explicit negative-scope tests for those tokens.
