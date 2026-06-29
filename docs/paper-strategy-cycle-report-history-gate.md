# Paper Strategy Cycle Report History Gate Runbook

## Purpose

`polymarket-alpha-lab strategy-cycle-history-gate` reads persisted paper
strategy-cycle reports from local Supabase/Postgres, reduces them into a
strategy-cycle history report, and then applies the pure history gate reducer.

Use this command before downstream autonomous paper recommendation stages need a
compact pass/watch/blocked signal for recent strategy-cycle scan quality. The
default command is read-only: it reads source history from the existing paper
strategy-cycle report table and prints one summary line.

## Required Source DB Environment

Set these source DB variables at the process edge before running the command:

```text
POLYMARKET_ALPHA_LAB_PAPER_STRATEGY_CYCLE_REPORT_DB_ENABLED=true
POLYMARKET_ALPHA_LAB_PAPER_STRATEGY_CYCLE_REPORT_DB_DSN
```

Optionally set a source table override:

```text
POLYMARKET_ALPHA_LAB_PAPER_STRATEGY_CYCLE_REPORT_DB_TABLE
```

When the optional source table variable is omitted, the command reads
`paper_strategy_cycle_reports`. The source DSN must point to the local
Supabase/Postgres stack accepted by the project local-DSN validator. Keep DSN
values and environment contents out of shell history, logs, tickets, and runbook
notes.

## Optional Gate Persistence Environment

Gate persistence is off unless the command is run with `--persist`. When
persisting gate reports, set these local Supabase/Postgres variables:

```text
POLYMARKET_ALPHA_LAB_STRATEGY_CYCLE_HISTORY_GATE_DB_ENABLED=true
POLYMARKET_ALPHA_LAB_STRATEGY_CYCLE_HISTORY_GATE_DB_DSN
```

Optionally set a gate table override:

```text
POLYMARKET_ALPHA_LAB_STRATEGY_CYCLE_HISTORY_GATE_DB_TABLE
```

When the optional gate table variable is omitted, the command writes to
`paper_strategy_cycle_report_history_gate_reports`. The gate DB DSN must also be
local-only. Do not pass source or gate DSNs or table names as command-line
arguments.

## Commands

Run the gate without persistence:

```bash
polymarket-alpha-lab strategy-cycle-history-gate --limit 50
```

Run the gate and persist the resulting gate report to local Supabase/Postgres:

```bash
polymarket-alpha-lab strategy-cycle-history-gate --limit 50 --persist
```

To restrict the source rows by history config version, add
`--source-config-version <config-version>`. `--limit` controls how many newest
persisted source cycle reports are loaded before the history reducer summarizes
them chronologically.

## Summary Output

The command prints one aggregate line:

```text
strategy-cycle-history-gate: status=<status> source_history_status=<status> reports=<count> latest_snapshot_ready_share=<rate> blocked_market_share=<rate> persisted=<true|false>
```

`status` is the gate status. `source_history_status` is the status from the
underlying strategy-cycle history report. `persisted=true` appears only when
`--persist` succeeds.

## Phase 1 Safety Boundary

Phase 1 is paper-only and report-only. This path performs no live trading, no
account auth, no wallet access, no private keys, no order signing, no order submission,
no order cancellation, no order replacement, and no exchange mutation.

The default command writes nothing. With `--persist`, the only permitted write is
the derived paper strategy-cycle history gate report to local Supabase/Postgres.
It must not mutate source strategy-cycle reports, exchange state, accounts,
wallets, orders, positions, or markets.

Operator output should stay aggregate-only: status, counts, rates, persistence
state, and reason codes. Do not print DSNs, table names, payload JSON, raw DB
records, secrets, or environment contents.

## Interpretation

`blocked` means the source history itself is blocked or the latest source
timestamp is missing. Treat this as a hard stop for downstream autonomous paper
recommendation stages.

`watch` means the source history is cautionary or stale. Treat this as a
throttle signal until fresh strategy-cycle reports improve the aggregate state.

`pass` means the source history currently satisfies the pure gate reducer and is
usable by downstream paper-only stages.
