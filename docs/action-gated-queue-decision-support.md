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

## Trend Report

The Action-Gated Decision-Support Trend Report is a library-only Phase 1 paper-only/report-only/readonly reducer over caller-supplied decision-support snapshot pairs. The caller supplies already-built snapshot pairs; the reducer sorts snapshots chronologically by `generated_at` before deriving trend fields and uses the original input position only as a deterministic tie-break for duplicate timestamps.

Duplicate `generated_at` values are reported as duplicate source timestamps so operators can identify ambiguous snapshot ordering without changing the source data.

Trend output is only a paper/report/readonly review aid. It does not rank reports, approve reports, allocate notional, size positions, construct execution intent, or perform execution.

The Phase 1 boundary stays explicit for the CLI surface:

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

Trend DB persistence stores compact scalar trend summaries, JSON count maps, reason-code rows, hard paper/report/readonly flags, and ordered source snapshot references to already-persisted decision-support reports. It does not duplicate priority/risk payloads, and it does not provide full trend hydration from the database; callers that need full reports must use the existing source snapshots.

## Trend CLI

The Phase 1 CLI surface is `polymarket-alpha-lab action-gated-queue-decision-support-trend`. It remains paper-only, report-only, and readonly from the operator point of view by default: it reads already-persisted decision-support reports from the source DB, builds a redacted aggregate trend summary, and prints review-only output.

The command uses environment-only DB configuration. It does not accept DSNs, credentials, wallet material, or other secret values as CLI flags, and CLI output must stay redacted.

### Source DB

Source snapshot loading is controlled only by the existing action-gated queue decision-support source DB environment variables:

```text
POLYMARKET_ALPHA_LAB_ACTION_GATED_QUEUE_DECISION_SUPPORT_DB_ENABLED
POLYMARKET_ALPHA_LAB_ACTION_GATED_QUEUE_DECISION_SUPPORT_DB_DSN
POLYMARKET_ALPHA_LAB_ACTION_GATED_QUEUE_DECISION_SUPPORT_DB_TABLE
```

Those source DB variables select the already-persisted decision-support reports that the trend command reads. They are process-edge runtime inputs only and must not be echoed into docs, notes, or CLI output.

### Optional Trend Persistence

The command supports optional `--persist` trend DB persistence. Without `--persist`, the command is a read/report-only trend summary over source snapshots and should not write trend rows.

When `--persist` is set, trend-row persistence still depends on environment-only trend DB configuration:

```text
POLYMARKET_ALPHA_LAB_ACTION_GATED_QUEUE_DECISION_SUPPORT_TREND_DB_ENABLED
POLYMARKET_ALPHA_LAB_ACTION_GATED_QUEUE_DECISION_SUPPORT_TREND_DB_DSN
POLYMARKET_ALPHA_LAB_ACTION_GATED_QUEUE_DECISION_SUPPORT_TREND_DB_REPORTS_TABLE
POLYMARKET_ALPHA_LAB_ACTION_GATED_QUEUE_DECISION_SUPPORT_TREND_DB_SOURCES_TABLE
```

That optional persistence path stores compact trend manifests only. It must not create live trading state, authenticate to an exchange, read accounts, construct orders, sign orders, submit orders, cancel orders, replace orders, or mutate an exchange.

### Persisted Trend DB History

The existing `polymarket-alpha-lab action-gated-queue-decision-support-trend` command is the rebuild path: it reads source decision-support rows, rebuilds the trend from those source snapshots, and optionally persists a compact trend manifest when `--persist` and trend DB env configuration are enabled.

The read-only history surface is `polymarket-alpha-lab action-gated-queue-decision-support-trend-db-history`. It reads persisted trend DB rows only, uses only the trend DB environment variables listed above, and does not require the source decision-support DB environment variables. It supports `--limit` and optional `--latest-risk-status pass|watch|blocked`, exposes no DSN or table CLI flags, and never persists new rows.

The history output reports the trend count, source snapshot count, first and latest trend timestamps, latest risk status, risk counts, duplicate `generated_at` count, consecutive watch and blocked streaks, latest deltas, and latest reason codes.

The Phase 1 boundary is unchanged: this command is paper-only, report-only, and read-only. It must not perform live trading, auth, wallet/private-key handling, account reads, order construction, order signing, order submission, order cancellation, order replacement, or exchange/order mutation.

### CLI Options

The command options follow the existing aggregate-report CLI pattern:

- `--source-limit`: optional positive integer source snapshot cap for the source DB read path.
- `--source-risk-status`: optional source filter for the latest source risk status with `pass`, `watch`, or `blocked`.
- `--persist`: optional flag that enables trend-row persistence only when the trend DB env config is enabled.
