# Research-result evaluation and calibration diagnostics

## Delivered, not inferred model performance

This node connects the existing `MarketTeamResearchRun` (including the
`market_run` inside a successful `CrossSourceResearchRun`) to explicit confirmed
binary outcomes. It scores **canonical P(YES)**, not selected-side probability
and not the model's separate confidence field. It does not fit a calibrator,
rewrite forecasts, promote a report, call a model, or run a trading strategy.

The existing `forecast_calibration`, `team_forecast_calibration`, and
`team_research_calibration_snapshot` modules target different legacy observation
or DB-row contracts. They remain unchanged. In particular, the legacy outcome
tracker's per-trade-leg accounting is not changed into per-event accounting.
This new boundary scores raw research attempts without making approved
`TeamForecastPacket` or DB rows merely to reuse a legacy approval-shaped API.

Files:

- `research_probability_scores.py`: Decimal binary scores and reliability bins.
- `team_research_evaluation.py`: content-bound records, confirmed outcomes,
  first-attempt selection, cohort diagnostics, and text-free report export.
- `scripts/run_research_evaluation_demo.py`: a synthetic, executable example.

## Inputs and clocks

`ResearchEvaluationRecord` wraps an existing market research run, a unique
`record_id`, a caller-supplied `model_id`, `protocol_version`, and `recorded_at`.
Both successful and unsuccessful market research attempts can be recorded. The
full run is copied and revalidated, including question/rules, source receipts,
research scope and flags. Its SHA256 includes those inputs and the research
output, not only the task ID or forecast probability. Only `to_dict()` on the
evaluation report is the intended public diagnostic export; do not serialize
records with `asdict()` into a log, as they retain input text in memory.

`recorded_at` is when the completed attempt actually became available to the
application. It must not precede the run's `as_of` data cutoff. **Never substitute
`as_of` for the real result-capture time** to make a slow or retrospective model
run appear predictive. Model/protocol identities are application assertions;
they are not present in the existing provider-neutral result. Supply the actual
model/version and a versioned research protocol (prompts, source policy, tools,
limits and forecast horizon); do not mix incompatible protocols under one ID.

`ResearchEvaluationOutcome` requires an exact `actual_yes` boolean, the matching
condition and market slug, a source reference and raw source SHA256, plus:

- `forecast_cutoff_at`: the predeclared last eligible prediction time, no later
  than the earliest time the outcome could be known. Use an earlier information
  cutoff when appropriate, not simply a later administrative settlement time.
- `resolved_at`: confirmed resolution time.
- `recorded_at`: when that confirmation was actually captured by the application.

The timestamps must satisfy `forecast_cutoff_at <= resolved_at <= recorded_at`.
Scored forecast records must be **strictly before** `forecast_cutoff_at`.
Outcome capture must be at or before the report's `generated_at`. A known later
resolution may be supplied for replay, but remains unavailable at an earlier
report time. A forecast captured after `generated_at` is excluded from that
report's visible cohort counts.

This is a binary confirmed-outcome boundary, not a new resolution oracle.
Pending, disputed, ambiguous or void outcomes must not be mapped to `False`.
Without a confirmed binary record, a completed prediction stays unscored with
`outcome_pending` (meaning no admissible binary outcome is available here).
Coinbase/Kraken prices, a closed-market flag, a high/low market price, and a model
opinion must not be used as proof of actual settlement. There is no automatic
Gamma-outcome parser or database-readback adapter in this node.

Hashes bind supplied content, **not authenticity, honest capture times, correct
settlement semantics, historical data availability, or an unchanged provider**.
The caller must retain authorized capture provenance. No data is written here;
any future durable capture integration must use local Supabase/Postgres only.

## Selection and denominator policy

The unit of scoring is one condition per `(team_id, model_id, protocol_version)`.
Within that cohort and condition, choose the **first recorded attempt visible
at generated_at**, before checking success status, probability, or outcome.
Later attempts remain in decision receipts as `later_attempt`; they never count
as additional events or replace a worse/failed first attempt. This deliberately
measures first-attempt performance, not a last-before-close trading strategy.

All supplied records have exactly one reason:
`scored`, `not_yet_recorded`, `later_attempt`, `intake_blocked`, `research_blocked`,
`research_failed`, `outcome_pending`, or `not_pre_outcome`.

Duplicate record IDs, recaptures of the same task within a cohort, duplicate or
conflicting resolutions, condition/slug conflicts, and same-time attempts that
make first selection ambiguous are rejected. Selection is independent of input
order. Outcomes with no visible research record are counted as orphan outcomes.

Each cohort shows visible attempts and selected conditions, including pending,
failed/blocked and late counts. In each cohort:

`selected_count = scored_count + outcome_pending_count + failed_or_blocked_count + late_count`.

Scores describe only the scored subset. Failures are not fabricated as p=0.5
or silently replaced by successful retries. Including the counts makes that
coverage limit visible. **The evaluator cannot discover omitted attempts or
markets**: an application can still bias the supplied dataset by leaving them
out. Pre-register the universe, capture all attempts, and keep holdout outcomes
out of model context. Do not compare cohorts as a leaderboard unless they share
an appropriate common event universe, horizon and selection protocol.

