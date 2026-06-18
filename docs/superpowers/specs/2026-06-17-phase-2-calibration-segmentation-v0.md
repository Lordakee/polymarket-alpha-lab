# Phase 2 Calibration Segmentation v0 Spec

## Goal

Add two pure local report modules that turn caller-supplied paper evidence into calibration and segmentation summaries without changing Phase 1 trading, research, screening, or run behavior.

The Phase 2 surface is module-local only. It must not add package-root exports, CLI commands, JSONL readers/writers, live-data wrappers, auth/account/wallet/order surfaces, recommendations, rankings, trade instructions, or financial advice.

## Modules

### `forecast_calibration`

`forecast_calibration` summarizes forecast probability quality from caller-supplied resolved evidence. It consumes `PaperForecastEvidenceObservation` rows and counts only rows with both `predicted_probability` and `actual_outcome_value` as calibration observations.

Required framing:

- Upstream evidence may derive `predicted_probability` from a modeled fair probability, a Polymarket implied probability proxy, or another local research estimate, but this module does not fetch, infer, reconcile, or trade on that source.
- Calibration is resolved-evidence-only: unresolved rows, edge-only rows, and return-only rows do not become calibration observations.
- Calibration outputs are descriptive report metrics only: bucket counts, Brier score, mean absolute error, observed outcome rates, expected calibration error, max bucket error, and status.
- The module must measure calibration before any later phase can move beyond reporting, but its statuses are report states only and are not transition, approval, ranking, recommendation, or trading signals.

### `strategy_segment_summary`

`strategy_segment_summary` groups existing paper-only evidence by stable local strategy and risk-tag segments.

Required framing:

- Segment rows describe where paper evidence is concentrated or weak.
- Segment output is not a ranking, recommendation, trade instruction, later-phase transition decision, or allocation signal.
- Segment rows must surface counts and quality metrics before interpreting performance.
- Segment summaries must keep probability and return observation roles separate. Probability metrics require complete `predicted_probability` plus `actual_outcome_value` evidence; return metrics require `paper_return_ratio` evidence.
- Return-only segments are descriptive return evidence, not calibration evidence.
- Segment summaries must keep thin probability samples visibly incomplete even when return evidence exists.

## Phase 2 Boundary

Phase 2 remains paper-only/report-only/read-only over caller-supplied typed evidence. It is not live trading.

Boundary shorthand: no live trading, no auth, no wallet/private key, no order placement/signing/submission/cancellation, no account reads, no recommendations/ranking/trade instruction/financial advice.

The modules must not:

- perform live trading
- authenticate
- read wallets
- read or handle private keys
- place, sign, submit, or cancel orders
- read accounts, positions, balances, fills, or exchange user state
- construct exchange trading clients
- rank investments
- recommend trades
- provide trade instructions
- provide financial advice
- alter strategy-cycle behavior
- tune screening weights
- size positions
- move a strategy beyond reporting
- add CLI commands
- add package-root exports
- read or write JSONL logs
- add file loaders, replay helpers, or from-file APIs

The report dataclasses must hard-enforce `paper_only is True`, `report_only is True`, and `readonly is True` where those flags are present.

## Probability And Risk Requirements

Phase 2 must preserve the upstream distinction between:

- `implied_probability`: the market's executable or displayed Polymarket probability proxy, derived from bid/ask/price context.
- `modeled_fair_probability`: the local forecast estimate being evaluated.

The current module-local APIs do not expose those names directly. They consume already-built paper evidence where `predicted_probability` is the local probability value to be evaluated and `actual_outcome_value` is the resolved outcome. Documentation and callers must not collapse price-derived probability, modeled fair probability, executable edge, and realized return into one role.

Before any later phase can move beyond reporting, evidence must separately measure:

- explicit and implicit cost
- slippage
- available liquidity and executable size
- settlement lag and unresolved-outcome risk
- market-rule ambiguity and rule-change risk
- calibration quality by segment
- sample size sufficiency by segment

The Phase 2 reports may say a sample is sufficient for descriptive reporting. They must not say a market, strategy, segment, or model should be traded.

## Inputs

Expected inputs are caller-supplied typed evidence such as:

- `PaperForecastEvidenceObservation` values with complete probability evidence: `predicted_probability` and `actual_outcome_value`
- `PaperForecastEvidenceObservation` values with complete return evidence: `paper_return_ratio` plus the existing executable-edge role fields required by that type
- configuration dataclasses supplied directly to each module-local builder

Inputs are caller-supplied in memory. The Phase 2 modules do not read files, write logs, fetch, authenticate, mutate external state, or provide CLI wrappers.

## Tests

Targeted verification for the implementation should include:

```bash
.venv/bin/python -m pytest \
  tests/test_forecast_calibration.py \
  tests/test_forecast_calibration_scope.py \
  tests/test_strategy_segment_summary.py \
  tests/test_strategy_segment_summary_scope.py -q
.venv/bin/python -m pytest -q
```

Scope tests must reject live/auth/wallet/private-key/account/order/recommendation/ranking/trade-instruction/financial-advice surfaces and should prove both modules remain pure local report modules.
