# Paper Trade Journal Decimal Compatibility Implementation Handoff

Date: 2026-06-26

## Node Summary

Implemented and pushed the next Group A Decimal compatibility reader node for
the paper trade journal DB row codec.

Committed and pushed:

- `3d13338 fix: harden paper trade journal Decimal payload codec`

Changed files:

- `src/polymarket_alpha_lab/paper_trade_journal_db_row.py`
- `tests/test_paper_trade_journal_db_row.py`

## What Changed

- Added fixed six-place Decimal serialization for new paper trade journal DB row
  payload writes using `Decimal("0.000001")` and fixed-point formatting.
- Rejected non-finite Decimals and value-changing overprecision before
  persistence.
- Canonicalized signed zero to `0.000000` so `Decimal("-0")` and
  `Decimal("0")` hash identically.
- Replaced stored-payload normalization with a raw JSON copy step that rejects
  Python `float`, `Decimal`, and `datetime` values before helper code can hide
  them.
- Re-ran row core validation in `paper_trade_record_from_db_row`, covering
  rows constructed with `object.__new__`.
- Required raw `payload_json` hash validation before any Decimal compatibility
  comparison.
- Added strict type-and-value matching for non-Decimal materialized fields, so
  bool/int confusion is rejected.
- Added codec-local Decimal compatibility only for explicit flat
  `PaperTradeRecord` Decimal payload paths:
  - `model_probability`
  - `confidence`
  - `research_bid`
  - `research_ask`
  - `research_midpoint`
  - `research_expected_entry_price`
  - `research_fair_value_estimate`
  - `research_theoretical_edge`
  - `research_spread`
  - `research_slippage_estimate`
  - `research_cost_adjusted_edge`
  - `max_executable_size`
  - `order_requested_size`
  - `fill_filled_size`
  - `fill_unfilled_size`
  - `fill_average_price`
  - `fill_worst_price`
  - `fill_best_bid`
  - `fill_best_ask`
  - `fill_midpoint`
  - `fill_spread`
  - `fill_slippage_estimate`
  - `account_equity_before_trade`
- Kept materialized row-vs-payload Decimal numeric matching limited to:
  - `fill_filled_size`
  - `fill_average_price`
  - `account_equity_before_trade`
- Preserved the paper-only/import-only surface; no live trading, auth, wallet,
  order mutation, network mutation, or new persistence backend code was
  introduced.

## Tests Added

Expanded `tests/test_paper_trade_journal_db_row.py` to cover:

- fixed six-place canonical payload output
- equivalent Decimal exponent hash stability
- zero-value canonicalization
- signed-zero canonicalization
- non-finite Decimal rejection before persistence
- overprecision rejection without rounding
- raw `Decimal` payload rejection before normalization
- raw `datetime` payload rejection before normalization
- raw `float` payload rejection
- self-hashed allowed legacy flat Decimal payload strings
- stale legacy hash rejection on both constructor and bypassed read paths
- value-changing legacy payload rejection
- bypassed overprecision payload rejection
- noncanonical datetime payload rejection
- bool/int confusion on bypassed rows
- malformed payload and hash mismatch defenses

## Verification

Commands run after the final test additions:

```bash
python3 -m pytest tests/test_paper_trade_journal_db_row.py -q
python3 -m pytest -q \
  tests/test_paper_trade_journal_db_row.py \
  tests/test_journal.py \
  tests/test_json_recovery.py
python3 -m pytest -q \
  tests/test_paper_trade_journal_store.py \
  tests/test_paper_trade_journal_psycopg.py \
  tests/test_psycopg_adapter_cleanup.py \
  tests/test_paper_trade_journal_db_cost_trend_load.py
python3 -m pytest -q \
  tests/test_cli.py::test_strategy_cycle_cli_wires_paper_trade_db_sink_when_enabled \
  tests/test_cli.py::test_strategy_cycle_cli_redacts_dsn_when_paper_trade_db_sink_fails \
  tests/test_cli.py::test_run_cli_wires_paper_trade_and_nav_db_sinks_when_env_enabled \
  tests/test_cli.py::test_run_cli_redacts_dsn_when_paper_trade_db_sink_failure_is_reported \
  tests/test_cli.py::test_run_cli_default_loop_persists_paper_trade_and_nav_db_sinks_from_real_cycle
python3 -m pytest tests/test_*db_row.py -q
python3 -m compileall -q \
  src/polymarket_alpha_lab/paper_trade_journal_db_row.py \
  tests/test_paper_trade_journal_db_row.py
git diff --check
codegraph sync
python3 -m pytest -q
```

