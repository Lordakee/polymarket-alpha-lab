# Phase 2 Calibration Segmentation v0 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add Phase 2 paper-only/report-only/read-only calibration and segmentation report modules without creating any live-trading, account, recommendation, ranking, trade-instruction, or financial-advice surface.

**Architecture:** Create two pure local leaf modules: `forecast_calibration` for resolved probability calibration evidence, and `strategy_segment_summary` for segment-level paper evidence summaries with separate probability and return observation roles. Keep all inputs caller-supplied in memory, keep APIs module-local, do not add package-root exports or CLI wrappers, and preserve the Phase 1 live-trading boundary.

**Boundary:** Phase 2 is still no live trading, no auth, no wallet/private key, no order placement/signing/submission/cancellation, no account reads, no recommendations/ranking/trade instruction/financial advice.

**Tech Stack:** Python stdlib, frozen dataclasses, `Decimal`, caller-supplied `PaperForecastEvidenceObservation` values, pytest, CodeGraph-aware repo navigation.

---

## File Structure

- Create `src/polymarket_alpha_lab/forecast_calibration.py`
  - Pure local report builder for resolved forecast evidence: rows count only observations with both `predicted_probability` and `actual_outcome_value`.
  - Hard-enforce `paper_only`, `report_only`, and `readonly`.
  - Keep public API names in the module-local `__all__` only; do not add package-root exports for this node.
  - No fetch, auth, wallet, private-key, account, order, recommendation, ranking, trade-instruction, financial-advice, file-reader, log-writer, replay, from-file, or CLI surfaces.
- Create `src/polymarket_alpha_lab/strategy_segment_summary.py`
  - Pure local report builder for segment rows over caller-supplied paper evidence.
  - Keep probability observation counts and return observation counts separate.
  - Keep return-only rows descriptive and keep thin probability samples incomplete rather than treating them as later-phase evidence.
  - Keep public API names in the module-local `__all__` only; do not add package-root exports for this node.
  - No strategy tuning, market scoring, position sizing, recommendations, rankings, trade instructions, file readers, log writers, replay/from-file APIs, or CLI surfaces.
- Create `tests/test_forecast_calibration.py`
  - Behavior tests for calibration math, empty evidence, thin samples, and Polymarket probability framing.
- Create `tests/test_forecast_calibration_scope.py`
  - Scope tests proving local-report-only imports and forbidden surface absence.
- Create `tests/test_strategy_segment_summary.py`
  - Behavior tests for segment grouping, count/ratio metrics, incomplete thin probability samples, and return-only role handling.
- Create `tests/test_strategy_segment_summary_scope.py`
  - Scope tests proving local-report-only imports and forbidden surface absence.
- Do not modify `src/polymarket_alpha_lab/__init__.py`
  - These modules remain module-level library APIs with exact module-local `__all__` values.
- Do not modify `src/polymarket_alpha_lab/cli.py`
  - This Phase 2 node is module-local API only. Do not add CLI commands, file readers, log writers, replay helpers, or from-file APIs.
- Modify `README.md`
  - Document Phase 2 direction as paper-only/report-only/read-only, with no live-trading overpromise.

## Task 1: Forecast Calibration Behavior Tests

- [ ] Write failing tests in `tests/test_forecast_calibration.py` for:
  - empty input returning zero counts and an incomplete status
  - calibrated bucket rows over resolved observations that include `predicted_probability` and `actual_outcome_value`
  - Brier score, expected calibration error, max bucket error, and mean absolute error using `Decimal`
  - sample-count floors keeping thin evidence incomplete
  - unresolved, edge-only, or return-only observations staying out of calibration counts
  - hard `paper_only is True`, `report_only is True`, and `readonly is True`
- [ ] Run `.venv/bin/python -m pytest tests/test_forecast_calibration.py -q` and confirm it fails because the module does not exist yet.

## Task 2: Forecast Calibration Scope Tests

- [ ] Write failing tests in `tests/test_forecast_calibration_scope.py` proving:
  - imports are stdlib plus existing local paper/report modules only
  - public exports are exactly the module-local calibration config, bucket, report, and builder types; no root exports and no log/reader/CLI types
  - source text contains the boundary fragments `no live trading`, `no auth`, `no wallet`, `no private key`, `no order`, `no account reads`, `no recommendation`, `no ranking`, `no trade instruction`, and `no financial advice`
  - no symbol names expose order placement, signing, submission, cancellation, account reads, wallet handling, private-key handling, recommendations, rankings, financial advice, file loading, log writing, replay, from-file APIs, or CLI commands
- [ ] Run `.venv/bin/python -m pytest tests/test_forecast_calibration_scope.py -q` and confirm it fails before implementation.

## Task 3: Implement `forecast_calibration`

