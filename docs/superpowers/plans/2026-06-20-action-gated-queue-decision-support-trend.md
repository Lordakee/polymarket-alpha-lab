# Action-Gated Queue Decision-Support Trend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a pure Phase 1 trend reducer over caller-supplied action-gated queue decision-support snapshot pairs.

**Architecture:** The first node is library-only: it consumes `(priority_report, risk_report)` pairs already produced by the decision-support DB loader or caller code, sorts them chronologically by `generated_at` with stable input-order tie breaking, and emits a frozen paper/report/readonly trend report. It does not add CLI commands, DB reads/writes, allocation, approval, sizing, or execution semantics.

**Tech Stack:** Python frozen dataclasses, `Decimal` only, pytest, CodeGraph-indexed source layout.

## Global Constraints

- Phase 1 boundary remains strict: no live trading, auth, wallet, private keys, account reads, order construction, signing, submission, cancellation, replacement, exchange mutation, or live execution.
- All new report dataclasses must be frozen and must enforce `paper_only is True`, `report_only is True`, and `readonly is True`.
- Use `Decimal` for numeric score/notional values; do not introduce float literals or float arithmetic.
- The reducer input is caller-supplied decision-support snapshot pairs: `tuple[(PaperActionGatedStrategyRecommendationQueuePriorityReport, PaperActionGatedStrategyRecommendationQueueRiskReport), ...]`.
- Trend calculations must sort snapshots by `generated_at` ascending and preserve input order for duplicate timestamps.
- Duplicate `generated_at` values must be counted explicitly.
- The first node is library-only: no CLI wiring, no DB persistence, no Supabase configuration, and no migration.

---

### Task 1: Core Trend Reducer

**Files:**
- Create: `src/polymarket_alpha_lab/action_gated_strategy_recommendation_queue_decision_support_trend.py`
- Test: `tests/test_action_gated_strategy_recommendation_queue_decision_support_trend.py`

**Interfaces:**
- Consumes: `PaperActionGatedStrategyRecommendationQueuePriorityReport`, `PaperActionGatedStrategyRecommendationQueueRiskReport`.
- Produces: `PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendSnapshotSummary`, `PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendReasonCodeRow`, `PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendReport`, `build_paper_action_gated_strategy_recommendation_queue_decision_support_trend_report`.

- [ ] **Step 1: Write failing tests for empty and single-snapshot reports**

```python
def test_decision_support_trend_empty_input_is_paper_report_readonly():
    trend = build_paper_action_gated_strategy_recommendation_queue_decision_support_trend_report(
        (),
        generated_at=GENERATED_AT,
    )

    assert trend.source_snapshot_count == 0
    assert trend.first_generated_at is None
    assert trend.latest_generated_at is None
    assert trend.latest_risk_status is None
    assert trend.risk_status_counts == ()
    assert trend.consecutive_latest_watch_count == 0
    assert trend.consecutive_latest_blocked_count == 0
    assert trend.ready_notional_first is None
    assert trend.ready_notional_latest is None
    assert trend.ready_notional_delta is None
    assert trend.top_priority_score_first is None
    assert trend.top_priority_score_latest is None
    assert trend.top_priority_score_delta is None
    assert trend.average_priority_score_first is None
    assert trend.average_priority_score_latest is None
    assert trend.average_priority_score_delta is None
    assert trend.source_queue_count_first is None
    assert trend.source_queue_count_latest is None
    assert trend.source_queue_count_delta is None
    assert trend.duplicate_generated_at_count == 0
    assert trend.reason_code_rows == ()
    assert trend.source_summaries == ()
    assert trend.paper_only is True
    assert trend.report_only is True
    assert trend.readonly is True
```

- [ ] **Step 2: Run focused test to verify RED**

Run: `.venv/bin/python -m pytest tests/test_action_gated_strategy_recommendation_queue_decision_support_trend.py -q`

Expected: FAIL because `polymarket_alpha_lab.action_gated_strategy_recommendation_queue_decision_support_trend` is missing.

- [ ] **Step 3: Implement minimal dataclasses and reducer for empty/single input**

Create the module with frozen dataclasses, strict type checks for exact priority/risk report classes, same-snapshot parity checks, hard flag checks, Decimal delta helpers, reason-code aggregation, UTC normalization, and `__all__`.

- [ ] **Step 4: Add chronological, streak, duplicate, and reason-code tests**

