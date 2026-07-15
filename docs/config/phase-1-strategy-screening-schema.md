# Phase 1 Strategy Screening Config Schema

This document defines the documentation-only schema contract for
`strategy.example.phase1-screening.json`. The sample is for Phase 1 strategy
screening configuration and operator review. It does not add runtime code, live
trading, account authentication, wallet handling, private-key handling, order
signing, order submission, order cancellation, order replacement, or exchange
mutation.

The example must remain paper-only, report-only, and readonly:

- `paper_only`: must be `true`.
- `report_only`: must be `true`.
- `readonly`: must be `true`.

Do not add live trading fields, private credentials, wallet fields, account
fields, order fields, signing fields, or execution toggles to this config
family.

## Top-Level Object

| Field | Type | Required | Meaning |
| --- | --- | --- | --- |
| `config_version` | string | Yes | Public version label for the Phase 1 screening config. |
| `paper_only` | boolean | Yes | Hard Phase 1 guard. Must be `true`. |
| `report_only` | boolean | Yes | Hard Phase 1 guard. Must be `true`. |
| `readonly` | boolean | Yes | Hard Phase 1 guard. Must be `true`. |
| `storage` | object | Yes | Local Supabase/Postgres evidence storage and readback settings. |
| `dsn_readiness_contract` | object | Yes | Exact public reason and count invariants for local Postgres DSN readiness. |
| `team_taxonomy` | object | Yes | Medium-scale specialist team routing categories. |
| `screening_thresholds` | object | Yes | Candidate screening thresholds represented as public config values. |
| `cost_assumptions` | object | Yes | Paper-only cost assumptions used to review apparent edge. |
| `freshness_sla` | object | Yes | Maximum allowed source ages before watch/block review. |
| `manual_review_gates` | object | Yes | Operator review gates and reason-code vocabulary. |

Decimal-like values are represented as quoted strings with six decimal places
where they model probabilities, edge, cost-adjusted return, or DSN readiness
rollups. Forecast row minimum counts and age limits are integers.

## Storage

`storage.kind` must be `local_supabase_postgres`. Phase 1 durable evidence uses
only local Supabase/Postgres. The config may name an environment variable such as
`POLYMARKET_ALPHA_LAB_LOCAL_SUPABASE_DSN`, but the sample must not contain a
real password, token, hosted DSN, or production database URL.

`storage.example_dsn` is a placeholder only:

```text
postgresql://postgres:<password>@127.0.0.1:54322/postgres
```

Any implementation that consumes a raw DSN must validate it with the project
local Postgres DSN validator before opening a connection. Documentation examples
must keep DSNs local and placeholder-based.

The `tables` object may document intended local paper/report evidence surfaces.
These table names are not execution authorization and must not imply live
orders, account reads, or exchange mutation.

## Local DSN Readiness Contract

`dsn_readiness_contract` mirrors the exact public contract returned by
`local_postgres_dsn_readiness`. It documents validation output only; it does not
accept a DSN, open a connection, or authorize persistence.

The count invariant is always:

```text
ready_check_count + blocker_count = required_check_count = 4.000000
```

The only valid status/count combinations are:

| Status | `ready_check_count` | `blocker_count` |
| --- | --- | --- |
| `ready` | `4.000000` | `0.000000` |
| `blocker` | `3.000000` | `1.000000` |

`blocker_count` counts the blocked readiness outcome, not the number of reason
codes. A two-code hosted, JSONL, or SQLite result therefore still has
`blocker_count = 1.000000`.

Reason tuples are exact and ordered:

| Input classification | Exact `reason_codes` |
| --- | --- |
| ready local Postgres DSN | `local_supabase_postgres_dsn_ready` |
| missing, malformed, or otherwise invalid | `local_supabase_postgres_dsn_invalid_blocker` |
| hosted Postgres | `hosted_database_dsn_rejected_blocker`, then `local_supabase_postgres_dsn_invalid_blocker` |
| JSONL/file DSN | `jsonl_file_dsn_rejected_blocker`, then `local_supabase_postgres_dsn_invalid_blocker` |
| SQLite DSN | `sqlite_dsn_rejected_blocker`, then `local_supabase_postgres_dsn_invalid_blocker` |

The readiness object and every public payload keep `paper_only=true`,
`report_only=true`, and `readonly=true`. The checked DSN remains redacted.

## Team Taxonomy

`team_taxonomy` defines routing categories for Phase 1 research responsibility.
It does not define execution authority, capital allocation, live
recommendations, or position sizing.

Required fields:

- `primary_team_required`: boolean; should be `true`.
- `secondary_team_max_count`: integer; example value is `2`.
- `teams`: array of team objects.

Each team object has:

- `team_id`: public team identifier such as `crypto_btc`.
- `category_ids`: public category or tag aliases routed to the team.
- `memory_policy`: one of `allow`, `throttle`, or `block`.

The sample team set mirrors the Phase 1 medium-scale operating model:
`politics`, `crypto_btc`, `crypto_eth`, `macro_rates`, `equity_indices`,
`commodities_gold`, `commodities_oil`, `sports_soccer`,
`sports_basketball`, and `sports_other`.

## Screening Thresholds

`screening_thresholds` contains paper-only candidate review thresholds.

