# Readiness Gate Strategy Risk Source Persistence Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make local Supabase/Postgres readiness-gate persistence compatible with the optional `strategy_risk_audit_history_gate` source.

**Architecture:** Keep `paper_autonomous_readiness_gate.py` pure and unchanged. Extend only the row-codec tests, DB-API store filters, psycopg pass-through adapter, and Supabase migration/schema tests so readiness reports with 3, 4, or 5 source rows can be stored, loaded, and queried by the new optional source config version.

**Tech Stack:** Python frozen dataclasses, DB-API `%s` placeholders, optional psycopg wrapper, local Supabase/Postgres SQL migrations, pytest fake connections, CodeGraph.

## Global Constraints

- Durable project data must use local Supabase/Postgres only.
- Do not use SQLite, Redis, Mongo, SQLAlchemy, hosted DB assumptions, file-backed persistence, or generic DB abstractions.
- Do not edit already-applied migration files. Add a new migration only.
- Keep `paper_autonomous_readiness_gate.py` Phase 1 pure: no DB, env, CLI, network, Supabase, psycopg, filesystem, live trading, auth, wallet, account, private key, or order surfaces.
- This node does not add live trading, account auth, wallets, private keys, order signing/submission/cancellation/replacement, exchange mutation, runners, or CLI flags.
- DB-API store functions must not commit or rollback. psycopg write wrappers own write transaction lifecycle; read wrappers use `autocommit=True`.
- Runtime values use `%s` placeholders. Only a validated table identifier may be interpolated into SQL.
- Review gates are read-only through local opencode using model `zhipuai-coding-plan/glm-5.2` and variant `max`.
- Codex worker subagents must use `gpt-5.5` with reasoning effort `xhigh`; fast mode is forbidden.

---

## File Structure

- Modify `tests/test_paper_autonomous_readiness_gate_db_row.py`: add strategy-risk-only 4-source and combined 5-source codec round trips.
- Modify `src/polymarket_alpha_lab/paper_autonomous_readiness_gate_store.py`: add `strategy_risk_audit_history_gate_config_version` query filter.
- Modify `tests/test_paper_autonomous_readiness_gate_store.py`: add SQL/param validation and invalid input validation for the new filter.
- Modify `src/polymarket_alpha_lab/paper_autonomous_readiness_gate_psycopg.py`: pass the new filter through to the DB-API store.
- Modify `tests/test_paper_autonomous_readiness_gate_psycopg.py`: verify psycopg load pass-through includes the new filter.
- Create `supabase/migrations/20260629000003_paper_autonomous_readiness_gate_strategy_risk_source.sql`: relax source length constraints from `(3, 4)` to `(3, 4, 5)` and add a five-source status-sort index.
- Modify `tests/test_paper_autonomous_readiness_gate_schema.py`: assert the new migration exists, uses a unique version, relaxes to `(3, 4, 5)`, adds the five-source index, and avoids forbidden surfaces.
- Modify `docs/paper-autonomous-readiness-gate-store-plan.md` only to mark old length/filter sections as historical if required by tests or review. Do not broadly rewrite historical plans.

---

### Task 1: DB Row Codec Compatibility

**Files:**
- Modify: `tests/test_paper_autonomous_readiness_gate_db_row.py`

**Interfaces:**
- Use existing `PaperAutonomousReadinessGateReport` and `PaperAutonomousReadinessGateSourceStatus`.
- Import `STRATEGY_RISK_AUDIT_HISTORY_GATE_SOURCE_NAME` from `polymarket_alpha_lab.paper_autonomous_readiness_gate`.
- Existing codec implementation should not need production changes if reducer validation already accepts the new source orders.

- [ ] **Step 1: Write failing or regression tests**

Add helpers:

```python
def _strategy_risk_source_report() -> PaperAutonomousReadinessGateReport:
    return _report(
        source_statuses=(
            _source_status(SCREENING_SOURCE_NAME, "pass", "screening-health-v0"),
            _source_status(ALLOCATION_SOURCE_NAME, "watch", "allocation-trend-gate-v0"),
            _source_status(INVESTMENT_LEDGER_SOURCE_NAME, "pass", "ledger-trend-gate-v0"),
            _source_status(
                STRATEGY_RISK_AUDIT_HISTORY_GATE_SOURCE_NAME,
                "pass",
                "strategy-risk-audit-history-gate-v0",
            ),
        ),
        reason_codes=(
            "allocation_proposal_db_history_health_trend_gate_watch",
            "investment_ledger_db_history_health_trend_gate_pass",
            "screening_decision_support_gate_db_history_health_pass",
            "strategy_risk_audit_history_gate_pass",
        ),
    )
```

Add a combined 5-source helper with order:

```text
screening -> strategy_cycle_report_history_gate -> allocation -> investment_ledger -> strategy_risk_audit_history_gate
```

Add tests:

