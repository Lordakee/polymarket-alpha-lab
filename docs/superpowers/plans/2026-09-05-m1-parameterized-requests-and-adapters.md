# M1 Stage Plan: Parameterized Requests And Source Adapters

Date: 2026-09-05
Stage: M1 of the [Project Delivery Plan](../../roadmap/2026-09-05-project-delivery-plan.md)
Status: plan review completed; findings dispositioned (see the final section)
Depends on: M0 (accepted; baseline `72d0a23a`)

## Parent-Plan Traceability

This stage implements the M1 milestone: typed per-source request parameters,
transport support for validated queries, bounded pagination, official
Polymarket adapters (Gamma markets, CLOB books), one registered public BTC
source, retry/rate-limit outcomes, and raw-before-normalized persistence
ordering. Data API account-oriented surfaces stay out. M2 bundle/dispatch
and M3 vertical-slice wiring are explicitly out of scope.

## Current-Code Facts

- `SourceDefinition.url_template` is concrete; `_validate_url_template`
  rejects query strings, placeholders, ports, and credentials.
- `CentralDataRequest.url` is template-validated, so any URL with a query
  is currently unrepresentable; `SafeGETTransport.fetch` additionally
  requires `request.url == source_def.url_template`.
- `SafeGETTransport` already enforces HTTPS exact-host allowlists, injected
  resolver with public-address checks, peer-IP pinning, redirect/proxy
  refusal, credential header refusal, content-type/encoding checks,
  bounded streaming reads, timeouts, and 1-3 attempts.
- The persistence policy flags URLs matching sensitive patterns
  (including a bare `id=` query parameter), so parameter NAMES must be
  chosen to stay inside the policy; the policy remains authoritative.
- `central_data_normalization.py` provides bounded JSON/RSS/XML parsing
  with Decimal-only numerics and strict error codes.
- Registry default sources: `polymarket_gamma_markets`
  (`/markets`, freshness 300 s), `polymarket_clob_book` (`/book`,
  freshness 30 s), `polymarket_data_trades` (deferred by this stage).

## Design Decisions

1. Query strings become typed data, not relaxed URL parsing.
   `CentralDataRequest` gains an optional canonical `query` mapping
   validated by name/value charset rules; the `url` stays the registered
   template. The transport composes template + canonical query through a
   dedicated `_validate_composed_query_url(template_url, query_mapping)`
   that: (a) percent-encodes with the canonical encoder; (b) requires the
   composed URL's scheme/host/path to equal the template's exactly;
   (c) rejects any percent-encoding inside the path or values that does
   not round-trip byte-identically through split/encode/decode; and
   (d) permits a query component only through this function.
   `_validate_request_url` keeps rejecting queries for template URLs;
   the fetch path accepts the template alone or a composed URL that
   re-encodes to exactly the same string. Validation happens twice by
   design: spec-layer name/value checks before composition, canonical
   round-trip after composition.
2. Parameter specifications live in the registry, not in callers. A new
   pure `RequestParamSpec` (typed: pattern-string, bounded-int, or enum;
   optional; bounded length) is attached to `SourceDefinition` via a new
   optional `query_params` tuple (default empty, backward compatible).
   `build_request_query(source_def, params)` validates names/types against
   the spec, rejects unknown parameters, applies a spec default when an
   optional parameter is omitted (a spec without a default is required and
   its omission raises `ValueError`), and returns the canonical query
   mapping. Canonical order is sorted-by-name so identical requests from
   different call sites produce one identity hash (dedup and replay).
   Spec-layer names are validated against a hard-coded reserved set
   (`id`, `uid`, `user_id`, `account_id`, `wallet`) that would trigger
   the persistence policy's sensitive-URL regex, so misconfiguration
   fails at registration time, not after a network round-trip; the
   persistence policy itself remains authoritative at persist time.
