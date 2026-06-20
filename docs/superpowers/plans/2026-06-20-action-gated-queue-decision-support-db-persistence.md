# Action-Gated Queue Decision-Support DB Persistence Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Persist the paper-only/report-only action-gated queue decision-support snapshot made from priority and risk reports.

**Architecture:** Add a persistence foundation for a composite snapshot containing `PaperActionGatedStrategyRecommendationQueuePriorityReport` and `PaperActionGatedStrategyRecommendationQueueRiskReport`. Mirror existing row/store/psycopg/env/migration patterns. This node creates library persistence infrastructure only; it does not wire live trading, accounts, wallets, order construction, signing, submission, cancellation, replacement, or exchange mutation.

**Tech Stack:** Python dataclasses, Decimal-only canonical JSON codec, DB-API SQL with validated table identifiers, optional psycopg adapter, Supabase migration SQL, pytest.

---

### Task 1: Decision-Support Row Codec

**Files:**
- Create: `src/polymarket_alpha_lab/action_gated_strategy_recommendation_queue_decision_support_db_row.py`
- Test: `tests/test_action_gated_strategy_recommendation_queue_decision_support_db_row.py`

- [ ] **Step 1: Write failing row codec tests**

Build sample priority and risk reports using their public dataclasses. Assert that `paper_action_gated_strategy_recommendation_queue_decision_support_to_db_row(priority_report, risk_report)` produces:
- deterministic `snapshot_sha256`
- `generated_at`
- priority scalar columns: `priority_source_report_count`, `priority_research_ready_count`, `priority_watch_count`, `priority_blocked_count`, `priority_total_ready_notional`, `top_research_priority_score`, `average_research_priority_score`
- risk scalar columns: `risk_config_version`, `risk_status`, `risk_recommended_next_step`, `risk_source_queue_count`, `risk_candidate_count`, `risk_ready_count`, `risk_total_ready_notional`, `risk_largest_queue_ready_notional`, `risk_reason_codes_json`
- `priority_payload_json`, `risk_payload_json`
- `paper_only=True`, `report_only=True`, `readonly=True`

Assert row-to-report round trip recovers both original reports. Assert floats, false hard flags, wrong types, duplicate JSON reason codes, and row/payload mismatches are rejected.

- [ ] **Step 2: Run RED**

Run:

```bash
.venv/bin/python -m pytest tests/test_action_gated_strategy_recommendation_queue_decision_support_db_row.py -q
```

Expected: module import failure.

- [ ] **Step 3: Implement codec**

Expose:

```python
@dataclass(frozen=True)
class PaperActionGatedStrategyRecommendationQueueDecisionSupportDbRow: ...

paper_action_gated_strategy_recommendation_queue_decision_support_to_db_row(
    priority_report,
    risk_report,
)
paper_action_gated_strategy_recommendation_queue_decision_support_from_db_row(row)
```

Return `(priority_report, risk_report)` from `from_db_row`.

Use `dataclasses.asdict`, canonical JSON with `allow_nan=False`, Decimal as strings, UTC ISO datetimes, no floats, recursive hard-flag validation, and `json_recovery.from_jsonable`.

- [ ] **Step 4: Run GREEN**

Run:

```bash
.venv/bin/python -m pytest tests/test_action_gated_strategy_recommendation_queue_decision_support_db_row.py tests/test_action_gated_strategy_recommendation_queue_priority.py tests/test_action_gated_strategy_recommendation_queue_risk.py -q
```

Expected: all pass.

### Task 2: Store And Psycopg Adapter

**Files:**
- Create: `src/polymarket_alpha_lab/action_gated_strategy_recommendation_queue_decision_support_store.py`
- Create: `src/polymarket_alpha_lab/action_gated_strategy_recommendation_queue_decision_support_psycopg.py`
- Test: `tests/test_action_gated_strategy_recommendation_queue_decision_support_store.py`
- Test: `tests/test_action_gated_strategy_recommendation_queue_decision_support_psycopg.py`

- [ ] **Step 1: Write failing store/adapter tests**

Tests should assert:
- default table `paper_action_gated_strategy_recommendation_queue_decision_support_reports`
- parameterized insert with `ON CONFLICT (snapshot_sha256) DO NOTHING`
- load filters by optional `risk_status`, `risk_config_version`, and `limit`
- rows can be dict, tuple, namedtuple, or db-row dataclass
- store never commits or rolls back
- psycopg adapter commits on success, rolls back on error, closes connections, and adapts JSON dict/list params with `Jsonb`

