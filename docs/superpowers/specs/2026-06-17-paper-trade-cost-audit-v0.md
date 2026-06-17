# Paper Trade Cost Audit v0 Spec

## Goal

Build a paper-only/report-only cost audit over existing `PaperTradeRecord` journal rows so the project can measure whether simulated Polymarket probability trades retain enough edge after execution friction.

## Phase 1 Boundary

- Input is a typed tuple of `PaperTradeRecord` values or a local paper trade JSONL path read by `PaperTradeJournal.read`.
- Output is an in-memory report and a CLI text summary.
- The module must not fetch markets.
- The module must not construct API clients.
- The module must not authenticate.
- The module must not read wallets.
- The module must not read private keys.
- The module must not place/sign/submit/cancel orders.
- The module must not rank investments.
- The module must not recommend trades.
- The module must not provide trade instructions.
- The module must not provide financial advice.
- The report must be `paper_only is True` and `report_only is True`.
- The module must not change strategy-cycle screening, paper execution, order sizing, or portfolio NAV behavior.

## Required Report Metrics

- `trade_count`
- `total_filled_size`
- `total_requested_size`
- `fill_rate`
- `mean_theoretical_edge`
- `mean_cost_adjusted_edge`
- `mean_edge_cost_drag` as an unweighted per-share mean
- `total_edge_cost_drag` as realized cost drag weighted by filled size
- `mean_research_slippage`
- `mean_fill_slippage`
- `partial_fill_count`
- `negative_cost_adjusted_edge_count`
- `largest_single_trade_cost_drag` as the largest filled-size-weighted single-trade drag

Ratios should be `Decimal` values quantized to `0.000001` where appropriate. Per-share edge values should be `Decimal` values quantized to `0.000001`. Empty input yields zero counts and `None` aggregate ratios/means.

## CLI

Add:

```bash
polymarket-alpha-lab cost-audit --trade-log <path>
```

The command reads the local paper trade journal only and prints one compact report. It must not construct a Polymarket client.

## Tests

- Core report tests for empty inputs, aggregate metrics, invalid inputs, frozen flags, and no-float Decimal behavior.
- CLI tests proving local journal read and no client construction.
- Public export tests in `tests/test_init.py`.
- A dedicated scope test proving the module imports only stdlib plus `polymarket_alpha_lab.journal`, exports only the paper report API, and defines no live/advice/order/auth/wallet surface names.
