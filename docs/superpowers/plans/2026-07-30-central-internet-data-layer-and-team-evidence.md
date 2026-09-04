# Central Internet Data Layer and Ten-Team Evidence Integration

Date: 2026-07-30

Status: Approved with minor fixes adopted from the 2026-07-30 Claude Code
plan review. Node A is now ready for the separately gated OpenCode execution
handoff. The review used `claude-opus-5` with effort `max`.

## Goal

Give the ten specialist teams centrally collected public evidence. Teams remain
pure forecast/evidence consumers and do not browse the internet themselves.
The central layer must collect Polymarket public data plus allowlisted public
internet data, preserve raw responses and provenance, normalize observations,
and distribute typed evidence into the existing team forecast/evidence packet
contract.

The result remains Phase 1 paper-only, report-only, and readonly. This work is
research data infrastructure, not a trading or account integration.

## Current Baseline

- `src/polymarket_alpha_lab/api.py` has a minimal read-only Gamma market and
  CLOB order-book client; it does not retain raw payloads or provenance.
- `TeamForecastEvidencePacket` already carries `source_id`, `source_type`,
  `data_timestamp`, `data_freshness_seconds`, evidence text, weight, and
  reason codes.
- The ten team forecast builders are pure supplied-input functions. They do
  not have network clients or a shared central dispatch path.
- Local Supabase/Postgres is the only approved durable persistence target.
- The existing source-quorum and source-reliability reports provide useful
  status vocabulary but are not an acquisition service.

## Binding Rules

- Use official Polymarket Gamma, CLOB, and Data API sources first for
  Polymarket fields. A later reviewed node may add the market WebSocket
  channel. Public internet sources are additive and must be explicitly
  registered.
- Public internet access is GET-only, unauthenticated, HTTPS-only, host-
  allowlisted, size-limited, rate-limited, and observable. Do not add API-key,
  cookie, login, browser automation, wallet, account, private-key, or order
  surfaces.
- Node A's transport disables automatic redirects and returns redirect
  responses to the caller. If a later node enables a redirect, every hop and
  the final URL must repeat HTTPS, exact-host, credential, and resolved-IP
  validation. Hostnames are resolved through an injected resolver before
  connection; loopback, RFC1918, link-local, ULA, multicast, metadata, and
  other non-public addresses are rejected, environment proxies are disabled,
  and a resolver/connection mismatch fails closed. Resolved addresses are
  canonicalized before the check: IPv4-mapped IPv6 values in `::ffff:0:0/96`
  are mapped back to IPv4 (or rejected as non-public), so mapped RFC1918,
  loopback, link-local, and metadata addresses cannot bypass the blocklist.
- Website scraping is a constrained, later fallback for a registered public
  source, never the default path when an official API exists. HTML parsing must
  be isolated behind a separately reviewed source adapter and must emit parse
  status and raw payload hash.
- Save raw API/web payloads before normalization. Every observation records
  source id/family, retrieval time, content time when known, status, payload
  hash, freshness, parse state, and a reproducible evidence reference.
- Raw bytes are an internal-only persistence input, never a public report field
  or durable file. Node B must reject responses over 2 MiB, retain accepted raw
  payloads for at most 30 days, and refuse/redact credentials, auth headers,
  cookies, API keys, private keys, wallet/account identifiers, email addresses,
  phone numbers, and direct user identifiers before local Postgres persistence.
  Public entity names, team names, athlete names, and market metadata are not
  classified as PII for this research surface. Public payloads expose only
  redacted provenance and hashes. Raw-byte SHA-256 is the identity for every
  media type; JSON canonical digests and parser versions are additional fields,
  not replacements for the raw-byte hash.
- Preserve the distinction between `null`, numeric zero, and `unknown`.
- Durable data and raw payloads go only to local Supabase/Postgres. Do not add
  SQLite, JSONL/file journals, Redis, Mongo, hosted databases, or a generic
  persistence abstraction.
- All typed artifacts carry `paper_only=True`, `report_only=True`, and
  `readonly=True` and reject unsafe live-surface fields.
