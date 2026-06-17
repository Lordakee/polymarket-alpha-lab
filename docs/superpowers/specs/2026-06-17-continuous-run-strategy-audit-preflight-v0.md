# Continuous Run Strategy Audit Preflight v0 Spec

## Goal

Add an optional `run --strategy-audit-preflight` gate that reads existing local
paper artifacts, builds the Strategy Risk Audit report, and blocks the
continuous paper run unless the local audit status is `audit_ready`.

This is a Phase 1 paper-only/report-only/read-only safety pause. It is not a
strategy-promotion signal, approval workflow, trade instruction, investment
ranking, recommendation, live-execution signal, or financial advice.

## Scope

The preflight belongs to `cli.py` only. It reuses the existing
`_run_strategy_audit(...)` local-log adapter and must not change
`runner.py` or `strategy_risk_audit.py`.

When enabled, the `run` command uses:

- `--cycle-log` as the Strategy Risk Audit cycle log.
- `--paper-journal` as the Strategy Risk Audit trade log.
- `--nav-log` as the Strategy Risk Audit NAV log.
- Optional `--outcome-log` as the latest persisted outcome evidence log.
- Optional `--strategy-audit-log` as an explicit opt-in local append-only JSONL
  evidence artifact for the preflight report.

The preflight runs before public client construction, before `run_strategy_loop`,
before `run_strategy_cycle`, before paper execution, before cycle-log append,
and before NAV marking.

## CLI Behavior

Default behavior is unchanged. Without `--strategy-audit-preflight`, `run`
continues to call the paper run loop exactly as before.

With `--strategy-audit-preflight`:

1. The command requires `--nav-log`, because the Strategy Risk Audit needs a NAV
   risk report.
2. The command builds the local Strategy Risk Audit report from existing logs.
3. If `--strategy-audit-log <path>` is supplied, the command appends the
   already-built report to that local JSONL evidence artifact.
4. The command prints the compact `strategy-audit:` summary.
5. If `report.status == "audit_ready"`, the run loop proceeds.
6. If `report.status` is `insufficient_evidence` or `blocked_by_risk`, the
   command exits non-zero and does not construct the public client or call the
   loop runner.
7. If local audit construction or audit-log append fails, the command exits
   non-zero and does not construct the public client or call the loop runner.

`--outcome-log` is optional. If omitted, the existing Strategy Risk Audit
semantics apply: settlement and forecast-quality evidence remain incomplete, so
the preflight will block unless all configured gates can still reach
`audit_ready`.

Audit logging is explicit opt-in. If `--strategy-audit-log` is omitted, no
Strategy Risk Audit log file is created or updated. When `run` is used without
`--strategy-audit-preflight`, `--strategy-audit-log` is inert because no Strategy
Risk Audit report is built.

For `run --config`, `strategy_audit_preflight`, `outcome_log`, and
`strategy_audit_log` may be set in the JSON config. The example config keeps
`strategy_audit_preflight` false so copying it does not unexpectedly block thin
paper runs or write audit logs. Explicit CLI flags still win over JSON config,
including `--no-strategy-audit-preflight` overriding a JSON `true`.

## Boundaries

Allowed:

- Read existing local paper JSONL artifacts explicitly passed by the caller.
- Build `PerformanceSummary`, `PaperNavRiskMetricsReport`,
  `PaperTradeCostAuditReport`, and optional `OutcomeTrackingReport` evidence
  through the existing CLI adapter.
- Append the already-built Strategy Risk Audit report to a local JSONL evidence
  artifact only when `--strategy-audit-log` or `strategy_audit_log` explicitly
  selects a path.
- Print local audit and run summaries.

Forbidden:

- No live trading.
- No account authentication.
- No private-key handling.
- No wallet handling.
- No account reads.
- No automated order placement, signing, submission, or cancellation.
- No order SDK integration.
- No strategy-weight tuning.
- No market ranking, project selection, trade recommendation, trade instruction,
  or financial advice.
- No changes to `runner.py` scope or imports.
- No changes to `strategy_risk_audit.py` file/log/client boundaries.
- No default audit-log writes.

## Acceptance Criteria

- `run --strategy-audit-preflight` allows the loop when a local audit report is
  `audit_ready`.
- The preflight prints the compact `strategy-audit` summary and all six
  Strategy Risk Audit gate rows.
- `run --strategy-audit-preflight` blocks when the local audit report is
  `insufficient_evidence`.
- `run --strategy-audit-preflight` blocks when the local audit report is
  `blocked_by_risk`.
- Blocked preflight does not call `client_factory()` and does not call
  `loop_runner(...)`.
- Failed preflight does not call `client_factory()` and does not call
  `loop_runner(...)`.
- `run --strategy-audit-preflight --strategy-audit-log <path>` appends both
  `audit_ready` and blocked reports before public client construction.
- Preflight requires `--nav-log` and fails before local audit construction when
  it is omitted.
- Default `run` behavior remains opt-in and does not require Strategy Risk Audit
  evidence or write audit logs.
- `run --config` can opt in with `strategy_audit_preflight: true` and can pass
  `outcome_log` and `strategy_audit_log` as local JSONL paths.
- Explicit `--no-strategy-audit-preflight` overrides a JSON config that sets
  `strategy_audit_preflight: true`.
- README and specs document the optional preflight as local-only paper
  observability, with optional append-only local JSONL evidence logging, not as
  approval, recommendation, ranking, trade instruction, financial advice, or live
  execution.
