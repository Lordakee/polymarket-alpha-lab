# Node A OpenCode Execution Handoff

Date: 2026-07-30

This is the Codex-approved execution plan after the Claude Code pre-stage plan
review recorded in
`.superpowers/reviews/2026-07-30-central-internet-data-layer-plan-review-r2.md`.
The adopted plan is the parent document
`docs/superpowers/plans/2026-07-30-central-internet-data-layer-and-team-evidence.md`.

## Executor

- External OpenCode process, not a Codex subagent or reviewer.
- Model: `grok/grok-4.5`.
- Variant/thinking effort: `high`.
- OpenCode may edit only the exclusive files listed below. It must not commit,
  push, modify project rules/plans, read secrets, use credentials, access
  accounts/wallets, or add live/order/exchange mutation paths.
- No real network, database, cache, or file-backed raw-payload write is needed
  for this node. Tests use injected fakes.

## Exclusive File Scope

Production files:

- `src/polymarket_alpha_lab/central_data_contracts.py`
- `src/polymarket_alpha_lab/central_data_transport.py`
- `src/polymarket_alpha_lab/central_data_registry.py`

Tests:

- `tests/test_central_data_contracts.py`
- `tests/test_central_data_transport.py`
- `tests/test_central_data_registry.py`

Do not edit `api.py`, team modules, database migrations, `AGENTS.md`, or any
other file in this node. If package exports are genuinely required, stop and
report the exact missing export rather than widening scope.

## Required Behavior

1. Use frozen dataclasses/enums, exact hard flags
   `paper_only=True`, `report_only=True`, `readonly=True`, Decimal-only values,
   canonical no-float serialization, and SHA-256 raw-byte identity.
2. Keep request/source/response/observation/evidence-reference contracts
   deterministic and timestamped. Preserve `null`, numeric zero, and
   `unknown` as distinct states.
3. Implement GET-only standard-library transport behind injected transport and
   resolver protocols. Reject request bodies, Authorization/Cookie/API-key
   credentials, HTTP, userinfo, credential query keys, fragments, explicit
   ports, IP literals, localhost/.local, loopback, RFC1918, link-local, ULA,
   multicast, metadata, and all other non-public resolved addresses.
4. Disable environment proxies and automatic redirects. Return redirect status
   to the caller; if redirect handling is represented, require revalidation of
   every hop and final URL. Canonicalize IPv4-mapped IPv6 (`::ffff:0:0/96`)
   before private-address checks and fail closed on resolver/connection
   mismatch.
5. Stream responses with a hard cap of `<=2 MiB`, bounded timeout and attempt
   budgets, explicit status/content-type/encoding/transport failure states,
   strict `Content-Length`/EOF consistency, and errors that do not echo
   response bodies or secrets. The default urllib opener is private, disables
   proxies/redirects, and revalidates GET/no-body/HTTPS/allowlist invariants;
   HTTP error responses must pass the same peer-IP check and be closed.
6. Registry entries must use exact source ids/families/hosts and constrained
   concrete endpoint definitions. The transport requires an immutable
   registry-issued definition and rejects unregistered source ids or endpoint
   paths. `source_family` is provider/lineage based; mirrors, versions, and
   subdomains of one provider share a family. Initial
   `minimum_current_source_families=1` is data only; no dispatch or persistence
   belongs in Node A.
7. Keep raw bytes in memory only for this node. Do not write files, databases,
   caches, or use `RawArchive`.

## Tests and Verification

Use fake resolver/transport/response objects only. Cover named cases for
GET-only/no-body, exact-host HTTPS allowlists, credential/userinfo/query/
fragment rejection, redirect blocking, DNS resolution, mapped IPv6, private/
loopback/link-local/metadata rejection, resolver/connection mismatch including
HTTPError responses, proxy bypass, streaming `<=2 MiB` cap, short-read and
`Content-Length` mismatch/oversize/malformed responses, unsupported content
encoding, timeout/attempt limits, raw-byte hashing, timestamp normalization,
null/zero/unknown, deep immutability, duplicate registry ids, registry endpoint
binding, endpoint template validation, ten-team default requirements, and
Phase 1 forbidden-surface scope. Run only the focused tests during execution;
Codex owns full-suite verification and the Claude result-review gate.

## Stop Conditions

Stop without widening scope if a behavior requires real network access,
credentials, persistence, a package export outside the listed files, or a
decision not specified by the parent plan. Report the blocker to Codex.
