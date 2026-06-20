# Action-Gated Candidate Research Queue Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a paper-only reducer that turns a paper recommendation cycle action gate into a candidate research/recommendation queue only when the gate says the cycle evidence is ready.

**Architecture:** Add a pure reducer layer between `paper_recommendation_cycle_action_gate` and the existing candidate assessment, strategy bundle, and strategy queue reducers. The reducer must be frozen, Decimal-only, deterministic, readonly/report-only/paper-only, and return a blocked/watch artifact instead of trying to repair missing evidence.

**Tech Stack:** Python dataclasses, Decimal arithmetic, pytest, existing Polymarket Alpha Lab reducer contracts, CodeGraph.

---

## File Structure

- Create `src/polymarket_alpha_lab/action_gated_strategy_recommendation_queue.py`
  - Owns the new pure reducer dataclasses.
  - Validates exact input types and hard phase-boundary flags.
  - Calls existing candidate assessment, readiness, recommendation bundle, and queue reducers only when the action gate recommends `build_candidate_research_queue`.
- Create `tests/test_action_gated_strategy_recommendation_queue.py`
  - Covers ready, watch, and blocked paths.
  - Uses existing fixture style from `tests/test_strategy_recommendation_queue.py` and `tests/test_paper_recommendation_cycle_action_gate.py`.
- Create `tests/test_action_gated_strategy_recommendation_queue_scope.py`
  - Guards against DB/network/auth/wallet/account/order/client/live trading surfaces.
- Modify `docs/strategy-recommendation-layer.md`
  - Documents the new action-gated queue position in the Phase 1 recommendation stack.
- Modify `docs/paper-recommendation-cycle-snapshot.md`
  - Explains how cycle review/action gate reports feed the candidate research queue.
- Optional later task: modify `src/polymarket_alpha_lab/cli.py` and CLI tests only after the pure reducer is stable.

## Task 1: Reducer Tests

**Files:**
- Create: `tests/test_action_gated_strategy_recommendation_queue.py`
- Create: `tests/test_action_gated_strategy_recommendation_queue_scope.py`

- [ ] **Step 1: Write the failing ready-path test**

Create a test that constructs:
- a `PaperRecommendationCycleActionGateReport` with `recommended_next_step == "build_candidate_research_queue"`;
- a `PaperProjectScreeningReport`;
- matching `PaperCostAwareEventStrategyReport` rows;
- a `PaperCandidateAssessmentConfig`;
- a `PaperStrategyRecommendationBundleConfig`;
- a readiness config.

Assert the reducer returns:
- `action_status == "research_ready"`;
- `recommended_next_step == "review_candidate_research_queue"`;
- non-`None` `candidate_assessment_report`, `bundle_report`, and `queue_summary_report`;
- hard flags are all `True`;
- ready/watch/blocked counts mirror the nested queue summary.

- [ ] **Step 2: Write the failing non-ready gate tests**

Add two tests:
- a watch action gate returns no nested bundle/queue and `recommended_next_step == "await_fresh_cycle_evidence"`;
- a blocked action gate returns no nested bundle/queue and `recommended_next_step == "repair_cycle_evidence"`.

Both tests must assert:
- `candidate_count == 0`;
- `ready_count == 0`;
- the report remains paper-only/report-only/readonly;
- the reason code/counts are copied from the action gate.

- [ ] **Step 3: Write scope tests**

Assert the new source file text does not contain forbidden phase-boundary surfaces:

```python
FORBIDDEN_TOKENS = (
    "py_clob_client",
    "ClobClient",
    "private_key",
    "api_key",
    "wallet",
    "allowance",
    "balance",
    "place_order",
    "submit_order",
    "cancel_order",
    "sign",
    "live",
    "requests.",
    "httpx.",
    "sqlalchemy",
    "psycopg",
    "supabase",
)
```

- [ ] **Step 4: Run tests to verify RED**

Run:

```bash
.venv/bin/python -m pytest tests/test_action_gated_strategy_recommendation_queue.py tests/test_action_gated_strategy_recommendation_queue_scope.py -q
```

Expected: FAIL because `polymarket_alpha_lab.action_gated_strategy_recommendation_queue` does not exist yet.

## Task 2: Pure Reducer Implementation

**Files:**
- Create: `src/polymarket_alpha_lab/action_gated_strategy_recommendation_queue.py`
- Test: `tests/test_action_gated_strategy_recommendation_queue.py`
- Test: `tests/test_action_gated_strategy_recommendation_queue_scope.py`

- [ ] **Step 1: Add frozen dataclasses**

