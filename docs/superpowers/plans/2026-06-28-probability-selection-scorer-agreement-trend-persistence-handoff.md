# Probability Selection Scorer Agreement Trend/Persistence Handoff

## Objective

Build the next report-only layer for probability-selection/scorer agreement:
pure trend reduction plus aggregate-only local Supabase/Postgres persistence,
then wire env-controlled agreement report persistence into the existing
`probability-selection-scorer-agreement` CLI path.

## Safety Boundary

- Phase remains `paper_only=True`, `report_only=True`, and `readonly=True`.
- No live trading, auth, wallets, private keys, order placement/signing,
  submission, cancellation, replacement, or exchange mutation.
- Durable data is local Supabase/Postgres only. Do not add SQLite, JSONL,
  Redis, Mongo, SQLAlchemy, hosted DB assumptions, or generic durable stores.
- CLI persistence is controlled only by environment config. Do not add
  `--persist`, `--dsn`, `--table`, file, wallet, auth, order, or live flags.
- Persist only aggregate agreement reports: no market slug, question,
  condition id, order, wallet, auth, private key, or source row details.

## Node Changes

- Added pure trend reducer:
  `src/polymarket_alpha_lab/probability_selection_scorer_agreement_trend.py`
  with focused trend and scope tests.
- Added aggregate DB row codec:
  `src/polymarket_alpha_lab/probability_selection_scorer_agreement_db_row.py`
  with deterministic `report_sha256`, strict payload/materialized consistency,
  float rejection, hard-flag validation, and aggregate-only tests.
- Added DB-API store:
  `src/polymarket_alpha_lab/probability_selection_scorer_agreement_store.py`
  with parameterized insert, `ON CONFLICT DO NOTHING`, latest-load filters, and
  no transaction control.
- Added psycopg boundary:
  `src/polymarket_alpha_lab/probability_selection_scorer_agreement_psycopg.py`
  with lazy psycopg imports, JSONB adaptation, `autocommit=True`, and no
  commit/rollback.
- Added local Supabase env config:
  `src/polymarket_alpha_lab/supabase_probability_selection_scorer_agreement_config.py`
  with DSN redaction, enabled/table validation, and no DB connection.
- Added migration:
  `supabase/migrations/20260625000011_probability_selection_scorer_agreement_reports.sql`
  for aggregate report rows, hard flag checks, order/filter indexes, and JSONB
  indexes.
- Updated `src/polymarket_alpha_lab/cli.py` so the agreement CLI can optionally
  persist the aggregate report to local Supabase when the agreement DB env is
  enabled. Existing source DB reads remain local-only and redacted.

## Verification Evidence

- Focused agreement trend/scope tests:
  `PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' PYTHONPATH=.:src python3 -m pytest -q tests/test_probability_selection_scorer_agreement_trend.py tests/test_probability_selection_scorer_agreement_trend_scope.py`
  Evidence: `14 passed`.
- Focused DB row tests:
  `PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' PYTHONPATH=.:src python3 -m pytest -q tests/test_probability_selection_scorer_agreement_db_row.py`
  Evidence: `22 passed`.
- Focused store tests:
  `PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' PYTHONPATH=.:src python3 -m pytest -q tests/test_probability_selection_scorer_agreement_store.py`
  Evidence: `13 passed`.
- Focused Supabase config tests:
  `PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' PYTHONPATH=.:src python3 -m pytest -q tests/test_supabase_probability_selection_scorer_agreement_config.py`
  Evidence: `24 passed`.
- Focused migration tests:
  `PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' PYTHONPATH=.:src python3 -m pytest -q tests/test_probability_selection_scorer_agreement_db_migration.py tests/test_supabase_migration_versions.py`
  Evidence: `5 passed`.
- Focused CLI/psycopg tests:
  `PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' PYTHONPATH=.:src python3 -m pytest -q tests/test_cli_probability_selection_scorer_agreement.py tests/test_cli_probability_selection_scorer_agreement_scope.py tests/test_probability_selection_scorer_agreement_psycopg.py`
  Evidence: `62 passed`.