- [ ] **Step 2: Run RED**

Run:

```bash
.venv/bin/python -m pytest tests/test_action_gated_strategy_recommendation_queue_decision_support_store.py tests/test_action_gated_strategy_recommendation_queue_decision_support_psycopg.py -q
```

Expected: module import failure.

- [ ] **Step 3: Implement store and adapter**

Store exports:

```python
DEFAULT_ACTION_GATED_STRATEGY_RECOMMENDATION_QUEUE_DECISION_SUPPORT_TABLE
insert_paper_action_gated_strategy_recommendation_queue_decision_support_report
load_paper_action_gated_strategy_recommendation_queue_decision_support_reports
```

Adapter exports matching `_with_psycopg` wrappers.

Keep this persistence-only. Do not import or call clients, accounts, auth, wallets, orders, signing, submission, cancellation, replacement, exchange, or live trading surfaces.

- [ ] **Step 4: Run GREEN**

Run:

```bash
.venv/bin/python -m pytest tests/test_action_gated_strategy_recommendation_queue_decision_support_store.py tests/test_action_gated_strategy_recommendation_queue_decision_support_psycopg.py tests/test_action_gated_strategy_recommendation_queue_decision_support_db_row.py -q
```

Expected: all pass.

### Task 3: Env Config, Migration, Docs, Scope

**Files:**
- Create: `src/polymarket_alpha_lab/supabase_action_gated_strategy_recommendation_queue_decision_support_config.py`
- Create: `tests/test_supabase_action_gated_strategy_recommendation_queue_decision_support_config.py`
- Create: `supabase/migrations/20260620000002_action_gated_strategy_recommendation_queue_decision_support_reports.sql`
- Create: `docs/action-gated-queue-decision-support-db-persistence.md`
- Create: `tests/test_action_gated_queue_decision_support_db_persistence_scope.py`
- Modify: `.env.example`
- Modify: `tests/test_supabase_cycle_snapshot_config.py`

- [ ] **Step 1: Write failing config/migration/scope tests**

Env vars:

```python
POLYMARKET_ALPHA_LAB_ACTION_GATED_QUEUE_DECISION_SUPPORT_DB_ENABLED
POLYMARKET_ALPHA_LAB_ACTION_GATED_QUEUE_DECISION_SUPPORT_DB_DSN
POLYMARKET_ALPHA_LAB_ACTION_GATED_QUEUE_DECISION_SUPPORT_DB_TABLE
```

Default table:

```python
paper_action_gated_strategy_recommendation_queue_decision_support_reports
```

Tests should assert strict boolean parsing, DSN redaction, blank `.env.example` vars, migration columns/checks/indexes, and docs/scope boundaries.

- [ ] **Step 2: Run RED**

Run:

```bash
.venv/bin/python -m pytest tests/test_supabase_action_gated_strategy_recommendation_queue_decision_support_config.py tests/test_action_gated_queue_decision_support_db_persistence_scope.py -q
```

Expected: import/file failures.

- [ ] **Step 3: Implement config, migration, docs, env example**

Migration columns should include snapshot hash, generated timestamp, priority scalar fields, risk scalar fields, JSON payloads, hard flags, and inserted timestamp. Checks should enforce JSON object payloads, risk status/next step pairing, nonnegative counts/notional/scores, and hard flags.

- [ ] **Step 4: Run GREEN**

Run:

```bash
.venv/bin/python -m pytest tests/test_supabase_action_gated_strategy_recommendation_queue_decision_support_config.py tests/test_action_gated_queue_decision_support_db_persistence_scope.py tests/test_supabase_cycle_snapshot_config.py::test_env_example_documents_supported_db_variable_names_only -q
```

Expected: all pass.

### Task 4: Integration Verification

- [ ] **Step 1: Run focused tests**

Run:

```bash
.venv/bin/python -m pytest \
  tests/test_action_gated_strategy_recommendation_queue_decision_support*.py \
  tests/test_supabase_action_gated_strategy_recommendation_queue_decision_support_config.py \
  tests/test_action_gated_queue_decision_support_db_persistence_scope.py -q
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

Expected: all pass, CodeGraph up to date, OpenCode `VERDICT: PASS`.
