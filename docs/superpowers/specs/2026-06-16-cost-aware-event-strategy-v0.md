# Cost-Aware Event Strategy v0 Design

## Purpose

Build the first strategy-layer primitive for Polymarket event contracts: a deterministic, cost-aware evaluator that compares supplied fair event probability against executable YES and NO prices. The module is paper-only and report-only. It produces a structured research report for later review; it never places orders, signs messages, authenticates, reads account state, or connects to live Polymarket clients.

## Polymarket Event Model

Polymarket markets are event outcome-token markets, not ordinary price assets. For a binary market:

- One YES token pays 1 dollar-equivalent pUSD if the event resolves YES and 0 otherwise.
- One NO token pays 1 dollar-equivalent pUSD if the event resolves NO and 0 otherwise.
- Buy-side research must use executable ask prices, not midpoint, last price, displayed probability, or chart price.
- The fair value of YES is the supplied fair probability of YES.
- The fair value of NO is `1 - fair_probability_yes`.
- Gross YES edge per share is `fair_probability_yes - yes_ask`.
- Gross NO edge per share is `(1 - fair_probability_yes) - no_ask`.
- Supplied YES/NO bids are preserved in the report for audit context, but buy-side edge calculations do not use bids.

Current official documentation references:

- Fees: https://docs.polymarket.com/trading/fees
- Prices and order book: https://docs.polymarket.com/concepts/prices-orderbook
- Positions and tokens: https://docs.polymarket.com/concepts/positions-tokens
- pUSD: https://docs.polymarket.com/concepts/pusd
- Gasless transactions: https://docs.polymarket.com/trading/gasless

## Scope Boundaries

Allowed:

- Use caller-supplied market metadata, fair probability, confidence, YES/NO bid/ask, ask depth, spread, resolution risk, and cost assumptions.
- Compute YES and NO gross edge, fee cost, non-fee costs, total cost, and net edge per share.
- Report deterministic gate results, reason codes, selected side, and paper review status.
- Append already-built reports to JSONL when an explicit log object is used.

Not allowed in this v0:

- Fetch market data.
- Query fee parameters from Polymarket.
- Authenticate or use API keys.
- Handle wallets, private keys, signatures, or relayers.
- Place, submit, sign, cancel, or route orders.
- Read account, position, balance, fill, or history state.
- Produce a capital instruction, investment recommendation, or live-execution authorization.
- Perform legal, compliance, geographic, or access analysis.

## Cost Model

The evaluator uses caller-supplied assumptions. It does not assume zero cost when costs are absent.

For a taker-style buy-side evaluation, per-share fee is:

```text
taker_fee_per_share = fee_rate * executable_price * (1 - executable_price)
```

This follows the official fee curve. The report also supports separate per-share assumptions for slippage, funding, finalization, time value, and risk cushion. These are treated as explicit research haircuts. They are not live-chain measurements.

Per-side total cost is:

```text
total_cost_per_share =
  fee_per_share
+ slippage_cost_per_share
+ funding_cost_per_share
+ finalization_cost_per_share
+ time_cost_per_share
+ risk_cost_per_share
```

Net edge is:

```text
net_edge_per_share = gross_edge_per_share - total_cost_per_share
```

## Decision Model

The evaluator produces side results for YES and NO, then selects a side only when all global and side-level gates pass.

Global gates:

- data integrity
- confidence
- spread
- resolution risk

Side/depth and edge gates:

- YES depth
- NO depth
- aggregate `edge_threshold` gate, with per-side edge details and reason codes on the YES and NO side results

Statuses:

- `paper_review_ready`: one side clears all gates and has the highest net edge.
- `watch`: no side clears the minimum edge, but at least one side has complete inputs and positive net edge.
- `blocked_by_inputs`: required inputs are missing or invalid.
- `blocked_by_risk`: confidence, spread, or resolution risk fails.
- `blocked_by_cost`: gross edge exists, but costs remove the edge.
- `no_paper_edge`: no valid-depth side has positive net edge.

The report can set `selected_side` to `yes`, `no`, or `none`. A selected side means only that the supplied inputs create a paper-review candidate under the configured thresholds. It is not a live instruction.

## Public API

New module:

```text
src/polymarket_alpha_lab/cost_aware_event_strategy.py
```

Exports:

- `PaperCostAwareEventCostAssumptions`
- `PaperCostAwareEventMarketSnapshot`
- `PaperCostAwareEventSideResult`
- `PaperCostAwareEventStrategyConfig`
- `PaperCostAwareEventStrategyGateResult`
- `PaperCostAwareEventStrategyLog`
- `PaperCostAwareEventStrategyReport`
- `build_paper_cost_aware_event_strategy_report`

The module imports only standard-library utilities needed for dataclasses, datetime, Decimal, JSONL serialization, paths, and typing.

## Validation Rules

- All probabilities, prices, rates, and ratios use `Decimal`.
- Probability values must be finite and in `[0, 1]`.
- Prices must be finite and in `[0, 1]`.
- Cost assumptions must be finite and nonnegative.
- Confidence must be finite and in `[0, 1]`.
- Spread and resolution risk must be finite and nonnegative.
- Ask size must be finite and positive for a side to be evaluable.
- Strings must be canonical nonblank strings.
- Datetimes normalize to UTC.
- Report objects must keep `paper_only is True` and `report_only is True`.
- JSONL serialization must reject non-finite Decimal values.

## Testing Strategy

Tests must be written before production code. The RED tests cover:

- YES EV from fair YES probability and YES ask.
- NO EV from complement probability and NO ask.
- Taker fee formula and symmetry.
- Cost breakdown arithmetic.
- Selection by net edge, not midpoint or gross edge alone.
- Gate failures for confidence, spread, resolution risk, missing ask, missing ask size, and cost-eroded edge.
- Validation of Decimal/probability/price/string/datetime fields.
- Frozen dataclasses and JSONL append behavior.
- Scope tests for no live API, wallet, account, browser, SDK, or order-placement surfaces.
- Package-root exports and README boundary text.

## Non-Goals

- No market scanner changes.
- No backtest engine.
- No probability model.
- No live data connector.
- No authenticated execution gateway.
- No account reconciliation.
- No live portfolio sizing.
- No compliance/legal/geographic analysis.