- Pure reducers and adapters must not import environment, psycopg, or network
  clients. Network and database work stays at central boundary modules.
- Each node has a focused plan review and a result review. Review prompts are
  read-only and go directly to local Claude Code with `claude-opus-5`, effort
  `max`, fast mode off, and no elapsed-time timeout. There is no fallback
  reviewer.
- After Claude approves the plan, Codex will revise the final execution plan
  if needed and delegate implementation to OpenCode with model `grok-4.5` and
  thinking level `high`. OpenCode may edit only its assigned files and may not
  commit, push, access secrets, or bypass the Phase 1 boundary.

## Scope and Node Split

The work is split into independently reviewable nodes. Within the approved
wave, central work and team adapter work run in parallel with disjoint file
ownership. A node cannot begin implementation before its own plan review.

### Node A: Central acquisition contracts and safe transport

Add the pure contracts and central boundary needed by all later nodes:

- `central_data_contracts.py`: immutable request, source definition, raw
  response, normalized observation, evidence reference, freshness, parse state,
  and failure/status enums. Include canonical serialization and SHA-256
  payload identity without floats.
- `central_data_transport.py`: a standard-library GET transport protocol and
  implementation that validates HTTPS/host allowlists, rejects credentials and
  private/local destinations, disables automatic redirects and environment
  proxies, validates every injected DNS result before connection, applies a
  streaming response-size cap of `<=2 MiB` plus timeout/attempt limits, and
  returns raw bytes plus
  retrieval metadata. Tests use a fake resolver and fake transport; Node A
  performs no real network, database, cache, or file write.
- `central_data_registry.py`: explicit source registry and team-to-source
  requirements. Registry entries state source family, allowed host, endpoint
  template, content type, freshness policy, and whether the source is official
  Polymarket API or public-internet fallback.
- `source_family` is a stable provider/lineage identifier: API versions,
  mirrors, and subdomains from the same provider share one family and cannot
  satisfy independent-family quorum twice. The initial registry sets
  `minimum_current_source_families=1` for every team; raising a team's quorum
  is a later reviewed policy change.
- Extend `api.py` only through the central transport/response contract; retain
  existing public method behavior and add Gamma/CLOB/Data public read methods
  only when they can return the new provenance-bearing result without breaking
  callers.

Focused tests cover GET-only/no-body behavior, exact-host HTTPS allowlists,
credential/userinfo/query/fragment rejection, redirect blocking, injected DNS
resolution, IPv4-mapped IPv6 normalization, private/loopback/link-local/
metadata rejection, resolver/connection mismatch, proxy bypass, streaming
response-size and timeout/attempt limits, raw-byte hashing, timestamp
normalization, null/zero/unknown semantics, registry validation, and Phase 1
forbidden-surface scope.

Node A keeps the existing `UrlopenTransport` and `PolymarketPublicClient`
behavior backward compatible for current callers, but marks that path as a
legacy compatibility surface. The central registry/dispatch never accepts its
arbitrary `base_url` or its unlimited `response.read()` path; migrating current
callers is a later node with its own review.

### Node B: Raw payload persistence and normalization

- Add one Supabase migration for raw response acquisition events, normalized
  observations, and redacted retention audit rows. Raw-byte SHA-256 is indexed
  provenance and intentionally non-unique; a deterministic source-bound event
  identity is the idempotency key, and conflicts are field-compared rather than
  silently discarded.
- Add a central DB-API store and psycopg boundary following existing local-DSN
  validation and redaction patterns. Reads and writes are explicit central
  evidence persistence operations; no generic store abstraction.
- Add normalization helpers for JSON/RSS adapters. The
  normalized model must retain the raw payload reference and mark unresolved,
  stale, contradictory, and parse-failed values instead of silently coercing
  them.
- Define an internal value shape that distinguishes `null`, numeric zero, and
  `unknown`. Node C's frozen evidence bundle, not Node B persistence, owns the
  downstream `TeamForecastEvidencePacket` placeholders: a required source item
  that is missing, stale, parse-failed, unknown, or quorum-blocked emits exactly
  one canonical zero-weight placeholder/reason code and structured availability
  for Node E to block forecast use. Node B stores the parse/value/freshness
  states and never fabricates a packet or probability impact.
