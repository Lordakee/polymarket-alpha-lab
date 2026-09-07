# P3 Stage Plan DRAFT: Independent Evidence And Real Quorum

(Pre-drafted during P2 settlement waiting, per the roadmap's "concurrent with
settlement waiting when useful". This draft becomes the formal P3 stage plan
only after P2 is committed and pushed; its review loop starts then.)

Date: 2026-09-07 (drafted 2026-09-07T11:45Z, pre-P2-close)
Stage: P3 of the Project Completion Plan
Dependencies: accepted and pushed P2; M1/M2/M5 contracts; P1 versioned cohorts

## Parent-Plan Traceability

P3 adds a second independent public price family for `btc_spot_price` and
`eth_spot_price`, defines comparable spot observations, and activates a
reviewed two-family quorum requirement — without weakening the accepted
contradiction contract. No numerical tolerance is assigned and no silent
averaging is authorized by this draft.

## Verified Starting Facts (from /tmp/p3_source_scouting.md, 2026-09-07)

- Current family: Kraken public (`api.kraken.com/0/public/Ticker`,
  `result.*.c[0]`, last trade, `cache-control: max-age=2`).
- Candidate A (strong): Coinbase Exchange
  `https://api.exchange.coinbase.com/products/{BTC,ETH}-USD/ticker`, field
  `price` (string, USD last trade), HTTP 200 keyless, real-time
  (`trade_id` advances within 6 s), latency 0.1-0.3 s, documented 10 req/s
  public limit, operator Coinbase Global, Inc. Retail `/v2/prices/.../spot`
  is CDN-cached ~60 s and is a backup only.
- Candidate B (strong): Bitstamp `https://www.bitstamp.net/api/v2/ticker/
  {btcusd,ethusd}/`, field `last` (string, USD last trade,
  `market_type: "SPOT"`), HTTP 200 keyless, real-time, latency 0.07-0.28 s,
  documented 8000 req/10 min, operator Bitstamp (Robinhood group).
- Cross-source sanity at probe time: BTC quotes within ~0.2% across
  Coinbase/Bitstamp/Gemini/Kraken — genuinely independent venues.
- Disqualified/unsuitable recorded in the scouting report: CryptoCompare
  (auth required), Binance (USDT quote + geo-fragile), OKX (USDT spot),
  CoinGecko (aggregate, 30-60 s cache — not an independent venue quote).
- Transport constraints: both candidates are public HTTPS GET, no keys, no
  cookies required (CDN-set cookies never needed), and fit the existing
  SafeGETTransport allowlist + persistence policy model.

## Proposed Work Items

1. Source registration: add `coinbase_exchange_ticker` (per-asset param
   `product_id` enum {BTC-USD, ETH-USD}) as the second `coinbase_exchange`
   family; keep Bitstamp as a documented reserve family (registered only if
   review asks for a third venue or Coinbase degrades). Add host to the
   default allowlist; freshness policy seconds conservative for a real-time
   feed (align with Kraken's 300 s default; retune only with smoke evidence).
2. Parser: map Coinbase ticker to the existing spot observation shape
   (Decimal price, observation time from `time` field (ISO-8601 ns —
   normalize to microsecond precision deterministically), reason codes for
   missing/invalid fields). Fail-closed like existing adapters.
3. Comparability semantics: a document (module docstring + fixtures) fixing
   asset, quote currency USD, measurement meaning = venue last trade,
   observation time = venue trade time (not retrieval), Decimal units, and
   parser version per family. Dispatch comparison stays exact-equality on
   typed values; genuine cross-provider differences therefore BLOCK the
   bundle — that behavior is intentional until a reviewed corroboration
   policy exists. This plan proposes NO tolerance; it only makes the block
   auditable per-family references.
4. Two-family requirement: extend item requirements for both spot items to
   the two registered families (kraken_public + coinbase_exchange), each
   family's observation carried through the bundle with full source
   references preserved into selection, conflict reporting, lineage and
   export. The existing exact-match contradiction contract then fails the
   bundle whenever the two venues disagree at the same measurement instant
   — recorded as a blocked result, never averaged.
5. Operational smoke: bounded live acquisition (one cycle per team) through
   the real transport; replay tests with recorded fixtures for agreement,
   genuine disagreement, single-family loss, stale/missing/parse-failed,
   and quorum loss. Mirror deduplication fixture (same provider, two names)
   must NOT satisfy the two-family requirement.
6. Cohort discipline: activating the requirement starts a NEW config cohort
   (e.g. `p3-crypto_{btc,eth}-v1`); the old 1/1 cohort is never relabeled
   corroborated. P2's frozen cohort and report remain untouched; any
   coverage change is reported only on the new cohort.
7. Docs and CLI: runbook section for the second family, registry matrix
   update, verification artifacts under `docs/verification/p3/`.

## Acceptance Criteria (from roadmap P3)

1. Both spot items have a verified second independent family with actual
   endpoint/access evidence (scouting report + live smoke) and a documented
   current/required family policy.
2. Replay and failure tests demonstrate agreement, genuine disagreement,
   mirror deduplication, stale/missing/parse-failed/unknown inputs, and
   loss of quorum; contradictions preserve references and block required
   evidence; blocked inputs never become neutral forecasts.
3. A one-family observation cannot satisfy an active two-family
   requirement; the old cohort is never retroactively labeled corroborated.
4. Readback/export provenance survives for both teams on the new cohort.

## Verification Plan

- Focused new tests + full suite (xdist, ~2 min) green; compileall; CLI
  inventory delta documented if commands change.
- Opt-in live smoke (env-gated) for one BTC and one ETH cycle.
- Claude plan review (this document) -> disposition -> implement -> verify
  -> Claude hard review until PASS -> commit -> push, only after P2 is
  pushed.

## Rollback

Revert P3 code/docs; drop nothing from P1/P2 evidence. Registered sources
are additive registry entries; removal restores the prior single-family
state without touching persisted evidence.
