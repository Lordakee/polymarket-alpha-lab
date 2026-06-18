# Phase 2 Strategy Segment Summary Trend v0 Spec

## Goal

Add a pure local `strategy_segment_summary_trend` reducer that summarizes append-order trends across caller-supplied `PaperStrategySegmentSummaryReport` values.

This is a paper-only, report-only, readonly Phase 2 reporting surface. It must stay module-local and must not change live trading, strategy behavior, package exports, CLI behavior, readers, writers, or existing forecast calibration docs.

## Scope

Create one future leaf module:

- `src/polymarket_alpha_lab/strategy_segment_summary_trend.py`

Expected module-local public API:

- `PaperStrategySegmentSummaryTrendConfig`
- `PaperStrategySegmentSummaryTrendStatusRow`
- `PaperStrategySegmentSummaryTrendReport`
- `build_paper_strategy_segment_summary_trend_report(reports, *, config, generated_at)`

The builder consumes only a list or tuple of already-built `PaperStrategySegmentSummaryReport` values supplied in memory by the caller. Input order is append order: `first_*`, `latest_*`, and consecutive counts come from the supplied sequence, not timestamp sorting.

## Hard Boundaries

The module must be:

- paper-only
- report-only
- readonly
- pure local reduction over caller-supplied report objects
- module-local API only

The module must not add:

- CLI commands or CLI wiring
- package-root exports
- readers, writers, JSONL helpers, replay helpers, from-file APIs, or path validation
- live data wrappers
- network calls
- auth, account, wallet, private-key, order, client, signing, submission, cancellation, or fill behavior
- ranking, recommendation, market selection, strategy promotion, trade instruction, position sizing, or financial advice

Do not modify source outside the future leaf module, tests outside the future trend tests, README, package root, CLI, forecast calibration docs, or unrelated docs.

## Semantics

The reducer summarizes already-built `PaperStrategySegmentSummaryReport` snapshots:

- summary report count
- first and latest report `generated_at`
- latest observation count
- latest strategy segment count
- latest risk-tag segment count
- latest segment status counts from the latest report
- status counts and ratios across all rows in all supplied reports
- latest rows grouped by status
- consecutive latest reports with any insufficient probability sample rows
- consecutive latest reports with any return-only rows

Status values are descriptive evidence states only:

- `insufficient_segment_probability_sample`
- `segment_evidence_observed`
- `segment_return_evidence_observed`

Statuses must not be treated as transition signals, approval signals, promotion signals, rankings, recommendations, trade instructions, or financial advice.

Ratios use `Decimal` quantized to `0.000001`. Empty input returns zero counts, absent timestamps, `None` ratios where no denominator exists, and `paper_only is True`, `report_only is True`, `readonly is True`.

## Validation

The builder must:

- accept only `list` or `tuple`
- reject strings, bytes, mappings, arbitrary iterables, mixed types, and wrong report types
- validate exact `PaperStrategySegmentSummaryTrendConfig` type
- validate `generated_at` is a `datetime`
- reject source reports unless `paper_only is True`, `report_only is True`, and `readonly is True`
- preserve append order even when timestamps are duplicated or non-monotonic
- avoid sorting reports by timestamp
- copy only descriptive fields from source reports

The output dataclasses must be frozen and must hard-enforce `paper_only is True`, `report_only is True`, and `readonly is True`.

## Acceptance Criteria

- The reducer has no IO, network, auth, account, wallet, order, client, ranking, recommendation, trade-instruction, or financial-advice surface.
- The API remains importable only from `polymarket_alpha_lab.strategy_segment_summary_trend`.
- Scope tests prove no package-root export or CLI entry was added.
- Behavior tests cover empty input, validation failures, append-order latest semantics, duplicate timestamps, status aggregation, ratios, consecutive insufficient-sample counts, consecutive return-only counts, and hard flags.
