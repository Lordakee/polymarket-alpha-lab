# Phase 1 Probability Event Go/No-Go Runbook

This operator manual describes how a human reviewer should use Phase 1
Polymarket probability-event filtering packets. It is a paper-only,
report-only, readonly operations guide. It does not authorize live trading,
investment advice, trade instructions, position sizing, wallet handling,
account authentication, order signing, order submission, order cancellation,
order replacement, exchange mutation, or account mutation.

Use this runbook with the strategy workflow in
[Phase 1 Probability Event Filtering Workflow](../strategy/phase1-probability-event-filtering-workflow.md).

## Operator Goal

The operator's job is to decide whether the packet is complete enough for a
separate manual review decision. The operator does not convert packet status
into an automated trade, order, allocation, or execution instruction.

The practical outcomes are:

- `go_for_manual_review`: the packet is complete and ready for human review;
- `no_go`: the packet is complete enough to reject;
- `research`: a named research gap needs follow-up;
- `watch`: a trigger or refresh condition should be monitored;
- `blocked`: the packet violates a boundary or has a non-actionable blocker.

## Inputs Required Before Review

Do not review a packet until these inputs are present:

- public market reference, market question, outcomes, and close time;
- resolution rules and official source hierarchy;
- primary specialist team route and packet digest;
- evidence summary with source timestamps, freshness, corroboration, and
  contradictions;
- canonical event `P(YES)` forecast probability and confidence;
- executable YES/NO price context or a reason executable price is unavailable;
- cost, EV, liquidity, depth, spread, fee, slippage, settlement, and
  resolution-risk sections;
- memory policy status: `allow`, `throttle`, or `block`;
- explicit `paper_only`, `report_only`, and `readonly` flags where supported;
- redaction status for DSNs, credentials, tokens, wallet/account material, and
  order-like sensitive values.

forecast_probability always denotes canonical Decimal P(YES), regardless of selected_side; selected_side identifies the paper-review side being evaluated and never reorients forecast_probability; P(NO) is 1 - P(YES).

If any required input is missing, the packet is `research` or `blocked`, not
`go_for_manual_review`.

## Step 1: Confirm Phase 1 Boundary

Before reading the market details, confirm the packet stays inside Phase 1.

Pass conditions:

- packet is paper-only, report-only, and readonly;
- no live order, wallet, account, auth, signing, submission, cancellation, or
  replacement behavior is requested;
- no private account state, credential, token, wallet material, or order id is
  exposed;
- persistence target is local Supabase/Postgres report history only;
- the packet says any manual action is outside the automated system boundary.

Fail closed if the packet contains execution language such as buy, sell, place,
submit, sign, cancel, replace, allocate, size position, use wallet, authenticate,
or mutate exchange state.

## Step 2: Review Market Discovery

Check whether the market is well-defined enough for research:

- question and outcome labels match the Polymarket event;
- close time and expected resolution timing are known;
- event category and specialist route make sense;
- resolution rules are linked or quoted in summarized form;
- official source hierarchy is identified;
- market is not closed, stale beyond usefulness, or missing usable market
  structure;
- initial reason for reviewing the market is explicit.

Route to `blocked` when the event definition or resolution path cannot be made
auditable. Route to `research` when the gap is specific and answerable.

## Step 3: Review Evidence Quality

Evidence quality comes before price edge. The operator should verify that the
packet explains why the team's probability estimate is better informed than the
market price.

Review checklist:

- sources are fresh enough for the event timeline;
- primary or official sources are used when available;
- secondary and commentary sources are labeled as such;
- each major claim is tied to the market's resolution criteria;
- contradictions are listed and resolved by source hierarchy or marked as open;
- missing facts and stale-source risks are explicit;
- redaction is applied before operator-facing output.

Outcomes:

- strong, corroborated, fresh evidence can advance to forecast review;
- single-source, stale, or incomplete evidence should become `research` or
  `watch`;
- unverifiable, contradicted, or unsafe evidence should become `blocked`.

## Step 4: Review Specialist Team Research

Confirm the primary team owns the right domain and that the packet contains an
explainable probability forecast.

Required checks:

- team id and event template are plausible for the market;
- forecast probability, confidence, and uncertainty are included;
- evidence-to-forecast reasoning is explicit;
- resolution-rule interpretation is reviewed by the team;
- memory policy is present and justified;
- prior failure modes and stale-memory warnings are not hidden;
- secondary-team disagreements are preserved when relevant.

Team memory can support source reliability or calibration notes. It cannot
approve trades, override weak evidence, size positions, create recommendations,
or authorize execution.

## Step 5: Review Costs, EV, Liquidity, and Settlement

