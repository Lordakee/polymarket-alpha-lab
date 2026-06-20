# Action-Gated Queue History DB Persistence Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a paper-only/report-only database persistence foundation for `PaperActionGatedStrategyRecommendationQueueHistoryReport`.

**Architecture:** Mirror the existing action-gated queue report persistence stack: pure row codec, DB-API store, optional psycopg adapter, env config, migration, docs, and scope tests. This node creates persistence primitives only; it does not wire automatic writes into live trading, accounts, wallets, order construction, signing, submission, cancellation, replacement, or exchange mutation.

**Tech Stack:** Python dataclasses, Decimal-only JSON codec, DB-API SQL with parameterized values and validated table identifiers, optional psycopg adapter, Supabase migration SQL, pytest.

---

### Task 1: History Row Codec

**Files:**
- Create: `src/polymarket_alpha_lab/action_gated_strategy_recommendation_queue_history_db_row.py`
- Test: `tests/test_action_gated_strategy_recommendation_queue_history_db_row.py`

- [ ] **Step 1: Write failing row codec tests**

Create tests that expect:

```python
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from polymarket_alpha_lab.action_gated_strategy_recommendation_queue_history import (
    PaperActionGatedStrategyRecommendationQueueHistoryReport,
)
from polymarket_alpha_lab.paper_recommendation_cycle_action_gate import (
    PaperRecommendationCycleActionGateReasonCodeCount,
)
from polymarket_alpha_lab.action_gated_strategy_recommendation_queue_history_db_row import (
    PaperActionGatedStrategyRecommendationQueueHistoryDbRow,
    paper_action_gated_strategy_recommendation_queue_history_report_from_db_row,
    paper_action_gated_strategy_recommendation_queue_history_report_to_db_row,
)


def _history_report() -> PaperActionGatedStrategyRecommendationQueueHistoryReport:
    return PaperActionGatedStrategyRecommendationQueueHistoryReport(
        generated_at=datetime(2026, 6, 20, 12, 0, tzinfo=UTC),
        source_report_count=3,
        first_source_generated_at=datetime(2026, 6, 20, 9, 0, tzinfo=UTC),
        last_source_generated_at=datetime(2026, 6, 20, 11, 0, tzinfo=UTC),
        research_ready_count=1,
        watch_count=1,
        blocked_count=1,
        total_ready_notional=Decimal("42.000000"),
        latest_action_status="research_ready",
        latest_recommended_next_step="review_candidate_research_queue",
        status_transition_count=2,
        ready_notional_delta=Decimal("12.000000"),
        latest_reason_code_counts=(
            PaperRecommendationCycleActionGateReasonCodeCount(
                reason_code="cycle_review_passed",
                count=1,
            ),
        ),
    )
```

Assert conversion to a DB row produces a deterministic lowercase sha256 digest, scalar columns, `latest_reason_code_counts_json`, `payload_json`, and hard flags. Assert converting the row back round-trips the report. Assert payload JSON rejects floats and hard flags set to false.

- [ ] **Step 2: Run RED**

Run:

```bash
.venv/bin/python -m pytest tests/test_action_gated_strategy_recommendation_queue_history_db_row.py -q
```

Expected: import failure for the new module or missing symbols.

- [ ] **Step 3: Implement row codec**

Implement:

```python
@dataclass(frozen=True)
class PaperActionGatedStrategyRecommendationQueueHistoryDbRow:
    report_sha256: str
    generated_at: datetime
    source_report_count: int
    first_source_generated_at: datetime | None
    last_source_generated_at: datetime | None
    research_ready_count: int
    watch_count: int
    blocked_count: int
    total_ready_notional: Decimal
    latest_action_status: str | None
    latest_recommended_next_step: str | None
    status_transition_count: int
    ready_notional_delta: Decimal
    latest_reason_code_counts_json: dict[str, int]
    payload_json: dict[str, object]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
```

Expose:

```python
paper_action_gated_strategy_recommendation_queue_history_report_to_db_row(report)
paper_action_gated_strategy_recommendation_queue_history_report_from_db_row(row)
```

Use `dataclasses.asdict`, `json.dumps(..., allow_nan=False, separators=(",", ":"), sort_keys=True)`, Decimal-to-string JSON, UTC datetime ISO strings, and `json_recovery.from_jsonable` to recover the history report.

- [ ] **Step 4: Run GREEN**

Run:

```bash
.venv/bin/python -m pytest tests/test_action_gated_strategy_recommendation_queue_history_db_row.py tests/test_action_gated_strategy_recommendation_queue_history.py -q
```

Expected: all pass.

### Task 2: DB-API Store And Psycopg Adapter

**Files:**
- Create: `src/polymarket_alpha_lab/action_gated_strategy_recommendation_queue_history_store.py`
- Create: `src/polymarket_alpha_lab/action_gated_strategy_recommendation_queue_history_psycopg.py`
- Test: `tests/test_action_gated_strategy_recommendation_queue_history_store.py`
- Test: `tests/test_action_gated_strategy_recommendation_queue_history_psycopg.py`

- [ ] **Step 1: Write failing store and adapter tests**

