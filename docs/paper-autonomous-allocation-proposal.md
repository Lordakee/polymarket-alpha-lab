# Paper Autonomous Allocation Proposal

## Scope

The Paper Autonomous Allocation Proposal is a paper-only/report-only/read-only autonomous allocation proposal for Polymarket probability-event allocation review. It consumes already-produced and persisted upstream paper reports and combines upstream paper reports into an allocation proposal status and recommended next step for operator review.

This stage moves toward autonomous investing only by preparing paper allocation proposals. It does not allocate capital, alter strategy behavior, create live instructions, or replace human review.

Proposal status, recommended-next-step fields, reason-code counts, and allocation rows are operator review aids, not approvals.

The proposal is not financial advice, not investment ranking, not automatic live investing, not order instruction, not execution authorization, not an approval workflow, and not a live-execution signal.

## Source Reports

The source of truth is the set of already-produced and persisted upstream paper reports selected by the loader or caller. The default operator flow uses:

- the latest autonomous screening decision-support gate report
- the latest action-gated queue decision-support priority and risk reports
- source action-gated queue reports across statuses, including paper research-ready rows
- the existing paper recommendation allocation reducer and allocation report

The decision-support snapshot alone is not enough for per-market rows; source queue reports provide the paper row details used to build allocation inputs.

The reducer must treat upstream paper reports as immutable evidence. It must not fetch live market data, read accounts, repair missing upstream reports, create new research, change upstream weights, or mutate source reports.

## Operator Flow

1. Upstream paper workflows produce and persist their own screening, queue, priority, risk, cost, and allocation-related report artifacts.
2. The read-only loader selects the requested persisted upstream report window and source queue rows.
3. The proposal reducer checks hard paper/report/read-only flags, consistency between the screening gate and queue reports, and source queue availability.
4. Ready source queue rows from research-ready reports become paper allocation inputs for the existing paper recommendation allocation reducer.
5. The operator reviews proposal status, recommended next step, reason codes, source queue summary, and paper allocation rows.
6. Any follow-up remains a paper review action outside this proposal stage.

The flow ends at report output. It is a paper allocation review checkpoint, not an execution workflow.

The reducer preserves the source queue row action in paper allocation inputs. If an upstream ready row carries a non-recommend action, the allocation reducer treats it as `non_recommend`, forcing operator review instead of upgrading it to a paper allocation.

## Allocation Proposal Status and Next Step

Allocation proposal status should describe whether the selected upstream paper evidence can support the next paper allocation review:

- `pass`: the autonomous screening gate and queue risk evidence passed, source queue rows are available, and the allocation reducer produced a paper proposal suitable for review.
- `watch`: upstream evidence exists but gate, risk, source consistency, cap pressure, or allocation constraints require operator inspection.
- `blocked`: upstream evidence is missing, stale, internally inconsistent, blocked by the screening gate or queue risk, or unable to produce a usable paper allocation proposal.

The recommended next step is a paper review label such as `review_paper_autonomous_allocation_proposal`, `hold_paper_autonomous_allocation_proposal`, or `block_paper_autonomous_allocation_proposal`.

A pass status is not permission to trade. A watch status is not a live monitoring instruction. A blocked status is not an exchange action.

## Paper Allocation Evidence

Paper notional is paper sizing, not capital commitment. Paper allocation proposal rows are not order tickets.

Paper allocation rows carry proposed paper notional, paper share quantities, cap usage, zero or reduced allocation reason codes, and allocation status for review. They are accounting rows for paper analysis only and must not be treated as capital movement, account state, exchange state, or a live-execution signal.

## Transaction and Cost Awareness

Transaction/cost awareness is upstream evidence. This proposal may reflect already-computed paper cost, fee-drag, liquidity, slippage, fill-quality, or cost-discipline evidence from upstream reports.

There is no live fee estimation, no live trading, no order construction, no order signing, no order submission, no order cancellation, no order replacement, and no exchange mutation in this stage.

The proposal must not query current fee schedules, request order books, build order payloads, estimate live fill costs, or transform paper cost awareness into execution authorization.

## CLI Contract

The operator command is env-only, report-only, read-only, and no-write:

```bash
.venv/bin/polymarket-alpha-lab paper-autonomous-allocation-proposal --limit 25
```

The command reads already-persisted upstream reports from environment-configured paper report stores. It accepts only `--limit`; it does not accept DSN/table/persist flags, does not write reports, and does not create missing upstream inputs.

The persisted handoff is a separate sibling producer command:

```bash
.venv/bin/polymarket-alpha-lab paper-autonomous-allocation-proposal-persist --limit 25
```

It additionally requires:

- `POLYMARKET_ALPHA_LAB_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_ENABLED`
- `POLYMARKET_ALPHA_LAB_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_DSN`
- `POLYMARKET_ALPHA_LAB_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_TABLE`

It accepts only `--limit`, persists only the final proposal report, and remains paper-only/report-only/read-only. It prints the usual aggregate summary plus `persisted=True/False`.

It does not write upstream reports, place orders, approve execution, read accounts, or mutate exchange state.

The CLI does not accept live/auth/wallet/private-key/api-key/account/order/trade/execute/submit/approve flags. It prints aggregate paper proposal status, recommended next step, counts, reason-code summaries, and redacted operator evidence only.

Do not put secret values, credentials, DSN values, wallet material, private keys, account identifiers, table names, payload JSON, hashes, market questions, or market slugs in operator examples or runbook output.

## DB History Readback

The DB history readback command is env-only, read-only, paper-only/report-only/readonly, and no-write:

```bash
.venv/bin/polymarket-alpha-lab paper-autonomous-allocation-proposal-db-history --limit 25
```

