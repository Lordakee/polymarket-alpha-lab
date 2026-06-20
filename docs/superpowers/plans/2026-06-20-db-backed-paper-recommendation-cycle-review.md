# DB-Backed Paper Recommendation Cycle Review Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a paper-only, DB-backed recommendation cycle review path that makes persisted recommendation snapshots auditable without enabling live trading.

**Architecture:** Keep reducers pure and DB-free. Runtime code may expose already-built paper evidence on `PaperStrategyCycleReport`; source adapters turn that evidence into recommendation snapshot artifacts; DB/CLI code remains at the process edge and only reads persisted snapshots.

**Tech Stack:** Python dataclasses, `Decimal`, pytest, local Supabase/Postgres adapters through existing psycopg edge modules, CodeGraph for navigation.

---

## File Structure

- `src/polymarket_alpha_lab/strategy_cycle.py`: expose stable, paper-only runtime evidence on `PaperStrategyCycleReport`.
- `tests/test_strategy_cycle.py`: prove existing behavior and serialization remain compatible after evidence exposure.
- `src/polymarket_alpha_lab/strategy_cycle_recommendation_artifact_source.py`: pure adapter from enriched cycle reports to recommendation artifact inputs.
- `tests/test_strategy_cycle_recommendation_artifact_source.py`: focused adapter behavior and boundary tests.
- `src/polymarket_alpha_lab/strategy_cycle_snapshot_source.py`: select rich artifacts when present and retain minimal fallback.
- `tests/test_strategy_cycle_snapshot_source.py`: fallback and rich-source behavior.
- `src/polymarket_alpha_lab/paper_recommendation_cycle_review.py`: pure reducer summarizing loaded snapshot history.
- `tests/test_paper_recommendation_cycle_review.py`: review reducer behavior.
- `tests/test_paper_recommendation_cycle_review_scope.py`: no DB/network/live/order boundary scan for the reducer.
- `src/polymarket_alpha_lab/cli.py`: later read-only CLI command for DB-backed review, behind existing DB config boundaries.
- `tests/test_cli.py`: injected-loader CLI tests, no real DB/network.
- `docs/paper-recommendation-cycle-snapshot.md`: runtime snapshot and review flow.
- `docs/strategy-recommendation-layer.md`: recommendation layer boundary and review semantics.

## Task 1: Runtime Evidence Exposure

**Files:**
- Modify: `src/polymarket_alpha_lab/strategy_cycle.py`
- Modify: `tests/test_strategy_cycle.py`

- [ ] **Step 1: Write failing tests**

Add a test that runs a cycle with ready markets and asserts the returned `PaperStrategyCycleReport` exposes immutable paper evidence needed downstream:

```python
def test_strategy_cycle_report_exposes_cost_aware_and_screening_evidence():
    report = run_strategy_cycle(...)
    assert report.cost_aware_reports
    assert report.screening_report is not None
    assert report.paper_only is True
    assert report.report_only is True
```

- [ ] **Step 2: Verify RED**

Run:

```bash
.venv/bin/python -m pytest tests/test_strategy_cycle.py::test_strategy_cycle_report_exposes_cost_aware_and_screening_evidence -q
```

Expected: fail because `cost_aware_reports` is not present yet.

- [ ] **Step 3: Implement minimal exposure**

Add a frozen tuple field to `PaperStrategyCycleReport`:

```python
cost_aware_reports: tuple[PaperCostAwareEventStrategyReport, ...] = ()
```

Normalize it with exact-type checks and existing paper/report flags. Populate it from the local cost-aware reports already built by `run_strategy_cycle`. Do not import DB or live trading code.

- [ ] **Step 4: Verify GREEN**

Run:

```bash
.venv/bin/python -m pytest tests/test_strategy_cycle.py -q
```

Expected: pass.

## Task 2: Pure Recommendation Cycle Review Reducer

**Files:**
- Create: `src/polymarket_alpha_lab/paper_recommendation_cycle_review.py`
- Create: `tests/test_paper_recommendation_cycle_review.py`
- Create: `tests/test_paper_recommendation_cycle_review_scope.py`

- [ ] **Step 1: Write failing reducer tests**

Add tests for:

```python
def test_cycle_review_summarizes_latest_snapshot_and_reason_counts():
    report = build_paper_recommendation_cycle_review_report(
        [blocked_snapshot, watch_snapshot, pass_snapshot],
        config=PaperRecommendationCycleReviewConfig(
            config_version="paper-recommendation-cycle-review-v0",
            stale_after_hours=Decimal("6.000000"),
        ),
        generated_at=GENERATED_AT,
    )
    assert report.snapshot_count == 3
    assert report.latest_final_status == "pass"
    assert report.blocked_snapshot_count == 1
    assert report.watch_snapshot_count == 1
```

- [ ] **Step 2: Verify RED**

Run:

