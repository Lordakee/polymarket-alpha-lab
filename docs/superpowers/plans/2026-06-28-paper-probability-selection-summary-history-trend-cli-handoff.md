# Paper Probability Selection Summary History Trend CLI Handoff

## Purpose

This node adds a read-only CLI entry point for the existing probability selection
summary history trend reducer:

```bash
polymarket-alpha-lab paper-probability-selection-summary-history-trend --limit 25
```

The command reads persisted `PaperProbabilitySelectionSummaryHistoryReport` rows
from the existing local Supabase/Postgres history table, reverses the newest-first
readback into chronological reducer input, builds a
`PaperProbabilitySelectionSummaryHistoryTrendReport`, and prints aggregate trend
metrics only.

## Changed Files

- `src/polymarket_alpha_lab/cli.py`
  - Added `PaperProbabilitySelectionSummaryHistoryTrendRunner`.
  - Added `paper-probability-selection-summary-history-trend`.
  - Parser surface is only `--limit`; parser uses `allow_abbrev=False`.
  - Limit validation happens before env reads, runner calls, or DB connection.
  - Runtime DB config is env-only via
    `from_paper_probability_selection_summary_history_db_env()`.
  - Default helper connects with `psycopg.connect(dsn, autocommit=True)`, calls
    `load_paper_probability_selection_summary_history_reports`, reverses
    newest-first rows to chronological order, and calls
    `build_paper_probability_selection_summary_history_trend_report`.
  - The helper closes the connection in `finally` and does not write, commit,
    rollback, insert, update, delete, or create durable files.
  - Error redaction now covers DSN/table, payload/question/market slug, market
    detail fields, secret-like fields, wallet/account/order fields, and SHA-256
    hashes.
  - Trend stdout uses aggregate fields only and sanitizes reason-code-like output
    before printing.

- `tests/test_cli_paper_probability_selection_summary_history_trend.py`
  - Covers help visibility, forbidden flags, disabled DB config, enabled DB
    without DSN, positive limit validation before side effects, env-only config,
    runner injection, aggregate output, expanded redaction, case-insensitive
    token/secret variant redaction, reason-code output sanitization, and default
    DB readback ordering/close behavior.

- `tests/test_cli_paper_probability_selection_summary_history_trend_scope.py`
  - AST guards for parser surface, command branch calls, read-only helper imports
    and calls, forbidden persistence/trading/file-backed surfaces, and aggregate
    summary fields.

## Constraints Preserved

- Paper-only/report-only/read-only boundary.
- No live trading.
- No auth, wallet, account, private-key, signing, order placement, cancel,
  replace, exchange mutation, or account reconciliation surface.
- No ranking, sizing, allocation, recommendation, approval workflow, or strategy
  promotion behavior.
- Durable project data remains local Supabase/Postgres only.
- No SQLite, JSONL, Redis, Mongo, SQLAlchemy, generic DB abstraction, hosted DB
  assumption, or file-backed durable store.
- No CLI DSN/table flags; DB configuration remains env-only.
- No `--persist` path for this command.
- CodeGraph exists and was used/synced.

## Review Notes

Parallel read-only subagents reviewed the node. Initial reviews found no parser,
DB-readback, or phase-boundary blockers. A later output-safety review found two
real issues before commit:

- Expanded sensitive keys such as `market_question`, `market_details`,
  `password`, `token`, `api_key`, `private_key`, `authorization`, and
  `credential` were not redacted from command error messages.
- Runner- or store-sourced reason codes could be printed verbatim even if a
  polluted canonical reason code contained market, credential, wallet, account,
  order, token, or secret-like fragments.
- A final verifier found that sensitive-key redaction still needed to be
  case-insensitive and cover common token/secret variants such as
  `access_token`, `refresh_token`, `auth_token`, `bearer_token`, `jwt_token`,
  `client_secret`, and `secret_key`.

Both issues were fixed with regression tests before final verification.

## Verified Commands

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' PYTHONPATH=.:src python3 -m pytest -q tests/test_cli_paper_probability_selection_summary_history_trend.py tests/test_cli_paper_probability_selection_summary_history_trend_scope.py
```

Result: `28 passed in 2.38s`.

After the final case-insensitive token/secret variant redaction fix, this command
was rerun.

Result: `29 passed in 2.25s`.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' PYTHONPATH=.:src python3 -m pytest -q tests/test_cli_paper_probability_selection_summary_history.py tests/test_cli_paper_probability_selection_summary_history_scope.py tests/test_cli_paper_probability_selection_summary_history_trend.py tests/test_cli_paper_probability_selection_summary_history_trend_scope.py
```

