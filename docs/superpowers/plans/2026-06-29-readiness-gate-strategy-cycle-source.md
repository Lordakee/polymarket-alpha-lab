# Readiness Gate Strategy Cycle Source Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the paper strategy-cycle report history gate as an optional fourth source in the paper autonomous readiness gate so scan/history quality can throttle or block downstream autonomous readiness.

**Architecture:** Keep the readiness gate pure and backward-compatible: existing three-source callers continue to produce the current report shape, while callers that pass a `PaperStrategyCycleReportHistoryGateReport` get a four-source readiness report. Persistence remains local Supabase/Postgres only; the existing readiness table is relaxed by a migration to accept either the legacy three-source sequence or the new four-source sequence.

**Tech Stack:** Python frozen dataclasses, existing readiness gate reducer/row/store/psycopg/config patterns, JSONB local Supabase/Postgres migrations, pytest.

## Global Constraints

- Durable project data must use local Supabase/Postgres only.
- Do not add SQLite, JSONL/file-backed durable substitutes, Redis, Mongo, SQLAlchemy, hosted remote DB assumptions, or a generic DB abstraction layer.
- Existing JSONL/file-backed journals are legacy compatibility surfaces; do not expand them.
- Phase 1 remains paper-only/read-only for market and trading behavior: no live trading, account auth, wallets, private keys, order signing/submission/cancellation/replacement, or exchange mutation.
- This node does not add a live readiness builder, broker adapter, wallet flow, order flow, or trade execution path.
- CLI/env changes, if any, must remain env-only for DB access; do not add DSN/table command-line flags.
- Review gates are read-only through local opencode using model `zhipuai-coding-plan/glm-5.2` and variant `max`.
- Codex worker subagents must use `gpt-5.5` with reasoning effort `xhigh`; fast mode is forbidden.

---

## Parallel Execution Shape

- **Wave 1, parallel-safe:** Task 1 pure reducer/source model, Task 2 schema tests/migration, and Task 4 docs/scope tests can start in separate write scopes.
- **Wave 2:** Task 3 store/row compatibility lands after Task 1 interface is committed.
- **Wave 3:** Focused integration tests, opencode read-only review, CodeGraph sync, secret scan, push.

## File Structure

- Modify `src/polymarket_alpha_lab/paper_autonomous_readiness_gate.py`: optional strategy-cycle history gate source.
- Modify `tests/test_paper_autonomous_readiness_gate.py`: pure reducer coverage for three-source compatibility and four-source behavior.
- Modify `tests/test_paper_autonomous_readiness_gate_db_row.py`: row codec round-trip for four-source payloads.
- Modify `src/polymarket_alpha_lab/paper_autonomous_readiness_gate_store.py`: optional strategy-cycle source config filter.
- Modify `tests/test_paper_autonomous_readiness_gate_store.py`: parameterized filter coverage and unsafe filter validation.
- Add `supabase/migrations/20260629000002_paper_autonomous_readiness_gate_strategy_cycle_source.sql`: relax existing local readiness table checks and add four-source sort index.
- Modify `tests/test_paper_autonomous_readiness_gate_schema.py`: effective migration coverage for three-or-four source lengths.
- Modify `docs/paper-autonomous-readiness-gate.md`: document the optional fourth source and Phase 1 boundary.
- Modify `tests/test_init.py` only if export tests need source-constant allowlist updates; do not export new constants from package root.

---

### Task 1: Pure Readiness Gate Fourth Source

**Files:**
- Modify: `src/polymarket_alpha_lab/paper_autonomous_readiness_gate.py`
- Test: `tests/test_paper_autonomous_readiness_gate.py`

**Interfaces:**
- Consumes: `polymarket_alpha_lab.paper_strategy_cycle_report_history_gate.PaperStrategyCycleReportHistoryGateReport`
- Produces:
  - module constant `STRATEGY_CYCLE_HISTORY_GATE_SOURCE_NAME = "strategy_cycle_report_history_gate"` (module-level only, not package-root export)
  - backward-compatible builder signature:

