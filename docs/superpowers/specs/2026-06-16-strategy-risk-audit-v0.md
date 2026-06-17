# Strategy Risk Audit v0 Design

## Purpose

Add a paper-only/report-only audit layer that summarizes whether the existing Phase 1 paper evidence is mature enough to discuss later automation work. It does not score markets, select projects, tune strategy weights, size positions, place orders, or provide financial advice.

## Inputs

Strategy Risk Audit v0 consumes caller-supplied typed reports:

- `PerformanceSummary`
- `PaperNavRiskMetricsReport`
- optional `OutcomeTrackingReport`

The module itself does not read files, fetch market data, authenticate, use browser automation, handle wallets or keys, submit orders, rank markets, recommend trades, or change strategy-cycle behavior.

## Gates

The v0 report has four gates:

- `paper_history`: requires enough strategy cycles, paper trades, and NAV snapshots to make the audit meaningful.
- `settlement_evidence`: requires enough resolved paper outcomes from `OutcomeTrackingReport`; absent outcome tracking is incomplete.
- `nav_drawdown`: blocks when NAV drawdown exceeds the configured limit.
- `open_exposure`: includes open paper position count for context and blocks when no-exit-depth marks or exposure concentration exceed configured limits.

The report status is:

- `audit_ready` only when all gates pass.
- `blocked_by_risk` when any gate fails.
- `insufficient_evidence` when any gate is incomplete and no gate fails.

## Public API

New module:

```text
src/polymarket_alpha_lab/strategy_risk_audit.py
```

Exports:

- `PaperStrategyRiskAuditConfig`
- `PaperStrategyRiskAuditGateResult`
- `PaperStrategyRiskAuditReport`
- `build_paper_strategy_risk_audit_report`

## Non-Goals

- No market/project selection.
- No strategy, forecast, screening, sizing, or execution changes.
- No cross-report coherence or freshness inference; callers must supply reports from a compatible paper-trading state and time window.
- No calibration-quality gate; `settlement_evidence` only checks resolved outcome count in v0.
- No fetch, live trading, auth, wallets, private keys, account reads, or orders.

The standalone boundary bullets below are intentionally explicit so static documentation checks can detect accidental scope drift.

- No auth.
- No wallets.
- No orders.
- No file readers or log writers.
- No recommendation, ranking, trade instruction, or financial advice.
- No ranking.
- No financial advice.
