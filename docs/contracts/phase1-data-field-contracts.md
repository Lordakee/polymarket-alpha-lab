# Phase 1 Data Field Contracts

This contract defines the shared field, precision, hashing, safety-flag, and
local Supabase persistence boundaries for these Phase 1 data objects:

- candidate markets
- research evidence
- prediction outputs
- cost snapshots
- expert team memory
- human decision packages
- settlement feedback

It is documentation only. It does not authorize schema creation, runtime
persistence changes, CLI flags, execution/auth/live-trading changes, or
alternate durable storage.

## Object Boundary

Every object covered here is a deterministic paper/report artifact. The object
may feed operator review, readback, audit, or diagnostics, but it must not
directly place, sign, submit, cancel, replace, or size orders. It also must not
read account state, wallet material, private keys, credentials, auth tokens, or
hosted exchange mutation surfaces.

The required safety flags are part of the object identity:

```text
paper_only = true
report_only = true
readonly = true
```

Where a specialized review object also exposes `paper_review_only`, that flag
must be true and must not weaken the three hard flags.

## Decimal Contract

All numeric fields that represent probability, cost, notional, size, score,
ratio, edge, spread, slippage, cost drag, or digest rollup values must use
Python `Decimal`, not float.

### Fixed-Six Values

Most report and DB payload Decimal fields are fixed-six values:

```text
quantum = Decimal("0.000001")
```

Fixed-six fields must:

- be finite;
- not exceed six decimal places;
- be quantized with half-even behavior where the reducer defines a decimal
  context;
- serialize to JSON and JSONB as strings, such as `"0.125000"`;
- reject JSON floats during recovery.

This applies to candidate-market scores, candidate costs, forecast
probabilities, probability gaps, notional totals, readiness ratios, cost audit
summary values, memory conflict ratios, manual boundary ratios, and settlement
NAV overlay values unless the owning object explicitly defines an integral
count or a nullable optional field.

### Count Values

Counts use either nonnegative `int` or integral `Decimal`, depending on the
owning object:

- candidate research report counts are `int`;
- strategy forecast source blend counts and rollups are integral `Decimal`;
- manual final boundary counts are integral `Decimal`;
- local Supabase evidence readiness counts are integral `Decimal`;
- reason-code count maps use positive or nonnegative integer counts as defined
  by their DB row codec.

Counts must not be represented as floats. Count parity checks must tie rollups
back to rows when a report has nested rows.

### Nullable Values

Nullable Decimal fields represent unavailable evidence. They must remain null
in JSON/JSONB and must not be silently converted to zero. This matters for:

- candidate market `net_edge_per_share`, `total_cost_per_share`,
  `confidence`, `spread`, and `resolution_risk`;
- forecast `model_forecast`, `team_forecast`, `market_price`,
  `source_weighted_probability`, `blended_probability`, `disagreement_gap`,
  and `candidate_probability`;
- cost snapshot optional means, slippages, drag values, and fill rate;
- settlement overlay `share_of_exit_nav`, `timing_cost_per_share`, and
  `adjusted_net_probability_edge`.

## Timestamp Contract

All timestamp fields must be timezone-aware datetimes and must normalize to UTC
before report validation, payload generation, and DB materialization.

Timestamp fields include:

- `generated_at`
- `observed_at`
- `latest_observed_at`
- `first_marked_at`
- `last_marked_at`
- settlement watch/observation timestamps in evidence packets

JSON payloads must use ISO-8601 strings from UTC-normalized datetimes. Naive
datetimes are invalid. Source observation timestamps must not be after their
own report generation timestamp when the owning reducer enforces that ordering.

### Input-Failure Timestamp Encoding

`InputFailureDegradationReadinessReport.generated_at` is an exact timezone-aware
`datetime` in memory and is normalized to `datetime.UTC`. Its public payload is
the exact result of `generated_at.isoformat()`, for example
`2026-07-12T10:30:00+00:00`. The UTC suffix must not be shortened to `Z` because
the exact string is part of the canonical `payload_digest` input.

### Forecast-Context Time Ordering

Forecast context enforces a stronger partial order than report time alone. When
all values are present, the required chain is:

```text
published_at <= captured_at <= context_captured_at <= generated_at
```

Both `published_at` and `captured_at` must be no later than
`context_captured_at`, and every row context time must be no later than
`generated_at`. When `context_captured_at` is absent, source timestamps must
still be `<= generated_at`. Direct row/report construction and public payload
generation must recheck these boundaries after UTC normalization.

## Digest And Hash Contract

Digest fields are lowercase SHA-256 hex unless a public payload wrapper names a
field-specific derived validation digest.

Canonical digest generation uses JSON with:

