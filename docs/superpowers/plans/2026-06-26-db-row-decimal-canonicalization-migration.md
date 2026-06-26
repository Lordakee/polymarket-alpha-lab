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
- For each task, run affected tests, full suite, opencode review with model `zhipuai-coding-plan/glm-5.2 --variant max`, CodeGraph sync, commit, push, and a handoff document.

---

## File Structure

- Modify per-task DB row codec files under `src/polymarket_alpha_lab/*_db_row.py`.
- Modify matching tests under `tests/test_*_db_row.py`.
- Add a migration/handoff note per completed task under `docs/superpowers/plans/`.
- Do not create shared Decimal utility code in the first task. Only add one after two or more completed tasks prove a repeated pattern and the compatibility contract is stable.

## Migration Groups

### Group A: Definite Snapshot/Hash Change

These files have direct tests or known payloads using non-six-place strings. They require explicit compatibility decisions before changing output:

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
python - <<'PY'
from pathlib import Path

path = Path("docs/superpowers/plans/2026-06-26-db-row-decimal-canonicalization-inventory.md")
needles = ("T" + "BD", "TO" + "DO", "implement later", "fill in details")
for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
    if any(needle in line for needle in needles):
        raise SystemExit(f"{path}:{line_no}: placeholder text found")
PY
```

Expected: no matches.

- [ ] **Step 3: Commit inventory only**

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

- [ ] **Step 1: Write RED test for canonical new write**

Add this test to `tests/test_action_gated_strategy_recommendation_queue_history_db_row.py`:

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
```

- [ ] **Step 2: Run RED test**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' PYTHONPATH=src /home/ubuntu/test-sandbox/.venv/bin/python -m pytest -q tests/test_action_gated_strategy_recommendation_queue_history_db_row.py::test_action_gated_queue_history_db_row_canonicalizes_equivalent_decimal_new_writes
```

Expected: fails because current `_json_ready(Decimal("42"))` returns `"42"`.

- [ ] **Step 3: Implement minimal six-place new-write output**

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

- [ ] **Step 4: Run GREEN tests**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' PYTHONPATH=src /home/ubuntu/test-sandbox/.venv/bin/python -m pytest -q tests/test_action_gated_strategy_recommendation_queue_history_db_row.py
```

Expected: all tests in that file pass.

- [ ] **Step 5: Run affected and full tests**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' PYTHONPATH=src /home/ubuntu/test-sandbox/.venv/bin/python -m pytest -q tests/test_action_gated_strategy_recommendation_queue_history_db_row.py tests/test_action_gated_strategy_recommendation_queue_db_row.py
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' PYTHONPATH=src /home/ubuntu/test-sandbox/.venv/bin/python -m pytest -q $(git ls-files 'tests/test_*.py')
```

Expected: both commands pass.

- [ ] **Step 6: Review, commit, push, handoff**

Run opencode read-only review with:

```bash
opencode run --format json --model zhipuai-coding-plan/glm-5.2 --variant max --dir /home/ubuntu/polymarket-alpha-lab "<read-only Decimal canonicalization review prompt>"
```

Then:

```bash
codegraph sync
git add src/polymarket_alpha_lab/action_gated_strategy_recommendation_queue_history_db_row.py tests/test_action_gated_strategy_recommendation_queue_history_db_row.py
git commit -m "fix: canonicalize action-gated history Decimal payloads"
git push origin main
```

Expected: remote `origin/main` matches local HEAD.

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
- No changing order placement or trading behavior.
- No new persistence backend.

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

- [ ] **Step 3: Commit design**

Run:

```bash
git add docs/superpowers/plans/2026-06-26-db-row-decimal-compatibility-reader-design.md
git commit -m "docs: design DB row Decimal compatibility reader"
git push origin main
```

Expected: commit and push succeed.
