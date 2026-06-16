# Operational Freeze + NAV Risk Metrics v0 Design

## Purpose

Freeze Phase 1 decision logic while markets are still pending settlement, and add a paper-only/report-only NAV risk metrics layer over existing local NAV marks. The metrics are observation tools only; they do not alter forecasts, screening weights, paper execution, position sizing, or run-loop behavior.

## Operational Freeze

Phase 1 decision logic is frozen at local HEAD `4b2cbbbcec2735e926a143463f0c70451cb45119` unless a later node explicitly documents a bug fix. During the freeze:

- do not tune screening weights from pending NAV marks;
- do not change forecast prompts, forecast providers, paper execution triggers, or sizing rules based on unresolved markets;
- do not introduce live trading, auth, wallets, private keys, account reads, order submission, or exchange-state reads;
- allow only read-only observability/reporting additions that help inspect pending paper risk.

## Inputs

NAV Risk Metrics v0 consumes caller-supplied typed values:

- `PaperNavSnapshot` values, normally read by `PaperNavLog.read(...)`.

It does not consume `PaperTradeRecord`, `PaperTradeJournal`, trade logs, trade counts, research records, proposal records, or account records.

The module itself does not fetch data, authenticate, use browser automation, call APIs, handle wallets/keys, place/cancel/sign/submit orders, rank investments, recommend trades, or provide financial advice.

## Metrics

For a NAV time series sorted by `marked_at`, compute:

- snapshot count;
- first and last mark timestamps;
- latest NAV, starting cash, cash balance, total cost basis, and unrealized exit P&L;
- peak and trough exit NAV;
- cumulative return from first NAV to latest NAV;
- maximum drawdown amount and percent;
- worst per-step NAV delta;
- volatility of per-step NAV returns as population standard deviation;
- latest open position count;
- mark-status counts for `fully_executable`, `partially_executable`, and `no_exit_depth`;
- pending notional as latest total cost basis;
- latest exposure concentration by market/condition using mark exit value divided by latest exit NAV.

All math is `Decimal` only and quantized to `Decimal("0.000001")` where ratios or derived scores are emitted.

## Public API

New module:

```text
src/polymarket_alpha_lab/nav_risk_metrics.py
```

Exports:

- `PaperNavRiskMetricsConfig`
- `PaperNavRiskExposureRow`
- `PaperNavRiskMetricsReport`
- `build_paper_nav_risk_metrics_report`

CLI:

- `polymarket-alpha-lab nav-risk --nav-log <path>`

The `nav-risk` command reads typed local NAV logs and prints the read-only NAV risk metrics. It does not trigger market fetches, NAV marking, outcome checks, paper execution, or any strategy cycle.

## Non-Goals

- No strategy changes.
- No screening-weight tuning.
- No LLM prompt changes.
- No paper execution changes.
- No live trading or order placement.
- No outcome resolution or calibration changes.
- No compliance/legal/geographic analysis.
- No `PaperTradeRecord`.
- No `PaperTradeJournal`.
- No trade-log input.
- No paper-trade count metric.