3. Parameter names are chosen to avoid the persistence policy's sensitive
   URL patterns (use `condition_id`/`slug`/`token_id`/`limit`/`offset`,
   never bare `id`/`uid`/`user_id`/`account_id`/`wallet`). This is an
   invariant test, not a convention comment.
4. Pagination is an explicit budget with a typed outcome.
   `PaginationPolicy(max_pages, items_per_page_range)` is defined per
   source in the registry layer; the fetch orchestration walks pages until
   exhausted or budget hit. `FailureStatus` gains
   `PAGINATION_BUDGET_EXHAUSTED = "pagination_budget_exhausted"`, used
   only on the acquisition-level `AcquisitionOutcome.failure_status`;
   every persisted raw/normalized row from a successful page keeps
   `failure_status="none"`, and the database CHECK constraints are
   unchanged because that value is never bound to a persisted row.
   Budget exhaustion is never silent truncation.
5. Adapters are pure and clock-free: freshness derives entirely from the
   raw row. `GammaMarketsAdapter` and `ClobBookAdapter` (plus the Kraken
   ticker adapter) map a `RawEventRow` plus its `SourceDefinition` to
   `NormalizedObservationRow` tuples using existing normalization
   helpers. Freshness is `(retrieval_time - observation_time) <=
   freshness_policy_seconds`, where `retrieval_time` comes from the raw
   row and `observation_time` is parsed from the payload or defaults to
   `retrieval_time`. There is no injected clock at all, so re-parsing the
   same row is deterministic by construction. Unknown shapes, missing
   fields, or Decimal-unsafe numerics produce `parse_state=failed/unknown`
   rows with reason codes instead of fabricated values.
6. One public BTC source is registered: Kraken public Ticker
   (`https://api.kraken.com/0/public/Ticker`, query `pair=XBTUSD`),
   unauthenticated GET JSON. `freshness_policy_seconds` is a conservative
   300 because the provider documents no update guarantee; the value is
   retuned in M4 only with smoke-run evidence. Provider availability is
   not claimed until the optional smoke runs; fixture tests are
   authoritative.
7. Persistence ordering is raw-first within a caller-owned transaction.
   `acquire_once` receives an already-constructed `CentralDataStore`
   bound to the caller's connection; it performs `insert_raw_event`
   first, then inserts normalized rows, and never commits or rolls back —
   transaction boundaries belong to the caller (matching the Node B
   `_write` boundary that would wrap it in production). Policy-refused
   responses are rejected by the row codec before any store call; the
   acquisition tests assert the raw-then-normalized call order with a
   fake store and assert that refused responses produce no store calls.
8. Retries: the transport keeps its 1-3 attempt budget; the orchestrator
   adds an injected-sleep backoff between attempts for retryable
   statuses (timeout/network). `retry-after` parsing accepts integer
   seconds only (HTTP-date is rejected), clamped to a maximum of 300
   seconds; a value above the clamp (or an unparseable one) fails the
   acquisition immediately with reason code `rate_limit_exceeded` and no
   retry, recording the clamped/unparseable detail. Retry-after delays
   are inter-attempt waits and never consume the pagination budget. No
   unbounded retry loops exist.

## Work Items

### 1. `src/polymarket_alpha_lab/central_data_request_params.py` (new)

`RequestParamSpec` (name; kind: `pattern`/`int_range`/`enum`; required;
default; max length), `build_request_query(source_def, params) -> Mapping`,
`canonical_query_string(query) -> str`, `request_query_identity(source_id,
query) -> str` (SHA-256 over the canonical string). Pure module; no stdlib
beyond hashlib/re/urllib.parse quoting.

### 2. Contract/transport extensions (edits)

- `central_data_contracts.py`: `CentralDataRequest.query` optional mapping
  with canonical name/value validation (names `[a-z0-9_]{1,32}`, values
  percent-encodable, no whitespace/control chars, bounded length).
