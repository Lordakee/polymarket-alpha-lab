# DB Row Decimal Canonicalization Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make DB row Decimal JSON encoding canonical without silently breaking historical payload hash compatibility.

**Architecture:** Treat Decimal canonicalization as a staged persistence migration, not a mechanical serializer refactor. Each task hardens one codec group with RED tests, explicit hash-impact notes, and compatibility decisions before changing production code.

**Tech Stack:** Python dataclasses, `Decimal`, JSON payload hashes, pytest, local Supabase/Postgres persistence boundaries.

## Global Constraints

- All DB persistence must use local Supabase/Postgres only.
- No SQLite, file DB, hosted/generic DB abstraction, SQLAlchemy, Redis, or Mongo.
- Phase boundary remains paper-only/report-only/readonly.
- No live trading, auth, wallet/private-key/account reads, order placement/signing/submission/cancel/replace, or exchange mutation.
- Use `Decimal` only for money/probability/cost arithmetic; do not introduce `float`.
- Preserve existing `from_db_row` read compatibility unless a task explicitly documents a migration boundary and tests it.
- Group A compatibility-reader design gate: Task 3 must be reviewed and committed before any Group A codec implementation begins. If branch policy requires remote landing, push only under the push policy below.
- For each task, run affected tests, full suite, opencode review with model `zhipuai-coding-plan/glm-5.2 --variant max`, an explicit `codegraph sync` step, commit, and a handoff document.
- Push policy: push only when explicitly authorized. This project thread currently has explicit user authorization to push verified nodes; without active explicit authorization, stop after the verified local commit and report the push command instead of running it.

---

## File Structure

- Modify per-task DB row codec files under `src/polymarket_alpha_lab/*_db_row.py`.
- Modify matching tests under `tests/test_*_db_row.py`.
- Add a migration/handoff note per completed task under `docs/superpowers/plans/`.
- Do not create shared Decimal utility code in the first task. Only add one after two or more completed tasks prove a repeated pattern and the compatibility contract is stable.

## Migration Groups

### Group A: Definite Snapshot/Hash Change

These files have direct tests or known payloads using non-six-place strings. They require explicit compatibility decisions before changing output:

No Group A implementation may start until `docs/superpowers/plans/2026-06-26-db-row-decimal-compatibility-reader-design.md` has landed through Task 3 review and commit.

- `src/polymarket_alpha_lab/paper_nav_snapshot_db_row.py`
- `src/polymarket_alpha_lab/paper_trade_journal_db_row.py`
- `src/polymarket_alpha_lab/outcome_tracking_db_row.py`
- `src/polymarket_alpha_lab/paper_trade_cost_audit_db_row.py`
- `src/polymarket_alpha_lab/action_gated_strategy_recommendation_queue_db_row.py`

### Group B: Low Fixture Churn, Persisted Hash Risk

These mostly test six-place strings today, but output hash can still change for equivalent Decimals with different exponent:

- `src/polymarket_alpha_lab/action_gated_strategy_recommendation_queue_history_db_row.py`
- `src/polymarket_alpha_lab/paper_autonomous_allocation_proposal_db_history_metrics_evaluation_db_row.py`
- `src/polymarket_alpha_lab/paper_autonomous_allocation_proposal_db_row.py`
- `src/polymarket_alpha_lab/paper_broker_db_row.py`
- `src/polymarket_alpha_lab/paper_execution_reconciliation_db_row.py`
- `src/polymarket_alpha_lab/strategy_candidate_research_queue_db_row.py`
- `src/polymarket_alpha_lab/strategy_candidate_research_queue_history_db_row.py`

### Group C: Nested/Payload-Only or Latent Decimal Branches

These are lower priority or require deeper payload compatibility review:

- `src/polymarket_alpha_lab/local_observability_trends_db_row.py`
- `src/polymarket_alpha_lab/paper_probability_recommendation_queue_db_row.py`
- `src/polymarket_alpha_lab/paper_probability_selection_summary_db_row.py`
- `src/polymarket_alpha_lab/paper_probability_selection_summary_history_db_row.py`
- `src/polymarket_alpha_lab/paper_project_screening_rank_stability_db_row.py`
- `src/polymarket_alpha_lab/paper_research_packet_db_row.py`
- `src/polymarket_alpha_lab/paper_research_packet_operator_flow_db_row.py`
- `src/polymarket_alpha_lab/paper_research_packet_quality_db_row.py`
- `src/polymarket_alpha_lab/strategy_recommendation_rank_stability_db_row.py`
- `src/polymarket_alpha_lab/strategy_risk_audit_db_row.py`

