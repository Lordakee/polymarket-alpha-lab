# Team Evaluation Attempt Latest Read

Narrow purpose: report exactly the latest persisted team-evaluation attempt
from local Supabase/Postgres as a read-only operator report. This is the
freeze-compliant first slice of strategy-cycle consumption of team-evaluation
evidence: it observes the latest attempt, its persisted status, and its
publication-gate evidence. It does not consume, rank, recommend, or act on
that evidence.

Scope constraints:

- Read-only reporting only. This module adds no writer, SQL, connection
  management, CLI command, environment variable, configuration family, or
  package-root export.
- The latest attempt is reported regardless of status; the reader never
  falls back to an older attempt and never selects or recommends a strategy
  side.
- Packet information is audit-only and contract-derived; packets are not
  persisted in the attempt row.
- Persistence is local Supabase/Postgres only. DSN handling, validation, and
  connection lifecycle stay owned by the reviewed Node 5 aggregation
  adapters.
- Keep this Phase 1 paper-only/report-only/readonly. The report supports
  local paper evidence review; it is not execution authorization.

## Module Surface

`src/polymarket_alpha_lab/team_evaluation_attempt_latest_read.py` exports
exactly three module-local names:

- `TeamEvaluationAttemptLatestReadReport`: one frozen, slotted dataclass
  carrying literal `paper_only=True`, `report_only=True`, and `readonly=True`
  hard flags.
- `read_latest_team_evaluation_attempt_report`: delegates to the Node 5
  DB-API store loader `load_latest_team_evaluation_attempt` over a
  caller-owned connection.
- `read_latest_team_evaluation_attempt_report_with_psycopg`: delegates to the
  Node 5 wrapper `load_latest_team_evaluation_attempt_with_psycopg`, which
  owns the table identifier check, the DSN check, the connection lifecycle,
  and the single commit.

Neither reader catches, rewrites, retries, or masks database errors; they
propagate unchanged to the caller.

## Latest-Row Ordering

Within a run (`tfr_id`) or a scope (`scope_version` plus `scope_key`), the
latest attempt is the first row ordered by `attempted_at DESC, tea_id DESC`
with `LIMIT 1`. Node 5 owns that ordering, the filter combination rules, and
the table identifier check; this reader only delegates and projects one
validated row. History is ordering, not linkage: attempts are immutable,
insert-only rows with no revision ordinal and no supersession link, so
"latest" is purely the ordering question above.

## No-Fallback Rule

The latest row is reported regardless of its status. When the latest attempt
is `watch` or `blocked`, the report says exactly that; the reader never falls
back through the newer watch/blocked attempt to an older `ready` row, never
retries with looser filters, and never fabricates a status, probability, or
row. The loaders make exactly one latest-attempt query per call.

When no row matches, the loaders return `None` and the reader returns an
explicit empty report: `attempt_present=False`,
`absence_reason="no_matching_attempt"`, every identity, status, gate, and
packet field `None`, both reason-code tuples empty, and all report hard flags
true. The empty report is a reported fact, not a failure or a fallback.

## Report Field Semantics

| Field | Meaning |
| --- | --- |
| `attempt_present` | True only when a latest row was projected into the report. |
| `absence_reason` | `"no_matching_attempt"` when no row matched, otherwise `None`. |
| `tea_id` | Persisted attempt identity (primary key) of the latest row. |
| `tfr_id` | Run identity the latest attempt belongs to. |
| `attempted_at` | Persisted attempt timestamp of the latest row. |
| `scope_version` | Persisted scope coordinate; `None` only in the empty report. |
| `scope_key` | Persisted scope coordinate; `None` only in the empty report. |
| `status` | Persisted row status: exactly `ready`, `watch`, or `blocked`. |
| `hard_flag` | Persisted row hard-flag value; must agree with the payload. |
| `publication_gate_present` | Whether the payload carries an external publication gate. |
| `publication_gate_status` | Gate status: `ready`, `watch`, or `blocked`; `None` when absent. |
| `reason_codes` | Node 2 result reason codes, preserved as a tuple. |
| `publication_gate_reason_codes` | Gate reason codes, reported separately from Node 2 codes. |
| `packet_presence` | Contract-derived projection state: `projected`, `suppressed`, or `None`. |
| `audit_packet_selected_side` | Always `None`; see Packet Reality below. |
| `audit_packet_forecast_probability_yes` | Audit-only canonical `P(YES)`, exposed only when projected. |

`None`, zero, and unknown are distinct values throughout; the reader never
collapses them.

