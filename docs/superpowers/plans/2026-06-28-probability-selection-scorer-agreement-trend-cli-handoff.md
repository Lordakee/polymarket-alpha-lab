# Probability Selection Scorer Agreement Trend CLI Handoff

Date: 2026-06-28

## Purpose

This node adds a read-only CLI entry point for the existing probability
selection/scorer agreement trend reducer:

```bash
polymarket-alpha-lab probability-selection-scorer-agreement-trend --limit 25
```

The command reads persisted aggregate
`ProbabilitySelectionScorerAgreementReport` rows from the existing local
Supabase/Postgres agreement-report table, reverses newest-first DB readback into
chronological reducer input, builds a
`ProbabilitySelectionScorerAgreementTrendReport`, and prints aggregate trend
metrics only.

## Implementation Status

Implemented in this node:

- `src/polymarket_alpha_lab/cli.py`
  - registers `probability-selection-scorer-agreement-trend`
  - adds injectable `probability_selection_scorer_agreement_trend_runner`
  - reads agreement DB config from env only
  - validates local Supabase/Postgres DSNs before connecting or running
  - requires injected runners to return the exact
    `ProbabilitySelectionScorerAgreementTrendReport` type before printing
  - loads persisted agreement reports with `psycopg.connect(..., autocommit=True)`
  - reverses newest-first DB readback into chronological reducer input
  - prints aggregate-only trend fields with sanitized reason-code output
  - redacts DSNs, DB hosts, table names, payloads, hashes, and identity-like
    fields on failure
- `tests/test_cli_probability_selection_scorer_agreement_trend.py`
  - covers CLI behavior, runner injection, config/env failures, remote DSN
    rejection, error redaction, output sanitization, readback ordering, and
    connection lifecycle, including load/build failures after connect
- `tests/test_cli_probability_selection_scorer_agreement_trend_scope.py`
  - locks parser surface, branch/helper boundaries, read-only DB behavior,
    redaction helper usage, and aggregate-only summary fields
- `README.md`
  - documents the new user-facing read-only trend command beside the existing
    probability selection/scorer agreement command
- `docs/superpowers/plans/2026-06-28-probability-selection-scorer-agreement-trend-cli-handoff.md`
  - records this implementation and verification boundary

## Current Context

- The pure trend reducer already exists in
  `src/polymarket_alpha_lab/probability_selection_scorer_agreement_trend.py`.
- Agreement report DB row/store/psycopg/env boundaries already exist from the
  previous trend/persistence node:
  - `src/polymarket_alpha_lab/probability_selection_scorer_agreement_store.py`
  - `src/polymarket_alpha_lab/probability_selection_scorer_agreement_psycopg.py`
  - `src/polymarket_alpha_lab/supabase_probability_selection_scorer_agreement_config.py`
  - `supabase/migrations/20260625000011_probability_selection_scorer_agreement_reports.sql`
- The intended CLI pattern should follow the adjacent read-only history trend
  commands, especially
  `paper-probability-selection-summary-history-trend` and
  `autonomous-market-scorer-history`.
- This node intentionally does not add a trend persistence table. It reads the
  existing persisted aggregate agreement reports and computes the trend in
  memory for stdout.

## CLI Surface

- Command name: `probability-selection-scorer-agreement-trend`
- CLI option: `--limit`, positive integer, default `25`
- Parser uses the existing top-level parser style with abbreviation
  disabled.
- Do not add CLI flags for DSN, table name, persistence, files, live trading,
  auth, wallet, account, private key, signing, order placement, cancellation,
  replacement, or execution.
- Env config is read only after CLI argument validation succeeds.
- Disabled agreement DB config fails cleanly before connecting or running
  the trend reducer.
- Enabled agreement DB config without DSN fails cleanly before connecting
  or running the trend reducer.
- Remote DSNs are rejected before connecting or running. Keep the existing
  local-Postgres/Supabase guard: `localhost`, `127.0.0.1`, `::1`, or explicit
  Unix socket hosts only.

## Environment Variables

Use the existing agreement-report DB env boundary only:

