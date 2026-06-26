# Action-Gated History Decimal Canonicalization Handoff

Date: 2026-06-26

## Node Summary

Completed Task 2 from the DB row Decimal canonicalization migration plan.

Committed and pushed:

- `80f6940 fix: canonicalize action-gated history Decimal payloads`

Changed files:

- `src/polymarket_alpha_lab/action_gated_strategy_recommendation_queue_history_db_row.py`
- `tests/test_action_gated_strategy_recommendation_queue_history_db_row.py`

## What Changed

- Added module-local `_DECIMAL_QUANTUM = Decimal("0.000001")`.
- Changed `_json_ready(Decimal)` for the action-gated history DB row codec to:
  - reject non-finite Decimal values
  - reject value-changing over-precision values instead of rounding them
  - emit fixed six-place strings for equivalent Decimal exponents
- Added tests proving:
  - `Decimal("42")` and `Decimal("42.000000")` produce identical six-place payloads and hashes
  - over-precision such as `Decimal("42.0000004")` is rejected
  - equivalent materialized Decimal scale is accepted when stored payload is canonical
  - self-hashed legacy payload strings such as `"42"` / `"12"` are rejected
- Preserved paper-only/report-only/readonly boundaries and did not touch persistence or execution surfaces.

## TDD Evidence

RED:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' PYTHONPATH=src \
  /home/ubuntu/test-sandbox/.venv/bin/python -m pytest -q \
  tests/test_action_gated_strategy_recommendation_queue_history_db_row.py::test_action_gated_queue_history_db_row_rejects_overprecision_decimal_writes
```

Observed result before the over-precision guard:

```text
FAILED ... Failed: DID NOT RAISE ValueError
```

GREEN and regression verification:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' PYTHONPATH=src \
  /home/ubuntu/test-sandbox/.venv/bin/python -m pytest -q \
  tests/test_action_gated_strategy_recommendation_queue_history_db_row.py::test_action_gated_queue_history_db_row_rejects_overprecision_decimal_writes \
  tests/test_action_gated_strategy_recommendation_queue_history_db_row.py::test_action_gated_queue_history_db_row_canonicalizes_equivalent_decimal_writes \
  tests/test_action_gated_strategy_recommendation_queue_history_db_row.py::test_action_gated_queue_history_db_row_from_db_row_rejects_bypassed_self_hashed_legacy_decimal_payload
```

Observed result:

```text
3 passed
```

## Verification

Commands run:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' PYTHONPATH=src \
  /home/ubuntu/test-sandbox/.venv/bin/python -m pytest -q \
  tests/test_action_gated_strategy_recommendation_queue_history_db_row.py

PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' PYTHONPATH=src \
  /home/ubuntu/test-sandbox/.venv/bin/python -m pytest -q \
  tests/test_action_gated_strategy_recommendation_queue_history_db_row.py \
  tests/test_action_gated_strategy_recommendation_queue_db_row.py

PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' PYTHONPATH=src \
  /home/ubuntu/test-sandbox/.venv/bin/python -m pytest -q \
  $(git ls-files 'tests/test_*.py')

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src \
  /home/ubuntu/test-sandbox/.venv/bin/python -m compileall -q src tests

git diff --check
codegraph sync
git diff --cached --check
```

Observed results:

- Target file: 54 passed.
- Affected files: 91 passed.
- Full suite: 9512 passed, 1 skipped.
- Compileall passed.
- Diff checks passed.
- CodeGraph sync reported already up to date.
- Credential-pattern scan over changed files produced no matches.

## Review

Read-only opencode review used:

```bash
opencode run --format json \
  --model zhipuai-coding-plan/glm-5.2 \
  --variant max \
  --dir /home/ubuntu/polymarket-alpha-lab \
  "<read-only code review prompt>"
```

Review artifact:

- `/tmp/polymarket-alpha-lab-review/action-gated-history-decimal-canonicalization-review.jsonl`

Review verdict:

- Approved.
- No blockers.

Non-blocking notes:

- Error wording could be more field-specific in future work.
- Optional extra over-precision boundary tests could document half-even neighbor values, but runtime review confirmed the implementation rejects those values.

## Repo State At Node Commit

After push:

```text
HEAD:        80f694080deda4ee7464a9f0cb61343bfe9affb8
origin/main: 80f694080deda4ee7464a9f0cb61343bfe9affb8
```

## Next Recommended Step

Create and review the Group A compatibility-reader design document before touching any Group A codec:

- `docs/superpowers/plans/2026-06-26-db-row-decimal-compatibility-reader-design.md`

This should define how old non-six-place payload hashes are accepted or rejected while new writes emit six-place Decimal strings.

Do not implement Group A until that design is reviewed and committed.
