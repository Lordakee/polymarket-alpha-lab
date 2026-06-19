# Strategy Cycle Snapshot Source Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a pure, paper-only source adapter that turns an existing `PaperStrategyCycleReport` into the `PaperRecommendationCycleSnapshotReport` shape asserted by `tests/test_strategy_cycle_snapshot_source.py`.

**Architecture:** The adapter is a new leaf module, `polymarket_alpha_lab.strategy_cycle_snapshot_source`, with one public function, `build_strategy_cycle_snapshot_source_report(cycle_report, iteration_started_at=None)`. It builds a four-stage `PaperRecommendationPipelineReport` and a two-row `PaperRecommendationArtifactIndexReport` from readonly adapter artifacts, without importing DB, API, auth, wallet, network, order, package-root export, CLI, runner, store, `project_screening`, or `strategy_cycle` modules. Structural validation keeps the pure source module from inheriting the live-layer import graph.

**Tech Stack:** Python frozen dataclasses, existing paper recommendation reducers, pytest, CodeGraph, OpenCode review.

---

### File Structure

- Create: `src/polymarket_alpha_lab/strategy_cycle_snapshot_source.py`
  - Responsibility: pure structural conversion from a `PaperStrategyCycleReport` instance into a `PaperRecommendationCycleSnapshotReport`.
  - Public API: `build_strategy_cycle_snapshot_source_report(cycle_report, iteration_started_at=None)`.
  - Internal adapter artifact: `_StrategyCycleSnapshotArtifact`.
- Preserve: `tests/test_strategy_cycle_snapshot_source.py`
  - Responsibility: authoritative RED/GREEN contract for this node.
  - Do not rewrite, relax, or rename its required stages/artifacts.
- Modify: `tests/test_paper_recommendation_cycle_snapshot_scope.py`
  - Responsibility: add `strategy_cycle_snapshot_source` to the existing cycle-snapshot scope checks.
  - Do not add it to `NON_LOG_MODULE_NAMES`; the module does not export public `*Report` dataclasses.
- Do not modify: `src/polymarket_alpha_lab/__init__.py`, CLI, runner, DB/store adapters.
  - Package-root export and default CLI DB-source wiring are deferred to later nodes.

### Authoritative Contract

- Import path: `polymarket_alpha_lab.strategy_cycle_snapshot_source`.
- Public function: `build_strategy_cycle_snapshot_source_report(cycle_report, iteration_started_at=None)`.
- One positional argument remains valid: `build_strategy_cycle_snapshot_source_report(cycle_report)`.
- `iteration_started_at` is optional runner compatibility only; the snapshot timestamp comes from `cycle_report.generated_at`.
- Wrong input type raises `ValueError` containing `PaperStrategyCycleReport`.
- Returned snapshot has `paper_only is True`, `report_only is True`, and `readonly is True`.
- Snapshot, nested pipeline report, and nested artifact index report use `cycle_report.generated_at` and `cycle_report.config_version`.
- Pipeline stages appear in this exact order:
  - `market_scan`
  - `market_consideration`
  - `cost_aware_snapshot`
  - `project_screening`
- Blocked/no-screening cycle expectations:
  - `market_scan`: `pass`, input `0`, output `scan_market_count`.
  - `market_consideration`: `pass`, input `scan_market_count`, output `considered_count`.
  - `cost_aware_snapshot`: `blocked`, input `considered_count`, output `snapshot_ready_count`.
  - `project_screening`: `blocked`, input `snapshot_ready_count`, output `0`.
- Passing/screened cycle expectations:
  - all four stages have status `pass`.
  - `project_screening.input_count == snapshot_ready_count`.
  - `project_screening.output_count == screening_report.ready_count`.
- Artifact rows are created through readonly adapter artifacts, not raw report objects:
  - `strategy_cycle_blocked_counts`
  - `strategy_cycle_screening_report`
- Raw artifact rows must not appear:
  - `paper_strategy_cycle_report`
  - `paper_project_screening_report`
- Blocked-count row:
  - status `blocked` when blocked total is positive, else `pass`.
  - `item_count == sum(count for _, count in cycle_report.blocked_counts)`.
  - reason codes are the sorted blocked status names from `cycle_report.blocked_counts`.
- Screening row:
  - when `screening_report is None` and markets were considered, status `blocked`, item count `0`, reason code `missing_screening_report`.
  - when a screening report has ready candidates, status `pass`, item count `screening_report.ready_count`, reason code `screening_ready_candidates`.
  - other valid screening outcomes may map to `watch` or `blocked`, but must stay paper-only/report-only/readonly.
- Module scope:
  - no DB/API/auth/order/network/store imports.
  - no live-layer imports from `polymarket_alpha_lab.strategy_cycle` or `polymarket_alpha_lab.project_screening`.
  - no calls named like auth/order/network mutations.

### Task 1: Confirm Existing RED Contract

**Files:**
- Verify: `tests/test_strategy_cycle_snapshot_source.py`

- [ ] **Step 1: Run RED before implementation**

Run:

```bash
.venv/bin/python -m pytest tests/test_strategy_cycle_snapshot_source.py -q
```

Expected before implementation: FAIL because `polymarket_alpha_lab.strategy_cycle_snapshot_source` is missing.

Expected after implementation: PASS.

### Task 2: Implement Pure Source Module

**Files:**
- Create: `src/polymarket_alpha_lab/strategy_cycle_snapshot_source.py`
- Verify: `tests/test_strategy_cycle_snapshot_source.py`

- [ ] **Step 1: Create only pure reducer imports**

Use only:

