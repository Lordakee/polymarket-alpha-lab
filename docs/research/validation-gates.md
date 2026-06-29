# Validation Gates

## Purpose

Define the evidence required before a Polymarket strategy can move from research to paper trading, from paper trading to human-approved proposals, and from proposals to limited live execution.

These gates are deliberately conservative. They are starting thresholds for engineering discipline, not proof of guaranteed return.

## Phase 1 Operational Audit Note

The Strategy Risk Audit CLI currently summarizes six Phase 1 paper-readiness checks: `paper_history`, `settlement_evidence`, `forecast_quality`, `cost_discipline`, `nav_drawdown`, and `open_exposure`. The pure Strategy Risk Audit report can append optional `settlement_nav_risk` evidence when the caller supplies an existing settlement/NAV overlay report. The optional source is paper-only/report-only/readonly; it does not add live trading; does not add auth or wallet handling; does not add order submission, cancellation, or replacement; and does not add persistence, DB loaders, env reads, or CLI flags. These checks are an operational evidence subset for paper-only/report-only workflows, not a replacement for the full Gate 0 through Gate 8 promotion framework.

An optional continuous paper-run preflight may pause new paper execution until the local Strategy Risk Audit status is `audit_ready`. If the caller explicitly supplies `--strategy-audit-log` or `strategy_audit_log`, the audit report may also be appended to a local append-only JSONL evidence artifact; otherwise no audit log is written. That pause and optional evidence artifact are not human approval readiness, not a proposal-mode promotion, not ranking, not a recommendation, not a trade instruction, not live execution, and not financial advice.

When a local Strategy Risk Audit JSONL artifact exists, `strategy-audit-history --strategy-audit-log <path>` can summarize append-order audit status counts, latest evidence state, latest failed/incomplete audit-check names, and per-check status counts. This history summary is paper-only/report-only/read-only observability over optional local evidence; it does not replace the Gate 0 through Gate 8 framework, approve strategy changes, rank markets, recommend trades, provide trade instruction, trigger live execution, or provide financial advice.

`strategy-evidence --cycle-log <path> --trade-log <path> --nav-log <path> [--outcome-log <path>] [--strategy-audit-log <path>]` is a separate read-only evidence snapshot over caller-selected local paper logs and existing local report builders. It summarizes performance, NAV risk, cost audit, optional outcomes, and optional Strategy Risk Audit history with local evidence statuses: `no_local_evidence`, `local_evidence_gaps`, `local_risk_flags`, and `local_evidence_observed`. These statuses are descriptive local evidence states only; the command writes no artifacts and does not construct clients, fetch data, authenticate, read accounts, touch wallets or private keys, create or manage orders, interact with live trading surfaces, or change strategy-cycle behavior.

## Gate 0: Data Integrity

A strategy cannot be evaluated until the data layer can prove:

- market, event, and token ids are stable across refreshes
- active, closed, accepting-orders, and resolution states are tracked separately
- best bid, best ask, spread, and order book depth have timestamps
- raw API payloads are archived before normalization
- null, zero, missing, and unknown values remain distinguishable
- score inputs can be reproduced from stored snapshots

Reject the strategy if its edge depends on fields that are missing, stale, or only visible through an unreliable manual browsing path.

## Gate 1: Signal Definition

A strategy must define:

- market universe
- inclusion and exclusion filters
- signal formula
- executable entry price
- expected exit price or exit rule
- maximum executable size
- risk tags
- rejection reasons

Reject the strategy if the signal cannot explain why a candidate was accepted or rejected.

## Gate 2: Historical Or Forward Sample

Default minimum evidence before proposal mode:

- at least 200 candidate observations
- at least 50 simulated trades
- at least 30 resolved or exited trades
- at least 4 weeks of forward collection when the strategy depends on live order book depth
- coverage across multiple market themes unless the strategy is intentionally theme-specific

These thresholds can be raised for sparse, slow-resolving, or high-variance strategies.

Reject the strategy if results come from a tiny sample, one lucky theme, one event cluster, or a period with unusual market conditions.

## Gate 3: Execution-Cost Reality

Paper trading must use:

- bid/ask prices, not midpoint
- order book walk for expected fills
- spread and slippage estimates
- exit valuation at executable bid or ask
- partial-fill handling
- rejected-trade logs

Reject the strategy if profitability disappears after spread, slippage, partial fills, fees, stale data, or exit costs.

## Gate 4: Forecast And Edge Quality

For probability-based strategies, track:

- Brier score
- calibration by probability bucket
- expected calibration error
- forecast error by market class
- edge decay from signal timestamp to fill timestamp

For relative-value or arbitrage-style strategies, track:

- theoretical edge
- executable edge
- fill probability
- residual exposure after partial fill
- time-to-close or time-to-resolution risk

Reject the strategy if the measured edge is mostly model optimism, stale pricing, or midpoint artifact.

## Gate 5: Risk And Drawdown

Before proposal mode, the strategy should satisfy:

- maximum paper drawdown within the configured strategy limit
- no single market dominates returns
- no single theme dominates returns unless the strategy is explicitly theme-scoped
- worst-case loss is explainable from position size and contract payoff
- liquidity-adjusted NAV does not diverge materially from midpoint NAV
- losing streak and drawdown duration are tolerable for the intended capital lockup

Reject the strategy if it can only look attractive by ignoring loss-to-zero, settlement delay, or exit liquidity.

## Gate 6: Human-Approval Readiness

A trade proposal must include:

- market URL and token id
- side and intended order type
- executable price assumption
- maximum size
- cost-adjusted edge
- thesis
- invalidating condition
- resolution rule or rule hash
- risk tags
- exposure after trade
- exit rule
- reason the trade could be wrong

Reject proposals that cannot be reviewed quickly from their own packet.

## Gate 7: Live Pilot Readiness

Before limited live execution, the system must prove:

- paper broker and live broker share the same interface
- order lifecycle states are modeled
- fills, partial fills, cancels, rejects, and expirations are journaled
- local positions reconcile against exchange state
- kill switch cancels open orders and prevents new orders
- stale data prevents order submission
- daily loss and drawdown stops are enforced
- secrets are isolated from research jobs and never logged

Reject live pilot if any reconciliation, kill-switch, or stale-data test fails.

## Gate 8: Live Pilot Promotion

A strategy can move from limited live pilot to strategy-specific automation only if:

- live fill quality is within tolerance versus paper assumptions
- no unresolved position mismatches remain
- realized slippage is within the configured limit
- losses stay inside strategy and portfolio caps
- manual review finds no repeated avoidable false positives
- rollback to proposal-only mode has been tested

Reject promotion if live results diverge from paper results without a clear, fixed cause.

## Automatic Rejection Criteria

Reject or pause a strategy immediately if:

- it relies on midpoint fills
- it cannot explain rejected trades
- it ignores resolution-rule ambiguity
- it requires unavailable historical order book depth
- it has unbounded theme concentration
- it breaches drawdown limits
- it shows calibration drift
- it produces orders during stale data windows
- it has unreconciled position state
- it needs credentials in research code

## Review Cadence

- Daily: data freshness, failed jobs, stale watchlists, rejected-trade counts.
- Weekly: paper PnL, drawdown, calibration, edge decay, liquidity-adjusted NAV.
- Per strategy promotion: full validation packet.
- Per live pilot: order lifecycle audit, reconciliation audit, rollback test.