```python
def test_readiness_gate_db_row_serializes_strategy_risk_source_payload_and_round_trips() -> None:
    ...

def test_readiness_gate_db_row_serializes_five_source_payload_and_round_trips() -> None:
    ...
```

Assert `row.source_config_versions_json` order exactly matches the source order and `codec.from_db_row(row) == report`.

- [ ] **Step 2: Run focused tests**

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:src python3 -m pytest -q tests/test_paper_autonomous_readiness_gate_db_row.py
```

Expected: pass if codec already supports reducer orders, or fail with the exact compatibility gap to fix.

- [ ] **Step 3: Implement only if needed**

If the tests fail, fix only the codec defect needed for new source orders. Do not add DB/store/schema behavior in this task.

- [ ] **Step 4: Commit**

```bash
git add tests/test_paper_autonomous_readiness_gate_db_row.py src/polymarket_alpha_lab/paper_autonomous_readiness_gate_db_row.py
git commit -m "test: cover readiness gate strategy risk db rows"
```

Omit the source file if no production change is needed.

---

### Task 2: Store And Psycopg Source Filter

**Files:**
- Modify: `src/polymarket_alpha_lab/paper_autonomous_readiness_gate_store.py`
- Modify: `tests/test_paper_autonomous_readiness_gate_store.py`
- Modify: `src/polymarket_alpha_lab/paper_autonomous_readiness_gate_psycopg.py`
- Modify: `tests/test_paper_autonomous_readiness_gate_psycopg.py`

**Interfaces:**
- Add store parameter:

```python
strategy_risk_audit_history_gate_config_version: str | None = None
```

- Use JSONB containment condition:

```python
conditions.append("source_config_versions_json @> %s")
params.append([
    [
        STRATEGY_RISK_AUDIT_HISTORY_GATE_SOURCE_NAME,
        strategy_risk_audit_history_gate_config_version,
    ],
])
```

- Add the same keyword-only parameter to `load_paper_autonomous_readiness_gate_reports_with_psycopg(...)` and pass it through to the store.

- [ ] **Step 1: Write failing tests**

In store tests:

```python
def test_load_readiness_gate_reports_filters_strategy_risk_audit_history_gate_source() -> None:
    ...
```

Assert params include:

```python
[
    ["strategy_risk_audit_history_gate", "strategy-risk-audit-history-gate-v0"],
]
```

Update deterministic filter-order test so the new filter is after strategy-cycle and before allocation only if strategy-cycle is already in the deterministic order; otherwise use:

```text
config_version, readiness_status, screening, strategy_cycle, strategy_risk, allocation, investment_ledger, limit
```

Update invalid query inputs with:

```python
({"strategy_risk_audit_history_gate_config_version": ""}, "strategy_risk_audit_history_gate_config_version")
```

In psycopg tests, extend fake load signature and expected tuple to include the new parameter.

- [ ] **Step 2: Run failing tests**

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:src python3 -m pytest -q \
  tests/test_paper_autonomous_readiness_gate_store.py \
  tests/test_paper_autonomous_readiness_gate_psycopg.py
```

Expected before implementation: unexpected keyword/signature or missing param assertions fail.

- [ ] **Step 3: Implement minimal store/psycopg changes**

Import `STRATEGY_RISK_AUDIT_HISTORY_GATE_SOURCE_NAME` in the store. Keep SQL parameterized and keep transaction ownership unchanged.

- [ ] **Step 4: Run focused tests**

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:src python3 -m pytest -q \
  tests/test_paper_autonomous_readiness_gate_store.py \
  tests/test_paper_autonomous_readiness_gate_psycopg.py
```

- [ ] **Step 5: Commit**

```bash
git add \
  src/polymarket_alpha_lab/paper_autonomous_readiness_gate_store.py \
  tests/test_paper_autonomous_readiness_gate_store.py \
  src/polymarket_alpha_lab/paper_autonomous_readiness_gate_psycopg.py \
  tests/test_paper_autonomous_readiness_gate_psycopg.py
git commit -m "feat: query readiness gates by strategy risk source"
```

---

### Task 3: Supabase Migration For 3/4/5 Source Rows

**Files:**
- Create: `supabase/migrations/20260629000003_paper_autonomous_readiness_gate_strategy_risk_source.sql`
- Modify: `tests/test_paper_autonomous_readiness_gate_schema.py`

**Migration Contract:**
- Do not edit `20260625000007_paper_autonomous_readiness_gate_reports.sql`.
- Do not edit `20260629000002_paper_autonomous_readiness_gate_strategy_cycle_source.sql`.
- Drop existing check constraints that contain:

```text
jsonb_array_length(source_statuses_json) in (3, 4)
jsonb_array_length(source_config_versions_json) in (3, 4)
```

- Add:

```sql
alter table public.paper_autonomous_readiness_gate_reports
    add constraint pargr_source_statuses_length_check
    check (jsonb_array_length(source_statuses_json) in (3, 4, 5));

