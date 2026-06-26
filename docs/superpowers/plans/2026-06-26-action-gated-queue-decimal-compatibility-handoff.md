# Action-Gated Queue Decimal Compatibility Handoff

Date: 2026-06-26

## Node Summary

This node hardened the action-gated strategy recommendation queue DB row Decimal payload codec.

Code commit:

- `bc01cc1799f37c286e558be51ea629c489270898` - `fix: harden action-gated queue Decimal row compatibility`

Changed files:

- `src/polymarket_alpha_lab/action_gated_strategy_recommendation_queue_db_row.py`
- `tests/test_action_gated_strategy_recommendation_queue_db_row.py`

## Behavior Implemented

- New writes canonicalize explicit Decimal payload fields to fixed six-decimal-place strings.
- Overprecision is rejected instead of rounded.
- `from_db_row` accepts legacy or semantically equivalent Decimal spellings only when `report_sha256` matches the exact stored payload and recovered report validation proves the row is safe.
- Compatibility is scoped to explicit schema Decimal paths through `_DECIMAL_PAYLOAD_PATTERNS`.
- Non-Decimal fields still require exact type and value matches.
- Raw Python `Decimal`, `datetime`, and float values in `payload_json` are rejected before normalization can hide them.
- Bypassed rows validate core materialized fields before payload recovery.
- `paper_only`, `report_only`, and `readonly` remain enforced.

No store, migration, psycopg, Supabase configuration, execution, auth, wallet, live trading, order placement, signing, submission, cancel, replace, or exchange mutation path was changed.

## TDD Evidence

Initial RED subset after adding tests:

- Result: `9 failed, 2 passed`
- Expected failure themes:
  - old strict canonical comparison rejected legacy Decimal spellings
  - raw `Decimal` and `datetime` payload values were normalized instead of rejected
  - bypassed row core validation was too late or too weak

GREEN subset after implementation:

- Result: 11 new or changed targeted tests passed.

## Verification

Target DB-row file:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' PYTHONPATH=src python3 -m pytest -q tests/test_action_gated_strategy_recommendation_queue_db_row.py
```

Result: `46 passed`

Affected store/psycopg slice:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' PYTHONPATH=src python3 -m pytest -q tests/test_action_gated_strategy_recommendation_queue_db_row.py tests/test_action_gated_strategy_recommendation_queue_store.py tests/test_action_gated_strategy_recommendation_queue_psycopg.py tests/test_action_gated_strategy_recommendation_queue_psycopg_read.py
```

Result: `91 passed`

Adjacent reducer slice:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' PYTHONPATH=src python3 -m pytest -q tests/test_action_gated_strategy_recommendation_queue.py tests/test_strategy_recommendation_bundle.py tests/test_strategy_recommendation_queue.py tests/test_candidate_assessment.py tests/test_strategy_candidate_recommendation.py tests/test_paper_strategy_selection_policy.py
```

Result: `57 passed`

DB-row regression:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' PYTHONPATH=src python3 -m pytest -q tests/test_*db_row.py
```

Result: `1710 passed`

Full suite:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' PYTHONPATH=src python3 -m pytest -q
```

Result: `9555 passed, 1 skipped`

Compile:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m compileall -q src tests
```

Result: passed

Diff checks:

```bash
git diff --check
git diff --cached --check
```

Result: clean

CodeGraph:

```bash
codegraph sync
```

Result: synced 2 changed files

Changed-file secret scan:

- Result: clean

Changed-file forbidden persistence/auth/trading static search:

- Result: no matches

## Review

First local opencode review attempt:

- Command timed out after 300 seconds and produced no verdict.
- Artifact: `/tmp/polymarket-alpha-lab-review/action-gated-queue-decimal-review.jsonl`
- This was not treated as approval.

Second local opencode review attempt:

- Review package: `/tmp/polymarket-alpha-lab-review/action-gated-queue-decimal-compact-review-package.md`
- Artifact: `/tmp/polymarket-alpha-lab-review/action-gated-queue-decimal-review-2.jsonl`
- Verdict: `APPROVED`
- Blocking findings: none

Non-blocking observations from review:

- `_decimal_to_json` may emit `"-0.000000"` for `Decimal("-0")`; reviewer considered this cosmetic and practically unreachable because schema fields are nonnegative.
- `_DECIMAL_PAYLOAD_PATTERNS` must track future schema Decimal fields.
- `report_sha256` and `total_ready_notional` were removed from the strict `_validate_row_matches_payload` loop and are covered elsewhere.

## Next Recommended Target

Continue the Group A Decimal compatibility work with another DB-row codec that has explicit Decimal-bearing payload or materialized fields and existing focused tests. Avoid already completed targets:

- NAV snapshot
- paper trade journal
- paper trade cost audit
- action-gated queue history
- screening gate canonical payload
- action-gated strategy recommendation queue DB row

Use TDD for the next node:

- add RED tests
- confirm the intended failures
- implement the narrow compatibility hardening
- run focused, affected, DB-row, compile, and full-suite verification as appropriate
- request local opencode review
- commit, sync CodeGraph, secret-scan, and push after approval
