# NAV Decimal Compatibility Implementation Handoff

Date: 2026-06-26

## Node Summary

Implemented and pushed the first Group A Decimal compatibility reader node for
the NAV snapshot DB row codec.

Committed and pushed:

- `e695e09 fix: harden NAV snapshot Decimal payload codec`

Changed files:

- `src/polymarket_alpha_lab/paper_nav_snapshot_db_row.py`
- `tests/test_paper_nav_snapshot_db_row.py`

## What Changed

- Added fixed six-place Decimal serialization for NAV snapshot DB row writes
  using `Decimal("0.000001")` and fixed-point formatting.
- Rejected non-finite Decimals and value-changing overprecision before write.
- Canonicalized signed zero to `0.000000` so `Decimal("-0")` and
  `Decimal("0")` hash identically.
- Added raw stored-payload validation that rejects Python `float`, `Decimal`,
  and `datetime` values before any JSON normalization can hide them.
- Re-ran row shape validation in `paper_nav_snapshot_from_db_row`, covering
  `object.__new__` bypassed rows.
- Required raw `payload_json` hash validation before any compatibility
  comparison.
- Added strict type-and-value checks for non-Decimal materialized fields, so
  bool/int confusion is rejected.
- Added narrow legacy compatibility only for these top-level materialized NAV
  Decimal payload paths:
  - `starting_cash`
  - `cash_balance`
  - `exit_nav`
  - `midpoint_nav`
  - `total_cost_basis`
  - `unrealized_exit_pnl`
- Kept `realized_pnl` and all nested mark Decimal paths canonical-only for this
  first NAV implementation node.
- Preserved NAV's existing phase flag shape: the codec carries `paper_only`
  only, and does not require `report_only` or `readonly` payload keys.
- Preserved the paper-only/import-only surface; no live trading, auth, wallet,
  order mutation, network, or database mutation code was introduced.

## Tests Added

Expanded `tests/test_paper_nav_snapshot_db_row.py` to cover:

- fixed six-place canonical payload output
- equivalent Decimal exponent hash stability
- zero and large fixed-notation values
- signed-zero canonicalization
- overprecision rejection without rounding
- self-hashed allowed legacy top-level materialized Decimal payload strings
- stale legacy hash rejection
- value-changing legacy payload rejection
- raw `Decimal` payload rejection before normalization
- bypassed nested float payload rejection
- missing nullable key versus explicit `null`
- bool/int confusion on bypassed rows

## Verification

Commands run after the final signed-zero patch:

```bash
python3 -m pytest tests/test_paper_nav_snapshot_db_row.py -q
python3 -m pytest \
  tests/test_paper_nav_snapshot_db_row.py \
  tests/test_positions.py \
  tests/test_json_recovery.py \
  tests/test_history_readers.py \
  tests/test_performance_summary.py \
  tests/test_paper_nav_liquidity_risk.py \
  -q
python3 -m compileall -q \
  src/polymarket_alpha_lab/paper_nav_snapshot_db_row.py \
  tests/test_paper_nav_snapshot_db_row.py
python3 -m pytest tests/test_*db_row.py -q
python3 -m pytest -q
git diff --check
codegraph sync
```

Observed results:

- Target NAV DB row tests: `21 passed`.
- Affected NAV/recovery tests: `110 passed`.
- DB row test set: `1678 passed`.
- Full suite: `9523 passed, 1 skipped`.
- Compileall passed.
- Diff check passed.
- CodeGraph reported already up to date after the final patch.
- Credential-pattern scan had one expected false positive: the literal
  `api_key` appears inside the pure-paper source-scan test's banned-word list.

## Review

Read-only opencode reviews used:

```bash
opencode run --format json \
  --model zhipuai-coding-plan/glm-5.2 \
  --variant max \
  --dir /home/ubuntu/polymarket-alpha-lab \
  "<read-only NAV Decimal compatibility review prompt>"
```

Review artifacts:

- `/tmp/polymarket-alpha-lab-review/nav-decimal-compatibility-review-rerun.jsonl`
- `/tmp/polymarket-alpha-lab-review/nav-decimal-compatibility-followup.jsonl`

Review verdicts:

- Main review: approved, no blockers.
- Follow-up after signed-zero patch: approved, no blockers.

Non-blocking review note:

- Pre-patch rows with non-canonical Decimal strings in non-materialized payload
  fields such as `realized_pnl` or nested marks will be rejected by the new
  reader. This is intentional for the first Group A NAV node because only the
  six top-level materialized Decimal paths are allowlisted for legacy numeric
  compatibility. If populated databases contain such rows, handle them with an
  explicit migration/backfill rather than widening this codec silently.

## Repo State At Node Commit

After push:

```text
HEAD:        e695e099dcf085f5d105501bfd90a7c5ec6cc049
origin/main: e695e099dcf085f5d105501bfd90a7c5ec6cc049
```

## Next Recommended Step

Start the next Group A codec only after treating the NAV node as the reference
pattern. Recommended candidates remain:

- `paper_trade_journal_db_row.py`
- `paper_trade_cost_audit_db_row.py`
- `action_gated_strategy_recommendation_queue_db_row.py`
- `outcome_tracking_db_row.py`

For the next node:

- Use TDD.
- Keep raw stored hash validation before compatibility normalization.
- Use codec-local explicit Decimal allowlists.
- Do not widen nested Decimal compatibility without a written sign/domain
  validation rule.
- Keep persistence local Supabase/Postgres-only and remain paper-only,
  report-only, and read-only.
