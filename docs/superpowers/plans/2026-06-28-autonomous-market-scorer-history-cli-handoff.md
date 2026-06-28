# Autonomous Market Scorer History CLI Handoff

Date: 2026-06-28

## Node Summary

Current node: new read-only `autonomous-market-scorer-history` CLI for aggregating historical autonomous market scorer reports from the local Supabase/Postgres store.

Scope observed from current on-disk code:

- CLI command: `autonomous-market-scorer-history`
- Config version: `autonomous-market-scorer-history-v0`
- DB config is env-only, using the existing autonomous market scorer DB env boundary:
  - `POLYMARKET_ALPHA_LAB_AUTONOMOUS_MARKET_SCORER_DB_ENABLED`
  - `POLYMARKET_ALPHA_LAB_AUTONOMOUS_MARKET_SCORER_DB_DSN`
  - `POLYMARKET_ALPHA_LAB_AUTONOMOUS_MARKET_SCORER_DB_TABLE`
- Default source table: `autonomous_market_scorer_reports`
- CLI option: `--limit`, positive integer, default `25`

## Safety Boundary

- The command is read-only: it opens a Postgres connection, loads existing autonomous market scorer reports, builds an aggregate history report, prints summaries, and closes the connection.
- DB configuration is local Supabase/Postgres via environment variables only; there is no CLI DSN/table argument.
- Stdout is aggregate-only:
  - source report counts
  - time span and latest report age context
  - latest gate status/streak
  - candidate/notional aggregates
  - blocked/skipped counts
  - history status and recommended next step
  - recurrence counts and max recurrence counts
  - sanitized reason-code summaries
- The CLI does not print raw table names, DSNs, payloads, payload JSON, score rows, report hashes, market slugs, condition IDs, questions, market details, tokens, wallet/account/auth/order fields, or signing material.
- Reason codes are sanitized before stdout. Unsafe values are replaced with `<redacted-reason-code>`, including non-canonical strings, long values, hash-like values, and values containing sensitive fragments such as condition, market slug, payload, hash, token, wallet, order, auth, private key, secret, or question/detail/title terms.
- DB errors are redacted before stderr, including DSN/table redaction plus payload/hash/market/condition/auth/wallet/order sensitive-field redaction.
- No live trading/auth/wallet/order/signing/submission/cancel/replace path is introduced.
- No persistence sink is introduced for the history report.

## Implementation Notes For Main Agent

- The history builder enforces paper-only/report-only/readonly hard flags on source reports, nested score rows where applicable, recurring counts, and the final history report.
- Source reports are loaded newest-first from the store, then reversed before aggregation so the builder receives chronological input.
- Recurring market/condition identifiers are only summarized as counts/max counts on stdout; raw identifier values are not printed.
- Recurring reason-code counts print only safe reason code labels with counts; redacted recurring reason codes are counted separately.
- The command requires the autonomous scorer DB env to be enabled and requires a DSN; disabled or missing-DSN cases fail before attempting a DB read.

## Final Verification TODO

Final verification completed before commit/push:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' PYTHONPATH=.:src python3 -m pytest -q \
  tests/test_cli_autonomous_market_scorer_history.py \
  tests/test_cli_autonomous_market_scorer_history_scope.py
```

Result: `33 passed in 2.35s` before review fixes, then covered by the
post-review broader slice below.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' PYTHONPATH=.:src python3 -m pytest -q \
  tests/test_cli_autonomous_market_scorer_history.py \
  tests/test_cli_autonomous_market_scorer_history_scope.py \
  tests/test_autonomous_market_scorer_history.py \
  tests/test_autonomous_market_scorer_history_scope.py \
  tests/test_autonomous_market_scorer_load.py \
  tests/test_autonomous_market_scorer_load_scope.py \
  tests/test_autonomous_market_scorer_db_store.py \
  tests/test_supabase_autonomous_market_scorer_config.py \
  tests/test_cli_paper_probability_selection_summary_history_trend.py \
  tests/test_cli_paper_probability_selection_summary_history_trend_scope.py
```

Result: `157 passed in 4.86s`

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' PYTHONPATH=.:src python3 -m pytest -q
```

Result: `9970 passed, 1 skipped in 66.58s`

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:src python3 -m compileall -q src tests
```

Result: passed

```bash
git diff --check
```

Result: passed

```bash
codegraph sync
```

Result: passed before opencode review; re-run after final review if files change.

```bash
rg -n "ghp_[A-Za-z0-9_]+|github_pat_[A-Za-z0-9_]+|sk-[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|BEGIN (RSA|OPENSSH|EC|DSA)? ?PRIVATE KEY" \
  src/polymarket_alpha_lab/cli.py \
  tests/test_cli_autonomous_market_scorer_history.py \
  tests/test_cli_autonomous_market_scorer_history_scope.py \
  docs/superpowers/plans/2026-06-28-autonomous-market-scorer-history-cli-handoff.md
```

Result: no matches

## Review Notes

- Subagent phase/DB-boundary review: no blockers.
- Subagent output-security review found two blockers:
  - plain `reason_codes` / `reason_code` fields in stderr were not redacted;
  - quoted structured sensitive values could be truncated incorrectly.
- Both blockers were fixed with regression tests:
  - `test_history_cli_read_errors_redact_reason_code_fields`
  - `test_history_cli_read_errors_redact_quoted_structured_payload_values`
- opencode review:
  - command: `opencode run --format json --model zhipuai-coding-plan/glm-5.2 --variant max --dir /home/ubuntu/polymarket-alpha-lab ...`
  - result: approved, no blockers

## Repo Status TODO

Status before commit:

- Branch: `main`
- HEAD before commit: `b51328d8ebf3bef21edf4f704de2f9e9555c5dce`
- `origin/main` before commit: `b51328d8ebf3bef21edf4f704de2f9e9555c5dce`
- Final changed files:
  - `src/polymarket_alpha_lab/cli.py`
  - `tests/test_cli_autonomous_market_scorer_history.py`
  - `tests/test_cli_autonomous_market_scorer_history_scope.py`
  - `docs/superpowers/plans/2026-06-28-autonomous-market-scorer-history-cli-handoff.md`

Status after commit/push to be verified by the main agent in the final response.

## Concerns / Follow-Up

- Tests and final repo status were intentionally left as TODO placeholders for the main agent to fill after completing verification.
- Confirm the final review includes both success-path aggregate stdout and failure-path redaction so DSN, table, payload, hash, market, condition, auth, wallet, order, and signing details cannot leak.