Result: `63 passed in 4.07s`.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' PYTHONPATH=.:src python3 -m pytest -q tests/test_cli_paper_probability_selection_summary_history_trend.py tests/test_cli_paper_probability_selection_summary_history_trend_scope.py tests/test_paper_probability_selection_summary_history_trend.py tests/test_paper_probability_selection_summary_history_trend_scope.py tests/test_paper_probability_selection_summary_history.py tests/test_paper_probability_selection_summary_history_store.py tests/test_paper_probability_selection_summary_history_psycopg.py tests/test_supabase_paper_probability_selection_summary_history_config.py
```

Result before final redaction hardening: `116 passed in 3.61s`.

After the final redaction hardening, the broader CLI/history/store/config slice
was run:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' PYTHONPATH=.:src python3 -m pytest -q tests/test_cli_paper_probability_selection_summary_history.py tests/test_cli_paper_probability_selection_summary_history_scope.py tests/test_cli_paper_probability_selection_summary_history_trend.py tests/test_cli_paper_probability_selection_summary_history_trend_scope.py tests/test_paper_probability_selection_summary_history_trend.py tests/test_paper_probability_selection_summary_history_trend_scope.py tests/test_paper_probability_selection_summary_history.py tests/test_paper_probability_selection_summary_history_store.py tests/test_paper_probability_selection_summary_history_psycopg.py tests/test_supabase_paper_probability_selection_summary_history_config.py
```

Result: `152 passed in 4.78s`.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' PYTHONPATH=.:src python3 -m pytest -q
```

Result before final redaction hardening: `9934 passed, 1 skipped in 66.55s`.

After final redaction hardening, full suite was rerun.

Result: `9935 passed, 1 skipped in 66.09s`.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:src python3 -m compileall -q src tests
git diff --check
python3 -m polymarket_alpha_lab --help | rg "paper-probability-selection-summary-history-trend|paper-probability-selection-summary-history"
codegraph sync
```

Results before final redaction hardening: compile passed, diff check passed,
help listed both commands, and CodeGraph reported `Already up to date`.

After final redaction hardening:

- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:src python3 -m compileall -q src tests`
  passed.
- `git diff --check` passed.
- `python3 -m polymarket_alpha_lab --help | rg "paper-probability-selection-summary-history-trend|paper-probability-selection-summary-history"`
  listed both commands.
- `codegraph sync` synced 2 changed files.

```bash
git diff -- . ':(exclude).codegraph/**' | rg -n "ghp_[A-Za-z0-9_]+|github_pat_[A-Za-z0-9_]+|sk-[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|BEGIN (RSA|OPENSSH|EC|DSA)? ?PRIVATE KEY"
```

Result: no matches; `rg` exited `1`.

Boundary scan for live trading, alternate persistence, and secret-like terms
only hit the newly added redaction/test literals, not production mutation or
alternate persistence paths.

## Opencode Review

Required before commit:

```bash
opencode run --format json --model zhipuai-coding-plan/glm-5.2 --variant max --dir /home/ubuntu/polymarket-alpha-lab 'DO NOT modify/create/delete ANY file. Read /tmp/polymarket-alpha-lab-review/paper-probability-selection-summary-history-trend-cli-review-package.md and perform a final code/plan review for the paper probability selection summary history trend CLI/readback node. Check parser surface, read-only/env-only local Supabase/Postgres behavior, no persist/live/auth/wallet/order/signing/exchange mutation, no durable file/SQLite/JSONL/Redis/Mongo/SQLAlchemy, error redaction, aggregate-only output, tests, verification evidence, and release readiness. Return blockers first.' > /tmp/polymarket-alpha-lab-review/paper-probability-selection-summary-history-trend-cli-opencode-review.jsonl
```

## Repo Status At Handoff Creation

Uncommitted intended files:

- `src/polymarket_alpha_lab/cli.py`
- `tests/test_cli_paper_probability_selection_summary_history_trend.py`
- `tests/test_cli_paper_probability_selection_summary_history_trend_scope.py`
- `docs/superpowers/plans/2026-06-28-paper-probability-selection-summary-history-trend-cli-handoff.md`

## Next Recommended Node

Continue CLI/readback integration for the remaining report-only observability
modules one command family at a time. The next good target is autonomous market
scorer history/load readback, keeping the same pattern: local Supabase/Postgres
env-only config, read-only default behavior, aggregate-only output, no persist
flag unless separately planned, and no live trading/auth/order surfaces.
