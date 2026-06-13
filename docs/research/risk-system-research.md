# Risk System Research

## Conclusion

Binary event contracts require risk controls built around loss-to-zero, correlation clusters, liquidity exits, settlement timing, and model calibration. The project should define stable performance as path quality and controlled drawdown, not guaranteed return.

The first risk MVP should implement:

- pre-trade checks
- position sizing
- liquidity-adjusted NAV
- portfolio risk monitoring
- journal analytics

## Risk Characteristics

### Zero-Payoff Risk

A YES or NO position can go to zero at resolution. Position size must be based on maximum loss, not share count or displayed probability.

```text
max_loss = entry_price * shares
max_profit = (1 - entry_price) * shares
position_risk_pct = max_loss / account_equity
```

### Correlation Risk

Many markets that look separate are economically the same theme. Risk must be aggregated by:

- market
- event group
- theme
- subtheme
- resolution source
- maturity bucket

### Tail Risk

Use discrete scenarios rather than normal-distribution assumptions:

- one market goes to zero
- all positions in one theme lose 50 percent
- all positions in one maturity bucket cannot exit
- bid depth drops 80 percent
- settlement is delayed

### Liquidity Exit Risk

Use exit NAV, not midpoint NAV, for risk:

- `mid_nav` for observation
- `exit_nav` for current executable valuation
- `stress_nav` for conservative valuation

For long positions, exit valuation should be based on bid-side depth.

### Spread And Slippage

Expected value must subtract spread, slippage, and exit costs.

```text
ev_net = model_probability - expected_avg_fill_price - estimated_exit_cost - risk_haircut
```

Order size should be capped by visible depth and maximum book participation.

## Position Sizing

Use the minimum of several caps:

- fixed fraction size
- fractional Kelly size
- market cap remaining
- theme cap remaining
- maturity bucket cap remaining
- liquidity cap

Kelly should be fractional and conservative:

```text
kelly_raw = (p_adjusted - cost_adjusted_price) / (1 - cost_adjusted_price)
kelly_used = max(0, kelly_raw) * kelly_fraction
```

Recommended initial mode:

- base fixed fraction for paper trading
- quarter Kelly as a sizing ceiling
- hard caps by market, theme, and maturity bucket

## Stable Performance Metrics

Primary metrics:

- max drawdown
- drawdown duration
- settled expectancy
- Brier score
- calibration error
- return per capital day
- worst market loss
- worst theme loss
- liquidity-adjusted NAV

Secondary metrics:

- Sharpe
- Sortino
- win rate
- average win/loss

Win rate alone is not meaningful for binary markets because a high-probability contract can have a high win rate and still negative expectancy.

## Paper Trading Journal

Required fields:

- market id and URL
- token id and outcome
- rule text hash
- resolution source
- decision timestamp
- model probability
- bid, ask, midpoint
- expected entry price
- spread and slippage estimate
- cost-adjusted edge
- confidence
- thesis
- invalidating conditions
- account equity
- final size
- sizing limiter
- market/theme/maturity exposure after trade
- simulated fill price from order book walk
- daily exit NAV
- exit reason
- realized PnL
- holding days
- forecast error

No paper trade should enter the journal unless the thesis, invalidating condition, rule text, and execution-cost fields are complete.

## MVP Risk Parameters

```yaml
portfolio:
  max_open_risk_pct: 0.25
  max_drawdown_warning_pct: 0.05
  max_drawdown_hard_pct: 0.10
  min_cash_pct: 0.20
position:
  base_risk_per_trade_pct: 0.005
  max_market_risk_pct: 0.02
  max_theme_risk_pct: 0.06
  max_subtheme_risk_pct: 0.04
  max_maturity_bucket_risk_pct: 0.10
kelly:
  enabled: true
  fraction: 0.25
  max_kelly_position_pct: 0.02
  probability_margin_of_error: 0.03
liquidity:
  max_spread_bps: 500
  max_entry_slippage_bps: 300
  max_exit_slippage_bps: 500
  max_order_book_participation_pct: 0.10
  min_exit_depth_ratio: 2.0
paper_trading:
  require_resolution_rule: true
  require_thesis: true
  require_invalidating_conditions: true
  use_order_book_walk_for_fills: true
  mark_positions_at_exit_price: true
```

