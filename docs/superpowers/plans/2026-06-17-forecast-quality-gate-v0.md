# Forecast Quality Gate v0 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a fifth Strategy Risk Audit gate that uses nested forecast probability calibration quality from `OutcomeTrackingReport`.

**Architecture:** Keep the change inside the existing pure `strategy_risk_audit.py` module. Do not import `forecast_evidence`; consume only attributes on the caller-supplied `OutcomeTrackingReport.forecast_evidence_report`. Update behavior/scope tests, docs, and README to reflect the 5-gate readiness audit.

**Tech Stack:** Python stdlib, frozen dataclasses, Decimal, pytest, CodeGraph.

---

## File Structure

- Modify `src/polymarket_alpha_lab/strategy_risk_audit.py`
  - Add `min_forecast_probability_observation_count` to `PaperStrategyRiskAuditConfig`.
  - Add `forecast_quality` to `GATE_NAMES`.
  - Add `_build_forecast_quality_gate`.
  - Insert the gate between `settlement_evidence` and `nav_drawdown`.
- Modify `tests/test_strategy_risk_audit.py`
  - Update ready/immature/blocking expectations from 4 gates to 5 gates.
  - Add tests for `forecast_quality` pass, fail, and incomplete states.
- Modify `tests/test_strategy_risk_audit_scope.py`
  - Keep import allowlist unchanged.
  - Add doc fragments for the new forecast quality gate and no-direct-forecast-evidence import boundary.
- Modify `README.md`
  - Update Strategy Risk Audit docs from four gates to five gates.
- Modify `docs/superpowers/specs/2026-06-16-strategy-risk-audit-v0.md`
  - Mention `forecast_quality` as an added v0 gate over nested forecast evidence.
- Create `docs/superpowers/specs/2026-06-17-forecast-quality-gate-v0.md`
  - Durable spec for this node.
- Create `docs/superpowers/plans/2026-06-17-forecast-quality-gate-v0.md`
  - This implementation plan.

## Task 1: RED Behavior Tests

- [x] Add a test proving a ready report has five gates in this order:
  - `paper_history`
  - `settlement_evidence`
  - `forecast_quality`
  - `nav_drawdown`
  - `open_exposure`
- [x] Assert `gate_count == 5`, `pass_count == 5`, `fail_count == 0`, and `incomplete_count == 0` for ready evidence.
- [x] Add a test where nested `probability_quality` fails and assert:
  - report status is `blocked_by_risk`
  - `forecast_quality.status == "fail"`
  - `forecast_quality.observed_value` includes `forecast_probability_quality_status=fail`
- [x] Add a test where nested probability sample count is below `min_forecast_probability_observation_count` and assert:
  - report status is `insufficient_evidence`
  - `forecast_quality.status == "incomplete"`
- [x] Add a test where `outcome_report is None` and assert both `settlement_evidence` and `forecast_quality` are incomplete.
- [x] Run `.venv/bin/python -m pytest tests/test_strategy_risk_audit.py -q` and confirm RED before production code changes.

## Task 2: RED Scope Tests

- [x] Update `tests/test_strategy_risk_audit_scope.py` expected gate documentation fragments:
  - `forecastquality`
  - `forecastevidencereport`
  - `nodirectimportofpolymarketalphalabforecastevidence`
- [x] Keep `ALLOWED_IMPORT_MODULES` unchanged; this proves the implementation does not import `polymarket_alpha_lab.forecast_evidence`.
- [x] Run `.venv/bin/python -m pytest tests/test_strategy_risk_audit_scope.py -q` and confirm RED while docs/module still lack the new gate.

## Task 3: Implement Pure Forecast Quality Gate

- [x] Add `"forecast_quality"` to `GATE_NAMES` between `settlement_evidence` and `nav_drawdown`.
- [x] Insert `_build_forecast_quality_gate(outcome_report)` in `gate_results` between settlement and NAV drawdown.
- [x] Add config field `min_forecast_probability_observation_count: int = 10` and validate it as a nonnegative int.
- [x] Implement `_build_forecast_quality_gate` using only `OutcomeTrackingReport.forecast_evidence_report` attributes:
  - absent outcome report -> incomplete
  - absent nested report -> incomplete
  - nested `probability_observation_count` below config floor -> incomplete
  - nested `probability_quality` gate status `pass` -> pass
  - nested `probability_quality` gate status `fail` -> fail
  - nested `probability_quality` gate status `incomplete` -> incomplete
- [x] Format observed value as:
  - `forecast_probability_quality_status=<status>; mean_probability_loss=<value>; worst_bucket_error=<value>; probability_observation_count=<value>`
- [x] Run focused behavior tests and keep scope tests green.

## Task 4: Docs and Export Stability

- [x] Update README Strategy Risk Audit status/API sections to mention five gates and forecast quality.
- [x] Update `docs/superpowers/specs/2026-06-16-strategy-risk-audit-v0.md` to include `forecast_quality` as a nested forecast evidence gate.
- [x] Keep `src/polymarket_alpha_lab/__init__.py` and public `__all__` unchanged.
- [x] Run `tests/test_strategy_risk_audit_scope.py` and `tests/test_init.py`.

## Task 5: Verification, Review, Commit

- [x] Run focused tests:
  - `.venv/bin/python -m pytest tests/test_strategy_risk_audit.py tests/test_strategy_risk_audit_scope.py tests/test_init.py -q`
- [x] Run regression tests:
  - `.venv/bin/python -m pytest tests/test_forecast_evidence.py tests/test_outcome_tracker.py tests/test_strategy_risk_audit.py tests/test_strategy_risk_audit_scope.py tests/test_init.py -q`
- [x] Run full suite:
  - `.venv/bin/python -m pytest -q`
- [x] Run `git diff --check`.
- [x] Run secret scan over `README.md docs src tests`.
- [x] Run `codegraph sync` and `codegraph status .`.
- [x] Request Claude review with `claude-opus-4-8`, effort max.
- [x] Commit locally only; do not push `origin/main`.
