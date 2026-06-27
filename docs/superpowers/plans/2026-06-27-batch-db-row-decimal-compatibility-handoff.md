# Batch DB-Row Decimal Compatibility Handoff

Date: 2026-06-27

## Repo Status

- Repo: `/home/ubuntu/polymarket-alpha-lab`
- Branch: `main`
- Base before this node: `9b7ea4f4cac3d54489d19da89f96efae6f45aa87`
- CodeGraph: synced, already up to date
- Batch scope: 12 independent DB-row codec/test pairs

## Changed Modules

- `action_gated_strategy_recommendation_queue_decision_support_db_row.py`
- `action_gated_strategy_recommendation_queue_history_db_row.py`
- `autonomous_market_scorer_db_row.py`
- `paper_autonomous_allocation_proposal_db_history_health_db_row.py`
- `paper_autonomous_allocation_proposal_db_row.py`
- `paper_autonomous_investment_ledger_db_history_health_db_row.py`
- `paper_autonomous_investment_ledger_db_row.py`
- `paper_autonomous_screening_decision_support_gate_db_row.py`
- `paper_broker_db_row.py`
- `paper_execution_reconciliation_db_row.py`
- `paper_order_lifecycle_db_row.py`
- `paper_recommendation_risk_budget_db_row.py`

Each module was updated with its matching `tests/test_*_db_row.py` file only.

## What Changed

- Added fixed six-place Decimal serialization for explicit allowlisted Decimal payload paths in all 12 codecs.
- Preserved raw stored payload, snapshot, or record hash validation before legacy Decimal normalization in `from_db_row`.
- Added safe read compatibility for self-hashed legacy Decimal strings that are mathematically equivalent to canonical six-place values.
- Added rejection coverage for stale hashes, value-changing Decimal strings, overprecision strings, non-allowlisted Decimal-like strings, and raw `float` / `Decimal` / `datetime` payload values.
- Preserved `paper_only`, `report_only`, and `readonly` hard flags.
- Kept the changed production files as pure codecs with no new persistence, network, auth, wallet, account, order mutation, signing, submission, cancellation, replacement, exchange, or live-trading surfaces.

## Verified Commands

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' PYTHONPATH=.:src python3 -m pytest -q tests/test_action_gated_strategy_recommendation_queue_history_db_row.py tests/test_autonomous_market_scorer_db_row.py tests/test_paper_execution_reconciliation_db_row.py tests/test_paper_broker_db_row.py tests/test_paper_autonomous_investment_ledger_db_row.py tests/test_paper_autonomous_investment_ledger_db_history_health_db_row.py tests/test_paper_autonomous_allocation_proposal_db_history_health_db_row.py tests/test_paper_autonomous_screening_decision_support_gate_db_row.py tests/test_action_gated_strategy_recommendation_queue_decision_support_db_row.py tests/test_paper_autonomous_allocation_proposal_db_row.py tests/test_paper_recommendation_risk_budget_db_row.py tests/test_paper_order_lifecycle_db_row.py
```

Result: `726 passed`

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' PYTHONPATH=.:src python3 -m pytest -q tests/test_action_gated_strategy_recommendation_queue_history_db_row.py tests/test_action_gated_strategy_recommendation_queue_history.py tests/test_action_gated_strategy_recommendation_queue_history_db_history.py tests/test_action_gated_strategy_recommendation_queue_decision_support_db_row.py tests/test_action_gated_strategy_recommendation_queue_decision_support_trend_db_row.py tests/test_action_gated_strategy_recommendation_queue_decision_support_trend.py
```

Result: `155 passed`

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' PYTHONPATH=.:src python3 -m pytest -q tests/test_autonomous_market_scorer.py tests/test_autonomous_market_scorer_db_row.py tests/test_autonomous_market_scorer_explanation.py tests/test_probability_selection_scorer_bridge.py
```

Result: `98 passed`

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' PYTHONPATH=.:src python3 -m pytest -q tests/test_paper_broker.py tests/test_paper_broker_db_row.py tests/test_paper_broker_store.py tests/test_paper_broker_load.py tests/test_paper_broker_psycopg.py tests/test_paper_broker_history.py tests/test_paper_broker_db_migration.py tests/test_paper_execution_reconciliation.py tests/test_paper_execution_reconciliation_db_row.py tests/test_paper_execution_reconciliation_db_history.py tests/test_paper_execution_reconciliation_health_gate.py tests/test_paper_execution_reconciliation_load.py
```

