# Action-Gated Queue History

## Scope

action-gated-queue-history is the planned Phase 1 paper-only/report-only/read-only queue history CLI and report surface for operators reviewing already-persisted paper queue reports. It summarizes history across action-gated queue reports for research attention only.

History rows, trend fields, and CLI summaries are research review aids, not trade approvals. The surface does not approve trades, does not automate investment, and supports human/operator research review only.

The boundary exclusions are explicit:

- no live trading
- no auth
- no wallet/private keys
- no account reads
- no order construction
- no order signing
- no order submission
- no order cancellation
- no order replacement
- no exchange mutation

## Source Data

The runtime sink appends paper queue reports after the runtime has already built the paper-only report. Those appended reports are the only intended history input.

The read-only DB loader reads already-persisted reports from the existing paper report store and returns typed report objects. It is a read-only report source and does not create, update, delete, or mutate report rows or exchange state.

The pure history reducer summarizes trend/history metrics from typed reports. It computes aggregate history fields such as source report count, first and last source timestamps, action-status counts, ready notional movement, status transitions, latest action status, latest next step, and latest reason-code counts.

The persisted history DB history command reads already-persisted history reports
only:

```text
polymarket-alpha-lab action-gated-queue-history-db-history
```

It uses only the action-gated queue history DB environment boundary. It supports
only --limit and --latest-action-status research_ready|watch|blocked, never
persists rows, never reads source queue reports, and prints only redacted
aggregate history over persisted history reports.

## Operator Flow

1. The runtime sink appends paper queue reports from paper-only action-gated queue runs.
2. The read-only DB loader reads already-persisted reports and returns typed report values without write semantics.
3. The pure history reducer summarizes trend/history metrics across those typed reports without side effects.
4. The CLI prints an aggregate-only summary for operator review.
5. The persisted history DB history command reads already-persisted history
   reports only and summarizes whether the stored history itself is stable,
   oscillating, or repeatedly blocked.

Optional `--persist` stores only the built aggregate
`PaperActionGatedStrategyRecommendationQueueHistoryReport` through the separate
history DB environment boundary. It does not change the source loader, does not
write source queue rows, and does not persist payload details to CLI output.

## CLI Output Safety

The CLI output must stay redacted and aggregate-only. CLI output must not include DSNs, table names, payload JSON, raw DB records, secrets, or env contents.

Operator notes should also exclude secrets, DSNs, table names, payload details, raw DB records, credentials, wallet material, and private keys. Runtime configuration stays at the process boundary and must not be copied into CLI output or reports.

## Review Boundaries

The history surface is for paper report review only. It can help an operator see whether persisted paper queue reports are trending toward research_ready, watch, or blocked, whether paper ready notional is rising or falling, and which paper reason-code counts explain the latest aggregate state.

The history flow ends at redacted aggregate reporting. It does not read accounts, construct orders, sign orders, submit orders, cancel orders, replace orders, use auth, handle wallet/private keys, approve trades, automate investment, or mutate an exchange.
