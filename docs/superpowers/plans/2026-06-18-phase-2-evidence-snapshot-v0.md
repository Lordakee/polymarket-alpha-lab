# Phase 2 Evidence Snapshot v0 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a module-local pure `phase_2_evidence_snapshot` reducer over caller-supplied `PaperForecastCalibrationReport`, `PaperStrategySegmentSummaryReport`, or explicit `None` values.

**Architecture:** Implement one leaf module that validates exact typed in-memory report inputs, treats explicit `None` as missing local evidence, and returns a frozen paper-only/report-only/readonly coverage and gap snapshot. Keep the API module-local; do not add CLI, package-root exports, readers, writers, live-data wrappers, clients, auth/account/wallet/order behavior, ranking, recommendations, trade instructions, or financial advice.

**Tech Stack:** Python frozen dataclasses, `datetime`, existing `PaperForecastCalibrationReport` and `PaperStrategySegmentSummaryReport` values, pytest, AST scope tests, CodeGraph-aware repo navigation.

---

## Planned File Structure

- Create: `src/polymarket_alpha_lab/phase_2_evidence_snapshot.py`
  - Pure reducer only.
  - Public names only in module-local `__all__`.
  - No file IO, network, client Protocol, CLI, package-root export, reader,
    writer, replay, from-file, live-data wrapper, auth, account, wallet, order,
    ranking, recommendation, trade-instruction, transition, promotional, or
    financial-advice surface.
- Create: `tests/test_phase_2_evidence_snapshot.py`
  - Behavior tests for validation, missing report gaps, present report coverage,
    combined statuses, gap rows, and hard report flags.
- Create: `tests/test_phase_2_evidence_snapshot_scope.py`
  - AST/source scope tests for imports, exports, forbidden names, forbidden calls,
    forbidden strings, and package-root/CLI non-integration.

Do not modify source outside the future module, tests outside the two future test
files, README, package root, CLI, trend docs, edge-cost docs, or unrelated docs
unless a later selected node explicitly expands scope.

## TDD Tasks

### Task 1: Behavior Tests First

- [ ] **Step 1: Write RED tests for missing local evidence**
  - Call the builder with both report inputs as explicit `None`.
  - Assert source presence booleans are false.
  - Assert coverage counts are zero or absent as appropriate.
  - Assert deterministic gap rows describe missing forecast calibration evidence
    and missing strategy segment evidence.
  - Assert `status == "phase_2_evidence_missing"`.
  - Assert `paper_only is True`, `report_only is True`, and `readonly is True`.

- [ ] **Step 2: Verify RED**

```bash
.venv/bin/python -m pytest tests/test_phase_2_evidence_snapshot.py -q
```

Expected before implementation: collection fails because
`polymarket_alpha_lab.phase_2_evidence_snapshot` does not exist, or behavior
assertions fail if a partial module exists.

- [ ] **Step 3: Write RED tests for validation**
  - Reject wrong config values and invalid `generated_at`.
  - Reject wrong forecast report values that are not exact
    `PaperForecastCalibrationReport` and not explicit `None`.
  - Reject wrong segment report values that are not exact
    `PaperStrategySegmentSummaryReport` and not explicit `None`.
  - Reject source reports whose `paper_only`, `report_only`, or `readonly` flag
    is not exactly `True`.

- [ ] **Step 4: Write RED tests for present report coverage**
  - Use a calibration report with an observed source status and assert snapshot
    fields copy generated timestamp, observation count, bucket count, source
    status, and key descriptive metric presence.
  - Use a segment summary report and assert snapshot fields copy generated
    timestamp, observation count, strategy segment count, risk-tag segment count,
    and row status counts.
  - Assert source report objects are not mutated.

- [ ] **Step 5: Write RED tests for mixed coverage and gaps**
  - Forecast present plus segment `None` yields
    `phase_2_evidence_partially_observed` and a segment missing gap row.
  - Forecast `None` plus segment present yields
    `phase_2_evidence_partially_observed` and a calibration missing gap row.
  - Empty calibration history creates a descriptive calibration gap row.
  - Insufficient calibration sample creates a descriptive calibration gap row.
  - Calibration quality flags create a descriptive calibration gap row.
  - Insufficient segment probability sample rows create descriptive segment gap
    rows.
  - Return-only segment rows create descriptive segment gap rows.

