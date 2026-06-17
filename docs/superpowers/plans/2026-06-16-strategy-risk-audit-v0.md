# Strategy Risk Audit v0 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a read-only paper evidence maturity audit over existing summary reports.

**Architecture:** Add one pure `strategy_risk_audit.py` module that consumes typed `PerformanceSummary`, `PaperNavRiskMetricsReport`, and optional `OutcomeTrackingReport` values. The module emits gate rows and one status; it reads no files and touches no live/client/order/auth surfaces.

**Tech Stack:** Python stdlib, frozen dataclasses, Decimal, pytest, CodeGraph.

---

## File Structure

- Create `src/polymarket_alpha_lab/strategy_risk_audit.py`
  - Frozen config/gate/report dataclasses and pure report builder.
- Create `tests/test_strategy_risk_audit.py`
  - Behavior, validation, frozen dataclass, and status tests.
- Create `tests/test_strategy_risk_audit_scope.py`
  - Static import/export/boundary tests and spec documentation checks.
- Modify `src/polymarket_alpha_lab/__init__.py`
  - Export the four public API names.
- Modify `tests/test_init.py`
  - Assert package-root exports.
- Modify `README.md`
  - Document Strategy Risk Audit v0 as a paper-only/report-only readiness gate.

## Task 1: RED Behavior Tests

- [x] Add `tests/test_strategy_risk_audit.py`.
- [x] Assert empty/immature evidence yields `insufficient_evidence`.
- [x] Assert drawdown/exposure breaches yield `blocked_by_risk`.
- [x] Assert enough history plus resolved outcomes and acceptable NAV risk yields `audit_ready`.
- [x] Assert dataclasses are frozen and `paper_only` / `report_only` are hard-enforced.
- [x] Run `pytest tests/test_strategy_risk_audit.py -q` and confirm RED.

## Task 2: RED Scope and Export Tests

- [x] Add `tests/test_strategy_risk_audit_scope.py`.
- [x] Assert imports are limited to stdlib plus `nav_risk_metrics`, `outcome_tracker`, and `performance_summary`.
- [x] Assert no live API, client, auth, wallet, order, fetch, ranking, recommendation, or advice surfaces.
- [x] Assert exact public exports.
- [x] Add package-root export tests in `tests/test_init.py`.

## Task 3: Implement Pure Audit Module

- [x] Create `strategy_risk_audit.py`.
- [x] Implement config thresholds with Decimal-only risk math.
- [x] Implement four gates: `paper_history`, `settlement_evidence`, `nav_drawdown`, `open_exposure`.
- [x] Implement status derivation: fail -> `blocked_by_risk`, incomplete -> `insufficient_evidence`, all pass -> `audit_ready`.

## Task 4: Docs and Exports

- [x] Add root exports.
- [x] Add README status/API note.
- [x] Keep all language framed as audit readiness, not market ranking or trading advice.

## Task 5: Verification, Review, Commit

- [x] Run focused tests.
- [x] Run full `pytest -q`.
- [x] Run `git diff --check`, secret scan, `codegraph sync`, and `codegraph status .`.
- [x] Request Claude review with `claude-opus-4-8`, effort max.
- [x] Commit locally only; do not push `origin/main`.