```text
sort_keys = true
separators = (",", ":")
ensure_ascii = true where the owning object uses public payload digests
allow_nan = false where DB row codecs materialize payload JSON
```

### Required Digest Fields

| Object | Digest Field | Canonical Source |
| --- | --- | --- |
| Candidate research queue DB row | `report_sha256` | Full canonical `payload_json`. |
| Cost snapshot DB row | `report_sha256` | Full canonical `payload_json`. |
| Probability event screen batch triage | `digest` | Payload without `digest`. |
| Manual decision packet | payload digest helper | Public redacted packet payload. |
| Manual go/no-go packet | `payload_digest` plus source payload digests | Public go/no-go payload with `payload_digest` blank during digesting. |
| Manual final boundary report | `derived_validation_digest` | Public final boundary payload with digest blank during digesting. |
| Candidate/source conflict and memory conflict reports | derived validation digest where present | Report values excluding the digest field. |
| Input failure degradation readiness | stored `payload_digest` | Exact public payload excluding `payload_digest`; includes every `InputFailureSignal` and nested/report hard flags. |
| Probability-event market-signal risk readiness | stored `payload_digest` | Exact public payload with `payload_digest` blank during digesting; includes rows, reason-code counts, and nested/report hard flags. |

Digest validation must be strict: if materialized scalar columns disagree with
the digest source payload, the persisted row is invalid.

For both stored `payload_digest` reports, an empty digest is only a constructor
sentinel that requests deterministic computation. The constructed report stores
a lowercase 64-character SHA-256 value; direct reconstruction and public
payload access must validate it again. Every `InputFailureSignal`, market-signal
row, market-signal reason-code count, and owning report must expose
`paper_only=True`, `report_only=True`, and `readonly=True`. Tampering with a
nested hard flag changes the signed payload and must be rejected.

## Payload Contract

The payload JSON object is the canonical recovery surface for persisted report
history. Materialized scalar columns exist only for filtering, sorting, and
readback summaries.

Payloads must:

- contain exactly the schema fields supported by the owning report or DB row
  codec;
- preserve nested hard flags on report rows;
- store Decimal values as strings on the declared Decimal paths;
- reject floats;
- reject unsafe live-surface fields;
- recover to the exact immutable report dataclass or public payload wrapper
  expected by the codec.

Payloads must not include raw credentials, account identifiers, wallet
material, private keys, API tokens, hosted database URLs, raw DSNs, live order
payloads, exchange mutation requests, raw source archives, or unredacted source
references.

## Object-Specific Persistence Boundaries

### Candidate Markets

Candidate market history is persisted only as deterministic
`PaperStrategyCandidateResearchQueueReport` snapshots in local
Supabase/Postgres when the dedicated DB environment family enables that
surface.

Default table:

```text
paper_strategy_candidate_research_queue_reports
```

Allowed persisted fields:

- `report_sha256`
- `generated_at`
- `config_version`
- `source_config_version`
- `action_status`
- `recommended_next_step`
- `research_status`
- candidate, research, watch, blocked, selected, skipped, and not-selected
  counts
- `total_ready_notional`
- `total_selected_notional`
- `total_suggested_notional`
- `top_research_priority_score`
- `average_research_ready_score`
- `source_reason_code_counts_json`
- `primary_reason_code_counts_json`
- `reason_codes_json`
- `rows_json`
- `payload_json`
- hard safety flags

Decimal JSON paths in `payload_json` and `rows_json` must use fixed-six strings.

### Research Evidence

Research evidence may be stored as local report evidence only when a specific
paper/report surface has an approved local Supabase/Postgres adapter and DSN
environment family. Evidence persistence must remain a readback/report-history
boundary, not a raw-source archive.

Allowed durable evidence is limited to redacted public identifiers, source
families, evidence types, observed UTC timestamps, relevance or severity
ratios, public notes, rule mappings, ambiguity status, reason codes, row
rollups, canonical payloads, and hard safety flags.

Raw source text, raw HTML, screenshots, private URLs, credentials, account
state, or live exchange payloads are outside this contract.

### Prediction Outputs

Prediction output persistence, when introduced for a covered surface, may store
only paper/report forecast diagnostics:

- candidate IDs;
- model/team/market/source probabilities;
- source reliability weights;
- source count and reliability rollups;
- blended probability;
- disagreement gaps and caps;
- candidate probability;
- probability sanity rows and report rollups;
- UTC observation/generation timestamps;
- reason codes;
- canonical payloads and hard safety flags.

Prediction outputs are not live trading signals. Persisted prediction outputs
must not include order sizing, authorization state, live account data, private
market access, or exchange mutation instructions.

### Cost Snapshots

