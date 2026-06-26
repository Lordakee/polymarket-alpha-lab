# Screening Gate Canonical Payload Handoff

Date: 2026-06-26

## Repo State

- Repo: `/home/ubuntu/polymarket-alpha-lab`
- Branch: `main`
- Current pushed commit: `cad7a7288fe79c47c98ea9991463f48cc236bc53`
- Commit message: `fix: harden screening gate DB row payload checks`
- `origin/main` was verified at the same commit after push.
- CodeGraph sync result before commit: synced 1 changed file.

## What Changed

- Hardened `paper_autonomous_screening_decision_support_gate_db_row.py`.
- Added strict JSON value comparison for materialized row/payload checks.
- Added recovered canonical payload validation in constructor and `from_db_row`.
- Canonicalized Decimal JSON serialization to six places for this codec.
- Required all hard flags on `reason_code_counts` payload objects.
- Strengthened tests with focused regressions for:
  - stale raw payload hash
  - self-hashed noncanonical Decimal payload
  - bool/int payload confusion
  - `reason_code_counts` objects missing all hard flags
  - missing nullable payload key
  - `object.__new__` bypass with recursive float payload
- Phase boundary remained unchanged:
  - paper-only/report-only/readonly
  - no live trading/auth/wallet/private-key/order placement/signing/submission/cancel/replace
  - no non-local-Supabase/Postgres persistence backend

## Verified Commands

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' PYTHONPATH=src /home/ubuntu/test-sandbox/.venv/bin/python -m pytest -q tests/test_paper_autonomous_screening_decision_support_gate_db_row.py
```

Result: `47 passed in 0.97s`

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' PYTHONPATH=src /home/ubuntu/test-sandbox/.venv/bin/python -m pytest -q tests/test_action_gated_strategy_recommendation_queue_db_row.py tests/test_action_gated_strategy_recommendation_queue_decision_support_db_row.py tests/test_action_gated_strategy_recommendation_queue_history_db_row.py tests/test_autonomous_market_scorer_db_row.py tests/test_local_observability_trends_db_row.py tests/test_paper_autonomous_allocation_proposal_db_history_health_db_row.py tests/test_paper_autonomous_allocation_proposal_db_history_metrics_evaluation_db_row.py tests/test_paper_autonomous_allocation_proposal_db_row.py tests/test_paper_autonomous_investment_ledger_db_history_health_db_row.py tests/test_paper_autonomous_investment_ledger_db_row.py tests/test_paper_autonomous_screening_decision_support_gate_db_row.py tests/test_paper_autonomous_screening_decision_support_gate_transition_db_row.py tests/test_paper_broker_db_row.py tests/test_paper_execution_reconciliation_db_row.py tests/test_paper_recommendation_cycle_snapshot_db_row.py tests/test_paper_trade_cost_audit_db_row.py tests/test_strategy_candidate_research_queue_db_row.py tests/test_strategy_candidate_research_queue_history_db_row.py
```

Result: `861 passed in 6.56s`

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' PYTHONPATH=src /home/ubuntu/test-sandbox/.venv/bin/python -m pytest -q $(git ls-files 'tests/test_*.py')
```

Result: `9509 passed, 1 skipped in 129.88s`

```bash
PYTHONPATH=src /home/ubuntu/test-sandbox/.venv/bin/python -m compileall -q src tests
git diff --check
git diff --cached --check
git diff -- src tests | rg -n "(ghp_[A-Za-z0-9_]+|github_pat_[A-Za-z0-9_]+|sk-[A-Za-z0-9_-]{20,}|BEGIN (RSA|OPENSSH|EC|PRIVATE) KEY|SUPABASE_[A-Z_]*KEY|POLYMARKET_.*(SECRET|PRIVATE|KEY))"
```

Result: compile/checks passed; secret scan had no matches.

```bash
opencode run --format json --model zhipuai-coding-plan/glm-5.2 --variant max --dir /home/ubuntu/polymarket-alpha-lab "<read-only screening gate canonical payload review prompt>"
```

Result: `approved: true`, `blocker_findings: []`.

## Uncommitted Files

- None at the time this handoff was written, before staging this handoff file.

## Follow-Up Notes

- Opencode noted only low-risk cleanup items:
  - avoid duplicate report recovery in `from_db_row`
  - keep strict comparison style consistent
  - preserve the assumed `json_recovery` exception contract
- The strict comparison consistency item was applied before commit.
- A read-only Decimal scan found many other historical DB row codecs whose payload hash semantics would change under global six-place Decimal serialization. Do not apply a blanket formatter change without a migration plan.

## Next Step

Start the next node as a planning/migration node for Decimal canonicalization:

1. Split DB row Decimal canonicalization into safe groups:
   - direct non-six-place snapshot/hash changes
   - low fixture churn but persisted-hash migration risk
   - latent/no-current-Decimal branches
2. Decide per group whether to harden now, add compatibility readers, or document a migration boundary.
3. Prefer a small high-value implementation slice after the plan is explicit, likely one codec with non-six-place tests and no live trading/auth/persistence boundary changes.
4. Run affected tests, full suite, opencode review, CodeGraph sync, commit, push, and write the next handoff.