- [ ] Create `src/polymarket_alpha_lab/forecast_calibration.py` with frozen dataclasses for config, bucket rows, and the final report.
- [ ] Implement a pure builder that accepts caller-supplied `PaperForecastEvidenceObservation` values and returns a report without fetching, authenticating, reading files/accounts, touching wallets/private keys, writing logs, constructing trading clients, or exposing CLI behavior.
- [ ] Preserve probability framing by documenting that `predicted_probability` is the already-supplied probability being evaluated against `actual_outcome_value`; this module does not fetch or infer Polymarket implied probability, modeled fair probability, executable edge, or realized return.
- [ ] Keep calibration resolved-evidence-only: incomplete probability rows, unresolved rows, edge-only rows, and return-only rows are excluded from calibration metrics.
- [ ] Run `.venv/bin/python -m pytest tests/test_forecast_calibration.py tests/test_forecast_calibration_scope.py -q` and confirm they pass.

## Task 4: Strategy Segment Summary Behavior Tests

- [ ] Write failing tests in `tests/test_strategy_segment_summary.py` for:
  - empty input returning zero segment rows and zero counts
  - grouping by strategy type and risk tags
  - segment counts, probability observation counts, return observation counts, calibration summaries, mean paper return ratio, and positive return rate
  - return-only segments remaining descriptive rather than calibration evidence
  - thin probability samples remaining incomplete even when return evidence exists
  - hard `paper_only is True`, `report_only is True`, and `readonly is True`
- [ ] Run `.venv/bin/python -m pytest tests/test_strategy_segment_summary.py -q` and confirm it fails because the module does not exist yet.

## Task 5: Strategy Segment Summary Scope Tests

- [ ] Write failing tests in `tests/test_strategy_segment_summary_scope.py` proving:
  - imports are stdlib plus existing local paper/report modules only
  - public exports are exactly the module-local segment summary config, row, report, and builder types; no root exports and no log/reader/CLI types
  - source text contains the same explicit Phase 2 boundary fragments as `forecast_calibration`
  - no symbol names expose live trading, auth, wallet, private-key, account-read, order, recommendation, ranking, trade-instruction, later-phase transition, position-sizing, financial-advice, file-loading, log-writing, replay, from-file, or CLI surfaces
- [ ] Run `.venv/bin/python -m pytest tests/test_strategy_segment_summary_scope.py -q` and confirm it fails before implementation.

## Task 6: Implement `strategy_segment_summary`

- [ ] Create `src/polymarket_alpha_lab/strategy_segment_summary.py` with frozen config, segment row, and report dataclasses.
- [ ] Implement deterministic grouping over caller-supplied local paper evidence only.
- [ ] Add row statuses so segment rows distinguish incomplete probability samples from sufficient probability samples and return-only evidence without ranking or recommending segments.
- [ ] Keep probability evidence fields (`predicted_probability` plus `actual_outcome_value`) separate from return evidence fields (`paper_return_ratio` plus the upstream executable-edge role required by `PaperForecastEvidenceObservation`).
- [ ] Keep return-only rows descriptive and ensure they do not satisfy probability calibration sample thresholds.
- [ ] Run `.venv/bin/python -m pytest tests/test_strategy_segment_summary.py tests/test_strategy_segment_summary_scope.py -q` and confirm they pass.

## Task 7: Module API And Docs

- [ ] Keep the two report APIs as module-level library APIs with exact module-local `__all__` values; do not add package-root exports in `src/polymarket_alpha_lab/__init__.py` for this node.
- [ ] Do not add CLI commands, file readers, log writers, replay helpers, from-file APIs, package-root exports, fetch paths, account paths, order paths, ranking, recommendation, or trading behavior.
- [ ] Update `README.md` to keep Phase 2 described as paper-only/report-only/read-only and to preserve the Phase 1 live-trading boundary.
- [ ] Run `.venv/bin/python -m pytest tests/test_cli.py -q` only if a future plan explicitly changes CLI despite this boundary.
- [ ] Run `.venv/bin/python -m pytest tests/test_init.py -q` only if a future plan explicitly changes package-root exports despite this boundary.

## Task 8: Verification

- [ ] Run targeted tests:

```bash
.venv/bin/python -m pytest \
  tests/test_forecast_calibration.py \
  tests/test_forecast_calibration_scope.py \
  tests/test_strategy_segment_summary.py \
  tests/test_strategy_segment_summary_scope.py -q
```

- [ ] Run the full suite:

```bash
.venv/bin/python -m pytest -q
```

- [ ] Run documentation and whitespace checks:

```bash
git diff --check
```

- [ ] Review the final diff and confirm no implementation creates live trading, auth, wallet/private-key handling, account reads, order placement/signing/submission/cancellation, recommendation, ranking, trade-instruction, later-phase transition, or financial-advice behavior.