```python
def build_paper_autonomous_readiness_gate_report(
    screening_report: object,
    allocation_report: object,
    investment_ledger_report: object,
    *,
    config: PaperAutonomousReadinessGateConfig,
    generated_at: datetime,
    strategy_cycle_history_gate_report: object | None = None,
) -> PaperAutonomousReadinessGateReport:
    ...
```

- New canonical source sequences:

```python
LEGACY_SOURCE_NAMES = (
    SCREENING_SOURCE_NAME,
    ALLOCATION_SOURCE_NAME,
    INVESTMENT_LEDGER_SOURCE_NAME,
)

SOURCE_NAMES = (
    SCREENING_SOURCE_NAME,
    STRATEGY_CYCLE_HISTORY_GATE_SOURCE_NAME,
    ALLOCATION_SOURCE_NAME,
    INVESTMENT_LEDGER_SOURCE_NAME,
)
```

- `PaperAutonomousReadinessGateReport` direct validation must accept exactly `LEGACY_SOURCE_NAMES` or `SOURCE_NAMES`, no other ordering.

- [ ] **Step 1: Write failing reducer tests**

Add tests with these exact behaviors:

```python
def test_readiness_gate_keeps_legacy_three_source_behavior_without_strategy_cycle_gate():
    report = _readiness_report()
    assert tuple(row.source_name for row in report.source_statuses) == (
        "screening_decision_support_gate_db_history_health",
        "allocation_proposal_db_history_health_trend_gate",
        "investment_ledger_db_history_health_trend_gate",
    )
    assert "strategy_cycle_report_history_gate_pass" not in report.reason_codes
```

```python
def test_readiness_gate_includes_strategy_cycle_history_gate_as_fourth_source():
    report = _readiness_report(
        strategy_cycle_history_gate_report=_strategy_cycle_history_gate_report(),
    )
    assert tuple(row.source_name for row in report.source_statuses) == (
        "screening_decision_support_gate_db_history_health",
        "strategy_cycle_report_history_gate",
        "allocation_proposal_db_history_health_trend_gate",
        "investment_ledger_db_history_health_trend_gate",
    )
    assert report.reason_codes == (
        "allocation_proposal_db_history_health_trend_gate_pass",
        "investment_ledger_db_history_health_trend_gate_pass",
        "paper_autonomous_readiness_gate_passed",
        "screening_decision_support_gate_db_history_health_pass",
        "strategy_cycle_report_history_gate_pass",
    )
```

```python
def test_readiness_gate_strategy_cycle_watch_throttles_and_blocked_blocks():
    watch_report = _readiness_report(
        strategy_cycle_history_gate_report=_strategy_cycle_history_gate_report(
            gate_status="watch",
        ),
    )
    assert watch_report.readiness_status == "watch"
    assert "strategy_cycle_report_history_gate_watch" in watch_report.reason_codes

    blocked_report = _readiness_report(
        strategy_cycle_history_gate_report=_strategy_cycle_history_gate_report(
            gate_status="blocked",
        ),
    )
    assert blocked_report.readiness_status == "blocked"
    assert "strategy_cycle_report_history_gate_blocked" in blocked_report.reason_codes
```

Also add direct constructor validation tests:

