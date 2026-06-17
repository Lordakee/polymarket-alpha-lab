# Strategy Risk Audit Cost Gate v0 Spec

## Goal

Extend Strategy Risk Audit v0 with a paper-only/report-only cost discipline gate over an optional `PaperTradeCostAuditReport`.

## Phase 1 Boundary

- `strategy_risk_audit.py` must remain pure report math over caller-supplied typed reports and preserve `paper_only` / `report_only` behavior.
- It may import `PaperTradeCostAuditReport`, but it must not import `PaperTradeJournal`, read files, fetch data, construct clients, authenticate, touch wallets/private keys, place/sign/submit/cancel orders, rank investments, recommend trades, provide trade instructions, or provide financial advice.
- Boundary summary: no file readers or log writers, no fetch, no auth, no wallets, no orders, no ranking, no recommendations, no trade instructions, and no financial advice.
- CLI orchestration may read the existing local paper trade journal with `PaperTradeJournal.read(...)` and build `PaperTradeCostAuditReport`; that command must not construct a Polymarket client.

## API Change

`build_paper_strategy_risk_audit_report(...)` adds:

```python
cost_audit_report: PaperTradeCostAuditReport | None
```

The report remains `paper_only is True` and `report_only is True`.

## Gate

Add a sixth gate named `cost_discipline`.

- If `cost_audit_report is None`, status is `incomplete`.
- If `cost_audit_report.trade_count` is below `PaperStrategyRiskAuditConfig.min_cost_audit_trade_count`, status is `incomplete`.
- If `cost_audit_report.mean_edge_cost_drag` is `None`, status is `incomplete`.
- If `cost_audit_report.mean_edge_cost_drag > PaperStrategyRiskAuditConfig.max_mean_edge_cost_drag`, status is `fail`.
- If `cost_audit_report.negative_cost_adjusted_edge_count > PaperStrategyRiskAuditConfig.max_negative_cost_adjusted_edge_count`, status is `fail`.
- Otherwise status is `pass`.

## Config Defaults

- `min_cost_audit_trade_count = 20`
- `max_mean_edge_cost_drag = Decimal("0.050000")`
- `max_negative_cost_adjusted_edge_count = 0`

These defaults keep the gate conservative while still report-only.

## CLI

`polymarket-alpha-lab strategy-audit --cycle-log <path> --trade-log <path> --nav-log <path> [--outcome-log <path>]` should build `PaperTradeCostAuditReport` from the same local `--trade-log` path and pass it into the audit. It must still avoid `client_factory()`.
