# Paper Recommendation Cycle Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a paper-only recommendation orchestration layer that can bundle candidate recommendations, selection policy output, and human-readable explanations before direct cycle/runner integration.

**Architecture:** Keep the first integration step as pure reducers and append-only JSONL storage, with no live trading, auth, wallet, private-key handling, or exchange writes. The bundle consumes already-built paper-only assessment/readiness reports and produces recommendation, selection, and explanation reports with strict readonly/report-only flags.

**Tech Stack:** Python dataclasses, Decimal-only math, pytest, existing JSON recovery patterns, CodeGraph for code navigation.

---

### File Structure

- Create: `src/polymarket_alpha_lab/strategy_recommendation_bundle.py`
  - Owns a frozen report bundling recommendation, selection policy, and explanation outputs.
  - Exposes `PaperStrategyRecommendationBundleConfig`, `PaperStrategyRecommendationBundleReport`, and `build_paper_strategy_recommendation_bundle_report`.
- Create: `tests/test_strategy_recommendation_bundle.py`
  - Focused tests for bundle construction, strict types, hard flags, timestamp normalization, and consistency.
- Create: `src/polymarket_alpha_lab/strategy_recommendation_log.py`
  - Owns append/read helpers for recommendation bundle JSONL logs.
  - Uses existing JSON recovery/from-jsonable patterns and preserves Decimal/datetime values.
- Create: `tests/test_strategy_recommendation_log.py`
  - Focused tests for append/read, missing log, corrupt lines recovery, strict bundle type checks, and hard flags.
- Modify: `docs/strategy-recommendation-layer.md`
  - Documents the new bundle/log step and states it remains paper-only/report-only/readonly.
- Modify: `tests/test_strategy_recommendation_layer_scope.py`
  - Extends boundary checks so new modules do not introduce live trading, auth, wallet, private-key, or order placement language.

### Task 1: Recommendation Bundle Reducer

**Files:**
- Create: `src/polymarket_alpha_lab/strategy_recommendation_bundle.py`
- Test: `tests/test_strategy_recommendation_bundle.py`

- [ ] **Step 1: Write failing tests**
  - Add a test that builds a `PaperStrategyRecommendationBundleReport` from fixture assessment/readiness reports and asserts the nested recommendation, selection, and explanation reports are present.
  - Add a test that invalid non-paper-only/read-only source reports are rejected.
  - Add a test that selection report counts and explanation rows match the recommendation report.

- [ ] **Step 2: Run focused test to verify RED**
  - Run: `.venv/bin/python -m pytest tests/test_strategy_recommendation_bundle.py -q`
  - Expected: fail because `polymarket_alpha_lab.strategy_recommendation_bundle` is missing.

- [ ] **Step 3: Implement minimal reducer**
  - Add frozen config/report dataclasses.
  - Validate exact source report/config types.
  - Call `build_paper_strategy_candidate_recommendation_report`, `build_paper_strategy_selection_policy_report`, and `build_paper_strategy_recommendation_explanation_report`.
  - Enforce `paper_only is True`, `report_only is True`, and `readonly is True`.

- [ ] **Step 4: Run focused test to verify GREEN**
  - Run: `.venv/bin/python -m pytest tests/test_strategy_recommendation_bundle.py -q`
  - Expected: pass.

### Task 2: Recommendation Bundle JSONL Log

**Files:**
- Create: `src/polymarket_alpha_lab/strategy_recommendation_log.py`
- Test: `tests/test_strategy_recommendation_log.py`

- [ ] **Step 1: Write failing tests**
  - Add append/read tests using `tmp_path`.
  - Add empty existing file behavior test returning an empty tuple.
  - Add missing file behavior test that propagates `FileNotFoundError`.
  - Add invalid JSON, invalid report row, and malformed Decimal tests that fail fast with line-numbered `ValueError` messages.
  - Add strict type and hard flag rejection tests.

- [ ] **Step 2: Run focused test to verify RED**
  - Run: `.venv/bin/python -m pytest tests/test_strategy_recommendation_log.py -q`
  - Expected: fail because `polymarket_alpha_lab.strategy_recommendation_log` is missing.

- [ ] **Step 3: Implement minimal append/read helpers**
  - Reuse existing JSON conversion/recovery patterns from other append-only logs.
  - Preserve the local JSONL reader convention: skip blank lines, return `()` for empty existing files, and fail fast on corrupt rows.
  - Preserve dataclass field names and exact nested report types.
  - Do not add package-root exports.

- [ ] **Step 4: Run focused test to verify GREEN**
  - Run: `.venv/bin/python -m pytest tests/test_strategy_recommendation_log.py -q`
  - Expected: pass.

### Task 3: Documentation and Boundary Tests

**Files:**
- Modify: `docs/strategy-recommendation-layer.md`
- Modify: `tests/test_strategy_recommendation_layer_scope.py`

- [ ] **Step 1: Write/update boundary tests**
  - Add the new bundle/log module paths to existing no-live-trading scope tests.
  - Expected forbidden terms remain live execution/auth/key/wallet/order placement related.

- [ ] **Step 2: Run focused test to verify RED or existing coverage gap**
  - Run: `.venv/bin/python -m pytest tests/test_strategy_recommendation_layer_scope.py -q`
  - Expected: fail before the new module files exist, or pass if written after module creation.

- [ ] **Step 3: Update docs**
  - Describe the flow: assessment/readiness -> recommendation bundle -> JSONL history -> future cycle/runner integration.
  - State that selected rows are paper sizing suggestions only and never exchange orders.

- [ ] **Step 4: Run focused test**
  - Run: `.venv/bin/python -m pytest tests/test_strategy_recommendation_layer_scope.py -q`
  - Expected: pass.

### Task 4: Cycle/CLI Integration Exploration

**Files:**
- Read-only: `src/polymarket_alpha_lab/strategy_cycle.py`, `src/polymarket_alpha_lab/runner.py`, `src/polymarket_alpha_lab/cli.py`, related tests.

- [ ] **Step 1: Map exact integration point**
  - Identify whether the recommendation bundle should be built inside `run_strategy_cycle` while cost-aware reports are still available, or in a new wrapper.

- [ ] **Step 2: Report next patch plan**
  - Output exact files, fields, tests, and risks for a later integration stage.

### Task 5: Verification and Review

**Files:**
- All changed files.

- [ ] **Step 1: Run focused tests**
  - Run bundle/log/scope tests.

- [ ] **Step 2: Run full verification**
  - Run: `.venv/bin/python -m compileall -q src/polymarket_alpha_lab tests`
  - Run: `.venv/bin/python -m pytest -q`
  - Run: `git diff --check`
  - Run a tracked-content secret scan.
  - Run: `codegraph sync`

- [ ] **Step 3: External review**
  - Run Claude Code review with `claude-opus-4-8`, effort `max`.
  - Fix any blocking findings and re-run focused/full verification.

- [ ] **Step 4: Commit and push**
  - Create one focused commit.
  - Push to `origin/main` only after all required gates pass.
