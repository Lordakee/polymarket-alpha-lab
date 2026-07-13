# Probability Event Readonly Supabase Principles

This Phase 1 node defines the readonly boundary and local persistence principles
for Polymarket probability-event filtering. It supports the strategy workflow
and operator runbook:

- [Phase 1 Probability Event Filtering Workflow](../strategy/phase1-probability-event-filtering-workflow.md)
- [Phase 1 Probability Event Go/No-Go Runbook](../operators/phase1-probability-event-go-no-go-runbook.md)

The node is documentation only. It does not add execution, authentication,
wallet, account, order, Supabase migration, CLI, or live trading behavior.

## Phase 1 Boundary Statement

Phase 1 probability-event filtering is:

- paper-only;
- report-only;
- readonly;
- local evidence and report persistence only;
- operator-facing decision support only.

Phase 1 probability-event filtering is not:

- live trading;
- automated investing;
- investment advice;
- trade instruction generation;
- position advice or position sizing;
- wallet handling or private-key handling;
- account authentication or hosted account reading;
- order signing, submission, cancellation, replacement, or routing;
- exchange mutation or account mutation;
- production database behavior or hosted database operation.

Any later phase that proposes live execution must be separately designed,
reviewed, approved, and tested with explicit credential handling, risk controls,
audit logs, authorization, and kill-switch behavior. This document does not
provide that authorization.

## Readonly Data Flow

The approved Phase 1 data flow is:

```text
safe readonly market and evidence inputs
  -> normalized probability-event screen
  -> specialist research packet
  -> cost, EV, liquidity, settlement, and resolution-risk review
  -> manual go/no-go packet
  -> local Supabase/Postgres report row
  -> readonly readback, diagnostics, trend review, and post-resolution learning
```

No step in this flow may create an order intent, order request, exchange
request, account request, wallet request, credential request, or live execution
signal.

## Local Supabase/Postgres as the Durable Boundary

All durable Phase 1 probability-event filtering data must use local
Supabase/Postgres only. The durable store is for report history, team memory,
diagnostics, and readonly learning. It is not exchange state, account state,
wallet state, order state, or execution state.

Approved durable report categories include:

- market discovery and screening rows;
- specialist team assignment and research packet summaries;
- evidence quality and source-readiness summaries;
- side-aware forecast and confidence summaries;
- cost, EV, liquidity, depth, spread, fee, slippage, settlement, and
  resolution-risk summaries;
- manual go/no-go packet rows;
- operator review status, reason codes, blocked reasons, and follow-up fields;
- readonly readback, diagnostic, trend, and outcome-learning summaries.

Durable rows should preserve enough context for audit replay without persisting
unsafe raw payloads. Prefer digests, public references, source labels, reason
codes, status fields, counts, timestamps, and redacted summaries.

## DSN and Connection Principles

Any raw database URL or DSN must be validated as a local Postgres DSN before a
connection is opened. DSNs may come from environment variables or approved local
configuration, but they must not be printed, persisted unredacted, or copied
into operator output.

Connection principles:

- accept only local Supabase/Postgres DSNs for durable Phase 1 report history;
- fail closed when the DSN is missing, hosted, malformed, or not local;
- do not introduce CLI DSN overrides unless an existing approved local pattern
  explicitly allows them;
- do not print passwords, tokens, hosts with credentials, or raw DSN strings;
- use redaction markers such as `<redacted>` in docs, logs, and reports.

## Forbidden Durable Substitutes

The probability-event filtering path must not introduce or expand alternate
durable stores as substitutes for local Supabase/Postgres.

Forbidden durable substitutes include:

- SQLite or SQLite fallback files;
- DuckDB;
- Redis;
- MongoDB;
- hosted database assumptions;
- SQLAlchemy-managed durable engines;
- generic durable-store abstraction layers;
- JSONL durable journals;
- CSV durable ledgers;
- file-backed durable stores;
- filesystem caches used as durable report history or team memory.

Compatibility files and generated artifacts may exist only when an existing
workflow treats them as non-durable fixtures, temporary outputs, or local
reports. They must not become Phase 1 durable memory, strategy state, or report
history.

## Redaction Principles

Operator output, docs examples, logs, persisted payload summaries, and review
packets must redact or omit:

- raw DSNs;
- passwords;
- API keys;
- auth tokens;
- cookies;
- private keys;
- seed phrases;
- wallet material;
- account identifiers;
- hosted account details;
- live order ids;
- credential-like headers;
- private source payloads.

Use placeholder values that cannot be mistaken for real credentials. Prefer
hashes, digests, row ids, public market references, and status fields over raw
sensitive payloads.

## Persistence Review Checklist

Before a new probability-event filtering report row or readback path is treated
as Phase 1-compliant, verify:

- `paper_only=True`, `report_only=True`, and `readonly=True` are preserved where
  the surface supports flags;
- durable data targets local Supabase/Postgres only;
- raw DSNs are validated as local before use and redacted from output;
- report payloads do not contain secrets, wallet data, account data, or
  order-like sensitive values;
- the row stores research/report evidence, not execution state;
- no alternate durable fallback is introduced;
- readback is readonly and cannot mutate database, exchange, account, wallet,
  order, or credential state;
- operator packet status does not become an automated execution signal.

## Manual Go/No-Go Persistence Rule

A manual go/no-go packet may be persisted only as local report evidence. The
persisted status is a research and review artifact. It is not an approval
record, not an investment recommendation, not an order instruction, and not a
position-sizing record.

Allowed statuses remain:

- `go_for_manual_review`;
- `no_go`;
- `research`;
- `watch`;
- `blocked`.

`go_for_manual_review` means a human can review the packet. It never means the
system should buy, sell, place, submit, sign, cancel, replace, or route an
order.
