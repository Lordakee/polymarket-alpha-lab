# Group A Decimal Compatibility Reader Design Handoff

Date: 2026-06-26

## Node Summary

Completed and pushed the Group A Decimal compatibility-reader design gate.

Committed and pushed:

- `03d9299 docs: design Group A Decimal compatibility reader`

Changed file:

- `docs/superpowers/plans/2026-06-26-db-row-decimal-compatibility-reader-design.md`

## What Changed

- Defined the dual-canonicality reader contract for Group A DB row codecs.
- Required raw stored hash validation before any Decimal compatibility normalization.
- Defined "raw stored hash" as the codec's existing hash helper over parsed raw `payload_json` using canonical JSON serialization, not byte-for-byte Postgres `jsonb` bytes.
- Required raw floats and raw `Decimal` objects to be rejected before helpers can normalize payloads through `_json_ready`.
- Required `from_db_row` to independently re-run raw hash, raw-payload type, materialized-field, and flag checks, even for rows built with `object.__new__`.
- Required codec-local explicit Decimal allowlists.
- Required materialized Decimal numeric matching only on allowlisted paths; non-Decimal fields remain exact type-and-value matches.
- Required bool/int checks to use identity/type checks.
- Required six-place fixed-notation new writes using quantize plus `format(..., "f")`, including zero and large-value tests.
- Chose `paper_nav_snapshot_db_row.py` as the first Group A implementation candidate.
- Explicitly deferred trade journal, cost audit, action-gated queue, and outcome tracking until after the NAV pattern lands.
- Clarified NAV's current phase flags: the codec carries `paper_only`; it does not carry `report_only` or `readonly` row fields.
- Identified initial NAV materialized Decimal allowlist candidates:
  - `starting_cash`
  - `cash_balance`
  - `exit_nav`
  - `midpoint_nav`
  - `total_cost_basis`
  - `unrealized_exit_pnl`
- Deferred `realized_pnl` and per-position mark Decimal paths from the initial NAV allowlist pending explicit sign/domain validation.

## Verification

Commands run:

```bash
python3 - <<'PY'
from pathlib import Path
path = Path('docs/superpowers/plans/2026-06-26-db-row-decimal-compatibility-reader-design.md')
needles = ('T' + 'BD', 'TO' + 'DO', 'implement ' + 'later', 'fill in ' + 'details')
for line_no, line in enumerate(path.read_text(encoding='utf-8').splitlines(), 1):
    if any(needle in line for needle in needles):
        raise SystemExit(f'{path}:{line_no}: placeholder text found')
print('placeholder scan passed')
PY

git diff --check
codegraph sync
git diff --cached --check
```

Observed results:

- Placeholder scan passed.
- Diff checks passed.
- CodeGraph sync reported already up to date.
- Credential-pattern scan over the design document produced no matches.

## Review

Read-only opencode reviews used:

```bash
opencode run --format json \
  --model zhipuai-coding-plan/glm-5.2 \
  --variant max \
  --dir /home/ubuntu/polymarket-alpha-lab \
  "<read-only design review prompt>"
```

Review artifacts:

- `/tmp/polymarket-alpha-lab-review/group-a-decimal-compatibility-reader-design-review.jsonl`
- `/tmp/polymarket-alpha-lab-review/group-a-decimal-compatibility-reader-design-followup.jsonl`

Review verdicts:

- Main design review: approved, no blockers.
- Follow-up after incorporating all seven clarifications: approved, no blockers.

## Repo State At Node Commit

After push:

```text
HEAD:        03d9299abe0d0c0cb706a1f583e76b45c9469081
origin/main: 03d9299abe0d0c0cb706a1f583e76b45c9469081
```

## Next Recommended Step

Start the first Group A implementation node:

- codec: `src/polymarket_alpha_lab/paper_nav_snapshot_db_row.py`
- tests: `tests/test_paper_nav_snapshot_db_row.py`

Required first actions:

- Use TDD.
- Confirm the local Decimal quantum constant name is unused before adding it.
- Add RED tests for:
  - six-place fixed-notation new writes, including zero and a large NAV value
  - self-hashed legacy NAV row read success only for explicitly allowlisted Decimal paths
  - stale legacy hash rejection
  - value-changing legacy payload rejection
  - raw float and raw `Decimal` payload rejection before `_json_ready` normalization
  - missing nullable key versus explicit `null`
  - bool/int confusion, including `paper_only: 1` and `mark_count: True`
  - `object.__new__` bypass validation in `from_db_row`
  - over-precision rejection without rounding
  - pure paper-only import surface

Do not touch the remaining Group A codecs until the NAV pattern is reviewed, committed, pushed, and handed off.