- `central_data_transport.py`: compose and re-validate template+query;
  allow the fetch URL to be template or template+canonical query; keep
  every existing protection. Query values never come from user strings
  unvalidated.
- `central_data_registry.py`: attach `query_params` specs and pagination
  policies to the two Polymarket sources; register the Kraken source and
  `crypto_btc` requirement adjustments (families stay as configured).

### 3. `src/polymarket_alpha_lab/central_data_source_adapters.py` (new)

Pure adapters `parse_gamma_markets(raw_row) -> tuple[NormalizedObservationRow, ...]`
and `parse_clob_book(raw_row) -> ...`, plus `parse_kraken_ticker(raw_row)`.
Each validates its documented JSON shape (fixture-derived), computes
freshness via the source policy with an injected `now`, preserves
null/zero/unknown distinctions, and emits reason codes such as
`schema_drift`, `missing_required_field`, `numeric_not_decimal`.

### 4. `src/polymarket_alpha_lab/central_data_acquisition.py` (new)

`AcquisitionOutcome` carries exactly: `source_id`, `request_identity`,
`raw_result: CentralDataInsertResult`, `normalized_rows:
tuple[NormalizedObservationRow, ...]`, `failure_status: FailureStatus`,
`reason_codes: tuple[str, ...]`, `attempts: int`, `retry_after_seconds:
int | None`, `pages_fetched: int`. `acquire_once(source_def, params,
transport, store)` builds the query, fetches, applies the persistence
policy, inserts raw first, then normalized rows, inside the caller's
transaction (no commit/rollback here). `acquire_paginated(...)` walks the
pagination budget. Backoff sleep is injected; default no-op for tests.
No environment or psycopg import; the store is the DB-API boundary from
Node B.

### 5. Tests (new)

- `tests/test_central_data_request_params.py`: spec validation, unknown
  parameter refusal, missing-required refusal, canonical ordering,
  identity stability, sensitive-name invariant (bare `id`/`uid`/
  `user_id`/`account_id`/`wallet` must be rejected by the spec layer).
- `tests/test_central_data_transport.py` (extend the existing file):
  template+query composition, non-canonical encoding rejection, query on
  a source without specs refusal, all prior protections still passing.
- `tests/test_central_data_source_adapters.py`: happy-path fixtures for
  the three adapters; schema-drift cases defined as (a) missing required
  field -> `parse_state=failed` with `missing_required_field`, (b)
  unexpected extra fields ignored for forward compatibility, (c) type
  mismatch (string where a Decimal is expected) -> `parse_state=failed`
  with `type_mismatch`; null vs zero vs unknown; non-Decimal numerics;
  oversized nesting; freshness fresh/stale derived deterministically from
  the row's own `retrieval_time` (identical re-parse outcome).
- `tests/test_central_data_acquisition.py`: fake transport + fake store;
  raw-before-normalized ordering assertion via call-order recording;
  policy-refused response produces zero store calls; retry/backoff
  attempt counting; retry-after values 0, 60, 300 schedule or clamp as
  specified and 301/999999/non-numeric fail immediately with
  `rate_limit_exceeded`; pagination budget exhaustion produces
  `failure_status=PAGINATION_BUDGET_EXHAUSTED` on the outcome while all
  persisted rows keep `failure_status="none"`; deterministic replay
  (same fixtures, same identities).

### 6. Optional real smoke (documented, not default)

Reuse the M0 pattern: an opt-in marker test (env-gated, no DSN required)
that fetches one Kraken ticker and one Gamma markets page through the real
transport and records status only. It must never run in the default suite.

## Verification

Recorded results (2026-09-05):

- Focused central-data suites: 97 passed (request params, adapters,
  acquisition, transport incl. parameterized additions, registry,
  contracts, db rows, normalization, policy, store, psycopg).
