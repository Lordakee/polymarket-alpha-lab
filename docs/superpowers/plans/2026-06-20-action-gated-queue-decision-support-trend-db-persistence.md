# Action-Gated Queue Decision-Support Trend DB Persistence Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Persist action-gated decision-support trend summaries to Supabase/Postgres without duplicating source priority/risk payloads.

**Architecture:** This node is a library-only Phase 1 persistence foundation. It stores a compact trend scalar summary plus an ordered source manifest that references existing decision-support snapshot hashes. It does not add CLI wiring, runtime sinks, source loaders, report hydration, live trading, auth, wallet, account, order, signing, submission, cancellation, replacement, or exchange mutation.

**Tech Stack:** Python frozen dataclasses, DB-API store functions, optional psycopg wrapper, Supabase SQL migration, pytest, CodeGraph.

## Global Constraints

- Phase 1 boundary remains strict: no live trading, auth, wallet, private keys, account reads, order construction, signing, submission, cancellation, replacement, exchange mutation, or live execution.
- Use short Postgres identifiers. Table and index identifier parts must be 63 bytes or less.
- Use table `paper_action_gated_queue_decision_support_trend_reports` and source table `paper_action_gated_queue_decision_support_trend_sources`.
- Do not persist full priority/risk payloads again; those live in `paper_action_gated_strategy_recommendation_queue_decision_support_reports`.
- Do not persist the full trend payload as the first-node primary durable object.
- Persist trend scalar summary fields, JSON count maps, reason rows, hard flags, and ordered source hashes.
- The row codec API must receive both `trend_report` and `snapshot_pairs`, rebuild the trend from the source pairs, and reject mismatches.
- Store loading returns DB row/manifest dataclasses, not hydrated `PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendReport`.
- Keep all DSN values redacted in reprs and exception messages.
- Do not add package-root exports unless a later node requires them.
- Pushing is allowed only when the active session includes explicit user authorization to publish green reviewed nodes to GitHub.

---

### Task 1: Trend Manifest Row Codec

**Files:**
- Create: `src/polymarket_alpha_lab/action_gated_strategy_recommendation_queue_decision_support_trend_db_row.py`
- Test: `tests/test_action_gated_strategy_recommendation_queue_decision_support_trend_db_row.py`

**Interfaces:**
- Consumes:
  - `PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendReport`
  - caller-supplied `(PaperActionGatedStrategyRecommendationQueuePriorityReport, PaperActionGatedStrategyRecommendationQueueRiskReport)` pairs
  - `paper_action_gated_strategy_recommendation_queue_decision_support_to_db_row(...)`
- Produces:
  - `ACTION_GATED_QUEUE_DECISION_SUPPORT_TREND_SCHEMA_VERSION = "action-gated-queue-decision-support-trend-v1"`
  - `PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendDbRow`
  - `PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendSourceDbRow`
  - `PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendDbRows`
  - `paper_action_gated_strategy_recommendation_queue_decision_support_trend_to_db_rows(trend_report, snapshot_pairs) -> PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendDbRows`
  - `paper_action_gated_strategy_recommendation_queue_decision_support_trend_from_db_rows(db_rows) -> PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendDbRows`

**Row fields:**
- Trend row:
  - `trend_sha256: str`
  - `trend_schema_version: str`
  - `source_window_sha256: str`
  - `generated_at: datetime`
  - `source_snapshot_count: int`
  - `first_generated_at: datetime | None`
  - `latest_generated_at: datetime | None`
  - `latest_risk_status: str | None`
  - `risk_pass_count: int`
  - `risk_watch_count: int`
  - `risk_blocked_count: int`
  - `consecutive_latest_watch_count: int`
  - `consecutive_latest_blocked_count: int`
  - `duplicate_generated_at_count: int`
  - `ready_notional_first: Decimal | None`
  - `ready_notional_latest: Decimal | None`
  - `ready_notional_delta: Decimal | None`
  - `top_priority_score_first: Decimal | None`
  - `top_priority_score_latest: Decimal | None`
  - `top_priority_score_delta: Decimal | None`
  - `average_priority_score_first: Decimal | None`
  - `average_priority_score_latest: Decimal | None`
  - `average_priority_score_delta: Decimal | None`
  - `source_queue_count_first: int | None`
  - `source_queue_count_latest: int | None`
  - `source_queue_count_delta: int | None`
  - `latest_reason_code_counts_json: dict[str, int]`
  - `total_reason_code_counts_json: dict[str, int]`
  - `repeated_reason_code_counts_json: dict[str, int]`
  - `reason_code_rows_json: list[dict[str, object]]`
  - `paper_only: bool = True`
  - `report_only: bool = True`
  - `readonly: bool = True`