- Add schema/store tests for idempotency, ordering, filters, malformed payloads,
  DSN validation before psycopg import/connect, cleanup, hard flags, the 2 MiB
  raw-response cap, 30-day retention metadata, and credential/PII refusal or
  redaction.

### Node C: Central source adapters and evidence distribution

- Implement official Polymarket adapters for Gamma market metadata, CLOB
  books/prices/history, and Data API public activity. No account or trading
  endpoints are permitted; market-channel/WebSocket snapshots are deferred to
  a later reviewed node.
- Implement a registered public-internet adapter for JSON/RSS public sources.
  It must use the same transport, provenance, freshness, parse, conflict, and
  raw-payload contracts as official sources. HTML parsing and WebSocket
  snapshots are explicitly deferred until a later plan review; no browser or
  streaming dependency is part of the first central adapter node.
- Implement `central_evidence_dispatch.py`: accept a market/team request,
  select registered sources, fetch/normalize centrally, apply source-family
  independence and freshness policy, and return deterministic per-team
  evidence bundles. A registry source has a canonical `source_family`; the
  initial ten-team policy requires at least one current source family and one
  current source per required item, while tracking additional families for
  corroboration. If a configured requirement is not met, dispatch returns a
  `blocked` bundle with `source_quorum_not_met` and zero-weight placeholders;
  it never silently promotes a single source. Teams receive bundles; they
  never receive a network client.
- Add central dispatch tests for source selection, deduplication, conflict
  reporting, stale/missing source handling, reproducibility, and all ten team
  ids.

### Node D: Ten team evidence adapters (parallel lanes)

