# M6 Stage Plan: Settlement And Research Value

Date: 2026-09-06
Stage: M6 of the [Project Delivery Plan](../../roadmap/2026-09-05-project-delivery-plan.md)
Status: plan review completed; findings dispositioned (see the final section)
Depends on: M5 Wave 1 (accepted; commit `ba424e73`)

## Parent-Plan Traceability

This stage delivers the delivery plan's M6 exit: a repeatable
settled-outcome evaluation that joins forecasts to resolved outcomes
with explicit cutoffs, computes Brier score, clipped log loss,
calibration buckets, coverage, and a market-implied baseline
comparison, refuses small-sample conclusions, and documents
limitations. Memory-as-context measurement and cost-adjusted paper
performance rollup remain recorded as future work inside the report's
limitations rather than being fabricated from absent settled samples.

## Current-Code Facts

- Forecast persistence (`team_forecast_*`) and outcome-tracking surfaces
  exist, but no joined settled-outcome evaluation report exists.
- Real settled samples do not exist yet (cycles began 2026-09-05); any
  evaluation today runs on recorded or synthetic samples and must say
  so. This is why the deliverable is the evaluator plus protocol, not a
  claimed result.

## Design Decisions

1. The evaluator is pure and boundary-checked. `SettledForecastSample`
   carries condition/team ids, canonical Decimal P(YES) forecast,
   market-implied P(YES), actual outcome (`yes`/`no`), forecast
   generated-at, and settled-at. Samples failing invariants —
   probability bounds, unknown outcome labels, `settled_at <
   generated_at`, or forecasts postdating the evaluation cutoff — are
   excluded with explicit reason codes, never silently dropped.
2. Metrics are hand-verifiable: Brier score as mean squared error
   against the 0/1 actual; log loss with forecasts clipped to
   [0.001, 0.999] before -log(p) (epsilon 0.001, config-declared, so
   p=0/1 cannot produce infinite loss); calibration in ten equal-width
   buckets [0.0,0.1) ... [0.9,1.0] with per-bucket counts and mean
   forecast, zero-count buckets rendered as "empty"; coverage as settled
   / (settled + pending); market-implied baseline Brier computed on the
   identical sample set so the comparison is paired.
3. Thresholds and the verdict rule are declared before evaluation, in
   config: `min_samples_indicative` (30) and `min_samples_comparative`
   (100). Verdict logic: N < 30 -> `insufficient_sample`; N >= 30 with
   team Brier >= market Brier -> `no_consistent_edge`; 30 <= N < 100
   with team Brier < market Brier -> `indicative_edge`; N >= 100 with
   team Brier < market Brier -> `comparative_edge`. The report states
   the counts and the rule; it never extrapolates.
4. Time-ordering is respected: an `as_of_evaluation_cutoff` config
   input excludes any sample whose forecast was generated after the
   cutoff (look-ahead rejection with reasons); the report records the
   cutoff and the excluded count.
5. The report is a frozen dataclass plus a deterministic text renderer;
   it includes sample counts, per-team counts (domain concentration),
   exclusions with reasons, uncertainty framing (binomial standard
   error for the Brier difference is out of scope at small N and is
   stated as a limitation instead), drawdown/capital-lockup fields as
   explicit not-yet-measured limitations, and a verdict enum
   (`insufficient_sample`, `no_consistent_edge`, `indicative_edge`,
   `comparative_edge`).
6. The CLI command `settlement-evaluation --samples <json-file>` runs
   the pure evaluator over an operator-supplied export (the future DB
   join produces this file); no new durable persistence is introduced.
   The JSON schema is documented in the report module docstring. The
   cost-adjusted paper-results arm and the memory-as-context benefit
   arm activate only once settled samples exist (trigger: settled
   N >= 30 adds the cost-adjustment arm; memory benefit is measured when
   memory-gated handoffs have settled outcomes) — the parent plan's M6
   section is amended accordingly. Forecast revision history is not yet
   tracked in persistence; the evaluator uses the first-recorded
   generated_at and documents mid-flight revision blindness as a known
   limitation until persistence carries revision history.

## Work Items

1. `src/polymarket_alpha_lab/settlement_evaluation.py` (new): sample
   contract, config, evaluator, report, renderer.
2. CLI: the single `settlement-evaluation` command (inventory 79 -> 80,
   documented decision).
3. Tests `tests/test_settlement_evaluation.py`: metric correctness on
   hand-computed cases; paired baseline comparison; clipping; look-ahead
   and invariant exclusions; calibration buckets; insufficient-sample
   verdicts at N below thresholds; determinism; renderer redaction
   (no payloads).
4. Protocol note appended to the domain matrix: how samples will be
   exported going forward (forecast rows joined to outcomes), and that
   the first real evaluation is expected after markets settle.

## Verification

Focused suite; full Python 3.11 regression; compile; `git diff --check`;
credential scan; inventory diff (+1 command, documented).

## Acceptance Criteria (mirrors delivery-plan M6 exit)

1. A repeatable settled-outcome report exists and runs from a recorded
   sample file with explicit cutoffs.
2. Brier, clipped log loss, calibration buckets, coverage, and the
   paired market-implied baseline are computed and correct.
3. Small samples yield `insufficient_sample` with counts; no
   profitability claim is possible from the report.
4. Look-ahead and invariant violations are excluded with reasons.
5. Limitations (uncertainty intervals, drawdown, capital lockup, fee
   sensitivity, memory benefit) are stated as not-yet-measured rather
   than fabricated.
6. No new durable persistence; no execution surfaces.

## Rollback

Revert the four work items; no schema or data dependency.

## Plan Review Response (2026-09-06)

Claude Code reviewed this plan read-only (`claude-opus-5`, effort `max`)
and returned REQUEST_CHANGES: two MAJOR, two MODERATE, two MINOR. All
six findings are accepted: the parent M6 section is amended to make the
cost-adjusted and memory-benefit arms explicitly post-settlement with
concrete activation triggers (plus the trigger commitment here); the
verdict rule is spelled out; log-loss clipping semantics fixed at
[0.001, 0.999]; revision-history blindness documented as a limitation;
ten calibration buckets with empty rendering; the CLI end-to-end test
added.

## Recorded Verification (2026-09-06)

- Focused: tests/test_settlement_evaluation.py — 8 passed covering
  hand-computed Brier/log-loss with paired baseline, clipping cap
  (-ln(0.001)), all four verdict branches, look-ahead and
  contract-violation exclusions with reasons, ten calibration buckets
  with empty rendering, team concentration and pending counts,
  limitation text, CLI end-to-end from a JSON fixture, determinism.
- Inventory regenerated: 80 commands (+settlement-evaluation,
  documented).
- Full Python 3.11 regression: 34284 passed, 8 skipped in 739.12 s.
- Compile checks, `git diff --check`, credential scan: clean.
- Honest state: no real settled samples exist yet (cycles began
  2026-09-05); any run today necessarily reports insufficient_sample.

## Hard-Review Cycle (2026-09-06)

First hard review returned FAIL with two findings, both fixed:

1. MAJOR missing coverage ratio: `SettlementEvaluationReport` now carries
   `coverage` computed as settled / (settled + pending) when the
   denominator is positive, rendered as `coverage_settled_ratio`, with a
   test asserting Decimal(5)/Decimal(9) for the mixed fixture.
2. MODERATE terminology: the limitation now reads "cost-adjusted paper
   results (fee/slippage/fill sensitivity) arm", matching the delivery
   plan wording.

Focused suite re-verified (8 passed); full regression re-run after the
fixes; hard review re-run.
