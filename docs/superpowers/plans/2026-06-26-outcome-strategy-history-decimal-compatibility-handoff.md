# Outcome And Strategy History Decimal Compatibility Handoff

Date: 2026-06-26

## Node Summary

This node hardened two persisted DB-row Decimal codecs:

- `outcome_tracking_db_row.py`
- `strategy_candidate_research_queue_history_db_row.py`

Code commit:

- `7c2c17f` - `fix: harden outcome and strategy history Decimal codecs`

Changed files:

- `src/polymarket_alpha_lab/outcome_tracking_db_row.py`
- `tests/test_outcome_tracking_db_row.py`
- `src/polymarket_alpha_lab/strategy_candidate_research_queue_history_db_row.py`
- `tests/test_strategy_candidate_research_queue_history_db_row.py`

## Parallel Work Notes

This node started with multiple subagents. Two larger worker attempts were rate-limited with HTTP 429 and were closed without integrating their target scopes. Two workers left bounded patches in disjoint files:

- outcome tracking DB row codec and tests
- strategy candidate research queue history DB row codec and tests

The controller took over those patches after interruption, reviewed the diffs, tightened one test isolation issue, ran verification, requested local opencode review, committed, and wrote this handoff.

No worker touched stores, migrations, psycopg, Supabase configuration, auth, wallet/private keys, live trading, order placement, signing, submission, cancel, replace, exchange mutation, or network mutation paths.

## Behavior Implemented

Outcome tracking DB row:

- New writes emit fixed six-place Decimal strings for explicit outcome/evidence Decimal payload paths.
- Equivalent Decimal exponents produce identical `payload_json` and `report_sha256`.
- `from_db_row` validates `report_sha256` against the raw stored payload before legacy Decimal normalization.
- Legacy Decimal strings are accepted only for explicit allowlisted outcome/evidence paths and only when the recovered report reserializes to the expected canonical payload.
- Raw Python `Decimal`, `datetime`, and float values inside `payload_json` are rejected before normalization can hide them.
- Materialized fields compare against payload values with exact type and value checks for non-Decimal scalars.
- Value-changing legacy Decimal strings and stale hashes are rejected.

Strategy candidate research queue history DB row:

- New writes emit fixed six-place Decimal strings for explicit top-level Decimal fields:
  - `total_ready_notional`
  - `total_selected_notional`
  - `total_suggested_notional`
  - `latest_top_research_priority_score`
  - `latest_average_research_ready_score`
  - `ready_notional_delta`
  - `selected_notional_delta`
- Equivalent Decimal exponents produce identical `payload_json` and `report_sha256`.
- `from_db_row` validates `report_sha256` against the raw stored payload before legacy Decimal normalization.
- Legacy Decimal strings are accepted only for the explicit top-level allowlist and only when the recovered report reserializes to the canonical payload.
- Raw Python `Decimal`, `datetime`, and float values inside `payload_json` are rejected before normalization.
- Fixed six-place values use `format(..., "f")`, including integer-valued Decimals such as `42.000000`.
- Overprecision is rejected without rounding, including large values through a local decimal context sized for the input.

## Boundary Check

The node did not add or change:

- local or remote database clients
- SQLite, file-backed DBs, JSONL durable persistence, SQLAlchemy, Redis, Mongo, or generic DB abstractions
- Supabase/Postgres configuration
- auth, wallet, private key, mnemonic, or account reads
- live trading, order placement, signing, submission, cancel, replace, or exchange mutation

The phase remains paper-only/report-only/readonly.

## Verification

Target tests:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' PYTHONPATH=src python3 -m pytest -q tests/test_outcome_tracking_db_row.py tests/test_strategy_candidate_research_queue_history_db_row.py
```

Result: `117 passed`

Affected slice:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' PYTHONPATH=src python3 -m pytest -q tests/test_outcome_tracking_db_row.py tests/test_outcome_tracker.py tests/test_forecast_evidence.py tests/test_strategy_candidate_research_queue_history_db_row.py tests/test_strategy_candidate_research_queue_history.py tests/test_strategy_candidate_research_queue_db_row.py tests/test_strategy_candidate_research_queue.py
```

Result: `255 passed`

DB-row regression:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' PYTHONPATH=src python3 -m pytest -q tests/test_*db_row.py
```

Result: `1728 passed`

Full suite:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' PYTHONPATH=src python3 -m pytest -q
```

Result: `9573 passed, 1 skipped`

Compile:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m compileall -q src tests
```

Result: passed

Diff hygiene:

```bash
git diff --check
```

Result: clean

Secret scan over changed files:

- Result: clean

CodeGraph:

```bash
codegraph sync
```

Result: synced 1 changed file.

## Review

Local opencode read-only review:

```bash
opencode run --format json --model zhipuai-coding-plan/glm-5.2 --variant max --dir /home/ubuntu/polymarket-alpha-lab "<read-only review prompt>"
```

Review package:

- `/tmp/polymarket-alpha-lab-review/outcome-strategy-history-decimal-review-package.md`

Review artifact:

- `/tmp/polymarket-alpha-lab-review/outcome-strategy-history-decimal-opencode-review.jsonl`

Verdict:

- `APPROVED`

Blocking findings:

- none

Non-blocking observation applied after review:

- The outcome raw payload rejection test now self-hashes JSON-serializable raw float payloads and uses the stale canonical hash only for raw `Decimal`/`datetime` cases that cannot be JSON-hashed. This keeps the raw-value rejection path covered while avoiding test helper serialization failures.

## Next Recommended Targets

Continue with disjoint codec/test pairs to preserve parallel development without file conflicts:

- `paper_probability_selection_summary_history_db_row.py`
- `strategy_candidate_research_queue_db_row.py`
- `paper_probability_recommendation_queue_db_row.py`
- `paper_autonomous_allocation_proposal_db_row.py`

Use the same gate:

- TDD with RED evidence before implementation
- focused and affected tests
- DB-row regression and full suite
- compileall and diff hygiene
- secret/persistence/trading static scans
- CodeGraph sync
- local opencode read-only review with `zhipuai-coding-plan/glm-5.2 --variant max`
- commit, handoff, push after approval
