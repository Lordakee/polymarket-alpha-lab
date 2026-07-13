# Phase 1 Report Discovery CLI

`report-discovery` is an operator navigation command for Phase 1 report
surfaces. It lists registered report entrypoints by aggregate category so a
human operator can find the next report or gate to run without scanning the full
CLI help output.

The command is discovery-only. It does not execute the listed reports, read or
write a database, persist evidence, create files, fetch market data, authenticate
accounts, inspect wallets, create order intent, submit orders, cancel orders, or
perform live trading.

## Command Shape

```text
polymarket-alpha-lab report-discovery [--category CATEGORY] [--format text]
```

Supported options:

| Option | Values | Meaning |
| --- | --- | --- |
| `--category` | `readiness`, `strategy-rollups`, `manual-review` | Limits output to one aggregate report category. Omit it to show all registered categories. |
| `--format` | `text` | Emits the readonly operator list as plain text. |

There are intentionally no input, output, persistence, database, account,
wallet, order, auth, execution, or live-trading flags on this command.

## Discoverable Report Categories

### `readiness`

Phase 1 readiness reports are read-only paper/report-only readiness gates and
digests for operator go/no-go review.

Current entrypoints:

- `paper-autonomous-readiness-digest`
- `team-memory-readiness-digest`
- `paper-autonomous-allocation-proposal-db-history-health-trend-gate`

Use this category when the operator needs to locate high-level readiness
digests before deciding which paper-only gate or report should be reviewed next.

### `strategy-rollups`

Critical strategy rollups are read-only paper/report-only summaries of strategy
selection, agreement, risk, and queue posture.

Current entrypoints:

- `probability-selection-scorer-agreement-trend-gate`
- `paper-probability-selection-summary-history-trend-gate`
- `paper-recommendation-cycle-action-gate`
- `action-gated-queue-decision-support-trend`

Use this category when the operator needs the aggregate strategy, scoring,
recommendation, or action-gated queue surfaces that summarize Phase 1 paper
posture.

### `manual-review`

Manual review packet reports are next-step read-only paper/report-only packet
commands for human operator review.

Current entrypoints:

- `paper-research-packet-operator-flow`
- `paper-research-packet-quality`
- `paper-research-packet-operator-flow-db-history-gate`

Use this category when the operator needs to find packet-quality, operator-flow,
or manual-review readiness surfaces.

## Operator Workflow

1. Run `polymarket-alpha-lab report-discovery` to list all registered Phase 1
   report groups.
2. Choose the category that matches the review objective:
   - readiness gate review;
   - strategy or queue rollup review;
   - manual packet triage.
3. Re-run with `--category <category>` when a narrower list is easier to scan.
4. Copy the exact command name from the output and run that report separately
   only if the operator intends to inspect that report surface.
5. Treat any downstream report output as Phase 1 paper/report evidence for
   human review, not as an execution signal.

## Readonly And Phase 1 Boundaries

`report-discovery` must remain:

- paper-only;
- report-only;
- readonly;
- operator-facing;
- deterministic text discovery over a fixed registry.

It must not:

- connect to local Supabase/Postgres or any hosted database;
- read from, write to, migrate, or persist database rows;
- fetch live market, account, wallet, order, or exchange data;
- request, print, store, or validate credentials;
- handle private keys, seed phrases, auth tokens, cookies, or wallet material;
- create order intent, order instructions, position advice, or investment
  advice;
- sign, submit, cancel, replace, route, or execute orders;
- perform live trading or mutate exchange/account state.

If a future phase needs executable behavior, database persistence, credential
handling, order handling, account reads, wallet handling, or live trading, that
work must be designed and reviewed as a separate phase. This CLI node provides
no such authorization.
