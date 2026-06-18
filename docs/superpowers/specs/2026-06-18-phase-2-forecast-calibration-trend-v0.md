# Phase 2 Forecast Calibration Trend v0 Spec

## Goal

Add a pure module-local `forecast_calibration_trend` reducer that summarizes
append-order movement across caller-supplied `PaperForecastCalibrationReport`
values.

This is a paper-only, report-only, readonly Phase 2 reporting node. It consumes
already-built calibration reports in memory and returns an in-memory trend report.
It does not read evidence, rebuild calibration, fetch data, persist artifacts, or
change any trading, research, screening, CLI, or package-root behavior.

## Scope

Future implementation should add one leaf module:

- `src/polymarket_alpha_lab/forecast_calibration_trend.py`

Expected module-local public API:

- `PaperForecastCalibrationTrendConfig`
- `PaperForecastCalibrationTrendStatusRow`
- `PaperForecastCalibrationTrendReport`
- `build_paper_forecast_calibration_trend_report(reports, *, config, generated_at)`

The API is module-local only. Do not add package-root exports, CLI commands,
readers, writers, replay helpers, from-file APIs, live-data wrappers, client
Protocols, or orchestration surfaces.

## Inputs

The builder accepts only a caller-supplied `list` or `tuple` of exact
`PaperForecastCalibrationReport` values, plus an exact
`PaperForecastCalibrationTrendConfig` and a `datetime` `generated_at`.

It must reject strings, bytes, mappings, arbitrary iterables, mixed types, wrong
report types, subclasses if exact-type validation is used locally, and any report
whose `paper_only`, `report_only`, or `readonly` flag is not exactly `True`.

## Trend Semantics

Input order is append order and is the source of truth.

- `first_*` fields come from `reports[0]`.
- `latest_*` fields come from `reports[-1]`.
- Consecutive counts scan backward from the append-order latest report.
- Reports are not sorted by timestamp.
- Duplicate timestamps are allowed.

Empty input yields a deterministic empty trend report with zero counts, absent
timestamps, absent latest metrics, `None` ratios where the denominator is zero,
and an empty-history status.

The trend report should summarize descriptive report movement, including:

- calibration report count
- first and latest source report timestamps
- latest source `observation_count`, `bucket_count`, status, Brier score, mean
  absolute error, expected calibration error, and max bucket error
- worst observed Brier score, expected calibration error, and max bucket error
  across non-empty source reports
- consecutive latest reports with descriptive quality flags
- status count rows and ratios for known `forecast_calibration` report statuses

Ratios use `Decimal` and the local ratio quantum convention (`0.000001`).

## Status Semantics

Trend statuses and status rows are descriptive evidence states only. They are not
transition signals, approval signals, promotional signals, gates, rankings,
recommendations, trade instructions, or financial advice.

Suggested descriptive trend statuses:

- `empty_calibration_trend_history`
- `latest_calibration_trend_evidence_observed`
- `latest_calibration_trend_sample_incomplete`
- `latest_calibration_trend_quality_flags`

These labels describe the supplied local paper reports. They must not imply that
a market, strategy, model, or account should be traded, advanced, promoted,
blocked, ranked, recommended, sized, or funded.

## Hard Boundaries

The module must remain:

- paper-only
- report-only
- readonly
- pure local reduction over caller-supplied `PaperForecastCalibrationReport`
  values
- module-local API only

The module must not:

- add CLI behavior
- add package-root exports
- read files or JSONL logs
- write files or JSONL logs
- add readers, writers, replay helpers, from-file APIs, path validators, or repair
  utilities
- add live-data wrappers
- fetch market data
- construct clients or client Protocols
- authenticate
- read accounts, balances, positions, fills, orders, wallets, private keys, or
  user exchange state
- place, sign, submit, cancel, amend, or simulate orders
- change paper execution, screening, strategy-cycle, NAV, outcome tracking,
  forecast calibration, or risk-audit behavior
- rank markets, strategies, reports, or models
- recommend trades or investments
- provide trade instructions
- provide financial advice

## Acceptance Criteria

- The builder is pure and deterministic for the supplied report order.
- The output report is frozen and hard-enforces `paper_only is True`,
  `report_only is True`, and `readonly is True`.
- Validation rejects non-list/tuple inputs, wrong report values, wrong config
  values, invalid `generated_at`, and source reports with false boundary flags.
- Empty input produces an empty descriptive trend report.
- Non-empty input preserves append order for first/latest fields and consecutive
  counts.
- Status rows cover known source calibration statuses in deterministic order.
- Scope tests reject imports, names, and string constants that would create live
  trading, auth, wallet, private-key, account, order, reader/writer, CLI,
  ranking, recommendation, trade-instruction, transition, promotional, or
  financial-advice surfaces.

## Verification Commands

Future implementation should run:

```bash
.venv/bin/python -m pytest \
  tests/test_forecast_calibration_trend.py \
  tests/test_forecast_calibration_trend_scope.py -q
.venv/bin/python -m pytest -q
git diff --check
```