Tests should assert:
- Default table is `paper_action_gated_strategy_recommendation_queue_history_reports`.
- Insert SQL is parameterized and uses `ON CONFLICT (report_sha256) DO NOTHING`.
- Load SQL supports optional `latest_action_status` and `limit` filters.
- Table names accept lowercase identifiers with optional schema prefix only.
- Cursor is closed.
- Store layer does not call commit/rollback.
- Psycopg adapter wraps JSON dict/list params in `Jsonb`, commits on success, rolls back on failure, and closes connection.

- [ ] **Step 2: Run RED**

Run:

```bash
.venv/bin/python -m pytest tests/test_action_gated_strategy_recommendation_queue_history_store.py tests/test_action_gated_strategy_recommendation_queue_history_psycopg.py -q
```

Expected: import failure for new modules or missing symbols.

- [ ] **Step 3: Implement store and adapter**

Store exports:

```python
DEFAULT_ACTION_GATED_STRATEGY_RECOMMENDATION_QUEUE_HISTORY_TABLE
insert_paper_action_gated_strategy_recommendation_queue_history_report
load_paper_action_gated_strategy_recommendation_queue_history_reports
```

Adapter exports:

```python
insert_paper_action_gated_strategy_recommendation_queue_history_report_with_psycopg
load_paper_action_gated_strategy_recommendation_queue_history_reports_with_psycopg
```

Keep this persistence-only; do not import or call any client, account, order, wallet, exchange, live trading, auth, signing, submission, cancellation, or replacement API.

- [ ] **Step 4: Run GREEN**

Run:

```bash
.venv/bin/python -m pytest tests/test_action_gated_strategy_recommendation_queue_history_store.py tests/test_action_gated_strategy_recommendation_queue_history_psycopg.py tests/test_action_gated_strategy_recommendation_queue_history_db_row.py -q
```

Expected: all pass.

### Task 3: Env Config, Migration, Docs, Scope

**Files:**
- Create: `src/polymarket_alpha_lab/supabase_action_gated_strategy_recommendation_queue_history_config.py`
- Create: `tests/test_supabase_action_gated_strategy_recommendation_queue_history_config.py`
- Create: `supabase/migrations/20260620000001_action_gated_strategy_recommendation_queue_history_reports.sql`
- Create: `docs/action-gated-queue-history-db-persistence.md`
- Create: `tests/test_action_gated_queue_history_db_persistence_scope.py`

- [ ] **Step 1: Write failing config, migration, and scope tests**

Config env vars:

```python
POLYMARKET_ALPHA_LAB_ACTION_GATED_QUEUE_HISTORY_DB_ENABLED
POLYMARKET_ALPHA_LAB_ACTION_GATED_QUEUE_HISTORY_DB_DSN
POLYMARKET_ALPHA_LAB_ACTION_GATED_QUEUE_HISTORY_DB_TABLE
```

Default table:

```python
paper_action_gated_strategy_recommendation_queue_history_reports
```

Tests should assert strict boolean parsing, DSN redaction in `repr`, no DSN echo in errors, blank `.env.example` entries, migration table/columns/checks/indexes, and scope guard prohibitions.

- [ ] **Step 2: Run RED**

Run:

```bash
.venv/bin/python -m pytest tests/test_supabase_action_gated_strategy_recommendation_queue_history_config.py tests/test_action_gated_queue_history_db_persistence_scope.py -q
```

Expected: import/file failures.

- [ ] **Step 3: Implement config, migration, docs, and env example additions**

Migration table columns:
- `report_sha256 text primary key`
- `generated_at timestamptz not null`
- `source_report_count integer not null`
- `first_source_generated_at timestamptz`
- `last_source_generated_at timestamptz`
- `research_ready_count integer not null`
- `watch_count integer not null`
- `blocked_count integer not null`
- `total_ready_notional numeric not null`
- `latest_action_status text`
- `latest_recommended_next_step text`
- `status_transition_count integer not null`
- `ready_notional_delta numeric not null`
- `latest_reason_code_counts jsonb not null`
- `payload jsonb not null`
- `paper_only boolean not null default true`
- `report_only boolean not null default true`
- `readonly boolean not null default true`
- `inserted_at timestamptz not null default now()`

Checks should enforce nonnegative counts/notional, JSON object payloads, hard flags true, latest next step matching latest status when present, and empty-history fields being null when `source_report_count = 0`.

- [ ] **Step 4: Run GREEN**

Run:

```bash
.venv/bin/python -m pytest tests/test_supabase_action_gated_strategy_recommendation_queue_history_config.py tests/test_action_gated_queue_history_db_persistence_scope.py -q
```

Expected: all pass.

### Task 4: Integration Verification

**Files:**
- No new files; run verification over all files from Tasks 1-3.

- [ ] **Step 1: Run focused verification**

Run:

```bash
.venv/bin/python -m pytest \
  tests/test_action_gated_strategy_recommendation_queue_history*.py \
  tests/test_supabase_action_gated_strategy_recommendation_queue_history_config.py \
  tests/test_action_gated_queue_history_db_persistence_scope.py -q
```

Expected: all pass.

- [ ] **Step 2: Run full verification and review**

Run:

```bash
.venv/bin/python -m pytest -q
.venv/bin/python -m compileall -q src tests
git diff --check
codegraph sync
opencode run --model zhipuai-coding-plan/glm-5.2 --variant max --dir /home/ubuntu/polymarket-alpha-lab "<review prompt>"
```

Expected: full tests pass, compileall passes, diff check passes, CodeGraph up to date, OpenCode returns `VERDICT: PASS`.