Cost snapshots are persisted through the local Supabase/Postgres
`paper_trade_cost_audit_reports` surface.

Default table:

```text
paper_trade_cost_audit_reports
```

Allowed persisted fields are the cost audit DB row fields:

- `report_sha256`
- `generated_at`
- `config_version`
- trade count and fill counts
- requested and filled size totals
- optional fill rate
- optional mean theoretical and cost-adjusted edge
- optional mean and total cost drag
- optional mean research and fill slippage
- optional largest single-trade cost drag
- `payload_json`
- hard safety flags

The cost snapshot surface stores paper cost evidence only. It is not a trade
journal expansion point, execution queue, or order mutation surface.

### Expert Team Memory

Expert team memory persistence is local report-history evidence for team memory
readiness, diagnostics, and specialist memory conflict summaries.

Default table for the readiness digest surface:

```text
team_memory_readiness_digest_reports
```

Allowed persisted fields include generated timestamps, config versions, digest
status, recommended next step, team/status counts, source status rows, source
config versions, reason-code counts, reason codes, canonical payload, and hard
safety flags.

Specialist memory conflict objects may be persisted only if the specific
surface defines an approved local Supabase/Postgres history adapter. They must
store public team/specialist identifiers, case-family keys, integral case
counts, fixed-six ratio scores, derived memory conflict status, reason codes,
digest fields where present, canonical payload, and hard safety flags.

### Human Decision Packages

Human decision packages are public redacted operator-review packets. They may
be materialized as payloads and digests for audit/readback, but must not become
authorization records for execution.

Allowed persisted or digestable fields:

- UTC `generated_at`
- config version
- checklist area statuses
- public redacted reason summaries
- public unresolved blockers
- next manual review action
- go/no-go status and review statuses
- source payload digests
- public output safety status
- manual final boundary counts, ready ratio, selected side, final status, and
  derived validation digest
- hard safety flags

Manual packets must reject unsafe text terms and references. They must not store
raw candidate IDs, market URLs, source links, DSNs, credentials, order terms,
wallet material, account state, or private execution instructions in public
reason text.

### Settlement Feedback

Settlement feedback persistence, when used for a covered surface, is local
paper/report evidence for settlement timing, evidence quality, settlement delay
risk, and NAV settlement overlay diagnostics.

Allowed persisted fields:

- condition and market identifiers;
- token counts and paper NAV exposure amounts;
- settlement timing status;
- timing cost per share;
- adjusted net probability edge;
- UTC generated, observed, and marked timestamps;
- settlement row and exposure row counts;
- status counts;
- exit value rollups;
- blocked/missing settlement NAV share;
- configured max blocked settlement exposure share;
- reason codes;
- canonical payload and hard safety flags.

Settlement feedback must not settle outcomes, mutate NAV, mutate balances,
create or alter orders, submit exchange actions, or change source-of-truth
market data.

## Local Supabase Persistence Boundary

Local Supabase/Postgres is the only approved durable persistence boundary for
project data. A covered object may be persisted only when all of these are true:

1. the specific surface has an approved local Supabase/Postgres persistence
   adapter or DB row codec;
2. persistence is default-off and enabled by that surface's environment family;
3. the raw DSN comes from process environment only;
4. the raw DSN passes the local Postgres DSN validator before any connection is
   opened;
5. the table name is a simple allowed local Postgres identifier;
6. the row preserves canonical payload, digest/hash, Decimal string, timestamp,
   row-count, and hard-flag checks.

The persistence boundary explicitly excludes:

- hosted Postgres or any hosted database assumption;
- SQLite, DuckDB, Redis, MongoDB, SQLAlchemy-managed engines, ORM abstraction
  layers, generic database abstraction layers, and file-backed durable stores;
- JSONL/CSV/filesystem journals as new durable substitutes;
- DSN CLI flags, sample DSNs, checked-in credentials, logs containing raw DSNs,
  or exception messages that expose raw connection material.

## Readback Contract

Readback paths must reconstruct immutable report objects or public payload
wrappers from canonical payload JSON. Readback may summarize history, latest
status, reason-code counts, duplicate-latest signals, and hard safety flags.

Readback must not:

- recommend live trades;
- tune live strategy weights;
- size positions for execution;
- authenticate exchange clients;
- read exchange accounts;
- construct, sign, submit, cancel, replace, or mutate orders;
- mutate external systems.

## Documentation Scope

This contract documents current object boundaries and expected field behavior.
Any future implementation that adds or changes persistence for these objects
must update this document and the data dictionary in the same change, while
still preserving Phase 1 paper-only, report-only, readonly boundaries unless a
separate explicitly approved phase changes that boundary.