- [ ] **Step 6: Write RED tests for descriptive status semantics**
  - Both reports present with no gap rows yields `phase_2_evidence_observed`.
  - Any present report family with descriptive gaps yields
    `phase_2_evidence_gaps_observed`.
  - Assert gap/status labels are evidence states only and are not named as
    promotion, transition, approval, ranking, recommendation, trading, or advice
    signals.

### Task 2: Scope Tests First

- [ ] **Step 1: Write RED scope tests**
  - Parse `src/polymarket_alpha_lab/phase_2_evidence_snapshot.py` with `ast`.
  - Allow only stdlib imports plus existing local `forecast_calibration` and
    `strategy_segment_summary` report modules.
  - Assert `__all__` contains exactly:
    `PaperPhase2EvidenceSnapshotConfig`,
    `PaperPhase2EvidenceGapRow`,
    `PaperPhase2EvidenceSnapshotReport`, and
    `build_paper_phase_2_evidence_snapshot_report`.
  - Assert `src/polymarket_alpha_lab/__init__.py` and
    `src/polymarket_alpha_lab/cli.py` do not expose the snapshot API.
  - Assert no public or private names expose live trading, auth, account, wallet,
    private-key, order, client, network, reader, writer, replay, from-file, CLI,
    ranking, recommendation, trade-instruction, transition, promotional, or
    financial-advice behavior.

- [ ] **Step 2: Verify RED**

```bash
.venv/bin/python -m pytest tests/test_phase_2_evidence_snapshot_scope.py -q
```

Expected before implementation: fail because the module does not exist or because
required boundary text/API is absent.

### Task 3: Minimal Implementation

- [ ] **Step 1: Create the module**
  - Define frozen dataclasses for config, gap rows, and the snapshot report.
  - Define the pure builder.
  - Import only stdlib helpers,
    `PaperForecastCalibrationReport`,
    `PaperStrategySegmentSummaryReport`, and known source status constants if
    they are already module-local and stable.

- [ ] **Step 2: Implement validation**
  - Require exact snapshot config type.
  - Require `generated_at` to be a `datetime`.
  - Accept only exact typed source reports or explicit `None`.
  - Require every non-`None` source report to preserve `paper_only is True`,
    `report_only is True`, and `readonly is True`.

- [ ] **Step 3: Implement local coverage reduction**
  - Copy only descriptive source fields into snapshot coverage fields.
  - Represent explicit `None` inputs as missing-local-evidence gap rows.
  - Count segment row statuses from the supplied segment report.
  - Build deterministic gap rows for empty histories, insufficient samples,
    calibration quality flags, insufficient segment probability samples, and
    return-only segment evidence.

- [ ] **Step 4: Keep statuses descriptive**
  - Use status labels only as evidence states.
  - Do not add labels, field names, messages, or helpers that imply transition,
    promotion, approval, blocking, ranking, recommendation, trade instruction,
    order action, position sizing, or financial advice.

### Task 4: Verification

- [ ] **Step 1: Run targeted behavior and scope tests**

```bash
.venv/bin/python -m pytest \
  tests/test_phase_2_evidence_snapshot.py \
  tests/test_phase_2_evidence_snapshot_scope.py -q
```

- [ ] **Step 2: Run adjacent report tests**

```bash
.venv/bin/python -m pytest \
  tests/test_forecast_calibration.py \
  tests/test_strategy_segment_summary.py \
  tests/test_phase_2_evidence_snapshot.py \
  tests/test_phase_2_evidence_snapshot_scope.py -q
```

- [ ] **Step 3: Run the full suite**

```bash
.venv/bin/python -m pytest -q
```

- [ ] **Step 4: Check whitespace and final scope**

```bash
git diff --check
git diff -- src/polymarket_alpha_lab/phase_2_evidence_snapshot.py \
  tests/test_phase_2_evidence_snapshot.py \
  tests/test_phase_2_evidence_snapshot_scope.py
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