It accepts only `--limit`. It reads the final allocation proposal DB configured by env and reads only persisted final allocation proposal reports.

It does not write reports and does not read upstream tables.
It does not place orders, approve execution, read accounts, or mutate exchange state.

It prints aggregate history status, proposal-status counts, latest aggregate allocation counts, duplicate timestamp count, and reason-code summaries.

## DB History Gate

The DB history gate command is env-only, read-only, paper-only/report-only/readonly, and no-write:

```bash
.venv/bin/polymarket-alpha-lab paper-autonomous-allocation-proposal-db-history-gate --limit 25
```

It accepts only `--limit`. It reads the final allocation proposal DB configured by env and reads only persisted final allocation proposal reports through the DB history readback.

It does not write reports and does not read upstream screening/queue tables.
It does not place orders, approve execution, read accounts, or mutate exchange state.

The gate status is not permission to trade. It is not financial advice, not investment ranking, and not an approval workflow.

It prints aggregate gate status, recommended next step, source history status, latest aggregate allocation counts, duplicate timestamp count, latest source age, and reason-code counts.

## DB History Health

The DB history health command is env-only, read-only, paper-only/report-only/readonly, and no-write:

```bash
.venv/bin/polymarket-alpha-lab paper-autonomous-allocation-proposal-db-history-health --limit 25
```

It accepts only `--limit`. It reads the final allocation proposal DB configured by env and reads only persisted final allocation proposal history through DB history readback.

It does not write reports and does not read upstream screening/queue tables.
It does not place orders, approve execution, read accounts, or mutate exchange state.

The health status is not permission to trade. It is not financial advice, not investment ranking, and not an approval workflow.

It prints aggregate health status, source history status, latest aggregate allocation counts, duplicate timestamp count, and reason-code counts.

## DB History Health Persistence

DB history health persistence stores already-built DB history health reports as local DB audit evidence.

Local DB persistence for DB history health reports is optional, default-off, env-driven, and separate from the read-only health command.

It persists only already-built health reports. It does not recompute proposal history, run trend or gate logic, read upstream tables, fetch market data, or mutate exchange state.

Persisted health rows are audit evidence only. They are not approval workflow records, not order intents, not execution requests, not strategy promotion signals, not trade instructions, not recommendations, not rankings, and not financial advice.

## DB History Health Trend

The DB history health trend command is env-only, read-only, paper-only/report-only/readonly, and no-write:

```bash
.venv/bin/polymarket-alpha-lab paper-autonomous-allocation-proposal-db-history-health-trend --limit 25
```

It accepts only `--limit`. It reads the final allocation proposal DB configured by env and reads only persisted final allocation proposal history through DB history readback before building one read-only trend report over that caller-selected window.

When fewer persisted proposal reports than the DB-history minimum are available, the loader emits one blocked boundary health snapshot so insufficient history remains visible in the trend output.

It does not write reports and does not read upstream screening/queue tables.
It does not place orders, approve execution, read accounts, or mutate exchange state.

The trend status is not permission to trade. It is not financial advice, not investment ranking, and not an approval workflow.

It prints aggregate health-status trend counts, latest health status, delta summaries, duplicate timestamp count, streak counts, and latest reason-code counts.

Its package-root Python API exposes:

- `PaperAutonomousAllocationProposalDbHistoryHealthTrendConfig`
- `PaperAutonomousAllocationProposalDbHistoryHealthTrendReasonCodeRow`
- `PaperAutonomousAllocationProposalDbHistoryHealthTrendSnapshotSummary`
- `PaperAutonomousAllocationProposalDbHistoryHealthTrendReport`
- `build_paper_autonomous_allocation_proposal_db_history_health_trend_report(...)`

The reducer summarizes already-produced DB history health reports across a caller-selected persisted window. It is trend reporting over existing paper artifacts only.

It must not write reports, must not read upstream screening or queue tables directly, and must not fetch, authenticate, handle wallets or private keys, read accounts, place orders, approve execution, or mutate exchange state.

The trend summary remains negative-boundary first: no live trading, no auth, no wallet, no key handling, no account reads, no order instruction, no execution authorization, no approval workflow, and no exchange mutation.

## DB History Health Trend Gate

The DB history health trend gate command is env-only, read-only, paper-only/report-only/readonly, and no-write:

```bash
.venv/bin/polymarket-alpha-lab paper-autonomous-allocation-proposal-db-history-health-trend-gate --limit 25
```

It accepts only `--limit`. It reads the final allocation proposal DB configured by env, derives the DB history health trend from persisted final allocation proposal history, and prints one aggregate gate report.

It does not write reports and does not read upstream screening/queue tables.
It does not place orders, approve execution, read accounts, or mutate exchange state.

The health-trend gate status is not permission to trade. It is not financial advice, not investment ranking, and not an approval workflow.

It prints aggregate health-trend gate status, recommended next step, latest health status, sample counts, duplicate timestamp count, latest streak counts, health-delta signals, and reason-code counts.

The health-trend gate reducer is not permission to trade, not financial advice, not investment ranking, and not an approval workflow.

## Review Boundaries

The Phase 1 boundary is explicit:

- no live trading
- no automatic live investing
- no auth
- no key handling
- no wallet handling
- no account handling
- no account reads
- no order instruction
- no order construction
- no order signing
- no order submission
- no order cancellation
- no order replacement
- no execution authorization
- no approval workflow
- no live-execution signal
- no exchange mutation
- no investment ranking
- no financial advice

Operator notes and runbooks should describe source report freshness, proposal status, recommended next step, paper allocation rows, and reason codes only.

This stage must not connect to authentication, key or wallet handling, account handling, exchange clients, live execution, or any component that can mutate exchange state.
