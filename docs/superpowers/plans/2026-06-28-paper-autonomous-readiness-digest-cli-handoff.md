# Paper Autonomous Readiness Digest CLI Handoff

Date: 2026-06-28

## Summary

This node introduces the `paper-autonomous-readiness-digest` CLI. The CLI reads persisted paper autonomous readiness gate reports from local Supabase/Postgres and prints aggregate readiness evidence for paper-mode evaluation.

The intended output is a readback-style digest of already persisted readiness evidence, not a new scoring source or execution path. It should help operators and follow-on agents quickly inspect whether paper autonomous readiness gates are producing consistent, reviewable evidence over recent runs.

## Safety Boundary

- Paper-only and read-only.
- No live trading.
- No authentication flow changes.
- No wallet access.
- No private key access.
- No order placement, cancellation, mutation, or routing.
- No portfolio mutation.
- No production exchange calls.
- Local Supabase/Postgres only.
- Reads persisted paper autonomous readiness gate reports and prints aggregate evidence.

## Changed Files

Implementation surface from this node:

- `src/polymarket_alpha_lab/cli.py`
  - Registers `paper-autonomous-readiness-digest`.
  - Adds a read-only helper that loads persisted readiness gate reports from local Supabase/Postgres through `psycopg`.
  - Prints aggregate digest status, evidence statuses, and safe reason-code counts only.
  - Applies a bounded read limit of 500 rows before env lookup, runner invocation, import, or DB connect.
  - Hardens CLI error redaction for bare `auth` fields and Python repr-style single-quoted sensitive fields.
- `src/polymarket_alpha_lab/supabase_paper_autonomous_readiness_gate_config.py`
  - Adds the env-bound local Supabase/Postgres config boundary for readiness gate reports.
  - Allows only explicit local Postgres/Supabase DSNs: `localhost`, `127.0.0.1`, `::1`, or explicit Unix socket paths.
- `tests/test_cli_paper_autonomous_readiness_digest.py`
  - Covers command registration, env-backed runner injection, bounded limits, aggregate-only output, safe reason-code output, and redacted failure output.
- `tests/test_cli_paper_autonomous_readiness_digest_scope.py`
  - AST scope checks for read-only parser/helper/summary behavior.
- `tests/test_supabase_paper_autonomous_readiness_gate_config.py`
  - Covers strict env parsing, local-only DSN handling, table-name validation, repr redaction, immutability, and public exports.
- `docs/superpowers/plans/2026-06-28-paper-autonomous-readiness-digest-cli-handoff.md`
  - This handoff.

No live trading, wallet, auth, or order mutation files are touched by this node.

## Verification Known From Handoff

Known focused verification results from the handoff before final closure:

- `pytest tests/test_cli_paper_autonomous_readiness_digest.py`
  - `23 passed`
- `pytest tests/test_supabase_paper_autonomous_readiness_gate_config.py`
  - `52 passed`
- `pytest tests/test_cli_paper_autonomous_readiness_digest.py tests/test_cli_paper_autonomous_readiness_digest_scope.py tests/test_supabase_paper_autonomous_readiness_gate_config.py tests/test_paper_autonomous_readiness_digest.py tests/test_paper_autonomous_readiness_digest_load.py tests/test_paper_autonomous_readiness_digest_scope.py`
  - `94 passed`
- `PYTHONPATH=. pytest tests/test_paper_autonomous_readiness_gate.py tests/test_paper_autonomous_readiness_gate_db_row.py tests/test_paper_autonomous_readiness_gate_store.py tests/test_paper_autonomous_readiness_gate_psycopg.py tests/test_paper_autonomous_readiness_gate_scope.py tests/test_paper_autonomous_readiness_gate_store_scope.py tests/test_paper_autonomous_readiness_gate_psycopg_scope.py tests/test_paper_autonomous_readiness_gate_db_row_scope.py tests/test_docs_paper_autonomous_readiness_gate_scope.py`
  - `99 passed`
- `pytest tests/test_cli_paper_autonomous_readiness_digest.py tests/test_cli_paper_autonomous_readiness_digest_scope.py tests/test_supabase_paper_autonomous_readiness_gate_config.py tests/test_paper_autonomous_readiness_digest.py tests/test_paper_autonomous_readiness_digest_load.py tests/test_paper_autonomous_readiness_digest_scope.py tests/test_cli_autonomous_market_scorer_history.py tests/test_cli_autonomous_market_scorer_history_scope.py tests/test_cli_paper_autonomous_investment_ledger_db_history_health_trend_gate.py tests/test_cli_paper_autonomous_investment_ledger_db_history_health_trend_gate_scope.py`
  - `168 passed`
- `PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' PYTHONPATH=.:src python3 -m pytest -q`
  - `10049 passed, 1 skipped`

Known compile/diff checks:

- `python3 -m py_compile src/polymarket_alpha_lab/cli.py src/polymarket_alpha_lab/supabase_paper_autonomous_readiness_gate_config.py tests/test_cli_paper_autonomous_readiness_digest.py tests/test_supabase_paper_autonomous_readiness_gate_config.py`
  - passed
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:src python3 -m compileall -q src tests`
  - passed
- `git diff --check`
  - passed
- `python3 -m polymarket_alpha_lab paper-autonomous-readiness-digest --help`
  - passed

Recommended verification before closing the implementation branch:

```bash
pytest tests/test_cli_paper_autonomous_readiness_digest.py \
  tests/test_cli_paper_autonomous_readiness_digest_scope.py \
  tests/test_supabase_paper_autonomous_readiness_gate_config.py \
  tests/test_paper_autonomous_readiness_digest.py \
  tests/test_paper_autonomous_readiness_digest_load.py \
  tests/test_paper_autonomous_readiness_digest_scope.py \
  tests/test_cli_autonomous_market_scorer_history.py \
  tests/test_cli_autonomous_market_scorer_history_scope.py \
  tests/test_cli_paper_autonomous_investment_ledger_db_history_health_trend_gate.py \
  tests/test_cli_paper_autonomous_investment_ledger_db_history_health_trend_gate_scope.py

PYTHONPATH=. pytest tests/test_paper_autonomous_readiness_gate.py \
  tests/test_paper_autonomous_readiness_gate_db_row.py \
  tests/test_paper_autonomous_readiness_gate_store.py \
  tests/test_paper_autonomous_readiness_gate_psycopg.py \
  tests/test_paper_autonomous_readiness_gate_scope.py \
  tests/test_paper_autonomous_readiness_gate_store_scope.py \
  tests/test_paper_autonomous_readiness_gate_psycopg_scope.py \
  tests/test_paper_autonomous_readiness_gate_db_row_scope.py \
  tests/test_docs_paper_autonomous_readiness_gate_scope.py

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:src python3 -m compileall -q src tests
git diff --check
```

## Follow-Up Candidates

- Add a probability-selection-scorer-agreement CLI/readback so scorer agreement can be inspected without mutating trading state.
- Add a scorer-to-allocation alignment read model to compare selected probabilities against downstream paper allocation evidence.
- Add a Phase 2 evidence snapshot DB trend so readiness evidence can be viewed over time instead of one run at a time.
- Optionally expand the readiness digest to multiple evidence sources once the single-source persisted report readback is stable.
- Broaden CLI redaction hardening from Dalton across related readback commands.