- `POLYMARKET_ALPHA_LAB_PROBABILITY_SELECTION_SCORER_AGREEMENT_DB_ENABLED`
- `POLYMARKET_ALPHA_LAB_PROBABILITY_SELECTION_SCORER_AGREEMENT_DB_DSN`
- `POLYMARKET_ALPHA_LAB_PROBABILITY_SELECTION_SCORER_AGREEMENT_DB_TABLE`

Default table:

- `probability_selection_scorer_agreement_reports`

The command does not introduce a new trend-specific durable table/env boundary
in this node. It reads the existing persisted agreement reports and computes the
trend in memory for stdout.

## Durable Data Boundary

- Durable project data remains local Supabase/Postgres only.
- Do not add SQLite, JSONL, Redis, Mongo, SQLAlchemy, generic durable store
  abstractions, hosted DB assumptions, file-backed caches, or local artifact
  history for production data.
- Do not persist the trend report in this CLI node.
- The DB helper uses `psycopg.connect(dsn, autocommit=True)`, calls
  `load_probability_selection_scorer_agreement_reports`, closes the connection in
  `finally`, and avoids `commit()`, `rollback()`, insert, update, delete, DDL, or
  sink calls.
- Store readback is expected to return newest-first rows; reverse that result
  before calling `build_probability_selection_scorer_agreement_trend_report`.

## Safety Boundary

- This is a read-only, report-only, paper-only observability command.
- Preserve hard flags through config, report construction, CLI output, and
  tests: `paper_only=True`, `report_only=True`, and `readonly=True`.
- No live trading, no CLOB/order endpoints, no order placement/signing,
  cancellation, replacement, or exchange mutation.
- No auth/session mutation, wallet/account/private-key handling, credential
  prompts, or secret logging.
- No market-ranking, allocation, sizing, recommendation promotion, approval
  workflow, or autonomous action behavior.
- The command may read existing local environment configuration but must not
  print DSNs, table names, credentials, raw source rows, payload JSON, report
  hashes, market slugs, condition IDs, questions, market details, wallet/account
  identifiers, auth material, or order-like data.

## Aggregate-Only Output

Stdout includes only aggregate trend report fields:

- command header
- `source_report_count`
- `first_generated_at`
- `latest_generated_at`
- `history_span_seconds`
- `latest_agreement_status`
- `latest_status_streak`
- status counts:
  - `aligned_report_count`
  - `low_overlap_report_count`
  - `gate_blocked_report_count`
  - `missing_inputs_report_count`
  - `insufficient_identifiers_report_count`
- `average_selected_count`
- `average_scorer_candidate_count`
- `trend_status`
- `recommended_next_step`
- sanitized `reason_codes`
- sanitized `recurring_reason_code_counts`

Hard safety flags are preserved through config/report validation, but the CLI
summary does not print them.

Reason-code-like output must be sanitized before printing. Unsafe values should
be replaced with `<redacted-reason-code>`, including non-canonical strings, long
values, hash-like values, and values containing sensitive fragments such as
condition, market slug, payload, hash, token, credential, wallet, account, order,
auth, private key, secret, question, detail, or title terms.

Stderr should use the existing redaction helpers so DSN/table names and
payload/hash/market/condition/auth/wallet/order/signing details cannot leak in
failure paths.

## Implemented Files

- `src/polymarket_alpha_lab/cli.py`
  - Added the command parser branch and runner injection parameter.
  - Added `ProbabilitySelectionScorerAgreementTrendRunner` typing.
  - Added the default read helper, env gating, local DSN validation, redacted
    failure handling, and aggregate-only summary printer.
  - Reuses existing redaction/local-DSN helpers rather than inventing a second
    policy.

- `tests/test_cli_probability_selection_scorer_agreement_trend.py`
  - Covers parser visibility, help text, forbidden flags, disabled DB config,
    enabled DB without DSN, positive limit validation before side effects,
    env-only config, local DSN rejection for remote hosts, runner injection,
    aggregate stdout, reason-code sanitization, redacted failures, default DB
    readback ordering, connection close, `autocommit=True`, and no
    commit/rollback.

- `tests/test_cli_probability_selection_scorer_agreement_trend_scope.py`
  - Adds AST/static guards for parser surface, command branch calls, read-only
    helper imports/calls, forbidden live/auth/wallet/order/file-backed durable
    surfaces, and aggregate-only summary fields.

