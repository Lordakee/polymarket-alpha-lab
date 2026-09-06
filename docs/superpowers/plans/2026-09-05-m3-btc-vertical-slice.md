# M3 Stage Plan: BTC Vertical Slice (First Node D/E Delivery)

Date: 2026-09-05
Stage: M3 of the [Project Delivery Plan](../../roadmap/2026-09-05-project-delivery-plan.md)
Status: plan review completed; findings dispositioned (see the final section)
Depends on: M2 (accepted; commit `68d03355`). This stage is smaller than
M1/M2 because it wires accepted contracts (bundle, persistence, builder)
rather than defining new persistence or dispatch boundaries.

## Parent-Plan Traceability

This stage delivers the first end-to-end slice: one pure BTC evidence
adapter wired to the existing `crypto_btc` supplied-input builder, a
single orchestration reducer producing a canonical Decimal P(YES)
forecast and an operator packet, a bounded single-market CLI command
with cycle status and durable readback through existing persistence
surfaces, and restart-stable identities. Batch mode, additional teams,
and paper-trade simulation wiring remain M4/M5 scope.

## Current-Code Facts

- `build_crypto_btc_team_forecast` takes condition/slug/question/event
  metadata, `CryptoBtcEvidenceInput` rows, a base probability, and a
  config; it returns a `TeamForecastPacket` plus
  `TeamForecastEvidencePacket` rows with canonical P(YES) semantics.
- `team_forecast_store.py`/`team_forecast_psycopg.py` already persist and
  load forecasts and evidence rows behind env-gated local DSNs.
- M1's Gamma adapter currently extracts conditionId/question/slug/
  outcomes/outcomePrices/active/closed/endDate but not `clobTokenIds`,
  which the CLOB book fetch needs per market.
- M2's bundle provides per-item `SelectedEvidence`/`ZeroWeightPlaceholder`
  with references and reason codes.

## Design Decisions

1. The BTC adapter is pure and refuses to invent probability impact.
   `crypto_btc_evidence_adapter.py` maps a ready bundle to
   `CryptoBtcEvidenceInput` rows: the BTC spot observation becomes
   descriptive evidence text (price, bid/ask, observation time, source
   family) with a documented weight policy; blocked items become
   zero-weight inputs carrying the bundle's reason codes; every input's
   `probability_impact` is exactly `Decimal("0")` in this slice because
   no reviewed model justifies moving P(YES) from spot price alone. The
   forecast therefore equals its base probability plus resolution-risk
   handling, and the packet's reason codes say so. The evidence remains
   operationally valuable: weights and reason codes drive the operator
   packet's confidence and blocked/watch signals, descriptive text
   provides audit context, and a later reviewed model can change
   `probability_impact` from zero without contract changes.
2. Base probability comes from executable market structure, centrally.
   The cycle reducer derives `base_probability` and the market-implied
   hint from the CLOB book observation of the **YES token** — identified
   by mapping `clobTokenIds` to the affirmative outcome, so the best
   bid/ask midpoint directly represents P(YES) (Decimal, clamped to
   (0,1)). A crossed YES book (bid >= ask) or empty YES book blocks the
   cycle with explicit reason codes instead of guessing.
3. One orchestration owner. `btc_research_cycle.py` is a pure reducer:
   it consumes already-fetched observations (metadata, book, ticker) and
   a bundle, and returns a `BtcCycleResult` (status ready/blocked, cycle
   identity, forecast packet, evidence packets, operator summary
   blocks, persistence keys). It does not fetch, import transport, or
   touch the environment; the CLI owns acquisition ordering.
4. Cycle identity is a deterministic function of its inputs:
   `sha256(condition_id | bundle_id | config_version | base_probability)`,
   with `generated_at` excluded. Each observation window is intentionally
   a distinct cycle for the audit trail (the bundle id carries `as_of`),
   so identity means "same inputs, same identity", not "same market
   forever". Retry safety comes from row-level idempotency instead: every
   persistence layer in the path (raw events, normalized observations,
   forecast rows) deduplicates by its own deterministic identity, so
   re-running after a partial failure adds no duplicate facts. Automatic
   retry with backoff is deferred to M4; retry orchestration in this
   stage is manual (operators re-run after resolving blockers).
5. The operator packet is a deterministic text report: market question
   and resolution references, as-of times, per-item evidence
   availability with source families and payload hashes, forecast P(YES)
   and selected side, executable bid/ask and midpoint, edge versus
   market implied, and blocked/watch reasons. It contains no raw
   payloads and no credentials.