- Network smoke gate verified skipped by default; one enabled run passed
  (`1 passed in 1.25s`): Kraken ticker (`pair=XBTUSD`) and a Gamma page
  (`limit=1`) both answered through the real `SafeGETTransport` with
  canonical query composition.
- In-memory compile checks for every changed Python file; `git diff
  --check` clean; credential-pattern scan of changed files clean.
- Full Python 3.11 regression: recorded in the stage hard-review prompt
  once completed (see below).
- No production changes outside the four src files listed; no CLI changes;
  no new migration.

Original verification requirements (all satisfied by the above):

- Focused: the four new/extended test files green.
- Full regression on Python 3.11; compile checks; `git diff --check`;
  credential-pattern scan over changed files.
- Registry snapshot test: default registry still contains exactly the
  documented sources and requirements after edits.
- No production changes outside the four src files listed; no CLI changes.

## Acceptance Criteria (mirrors delivery-plan M1 exit)

1. Deterministic fixture adapters yield source-bound normalized
   observations with provenance preserved and no fabricated values.
2. Parameter abuse (unknown, missing-required, wrong type, sensitive
   names), non-canonical encodings, and pagination exhaustion all have
   negative tests.
3. Parser/version changes surface as parse-state/reason-code outcomes,
   not exceptions or invented values.
4. Raw-first persistence ordering is asserted; refused payloads never
   reach SQL.
5. Transport protections from Node A remain intact (existing transport
   tests unchanged and passing).
6. The optional network smoke is env-gated and off by default; its
   absence does not reduce acceptance because fixtures are authoritative.

## Rollback

Revert the six work items; no data or schema depends on them (no new
migration in this stage).

## Plan Review Response (2026-09-05)

Claude Code reviewed this plan read-only (`claude-opus-5`, effort `max`)
and returned REQUEST_CHANGES: three BLOCKER, four MAJOR, four MINOR, two
actionable NIT findings. Dispositions:

1. BLOCKER "composed URL always fails `_validate_request_url`": the
   premise misread work item 2 (transport edits were already in scope),
   but the requested precision is adopted: a dedicated
   `_validate_composed_query_url` with template-equality, canonical
   round-trip, and path-encoding checks is now specified, and
   `_validate_request_url` keeps rejecting queries for plain templates.
2. BLOCKER "bare `id` passes spec validation and fails only post-fetch":
   ACCEPTED; `RequestParamSpec` now validates names against a hard-coded
   reserved set so registration fails fast, while the persistence policy
   stays authoritative at persist time.
3. BLOCKER "pagination exhaustion not bound to a typed outcome":
   ACCEPTED; `FailureStatus.PAGINATION_BUDGET_EXHAUSTED` is added for
   acquisition-level outcomes only, persisted rows keep `none`, and the
   database CHECK constraints stay unchanged because the value is never
   bound to a row.
4. MAJOR raw-first transaction boundary: ACCEPTED; `acquire_once` takes
   the caller's store, never commits/rolls back, and tests assert
   call order with a recording fake store.
5. MAJOR retry-after safety: ACCEPTED; integer seconds only, 300-second
   clamp, immediate `rate_limit_exceeded` failure above the clamp or on
   unparseable values, no budget consumption.
6. MAJOR freshness clock: ACCEPTED and strengthened; adapters take no
   clock at all and derive freshness from the row's own timestamps.
7. MAJOR Kraken freshness: ACCEPTED; conservative 300 seconds pending
   M4 smoke evidence.
8. MINOR test-file naming: ACCEPTED (extend the existing transport test
   file).
9. MINOR default semantics: ACCEPTED (omit applies default; no default
   means required).
10. MINOR sorted-order rationale: ACCEPTED (documented).
11. MINOR AcquisitionOutcome schema: ACCEPTED (explicit field list).
12. NIT title: ACCEPTED ("Node C0/C1" removed).
13. NIT module naming: no action needed per the reviewer's own analysis.
14. NIT schema-drift definitions: ACCEPTED (three concrete drift cases).