- Full focused agreement node suite:
  `PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' PYTHONPATH=.:src python3 -m pytest -q tests/test_probability_selection_scorer_agreement.py tests/test_probability_selection_scorer_agreement_scope.py tests/test_probability_selection_scorer_agreement_trend.py tests/test_probability_selection_scorer_agreement_trend_scope.py tests/test_probability_selection_scorer_agreement_db_row.py tests/test_probability_selection_scorer_agreement_store.py tests/test_probability_selection_scorer_agreement_psycopg.py tests/test_supabase_probability_selection_scorer_agreement_config.py tests/test_probability_selection_scorer_agreement_db_migration.py tests/test_probability_selection_scorer_agreement_load.py tests/test_cli_probability_selection_scorer_agreement.py tests/test_cli_probability_selection_scorer_agreement_scope.py tests/test_supabase_migration_versions.py`
  Evidence: `192 passed`.
- Post-review migration/CLI focused suite:
  `PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' PYTHONPATH=.:src python3 -m pytest -q tests/test_probability_selection_scorer_agreement_db_migration.py tests/test_supabase_migration_versions.py tests/test_cli_probability_selection_scorer_agreement.py tests/test_cli_probability_selection_scorer_agreement_scope.py`
  Evidence: `61 passed`.
- Post-review full focused agreement node suite:
  `PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' PYTHONPATH=.:src python3 -m pytest -q tests/test_probability_selection_scorer_agreement.py tests/test_probability_selection_scorer_agreement_scope.py tests/test_probability_selection_scorer_agreement_trend.py tests/test_probability_selection_scorer_agreement_trend_scope.py tests/test_probability_selection_scorer_agreement_db_row.py tests/test_probability_selection_scorer_agreement_store.py tests/test_probability_selection_scorer_agreement_psycopg.py tests/test_supabase_probability_selection_scorer_agreement_config.py tests/test_probability_selection_scorer_agreement_db_migration.py tests/test_probability_selection_scorer_agreement_load.py tests/test_cli_probability_selection_scorer_agreement.py tests/test_cli_probability_selection_scorer_agreement_scope.py tests/test_supabase_migration_versions.py`
  Evidence: `193 passed`.

## Full Verification Evidence

- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:src python3 -m compileall -q src tests`
  Evidence: passed.
- `git diff --check`
  Evidence: passed.
- `PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' PYTHONPATH=.:src python3 -m pytest -q`
  Evidence: `10195 passed, 1 skipped in 72.99s`.
- Post-review `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:src python3 -m compileall -q src tests`
  Evidence: passed.
- Post-review `git diff --check`
  Evidence: passed.
- Post-review `PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' PYTHONPATH=.:src python3 -m pytest -q`
  Evidence: `10196 passed, 1 skipped in 76.94s`.
- Post-review `codegraph sync`
  Evidence: synced 1 changed file after README/migration/test updates.

## Verification Still Required Before Commit

None; commit and push are next.

## OpenCode Review

- First opencode attempt using the default state DB failed before review with
  `SQLiteError: no such column: replacement_seq` from opencode's local state
  database. Isolated `XDG_DATA_HOME` with copied auth fixed the tool issue.
- Review command:
  `XDG_DATA_HOME=/tmp/opencode-review-state-polymarket-agreement opencode run --format json --model zhipuai-coding-plan/glm-5.2 --variant max --dir /home/ubuntu/polymarket-alpha-lab 'DO NOT modify/create/delete ANY file. Review the current uncommitted probability-selection-scorer-agreement trend/persistence node for phase-boundary, local Supabase-only durable data, no live/auth/wallet/order mutation, aggregate-only output/persistence, tests, and migration correctness. Return findings only, ordered by severity.'`
- Evidence: approved with minor findings only. Addressed L1 by adding migration
  `payload ?| array[...]` defense-in-depth against sensitive keys and L2 by
  documenting the env-driven agreement command/persistence surface in README.
  L3 (connection exception chaining) was left unchanged to preserve the current
  DSN-leak-minimizing posture.

## Subagent Note

Earlier handoff reported `/v1/responses` 403 quota/subscription exhaustion for
subagent attempts. This node attempted multiple subagents again; the management
tool returned `not_found` for spawned ids, so main-thread implementation plus
local parallel verification continued without blocking progress.

## Next Work

- Finish full verification, CodeGraph sync, and opencode review.
- Fix any review findings, rerun focused/full verification, then commit and push.
- After this node, use the persisted agreement reports as a local-Supabase input
  for a report-only agreement trend CLI and, later, an autonomous gating signal.
