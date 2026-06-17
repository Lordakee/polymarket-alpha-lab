# Strategy Audit History Summary v0 Spec

## Goal

Summarize local Strategy Risk Audit JSONL evidence into a paper-only/report-only
history report so continuous paper-run operators can inspect append-order audit
status counts, latest evidence state, and missing evidence patterns over time.

This is Phase 1 paper-only/report-only/read-only local observability over
already-written Strategy Risk Audit reports. It is not an approval workflow,
strategy-promotion path, market ranking, project selection, recommendation,
trade instruction, financial advice, or live execution.

## Scope

Add a focused pure summary module for values already loaded from
`PaperStrategyRiskAuditLog`:

- `PaperStrategyRiskAuditHistoryConfig`
- `PaperStrategyRiskAuditHistoryStatusRow`
- `PaperStrategyRiskAuditHistoryGateStatusSummary`
- `PaperStrategyRiskAuditHistoryReport`
- `build_paper_strategy_risk_audit_history_report(reports, *, config, generated_at)`

Add a local CLI report:

- `strategy-audit-history --strategy-audit-log <path>`

The CLI reads the local Strategy Risk Audit JSONL artifact with
`PaperStrategyRiskAuditLog.read(...)`, builds a history report, and prints a
compact summary.

Default behavior of existing commands is unchanged.

## Boundaries

Allowed:

- Read a caller-selected local Strategy Risk Audit JSONL artifact.
- Build a pure report from already-built `PaperStrategyRiskAuditReport` values.
- Count audit statuses and audit-check statuses.
- Report latest append-order audit status, latest failed audit checks, latest
  incomplete audit checks, and consecutive non-ready status counts.
- Print a local summary.
- Preserve existing command behavior and avoid writing new artifacts.

Forbidden:

- No live trading.
- No account authentication.
- No wallet or private-key handling.
- No account reads.
- No order placement, signing, submission, or cancellation.
- No market ranking, project selection, recommendation, trade instruction, or
  financial advice.
- No public client construction for `strategy-audit-history`.
- No changes to `runner.py`.
- No changes to the pure Strategy Risk Audit math in `strategy_risk_audit.py`.
- No package-root export.
- No default writes and no new strategy behavior.
- No approval workflow, ranking, recommendation, trade instruction, live
  execution, or financial advice.

## Report Semantics

The input order is append-order log order. `latest_*` fields refer to the last
report supplied, not the maximum timestamp after sorting. Duplicate timestamps
are allowed because consecutive paper runs may be close together and because the
append-only artifact is the source of truth.

Report status values:

- `empty_audit_history`: no audit reports were supplied.
- `latest_audit_ready`: the latest supplied audit report status is
  `audit_ready`.
- `latest_insufficient_evidence`: the latest supplied audit report status is
  `insufficient_evidence`.
- `latest_blocked_by_risk`: the latest supplied audit report status is
  `blocked_by_risk`.

These labels describe local evidence state only. They do not approve, rank,
recommend, instruct, or authorize any trade or strategy action.

## CLI Behavior

`strategy-audit-history`:

1. Requires `--strategy-audit-log <path>`.
2. Reads the local Strategy Risk Audit JSONL artifact.
3. Builds a `PaperStrategyRiskAuditHistoryReport`.
4. Prints status counts, latest status, latest failed/incomplete audit-check
   names, and audit-check status summaries.
5. Returns `0` on success and `1` if the local log cannot be read or the report
   cannot be built.
6. Never constructs `PolymarketPublicClient`, calls `client_factory()`, fetches
   market data, authenticates, or handles orders.

## Acceptance Criteria

- The builder validates a list/tuple of real `PaperStrategyRiskAuditReport`
  values and rejects strings, bytes, non-iterables, and mixed types.
- Empty input returns `empty_audit_history`, zero counts, no latest timestamp,
  no latest failed/incomplete audit-check names, and status summaries with zero
  counts.
- Non-empty input preserves append order for first/latest timestamps and latest
  status.
- Status rows cover `audit_ready`, `insufficient_evidence`, and
  `blocked_by_risk` with counts and ratios.
- Audit-check status summaries cover each of the six Strategy Risk Audit checks
  for `pass`, `fail`, and `incomplete`.
- Consecutive latest non-ready counts are computed from the end of the supplied
  sequence.
- Latest failed and incomplete audit-check names are copied from the latest
  audit report.
- `strategy-audit-history --strategy-audit-log <path>` prints the report and
  does not construct a public client.
- README/specs document that the command is a local evidence summary only, not
  approval, recommendation, ranking, trade instruction, financial advice, or live
  execution.
