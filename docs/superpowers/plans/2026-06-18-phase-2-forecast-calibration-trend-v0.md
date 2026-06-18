# Phase 2 Forecast Calibration Trend v0 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a module-local pure `forecast_calibration_trend` reducer over caller-supplied `PaperForecastCalibrationReport` values.

**Architecture:** Implement one leaf module that validates exact in-memory calibration report inputs, preserves append-order semantics, and returns a frozen paper-only/report-only/readonly trend report. Keep the API module-local; do not add CLI, package-root exports, readers, writers, live-data wrappers, clients, auth/account/wallet/order behavior, ranking, recommendations, trade instructions, or financial advice.

**Tech Stack:** Python frozen dataclasses, `datetime`, `Decimal`, existing `PaperForecastCalibrationReport` values, pytest, AST scope tests, CodeGraph-aware repo navigation.

---

## Planned File Structure

- Create: `src/polymarket_alpha_lab/forecast_calibration_trend.py`
  - Pure reducer only.
  - Public names only in module-local `__all__`.
  - No file IO, network, client Protocol, CLI, package-root export, reader,
    writer, replay, from-file, live-data wrapper, auth, account, wallet, order,
    ranking, recommendation, trade-instruction, transition, promotional, or
    financial-advice surface.
- Create: `tests/test_forecast_calibration_trend.py`
  - Behavior tests for validation, empty input, append-order latest semantics,
    worst-observed metrics, consecutive latest status counts, status rows, and
    hard report flags.
- Create: `tests/test_forecast_calibration_trend_scope.py`
  - AST/source scope tests for imports, exports, forbidden names, forbidden calls,
    forbidden strings, and package-root/CLI non-integration.

Do not modify source outside the future module, tests outside the two future test
files, README, package root, CLI, or other docs unless a later selected node
explicitly expands scope.

## TDD Tasks

### Task 1: Behavior Tests First

- [ ] **Step 1: Write RED tests for empty trend output**
  - Assert zero report count.
  - Assert absent first/latest timestamps and latest metrics.
  - Assert `status == "empty_calibration_trend_history"`.
  - Assert `paper_only is True`, `report_only is True`, and `readonly is True`.

- [ ] **Step 2: Verify RED**

```bash
.venv/bin/python -m pytest tests/test_forecast_calibration_trend.py -q
```

Expected before implementation: collection fails because
`polymarket_alpha_lab.forecast_calibration_trend` does not exist.

- [ ] **Step 3: Write RED tests for validation**
  - Reject non-list/tuple inputs, strings, bytes, mappings, arbitrary iterables,
    wrong report values, wrong config values, invalid `generated_at`, and source
    reports whose `paper_only`, `report_only`, or `readonly` flag is not exactly
    `True`.

- [ ] **Step 4: Write RED tests for append-order semantics**
  - Use reports with non-sorted or duplicate `generated_at` values.
  - Assert `first_report_generated_at` comes from `reports[0]`.
  - Assert `latest_report_generated_at`, latest status, latest counts, and latest
    metrics come from `reports[-1]`.
  - Assert the builder never sorts source reports by timestamp.

- [ ] **Step 5: Write RED tests for descriptive trend metrics**
  - Assert status rows cover the known `forecast_calibration` report statuses.
  - Assert status ratios are `Decimal` values quantized to `0.000001`.
  - Assert worst observed Brier score, expected calibration error, and max bucket
    error ignore absent values and select the highest observed descriptive metric.
  - Assert consecutive latest quality-flag count scans backward in append order.

### Task 2: Scope Tests First

- [ ] **Step 1: Write RED scope tests**
  - Parse `src/polymarket_alpha_lab/forecast_calibration_trend.py` with `ast`.
  - Allow only stdlib imports plus the existing local `forecast_calibration`
    report module.
  - Assert `__all__` contains exactly:
    `PaperForecastCalibrationTrendConfig`,
    `PaperForecastCalibrationTrendStatusRow`,
    `PaperForecastCalibrationTrendReport`, and
    `build_paper_forecast_calibration_trend_report`.
  - Assert `src/polymarket_alpha_lab/__init__.py` and
    `src/polymarket_alpha_lab/cli.py` do not expose the trend API.
  - Assert no public or private names expose live trading, auth, account, wallet,
    private-key, order, client, network, reader, writer, replay, from-file, CLI,
    ranking, recommendation, trade-instruction, transition, promotional, or
    financial-advice behavior.

- [ ] **Step 2: Verify RED**

```bash
.venv/bin/python -m pytest tests/test_forecast_calibration_trend_scope.py -q
```

Expected before implementation: fail because the module does not exist or because
required boundary text/API is absent.

### Task 3: Minimal Implementation

- [ ] **Step 1: Create the module**
  - Define frozen dataclasses for config, status rows, and the trend report.
  - Define the pure builder.
  - Import only stdlib helpers and `PaperForecastCalibrationReport` plus the
    known calibration statuses from `forecast_calibration.py`.

- [ ] **Step 2: Implement validation**
  - Require exact trend config type.
  - Require `generated_at` to be a `datetime`.
  - Require `reports` to be a list or tuple.
  - Require every report to be exactly `PaperForecastCalibrationReport`.
  - Require every report to preserve `paper_only is True`,
    `report_only is True`, and `readonly is True`.

- [ ] **Step 3: Implement append-order reduction**
  - Empty input returns deterministic empty values.
  - Non-empty input uses `reports[0]` and `reports[-1]` for first/latest fields.
  - Compute status rows in deterministic known-status order.
  - Compute worst-observed descriptive metrics from non-`None` source values.
  - Compute consecutive latest quality-flag count by scanning backward from the
    append-order latest report.

- [ ] **Step 4: Keep statuses descriptive**
  - Use status labels only as evidence states.
  - Do not add labels or messages that imply transition, promotion, approval,
    blocking, ranking, recommendation, trade instruction, or financial advice.

### Task 4: Verification

- [ ] **Step 1: Run targeted behavior and scope tests**

```bash
.venv/bin/python -m pytest \
  tests/test_forecast_calibration_trend.py \
  tests/test_forecast_calibration_trend_scope.py -q
```

- [ ] **Step 2: Run adjacent calibration tests**

```bash
.venv/bin/python -m pytest \
  tests/test_forecast_calibration.py \
  tests/test_forecast_calibration_scope.py \
  tests/test_forecast_calibration_trend.py \
  tests/test_forecast_calibration_trend_scope.py -q
```

- [ ] **Step 3: Run the full suite**

```bash
.venv/bin/python -m pytest -q
```

- [ ] **Step 4: Check whitespace and final scope**

```bash
git diff --check
git diff -- src/polymarket_alpha_lab/forecast_calibration_trend.py \
  tests/test_forecast_calibration_trend.py \
  tests/test_forecast_calibration_trend_scope.py
```

- [ ] **Step 5: Review boundary compliance**
  - Confirm no CLI, package-root export, reader, writer, replay, from-file API,
    live-data wrapper, auth/account/wallet/order behavior, ranking,
    recommendation, trade instruction, transition/promotion signal, or financial
    advice was introduced.

## Notes For Implementers

- This plan does not claim any tests have passed.
- Use CodeGraph first in indexed workspaces before grep/find or manual file
  reads.
- Keep commits small: tests RED, implementation GREEN, refactor only after the
  targeted tests pass.
