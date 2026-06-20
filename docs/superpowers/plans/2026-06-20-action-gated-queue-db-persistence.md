# Action-Gated Queue DB Persistence Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Persist paper-only action-gated strategy recommendation queue reports to local Supabase/Postgres with deterministic round-trip codecs and redacted process-boundary configuration.

**Architecture:** Keep `action_gated_strategy_recommendation_queue` pure and DB-free. Add a DB row codec, DB-API store, psycopg adapter, Supabase env config, migration, and optional CLI/runtime sink wiring as separate boundary modules. Persist ready, watch, and blocked queue reports as durable audit evidence without introducing live trading, auth, wallet, account, order, or exchange mutation surfaces.

**Tech Stack:** Python dataclasses, json, hashlib, Decimal string encoding, DB-API style cursors, psycopg optional adapter, Supabase/Postgres SQL migrations, pytest fake connections.

---

## File Structure

- Create `supabase/migrations/20260620000000_action_gated_strategy_recommendation_queue_reports.sql`
  - Defines report table for durable action-gated queue artifacts.
- Create `src/polymarket_alpha_lab/action_gated_strategy_recommendation_queue_db_row.py`
  - Converts exact report objects to canonical DB rows and back.
- Create `src/polymarket_alpha_lab/action_gated_strategy_recommendation_queue_store.py`
  - DB-API insert/load functions with safe table validation and parameterized SQL.
- Create `src/polymarket_alpha_lab/action_gated_strategy_recommendation_queue_psycopg.py`
  - Thin optional psycopg adapter for connect/commit/rollback/close and Jsonb wrapping.
- Create `src/polymarket_alpha_lab/supabase_action_gated_strategy_recommendation_queue_config.py`
  - Default-off env config with DSN redaction and table validation.
- Create tests for each new module:
  - `tests/test_action_gated_strategy_recommendation_queue_db_row.py`
  - `tests/test_action_gated_strategy_recommendation_queue_store.py`
  - `tests/test_action_gated_strategy_recommendation_queue_psycopg.py`
  - `tests/test_supabase_action_gated_strategy_recommendation_queue_config.py`
  - `tests/test_action_gated_strategy_recommendation_queue_db_scope.py`
- Modify `.env.example`
  - Add blank DB env variables only.
- Modify `docs/strategy-recommendation-layer.md`
  - Document durable DB audit path.

## Task 1: Migration And Env Config

**Files:**
- Create: `supabase/migrations/20260620000000_action_gated_strategy_recommendation_queue_reports.sql`
- Create: `src/polymarket_alpha_lab/supabase_action_gated_strategy_recommendation_queue_config.py`
- Create: `tests/test_supabase_action_gated_strategy_recommendation_queue_config.py`
- Modify: `.env.example`

- [ ] **Step 1: Write failing env config tests**

Cover:
- disabled by default;
- enabled requires DSN but error/repr does not echo DSN;
- padded DSN is rejected without echoing it;
- enabled values are strict: `""`, `0`, `false`, `1`, `true`;
- table name defaults to `paper_action_gated_strategy_recommendation_queue_reports`;
- table names must be lowercase identifiers with optional schema prefix;
- `.env.example` contains blank DB vars and no sample DSN.

- [ ] **Step 2: Implement env config**

Expose:
- `SupabaseActionGatedStrategyRecommendationQueueConfig`
- `from_action_gated_strategy_recommendation_queue_db_env`

Env vars:
- `POLYMARKET_ALPHA_LAB_ACTION_GATED_QUEUE_DB_ENABLED`
- `POLYMARKET_ALPHA_LAB_ACTION_GATED_QUEUE_DB_DSN`
- `POLYMARKET_ALPHA_LAB_ACTION_GATED_QUEUE_DB_TABLE`

- [ ] **Step 3: Add SQL migration**

Create table:
- `public.paper_action_gated_strategy_recommendation_queue_reports`

Columns:
- `report_sha256 text primary key`
- `generated_at timestamptz not null`
- `config_version text not null`
- `source_config_version text not null`
- `action_status text not null`
- `recommended_next_step text not null`
- `candidate_count integer not null`
- `ready_count integer not null`
- `watch_count integer not null`
- `blocked_count integer not null`
- `total_ready_notional numeric not null`
- `reason_code_counts jsonb not null`
- `payload jsonb not null`
- hard flags as true checks
- `inserted_at timestamptz not null default now()`

Indexes:
- `generated_at desc`
- `(source_config_version, generated_at desc)`
- `(action_status, generated_at desc)`
- `(recommended_next_step, generated_at desc)`
- `(source_config_version, action_status, generated_at desc, inserted_at desc, report_sha256 desc)`

Checks:
- SHA-256 report id shape;
- action-status enum and recommended-next-step enum;
- action-status/recommended-next-step pairing;
- nonnegative counts and notional;
- `candidate_count = ready_count + watch_count + blocked_count`;
- watch/blocked reports stay empty with zero ready notional;
- JSON object payload columns;
- hard flags are true.

## Task 2: DB Row Codec