Add tests that cover reverse-loaded DB order, stable duplicate timestamp handling, watch/blocked latest streaks, repeated reason-code counts, hard flag rejection, frozen dataclass invariants, and invalid input rejection.

- [ ] **Step 5: Run focused tests to verify GREEN**

Run: `.venv/bin/python -m pytest tests/test_action_gated_strategy_recommendation_queue_decision_support_trend.py -q`

Expected: all tests in the file pass.

- [ ] **Step 6: Commit after review and full verification**

```bash
git add src/polymarket_alpha_lab/action_gated_strategy_recommendation_queue_decision_support_trend.py tests/test_action_gated_strategy_recommendation_queue_decision_support_trend.py
git commit -m "Add action-gated decision support trend reducer"
```

### Task 2: Scope Guard And Documentation

**Files:**
- Create: `tests/test_action_gated_queue_decision_support_trend_scope.py`
- Modify: `docs/action-gated-queue-decision-support.md`

**Interfaces:**
- Consumes: the trend module from Task 1.
- Produces: scope tests that keep the module paper/report/readonly and docs describing trend-only behavior.

- [ ] **Step 1: Write a failing scope test against the intended module**

```python
def test_decision_support_trend_module_stays_phase_1_readonly():
    source = inspect.getsource(trend_module)
    tree = ast.parse(source)
    imported_modules = set()
    call_names = set()
    float_literals = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
        elif isinstance(node, ast.Call):
            function = node.func
            if isinstance(function, ast.Name):
                call_names.add(function.id)
            elif isinstance(function, ast.Attribute):
                call_names.add(function.attr)
        elif isinstance(node, ast.Constant) and isinstance(node.value, float):
            float_literals.append(node.value)
    assert imported_modules.isdisjoint(FORBIDDEN_IMPORTS)
    assert call_names.isdisjoint(FORBIDDEN_CALLS)
    assert float_literals == []
    assert all(fragment not in source.lower() for fragment in FORBIDDEN_FRAGMENTS)
```

- [ ] **Step 2: Run focused scope test to verify RED or PASS with Task 1 implementation**

Run: `.venv/bin/python -m pytest tests/test_action_gated_queue_decision_support_trend_scope.py -q`

Expected before Task 1 exists: FAIL on import. Expected after Task 1 exists: PASS.

- [ ] **Step 3: Update docs with trend semantics**

Add a concise section stating that callers supply decision-support snapshot pairs, the reducer sorts snapshots chronologically, duplicate timestamps are counted, output is trend-only, and CLI/DB wiring is intentionally deferred.

- [ ] **Step 4: Run focused docs/scope tests**

Run: `.venv/bin/python -m pytest tests/test_action_gated_queue_decision_support_trend_scope.py -q`

Expected: PASS.

### Task 3: Review, Verification, And Push

**Files:**
- Modify only files from Tasks 1 and 2 unless review finds a concrete defect.

**Interfaces:**
- Consumes: implemented trend reducer, tests, docs.
- Produces: reviewed, verified, pushed commit.

- [ ] **Step 1: Run focused tests**

```bash
.venv/bin/python -m pytest tests/test_action_gated_strategy_recommendation_queue_decision_support_trend.py tests/test_action_gated_queue_decision_support_trend_scope.py -q
```

- [ ] **Step 2: Run full verification**

```bash
.venv/bin/python -m pytest -q
.venv/bin/python -m compileall -q src tests
git diff --check
codegraph sync
codegraph status .
```

- [ ] **Step 3: Request OpenCode review**

```bash
opencode run --model zhipuai-coding-plan/glm-5.2 --variant max --dir /home/ubuntu/polymarket-alpha-lab "<review prompt>"
```

- [ ] **Step 4: Fix Critical or Important findings and re-run focused/full verification**

Use the review findings as requirements. Do not proceed with unfixed Critical or Important findings.

- [ ] **Step 5: Commit and push only with explicit user authorization**

```bash
git add docs/superpowers/plans/2026-06-20-action-gated-queue-decision-support-trend.md src/polymarket_alpha_lab/action_gated_strategy_recommendation_queue_decision_support_trend.py tests/test_action_gated_strategy_recommendation_queue_decision_support_trend.py tests/test_action_gated_queue_decision_support_trend_scope.py docs/action-gated-queue-decision-support.md
git commit -m "Add action-gated decision support trend report"
```

Push after commit only when the active session includes explicit user
authorization to publish green reviewed nodes to GitHub; otherwise leave the
commit local and ask for confirmation.
