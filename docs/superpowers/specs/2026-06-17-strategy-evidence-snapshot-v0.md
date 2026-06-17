# Strategy Evidence Snapshot v0 Spec

## Goal

Build a paper-only/report-only/read-only Strategy Evidence Snapshot over already
available local paper artifacts so Phase 1 operators can inspect whether the
current strategy evidence set is present, thin, risk-flagged, or missing key
inputs without changing any strategy behavior.

This is local observability only. It is not an approval workflow, market ranking,
project selection, recommendation, trade instruction, financial advice, strategy
promotion, or live-execution signal.

## Scope

Add a pure module:

- `PaperStrategyEvidenceSnapshotConfig`
- `PaperStrategyEvidenceSnapshotReport`
- `build_paper_strategy_evidence_snapshot_report(...)`

The builder consumes already-built typed reports:

- `PerformanceSummary`
- `PaperNavRiskMetricsReport`
- `PaperTradeCostAuditReport`
- optional `OutcomeTrackingReport`
- optional `PaperStrategyRiskAuditHistoryReport`

Add a local CLI report:

- `strategy-evidence --cycle-log <path> --trade-log <path> --nav-log <path> [--outcome-log <path>] [--strategy-audit-log <path>]`

The CLI reads existing local logs, builds the existing local reports, builds the
evidence snapshot, and prints a compact summary.

Default behavior of existing commands is unchanged.

## Boundaries

Allowed:

- Read caller-selected local paper JSONL artifacts.
- Build existing local typed reports from those logs.
- Build one pure evidence snapshot from typed report inputs.
- Print descriptive counts, latest local evidence status, and evidence-gap names.

Forbidden:

- No live trading.
- No account authentication.
- No wallet or private-key handling.
- No account reads.
- No order placement, signing, submission, or cancellation.
- No market ranking, project selection, recommendation, trade instruction, or
  financial advice.
- No public client construction for `strategy-evidence`.
- No writes, appends, rewrites, deletions, or artifact repair.
- No changes to `runner.py`.
- No changes to `strategy_cycle.py` behavior.
- No changes to Strategy Risk Audit math in `strategy_risk_audit.py`.
- No package-root export.
- No screening weight, forecast prompt/provider, paper-execution trigger, or
  sizing change.

## Report Semantics

Snapshot status values describe local evidence state only:

- `no_local_evidence`: cycles, paper trades, NAV snapshots, outcomes, and audit
  history are all absent.
- `local_evidence_gaps`: one or more required local evidence families are absent
  or thin, and no risk flag has precedence.
- `local_risk_flags`: local evidence exists and at least one descriptive risk
  flag is present.
- `local_evidence_observed`: local evidence families are present and no
  configured descriptive risk flag is present.

Evidence-gap names are deterministic strings such as `missing_cycles`,
`missing_paper_trades`, `missing_nav_snapshots`, `missing_outcome_evidence`,
`missing_strategy_audit_history`, `latest_strategy_audit_not_ready`,
`negative_cost_adjusted_edges`, and `unexecutable_open_positions`.

These values do not authorize action. They are only a compact summary of local
paper evidence.

## CLI Behavior

`strategy-evidence`:

1. Requires `--cycle-log`, `--trade-log`, and `--nav-log`.
2. Optionally reads `--outcome-log` and `--strategy-audit-log`.
3. Builds existing `PerformanceSummary`, `PaperNavRiskMetricsReport`,
   `PaperTradeCostAuditReport`, optional latest `OutcomeTrackingReport`, and
   optional `PaperStrategyRiskAuditHistoryReport`.
4. Builds and prints `PaperStrategyEvidenceSnapshotReport`.
5. Returns `0` on success and `1` if local logs cannot be read or the report
   cannot be built.
6. Never constructs `PolymarketPublicClient`, calls `client_factory()`, fetches
   market data, authenticates, handles wallets, or handles orders.

## Acceptance Criteria

- The pure builder validates exact typed report inputs and rejects strings,
  mappings, arbitrary objects, and wrong report types.
- The pure builder uses `Decimal` values only for numeric ratios and preserves
  `paper_only is True` and `report_only is True`.
- Empty/thin local inputs produce deterministic evidence-gap names.
- Optional outcome and audit-history inputs are handled without file access in
  the pure module.
- `strategy-evidence` reads local logs only and does not construct a public
  client on success, runner-injected success, runner failure, or missing-log
  failure.
- `strategy-evidence` does not write or mutate any supplied log.
- Existing `history`, `nav-risk`, `cost-audit`, `strategy-audit`,
  `strategy-audit-history`, `run`, and `strategy-cycle` behavior is unchanged.
- README/specs document the command as local evidence observability only, not
  approval, recommendation, ranking, trade instruction, financial advice, or live
  execution.