**Files:**
- Create: `src/polymarket_alpha_lab/action_gated_strategy_recommendation_queue_db_row.py`
- Create: `tests/test_action_gated_strategy_recommendation_queue_db_row.py`
- Create: `tests/test_action_gated_strategy_recommendation_queue_db_scope.py`

- [ ] **Step 1: Write failing row codec tests**

Use real ready and watch action-gated reports. Assert:
- exact report type required;
- false hard flags rejected;
- canonical SHA is deterministic;
- payload encodes `Decimal` as strings and datetimes as UTC ISO strings;
- no floats appear in payload;
- DB row round-trips to an exact typed report;
- ready/watch/blocked counts and `total_ready_notional` surface as row fields.

- [ ] **Step 2: Implement codec**

Expose:
- `PaperActionGatedStrategyRecommendationQueueDbRow`
- `paper_action_gated_strategy_recommendation_queue_report_to_db_row`
- `paper_action_gated_strategy_recommendation_queue_report_from_db_row`

Keep this module pure: no DB imports, no psycopg, no env reads, no network.

## Task 3: DB-API Store

**Files:**
- Create: `src/polymarket_alpha_lab/action_gated_strategy_recommendation_queue_store.py`
- Create: `tests/test_action_gated_strategy_recommendation_queue_store.py`

- [ ] **Step 1: Write failing fake-DB tests**

Cover:
- insert uses parameterized SQL;
- insert uses `ON CONFLICT (report_sha256) DO NOTHING`;
- unsafe table names rejected before cursor creation;
- cursor is closed;
- store does not commit;
- load supports optional `source_config_version`, `action_status`, and `limit`;
- load orders by `generated_at desc, inserted_at desc, report_sha256 desc`;
- load handles dict, namedtuple-like, and positional rows.

- [ ] **Step 2: Implement DB-API store**

Expose:
- `DEFAULT_ACTION_GATED_STRATEGY_RECOMMENDATION_QUEUE_TABLE`
- `insert_paper_action_gated_strategy_recommendation_queue_report`
- `load_paper_action_gated_strategy_recommendation_queue_reports`

## Task 4: Psycopg Adapter

**Files:**
- Create: `src/polymarket_alpha_lab/action_gated_strategy_recommendation_queue_psycopg.py`
- Create: `tests/test_action_gated_strategy_recommendation_queue_psycopg.py`

- [ ] **Step 1: Write failing adapter tests**

Cover:
- lazy import of psycopg;
- missing psycopg error mentions install extra, not DSN;
- successful insert/load commits/closes;
- failure rolls back/closes and does not echo DSN;
- dict/list params are wrapped in Jsonb.

- [ ] **Step 2: Implement adapter**

Expose:
- `insert_paper_action_gated_strategy_recommendation_queue_report_with_psycopg`
- `load_paper_action_gated_strategy_recommendation_queue_reports_with_psycopg`

## Task 5: CLI/Runtime Sink Wiring

**Files:**
- Modify only after Tasks 1-4 are green:
  - `src/polymarket_alpha_lab/cli.py`
  - `tests/test_cli.py`
  - a dedicated CLI scope test if needed

- [ ] **Step 1: Add opt-in persistence without changing reducer behavior**

The runtime should persist generated action-gated queue reports only when the new DB env config is enabled. It must not persist by default.

- [ ] **Step 2: Preserve redaction and injection**

Tests must prove:
- injected sink receives DSN/table/report;
- disabled env does not call sink;
- sink errors redact DSN;
- watch/blocked reports are persisted as audit artifacts;
- no live trading/account/order surfaces are added.

## Task 6: Durable Audit Documentation

**Files:**
- Modify: `docs/strategy-recommendation-layer.md`

- [ ] **Step 1: Document DB audit path**

Add a high-level note that action-gated queue reports may be persisted as
local Supabase/Postgres audit artifacts for readonly review/replay/research.
State explicitly that persisted rows remain paper-only evidence records, not
live trade approvals, order intents, signed payloads, account reads, wallet
interactions, or exchange mutations.

## Verification

Run:

```bash
.venv/bin/python -m pytest tests/test_action_gated_strategy_recommendation_queue_db_row.py tests/test_action_gated_strategy_recommendation_queue_store.py tests/test_action_gated_strategy_recommendation_queue_psycopg.py tests/test_supabase_action_gated_strategy_recommendation_queue_config.py tests/test_action_gated_strategy_recommendation_queue_db_scope.py -q
.venv/bin/python -m pytest -q
.venv/bin/python -m compileall -q src tests
git diff --check
codegraph sync && codegraph status .
opencode run --model zhipuai-coding-plan/glm-5.2 --variant max --dir /home/ubuntu/polymarket-alpha-lab "<review prompt>"
```

## Self-Review

- Spec coverage: The plan covers migration/env config, pure codec, DB-API store, psycopg adapter, optional CLI/runtime sink wiring, docs, tests, OpenCode review, and push.
- Placeholder scan: No TBD/TODO/fill-in-later placeholders remain.
- Type consistency: Names stay anchored to action-gated strategy recommendation queue and avoid package-root exports.