```bash
.venv/bin/python -m pytest tests/test_paper_recommendation_cycle_review.py -q
```

Expected: fail with module not found.

- [ ] **Step 3: Implement reducer**

Use frozen dataclasses:

```python
@dataclass(frozen=True)
class PaperRecommendationCycleReviewConfig:
    config_version: str
    stale_after_hours: Decimal

@dataclass(frozen=True)
class PaperRecommendationCycleReviewReport:
    generated_at: datetime
    config_version: str
    snapshot_count: int
    latest_generated_at: datetime | None
    latest_final_status: str | None
    blocked_snapshot_count: int
    watch_snapshot_count: int
    pass_snapshot_count: int
    blocked_artifact_count: int
    watch_artifact_count: int
    missing_required_artifact_names: tuple[str, ...]
    reason_code_counts: tuple[PaperRecommendationCycleReviewReasonCodeCount, ...]
    review_status: str
    stale_history: bool
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
```

The reducer accepts only in-memory `PaperRecommendationCycleSnapshotReport` values. It must not import psycopg, CLI, API clients, wallets, accounts, or order code.

- [ ] **Step 4: Verify GREEN**

Run:

```bash
.venv/bin/python -m pytest tests/test_paper_recommendation_cycle_review.py tests/test_paper_recommendation_cycle_review_scope.py -q
```

Expected: pass.

## Task 3: Rich Snapshot Source Adapter

**Files:**
- Create: `src/polymarket_alpha_lab/strategy_cycle_recommendation_artifact_source.py`
- Create: `tests/test_strategy_cycle_recommendation_artifact_source.py`
- Modify: `src/polymarket_alpha_lab/strategy_cycle_snapshot_source.py`
- Modify: `tests/test_strategy_cycle_snapshot_source.py`

- [ ] **Step 1: Write failing adapter tests**

Add tests proving a cycle report with cost-aware evidence creates additional artifact rows while a minimal cycle report still produces the existing fallback snapshot.

- [ ] **Step 2: Verify RED**

Run:

```bash
.venv/bin/python -m pytest tests/test_strategy_cycle_recommendation_artifact_source.py tests/test_strategy_cycle_snapshot_source.py -q
```

Expected: fail on missing adapter.

- [ ] **Step 3: Implement pure adapter**

Build report-like artifacts with `artifact_name`, `config_version`, `generated_at`, `status`, `item_count`, `reason_codes`, safety flags, and no IO.

- [ ] **Step 4: Verify GREEN**

Run:

```bash
.venv/bin/python -m pytest tests/test_strategy_cycle_recommendation_artifact_source.py tests/test_strategy_cycle_snapshot_source.py -q
```

Expected: pass.

## Task 4: DB-Backed CLI Review Command

**Files:**
- Modify: `src/polymarket_alpha_lab/cli.py`
- Modify: `tests/test_cli.py`

- [ ] **Step 1: Write failing CLI tests**

Add tests for a read-only command such as:

```bash
polymarket-alpha-lab paper-recommendation-cycle-review --limit 50
```

The test must inject a fake loader or fake psycopg and assert DSNs are redacted.

- [ ] **Step 2: Verify RED**

Run:

```bash
.venv/bin/python -m pytest tests/test_cli.py::<new_review_cli_test> -q
```

Expected: fail because command is absent.

- [ ] **Step 3: Implement CLI command**

Load existing cycle snapshots with `load_paper_recommendation_cycle_snapshots_with_psycopg`, pass them into `build_paper_recommendation_cycle_review_report`, and print only concise counts/statuses. Do not print raw payload JSON or DSNs.

- [ ] **Step 4: Verify GREEN**

Run:

```bash
.venv/bin/python -m pytest tests/test_cli.py -q
```

Expected: pass.

## Task 5: Documentation And Boundary Hardening

**Files:**
- Modify: `docs/paper-recommendation-cycle-snapshot.md`
- Modify: `docs/strategy-recommendation-layer.md`

- [ ] **Step 1: Update documentation**

Document the flow:

```text
strategy cycle
-> rich paper recommendation artifacts
-> artifact index + pipeline report
-> cycle snapshot
-> Supabase/Postgres persistence
-> DB-backed review/trend CLI
```

- [ ] **Step 2: Verify docs and tests**

Run:

```bash
git diff --check
.venv/bin/python -m pytest tests/test_paper_recommendation_cycle_snapshot*.py tests/test_cli.py -q
```

Expected: pass.

## Final Verification

Run:

```bash
.venv/bin/python -m pytest -q
.venv/bin/python -m compileall -q src tests
git diff --check
codegraph sync && codegraph status .
opencode run --model zhipuai-coding-plan/glm-5.2 --variant max --dir /home/ubuntu/polymarket-alpha-lab "<review prompt>"
```

Expected: full suite passes, CodeGraph is up to date, OpenCode review passes.
