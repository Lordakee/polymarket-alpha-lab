# Paper Strategy Cycle Report DB History Runbook

## Purpose

`polymarket-alpha-lab strategy-cycle-db-history` prints a read-only history
summary from persisted `PaperStrategyCycleReport` rows in the
`paper_strategy_cycle_reports` table.

Use it to inspect whether recent paper strategy-cycle history is sufficient for
downstream paper-only selection signals. The command reads existing local
Supabase/Postgres rows, summarizes aggregate readiness and blocked-market
metrics, and writes no rows.

## Required Environment

Set these variables at the process edge before running the command:

```text
POLYMARKET_ALPHA_LAB_PAPER_STRATEGY_CYCLE_REPORT_DB_ENABLED=true
POLYMARKET_ALPHA_LAB_PAPER_STRATEGY_CYCLE_REPORT_DB_DSN
```

Optionally set a source table override:

```text
POLYMARKET_ALPHA_LAB_PAPER_STRATEGY_CYCLE_REPORT_DB_TABLE
```

When the optional table variable is omitted, the command reads
`paper_strategy_cycle_reports`. The DSN must point to the local
Supabase/Postgres stack accepted by the project local-DSN validator. Keep DSN
values and environment contents out of shell history, logs, tickets, and runbook
notes.

## Command

Run from the repository root or any environment where the package CLI is
available:

```bash
polymarket-alpha-lab strategy-cycle-db-history --limit 50
```

`--limit` controls how many newest persisted cycle reports are loaded before the
history reducer summarizes them chronologically. The command uses environment
configuration only for DB connectivity and table selection.

## Safety

This is a local Supabase/Postgres-only, read-only paper reporting path. It must
not contact exchange mutation surfaces or perform production trading. It does
not use custody tooling, auth flows, signing secrets, account reads, order
construction, order submission, cancellation, replacement, or exchange mutation.

Operator output should stay aggregate-only: status, counts, rates, and reason
codes. Do not print DSNs, table names, payload JSON, raw DB records, secrets, or
environment contents.

## Interpretation

`blocked` means the persisted history is too sparse, or the latest snapshot
readiness share is below the configured threshold. Treat it as a signal that the
history is not yet reliable enough for downstream paper-only selection signals.

`watch` means the history is present, but the blocked-market share is high.
Use it as a caution state for paper-only selection signals until additional
cycles improve the aggregate history.

`pass` means the history is currently usable for downstream paper-only selection
signals under the configured minimum report count, latest snapshot-readiness
threshold, and blocked-market-share limit.