## Status, Hard Flag, And Gate Evidence

- `status` is the persisted row status and must agree with the payload's
  status. The status domain is exactly `ready`, `watch`, or `blocked`;
  `pass` is not a status and disagreement between row and payload is
  rejected.
- `hard_flag` is the persisted row value and must agree with the payload.
  Required hard flags on the payload and gate must be literally true.
- `publication_gate_present` and `publication_gate_status` describe the
  payload's `run_metadata.external_publication_gate`, read only when
  present. When present, it must be an exact five-field map (`status`,
  `reason_codes`, `paper_only`, `report_only`, `readonly`) whose status is
  `ready`, `watch`, or `blocked`, whose reason codes are sorted,
  duplicate-free, and canonical, and whose hard flags are all literally
  true. A missing gate is a valid state and reports as
  `publication_gate_present=False` with `publication_gate_status=None`.
- The two reason-code tuples stay separate: `reason_codes` carries the Node
  2 result codes from `node2_result.result.reason_codes`, and
  `publication_gate_reason_codes` carries the gate codes. They are never
  merged or cross-filled.

## Packet Reality

The attempt row schema does not persist packets. `packet_presence` is a
contract-derived projection state, not proof that packet bytes were
persisted:

- `projected` when the Node 2 result status is `ready` and the publication
  gate is absent or `ready`;
- `suppressed` when the Node 2 result or the publication gate is `watch` or
  `blocked`;
- `None` when no row exists.

`audit_packet_selected_side` is always `None`. The row schema has no
`legacy_forecast_packet`, and if packet-shaped keys such as
`legacy_forecast_packet`, `selected_side`, or `forecast_probability` are
injected into the canonical payload, the reader rejects the row with
`ValueError` rather than infer or trust them.

`audit_packet_forecast_probability_yes` exposes the Node 2
`node2_result.result.publishable_probability_yes` only when
`packet_presence` is `projected`, parsed only from its canonical fixed-six
Decimal string. It is labeled audit-only canonical `P(YES)`: a probability
observation for audit, never a side recommendation or a trading signal. It
is `None` for suppressed or absent packets, and a non-ready Node 2 result
never exposes a packet probability.

## Fail-Closed Validation

For a present row, the reader rechecks the exact eight-key outer payload,
the Node 2 result schema, row/payload status agreement, row hard-flag
agreement, and required hard flags, using read-only dictionary access to
`row.evaluation_scope_payload`. It does not reconstruct Node 3 dataclasses
and does not import `TeamForecastPacket`. Missing, extra, non-dict,
noncanonical, or tampered values — including unsorted or duplicated reason
codes, noncanonical Decimal probability strings, invalid gate statuses or
flags, and injected packet-shaped fields — are rejected with `ValueError`.
Nothing is repaired, defaulted, or inferred.

## Local Supabase/Postgres Boundary

- Durable project persistence is local Supabase/Postgres only; see the
  [team evidence aggregation runbook](team-evidence-aggregation-supabase-runbook.md)
  for the schema, env surface, and latest-attempt query semantics.
- The reader introduces no new environment variable. Callers pass the
  existing `POLYMARKET_ALPHA_LAB_TEAM_EVIDENCE_AGGREGATION_DB_*` family
  (enabled flag, DSN, table) through the Node 5 adapter.
- `validate_local_postgres_dsn` runs before any connection is opened. That
  validation is owned by the Node 5 adapter, so invalid DSN input fails
  before any connection activity; this module never opens a connection
  itself.
- DSN and credential values are never printed or logged, and no credential
  material belongs in this repository.

## Phase 1 Boundary

This surface is paper-only, report-only, and readonly local paper evidence
reporting. No live trading, account authentication, wallet handling,
private-key handling, hosted account reads, order signing, order submission,
order cancellation, order replacement, or exchange/order mutation belongs on
this path, and this report does not authorize any of them.

## Post-Freeze Future Work (Deferred)

All of the following stays deferred until the settlement freeze lifts
through a separately reviewed node:

- Wiring this reader into `strategy_cycle.py` as an observability input.
  Provider configuration and dispatch remain frozen until that work is
  explicitly reopened.
- Any decision path passing this evidence into the central cost engine,
  which owns executable cost/slippage analysis and final `YES`/`NO`/`none`
  side selection. This reader never selects a side.
- Promoting a persisted packet `selected_side` into strategy authority; it
  remains an audit input only.
- Provider wiring, ranking, recommendations, trade instructions, execution,
  credentials, and order mutations, which are outside this slice.
