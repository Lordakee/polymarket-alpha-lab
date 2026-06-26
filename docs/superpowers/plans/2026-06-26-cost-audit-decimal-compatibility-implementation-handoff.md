# Cost Audit Decimal Compatibility Implementation Handoff

Date: 2026-06-26

## Node Summary

- Commit: `5e48c9b6bcfb827c48bcdaad9353e3635706104f`
- Subject: `fix: harden cost-audit Decimal row compatibility`
- Scope: Group A Decimal compatibility hardening for `paper_trade_cost_audit_db_row.py`.
- Changed files:
  - `src/polymarket_alpha_lab/paper_trade_cost_audit_db_row.py`
  - `tests/test_paper_trade_cost_audit_db_row.py`

## What Changed

- Added strict row-core validation in `paper_trade_cost_audit_report_from_db_row()` so `object.__new__` bypassed rows cannot reach later code with invalid row field types.
- Replaced inbound `payload_json` normalization with a strict JSON copier that rejects raw Python `Decimal`, `float`, `datetime`, non-string object keys, tuples, and other non-JSON runtime objects before normalization can hide them.
- Kept `report_sha256` validation tied to the exact stored `payload_json` bytes before Decimal compatibility recovery.
- Added top-level path-scoped Decimal compatibility for the cost-audit summary payload fields only.
- Changed materialized Decimal matching from exact JSON string rendering to finite Decimal numeric equality, including nullable fields.
- Preserved existing size-field write spellings for `total_filled_size` and `total_requested_size` such as `"240"` and `"300"`, avoiding a cost-audit hash migration.
- Canonicalized quantized cost-audit Decimal write fields to six fixed decimal places and rejected overprecision instead of rounding.
- Canonicalized signed zero on size field writes to `"0"`; quantized signed zeros become `"0.000000"`.
- Preserved `paper_only`, `report_only`, `readonly`, local Supabase/Postgres-only persistence assumptions, and no live trading/auth/order mutation surfaces.

## Legacy Decimal Allowlist

Compatibility is limited to these explicit top-level payload paths:

- `total_filled_size`
- `total_requested_size`
- `fill_rate`
- `mean_theoretical_edge`
- `mean_cost_adjusted_edge`
- `mean_edge_cost_drag`
- `total_edge_cost_drag`
- `mean_research_slippage`
- `mean_fill_slippage`
- `largest_single_trade_cost_drag`

No nested or future Decimal-looking strings are compatible unless the allowlist and tests are deliberately updated.

## Tests Added Or Updated

- New-write equivalent quantized Decimal exponent canonicalization and stable hash.
- Signed-zero size Decimal canonicalization.
- Quantized overprecision rejection without rounding.
- Equivalent materialized Decimal exponent readback from bypassed rows.
- Self-hashed legacy Decimal payload readback for allowlisted fields.
- Stale legacy payload hash rejection.
- Value-changing legacy payload rejection.
- Raw Decimal and raw datetime payload rejection before normalization, including bypassed rows.
- Bool/int confusion rejection in bypassed rows.
- Bypassed non-datetime `generated_at` rejection as controlled `ValueError`.
- Bypassed overprecision payload rejection.
- Existing noncanonical payload/hash tests updated from equivalent spellings to value-changing spellings.

## Verification

Commands run after implementation:

```bash
python3 -m pytest tests/test_paper_trade_cost_audit_db_row.py -q
# 52 passed

python3 -m pytest tests/test_paper_trade_cost_audit.py tests/test_paper_trade_cost_audit_db_row.py tests/test_paper_trade_cost_audit_store.py tests/test_paper_trade_cost_audit_db_scope.py tests/test_cli_cost_audit_db_trend.py tests/test_paper_trade_cost_audit_db_history_load.py tests/test_paper_trade_journal_db_cost_trend_load.py -q
# 116 passed

python3 -m pytest tests/test_paper_trade_journal_db_row.py tests/test_paper_trade_cost_audit_db_row.py -q
# 74 passed

python3 -m pytest tests/test_*db_row.py -q
# 1701 passed

python3 -m pytest -q
# 9546 passed, 1 skipped

python3 -m compileall -q src tests
# passed

git diff --check
# passed

codegraph sync
# already up to date
```

Secret scan over the changed code/test diff found no matches for common GitHub, OpenAI, AWS, or private-key patterns.

## Review

Read-only subagent support completed for:

- RED-test matrix and compatibility edge cases.
- Journal/NAV helper pattern comparison.
- Supabase/Postgres migration and store parity.
- Handoff/review checklist.

Local opencode review was attempted three times using `zhipuai-coding-plan/glm-5.2` with `--variant max` and read-only prompts. All three attempts timed out before producing a final verdict or findings. Artifacts:

- `/tmp/polymarket-alpha-lab-review/cost-audit-decimal-compatibility-review.jsonl`
- `/tmp/polymarket-alpha-lab-review/cost-audit-decimal-compatibility-review-2.jsonl`
- `/tmp/polymarket-alpha-lab-review/cost-audit-decimal-compatibility-review-3.jsonl`
- `/tmp/polymarket-alpha-lab-review/cost-audit-decimal-compatibility.diff`
- `/tmp/polymarket-alpha-lab-review/cost-audit-decimal-compatibility-v2.diff`

No opencode approval should be inferred from those artifacts; they are retained as evidence of the failed review attempts.

## Repo State At Node Commit

- `HEAD`: `5e48c9b6bcfb827c48bcdaad9353e3635706104f`
- `origin/main`: `5e48c9b6bcfb827c48bcdaad9353e3635706104f`
- Worktree after the code push: clean before this handoff document was added.

## Next Recommended Step

Continue Group A DB-row Decimal compatibility with the next flat or explicitly reviewed payload surface, likely `action_gated_strategy_recommendation_queue_db_row.py` or `outcome_tracking_db_row.py`. Keep the same pattern: TDD first, strict JSON boundary, raw-hash-first read compatibility, explicit path allowlists, local Supabase/Postgres only, and no live/auth/order mutation.