Define:
- `PaperActionGatedStrategyRecommendationQueueConfig`
- `PaperActionGatedStrategyRecommendationQueueReport`

The report must include:
- `generated_at`
- `source_config_version`
- `action_status`
- `recommended_next_step`
- `reason_code_counts`
- `candidate_count`
- `ready_count`
- `watch_count`
- `blocked_count`
- `total_ready_notional`
- optional `candidate_assessment_report`
- optional `bundle_report`
- optional `queue_summary_report`
- hard flags defaulting to `True`

- [ ] **Step 2: Add the pure reducer function**

Define:

```python
def build_paper_action_gated_strategy_recommendation_queue_report(
    action_gate_report: object,
    screening_report: object,
    cost_reports: Iterable[object],
    *,
    config: PaperActionGatedStrategyRecommendationQueueConfig,
    generated_at: datetime,
) -> PaperActionGatedStrategyRecommendationQueueReport:
    ...
```

If `action_gate_report.recommended_next_step != "build_candidate_research_queue"`, return an empty report copied from gate status/counts without calling downstream reducers.

If the gate is ready:
- build candidate assessment using `build_paper_candidate_assessment_report`;
- build readiness report using the existing readiness reducer/config chosen by local patterns;
- build strategy recommendation bundle using `build_paper_strategy_recommendation_bundle_report`;
- build queue summary using `build_paper_strategy_recommendation_queue_summary_report`;
- copy counts and notional from the queue summary.

- [ ] **Step 3: Validate exact types and flags**

The reducer must reject:
- non-`PaperRecommendationCycleActionGateReport` action gate input;
- non-`PaperProjectScreeningReport` screening input;
- non-`PaperActionGatedStrategyRecommendationQueueConfig` config;
- non-`datetime` generated_at;
- reports whose hard flags are not all true.

- [ ] **Step 4: Run reducer tests to verify GREEN**

Run:

```bash
.venv/bin/python -m pytest tests/test_action_gated_strategy_recommendation_queue.py tests/test_action_gated_strategy_recommendation_queue_scope.py -q
```

Expected: PASS.

## Task 3: Documentation

**Files:**
- Modify: `docs/strategy-recommendation-layer.md`
- Modify: `docs/paper-recommendation-cycle-snapshot.md`

- [ ] **Step 1: Document the new reducer**

Add a concise section explaining:
- the action gate must recommend `build_candidate_research_queue`;
- otherwise the queue builder returns a watch/blocked report;
- the reducer is paper-only/report-only/readonly and does not repair data itself.

- [ ] **Step 2: Document operator interpretation**

Describe the three possible operational outcomes:
- `research_ready` -> candidate queue can be reviewed;
- `watch` -> wait for fresh paper-cycle evidence;
- `blocked` -> repair cycle evidence before queue construction.

## Task 4: Verification, Review, Commit, Push

**Files:**
- All files changed by the node.

- [ ] **Step 1: Run focused adjacent tests**

```bash
.venv/bin/python -m pytest tests/test_action_gated_strategy_recommendation_queue.py tests/test_action_gated_strategy_recommendation_queue_scope.py tests/test_paper_recommendation_cycle_action_gate.py tests/test_strategy_recommendation_queue.py tests/test_strategy_recommendation_bundle.py tests/test_candidate_assessment.py -q
```

- [ ] **Step 2: Run full verification**

```bash
.venv/bin/python -m pytest -q
.venv/bin/python -m compileall -q src tests
git diff --check
codegraph sync && codegraph status .
```

- [ ] **Step 3: Run OpenCode review**

```bash
opencode run --model zhipuai-coding-plan/glm-5.2 --variant max --dir /home/ubuntu/polymarket-alpha-lab "<review prompt>"
```

- [ ] **Step 4: Commit and push**

```bash
git add src/polymarket_alpha_lab/action_gated_strategy_recommendation_queue.py tests/test_action_gated_strategy_recommendation_queue.py tests/test_action_gated_strategy_recommendation_queue_scope.py docs/strategy-recommendation-layer.md docs/paper-recommendation-cycle-snapshot.md docs/superpowers/plans/2026-06-20-action-gated-candidate-research-queue.md
git commit -m "Add action-gated strategy recommendation queue"
git push origin main
```

## Self-Review

- Spec coverage: The plan covers ready, watch, blocked action-gate outcomes, exact type validation, hard flags, docs, focused/full verification, OpenCode review, commit, and push.
- Placeholder scan: No TBD/TODO/fill-in-later placeholders remain.
- Type consistency: Names are consistent with existing `Paper...Report` reducer naming and the planned source/test file names.