The operator should reject packets that depend on raw forecast edge while
ignoring market frictions.

Minimum checks:

- side-aware gross edge is calculated against executable YES/NO price;
- total cost includes spread, fees, slippage, fill risk, and any explicit
  settlement or lockup drag;
- EV remains positive after cost and uncertainty adjustments;
- book depth supports the intended paper notional or the packet explains why no
  paper candidate can be promoted;
- spread and depth are fresh enough for the decision time;
- settlement timing, dispute window, finalization lag, and capital lockup are
  reviewed;
- resolution-risk notes explain what evidence will prove the outcome.

```text
YES side probability = forecast_probability
NO side probability = 1 - forecast_probability
```

Do not accept midpoint-only edge, stale executable prices, missing liquidity,
or optimistic full-fill assumptions as sufficient for `go_for_manual_review`.

## Step 6: Assign Go/No-Go Status

Use the narrowest justified status:

| Status | Operator Standard |
| --- | --- |
| `go_for_manual_review` | All gates are complete enough for a human to review the decision support packet. This is not an execution instruction. |
| `no_go` | The packet is complete and shows insufficient net EV, weak decision quality, or unacceptable risk. |
| `research` | A specific source, forecast, cost, liquidity, settlement, resolution, or memory gap has an owner and deadline. |
| `watch` | No current decision is justified, but a named trigger could change the packet. |
| `blocked` | The packet violates Phase 1 boundaries or has an unresolvable blocker. |

When uncertain between two states, choose the safer state. For example, choose
`research` over `go_for_manual_review`, `watch` over `no_go` when a concrete
future trigger matters, and `blocked` over `research` when the missing evidence
cannot be obtained safely.

## Go/No-Go Packet Template

Use this structure for operator-facing packet output:

```text
packet_id:
generated_at_utc:
paper_only: true
report_only: true
readonly: true

market:
  market_ref:
  question:
  outcomes:
  close_time_utc:
  resolution_source:
  resolution_summary:

team_research:
  primary_team:
  secondary_teams:
  specialist_packet_digest:
  forecast_probability:
  confidence:
  uncertainty_range:
  memory_policy:
  memory_notes:

evidence:
  source_quality_status:
  source_count:
  primary_sources:
  corroboration_summary:
  contradiction_summary:
  stale_or_missing_facts:

market_review:
  selected_side:
  executable_yes_price:
  executable_no_price:
  gross_edge_probability:
  total_cost_probability:
  net_edge_probability:
  ev_summary:
  liquidity_status:
  depth_status:
  spread_status:
  settlement_risk_status:
  resolution_risk_status:

operator_decision:
  status:
  reason_codes:
  required_follow_ups:
  watch_triggers:
  blocked_reasons:
  redaction_status:
  local_persistence_status:
```

The packet should be concise enough for review but complete enough for replay.
It should preserve source references or digests without printing secrets,
credentials, raw DSNs, wallet/account material, or order-like sensitive values.

## Local Persistence and Readback

After review, persist only report evidence to local Supabase/Postgres through
approved local DSN-validated paths. The persisted row should support replay of
the decision and later diagnostics without becoming execution state.

Persisted report rows should include:

- packet id and generated timestamp;
- market reference and team route;
- status and reason codes;
- evidence quality, forecast, cost, EV, liquidity, settlement, and
  resolution-risk summaries;
- memory policy and referenced local memory digests;
- redaction status and readonly flags;
- operator follow-up fields.

Do not persist raw credentials, raw DSNs, tokens, private account data, wallet
material, live order identifiers, or private source payloads. Do not use file
journals, CSV ledgers, SQLite, DuckDB, Redis, MongoDB, hosted databases, or
generic durable-store fallbacks as the durable Phase 1 record.

## Escalation Rules

Escalate to `blocked` when:

- any step requires authentication, wallet/account access, private keys, or
  exchange mutation;
- the packet asks the system to submit, sign, cancel, replace, or route an
  order;
- the resolution source cannot be identified;
- evidence is unsafe, untraceable, or contradicted by stronger sources;
- the local persistence boundary is violated;
- sensitive values are unredacted in operator output.

Escalate to `research` when:

- the source gap is specific and answerable;
- executable price or depth is stale but refreshable;
- settlement timing needs a primary-source check;
- team memory is throttled but not blocked;
- a secondary specialist can resolve a domain disagreement.

Escalate to `watch` when:

- a future official release, close-time update, source refresh, price move, or
  liquidity change is the actual decision trigger;
- the current market is too thin but may become liquid before close;
- the event timeline is not mature enough for a reliable forecast.