---

### Task 1: Inventory And Compatibility Matrix

**Files:**
- Create: `docs/superpowers/plans/2026-06-26-db-row-decimal-canonicalization-inventory.md`
- No production code changes.

**Interfaces:**
- Consumes: read-only scan results from the previous subagent report.
- Produces: a table with one row per codec, one compatibility choice, and the tests that prove it.

- [ ] **Step 1: Write the inventory document**

Create `docs/superpowers/plans/2026-06-26-db-row-decimal-canonicalization-inventory.md` with this structure:

```markdown
# DB Row Decimal Canonicalization Inventory

## Compatibility Policy

- New writes should prefer six-place canonical Decimal strings.
- Existing rows must remain readable unless this document marks a codec as requiring a hash migration.
- `from_db_row` may accept legacy payload strings only when the raw `report_sha256` matches the legacy payload exactly and recovered report validation proves the payload is semantically safe.
- The inventory matrix must contain one row for every tracked `src/polymarket_alpha_lab/*_db_row.py` file and must verify that count against `git ls-files`.

## Codec Matrix

| Codec | Group | Current Decimal Format | Hash Field | Compatibility Choice | Required Tests |
|---|---|---|---|---|---|
| paper_nav_snapshot_db_row.py | A | non-six-place snapshots | snapshot_sha256 | defer implementation; design compatibility reader first | snapshot old-read, new-write canonical |
| paper_trade_journal_db_row.py | A | non-six-place snapshots | record_sha256 | defer implementation; design compatibility reader first | journal old-read, new-write canonical |
| outcome_tracking_db_row.py | A | non-six-place snapshots | report_sha256 | defer implementation; design compatibility reader first | outcome old-read, new-write canonical |
| paper_trade_cost_audit_db_row.py | A | mixed size/ratio strings | report_sha256 | implement only after preserving integer-size semantics | cost audit old-read, ratio canonical |
| action_gated_strategy_recommendation_queue_db_row.py | A | nested 4-place inputs | report_sha256 | implement after nested payload impact review | queue nested old-read, new-write canonical |
```
```

- [ ] **Step 2: Verify inventory has no placeholders**

Run:

```bash
python3 - <<'PY'
from pathlib import Path

path = Path("docs/superpowers/plans/2026-06-26-db-row-decimal-canonicalization-inventory.md")
needles = ("T" + "BD", "TO" + "DO", "implement " + "later", "fill in " + "details")
for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
    if any(needle in line for needle in needles):
        raise SystemExit(f"{path}:{line_no}: placeholder text found")
PY
```

Expected: no matches.

- [ ] **Step 3: Verify inventory row count matches tracked DB row codecs**

Run:

```bash
python3 - <<'PY'
from pathlib import Path
import subprocess

path = Path("docs/superpowers/plans/2026-06-26-db-row-decimal-canonicalization-inventory.md")
tracked = subprocess.check_output(
    ["git", "ls-files", "src/polymarket_alpha_lab/*_db_row.py"],
    text=True,
).splitlines()
matrix_rows = [
    line for line in path.read_text(encoding="utf-8").splitlines()
    if line.startswith("| `") and line.endswith("|")
]
if len(matrix_rows) != len(tracked):
    raise SystemExit(f"matrix row count {len(matrix_rows)} != tracked DB row count {len(tracked)}")
PY
```

Expected: matrix row count equals tracked DB row codec count.

- [ ] **Step 4: Sync CodeGraph after inventory review**

Run:

```bash
codegraph sync
```

Expected: sync completes successfully, or reports no indexed source changes for this docs-only task.

- [ ] **Step 5: Commit inventory only**

Run:

```bash
git add docs/superpowers/plans/2026-06-26-db-row-decimal-canonicalization-inventory.md
git commit -m "docs: inventory DB row Decimal canonicalization"
```

Expected: commit succeeds with only the inventory document staged.

### Task 2: Choose One Group B Codec For Safe New-Write Canonicalization

**Files:**
- Modify one selected codec and matching test. Recommended first target:
  - `src/polymarket_alpha_lab/action_gated_strategy_recommendation_queue_history_db_row.py`
  - `tests/test_action_gated_strategy_recommendation_queue_history_db_row.py`

**Interfaces:**
- Consumes: Task 1 compatibility policy.
- Produces: one proven pattern for six-place new writes while preserving current `from_db_row` safety.

- [ ] **Step 1: Write RED tests for canonical new writes and legacy-payload read guard**

Add these tests to `tests/test_action_gated_strategy_recommendation_queue_history_db_row.py`:

```python
def test_action_gated_queue_history_db_row_canonicalizes_equivalent_decimal_new_writes():
    first = to_db_row(
        _history_report(
            total_ready_notional=Decimal("42"),
            ready_notional_delta=Decimal("12"),
        ),
    )
    second = to_db_row(
        _history_report(
            total_ready_notional=Decimal("42.000000"),
            ready_notional_delta=Decimal("12.000000"),
        ),
    )

    assert first.payload_json["total_ready_notional"] == "42.000000"
    assert first.payload_json["ready_notional_delta"] == "12.000000"
    assert first.payload_json == second.payload_json
    assert first.report_sha256 == second.report_sha256


def test_action_gated_queue_history_db_row_from_db_row_rejects_legacy_decimal_payload():
    row = to_db_row(
        _history_report(),
    )
    legacy_payload_json = {
        **row.payload_json,
        "total_ready_notional": "42",
        "ready_notional_delta": "12",
    }
    legacy_row = _bypassed_history_row(
        row,
        report_sha256=_payload_sha256(legacy_payload_json),
        total_ready_notional=Decimal("42"),
        ready_notional_delta=Decimal("12"),
        payload_json=legacy_payload_json,
    )

    with pytest.raises(ValueError, match="payload_json|total_ready_notional|ready_notional_delta"):
        from_db_row(
            legacy_row,
        )
```

- [ ] **Step 2: Run RED tests**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' PYTHONPATH=src /home/ubuntu/test-sandbox/.venv/bin/python -m pytest -q tests/test_action_gated_strategy_recommendation_queue_history_db_row.py::test_action_gated_queue_history_db_row_canonicalizes_equivalent_decimal_new_writes tests/test_action_gated_strategy_recommendation_queue_history_db_row.py::test_action_gated_queue_history_db_row_from_db_row_rejects_legacy_decimal_payload
```

Expected: both tests fail because current `_json_ready(Decimal("42"))` returns `"42"` and a self-hashed legacy payload still reads successfully.

- [ ] **Step 3: Confirm `_DECIMAL_QUANTUM` name is free**

Run:

```bash
rg -n '\b_DECIMAL_QUANTUM\b' src/polymarket_alpha_lab/action_gated_strategy_recommendation_queue_history_db_row.py tests/test_action_gated_strategy_recommendation_queue_history_db_row.py
```

Expected: no matches.

- [ ] **Step 4: Implement minimal six-place new-write output and legacy read guard**

In `src/polymarket_alpha_lab/action_gated_strategy_recommendation_queue_history_db_row.py`, add:

```python
_DECIMAL_QUANTUM = Decimal("0.000001")
```

Then change the Decimal branch in `_json_ready` to:

```python
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return format(value.quantize(_DECIMAL_QUANTUM), "f")
```

- [ ] **Step 5: Run GREEN tests**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' PYTHONPATH=src /home/ubuntu/test-sandbox/.venv/bin/python -m pytest -q tests/test_action_gated_strategy_recommendation_queue_history_db_row.py
```

Expected: all tests in that file pass.

- [ ] **Step 6: Run affected and full tests**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' PYTHONPATH=src /home/ubuntu/test-sandbox/.venv/bin/python -m pytest -q tests/test_action_gated_strategy_recommendation_queue_history_db_row.py tests/test_action_gated_strategy_recommendation_queue_db_row.py
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' PYTHONPATH=src /home/ubuntu/test-sandbox/.venv/bin/python -m pytest -q $(git ls-files 'tests/test_*.py')
```

Expected: both commands pass.

- [ ] **Step 7: Review with opencode**

Run opencode read-only review with:

```bash
opencode run --format json --model zhipuai-coding-plan/glm-5.2 --variant max --dir /home/ubuntu/polymarket-alpha-lab "<read-only Decimal canonicalization review prompt>"
```

Expected: approved or returns blockers that are resolved before commit.

- [ ] **Step 8: Sync CodeGraph**

Run:

```bash
codegraph sync
```

Expected: CodeGraph refresh completes and includes the changed codec/test symbols.

- [ ] **Step 9: Commit verified node**

Run:

```bash
git add src/polymarket_alpha_lab/action_gated_strategy_recommendation_queue_history_db_row.py tests/test_action_gated_strategy_recommendation_queue_history_db_row.py
git commit -m "fix: canonicalize action-gated history Decimal payloads"
```

Expected: commit succeeds with only the selected codec and matching test staged.

- [ ] **Step 10: Push only when explicitly authorized and write handoff**

Because this project thread currently has explicit user authorization to push verified nodes, run the push only after the RED/GREEN tests, affected/full tests, opencode review, CodeGraph sync, and commit have all succeeded:

```bash
git push origin main
```

If active explicit authorization is absent in a future execution thread, do not run the push; record the verified local commit hash and the exact push command in the handoff note instead.

Expected when pushed: remote `origin/main` matches local HEAD.

### Task 3: Decide Group A Compatibility Reader Design

**Files:**
- Create: `docs/superpowers/plans/2026-06-26-db-row-decimal-compatibility-reader-design.md`

**Interfaces:**
- Consumes: Task 1 inventory and Task 2 implementation evidence.
- Produces: a decision document for how to read old non-six-place payload hashes while writing new canonical payloads.

- [ ] **Step 1: Write compatibility design**

Create `docs/superpowers/plans/2026-06-26-db-row-decimal-compatibility-reader-design.md`:

```markdown
# DB Row Decimal Compatibility Reader Design

## Decision

Use dual canonicality:

- Stored row hash must match the raw stored `payload_json`.
- Recovered report must be semantically valid.
- New writes emit six-place Decimal strings.
- Readers may accept old payload strings only when materialized fields match raw payload and a normalized recovered report matches the expected semantic values.

## Non-Goals

- No live migration SQL in this task.
- No live trading, auth, wallet/private-key/account reads, order placement/signing/submission/cancel/replace, or exchange mutation.
- No SQLite, file DB, hosted/generic DB abstraction, SQLAlchemy, Redis, Mongo, or non-local Supabase/Postgres persistence.

## First Group A Candidate

Choose exactly one:

- `paper_nav_snapshot_db_row.py` if NAV snapshot compatibility matters most.
- `paper_trade_journal_db_row.py` if execution journal compatibility matters most.
- `outcome_tracking_db_row.py` if outcome validation history compatibility matters most.
```

- [ ] **Step 2: Review design with opencode**

Run:

```bash
opencode run --format json --model zhipuai-coding-plan/glm-5.2 --variant max --dir /home/ubuntu/polymarket-alpha-lab "Read-only plan review for docs/superpowers/plans/2026-06-26-db-row-decimal-compatibility-reader-design.md. Check persistence compatibility, local Supabase-only rule, paper-only boundary, and testability."
```

Expected: approved or actionable blockers.

- [ ] **Step 3: Sync CodeGraph after design review**

Run:

```bash
codegraph sync
```

Expected: sync completes successfully, or reports no indexed source changes for this docs-only task.

- [ ] **Step 4: Commit design**

Run:

```bash
git add docs/superpowers/plans/2026-06-26-db-row-decimal-compatibility-reader-design.md
git commit -m "docs: design DB row Decimal compatibility reader"
```

Expected: commit succeeds with only the design document staged.

- [ ] **Step 5: Push design only when explicitly authorized**

Because this project thread currently has explicit user authorization to push verified nodes, run:

```bash
git push origin main
```

If active explicit authorization is absent in a future execution thread, do not run the push; record the verified local commit hash and the exact push command in the handoff note instead.

Expected when pushed: remote `origin/main` matches local HEAD.
