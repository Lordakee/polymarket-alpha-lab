# Strategy Audit CLI v0 Spec

## Goal

Expose the existing Strategy Risk Audit as a local CLI report over paper artifacts so Phase 1 operators can inspect readiness gates without writing Python glue.

## In Scope

- Add `OutcomeTrackingLog` to persist and read full `OutcomeTrackingReport` JSONL snapshots.
- Extend `check-outcomes` with optional `--outcome-log <path>` that appends the full outcome-tracking report.
- Add `strategy-audit --cycle-log <path> --trade-log <path> --nav-log <path> [--outcome-log <path>]`.
- `strategy-audit` reads local typed logs only, builds `PerformanceSummary`, builds `PaperNavRiskMetricsReport`, optionally loads the latest `OutcomeTrackingReport`, then calls `build_paper_strategy_risk_audit_report(...)`.
- Allow `run --strategy-audit-preflight` to reuse the same local-log Strategy Risk Audit adapter as an optional preflight for continuous paper runs; this does not change default run behavior.
- Print a compact report summary plus every gate row.

## Out of Scope

- No live trading, auth, wallet, private key, order placement, order cancellation, signing, account reads, or trading SDK integration.
- No strategy-weight tuning, market ranking, project selection, recommendation, trade instruction, or financial advice.
- No changes to `strategy_risk_audit.py` file/log/client boundaries.
- No attempt to reconstruct `OutcomeTrackingReport` from `PaperForecastEvidenceReport`; the full outcome report must be persisted separately.

## Boundary Rules

`strategy-audit` is local-only orchestration. It must not construct `PolymarketPublicClient`, call `client_factory()`, call `check_outcomes`, fetch Gamma/CLOB data, read credentials, or write audit logs. It may read the local JSONL inputs explicitly passed by the caller.

When reused by `run --strategy-audit-preflight`, the audit remains local-only: it reads only explicitly passed JSONL artifacts, must run before public client construction, and must not construct `PolymarketPublicClient`, call `client_factory()`, fetch Gamma/CLOB data, read credentials, or write audit logs.

`check-outcomes --outcome-log` remains the existing read-only public Gamma outcome checker. The new flag only persists the already-built `OutcomeTrackingReport`; it does not add any new network or execution surface.

## Expected CLI

```bash
polymarket-alpha-lab check-outcomes \
  --journal artifacts/paper-trades.jsonl \
  --outcome-log artifacts/outcomes.jsonl

polymarket-alpha-lab strategy-audit \
  --cycle-log artifacts/strategy-cycle.jsonl \
  --trade-log artifacts/paper-trades.jsonl \
  --nav-log artifacts/nav.jsonl \
  --outcome-log artifacts/outcomes.jsonl
```

When `--outcome-log` is omitted or empty, settlement and forecast-quality gates remain incomplete.

For `run --strategy-audit-preflight`, an omitted or empty `--outcome-log` keeps settlement and forecast-quality evidence incomplete, so the preflight blocks unless the resulting local audit status is still `audit_ready`.

## Acceptance Criteria

- `OutcomeTrackingLog.append(report)` validates a real `OutcomeTrackingReport`, writes JSONL, creates parent directories, and rejects invalid inputs before creating files.
- `OutcomeTrackingLog.read(path)` returns fully typed reports, skips blank lines, returns `()` for empty files, and raises `ValueError` with the line number for invalid JSON.
- `check-outcomes --outcome-log` appends the full report even when zero observations resolved.
- `strategy-audit` can run with local cycle/trade/nav logs and no outcome log, prints six gates, and does not construct a client.
- `strategy-audit --outcome-log` uses the latest full outcome report.
- Public package exports include `OutcomeTrackingLog`.
- README documents the command and boundary clearly.