6. The CLI command is bounded and single-market: `btc-research-cycle
   --market <slug-or-condition-id>` fetches Gamma metadata, the CLOB
   book, and the Kraken ticker through the M1 acquisition path,
   persists raw/normalized rows only when the central-data DSN env is
   enabled, builds the bundle and cycle, persists the forecast and
   evidence only when the team-forecast DSN env is enabled, prints the
   operator packet and cycle status, and exits nonzero on blocked
   cycles. No batch mode in this stage.
7. Gamma adapter extension is additive: extract `clobTokenIds` (embedded
   JSON array of decimal-string token ids) with
   `embedded_json_invalid`/`missing_required_field` handling; existing
   extracted fields and their tests are unchanged.

## Work Items

1. `src/polymarket_alpha_lab/central_data_source_adapters.py` (edit):
   additive `clob_token_ids` extraction plus tests.
2. `src/polymarket_alpha_lab/crypto_btc_evidence_adapter.py` (new):
   pure bundle-to-inputs mapping and weight policy.
3. `src/polymarket_alpha_lab/btc_research_cycle.py` (new):
   `BtcCycleResult`, `run_btc_research_cycle` reducer, operator packet
   renderer, blocked/watch reason propagation.
4. `src/polymarket_alpha_lab/cli.py` (edit): the single
   `btc-research-cycle` command with env-gated persistence and nonzero
   exit on blocked cycles. The CLI remains approximately 15k lines
   (measured at the M0 baseline); this stage adds one bounded command
   and does not restructure the file — focused extraction is M4 scope.
5. Tests:
   - `tests/test_crypto_btc_evidence_adapter.py`: ready mapping,
     blocked zero-weight inputs with reasons, zero probability impact,
     deterministic replay.
   - `tests/test_btc_research_cycle.py`: ready cycle from fixture
     observations (canonical P(YES) equals midpoint-derived base with
     documented reasons), blocked cycle on unusable book, blocked cycle
     when required items are placeholders, operator packet content and
     determinism, cycle identity stability across replay with different
     `generated_at`.
   - CLI test (offline, no network): argument validation, blocked-cycle
     exit behavior using injected fixture fetchers where the command
     surface allows; live path is exercised only by the env-gated smoke
     pattern already established.
6. `tests/test_central_data_network_smoke.py` (edit, env-gated): extend
   the opt-in smoke to run one real BTC cycle end to end when both the
   network gate and the central-data DSN env are enabled.

## Verification

Recorded results (2026-09-05):

- Focused: adapter + cycle + policy + all central-data suites — 108
  passed, 5 skipped (gated); extended live smoke passed against real
  Gamma, CLOB, and Kraken data through the full
  fetch -> persist-shaped rows -> bundle -> cycle -> operator-packet
  chain (discarding store, no DB writes).
- CLI baseline regenerated (78 commands) with the explicit compatibility
  decision recorded in the inventory header.
- Full Python 3.11 regression recorded in the hard-review prompt.
- Compile checks, `git diff --check`, credential scan clean.

## Implementation Findings (2026-09-05)

First contact with live provider data surfaced three pre-real-data gaps,
each fixed with dedicated regression tests:

1. Persistence policy false positives. The wallet/phone heuristics
   refused every real Gamma page: 40-hex strings appear only under
   public market-infrastructure keys (`assetAddress`, `submitted_by`,
   `resolvedBy` — collateral and UMA oracle addresses), and the phone
   heuristic fired on digit runs inside 64-hex ids and ISO dates.
   Refined, fail-closed: in JSON bodies a wallet-shaped string is now
   refused unless it is the value of a key without account/person
   semantics (keys matching wallet/account/user/owner/trader/maker/
   taker/sender/recipient/customer/person/deposit/withdraw/email/phone
   still refuse; array or free-text positions still refuse); non-JSON
   bodies keep the blanket wallet rule. Phone detection now requires
   real phone shape (3-4 digit grouping with separators) and excludes
   ISO-date shapes. Unit tests pin both directions.
2. Canonical parameter value length. Real CLOB token ids are 77-78
   decimal digits and real slags reach 81 characters, exceeding the
   19/64-char limits. Canonical value charset length raised to 128 and
   the token_id/slug patterns widened; all prior canonicality rules
   unchanged.
