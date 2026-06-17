# Strategy Risk Audit Log v0 Spec

## Goal

Persist local Strategy Risk Audit reports as an append-only JSONL artifact so
continuous paper-run preflight decisions and manual `strategy-audit` checks have
a durable evidence trail that can also be summarized by the local
`strategy-audit-history` command.

This is Phase 1 paper-only/report-only observability over read-only local inputs
plus an explicit append-only local result artifact. It is not an approval
workflow, strategy-promotion signal, trade instruction, investment ranking,
recommendation, live-execution signal, or financial advice.

## Scope

Add a focused local log module for `PaperStrategyRiskAuditReport` values:

- `PaperStrategyRiskAuditLog(path).append(report)`
- `PaperStrategyRiskAuditLog.read(path)`

The log module may serialize and recover already-built
`PaperStrategyRiskAuditReport` dataclasses. It must not build audits, fetch data,
construct clients, read account state, authenticate, handle wallets or private
keys, or perform order actions.

Expose optional CLI persistence:

- `strategy-audit --strategy-audit-log <path>` appends the report that the
  command already builds and prints.
- `run --strategy-audit-preflight --strategy-audit-log <path>` appends the
  preflight report before deciding whether the paper run may proceed.
- `strategy-audit-history --strategy-audit-log <path>` may later read the same
  local JSONL artifact and print append-order status history without appending.
- `run --config` may set `strategy_audit_log` to the same local JSONL path.

Default behavior remains unchanged. No audit log is written unless the caller
explicitly supplies `--strategy-audit-log` or the matching JSON config key for
`run`.

## Boundaries

Allowed:

- Append and read local JSONL report artifacts explicitly selected by the
  caller.
- Round-trip the `PaperStrategyRiskAuditReport` values produced by the current
  Strategy Risk Audit builder, including all six gate rows. The v0 JSONL format
  follows existing report-log style and does not add type tags for arbitrary
  `Decimal | int | str | None` gate values.
- Create parent directories for valid log paths.
- Reject invalid append inputs before creating files.
- Skip blank lines and report invalid JSON with a line number on reads.

Forbidden:

- No live trading.
- No account authentication.
- No wallet or private-key handling.
- No account reads.
- No order placement, signing, submission, or cancellation.
- No market ranking, project selection, recommendation, trade instruction, or
  financial advice.
- No changes to `runner.py`.
- No changes to the pure Strategy Risk Audit math in `strategy_risk_audit.py`.
- No package-root export; `polymarket_alpha_lab.__all__` continues to expose
  only the pure Strategy Risk Audit report API for `PaperStrategyRiskAudit*`
  names.

## CLI Behavior

`strategy-audit`:

1. Builds the local audit report exactly as before.
2. If `--strategy-audit-log` is supplied, appends that report to the JSONL log.
3. Prints the compact strategy-audit summary.
4. Returns `0` on success; returns `1` if report construction or log append
   fails.

`run --strategy-audit-preflight`:

1. Builds the local audit report before public client construction.
2. If `--strategy-audit-log` is supplied, appends the audit report before the
   status gate is evaluated.
3. Prints the compact strategy-audit summary.
4. If the report is not `audit_ready`, exits `1` before client construction and
   loop execution.
5. If the report is `audit_ready`, proceeds to the paper run.

When `run` is used without `--strategy-audit-preflight`, `--strategy-audit-log`
is inert because no Strategy Risk Audit report is built. If no audit log path is
supplied, behavior is unchanged and no audit artifact is written.

`strategy-audit-history`:

1. Reads a caller-selected local Strategy Risk Audit JSONL artifact.
2. Builds a paper-only/report-only/read-only history summary from already-built
   reports.
3. Prints append-order status counts, latest evidence state, latest
   failed/incomplete audit-check names, and per-check status counts.
4. Does not append to the log or change run behavior.

## Acceptance Criteria

- `PaperStrategyRiskAuditLog.append(report)` validates a real
  `PaperStrategyRiskAuditReport`, creates parent directories, writes one JSONL
  line, and rejects invalid inputs before creating files.
- `PaperStrategyRiskAuditLog.read(path)` returns fully typed
  `PaperStrategyRiskAuditReport` values, skips blank lines, returns `()` for an
  empty file, and raises `ValueError` with the line number for invalid JSON.
- The log module exposes `PaperStrategyRiskAuditLog` through its own module
  `__all__`; the package root does not export it.
- `strategy-audit --strategy-audit-log <path>` appends the same report it prints
  without constructing a public client.
- `run --strategy-audit-preflight --strategy-audit-log <path>` appends both
  `audit_ready` and blocked preflight reports before public client construction.
- `run --config` can provide `strategy_audit_log` as a local path.
- Default `run` behavior and default `strategy-audit` behavior do not write audit
  logs.
- `strategy-audit-history --strategy-audit-log <path>` reads the local log and
  prints a read-only evidence summary without constructing a public client.
- README and specs document the optional log as a local evidence artifact, not as
  approval, recommendation, ranking, trade instruction, financial advice, or live
  execution.