alter table public.paper_autonomous_readiness_gate_reports
    add constraint pargr_source_config_versions_length_check
    check (jsonb_array_length(source_config_versions_json) in (3, 4, 5));
```

- Add index:

```sql
create index if not exists pargr_five_source_status_sort_idx
    on public.paper_autonomous_readiness_gate_reports
    (
        (source_statuses_json #>> '{0,status}'),
        (source_statuses_json #>> '{1,status}'),
        (source_statuses_json #>> '{2,status}'),
        (source_statuses_json #>> '{3,status}'),
        (source_statuses_json #>> '{4,status}'),
        generated_at desc,
        inserted_at desc,
        report_sha256 desc
    );
```

- No functions other than anonymous `do $$` migration blocks. No triggers, RLS, policies, foreign keys, external DBs, live/auth/wallet/key/order terms.

- [ ] **Step 1: Write failing schema tests**

Add tests:

```python
def test_readiness_gate_strategy_risk_source_migration_uses_expected_sequence() -> None:
    ...

def test_readiness_gate_strategy_risk_source_migration_relaxes_source_lengths() -> None:
    ...

def test_readiness_gate_strategy_risk_source_migration_adds_five_source_sort_index() -> None:
    ...

def test_readiness_gate_strategy_risk_source_migration_avoids_forbidden_surfaces() -> None:
    ...
```

Expected before migration exists: tests fail because file is missing.

- [ ] **Step 2: Run failing tests**

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:src python3 -m pytest -q tests/test_paper_autonomous_readiness_gate_schema.py
```

- [ ] **Step 3: Add migration**

Create the new migration exactly in `supabase/migrations/20260629000003_paper_autonomous_readiness_gate_strategy_risk_source.sql`.

- [ ] **Step 4: Run focused tests**

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:src python3 -m pytest -q tests/test_paper_autonomous_readiness_gate_schema.py
```

- [ ] **Step 5: Commit**

```bash
git add \
  supabase/migrations/20260629000003_paper_autonomous_readiness_gate_strategy_risk_source.sql \
  tests/test_paper_autonomous_readiness_gate_schema.py
git commit -m "db: allow strategy risk readiness source rows"
```

---

### Task 4: Docs And Verification

**Files:**
- Modify: `docs/paper-autonomous-readiness-gate-store-plan.md` only if required to stop stale current guidance.

**Requirements:**
- If docs are updated, mark old length-3 and old filter lists as historical, and mention current local Supabase/Postgres compatibility accepts 3, 4, or 5 readiness source rows after migrations through `20260629000003`.
- Do not add CLI/env/live/auth/wallet/key/order wording beyond boundary statements.

- [ ] **Step 1: Run focused integration tests**

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:src python3 -m pytest -q \
  tests/test_paper_autonomous_readiness_gate_db_row.py \
  tests/test_paper_autonomous_readiness_gate_store.py \
  tests/test_paper_autonomous_readiness_gate_psycopg.py \
  tests/test_paper_autonomous_readiness_gate_schema.py \
  tests/test_paper_autonomous_readiness_gate.py \
  tests/test_paper_autonomous_readiness_gate_scope.py
```

- [ ] **Step 2: Run full verification**

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' PYTHONPATH=.:src python3 -m pytest -q
PYTHONDONTWRITEBYTECODE=1 python3 -m compileall -q src tests
git diff --check
codegraph sync
git grep -n -E '(ghp_[A-Za-z0-9]{36,}|github_pat_[A-Za-z0-9_]{20,}|sk-proj-[A-Za-z0-9_-]{20,}|sk-live-[A-Za-z0-9_-]{20,}|-----BEGIN (RSA |OPENSSH |EC |DSA |)PRIVATE KEY-----)' HEAD || true
```

- [ ] **Step 3: opencode read-only review**

```bash
opencode run -m zhipuai-coding-plan/glm-5.2 --variant max --dir /home/ubuntu/polymarket-alpha-lab "<read-only review prompt for origin/main..HEAD>"
```

Prompt requirements:

```text
Read-only review. Review commits origin/main..HEAD for node: readiness gate strategy-risk source persistence compatibility. Requirements: DB row round-trips strategy-risk-only 4-source and combined 5-source readiness reports; store and psycopg load filters support strategy_risk_audit_history_gate_config_version with parameterized JSONB containment; new Supabase/Postgres migration relaxes readiness source length checks to 3/4/5 and adds five-source status sort index; applied migrations are not edited; no DB backend except local Supabase/Postgres; no live trading/auth/wallet/private keys/order signing/submission/cancellation/replacement/exchange mutation; pure readiness reducer remains free of DB/store/schema/CLI/env changes. Output Critical/Important/Minor and verdict.
```

- [ ] **Step 4: Push if approved**

```bash
git push origin main
```

