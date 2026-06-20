# Cycle Review Action Gate Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert a DB-backed paper recommendation cycle review into a pure paper-only action gate that says whether the system may proceed to candidate research review, should wait for fresher evidence, or must repair missing/blocked cycle evidence.

**Architecture:** Keep the action gate as a pure reducer over `PaperRecommendationCycleReviewReport`. The CLI may load persisted cycle snapshots through the existing cycle snapshot DB read edge, build the review report, pass it into the gate, and print concise counts/status only. The action gate never reads DBs, files, wallets, accounts, markets, or order APIs.

**Tech Stack:** Python frozen dataclasses, `Decimal`, pytest, existing cycle snapshot DB loader and config, CodeGraph for navigation, OpenCode for final review.

---

## File Structure

- `src/polymarket_alpha_lab/paper_recommendation_cycle_action_gate.py`: pure reducer that maps a `PaperRecommendationCycleReviewReport` to action status and reason-code pressure.
- `tests/test_paper_recommendation_cycle_action_gate.py`: reducer behavior tests.
- `tests/test_paper_recommendation_cycle_action_gate_scope.py`: AST boundary tests for the pure reducer.
- `src/polymarket_alpha_lab/cli.py`: read-only CLI command that loads persisted snapshots, builds a cycle review report, builds the action gate report, and prints a concise summary.
- `tests/test_cli.py`: injected-runner/default loader CLI tests.
- `tests/test_cli_paper_recommendation_cycle_action_gate_scope.py`: AST boundary test for the new CLI branch.
- `docs/paper-recommendation-cycle-snapshot.md`: document where the action gate sits after DB-backed review.
- `docs/strategy-recommendation-layer.md`: document that the gate allows paper research/review only, never live execution.

## Task 1: Pure Cycle Action Gate Reducer

**Files:**
- Create: `src/polymarket_alpha_lab/paper_recommendation_cycle_action_gate.py`
- Create: `tests/test_paper_recommendation_cycle_action_gate.py`
- Create: `tests/test_paper_recommendation_cycle_action_gate_scope.py`

- [ ] **Step 1: Write failing reducer tests**

Add tests that build `PaperRecommendationCycleReviewReport` values and assert:

```python
def test_cycle_action_gate_allows_research_review_when_cycle_review_passes():
    review = review_report(review_status="pass", latest_final_status="pass")
    report = build_paper_recommendation_cycle_action_gate_report(
        review,
        config=PaperRecommendationCycleActionGateConfig(
            config_version="paper-recommendation-cycle-action-gate-v0",
        ),
        generated_at=GENERATED_AT,
    )
    assert report.action_status == "research_ready"
    assert report.recommended_next_step == "build_candidate_research_queue"
    assert report.blocked_reason_count == 0
```

Add tests that:
- `review_status="watch"` maps to `action_status="watch"` and `recommended_next_step="await_fresh_cycle_evidence"`.
- missing required artifacts or `review_status="blocked"` maps to `action_status="blocked"` and `recommended_next_step="repair_cycle_evidence"`.
- stale history maps to watch with reason `cycle_history_stale`.
- reason-code counts are copied and deterministically sorted.
- dataclasses are frozen and reject unsafe flags.

- [ ] **Step 2: Verify RED**

Run:

```bash
.venv/bin/python -m pytest tests/test_paper_recommendation_cycle_action_gate.py tests/test_paper_recommendation_cycle_action_gate_scope.py -q
```

Expected: fail with module not found.

- [ ] **Step 3: Implement reducer**

Use frozen dataclasses:

```python
@dataclass(frozen=True)
class PaperRecommendationCycleActionGateConfig:
    config_version: str

@dataclass(frozen=True)
class PaperRecommendationCycleActionGateReasonCodeCount:
    reason_code: str
    count: int

@dataclass(frozen=True)
class PaperRecommendationCycleActionGateReport:
    generated_at: datetime
    config_version: str
    source_config_version: str
    review_status: str
    latest_final_status: str | None
    action_status: str
    recommended_next_step: str
    missing_required_artifact_count: int
    blocked_reason_count: int
    watch_reason_count: int
    reason_code_counts: tuple[PaperRecommendationCycleActionGateReasonCodeCount, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
```

