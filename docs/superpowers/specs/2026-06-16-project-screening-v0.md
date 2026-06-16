# Project Screening v0 Design

## Purpose

Build a paper-only, report-only screening layer over already-built Cost-Aware Event Strategy reports. The module turns a supplied batch of cost-aware event reports into a deterministic research queue for human review. It never fetches markets, reads accounts, authenticates, handles wallets, places orders, ranks investments, recommends trades, or provides financial advice.

## Inputs

Project Screening v0 consumes only caller-supplied `PaperCostAwareEventStrategyReport` objects. Each source report already contains the event probability model, executable ask prices, cost assumptions, depth gates, risk gates, and paper-review status.

The screening module does not:

- fetch or refresh Polymarket data;
- query fees, order books, positions, balances, fills, or account history;
- use browser automation or API clients;
- infer probabilities from external sources;
- create capital allocation, position sizing, trade instructions, investment rankings, or recommendations.

## Screening Model

For each source report, Project Screening v0 computes a deterministic research screening score. The score is for queue triage only. It is not expected return, investment quality, or advice.

Candidate side selection for scoring:

- If the source report has `selected_side` equal to `yes` or `no`, use that side result.
- Otherwise, use the valid-depth side with the highest available net edge when one exists.
- If neither side has executable price, ask depth, and net edge, the candidate remains non-evaluable.

Depth validity mirrors Cost-Aware Event Strategy v0:

- executable ask must be present;
- ask depth must be present and positive;
- net edge must be present.

Per-candidate components:

```text
edge_component = best_valid_net_edge * net_edge_weight
confidence_component = confidence * confidence_weight
depth_component = min(valid_ask_size / reference_ask_size, 1) * depth_weight
spread_penalty = spread * spread_penalty_weight
resolution_penalty = resolution_risk * resolution_risk_penalty_weight
cost_penalty = total_cost_per_share * cost_penalty_weight

screening_score =
  edge_component
+ confidence_component
+ depth_component
- spread_penalty
- resolution_penalty
- cost_penalty
```

All numeric values use `Decimal`. Scores are quantized to a fixed quantum for deterministic reports.

## Buckets And Queue Order

The report assigns each candidate to one research bucket:

- `research_ready`: source status is `paper_review_ready`, the candidate has valid depth and net edge, and screening score is at or above `min_screening_score`.
- `watch`: source status is `watch`, or a valid-depth candidate has positive net edge but does not clear `min_screening_score`.
- `defer`: candidate is evaluable but has no positive valid-depth net edge, or source status is `blocked_by_cost` or `no_paper_edge`.
- `blocked`: source status is `blocked_by_inputs` or `blocked_by_risk`, or the source report fails validation.

Queue sequence is deterministic and exists only for research workflow ergonomics:

1. `research_ready`
2. `watch`
3. `defer`
4. `blocked`

Within each bucket, candidates are sequenced by descending screening score, then market slug. This is not an investment ranking and must not be used as a trade recommendation.

## Public API

New module:

```text
src/polymarket_alpha_lab/project_screening.py
```

Exports:

- `PaperProjectScreeningConfig`
- `PaperProjectScreeningCandidate`
- `PaperProjectScreeningGateResult`
- `PaperProjectScreeningQueueItem`
- `PaperProjectScreeningReport`
- `PaperProjectScreeningLog`
- `build_paper_project_screening_report`

The module may import the Cost-Aware Event Strategy report/result dataclasses and otherwise uses only Python standard library modules for dataclasses, datetime, Decimal, JSONL serialization, paths, and typing.

## Validation Rules

- All weights, thresholds, scores, and sizes use `Decimal`.
- `reference_ask_size` must be finite and positive.
- Weights and `min_screening_score` must be finite and nonnegative.
- Candidate source reports must be `PaperCostAwareEventStrategyReport` instances.
- Candidate slugs must be unique within one screening report.
- Strings must be canonical nonblank strings.
- Datetimes normalize to UTC.
- Report objects must keep `paper_only is True` and `report_only is True`.
- JSONL serialization must reject non-finite Decimal values.

## Scope Tests

Scope tests must enforce:

- no live API, SDK, account, wallet, private key, browser, websocket, transport, order, recommendation, ranking, or investment instruction surfaces;
- no imports beyond approved stdlib modules and `polymarket_alpha_lab.cost_aware_event_strategy`;
- exact module exports;
- package-root exports match the new public API;
- README text states paper/report-only boundaries and explicitly denies ranking, recommending, ordering, wallet, auth, and financial-advice behavior.

## Non-Goals

- No live market scanner changes.
- No probability model.
- No external research ingestion.
- No portfolio sizing.
- No backtest engine.
- No automatic investment or order execution.
- No legal, compliance, or geographic analysis.
