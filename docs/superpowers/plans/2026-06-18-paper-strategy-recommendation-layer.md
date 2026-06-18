# Paper Strategy Recommendation Layer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a paper-only recommendation and selection layer that turns candidate assessment and readiness gates into auditable ranked recommendations without live trading or order placement.

**Architecture:** Keep this as reducer-only modules with frozen dataclasses and direct-constructor validation. The recommendation reducer owns ranked candidate actions, the selection policy owns paper sizing caps, and the explanation reducer owns deterministic human-readable rationale.

**Tech Stack:** Python dataclasses, `Decimal`, pytest, CodeGraph, existing `polymarket_alpha_lab` paper-only reducers.

---

## File Ownership

- `src/polymarket_alpha_lab/strategy_candidate_recommendation.py`: recommendation ranking reducer only.
- `tests/test_strategy_candidate_recommendation.py`: tests for recommendation ranking and validation.
- `src/polymarket_alpha_lab/paper_strategy_selection_policy.py`: paper-only sizing and selection policy only.
- `tests/test_paper_strategy_selection_policy.py`: tests for selection caps and validation.
- `src/polymarket_alpha_lab/strategy_recommendation_explain.py`: deterministic explanation reducer only.
- `tests/test_strategy_recommendation_explain.py`: tests for explanation output and validation.
- `src/polymarket_alpha_lab/settlement_freshness_gate.py`: direct-constructor semantic hardening only.
- `tests/test_settlement_freshness_gate.py`: settlement hardening tests only.
- Do not modify `src/polymarket_alpha_lab/__init__.py`.
- Do not add live trading, auth, wallet, relayer, private key, or real order concepts.

## Parallel Nodes

### Task 1: Recommendation Reducer

**Files:**
- Create: `src/polymarket_alpha_lab/strategy_candidate_recommendation.py`
- Create: `tests/test_strategy_candidate_recommendation.py`

- [x] **Step 1: Inspect source reducer shapes**

Run:

```bash
codegraph explore "PaperCandidateAssessmentReport PaperCandidateAssessmentRow PaperStrategyReadinessStateReport recommendation reducer"
```

Expected: source for candidate assessment and readiness state is available.

- [ ] **Step 2: Write failing recommendation tests**

Test cases:

```python
def test_recommends_ready_candidate_when_readiness_passes():
    report = build_paper_strategy_candidate_recommendation_report(
        assessment_report_with_ready_candidate(),
        readiness_report("pass"),
        config=PaperStrategyCandidateRecommendationConfig(
            config_version="recommendation-test",
            min_recommendation_score=Decimal("0.010000"),
        ),
        generated_at=NOW,
    )
    assert report.recommend_count == 1
    assert report.recommendation_rows[0].action == "recommend"
    assert "readiness_passed" in report.recommendation_rows[0].reason_codes
```

Also cover readiness watch, readiness blocked, blocked candidate, deterministic ordering, input flag validation, and direct-constructor count validation.

- [ ] **Step 3: Implement reducer**

Public API:

```python
@dataclass(frozen=True)
class PaperStrategyCandidateRecommendationConfig:
    config_version: str
    min_recommendation_score: Decimal = Decimal("0.010000")


@dataclass(frozen=True)
class PaperStrategyCandidateRecommendationRow:
    market_slug: str
    question: str
    action: str
    selected_side: str
    assessment_status: str
    readiness_status: str
    recommendation_score: Decimal
    reason_codes: tuple[str, ...]


@dataclass(frozen=True)
class PaperStrategyCandidateRecommendationReport:
    generated_at: datetime
    config_version: str
    candidate_count: int
    recommend_count: int
    watch_count: int
    reject_count: int
    recommendation_rows: tuple[PaperStrategyCandidateRecommendationRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
```

Use `build_paper_strategy_candidate_recommendation_report(assessment_report, readiness_report, *, config, generated_at)` and deterministic ordering by action priority, descending `recommendation_score`, then `market_slug`.

- [ ] **Step 4: Run focused tests**

Run:

```bash
.venv/bin/python -m pytest tests/test_strategy_candidate_recommendation.py -q
```

Expected: all recommendation tests pass.

### Task 2: Selection Policy Reducer

**Files:**
- Create: `src/polymarket_alpha_lab/paper_strategy_selection_policy.py`
- Create: `tests/test_paper_strategy_selection_policy.py`

- [ ] **Step 1: Wait for recommendation public API**

Run:

```bash
test -f src/polymarket_alpha_lab/strategy_candidate_recommendation.py
```

Expected: exit code `0`. If absent, pause this node until Task 1 lands.

- [ ] **Step 2: Write failing selection tests**

Test cases:

```python
def test_selects_recommended_candidates_under_caps():
    report = build_paper_strategy_selection_policy_report(
        recommendation_report_with_actions(("recommend", "watch", "reject")),
        config=PaperStrategySelectionPolicyConfig(
            config_version="selection-test",
            base_position_notional=Decimal("10.000000"),
            max_position_notional=Decimal("5.000000"),
            max_total_notional=Decimal("10.000000"),
        ),
        generated_at=NOW,
    )
    assert report.selected_count == 1
    assert report.selection_rows[0].decision == "selected"
```

Also cover per-position cap, total cap, non-recommend rows, source flag validation, and direct-constructor total/count mismatch validation.

- [ ] **Step 3: Implement reducer**

Public API:

