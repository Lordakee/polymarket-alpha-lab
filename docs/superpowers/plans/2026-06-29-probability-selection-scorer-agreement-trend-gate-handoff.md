# Probability Selection Scorer Agreement Trend Gate Handoff

Date: 2026-06-29

## Summary

This node documents the pure reducer callable
`build_probability_selection_scorer_agreement_trend_gate_report` in the
`probability_selection_scorer_agreement_trend_gate` module. The reducer accepts
an already-built `ProbabilitySelectionScorerAgreementTrendReport` and emits a
paper-only/report-only/readonly
`ProbabilitySelectionScorerAgreementTrendGateReport` with a `pass`, `watch`, or
`blocked` gate status.

The gate report is an observability artifact over aggregate probability
selection/scorer agreement trend evidence. It does not build trend inputs,
load reports, run a CLI, persist output, connect to a database, or authorize
any trading behavior.

## Implemented Surface

- Module:
  `src/polymarket_alpha_lab/probability_selection_scorer_agreement_trend_gate.py`
- Public reducer:
  `build_probability_selection_scorer_agreement_trend_gate_report`
- Input type:
  `ProbabilitySelectionScorerAgreementTrendReport`
- Output type:
  `ProbabilitySelectionScorerAgreementTrendGateReport`
- Config type:
  `ProbabilitySelectionScorerAgreementTrendGateConfig`
- Reason-code row type:
  `ProbabilitySelectionScorerAgreementTrendGateReasonCodeCount`

The reducer uses exact type checks for the source report and config, preserves
hard flags (`paper_only=True`, `report_only=True`, `readonly=True`), normalizes
timestamps to UTC, derives `trend_report_age_seconds`, and copies aggregate
source trend fields into the gate report for review.

## Gate Semantics

- `pass`: stable aligned agreement trend evidence with enough source history,
  fresh trend evidence, no repeated source reason-code threshold breach, and no
  latest scorer-gate blocker.
- `blocked`: insufficient agreement-trend history, any latest `gate_blocked`
  agreement status, or repeated latest scorer-gate blockers.
- `watch`: latest non-aligned non-blocking statuses such as low overlap, missing
  inputs, or insufficient identifiers; stale trend evidence; repeated
  watch-level status streaks; or repeated source reason codes, unless a blocking
  condition also applies.

The current default thresholds are:

- `min_source_report_count=3`
- `max_latest_status_streak_for_watch=1`
- `max_latest_status_streak_for_block=2`
- `max_trend_report_age_seconds=86400`
- `max_recurring_reason_code_count=2`

## Safety Boundary

This node is pure Python and report-only. It has:

- no CLI
- no runner
- no loader
- no DB connection
- no environment-variable read
- no Supabase/Postgres access
- no persistence
- no SQLite
- no JSONL durable history
- no Redis
- no Mongo
- no SQLAlchemy
- no hosted DB assumption
- no generic durable store
- no file-backed cache
- no insert, update, delete, DDL, or sink path
- no trend-gate persistence
- no DSN, table, or file inputs
- no live trading
- no auth/session behavior
- no private keys
- no wallets
- no accounts
- no order construction, signing, submission, cancellation, or replacement
- no exchange mutation

The gate report is not permission to trade, financial advice, investment
ranking, order instruction, execution authorization, or an approval workflow.

## Integration Boundary

Do not claim readiness-gate or readiness-digest integration for this node. The
current deliverable is the standalone pure reducer and documentation only.

Future integration, if requested, should be a separate node with explicit scope,
tests, and docs for how this gate report is consumed.

## Documentation Update

`README.md` now documents this reducer after the existing
"Probability Selection Scorer Agreement Trend" section and before "Paper
Autonomous Allocation Proposal". The README wording keeps the reducer separate
from the existing trend CLI and explicitly states the non-trading and
non-approval boundaries.

## Verification

Focused reducer and adjacent agreement-trend checks:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' PYTHONPATH=.:src python3 -m pytest -q \
  tests/test_probability_selection_scorer_agreement_trend.py \
  tests/test_probability_selection_scorer_agreement_trend_scope.py \
  tests/test_cli_probability_selection_scorer_agreement_trend.py \
  tests/test_cli_probability_selection_scorer_agreement_trend_scope.py \
  tests/test_probability_selection_scorer_agreement_trend_gate.py \
  tests/test_probability_selection_scorer_agreement_trend_gate_scope.py
```

Result: `60 passed`.

Full regression:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' PYTHONPATH=.:src python3 -m pytest -q
```

Result: `10242 passed, 1 skipped`.

Static checks:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:src python3 -m compileall -q src tests
git diff --check
```

Both completed cleanly.
