# Strategy Research

## Conclusion

The first product should not try to guess which event outcome is correct. It should first identify measurable, repeatable, and paper-testable edges.

The most suitable initial edges are:

- market quality filtering
- order book spread and depth diagnostics
- liquidity reward efficiency
- multi-outcome price-sum inconsistencies
- related-market logical constraints
- post-fill adverse drift analysis

Directional prediction, news-lag trading, and event-close convergence can be valuable later, but they have higher execution and model-risk requirements.

## Edge Types

### Mispricing

Compare an independent model probability with executable bid/ask prices. Use this only where the external model is well-specified, timestamped, and historically tested.

Failure modes:

- model predicts real-world intuition instead of market rule text
- model misses information already priced by the market
- backtest uses midpoint while execution requires ask or bid
- sample size is too small

### Information Lag

Detect delays between external event updates and market prices.

Requirements:

- low-latency external data
- order book snapshots
- reliable event timestamps
- strict false-positive handling

This is not a good first system core unless the project has a real information-speed advantage.

### Spread And Market Making

Evaluate whether the market has enough spread, depth, and trade frequency to make passive liquidity provision worth studying.

The diagnostic system should track:

- spread
- depth
- volatility
- fill toxicity
- post-fill price drift
- inventory risk

### Liquidity Rewards

Rewards can become a structured return source only after subtracting inventory risk, adverse selection, and competition.

The project should estimate:

- reward pool and scoring parameters
- expected share of score
- order fill probability
- post-fill loss risk
- capital efficiency versus other markets

### Multi-Outcome Price Sum

For mutually exclusive and complete outcome sets, the cost of buying all YES outcomes should be close to 1 after costs.

Use executable prices and depth:

```text
sum(best_ask_all_outcomes) < 1 - buffer
sum(best_bid_all_outcomes) > 1 + buffer
```

The buffer must cover slippage, partial fills, failed execution, settlement delay, and rule ambiguity.

### Related-Market Constraints

Build a relationship graph between markets:

- mutually exclusive
- collectively exhaustive
- inclusion relationship
- exclusion relationship
- same event, different threshold
- same theme, different date

Scan for price violations using bid/ask and depth, not midpoint.

## Strategy Stability Ranking

Best for phase one:

- market quality scoring
- spread and depth diagnostics
- multi-outcome price-sum scans
- related-market constraint scans
- liquidity reward monitoring

Potential phase two:

- event-close convergence
- external-data mispricing models
- portfolio relative value

Phase three or later:

- high-frequency information lag
- real-time sports trading
- news reaction trading

Avoid as the system core:

- subjective direction-only bets
- low-liquidity long-tail markets
- markets with unclear rules and no external data source

## Validation

Every signal should produce this shape:

```text
market_id
token_id
timestamp
strategy_type
observed_price
executable_price
fair_value_estimate
theoretical_edge
cost_adjusted_edge
confidence
max_executable_size
risk_tags
```

Validation should use:

- historical data where available
- paper trading with bid/ask execution
- order book walk simulation
- rejected-trade logs
- performance by strategy, market class, price bucket, and holding period

If a strategy only works under optimistic midpoint fills, it should be rejected.