Each adapter is a pure module with a paired test file. It consumes a central
evidence bundle and emits team-specific `TeamForecastEvidencePacket` rows (and
the supplied-input shape expected by that team's existing forecast builder).
No adapter imports `urllib`, `requests`, browser tooling, environment, psycopg,
or a credential-bearing client.

Required evidence families:

| Team | Central evidence requirements |
| --- | --- |
| `politics` | election calendar/rules, official results or certification, polling, policy/news events |
| `crypto_btc` | BTC spot/derivatives, ETF flows, volatility, macro/liquidity context |
| `crypto_eth` | ETH spot/relative value, ETF/staking/ecosystem events, volatility/network context |
| `macro_rates` | economic calendar, inflation/employment, Fed/rates pricing, bond and macro-surprise data |
| `equity_indices` | index/ETF/futures, breadth, earnings calendar, index volatility and macro context |
| `commodities_gold` | gold spot/futures, USD and real rates, inflation, geopolitical events |
| `commodities_oil` | crude spot/futures, OPEC/supply, inventory/demand, shipping/geopolitical events |
| `sports_soccer` | fixtures/results, standings/form, lineups/injuries, odds consensus, competition rules |
| `sports_basketball` | schedule/results, matchup/team strength, injuries/rotation, fatigue, odds consensus |
| `sports_other` | sport-specific schedule/results/rankings, conditions/injuries, odds, resolution rules |

The ten adapters are developed in parallel groups with non-overlapping files:

- Lane D1: politics, crypto BTC, crypto ETH.
- Lane D2: macro rates, equity indices, commodities gold.
- Lane D3: commodities oil, sports soccer, sports basketball, sports other.

The adapter contract must make absent, stale, contradictory, and unknown
evidence visible through reason codes and source references. It must not invent
values or silently promote a single source when the configured quorum requires
independent corroboration.

### Node E: Forecast integration and orchestration

- Wire central bundles into all ten existing team workflows while preserving
  their pure builder signatures where possible. Add a single paper/report/
  readonly orchestration entry point that can run one market or a batch.
- Add deterministic evidence-to-forecast packet assembly, source references,
  freshness scoring, and DB-row conversion through existing codecs.
- Keep market microstructure, cost-aware edge, recommendation, risk, paper
  allocation, and outcome scoring in the central layer. Team adapters only
  prepare domain evidence and forecast inputs.
- Add end-to-end tests from fake central responses through each team adapter,
  `TeamForecastEvidencePacket`, `TeamForecastPacket`, and local persistence.

### Node F: Documentation, verification, and release gate

- Update team framework and runbooks to state that teams consume central
  evidence and cannot browse independently.
- Add source catalog, freshness/quality policy, operator failure handling, and
  Phase 1 safety documentation.
- Run focused tests, full `pytest`, `compileall`, `git diff --check`, secret
  scan, CodeGraph sync/status, and an external Claude Code result review.
- Commit and push only the reviewed, verified node. Do not push partial waves.

## Ownership and Parallel Execution

Before each implementation wave, assign exclusive file ownership. The central
lane owns Nodes A-C and shared orchestration files; D1-D3 own only their team
adapter modules/tests; a verification lane owns no production files. Agents
must reclaim completed/blocked handles promptly and redeploy capacity to the
next independent lane. No fixed coordinator-side subagent count is assumed.

The first post-approval execution wave is Node A alone so its security and
tri-state contracts can receive a result review. After Node A's result review,
Node B/C and the three Node D lanes may run concurrently against the frozen
contracts with disjoint files. This preserves parallel central/team
development without letting teams guess an unstable evidence shape.

## Acceptance Criteria

- A team can obtain all required public evidence through the central layer
  without performing network access itself.
- Official Polymarket data and registered public-internet data share one
  provenance/raw-payload/freshness/conflict contract.
- Every observation is reproducible from its source id, request parameters,
  retrieval/content timestamps, raw payload hash, and parser version.
- Missing, stale, contradictory, `null`, `0`, and `unknown` values remain
  distinguishable in team evidence packets.
- All ten teams have tested adapters and central dispatch coverage, while the
  existing pure forecast builders remain usable with supplied inputs.
- No live trading, auth, wallet, private key, account, order, or exchange
  mutation path is introduced.
- Durable persistence is local Supabase/Postgres only and raw payloads are not
  written to files as a durable substitute.
- Focused and full verification passes; CodeGraph is current; Claude Code
  result review reports no unresolved Critical or Important findings; the
  reviewed commit is pushed to GitHub.

## Risks and Decisions for Claude Review

1. Confirm the initial public-source catalog. The implementation must not
   assume credentials for sources whose public endpoint policy is unclear;
   those sources stay registry-configured and blocked until an unauthenticated
   endpoint is verified.
2. Confirm the initial `minimum_current_source_families=1` policy and the
   blocked-bundle/zero-weight placeholder behavior. A later node may raise
   per-team quorum thresholds only through a new reviewed plan.
3. Confirm the exact internal-only raw payload retention/redaction policy in
   Node B before any durable write is implemented.
4. Confirm the explicit deferral of HTML, browser, and WebSocket acquisition;
   the first adapter node is JSON/RSS plus official HTTP APIs only.

## Review Gate

Submit this document and the current baseline files to local Claude Code with a
read-only prompt. The prompt must request a verdict of `Proceed` or `Blocked`,
list Critical/Important/Minor findings, and explicitly check Phase 1 safety,
local Supabase-only persistence, provenance/reproducibility, source allowlists,
team isolation, ownership conflicts, testability, and whether the node split is
small enough for one review per node. Do not begin implementation until the
verdict is accepted. After acceptance, Codex will record any adopted changes in
the final execution plan and hand the approved node to OpenCode
(`grok-4.5`, `high`) for implementation.

## Plan Review Record

- 2026-07-30 initial review: output was incomplete and contained four
  Important findings; implementation remained blocked.
- 2026-07-30 compact Revision 1 review: `Blocked`; Critical 0, Important 1,
  Minor 3. The Important finding was the missing explicit IPv4-mapped IPv6
  normalization requirement.
- 2026-07-30 compact Revision 2 review: `Proceed with fixes`; Critical 0,
  Important 0, Minor 3. All three non-blocking findings were adopted above:
  the `<=2 MiB` transport cap, exact placeholder/reason-code mapping, and the
  documentation typo correction. No implementation started before this gate.