- Source row:
  - `trend_sha256: str`
  - `trend_ordinal: int`
  - `source_input_position: int`
  - `snapshot_sha256: str`
  - `source_generated_at: datetime`
  - `paper_only: bool = True`
  - `report_only: bool = True`
  - `readonly: bool = True`
- Aggregate:
  - `trend_row: PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendDbRow`
  - `source_rows: tuple[PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendSourceDbRow, ...]`

- [ ] **Step 1: Write failing codec tests**

Cover canonical serialization, hashes, source manifest ordering, empty trend shape, no floats, false flags, mismatched trend/source pairs, direct row invariant revalidation, and pure codec boundary.

- [ ] **Step 2: Run RED**

```bash
.venv/bin/python -m pytest tests/test_action_gated_strategy_recommendation_queue_decision_support_trend_db_row.py -q
```

Expected: import/module failures until implementation exists.

- [ ] **Step 3: Implement codec**

Implementation rules:
- Strict exact-type checks for trend reports and source pairs.
- Rebuild expected trend with `build_paper_action_gated_strategy_recommendation_queue_decision_support_trend_report(snapshot_pairs, generated_at=trend_report.generated_at)`.
- Require rebuilt trend equals supplied trend.
- Compute source `snapshot_sha256` by converting each source pair through the existing decision-support DB row codec.
- Build source rows in trend summary order using `summary.input_position`.
- Compute `source_window_sha256` over ordered `trend_ordinal`, `source_input_position`, and `snapshot_sha256`.
- Compute `trend_sha256` over schema version, source window hash, and scalar summary fields excluding operational `inserted_at`.
- Reject floats recursively in JSON-like maps.
- Normalize count tuples into JSON objects only after checking canonical counts.
- Recompute and validate row/manifest consistency in `__post_init__` and from-db recovery.

- [ ] **Step 4: Run GREEN**

```bash
.venv/bin/python -m pytest tests/test_action_gated_strategy_recommendation_queue_decision_support_trend_db_row.py -q
```

### Task 2: DB-API Store And psycopg Wrapper

**Files:**
- Create: `src/polymarket_alpha_lab/action_gated_strategy_recommendation_queue_decision_support_trend_store.py`
- Create: `src/polymarket_alpha_lab/action_gated_strategy_recommendation_queue_decision_support_trend_psycopg.py`
- Test: `tests/test_action_gated_strategy_recommendation_queue_decision_support_trend_store.py`
- Test: `tests/test_action_gated_strategy_recommendation_queue_decision_support_trend_psycopg.py`

**Interfaces:**
- Produces:
  - `DEFAULT_ACTION_GATED_QUEUE_DECISION_SUPPORT_TREND_REPORTS_TABLE = "paper_action_gated_queue_decision_support_trend_reports"`
  - `DEFAULT_ACTION_GATED_QUEUE_DECISION_SUPPORT_TREND_SOURCES_TABLE = "paper_action_gated_queue_decision_support_trend_sources"`
  - `insert_paper_action_gated_strategy_recommendation_queue_decision_support_trend_db_rows(connection, trend_report, snapshot_pairs, *, reports_table_name=..., sources_table_name=...)`
  - `load_paper_action_gated_strategy_recommendation_queue_decision_support_trend_db_rows(connection, *, latest_risk_status=None, limit=None, reports_table_name=..., sources_table_name=...)`
  - psycopg wrappers with `_with_psycopg` suffix for insert/load.

- [ ] **Step 1: Write failing store and psycopg tests**

Store tests should use fake companion row modules like existing store tests, validate parameterized SQL, no commit/rollback in DB-API store, table validation before cursor creation, source-row insert, load grouping by trend hash, and load sorting by `generated_at desc, inserted_at desc, trend_sha256 desc`.

psycopg tests should verify lazy import, Jsonb wrapping for dict/list params, commit/rollback/close, and DSN redaction.

- [ ] **Step 2: Implement store**

Rules:
- Validate table names before cursor creation.
- Accept optional schema prefix and require each identifier part length `<= 63`.
- Insert trend row first with `ON CONFLICT (trend_sha256) DO NOTHING`.
- Insert source rows with `ON CONFLICT (trend_sha256, trend_ordinal) DO NOTHING`.
- Use only `%s` placeholders.
- Load report rows and source rows separately, then group source rows by `trend_sha256`.
- Return `tuple[PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendDbRows, ...]`.

- [ ] **Step 3: Implement psycopg wrapper**

Rules:
- Importing module must not import psycopg.
- Lazy import `psycopg` and `psycopg.types.json.Jsonb`.
- Wrap dict/list SQL parameters recursively at the adapter boundary.
- Commit on success, rollback on store failure, close always.
- Never echo DSN values in exception text.

