# Paper Autonomous Readiness Gate

## Scope

The paper autonomous readiness gate is a Phase 1 paper-only/report-only/read-only pure reducer.
It consumes already-built typed reports and emits an operator-facing paper review
status. It does not query or load DB history, does not connect to Supabase or
Postgres, does not read env, and does not persist reports. This node still
does not add a CLI builder, env reads, broker/order requests, or persistence
behavior to the pure reducer.
It does not add persistence/schema/store compatibility and does not add DB
loaders/env/CLI/live/auth/wallet/key/order behavior.

## Source Reports

The reducer accepts these required already-built typed reports:

- screening decision-support gate DB-history health
- allocation proposal DB-history health trend gate
- investment-ledger DB-history health trend gate

The reducer also accepts optional pure sources:

- strategy-cycle report history gate, recorded as
  `strategy_cycle_report_history_gate`
- strategy-risk-audit history gate, recorded as
  `strategy_risk_audit_history_gate`

When present, the strategy-cycle source is ordered after the screening source
and before the allocation source. The strategy-risk source is appended after the
investment-ledger source.

Compatibility remains explicit: three-source legacy reports remain valid,
strategy-cycle-only four-source reports remain valid, strategy-risk-only
four-source reports remain valid, and combined five-source reports are used when
both optional pure sources are supplied.

DB history selection, env config, trend loading, persistence, and upstream
source-table reads stay outside this reducer.

## Readiness Status

The readiness report has `pass`, `watch`, or `blocked` status. A `blocked`
source blocks the readiness gate; otherwise a `watch` source makes the readiness
gate watch; otherwise the gate passes.

The status is for operator-facing paper review.

- does not alter strategy behavior
- does not trigger allocation
- does not stop execution paths
- does not promote a paper status into a trading decision

## Review Boundaries

- no CLI
- no CLI builder
- no runner
- no sink
- no loader
- no DB loaders
- no persistence path
- no persistence behavior in the pure reducer
- no DB schema/store compatibility changes
- no env read
- no env reads
- no DSN/table flags
- no `--persist`
- no `--fast`
- no live trading
- no auth
- no broker/order requests
- no key handling
- no private keys
- no wallet handling
- no account reads
- no order construction
- no order signing
- no order submission
- no order cancellation
- no order replacement
- no exchange mutation
- pass status is not permission to trade
- not financial advice
- not investment ranking
- not order instruction
- not execution authorization
- not an approval workflow