Observed results:

- Target journal DB row tests: `22 passed`.
- Journal/recovery affected slice: `100 passed`.
- Store/psycopg/cost-trend affected slice: `90 passed`.
- CLI sink wiring affected slice: `5 passed`.
- DB row test set: `1690 passed`.
- Full suite: `9535 passed, 1 skipped`.
- Compileall passed.
- Diff check passed.
- CodeGraph reported already up to date.
- Credential-pattern scan over the changed source/test files had only expected
  false positives inside the pure-paper banned-word test list.

## Review

Read-only opencode reviews used:

```bash
opencode run --format json \
  --model zhipuai-coding-plan/glm-5.2 \
  --variant max \
  --dir /home/ubuntu/polymarket-alpha-lab \
  "<read-only paper trade journal Decimal compatibility review prompt>"
```

Review artifacts:

- `/tmp/polymarket-alpha-lab-review/journal-decimal-compatibility-review.jsonl`
- `/tmp/polymarket-alpha-lab-review/journal-decimal-compatibility-followup.jsonl`

Review verdicts:

- Main review after the implementation: approved, no blockers.
- Follow-up after additional edge-case tests: approved, no blockers.

Non-blocking review notes:

- Value-preserving overprecise legacy Decimal strings such as `0.514000000`
  are accepted on read when the stored hash matches the stored payload. This is
  consistent with the explicit legacy-equivalent Decimal compatibility policy;
  reserialization returns the fixed six-place canonical string.
- If `PaperTradeRecord` gains new Decimal fields later, legacy short-form
  strings for the new field will fail closed until the codec-local allowlist and
  tests are updated.

## Repo State At Node Commit

After push:

```text
HEAD:        3d13338e87e270dbd7acd90b9adff41dd50db0a8
origin/main: 3d13338e87e270dbd7acd90b9adff41dd50db0a8
```

## Supabase-Only Persistence Follow-Up

A parallel read-only scan found that the repository still contains legacy
JSONL/file-backed journals, raw archive writers, local JSON/JSONL input
loaders, and DB-API-style store modules. Under the strict project rule that all
project data persistence must use local Supabase/Postgres only, those are
migration candidates.

This node did not migrate those surfaces because it was scoped to a pure DB row
codec compatibility fix. The next persistence cleanup should be a planned
migration node, not an opportunistic edit inside Decimal codec work.

Recommended follow-up:

- Freeze new file-backed persistence in `AGENTS.md`.
- Inventory existing JSONL/file-backed write paths.
- Migrate one write path at a time to local Supabase/Postgres.
- Keep legacy file readers only behind explicit read-only compatibility
  boundaries until equivalent Supabase/Postgres backfills exist.

## Next Recommended Step

Continue Group A Decimal compatibility work with:

- `src/polymarket_alpha_lab/paper_trade_cost_audit_db_row.py`
- `tests/test_paper_trade_cost_audit_db_row.py`

Use the cost-audit design handoff from the read-only subagent:

- allow legacy equivalent strings only for top-level materialized summary
  Decimal fields
- keep payload Decimal strings canonical
- keep the hash anchored to canonical `payload_json`
- reject bools, floats, non-finite strings, and noncanonical row strings that
  would break payload parity
