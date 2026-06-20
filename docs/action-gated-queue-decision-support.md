# Action-Gated Queue Decision Support

## Scope

Action-gated queue decision support is Phase 1 paper-only/report-only/readonly decision support for operators reviewing already-built action-gated queue reports. It summarizes persisted paper reports for research attention only.

Priority and risk outputs are operator review aids, not trade approvals. Recommended next-step fields are labels for paper research allocation and review sequencing, not permission to trade.

The boundary exclusions are explicit:

- no live trading
- no authenticated exchange flow
- no wallet/private keys
- no account reads
- no order construction
- no order signing
- no order submission
- no order cancellation
- no order replacement
- no exchange mutation

## Source Data

Supabase/Postgres is a read-only source of already-persisted action-gated queue reports without secrets/DSNs/env contents. Operators should treat it as a persisted report source only: the database path loads existing queue reports and does not create, update, delete, or mutate exchange state.

Do not document secret values, DSNs, env contents, credentials, wallet material, or raw payload JSON in operator notes. Runtime configuration stays at the process boundary and any CLI output must stay redacted.

## Operator Flow

1. Runtime sink appends action-gated queue reports after the runtime has already built the paper-only queue report.
2. The read-only psycopg loader loads persisted queue reports and returns typed report objects without adding summary or write semantics.
3. The priority reducer ranks whole queue reports for human research attention, preserving report-level context rather than turning candidates into executable intent.
4. The risk summary highlights cap utilization, source queue status pressure, and reason codes so an operator can see whether the persisted queue set is pass, watch, or blocked for paper research allocation.
5. The CLI prints a redacted decision-support summary with aggregate priority and risk fields only.

## Review Boundaries

Priority rows, risk summaries, and CLI summaries are operator review aids, not trade approvals. They can help an operator decide which persisted queue report to inspect first, whether ready notional is near a paper cap, and which watch or blocking reason codes explain the current state.

The decision-support flow ends at redacted reporting. It does not read accounts, construct orders, sign orders, submit orders, cancel orders, replace orders, authenticate to an exchange, handle wallet/private keys, or mutate an exchange.
