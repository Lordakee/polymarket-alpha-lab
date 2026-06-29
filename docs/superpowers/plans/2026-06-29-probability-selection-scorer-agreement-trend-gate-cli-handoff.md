# Probability Selection Scorer Agreement Trend Gate CLI/Readback Handoff

Date: 2026-06-29

## Status

The `probability-selection-scorer-agreement-trend-gate` CLI/readback node is
implemented. This handoff records the shipped boundary and verification
evidence for this node.

Command:

```bash
polymarket-alpha-lab probability-selection-scorer-agreement-trend-gate --limit 25
```

Current repo status:

- Source implementation: complete in `src/polymarket_alpha_lab/cli.py`.
- CLI tests: complete in
  `tests/test_cli_probability_selection_scorer_agreement_trend_gate.py` and
  `tests/test_cli_probability_selection_scorer_agreement_trend_gate_scope.py`.
- README/handoff docs: updated for implemented-command wording and Phase 1
  boundaries.
- opencode review: approved with no blockers.

## Required Boundary

This command is an env-only local Supabase/Postgres readback from persisted
`probability_selection_scorer_agreement_reports` via the existing agreement DB
env/config and loader:

- `POLYMARKET_ALPHA_LAB_PROBABILITY_SELECTION_SCORER_AGREEMENT_DB_ENABLED`
- `POLYMARKET_ALPHA_LAB_PROBABILITY_SELECTION_SCORER_AGREEMENT_DB_DSN`
- `POLYMARKET_ALPHA_LAB_PROBABILITY_SELECTION_SCORER_AGREEMENT_DB_TABLE`

Data flow:

```text
persisted aggregate agreement reports
  -> existing agreement report loader
  -> chronological agreement trend reducer
  -> pure agreement trend-gate reducer
  -> aggregate-only stdout
```

Implementation reads selected DB rows newest-first, reverses them for the
chronological trend reducer, builds the gate report in memory, prints the summary,
and close the connection. It writes nothing, creates no new durable gate table,
and adds no JSONL, SQLite, file durable store, Redis, Mongo, SQLAlchemy, hosted
DB assumption, generic durable-store abstraction, or file-backed cache. All
durable data for this node remains local Supabase/Postgres only.

## CLI And Output

The only CLI option is `--limit`, a positive integer defaulting to `25`. Do not
add DSN, table, persist, file, live, auth, private-key, wallet, account, order,
signing, submission, cancel, replace, or exchange-mutation flags.

Stdout is aggregate-only. It may include gate status, recommended next step,
source report count, trend status, latest agreement status/streak,
timestamp/span fields, aggregate status counts, aggregate averages, and
sanitized reason-code summaries. It must not include source rows, payloads,
report hashes, DB internals, market slugs, questions, condition ids, wallets,
accounts, auth material, private keys, or order-like details. Unsafe
reason-code-like values should print as `<redacted-reason-code>`.

Failure paths should continue using existing redaction helpers for DSNs, table
names, credentials, payloads, hashes, market identifiers, condition IDs,
questions, wallets/accounts, auth material, private keys, and order-like data.

## Phase 1 Boundary

This node is read-only/paper-only/report-only/readonly operator observability
over already-persisted local aggregate agreement reports. It is not permission
to trade, financial advice, investment ranking, trade recommendation, order
instruction, execution authorization, or an approval workflow.

Do not add live trading, auth/session flows, credential prompts, wallet/account
handling, private key handling, account reads, order construction, order
signing, order submission, order cancellation, order replacement, CLOB/order
endpoint calls, exchange mutation, market ranking, investment ranking,
readiness-gate integration, readiness-digest integration, or strategy-policy
integration.

It is not wired into readiness/digest/strategy policy yet.

## Verification Evidence

Focused CLI/readback tests:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' PYTHONPATH=.:src python3 -m pytest -q \
  tests/test_cli_probability_selection_scorer_agreement_trend_gate.py \
  tests/test_cli_probability_selection_scorer_agreement_trend_gate_scope.py
```

Result: `49 passed`.

Adjacent CLI/readback tests:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' PYTHONPATH=.:src python3 -m pytest -q \
  tests/test_cli_probability_selection_scorer_agreement_trend.py \
  tests/test_cli_probability_selection_scorer_agreement_trend_scope.py \
  tests/test_cli_probability_selection_scorer_agreement_trend_gate.py \
  tests/test_cli_probability_selection_scorer_agreement_trend_gate_scope.py
```

Result: `81 passed`.

Reducer adjacency:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' PYTHONPATH=.:src python3 -m pytest -q \
  tests/test_probability_selection_scorer_agreement_trend.py \
  tests/test_probability_selection_scorer_agreement_trend_scope.py \
  tests/test_probability_selection_scorer_agreement_trend_gate.py \
  tests/test_probability_selection_scorer_agreement_trend_gate_scope.py
```

Result: `28 passed`.

Agreement DB/store/config adjacency:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' PYTHONPATH=.:src python3 -m pytest -q \
  tests/test_probability_selection_scorer_agreement_db_row.py \
  tests/test_probability_selection_scorer_agreement_store.py \
  tests/test_probability_selection_scorer_agreement_psycopg.py \
  tests/test_supabase_probability_selection_scorer_agreement_config.py
```

Result: `66 passed`.

Full suite:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' PYTHONPATH=.:src python3 -m pytest -q
```

Result: `10291 passed, 1 skipped`.

Static checks:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:src python3 -m compileall -q src tests
git diff --check
PYTHONPATH=.:src python3 -m polymarket_alpha_lab --help | rg "probability-selection-scorer-agreement-trend-gate|probability-selection-scorer-agreement-trend|probability-selection-scorer-agreement"
git diff -- . ':(exclude).codegraph/**' | rg -n "ghp_[A-Za-z0-9_]+|github_pat_[A-Za-z0-9_]+|sk-[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|BEGIN (RSA|OPENSSH|EC|DSA)? ?PRIVATE KEY" || true
```

Results: compileall clean, `git diff --check` clean, CLI help smoke showed the
new command, and diff secret scan returned no matches.

opencode review:

```bash
opencode run --format json --model zhipuai-coding-plan/glm-5.2 --variant max
```

Result: approved, no blockers.

## Next Steps

- Commit and push this node.
- A future node may wire this readback into a broader readiness/digest view, but
  only after a separate plan and tests. This node intentionally stops at
  read-only aggregate CLI/readback.