3. CLOB book `timestamp` is epoch milliseconds. The adapter normalizes
   deterministically (values above 1e12 treated as milliseconds) instead
   of raising out-of-range datetimes.

These are corrections of implementation drift against documented intent
(market metadata is explicitly non-PII in the Node B design); no
refusal case for actual account identifiers, credentials, emails, or
formatted phones was weakened, and the permanent unit tests prove both
directions.

## Acceptance Criteria (mirrors delivery-plan M3 exit)

1. Positive and blocked BTC cases traverse observations, bundle,
   forecast, and operator packet from fixtures.
2. Every used evidence item is traceable to source family, payload
   hash, and parser version through the bundle references.
3. Replay produces identical cycle identity and canonical outputs;
   differing `generated_at` does not change identity.
4. The forecast preserves canonical Decimal P(YES) semantics and states
   its base-probability origin; unavailable required evidence blocks
   rather than neutralizing.
5. The CLI is bounded, single-market, env-gated for persistence, exits
   nonzero on blocked cycles, and prints the deterministic operator
   packet.
6. No live trading, order submission, wallet, account, or credential
   surface is introduced.

## Rollback

Revert the five work items; no schema or persisted-data dependency.

## Plan Review Response (2026-09-05)

Claude Code reviewed this plan read-only (`claude-opus-5`, effort `max`)
and returned REQUEST_CHANGES: two MAJOR, four MINOR, one NIT.
Dispositions:

1. MAJOR cycle identity vs idempotency: ACCEPTED via the reviewer's
   second interpretation — each observation window is a distinct cycle
   with a deterministic input-derived identity; retry safety is row-level
   idempotency, and automatic backoff is deferred to M4.
2. MAJOR CLOB sidedness: ACCEPTED; the base probability uses the YES
   token's book via the `clobTokenIds` mapping, with crossed/empty YES
   books blocking the cycle.
3. MINOR retry policy guidance: ACCEPTED; manual retry and partial-
   failure semantics documented in decision 4.
4. MINOR zero-impact defense: ACCEPTED; the operational-value sentence
   is added to decision 1.
5. MINOR smoke-file naming: REJECTED as factually incorrect. The file
   `tests/test_central_data_network_smoke.py` exists — it was delivered
   by M1 (the reviewer's grep apparently missed it) and is distinct from
   the older `tests/test_central_data_supabase_smoke.py`. Work item 6
   correctly targets the network smoke file.
6. MINOR CLI size acknowledgment: ACCEPTED.
7. NIT brevity rationale: ACCEPTED.

## Hard-Review Record (2026-09-05/06)

The M3 hard review ran in three parts because the Claude gateway suffered
a multi-hour upstream outage for review-sized sessions (502s; even
previously-successful prompts failed, while tiny prompts passed):

- Criterion A (acceptance criteria): PASS, zero findings.
- Criterion C (CLI, adapters, scope): PASS with one MINOR — the YES-token
  positional fallback. Fixed fail-closed: markets without an outcome
  labeled "yes" now block with `yes_token_unidentified` instead of
  guessing position; regression test added.
- Criterion B (policy refinement safety): completed as three short
  default-model micro-reviews after the opus-5 route proved unavailable.
  - B1 found abbreviated/homoglyph/non-English account-ish keys bypassing
    the account-key denylist. Fixed structurally: the kv-exemption now
    uses an explicit public-metadata key ALLOWLIST (fail-closed; unknown
    spellings refuse), matching the project's allowlist philosophy.
  - B2 found US-centric phone shapes (`+44 20 1234 5678`, `1234-5678`
    passed). Fixed: leading-plus, multi-separator 8+ digit, and two-group
    8+ digit shapes are refused; ISO and US date shapes excluded;
    one-separator id-like runs (`12345678-9`) stay allowed.
  - Closure review: wallet allowlist PASS; it argued `1234-5678` is more
    often an id than a phone — directly contradicting B2. Resolved toward
    refusal (B2's requirement) under the policy's stated fail-closed
    priority for personal data; recorded as a known documented tradeoff,
    with dashed 8-digit ids rare in registered market metadata.
- Verification after every fix: policy suite, adjacent central-data and
  BTC suites, and the live opt-in network smoke all green; full Python
  3.11 regression re-run green after the final phone/wallet fixes before
  commit.

All findings from every review part are either fixed with regression
tests or documented as accepted tradeoffs with rationale.