```python
with pytest.raises(ValueError, match="strategy_cycle_history_gate_report must be a"):
    api.build_paper_autonomous_readiness_gate_report(
        _screening_report(),
        _allocation_report(),
        _ledger_report(),
        config=api.PaperAutonomousReadinessGateConfig(),
        generated_at=GENERATED_AT,
        strategy_cycle_history_gate_report=object(),
    )
```

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:src python3 -m pytest -q tests/test_paper_autonomous_readiness_gate.py
```

Expected before implementation: failures for missing `_strategy_cycle_history_gate_report` helper or unsupported keyword/source sequence.

- [ ] **Step 2: Implement the pure reducer**

Implementation details:
- Import `PaperStrategyCycleReportHistoryGateReport`.
- Add `STRATEGY_CYCLE_HISTORY_GATE_SOURCE_NAME`.
- Keep `SOURCE_NAMES` as the four-source canonical sequence and add `LEGACY_SOURCE_NAMES`.
- In `_normalize_source_statuses()` and `_normalize_source_config_versions()`, accept only `LEGACY_SOURCE_NAMES` or `SOURCE_NAMES`.
- In the builder, validate `strategy_cycle_history_gate_report` only when it is not `None`.
- Convert strategy-cycle gate status with:

```python
PaperAutonomousReadinessGateSourceStatus(
    source_name=STRATEGY_CYCLE_HISTORY_GATE_SOURCE_NAME,
    status=strategy_cycle_history_gate_report.gate_status,
    recommended_next_step=strategy_cycle_history_gate_report.recommended_next_step,
    generated_at=strategy_cycle_history_gate_report.generated_at,
    config_version=strategy_cycle_history_gate_report.config_version,
)
```

- Preserve hard-flag validation for all source reports.
- Do not add DB access, env reads, CLI parsing, live execution, order logic, wallet logic, or credentials.

- [ ] **Step 3: Verify and commit**

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:src python3 -m pytest -q tests/test_paper_autonomous_readiness_gate.py
PYTHONDONTWRITEBYTECODE=1 python3 -m compileall -q src tests
git diff --check
git add src/polymarket_alpha_lab/paper_autonomous_readiness_gate.py tests/test_paper_autonomous_readiness_gate.py
git commit -m "feat: add strategy cycle source to readiness gate"
```

---

### Task 2: Readiness Gate Schema Compatibility

**Files:**
- Add: `supabase/migrations/20260629000002_paper_autonomous_readiness_gate_strategy_cycle_source.sql`
- Modify: `tests/test_paper_autonomous_readiness_gate_schema.py`

**Interfaces:**
- Consumes: existing table `public.paper_autonomous_readiness_gate_reports`
- Produces: local Supabase/Postgres migration that allows readiness gate reports with either 3 or 4 source rows.

- [ ] **Step 1: Write failing schema tests**

Add tests that assert:
- the new migration file exists with sequence `20260629000002`
- it relaxes both `source_statuses_json` and `source_config_versions_json` length checks to allow `3` or `4`
- it adds a deterministic sort index for four-source rows including `source_statuses_json #>> '{3,status}'`
- it does not mention SQLite, Redis, Mongo, SQLAlchemy, hosted DB, auth, wallet, private keys, order signing, order submission, or live trading

Use exact snippets:

```python
NEW_MIGRATION = MIGRATIONS_DIR / "20260629000002_paper_autonomous_readiness_gate_strategy_cycle_source.sql"

def test_readiness_gate_strategy_cycle_source_migration_relaxes_source_lengths() -> None:
    sql = NEW_MIGRATION.read_text(encoding="utf-8").lower()
    assert "jsonb_array_length(source_statuses_json) in (3, 4)" in sql
    assert "jsonb_array_length(source_config_versions_json) in (3, 4)" in sql
```

```python
def test_readiness_gate_strategy_cycle_source_migration_adds_four_source_sort_index() -> None:
    sql = " ".join(NEW_MIGRATION.read_text(encoding="utf-8").lower().split())
    assert "source_statuses_json #>> '{3,status}'" in sql
    assert "pargr_four_source_status_sort_idx" in sql
```

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:src python3 -m pytest -q tests/test_paper_autonomous_readiness_gate_schema.py
```

Expected before implementation: missing migration failure.

- [ ] **Step 2: Implement migration**

Use a Postgres-only migration. Because the old length checks were unnamed, drop matching constraints by `pg_get_constraintdef()`:

```sql
do $$
declare
    constraint_name text;
