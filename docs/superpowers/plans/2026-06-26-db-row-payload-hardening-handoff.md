# DB Row Payload Hardening Handoff

Date: 2026-06-26

## Repo State

- Repo: `/home/ubuntu/polymarket-alpha-lab`
- Branch: `main`
- Current pushed commit: `52b3d97793726dba5e77a6ce4c3a423b4c78e7f3`
- Commit message: `fix: harden DB row payload construction`
- `origin/main` was verified at the same commit after push.
- CodeGraph sync result before commit: already up to date.

## What Changed

- Hardened 18 DB row codec modules and matching tests.
- Added constructor and `from_db_row` validation for:
  - raw `payload_json` hash consistency
  - recovered canonical payload equality
  - recursive hard-flag enforcement
  - noncanonical Decimal payload strings
  - raw Decimal/float JSON values
  - bool/int confusion
  - nullable key omission vs explicit null
  - `object.__new__` row bypasses
- Phase boundary remained unchanged:
  - paper-only/report-only/readonly
  - no live trading/auth/wallet/private-key/order placement/signing/submission/cancel/replace
  - no non-local-Supabase/Postgres persistence backend

## Verified Commands

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' PYTHONPATH=src /home/ubuntu/test-sandbox/.venv/bin/python -m pytest -q tests/test_paper_autonomous_allocation_proposal_db_history_metrics_evaluation_db_row.py::test_metrics_evaluation_from_db_row_rejects_bypassed_raw_decimal_payload_with_stale_hash tests/test_paper_autonomous_allocation_proposal_db_history_health_db_row.py::test_health_db_row_rejects_self_hashed_noncanonical_decimal_payload
```

Result: `2 passed in 1.01s`

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' PYTHONPATH=src /home/ubuntu/test-sandbox/.venv/bin/python -m pytest -q tests/test_paper_autonomous_allocation_proposal_db_history_metrics_evaluation_db_row.py tests/test_paper_autonomous_allocation_proposal_db_history_health_db_row.py
```

Result: `102 passed in 1.25s`

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' PYTHONPATH=src /home/ubuntu/test-sandbox/.venv/bin/python -m pytest -q tests/test_action_gated_strategy_recommendation_queue_db_row.py tests/test_action_gated_strategy_recommendation_queue_decision_support_db_row.py tests/test_action_gated_strategy_recommendation_queue_history_db_row.py tests/test_autonomous_market_scorer_db_row.py tests/test_local_observability_trends_db_row.py tests/test_paper_autonomous_allocation_proposal_db_history_health_db_row.py tests/test_paper_autonomous_allocation_proposal_db_history_metrics_evaluation_db_row.py tests/test_paper_autonomous_allocation_proposal_db_row.py tests/test_paper_autonomous_investment_ledger_db_history_health_db_row.py tests/test_paper_autonomous_investment_ledger_db_row.py tests/test_paper_autonomous_screening_decision_support_gate_db_row.py tests/test_paper_autonomous_screening_decision_support_gate_transition_db_row.py tests/test_paper_broker_db_row.py tests/test_paper_execution_reconciliation_db_row.py tests/test_paper_recommendation_cycle_snapshot_db_row.py tests/test_paper_trade_cost_audit_db_row.py tests/test_strategy_candidate_research_queue_db_row.py tests/test_strategy_candidate_research_queue_history_db_row.py
```

Result: `855 passed in 7.03s`

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' PYTHONPATH=src /home/ubuntu/test-sandbox/.venv/bin/python -m pytest -q $(git ls-files 'tests/test_*.py')
```

Result: `9503 passed, 1 skipped in 126.33s`

```bash
PYTHONPATH=src /home/ubuntu/test-sandbox/.venv/bin/python -m compileall -q src tests
git diff --check
git diff --cached --check
git diff --cached -- src tests | rg -n "(ghp_[A-Za-z0-9_]+|github_pat_[A-Za-z0-9_]+|sk-[A-Za-z0-9_-]{20,}|BEGIN (RSA|OPENSSH|EC|PRIVATE) KEY|SUPABASE_[A-Z_]*KEY|POLYMARKET_.*(SECRET|PRIVATE|KEY))"
```

Result: compile/checks passed; secret scan had no matches.

```bash
opencode run --format json --model zhipuai-coding-plan/glm-5.2 --variant max --dir /home/ubuntu/polymarket-alpha-lab "<read-only final review prompt>"
```

Result: `approved: true`, `blocker_findings: []`.

## Uncommitted Files

- None at the time this handoff was written, before staging this handoff file.

## Follow-Up Notes

Opencode marked these as non-blocking follow-ups:

- Align Decimal canonicalization style across DB row codecs.
- Strengthen/normalize canonical recovered payload enforcement in weaker codecs, especially screening decision support gate DB row.
- Normalize helper names for payload recoverability checks.

## Next Step

Start the next node by addressing the Decimal/canonicalization consistency follow-up as a scoped cleanup:

1. Identify DB row codecs still using plain `str(Decimal)` in `_json_ready`.
2. Add focused RED tests for logically equivalent Decimal values producing canonical six-place payload strings and stable hashes where applicable.
3. Apply minimal codec changes without altering Phase 1 boundaries.
4. Run affected tests, full suite, opencode review, CodeGraph sync, commit, push, and write the next handoff.