```python
@dataclass(frozen=True)
class PaperStrategySelectionPolicyConfig:
    config_version: str
    base_position_notional: Decimal
    max_position_notional: Decimal
    max_total_notional: Decimal


@dataclass(frozen=True)
class PaperStrategySelectionPolicyRow:
    market_slug: str
    question: str
    selected_side: str
    decision: str
    requested_notional: Decimal
    selected_notional: Decimal
    reason_codes: tuple[str, ...]


@dataclass(frozen=True)
class PaperStrategySelectionPolicyReport:
    generated_at: datetime
    config_version: str
    candidate_count: int
    selected_count: int
    skipped_count: int
    not_selected_count: int
    total_selected_notional: Decimal
    selection_rows: tuple[PaperStrategySelectionPolicyRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
```

Use Decimal-only sizing. Never create order objects.

- [ ] **Step 4: Run focused tests**

Run:

```bash
.venv/bin/python -m pytest tests/test_paper_strategy_selection_policy.py -q
```

Expected: all selection policy tests pass.

### Task 3: Recommendation Explanation Reducer

**Files:**
- Create: `src/polymarket_alpha_lab/strategy_recommendation_explain.py`
- Create: `tests/test_strategy_recommendation_explain.py`

- [ ] **Step 1: Wait for recommendation public API**

Run:

```bash
test -f src/polymarket_alpha_lab/strategy_candidate_recommendation.py
```

Expected: exit code `0`. If absent, pause this node until Task 1 lands.

- [ ] **Step 2: Write failing explanation tests**

Test cases:

```python
def test_explains_recommend_watch_and_reject_rows():
    report = build_paper_strategy_recommendation_explanation_report(
        recommendation_report_with_actions(("recommend", "watch", "reject")),
        generated_at=NOW,
    )
    assert report.recommend_count == 1
    assert report.watch_count == 1
    assert report.reject_count == 1
    assert report.explanation_rows[0].primary_reason_code
```

Also cover source flag validation and direct-constructor count mismatch validation.

- [ ] **Step 3: Implement reducer**

Public API:

```python
@dataclass(frozen=True)
class PaperStrategyRecommendationExplanationRow:
    market_slug: str
    action: str
    selected_side: str
    recommendation_score: Decimal
    primary_reason_code: str
    reason_codes: tuple[str, ...]
    explanation: str


@dataclass(frozen=True)
class PaperStrategyRecommendationExplanationReport:
    generated_at: datetime
    source_config_version: str
    row_count: int
    recommend_count: int
    watch_count: int
    reject_count: int
    explanation_rows: tuple[PaperStrategyRecommendationExplanationRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
```

Explanations must be deterministic template strings based on row action and primary reason code.

- [ ] **Step 4: Run focused tests**

Run:

```bash
.venv/bin/python -m pytest tests/test_strategy_recommendation_explain.py -q
```

Expected: all explanation tests pass.

### Task 4: Settlement Constructor Hardening

**Files:**
- Modify: `src/polymarket_alpha_lab/settlement_freshness_gate.py`
- Modify: `tests/test_settlement_freshness_gate.py`

- [ ] **Step 1: Add failing hardening tests**

Test cases:

```python
def test_report_rejects_pending_counts_without_source():
    with pytest.raises(ValueError, match="pending_count must be zero without source"):
        PaperSettlementFreshnessGateReport(
            source_report_count=0,
            pending_count=1,
            stale_pending_count=0,
            ...
        )
```

Also reject stale count without source and wrong canonical row reason strings.

- [ ] **Step 2: Harden validation**

In `_validate_report_consistency`, require `pending_count == 0` and `stale_pending_count == 0` when `source_report_count == 0`.

In row semantic validation, require canonical reasons for each gate based on observed values and status.

- [ ] **Step 3: Run focused tests**

Run:

```bash
.venv/bin/python -m pytest tests/test_settlement_freshness_gate.py -q
```

Expected: all settlement freshness tests pass.

### Task 5: Integration Verification

**Files:**
- Modify only if tests expose integration gaps in the modules above.

- [ ] **Step 1: Run focused new-module tests**

Run:

```bash
.venv/bin/python -m pytest \
  tests/test_strategy_candidate_recommendation.py \
  tests/test_paper_strategy_selection_policy.py \
  tests/test_strategy_recommendation_explain.py \
  tests/test_settlement_freshness_gate.py \
  -q
```

Expected: all focused tests pass.

- [ ] **Step 2: Run compileall**

Run:

```bash
.venv/bin/python -m compileall -q src/polymarket_alpha_lab tests
```

Expected: exit code `0`.

- [ ] **Step 3: Run full suite**

Run:

```bash
.venv/bin/python -m pytest -q
```

Expected: all tests pass.

- [ ] **Step 4: Run diff checks**

Run:

```bash
git diff --check
git diff --cached --check
```

Expected: both commands exit `0`.

- [ ] **Step 5: Sync CodeGraph**

Run:

```bash
codegraph sync
```

Expected: sync completes successfully.

- [ ] **Step 6: Final audit**

Run Claude Code audit with `claude-opus-4-8` and effort `max` over the staged diff. Required result: no blocking Critical/High/Medium findings before push.

- [ ] **Step 7: Commit and push**

Run:

```bash
git add src/polymarket_alpha_lab tests docs/superpowers/plans/2026-06-18-paper-strategy-recommendation-layer.md
git commit -m "Add paper-only strategy recommendation layer"
git push origin main
```

Expected: commit exists locally and `origin/main` advances to that commit.
