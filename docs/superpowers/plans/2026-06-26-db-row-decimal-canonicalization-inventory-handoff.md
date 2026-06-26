# DB Row Decimal Canonicalization Inventory Handoff

Date: 2026-06-26

## Node Summary

Completed the Decimal canonicalization planning/inventory repair node.

Committed and pushed:

- `08f8422 docs: inventory DB row Decimal canonicalization`

Changed files:

- `docs/superpowers/plans/2026-06-26-db-row-decimal-canonicalization-migration.md`
- `docs/superpowers/plans/2026-06-26-db-row-decimal-canonicalization-inventory.md`

## What Changed

- Replaced unconditional push wording with an explicit push policy:
  push only when explicitly authorized; this project thread currently has explicit authorization to push verified nodes.
- Added a hard Group A gate: no Group A Decimal canonicalization implementation until the compatibility-reader design doc is reviewed and committed.
- Added explicit `codegraph sync` steps to the migration plan.
- Added Task 2 requirements for:
  - legacy-payload read guard testing
  - `_DECIMAL_QUANTUM` name availability check before adding the constant
- Expanded the inventory to one matrix row for every git-tracked `src/polymarket_alpha_lab/*_db_row.py` codec.
- Inventory now includes all 42 DB row codec files and records:
  - group
  - current Decimal format or no Decimal surface
  - hash field
  - compatibility choice
  - required tests
- Explicitly classified `paper_order_lifecycle_db_row.py` as pure paper/order-lifecycle reporting only, with no live order placement/cancel/replace surface.
- Re-stated local Supabase/Postgres-only persistence and paper-only/report-only/readonly boundaries.

## Verification

Commands run:

```bash
python3 - <<'PY'
from pathlib import Path
paths = [
    Path('docs/superpowers/plans/2026-06-26-db-row-decimal-canonicalization-migration.md'),
    Path('docs/superpowers/plans/2026-06-26-db-row-decimal-canonicalization-inventory.md'),
]
needles = ('T' + 'BD', 'TO' + 'DO', 'implement ' + 'later', 'fill in ' + 'details')
for path in paths:
    for line_no, line in enumerate(path.read_text(encoding='utf-8').splitlines(), 1):
        if any(needle in line for needle in needles):
            raise SystemExit(f'{path}:{line_no}: placeholder text found')
print('placeholder scan passed')
PY

python3 - <<'PY'
from pathlib import Path
import re
import subprocess
path = Path('docs/superpowers/plans/2026-06-26-db-row-decimal-canonicalization-inventory.md')
tracked = [Path(p).name for p in subprocess.check_output(['git','ls-files','src/polymarket_alpha_lab/*_db_row.py'], text=True).splitlines()]
rows = []
for line in path.read_text(encoding='utf-8').splitlines():
    m = re.match(r'^\| `([^`]+)` \|', line)
    if m:
        rows.append(m.group(1))
if rows != tracked:
    raise SystemExit('inventory row list mismatch')
print(f'inventory rows: {len(rows)}; tracked DB row codecs: {len(tracked)}')
PY

git diff --check
codegraph sync
git diff --cached --check
```

Observed results:

- Placeholder scan passed.
- Inventory rows: 42; tracked DB row codecs: 42.
- `git diff --check` passed.
- `codegraph sync` reported already up to date.
- Staged diff check passed.
- Credential-pattern scan over changed docs produced no matches.

## Review

Opencode review used:

```bash
opencode run --format json \
  --model zhipuai-coding-plan/glm-5.2 \
  --variant max \
  --dir /home/ubuntu/polymarket-alpha-lab \
  "<read-only review prompt>"
```

Review artifacts:

- `/tmp/polymarket-alpha-lab-review/decimal-canonicalization-inventory-plan-review-rerun.jsonl`
- `/tmp/polymarket-alpha-lab-review/decimal-canonicalization-inventory-plan-review-followup.jsonl`

Review verdicts:

- Main review: approved, no blockers.
- Follow-up after adding the global phase-boundary sentence: approved, no blockers.

## Repo State At Node Commit

After push:

```text
HEAD:        08f8422b9db026a3c1049f7e4f09df00600cf7b0
origin/main: 08f8422b9db026a3c1049f7e4f09df00600cf7b0
```

## Next Recommended Step

Begin Task 2 from the migration plan:

- target codec: `src/polymarket_alpha_lab/action_gated_strategy_recommendation_queue_history_db_row.py`
- target test: `tests/test_action_gated_strategy_recommendation_queue_history_db_row.py`

Required first actions:

- Add RED tests for equivalent Decimal new-write canonicalization and legacy-payload read guard.
- Verify `_DECIMAL_QUANTUM` is not already present in the target codec/test before adding it.
- Implement only the minimal Group B codec change.
- Run targeted RED/GREEN, affected tests, full suite, opencode review, `codegraph sync`, commit, push, and a new handoff.

Do not start any Group A codec implementation until the compatibility-reader design document has been reviewed and committed.