```python
from dataclasses import dataclass
from datetime import UTC, datetime

from polymarket_alpha_lab.paper_recommendation_artifact_index import (
    build_paper_recommendation_artifact_index_report,
)
from polymarket_alpha_lab.paper_recommendation_cycle_snapshot import (
    PaperRecommendationCycleSnapshotReport,
    build_paper_recommendation_cycle_snapshot_report,
)
from polymarket_alpha_lab.paper_recommendation_pipeline import (
    PaperRecommendationPipelineStage,
    build_paper_recommendation_pipeline_report,
)
```

- [ ] **Step 2: Add readonly adapter artifact**

```python
SAFETY_FLAGS = ("paper_only", "report_only", "readonly")


@dataclass(frozen=True)
class _StrategyCycleSnapshotArtifact:
    artifact_name: str
    config_version: str
    generated_at: datetime
    status: str
    item_count: int
    reason_codes: tuple[str, ...]
    flags: tuple[str, ...] = SAFETY_FLAGS
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
```

- [ ] **Step 3: Add public builder**

Implementation requirements:

- accept `cycle_report: object` positionally;
- accept optional `iteration_started_at: datetime | None = None`;
- validate `cycle_report` structurally by exact type name/module and hard paper/report flags;
- validate optional `iteration_started_at` only when supplied;
- normalize `generated_at` to UTC;
- validate count fields as exact nonnegative `int`;
- build pipeline report, artifact index report, then cycle snapshot report using existing builders;
- export only `build_strategy_cycle_snapshot_source_report` through module `__all__`.

- [ ] **Step 4: Add deterministic helpers**

Helpers must implement the status/count/reason mapping in the Authoritative Contract and must never pass `PaperStrategyCycleReport` or `PaperProjectScreeningReport` directly into `build_paper_recommendation_artifact_index_report`.

- [ ] **Step 5: Run focused GREEN**

Run:

```bash
.venv/bin/python -m pytest tests/test_strategy_cycle_snapshot_source.py -q
```

Expected: PASS.

### Task 3: Add Scope Coverage

**Files:**
- Modify: `tests/test_paper_recommendation_cycle_snapshot_scope.py`

- [ ] **Step 1: Add the module to scope targets**

Add only:

```python
"strategy_cycle_snapshot_source",
```

to `TARGET_MODULE_NAMES`.

Do not add the module to `NON_LOG_MODULE_NAMES`, because this module does not export public report dataclasses.

- [ ] **Step 2: Run scope tests**

Run:

```bash
.venv/bin/python -m pytest tests/test_paper_recommendation_cycle_snapshot_scope.py -q
```

Expected: PASS.

### Task 4: Verification and Review Gates

**Files:**
- Verify: `docs/superpowers/plans/2026-06-19-strategy-cycle-snapshot-source-node.md`
- Verify: `src/polymarket_alpha_lab/strategy_cycle_snapshot_source.py`
- Verify: `tests/test_strategy_cycle_snapshot_source.py`
- Verify: `tests/test_paper_recommendation_cycle_snapshot_scope.py`

- [ ] **Step 1: Focused and adjacent tests**

Run:

```bash
.venv/bin/python -m pytest \
  tests/test_strategy_cycle_snapshot_source.py \
  tests/test_paper_recommendation_cycle_snapshot_scope.py \
  tests/test_paper_recommendation_pipeline.py \
  tests/test_paper_recommendation_artifact_index.py \
  tests/test_paper_recommendation_cycle_snapshot.py \
  -q
```

- [ ] **Step 2: Full repository verification**

Run:

```bash
.venv/bin/python -m pytest -q
.venv/bin/python -m compileall -q src tests
git diff --check
codegraph sync
codegraph status .
```

- [ ] **Step 3: Secret scan**

Run a narrow scan over intended staged/diff paths only. Do not print or inspect Supabase `.env` values.

- [ ] **Step 4: OpenCode post-stage review**

Run:

```bash
opencode run -m zhipuai-coding-plan/glm-5.2 --variant max --dir /home/ubuntu/polymarket-alpha-lab -- "<read-only review prompt>"
```

Prompt requirements:

```text
Do not modify, create, delete, stage, commit, or format files. Output only verdict and findings.
Review the strategy cycle snapshot source node against:
- tests/test_strategy_cycle_snapshot_source.py is authoritative.
- source module path is polymarket_alpha_lab.strategy_cycle_snapshot_source.
- public function remains positional-compatible: build_strategy_cycle_snapshot_source_report(cycle_report).
- optional iteration_started_at must not change snapshot timestamp semantics.
- stage names and artifact row names match tests exactly.
- raw strategy/screening reports are not passed as artifact-index artifacts.
- no package-root export, CLI wiring, DB/source defaulting, live/auth/order/network/store imports, or unsafe calls.
- focused/full tests, compileall, diff check, CodeGraph, and secret scan have been run.
Return VERDICT: PASS or FAIL, then findings with file:line references.
```

### Task 5: Commit and Push Completed Node

**Files to stage after all gates pass:**

```text
docs/superpowers/plans/2026-06-19-strategy-cycle-snapshot-source-node.md
src/polymarket_alpha_lab/strategy_cycle_snapshot_source.py
tests/test_strategy_cycle_snapshot_source.py
tests/test_paper_recommendation_cycle_snapshot_scope.py
```

Run:

```bash
git add docs/superpowers/plans/2026-06-19-strategy-cycle-snapshot-source-node.md \
  src/polymarket_alpha_lab/strategy_cycle_snapshot_source.py \
  tests/test_strategy_cycle_snapshot_source.py \
  tests/test_paper_recommendation_cycle_snapshot_scope.py
git status --short
git commit -m "Add strategy cycle snapshot source"
git push origin main
```

Expected: commit and push succeed. The user explicitly wants completed Codex nodes pushed to GitHub.
