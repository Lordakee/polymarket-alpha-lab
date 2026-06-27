# Probability DB-Row Decimal Compatibility Handoff

Date: 2026-06-27

## Repo Status

- Repo: `/home/ubuntu/polymarket-alpha-lab`
- Branch: `main`
- Base before this node: `ccf3116a40414af8128fe4d1ffb91b46a62ad003`
- Working node scope:
  - `src/polymarket_alpha_lab/paper_probability_recommendation_queue_db_row.py`
  - `tests/test_paper_probability_recommendation_queue_db_row.py`
  - `src/polymarket_alpha_lab/paper_probability_selection_summary_history_db_row.py`
  - `tests/test_paper_probability_selection_summary_history_db_row.py`
  - `src/polymarket_alpha_lab/strategy_candidate_research_queue_db_row.py`
  - `tests/test_strategy_candidate_research_queue_db_row.py`

## What Changed

- Hardened three DB-row codecs to write fixed six-place Decimal strings for explicit allowlisted payload paths.
- Added safe legacy read compatibility for self-hashed payloads that use equivalent Decimal string exponents.
- Preserved raw payload hash validation before legacy Decimal normalization on `from_db_row`.
- Added rejection coverage for value-changing overprecision, non-allowlisted Decimal-like payload changes, raw `float` / `Decimal` / `datetime` JSON values, bool/int confusion, and bypassed unsafe hard flags.
- Kept the changed production files as pure row codecs with no new persistence, network, auth, wallet, account, order, signing, submission, cancellation, replacement, exchange, or live-trading surfaces.

## Verified Commands

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' PYTHONPATH=src python3 -m pytest -q tests/test_strategy_candidate_research_queue_db_row.py
```

Result: `69 passed`

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' PYTHONPATH=src python3 -m pytest -q tests/test_paper_probability_selection_summary_history_db_row.py tests/test_paper_probability_recommendation_queue_db_row.py tests/test_strategy_candidate_research_queue_db_row.py
```

Result: `172 passed`

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' PYTHONPATH=src python3 -m pytest -q tests/test_paper_probability_selection_summary_history_db_row.py tests/test_paper_probability_selection_summary_history.py tests/test_paper_probability_selection_summary_history_psycopg.py
```

Result: `78 passed`

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' PYTHONPATH=src python3 -m pytest -q tests/test_paper_probability_recommendation_queue_db_row.py tests/test_paper_probability_recommendation_queue.py
```

Result: `57 passed`

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' PYTHONPATH=src python3 -m pytest -q tests/test_strategy_candidate_research_queue_db_row.py tests/test_strategy_candidate_research_queue.py
```

Result: `73 passed`

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' PYTHONPATH=src python3 -m pytest -q tests/test_paper_probability_selection_summary_history_db_row.py tests/test_paper_probability_recommendation_queue_db_row.py tests/test_strategy_candidate_research_queue_db_row.py tests/test_strategy_recommendation_layer_scope.py::test_recommendation_layer_imports_only_allowlisted_dependencies
```

Result: `188 passed`

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' PYTHONPATH=src python3 -m pytest -q tests/test_*db_row.py
```

Result: `1764 passed`

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m compileall -q src tests
```

Result: passed

```bash
git diff --check
```

Result: passed

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' PYTHONPATH=src python3 -m pytest -q
```

Result: `9609 passed, 1 skipped`

```bash
codegraph sync
```

Result: already up to date

Secret scan over changed files: clean.

Production forbidden persistence/trading scan over changed production files: clean.

## Review

- Review package: `/tmp/polymarket-alpha-lab-review/probability-db-row-decimal-review-package.md`
- opencode artifact: `/tmp/polymarket-alpha-lab-review/probability-db-row-decimal-opencode-review.jsonl`
- Reviewer command used `zhipuai-coding-plan/glm-5.2 --variant max` in read-only mode.
- Verdict: `APPROVED`
- Blocking findings: none.
- Residual notes: reviewer called out low-risk consistency differences between local helper names and Decimal-check implementations; no correctness or boundary issue was found.

## Uncommitted Files At Handoff Creation

Expected before commit:

- `src/polymarket_alpha_lab/paper_probability_recommendation_queue_db_row.py`
- `src/polymarket_alpha_lab/paper_probability_selection_summary_history_db_row.py`
- `src/polymarket_alpha_lab/strategy_candidate_research_queue_db_row.py`
- `tests/test_paper_probability_recommendation_queue_db_row.py`
- `tests/test_paper_probability_selection_summary_history_db_row.py`
- `tests/test_strategy_candidate_research_queue_db_row.py`
- `docs/superpowers/plans/2026-06-27-probability-db-row-decimal-compatibility-handoff.md`

## Next Step

After this node is committed and pushed, start the next parallel batch from the read-only inventories:

1. Prioritize confirmed Decimal compatibility gaps with disjoint write scopes:
   - `action_gated_strategy_recommendation_queue_history_db_row.py`
   - `autonomous_market_scorer_db_row.py`
   - `paper_execution_reconciliation_db_row.py`
   - `paper_broker_db_row.py`
2. Keep each worker scoped to one codec/test pair and one unique handoff doc.
3. Maintain the project iron rules: local Supabase/Postgres only for durable data, paper-only/report-only/readonly, no live trading/auth/wallet/order mutation, no fast mode, and opencode read-only review before push.
4. Track the larger strategy-product next step separately: a Supabase-backed `paper-probability-selection-summary-history` CLI is the best next user-facing loop capability after the codec hardening batch.
