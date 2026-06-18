# Phase 2 Evidence Snapshot v0 Spec

## Goal

Add a pure module-local `phase_2_evidence_snapshot` reducer that combines
caller-supplied `PaperForecastCalibrationReport` and
`PaperStrategySegmentSummaryReport` values into one descriptive coverage/gap
snapshot.

This is a paper-only, report-only, readonly Phase 2 reporting node. It consumes
already-built typed reports or explicit `None` values in memory and returns an
in-memory snapshot report. It does not read evidence, rebuild reports, fetch
data, persist artifacts, or change trading, research, screening, CLI, or
package-root behavior.

## Scope

Future implementation should add one leaf module:

- `src/polymarket_alpha_lab/phase_2_evidence_snapshot.py`

Expected module-local public API:

- `PaperPhase2EvidenceSnapshotConfig`
- `PaperPhase2EvidenceGapRow`
- `PaperPhase2EvidenceSnapshotReport`
- `build_paper_phase_2_evidence_snapshot_report(*, forecast_calibration_report, strategy_segment_summary_report, config, generated_at)`

The API is module-local only. Do not add package-root exports, CLI commands,
readers, writers, replay helpers, from-file APIs, live-data wrappers, client
Protocols, or orchestration surfaces.

## Inputs

The builder accepts:

- `forecast_calibration_report`: an exact `PaperForecastCalibrationReport` or
  explicit `None`
- `strategy_segment_summary_report`: an exact
  `PaperStrategySegmentSummaryReport` or explicit `None`
- `config`: an exact `PaperPhase2EvidenceSnapshotConfig`
- `generated_at`: a `datetime`

`None` is meaningful: it means the caller has no local evidence report for that
area. The reducer must describe that absence as a local evidence gap. It must not
try to load, fetch, infer, or repair the missing report.

The builder must reject wrong report types, wrong config values, invalid
`generated_at`, and source reports whose `paper_only`, `report_only`, or
`readonly` flag is not exactly `True`.

## Snapshot Semantics

The snapshot is a descriptive coverage/gap view over the two supplied report
families:

- forecast calibration coverage: whether a calibration report is present,
  calibration observation count, bucket count, generated timestamp, source
  status, and missing/thin/quality-flag gap state
- strategy segment coverage: whether a segment summary report is present,
  observation count, strategy segment count, risk-tag segment count, generated
  timestamp, row status counts, and missing/thin/return-only gap state
- combined coverage status describing whether both source report families are
  present, partially present, or absent
- deterministic gap rows for missing reports, empty histories, insufficient
  calibration samples, calibration quality flags, insufficient segment
  probability samples, and return-only segment evidence

Suggested descriptive snapshot statuses:

- `phase_2_evidence_missing`
- `phase_2_evidence_partially_observed`
- `phase_2_evidence_observed`
- `phase_2_evidence_gaps_observed`

Gap and status labels are descriptive evidence states only. They are not
transition signals, approval signals, promotion signals, gates, rankings,
recommendations, trade instructions, or financial advice.

## Hard Boundaries

The module must remain:

- paper-only
- report-only
- readonly
- pure local reduction over caller-supplied typed report objects or explicit
  `None`
- module-local API only

The module must not:

- add CLI behavior
- add package-root exports
- read files or JSONL logs
- write files or JSONL logs
- add readers, writers, replay helpers, from-file APIs, path validators, or
  repair utilities
- add live-data wrappers
- fetch market data
- construct clients or client Protocols
- authenticate
- read accounts, balances, positions, fills, orders, wallets, private keys, or
  user exchange state
- place, sign, submit, cancel, amend, or simulate orders
- change paper execution, screening, strategy-cycle, NAV, outcome tracking,
  forecast calibration, segment summary, trend, risk-audit, or edge-cost
  behavior
- rank markets, strategies, reports, segments, gaps, or models
- recommend trades or investments
- provide trade instructions
- provide financial advice

## Acceptance Criteria

- The reducer is pure and deterministic for the supplied in-memory reports.
- Explicit `None` inputs produce descriptive missing-local-evidence gap rows.
- Source report values are copied only into descriptive coverage fields.
- The output report is frozen and hard-enforces `paper_only is True`,
  `report_only is True`, and `readonly is True`.
- The implementation validates exact config type, `generated_at`, report types,
  explicit `None`, and source report boundary flags.
- Snapshot statuses and gap rows remain descriptive evidence states and do not
  encode transition, promotion, ranking, recommendation, trading, or advice
  semantics.
- Scope tests reject imports, names, and string constants that would create live
  trading, auth, wallet, private-key, account, order, reader/writer, CLI,
  ranking, recommendation, trade-instruction, transition, promotional, or
  financial-advice surfaces.

## Verification Commands

Future implementation should run:

```bash
.venv/bin/python -m pytest \
  tests/test_phase_2_evidence_snapshot.py \
  tests/test_phase_2_evidence_snapshot_scope.py -q
.venv/bin/python -m pytest -q
git diff --check
```