- [ ] **Step 4: Run GREEN**

```bash
.venv/bin/python -m pytest tests/test_action_gated_strategy_recommendation_queue_decision_support_trend_store.py tests/test_action_gated_strategy_recommendation_queue_decision_support_trend_psycopg.py -q
```

### Task 3: Supabase Config, Migration, Env, And Docs

**Files:**
- Create: `src/polymarket_alpha_lab/supabase_action_gated_strategy_recommendation_queue_decision_support_trend_config.py`
- Create: `tests/test_supabase_action_gated_strategy_recommendation_queue_decision_support_trend_config.py`
- Create: `supabase/migrations/20260620000003_action_gated_queue_decision_support_trend_reports.sql`
- Modify: `.env.example`
- Modify: `docs/action-gated-queue-decision-support.md`
- Modify: `docs/superpowers/plans/2026-06-20-action-gated-queue-decision-support-trend-db-persistence.md`

**Interfaces:**
- Env vars:
  - `POLYMARKET_ALPHA_LAB_ACTION_GATED_QUEUE_DECISION_SUPPORT_TREND_DB_ENABLED`
  - `POLYMARKET_ALPHA_LAB_ACTION_GATED_QUEUE_DECISION_SUPPORT_TREND_DB_DSN`
  - `POLYMARKET_ALPHA_LAB_ACTION_GATED_QUEUE_DECISION_SUPPORT_TREND_DB_REPORTS_TABLE`
  - `POLYMARKET_ALPHA_LAB_ACTION_GATED_QUEUE_DECISION_SUPPORT_TREND_DB_SOURCES_TABLE`
- Config:
  - `SupabaseActionGatedStrategyRecommendationQueueDecisionSupportTrendConfig`
  - `from_action_gated_strategy_recommendation_queue_decision_support_trend_db_env(...)`

- [ ] **Step 1: Write failing config/migration tests**

Cover strict enabled values, DSN redaction, optional schema table validation, 63-byte identifier guard, `.env.example` blank vars, migration table names, columns, checks, foreign key, indexes, and no sample DSN.

- [ ] **Step 2: Implement config and migration**

Migration rules:
- Create reports and sources tables with short names.
- Source table FK references existing `public.paper_action_gated_strategy_recommendation_queue_decision_support_reports(snapshot_sha256)`.
- Reports table has `trend_sha256` primary key and unique `(trend_schema_version, source_window_sha256)`.
- Empty/non-empty constraints mirror the reducer's nullable fields.
- JSON count columns are objects and `reason_code_rows` is an array.
- Index names stay under 63 bytes.

- [ ] **Step 3: Update docs**

Document that trend DB persistence stores scalar summaries plus ordered source snapshot references, not duplicate priority/risk payloads or full trend hydration. State CLI/runtime wiring is deferred.

- [ ] **Step 4: Run GREEN**

```bash
.venv/bin/python -m pytest tests/test_supabase_action_gated_strategy_recommendation_queue_decision_support_trend_config.py tests/test_docs_action_gated_queue_decision_support_scope.py -q
```

### Task 4: Integration Review And Push

**Files:**
- Only the files listed in Tasks 1-3 unless review finds a concrete defect.

- [ ] **Step 1: Focused verification**

```bash
.venv/bin/python -m pytest tests/test_action_gated_strategy_recommendation_queue_decision_support_trend_db_row.py tests/test_action_gated_strategy_recommendation_queue_decision_support_trend_store.py tests/test_action_gated_strategy_recommendation_queue_decision_support_trend_psycopg.py tests/test_supabase_action_gated_strategy_recommendation_queue_decision_support_trend_config.py tests/test_docs_action_gated_queue_decision_support_scope.py -q
```

- [ ] **Step 2: Full verification**

```bash
.venv/bin/python -m pytest -q
.venv/bin/python -m compileall -q src tests
git diff --check
codegraph sync
codegraph status .
```

- [ ] **Step 3: OpenCode review**

```bash
opencode run --model zhipuai-coding-plan/glm-5.2 --variant max --dir /home/ubuntu/polymarket-alpha-lab "<review prompt>"
```

- [ ] **Step 4: Fix Critical or Important findings and re-run verification**

No Critical or Important findings may remain.

- [ ] **Step 5: Commit and push only with explicit user authorization**

```bash
git add <task-files>
git commit -m "Add action-gated decision support trend DB persistence"
```

Push only when the active session includes explicit user authorization to publish green reviewed nodes to GitHub; otherwise leave the commit local and ask for confirmation.