There is deliberately no pooled score across cohorts. Multiple teams predicting
the same condition do not turn it into several independent events. Distinct
conditions can still be correlated; no independence or significance is claimed.

## Metrics and numerical conventions

Inputs are exact finite Decimals in [0,1], at most 18 coefficient digits and at
most 12 decimal places; invalid values are rejected, never clipped. Output
metrics use a private 64-digit Decimal context and half-even rounding to 12
places, independent of the caller's Decimal precision, rounding mode or traps.
No NumPy/scikit-learn or other dependency is introduced.

For the n scored outcomes, let `p` be P(YES) and `y` be 1 for YES, 0 for NO:

- **Mean Brier score:** `mean((p-y)^2)` on the binary [0,1] scale. Lower is better.
- **Neutral baseline:** p=0.5 on exactly the same scored events gives 0.25.
  `brier_skill_vs_half = 1 - mean_brier/0.25`; this is NOT skill against executable
  market prices, empirical climatology or a profitable trading benchmark.
- **Mean log loss:** natural logarithm, `mean(-ln(p))` on YES and
  `mean(-ln(1-p))` on NO. Correct certainty scores zero. Any wrong certainty
  makes the cohort loss infinite; export `mean_log_loss=null`,
  `log_loss_status="infinite"`, and `infinite_log_loss_count>0`. It is not a
  finite-only average and there is no hidden epsilon clipping. Empty data also
  has null loss but `log_loss_status="empty"`.
- **Reliability bins:** equal-width bins, counts 2/5/10/20, default 10;
  lower bound inclusive, upper exclusive, except final bin includes 1.
  Report each bin's count, mean P(YES), observed YES rate and a sparse flag.
  Empty bins have null means, not zero rates.
- **Expected calibration error:** sum over bins of
  `abs(sum(p_in_bin) - yes_count_in_bin) / n`. Compute from unrounded sufficient
  statistics, not from displayed rounded bin means or weights.

Default minimum sample count is 30 and minimum bin count is 5. These are visible,
configurable **engineering warnings**, not sample-size guarantees. Status is
`empty`, `insufficient_sample`, or `descriptive_only`, never validated/approved.
A 70% bin with 7 YES outcomes among 10 reports 70% observed frequency and zero
in-bin gap, but does not prove calibrated generalization. Fixed-bin ECE depends
on binning and sample size. Brier and log loss measure more than calibration;
lower loss alone does not demonstrate better calibration. No confidence
intervals, uncertainty estimates, recalibration fitting or train/holdout split
are implemented. A future fitted calibrator needs a separately versioned,
chronological training/holdout protocol, not in-sample diagnostic success.

## Application use

```python
from polymarket_alpha_lab.team_research_evaluation import (
    ResearchEvaluationRecord, ResearchEvaluationOutcome, ResearchEvaluationReport,
)

# market_run comes from the existing market pipeline, or cross_source_run.market_run.
record = ResearchEvaluationRecord(
    record_id=record_id, model_id=model_version, protocol_version=protocol_version,
    recorded_at=actual_result_capture_time, run=market_run,
)
# confirmed_outcomes is a tuple of operator/application-verified
# ResearchEvaluationOutcome records, never inferred here from spot candles.
report = ResearchEvaluationReport(
    records=all_recorded_attempts, outcomes=confirmed_outcomes,
    generated_at=evaluation_time,
)
print(report.to_dict())  # strings for Decimal, explicit nulls, no source/model text
```

The existing cross-source run may be blocked before market intake; its
`market_run` is then None and is not accepted as an evaluation record. Such
pre-market data-collection failures remain outside this node's attempt count
and must be accounted for by the application's complete-universe collector.
This report must not be advertised as full operational coverage of all requests.

## Reproduction and delivery evidence

```bash
python scripts/run_research_evaluation_demo.py
python -m pytest -q tests/test_research_probability_scores.py tests/test_team_research_evaluation.py
python scripts/verify_local.py --full
```

The demo runs the real market intake and Agent loop with a **scripted model**
and synthetic evidence for ten distinct events, all assigned p=0.7, with seven
constructed YES outcomes. Output explicitly declares synthetic_demo=true,
public_network_called=false and live_model_called=false. Expected Brier is
0.21; the populated bin has mean/observed rate 0.7; sample status remains
insufficient_sample. These are fixture identities, not measured model quality.

The report recomputes its derived metrics when exporting and omits evidence
text, prompts and model summaries. Input objects are copied/revalidated.
All report surfaces preserve paper_only/report_only/readonly; there is no
model invocation in the evaluator, credential access, file journal, database,
network request, automatic publication, or strategy-cycle wiring.

The owner authorized self-review, commit and merge without external-review or
CodeGraph gates. Actual focused/full counts and exact tested/merged revisions
belong in the PR, not a speculative PASS in this document.

Primary metric references (definitions only, no runtime dependency):
https://scikit-learn.org/1.8/modules/calibration.html
https://scikit-learn.org/1.6/modules/generated/sklearn.metrics.log_loss.html
Our un-clipped boundary policy deliberately differs from numerical clipping
commonly used by library log-loss implementations.