| Field | Type | Example | Meaning |
| --- | --- | --- | --- |
| `min_source_verified_edge` | decimal string | `"0.010000"` | Minimum source-supported forecast-vs-price edge before cost review. |
| `min_research_readiness` | decimal string | `"0.500000"` | Minimum research readiness score. |
| `min_attention_score` | decimal string | `"0.500000"` | Minimum attention queue score. |
| `min_source_reliability_score` | decimal string | `"0.650000"` | Minimum source reliability score. |
| `default_min_source_count` | integer | `2` | Default minimum source count carried by a forecast-context row. |
| `default_min_source_family_count` | integer | `2` | Default minimum distinct source-family count carried by a forecast-context row. |
| `microstructure_min_source_count` | integer | `1` | Minimum source count for microstructure model bases. |
| `microstructure_min_source_family_count` | integer | `1` | Minimum source-family count for microstructure model bases. |
| `superforecaster_min_source_count` | integer | `3` | Minimum source count for the superforecaster model basis. |
| `superforecaster_min_source_family_count` | integer | `3` | Minimum source-family count for the superforecaster model basis. |
| `max_liquidity_exit_risk` | decimal string | `"0.750000"` | Maximum acceptable paper liquidity exit risk. |
| `max_resolution_ambiguity` | decimal string | `"0.750000"` | Maximum acceptable resolution ambiguity. |
| `max_uncertainty_band_width` | decimal string | `"0.300000"` | Maximum probability uncertainty band width before review. |
| `max_portfolio_impact_for_paper_review` | decimal string | `"0.050000"` | Paper review cap for modeled portfolio impact. |

Failing a threshold should produce watch or blocked review status; it must not
create trade instructions or live order intent.

Forecast-context thresholds are selected by `model_basis`, not by one global
source quorum. `yes_ask_naive_v0` and `book_imbalance_v0` use the
microstructure `1/1` source/source-family minimums;
`superforecaster_prompt_v0` uses `3/3`; every other supported basis uses the
default `2/2`. The selected values are materialized as
`minimum_source_count` and `minimum_source_family_count` on each row and must be
replayed exactly during row validation.

Runtime configuration may make these dual quorums stricter, but it must not
lower the microstructure values below `1/1`, the default values below `2/2`, or
the superforecaster values below `3/3`.

## Cost Assumptions

`cost_assumptions` are paper-only research factors. They should be explicit so
operators can see how spread, slippage, liquidity, fees, and settlement delay
affect apparent edge.

Required fields:

- `currency`: display currency for the paper notional.
- `paper_notional_per_candidate`: decimal string; illustrative paper notional.
- `fee_bps`: decimal string; modeled fee basis points.
- `half_spread_bps`: decimal string; modeled half-spread basis points.
- `slippage_bps`: decimal string; modeled slippage basis points.
- `liquidity_haircut_bps`: decimal string; modeled liquidity haircut.
- `settlement_delay_cost_bps_per_day`: decimal string; daily settlement delay cost.
- `minimum_cost_adjusted_edge`: decimal string; edge floor after cost assumptions.

These values are not account balances, live sizing, capital allocation, or order
instructions.

## Freshness SLA

`freshness_sla` sets maximum source ages, in seconds, before a candidate should
be downgraded to watch or blocked.

Required fields:

- `market_metadata_max_age_seconds`
- `market_depth_snapshot_max_age_seconds`
- `source_evidence_max_age_seconds`
- `team_memory_max_age_seconds`
- `outcome_history_max_age_seconds`

Freshness failures should preserve operator-facing reason codes and require
manual review before any paper candidate can advance.

## Manual Review Gates

`manual_review_gates` defines the operator review contract.

Required fields:

- `require_review_before_candidate`: should be `true`.
- `gate_statuses`: must be limited to `pass`, `watch`, and `blocked`.
- `watch_requires_review`: should be `true`.
- `blocked_requires_research_reset`: should be `true`.
- `required_reviewer_notes`: public note categories the operator must cover.
- `review_reason_codes`: exact category-readiness manual review reason vocabulary.
- `block_reason_codes`: public reason-code vocabulary for blocked candidates.

The category-readiness manual review reasons are mutually exclusive:

- use `manual_review_not_required` when the category policy does not require
  manual review;
- use `manual_review_required` when review is required but not completed; this
  is a watch reason unless another category blocker is present;
- use `manual_review_completed` when required review is complete; remove
  `manual_review_required`, and allow ready status when no other blocker exists.

`operator_review_missing` is not part of the category-readiness reason enum and
must not be substituted for `manual_review_required`. DSN-related block reasons
must use the exact reason tuples defined by `dsn_readiness_contract` rather than
the obsolete `local_supabase_dsn_missing` label.

Forecast-context quorum failures use the distinct runtime reasons
`source_count_below_minimum` and `source_family_count_below_minimum` so operators
can see which half of the dual quorum failed. `source_quorum_insufficient` is not part
of this config vocabulary and must not replace those runtime reasons.

Manual review is an operator-facing paper/report gate only. It must not collect
credentials, authorize execution, sign orders, submit orders, or mutate exchange
state.

## Redaction And Forbidden Fields

Configuration examples must use placeholders only. Do not include real API keys,
passwords, cookies, auth headers, wallet material, private keys, seed phrases,
account identifiers, hosted account details, or live order identifiers.

Forbidden field families include:

- `live_*`
- `wallet_*`
- `private_key`
- `seed_phrase`
- `account_*`
- `auth_*`
- `order_*`
- `signature`
- `submit_*`
- `cancel_*`
- `replace_*`
- `execute_*`

The existing legacy `strategy.example.json` may contain historical paper-cycle
fields. New Phase 1 screening examples should use
`strategy.example.phase1-screening.json` as the documentation baseline and keep
the hard flags explicit.
