# Phase 2 Strategy Segment Summary Trend v0 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a module-local pure reducer over caller-supplied `PaperStrategySegmentSummaryReport` values.

**Architecture:** Implement one leaf module, `strategy_segment_summary_trend.py`, that validates exact typed report inputs and returns a frozen descriptive trend report. Preserve append order, keep all APIs module-local, and add no CLI, package-root export, IO, live-data, auth/account/wallet/order, ranking, recommendation, trade-instruction, or financial-advice behavior.

**Tech Stack:** Python frozen dataclasses, `datetime`, `Decimal`, existing `PaperStrategySegmentSummaryReport` values, pytest, AST scope tests, CodeGraph-aware repo navigation.

---

## Commit Boundary

This plan is for a future implementation node. The current docs-only node must not modify source, tests, README, package root, CLI, forecast calibration docs, or unrelated docs.

## Planned File Structure

- Create: `src/polymarket_alpha_lab/strategy_segment_summary_trend.py`
- Create: `tests/test_strategy_segment_summary_trend.py`
- Create: `tests/test_strategy_segment_summary_trend_scope.py`

Do not modify:

- `src/polymarket_alpha_lab/__init__.py`
- `src/polymarket_alpha_lab/cli.py`
- readers, writers, logs, replay helpers, or package-root files
- README or forecast calibration docs

## TDD Tasks

### Task 1: Behavior Tests

- [ ] Add failing tests for empty input:
  - `segment_summary_report_count == 0`
  - `first_report_generated_at is None`
  - `latest_report_generated_at is None`
  - latest counts are zero
  - status rows have zero counts and `None` ratios
  - hard flags are `paper_only is True`, `report_only is True`, `readonly is True`

- [ ] Add failing validation tests:
  - config must be exact `PaperStrategySegmentSummaryTrendConfig`
  - `generated_at` must be a `datetime`
  - reports must be `list` or `tuple`
  - strings, bytes, mappings, arbitrary iterables, wrong types, and mixed types are rejected
  - input reports must be exact `PaperStrategySegmentSummaryReport`
  - input reports must preserve `paper_only is True`, `report_only is True`, and `readonly is True`

- [ ] Add failing append-order tests:
  - latest fields come from the last supplied report
  - duplicate timestamps are allowed
  - non-monotonic timestamps do not cause sorting
  - consecutive counts walk backward from the last supplied report

- [ ] Add failing aggregation tests:
  - latest observation, strategy-segment, and risk-tag counts are copied from the latest report
  - status counts and ratios aggregate rows across all supplied reports
  - latest status counts summarize rows from only the append-order latest report
  - consecutive reports with insufficient probability sample rows are counted descriptively
  - consecutive reports with return-only rows are counted descriptively

Run:

```bash
.venv/bin/python -m pytest tests/test_strategy_segment_summary_trend.py -q
```

Expected before implementation: fail during collection or behavior assertions.

### Task 2: Scope Tests

- [ ] Add AST/import tests proving the module imports only stdlib plus `strategy_segment_summary`.
- [ ] Assert `__all__` is exactly:

```python
(
    "PaperStrategySegmentSummaryTrendConfig",
    "PaperStrategySegmentSummaryTrendStatusRow",
    "PaperStrategySegmentSummaryTrendReport",
    "build_paper_strategy_segment_summary_trend_report",
)
```

- [ ] Assert there is no package-root export in `src/polymarket_alpha_lab/__init__.py`.
- [ ] Assert there is no CLI command or CLI import.
- [ ] Assert symbol names and source text do not expose readers, writers, JSONL helpers, replay helpers, from-file APIs, live data wrappers, network calls, auth, account, wallet, private-key, order, client, signing, submission, cancellation, fills, rankings, recommendations, trade instructions, position sizing, promotion, transition, or financial advice.

Run:

```bash
.venv/bin/python -m pytest tests/test_strategy_segment_summary_trend_scope.py -q
```

Expected before implementation: fail because the module does not exist.

### Task 3: Implement Pure Reducer

- [ ] Create `src/polymarket_alpha_lab/strategy_segment_summary_trend.py`.
- [ ] Define frozen config, status-row, and report dataclasses.
- [ ] Validate exact config type and `generated_at`.
- [ ] Normalize reports from only `list` or `tuple`.
- [ ] Validate every source report is exact `PaperStrategySegmentSummaryReport` and has hard paper/report/readonly flags.
- [ ] Build the trend report using append order only.
- [ ] Quantize ratios to `Decimal("0.000001")`.
- [ ] Keep statuses descriptive evidence states only; do not encode transition, promotion, ranking, recommendation, trading, or advice semantics.
- [ ] Add no CLI, package-root export, reader, writer, live wrapper, auth/account/wallet/order/client behavior, ranking, recommendation, trade instruction, or financial-advice behavior.

Run:

```bash
.venv/bin/python -m pytest \
  tests/test_strategy_segment_summary_trend.py \
  tests/test_strategy_segment_summary_trend_scope.py -q
```

Expected after implementation: pass.

### Task 4: Verification

- [ ] Run targeted trend tests:

```bash
.venv/bin/python -m pytest \
  tests/test_strategy_segment_summary_trend.py \
  tests/test_strategy_segment_summary_trend_scope.py -q
```

- [ ] Run existing segment summary tests to catch contract drift:

```bash
.venv/bin/python -m pytest tests/test_strategy_segment_summary.py -q
```

- [ ] Run full suite:

```bash
.venv/bin/python -m pytest -q
```

- [ ] Run whitespace check:

```bash
git diff --check
```

- [ ] Review final diff and confirm only the planned implementation/test files changed, with no source changes outside `strategy_segment_summary_trend.py` and no package-root, CLI, README, forecast calibration doc, reader, writer, or live-data changes.
