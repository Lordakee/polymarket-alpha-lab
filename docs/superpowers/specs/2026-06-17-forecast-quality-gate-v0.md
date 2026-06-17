# Forecast Quality Gate v0 Design

## Purpose

Add a paper-only/report-only probability calibration gate to Strategy Risk Audit v0 so resolved outcome evidence is not treated as mature solely because enough markets have settled. The gate consumes the existing `OutcomeTrackingReport.forecast_evidence_report` value and summarizes whether forecast probability quality is ready, blocked, or incomplete.

## Inputs

Forecast Quality Gate v0 is part of `Strategy Risk Audit v0` and consumes only caller-supplied typed reports already passed to `build_paper_strategy_risk_audit_report`:

- `PerformanceSummary`
- `PaperNavRiskMetricsReport`
- optional `OutcomeTrackingReport`

The gate reads `OutcomeTrackingReport.forecast_evidence_report` when present. It uses the nested `probability_quality` gate and `probability_observation_count`; it does not require executable-edge evidence because current outcome tracking emits probability-only observations. It does not import the forecast evidence module directly, read logs, write logs, fetch market data, authenticate, use API clients, handle wallets or keys, submit orders, rank markets, recommend trades, or change strategy-cycle behavior.

## Gate Semantics

Add one gate after `settlement_evidence` and before NAV risk gates:

- `forecast_quality`: incomplete when `OutcomeTrackingReport` or its nested forecast evidence report is absent.
- `forecast_quality`: incomplete when nested `probability_observation_count` is below `PaperStrategyRiskAuditConfig.min_forecast_probability_observation_count`.
- `forecast_quality`: pass when nested `probability_quality` gate status is `pass` and the audit-level probability sample floor is met.
- `forecast_quality`: fail when nested `probability_quality` gate status is `fail`.
- `forecast_quality`: incomplete when nested `probability_quality` gate status is `incomplete`.

The gate's observed value should include the nested forecast evidence status plus core calibration metrics:

```text
forecast_probability_quality_status=pass; mean_probability_loss=0.1600; worst_bucket_error=0.4000; probability_observation_count=12
```

The report status remains:

- `audit_ready` only when all gates pass.
- `blocked_by_risk` when any gate fails.
- `insufficient_evidence` when any gate is incomplete and no gate fails.

## Public API

No new public classes or builders. Existing public API remains:

- `PaperStrategyRiskAuditConfig`
- `PaperStrategyRiskAuditGateResult`
- `PaperStrategyRiskAuditReport`
- `build_paper_strategy_risk_audit_report`

The existing `PaperStrategyRiskAuditReport.gate_count` increases from 4 to 5.

## Non-Goals

- No direct import of `polymarket_alpha_lab.forecast_evidence` in `strategy_risk_audit.py`.
- No full forecast evidence readiness requirement; v0 is a probability calibration gate because outcome tracking currently emits probability-only observations.
- No file readers or log writers.
- No fetch, live trading, auth, wallets, private keys, account reads, or orders.
- No recommendation, ranking, trade instruction, or financial advice.
- No cross-report coherence or freshness inference; callers must supply reports from a compatible paper-trading state and time window.
- No strategy weight tuning, market scoring, project selection, or position sizing.

The standalone boundary bullets below are intentionally explicit so static documentation checks can detect accidental scope drift.

- No auth.
- No wallets.
- No orders.
- No file readers.
- No fetch.
- No recommendation.
- No ranking.
- No financial advice.