begin
    for constraint_name in
        select conname
        from pg_constraint
        where conrelid = 'public.paper_autonomous_readiness_gate_reports'::regclass
          and contype = 'c'
          and pg_get_constraintdef(oid) like '%jsonb_array_length(source_statuses_json) = 3%'
    loop
        execute format(
            'alter table public.paper_autonomous_readiness_gate_reports drop constraint if exists %I',
            constraint_name
        );
    end loop;

    for constraint_name in
        select conname
        from pg_constraint
        where conrelid = 'public.paper_autonomous_readiness_gate_reports'::regclass
          and contype = 'c'
          and pg_get_constraintdef(oid) like '%jsonb_array_length(source_config_versions_json) = 3%'
    loop
        execute format(
            'alter table public.paper_autonomous_readiness_gate_reports drop constraint if exists %I',
            constraint_name
        );
    end loop;
end $$;

alter table public.paper_autonomous_readiness_gate_reports
    add constraint pargr_source_statuses_length_check
    check (jsonb_array_length(source_statuses_json) in (3, 4));

alter table public.paper_autonomous_readiness_gate_reports
    add constraint pargr_source_config_versions_length_check
    check (jsonb_array_length(source_config_versions_json) in (3, 4));

create index if not exists pargr_four_source_status_sort_idx
    on public.paper_autonomous_readiness_gate_reports
    (
        (source_statuses_json #>> '{0,status}'),
        (source_statuses_json #>> '{1,status}'),
        (source_statuses_json #>> '{2,status}'),
        (source_statuses_json #>> '{3,status}'),
        generated_at desc,
        inserted_at desc,
        report_sha256 desc
    );
```

- [ ] **Step 3: Verify and commit**

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:src python3 -m pytest -q tests/test_paper_autonomous_readiness_gate_schema.py
PYTHONDONTWRITEBYTECODE=1 python3 -m compileall -q src tests
git diff --check
git add supabase/migrations/20260629000002_paper_autonomous_readiness_gate_strategy_cycle_source.sql tests/test_paper_autonomous_readiness_gate_schema.py
git commit -m "feat: relax readiness gate schema for strategy cycle source"
```

---

### Task 3: Row Codec And Store Query Support

**Files:**
- Modify: `tests/test_paper_autonomous_readiness_gate_db_row.py`
- Modify: `src/polymarket_alpha_lab/paper_autonomous_readiness_gate_store.py`
- Modify: `tests/test_paper_autonomous_readiness_gate_store.py`

**Interfaces:**
- Consumes: Task 1 four-source readiness reports.
- Produces:

```python
def load_paper_autonomous_readiness_gate_reports(
    connection: Any,
    *,
    config_version: str | None = None,
    readiness_status: str | None = None,
    screening_config_version: str | None = None,
    strategy_cycle_history_gate_config_version: str | None = None,
    allocation_config_version: str | None = None,
    investment_ledger_config_version: str | None = None,
    limit: int | None = None,
    table_name: str = DEFAULT_PAPER_AUTONOMOUS_READINESS_GATE_REPORTS_TABLE,
) -> tuple["PaperAutonomousReadinessGateReport", ...]:
    ...
```

- [ ] **Step 1: Write failing DB row and store tests**

Add a four-source `_report()` variant in `tests/test_paper_autonomous_readiness_gate_db_row.py` and assert:

```python
assert row.source_config_versions_json == [
    [SCREENING_SOURCE_NAME, "screening-health-v0"],
    ["strategy_cycle_report_history_gate", "strategy-cycle-history-gate-v0"],
    [ALLOCATION_SOURCE_NAME, "allocation-trend-gate-v0"],
    [INVESTMENT_LEDGER_SOURCE_NAME, "ledger-trend-gate-v0"],
]
assert codec.from_db_row(row) == report
```

Add store filter tests:

```python
reports = load_paper_autonomous_readiness_gate_reports(
    connection,
    strategy_cycle_history_gate_config_version="strategy-cycle-history-gate-v0",
)
sql, params = connection.cursor_instance.calls[0]
assert "source_config_versions_json @> %s" in sql
assert [["strategy_cycle_report_history_gate", "strategy-cycle-history-gate-v0"]] in params
```

Add invalid query validation:

```python
with pytest.raises(ValueError, match="strategy_cycle_history_gate_config_version"):
    load_paper_autonomous_readiness_gate_reports(
        FakeConnection(),
        strategy_cycle_history_gate_config_version="",
    )
```

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:src python3 -m pytest -q tests/test_paper_autonomous_readiness_gate_db_row.py tests/test_paper_autonomous_readiness_gate_store.py
```

Expected before implementation: direct four-source constructor and/or store keyword failures.

- [ ] **Step 2: Implement store support**

- Import `STRATEGY_CYCLE_HISTORY_GATE_SOURCE_NAME`.
- Validate `strategy_cycle_history_gate_config_version` with `_require_canonical_string`.
- Add a `source_config_versions_json @> %s` condition with `[[STRATEGY_CYCLE_HISTORY_GATE_SOURCE_NAME, strategy_cycle_history_gate_config_version]]`.
- Keep table-name validation before cursor creation.
- Do not change insert SQL columns or add non-Postgres storage.

- [ ] **Step 3: Verify and commit**

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:src python3 -m pytest -q tests/test_paper_autonomous_readiness_gate.py tests/test_paper_autonomous_readiness_gate_db_row.py tests/test_paper_autonomous_readiness_gate_store.py
PYTHONDONTWRITEBYTECODE=1 python3 -m compileall -q src tests
git diff --check
git add src/polymarket_alpha_lab/paper_autonomous_readiness_gate_store.py tests/test_paper_autonomous_readiness_gate_db_row.py tests/test_paper_autonomous_readiness_gate_store.py
git commit -m "feat: query readiness gates by strategy cycle source"
```

---

### Task 4: Docs And Scope Tests

**Files:**
- Modify: `docs/paper-autonomous-readiness-gate.md`
- Modify: `tests/test_init.py` only if needed
- Modify or add doc/scope tests if existing docs tests require updates.

**Interfaces:**
- Consumes: Task 1 source name and builder signature.
- Produces: documentation that explains legacy three-source and optional four-source readiness reports.

- [ ] **Step 1: Write failing docs/scope tests**

If `tests/test_docs_paper_autonomous_readiness_gate_scope.py` exists, update it to require the new source wording. If there is no direct test, add one there. Required snippets:

```python
required_snippets = (
    "strategy-cycle report history gate",
    "optional fourth source",
    "strategy_cycle_report_history_gate",
    "three-source legacy reports remain valid",
    "no live trading",
    "no auth",
    "no wallet",
    "no order submission",
)
```

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:src python3 -m pytest -q tests/test_docs_paper_autonomous_readiness_gate_scope.py tests/test_init.py
```

Expected before implementation: missing snippet failure.

- [ ] **Step 2: Update docs without expanding package root**

Update `docs/paper-autonomous-readiness-gate.md`:
- Source Reports now list:
  - screening decision-support gate DB-history health
  - optional strategy-cycle report history gate
  - allocation proposal DB-history health trend gate
  - investment-ledger DB-history health trend gate
- State that legacy three-source reports remain valid for older local rows and callers.
- State that this node still does not add CLI builder, env reads, broker/order requests, or persistence behavior to the pure reducer.
- Do not add new package-root exports.

- [ ] **Step 3: Verify and commit**

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:src python3 -m pytest -q tests/test_docs_paper_autonomous_readiness_gate_scope.py tests/test_init.py
PYTHONDONTWRITEBYTECODE=1 python3 -m compileall -q src tests
git diff --check
git add docs/paper-autonomous-readiness-gate.md tests/test_docs_paper_autonomous_readiness_gate_scope.py tests/test_init.py
git commit -m "docs: document readiness gate strategy cycle source"
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
