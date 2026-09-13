# Contract-shape checks before new crypto research

## Input readiness is not permission to forecast

PR17's affected-machine check succeeded with a recorded interrupted first search
and recovery on its second allowed attempt. That transport result remains valid.
The selected BTC contract was a whole-period touch event: recent Coinbase/Kraken
USD hourly bars cannot establish whether the Binance USDT minute Low crossed the
threshold earlier in that period. This node addresses that separate research
boundary; it does not rerun the user's network or reinterpret its first failure.

The preview still returns `status=prepared` when its market and price inputs are
well formed, fresh and mutually consistent. It now also returns:

- `contract_scope`: a versioned, conservative rule-shape assessment and warnings.
- `forecast_start_status`: `blocked_by_contract_scope` or `requires_operator_approval`.

Neither status means a model ran, a forecast was approved or an outcome was
confirmed. Both existing preview CLIs pass these additional fields through. A zero
preview exit code means input preparation succeeded, NOT research admissibility.
No new public request, model call, database write or authorization is implicit.

## Conservative supported scope

| Shape | New recent-hourly launch policy |
| --- | --- |
| `path_dependent` | Block with `crypto_launch_path_history_required`. Touch/dip/reach/hit, Low/High, any-time or throughout-type hints require full relevant history and a prior-trigger check. |
| `aggregate_price` | Block with `crypto_launch_aggregate_history_required`. Average/TWAP/VWAP/median-type hints need the complete specified aggregation window and source. |
| `unclassified` | Block with `crypto_launch_contract_scope_unsupported`. Missing, ambiguous, multilingual or unsupported forms do not default to terminal-price events. |
| `terminal_price_hint` | May reach the existing explicit operator terms-approval gate. It is NOT semantically verified or automatically approved. |

The deliberately narrow terminal form is an English Bitcoin/BTC or Ethereum/ETH
above/below price question on a named date, paired with one Yes-if / otherwise-No
clause mentioning the matching asset, one-minute Close, a specified clock form,
and a compatible comparator. Explicit dollar thresholds in that clause cannot
contradict the title. Fullwidth presentation/curly quotes and whitespace normalize;
words, HTML and negations are not removed to manufacture a match. Path markers in
EITHER the question or the full rules take precedence. Unsupported or conflicting
forms fail closed. Some valid real contracts will therefore be rejected.

This is a **rule-shape filter, not a general natural-language contract parser**.
It can produce conservative false positives and may miss semantics that its
patterns do not express. It does not resolve exact dates, daylight saving time,
observation instants, all comparator edge cases, rule clarifications, source
identity or whether an event has already happened. Every result explicitly reports
`classification_is_semantic_proof=false`, `observation_time_verified=false` and
`settlement_source_verified=false`. A terminal hint must still be reviewed against
the ENTIRE fresh contract rules, and its actual observation time must be future
relative to the prospective forecast. Scheduled market end is not that proof.

## Enforcement and source distinctions

`CryptoResearchPreview.request()` recomputes the assessment from its original
validated task terms AFTER checking the approved terms hash. Unsupported shapes
raise before a `CapturedResearchRequest` is constructed. The normal
`ProjectResearchSession.launch_crypto_research()` consequently cannot create a new
market/claim or invoke a factory/model for these shapes, even with a matching hash.
Mutating the diagnostic dictionary does not change the gate. There is no override
flag, supplied scope verdict, increased-lookback escape or fake historical source.

A 24-hour window remains the wrong data when a contract requires an entire week,
a different venue, pair, aggregation or prior-trigger analysis. This node does NOT
implement a full-history collector, calculate whether a threshold was hit, or set
probability to zero/one. Unknown remains unknown.

Warnings explicitly identify recognized Binance-versus-reference-venue,
USD-versus-USDT and hourly-versus-minute distinctions. These are hints, not an
authenticated extraction of the resolution source. Coinbase/Kraken continue to be
reference feeds only, even for a supported terminal candidate. Small cross-venue
price differences do not establish oracle equivalence or model quality.

## Persistence, replay and compatibility

No database migration, request codec, protocol cohort, original market text,
source hash or required-source list changes. The existing two-source actual-read
and citation requirements remain in force. Gate metadata is recomputable from
stored terms but is not a new durable approval/certification record.

Existing captured/incomplete task replay continues to return the original receipt
without a public fetch, model call or retrospective rewrite. This is readback,
not recertification under the new rule. The generic captured runner and legacy
builders are unchanged; they support other domains and are NOT claimed to enforce
this high-level crypto-launch restriction. Do not use them to route around it.
Preflight rejections remain pre-claim, not durable failed research attempts.

The new module ships automatically with source modules; this runbook is explicitly
included in newly built kits. Old kits/manifests remain unchanged and do not gain
this policy automatically. Updating already-initialized user projects is not part
of this node; do not overlay old bundles or move their `.local` directories.

## Verification boundary

Tests first reproduce that the old launcher accepted a touch event and an unknown
shape, and that its preview lacked the separate gate status. Regression cases
cover both assets, marker precedence, aggregate/unknown/malformed rules, Unicode
presentation, conflicting thresholds, approved-hash rejection, dictionary mutation,
lookback changes and legacy replay. Synthetic terminal fixtures replace previously
generic fixtures; none of the previous budget, claim, citation or failure assertions
are relaxed.

The existing native Windows proof is extended: a path-dependent preview is rejected
through the production managed session against an EMPTY temporary database, with
zero markets/claims/attempts and zero model/fetch calls. The subsequent terminal
fixture still exercises real registration/capture, duplicate replay, failure and
incomplete-history behavior, and restart readback. The user's database is not used.
Exact test counts, final commit and reviewed CI evidence belong in the PR.

Official rule/source context checked 2026-09-14:
https://docs.polymarket.com/concepts/resolution