Result: `187 passed`

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' PYTHONPATH=.:src python3 -m pytest -q tests/test_paper_autonomous_investment_ledger.py tests/test_paper_autonomous_investment_ledger_db_row.py tests/test_paper_autonomous_investment_ledger_store.py tests/test_paper_autonomous_investment_ledger_psycopg.py tests/test_paper_autonomous_investment_ledger_load.py tests/test_paper_autonomous_investment_ledger_db_migration.py tests/test_paper_autonomous_investment_ledger_db_history_health.py tests/test_paper_autonomous_investment_ledger_db_history_health_db_row.py tests/test_paper_autonomous_investment_ledger_db_history_health_store.py tests/test_paper_autonomous_investment_ledger_db_history_health_psycopg.py tests/test_paper_autonomous_investment_ledger_db_history_health_load.py
```

Result: `263 passed`

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' PYTHONPATH=.:src python3 -m pytest -q tests/test_paper_autonomous_allocation_proposal_db_row.py tests/test_paper_autonomous_allocation_proposal.py tests/test_paper_autonomous_allocation_proposal_db_history.py tests/test_paper_autonomous_allocation_proposal_db_history_metrics.py tests/test_paper_autonomous_allocation_proposal_db_history_health.py tests/test_paper_autonomous_allocation_proposal_db_history_health_db_row.py tests/test_paper_autonomous_allocation_proposal_db_history_health_store.py tests/test_paper_recommendation_allocation.py
```

Result: `245 passed`

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' PYTHONPATH=.:src python3 -m pytest -q tests/test_paper_autonomous_screening_decision_support_gate.py tests/test_paper_autonomous_screening_decision_support_gate_db_row.py tests/test_paper_autonomous_screening_decision_support_gate_load.py tests/test_paper_autonomous_screening_decision_support_gate_store.py tests/test_paper_autonomous_screening_decision_support_gate_transition.py tests/test_paper_autonomous_screening_decision_support_gate_transition_load.py tests/test_paper_autonomous_screening_decision_support_gate_transition_db_row.py
```

Result: `175 passed`

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' PYTHONPATH=.:src python3 -m pytest -q tests/test_paper_recommendation_risk_budget_db_row.py tests/test_strategy_recommendation_layer_scope.py
```

Result: `185 passed`

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' PYTHONPATH=.:src python3 -m pytest -q tests/test_paper_order_lifecycle.py tests/test_paper_order_lifecycle_db_row.py tests/test_paper_order_lifecycle_store.py tests/test_paper_order_lifecycle_psycopg.py tests/test_paper_order_lifecycle_db_history.py tests/test_paper_order_lifecycle_db_history_load.py tests/test_paper_order_lifecycle_scope.py tests/test_paper_order_lifecycle_db_row_scope.py tests/test_paper_order_lifecycle_store_scope.py tests/test_paper_order_lifecycle_db_history_scope.py tests/test_paper_execution_reconciliation.py tests/test_paper_execution_reconciliation_load.py tests/test_paper_execution_reconciliation_load_scope.py tests/test_paper_execution_reconciliation_db_row.py
```

Result: `131 passed`

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' PYTHONPATH=.:src python3 -m pytest -q tests/test_*db_row.py
```

Result: `1914 passed`

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:src python3 -m compileall -q src tests
```

Result: passed

```bash
git diff --check
```

Result: passed

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' PYTHONPATH=.:src python3 -m pytest -q
```

Result: `9759 passed, 1 skipped`

Secret scan over changed files: clean.

Production forbidden persistence/trading scan over changed production files: clean.

## Review

- Review package: `/tmp/polymarket-alpha-lab-review/batch-db-row-decimal-review-package.md`
- opencode artifact: `/tmp/polymarket-alpha-lab-review/batch-db-row-decimal-opencode-review.jsonl`
- Reviewer command used `zhipuai-coding-plan/glm-5.2 --variant max` in read-only mode.
- Verdict: `APPROVED`
- Blocking findings: none.
- Low-risk follow-up notes:
  - Add per-module pure-codec AST guards across the other codecs, not just the allocation proposal history health test.
  - Consider later unifying helper naming and comparison style, especially `paper_broker_db_row.py` scale-preserving materialized comparison and `paper_execution_reconciliation_db_row.py` field-path structure.

## Uncommitted Files At Handoff Creation

Expected before commit:

- 12 changed production codec files listed above.
- 12 matching changed `tests/test_*_db_row.py` files.
- `docs/superpowers/plans/2026-06-27-batch-db-row-decimal-compatibility-handoff.md`

## Next Step

After commit and push:

1. Start a smaller follow-up hardening batch for remaining confirmed Decimal codec gaps, or switch to the higher-value product loop: Supabase-backed `paper-probability-selection-summary-history` CLI.
2. Keep future parallel workers to disjoint write scopes and add one handoff doc per node.
3. Maintain local Supabase/Postgres-only durable data, paper-only/report-only/readonly, no live trading/auth/wallet/order mutation, no fast mode, and opencode read-only review before push.