- `README.md`
  - Documents the read-only trend command and boundaries.

- `docs/superpowers/plans/2026-06-28-probability-selection-scorer-agreement-trend-cli-handoff.md`
  - This handoff.

## Commands To Run

Focused pure trend coverage:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' PYTHONPATH=.:src python3 -m pytest -q \
  tests/test_probability_selection_scorer_agreement_trend.py \
  tests/test_probability_selection_scorer_agreement_trend_scope.py
```

Focused CLI coverage for this node:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' PYTHONPATH=.:src python3 -m pytest -q \
  tests/test_cli_probability_selection_scorer_agreement_trend.py \
  tests/test_cli_probability_selection_scorer_agreement_trend_scope.py
```

Latest result before review: `32 passed in 2.88s`.

Agreement CLI/store adjacency:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' PYTHONPATH=.:src python3 -m pytest -q \
  tests/test_probability_selection_scorer_agreement.py \
  tests/test_probability_selection_scorer_agreement_scope.py \
  tests/test_probability_selection_scorer_agreement_load.py \
  tests/test_probability_selection_scorer_agreement_db_row.py \
  tests/test_probability_selection_scorer_agreement_store.py \
  tests/test_probability_selection_scorer_agreement_psycopg.py \
  tests/test_supabase_probability_selection_scorer_agreement_config.py \
  tests/test_probability_selection_scorer_agreement_db_migration.py \
  tests/test_cli_probability_selection_scorer_agreement.py \
  tests/test_cli_probability_selection_scorer_agreement_scope.py
```

Latest result before review: `223 passed in 6.72s`.

Syntax and diff checks:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:src python3 -m compileall -q src tests
git diff --check
```

Latest result before review: compileall passed, `git diff --check` passed.

Help surface check:

```bash
PYTHONPATH=.:src python3 -m polymarket_alpha_lab --help | rg "probability-selection-scorer-agreement-trend|probability-selection-scorer-agreement"
```

Latest result before review: both `probability-selection-scorer-agreement` and
`probability-selection-scorer-agreement-trend` appeared in top-level help.

Secret scan:

```bash
git diff -- . ':(exclude).codegraph/**' | rg -n "ghp_[A-Za-z0-9_]+|github_pat_[A-Za-z0-9_]+|sk-[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|BEGIN (RSA|OPENSSH|EC|DSA)? ?PRIVATE KEY"
```

Latest result before review: no matches.

Full regression before commit:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' PYTHONPATH=.:src python3 -m pytest -q
```

CodeGraph refresh after implementation changes:

```bash
codegraph sync
```

## Review Gate

Before commit, request an `opencode` review focused on:

- CLI/readback safety boundary.
- Env-only local Supabase/Postgres durable-data rule.
- No live/auth/wallet/order/signing/exchange mutation.
- No durable file/SQLite/JSONL/Redis/Mongo/SQLAlchemy additions.
- Aggregate-only stdout and redacted stderr.
- Correct chronological reducer input from newest-first DB rows.
- Adequacy of CLI, scope, and adjacent agreement tests.

Suggested command:

```bash
opencode run --format json --model zhipuai-coding-plan/glm-5.2 --variant max --dir /home/ubuntu/polymarket-alpha-lab 'DO NOT modify/create/delete ANY file. Review the current uncommitted probability-selection-scorer-agreement-trend CLI/readback node for parser surface, read-only/env-only local Supabase/Postgres behavior, no persist/live/auth/wallet/order/signing/exchange mutation, no durable file/SQLite/JSONL/Redis/Mongo/SQLAlchemy, error redaction, aggregate-only output, chronological reducer input, tests, and release readiness. Return blockers first.'
```

## Repo Status At Handoff Creation

Known status while this handoff was created:

- Target handoff file was newly added and later updated with implementation
  status.
- The implemented node touches README, CLI, CLI behavior tests, CLI scope tests,
  and this handoff.

## Next Steps

- Run the full regression command before commit.
- Run `codegraph sync` only after implementation/source/test changes are made.
- Request the review gate and fix any blocking findings.
- If a later node needs durable trend history, plan it separately with an
  explicit local Supabase/Postgres migration and env boundary; do not fold trend
  persistence into this read-only CLI node.