Action rules:
- `review_status == "pass"` and no missing artifacts and not stale -> `research_ready`, next step `build_candidate_research_queue`.
- `review_status == "blocked"` or missing required artifacts -> `blocked`, next step `repair_cycle_evidence`.
- Otherwise -> `watch`, next step `await_fresh_cycle_evidence`.

Derived reason codes:
- Always copy source reason counts.
- Add `cycle_review_pass`, `cycle_review_watch`, or `cycle_review_blocked`.
- Add `missing_required_artifacts` when missing artifacts exist.
- Add `cycle_history_stale` when `stale_history` is true.

The reducer must import only standard library dataclass/datetime plus `PaperRecommendationCycleReviewReport`; no DB, CLI, API, wallet, account, order, signing, network, or file I/O.

- [ ] **Step 4: Verify GREEN**

Run:

```bash
.venv/bin/python -m pytest tests/test_paper_recommendation_cycle_action_gate.py tests/test_paper_recommendation_cycle_action_gate_scope.py -q
```

Expected: pass.

## Task 2: DB-Backed CLI Command

**Files:**
- Modify: `src/polymarket_alpha_lab/cli.py`
- Modify: `tests/test_cli.py`

- [ ] **Step 1: Write failing CLI tests**

Add tests for:

```bash
polymarket-alpha-lab paper-recommendation-cycle-action-gate --limit 50
```

The tests must:
- require cycle snapshot DB enabled.
- inject a fake runner and assert it receives DSN/table/source config/limit plus a `PaperRecommendationCycleActionGateConfig`.
- verify printed output contains `action_status`, `recommended_next_step`, missing artifact count, and reason counts.
- verify DSNs are redacted on runner failure.
- verify the default psycopg load path uses fake psycopg modules and no real DB/network.

- [ ] **Step 2: Verify RED**

Run the new CLI tests with `pytest -q`.

Expected: fail because command is absent.

- [ ] **Step 3: Implement command**

Mirror the existing `paper-recommendation-cycle-review` command:
- use `from_cycle_snapshot_db_env()`.
- load snapshots with `load_paper_recommendation_cycle_snapshots_with_psycopg`.
- build `PaperRecommendationCycleReviewConfig`.
- build `PaperRecommendationCycleActionGateConfig`.
- build `PaperRecommendationCycleActionGateReport`.
- print concise summary only.
- redact DSN on DB/runner failure.

- [ ] **Step 4: Verify GREEN**

Run:

```bash
.venv/bin/python -m pytest tests/test_cli.py -q
```

Expected: pass.

## Task 3: CLI Boundary Scope Test

**Files:**
- Create: `tests/test_cli_paper_recommendation_cycle_action_gate_scope.py`

- [ ] **Step 1: Add AST scope tests**

Parse `src/polymarket_alpha_lab/cli.py` and assert:
- exactly one branch checks `args.command == "paper-recommendation-cycle-action-gate"`.
- branch calls `_run_cycle_snapshot_db_action_gate` and `_print_cycle_snapshot_db_action_gate_summary`.
- parser surface is exactly `--source-config-version`, `source_config_version`, `--limit`, `limit`, `--stale-after-hours`, `stale_after_hours`.
- branch contains no live/auth/wallet/private-key/account/order/sign/submit/cancel/client construction surfaces.

- [ ] **Step 2: Verify**

Run:

```bash
.venv/bin/python -m pytest tests/test_cli_paper_recommendation_cycle_action_gate_scope.py -q
```

Expected: pass once Task 2 implementation exists.

## Task 4: Documentation

**Files:**
- Modify: `docs/paper-recommendation-cycle-snapshot.md`
- Modify: `docs/strategy-recommendation-layer.md`

- [ ] **Step 1: Update docs**

Document the flow:

```text
strategy cycle
-> rich paper recommendation artifacts
-> cycle snapshot
-> Supabase/Postgres persistence
-> DB-backed cycle review
-> paper cycle action gate
-> candidate research/recommendation queue
```

Make explicit that the action gate is not live approval, not order management, not account inspection, and not capital deployment.

- [ ] **Step 2: Verify docs**

Run:

```bash
git diff --check -- docs/paper-recommendation-cycle-snapshot.md docs/strategy-recommendation-layer.md
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

Expected: full suite passes, CodeGraph is up to date, OpenCode returns PASS or only non-blocking findings.
