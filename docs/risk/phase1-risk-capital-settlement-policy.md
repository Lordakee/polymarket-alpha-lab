# Phase 1 Risk, Capital, And Settlement Policy

Date: 2026-07-12
Status: Phase 1 documentation policy
Scope: Polymarket probability-event paper screening only

This document defines the Phase 1 risk policy for Polymarket probability-event
screening packets. It is a paper-only, report-only, readonly policy node. It
does not authorize live trading, investment advice, trade instructions,
position sizing, wallet handling, account authentication, order signing, order
submission, order cancellation, order replacement, exchange mutation, or account
mutation.

Use this policy with the Phase 1 strategy workflow and operator runbook:

- [Phase 1 Probability Event Filtering Workflow](../strategy/phase1-probability-event-filtering-workflow.md)
- [Phase 1 Probability Event Go/No-Go Runbook](../operators/phase1-probability-event-go-no-go-runbook.md)

## Policy Goal

Phase 1 may identify probability events that deserve research attention, but it
must not convert forecast edge into automated execution. The risk layer exists
to make market frictions, settlement timing, capital lockup, and portfolio
exposure explicit before a human operator reviews any packet.

A passing risk packet means only:

- the event is documented well enough for manual review;
- market frictions are visible and cost-adjusted;
- settlement and capital lockup risks are not hidden;
- exposure and correlation concerns are named;
- the recommended state remains manual decision support.

A passing risk packet does not mean buy, sell, allocate, size, execute, or
approve live capital.

## Readonly Phase 1 Boundary

Allowed Phase 1 risk activity:

- read-only review of public market metadata and supplied order-book context;
- paper-only calculations for cost, spread, slippage, fee drag, EV, settlement
  delay, capital lockup, and exposure;
- manual go/no-go policy classification;
- local report persistence and readonly readback where already approved by
  Phase 1 documentation;
- operator-facing explanation of risk gates, reason codes, and required
  follow-ups.

Forbidden Phase 1 risk activity:

- live trading, automated investing, or investment recommendations;
- position sizing, allocation approval, capital deployment, or portfolio
  construction instructions;
- account authentication, hosted account reads, wallet/private-key handling, or
  private order-state inspection;
- order signing, submission, cancellation, replacement, or exchange mutation;
- treating paper EV, score, rank, or readiness status as an executable signal.

When policy language and a candidate packet conflict, the safer interpretation
wins and the packet is `blocked` or `research`.

## Cost Policy

Every probability-event packet must separate gross forecast edge from the cost
of expressing that edge in the market. Midpoint-only comparisons are not
sufficient.

Required cost fields:

| Field | Phase 1 Standard | Blocker When Missing |
| --- | --- | --- |
| Selected side | YES or NO side under review, tied to the forecast probability. | Side is implied but not stated. |
| Executable price | Best available executable price for the selected side, with timestamp and source. | Only midpoint, last trade, or stale quote is available. |
| Spread cost | Difference between bid and ask, or side-aware penalty for crossing the spread. | Spread is unavailable, stale, crossed, or ignored. |
| Slippage estimate | Expected price degradation for the intended paper notional across visible depth. | Depth is too thin, fragmented, stale, or not supplied. |
| Taker fee estimate | Explicit fee assumption or `unknown_fee_blocker` reason code. | Packet assumes zero fees without support. |
| Total cost probability | Combined spread, slippage, fee, fill-risk, and settlement drag expressed in probability points where practical. | Costs are listed but not included in net edge. |

Cost policy should be conservative. If the packet cannot support a current,
side-aware executable price, it cannot be `go_for_manual_review`.

## Spread And Slippage Policy

Spread and slippage are separate risks. Spread measures the current gap between
best bid and best ask. Slippage measures the additional price movement expected
when a paper notional consumes available depth.

Minimum checks:

- quote timestamp is fresh enough for the event and decision time;
- selected side uses the executable ask or bid relevant to the hypothetical
  action, not a midpoint shortcut;
- spread width is shown in probability points;
- top-of-book size and visible depth support the paper notional;
- partial-fill risk is described when depth is insufficient;
- volatility near close time or news events is called out;
- stale, crossed, empty, or inconsistent books force `research`, `watch`, or
  `blocked`.

No packet should promote a candidate when its edge disappears after crossing the
spread or consuming realistic visible depth.

## Taker Fee Policy

Phase 1 must not hide fee assumptions. If the packet includes a fee estimate,
it must name the assumption source or explicitly state that the fee is a
conservative placeholder. If the fee schedule cannot be verified in the packet,
the packet must carry a visible reason code such as `fee_schedule_unverified`.

Required treatment:

- show fee drag separately from spread and slippage;
- include fee drag in total cost and net edge;
- avoid hardcoding fee assumptions as universal facts without packet evidence;
- mark the packet `research` when fee uncertainty can be resolved by a safe
  readonly source;
- mark the packet `blocked` when fee treatment is necessary but cannot be made
  auditable within Phase 1 boundaries.

Zero-fee assumptions are not allowed unless the packet provides a current,
auditable reason and still preserves the readonly boundary.

## Settlement Delay Policy

Probability-event returns are affected by time to resolution and final
settlement. Phase 1 packets must make the capital timeline visible even when no
live capital is deployed.

Required settlement review:

- market close time and expected resolution time;
- official resolution source and source-publication lag;
- dispute, challenge, finalization, or manual adjudication window where known;
- historical delay notes for similar events when available;
- ambiguous wording or source hierarchy risk;
- expected settlement delay in hours or a conservative unresolved label;
- required evidence that will prove the outcome.

Settlement delay becomes a blocker when the event cannot be resolved against a
clear source hierarchy, when the proof date is ambiguous, or when the packet
depends on a resolution path that is not safe to verify through readonly
sources.

## Capital Lockup Policy

Capital lockup is a risk even in paper-only analysis because it changes the
quality and comparability of net edge. A candidate with positive expected value
but long or uncertain settlement may be inferior to a lower-edge event with
faster, cleaner resolution.

Required lockup treatment:

- expected lockup window from hypothetical fill to final settlement;
- capital-at-risk proxy for the paper notional under review;
- opportunity-cost note when delay is material;
- unresolved or pending-settlement state in paper NAV or outcome summaries where
  applicable;
- reason code when lockup uncertainty changes the decision state.

Capital lockup policy does not approve capital allocation. It only records how
long a hypothetical paper unit would be unavailable and whether that delay
should reduce, pause, or block manual review.

## Correlation And Exposure Policy

Phase 1 packets must avoid treating related events as independent when they
share drivers, outcomes, sources, or resolution paths.

Exposure review should identify:

- repeated exposure to the same underlying event or question family;
- same candidate appearing across YES/NO mirrors, duplicates, or highly similar
  markets;
- common macro, political, crypto, sports, or source-driven catalyst;
- shared oracle, source hierarchy, or manual adjudication dependency;
- close-time clustering that could create simultaneous settlement or liquidity
  stress;
- concentration by specialist team, category, event template, or evidence
  source;
- contradiction between packet-level attractiveness and portfolio-level risk.

Correlation concerns should become `watch` when a trigger can reduce
uncertainty, `research` when duplicate or exposure mapping is incomplete, and
`blocked` when exposure cannot be bounded inside Phase 1 readonly evidence.

### Portfolio Probability-Event Watch Reasons

`PortfolioProbabilityEventReadinessReport` uses a closed, ordered reason enum.
Its canonical watch reasons are:

- `same_outcome_dependency_watch`
- `correlation_cluster_concentration_watch`
- `event_category_concentration_watch`
- `capital_lockup_concentration_watch`
- `extended_lockup_watch`
- `negative_edge_after_lockup_watch`
- `low_exit_liquidity_watch`

Rows use the matching `*_block` reason when a concentration or extended-lockup
block threshold is reached. A row with neither a block nor watch reason uses
`portfolio_probability_event_readiness_pass`.

Report reason aggregation is intentionally asymmetric. With no block reason,
the report preserves all canonical watch reasons present in its rows. Once any
block reason exists, the report summary retains block reasons plus
`low_exit_liquidity_watch` only; the other watch reasons remain row evidence but
are not repeated in the blocked report summary. Tests and adapters must preserve
this ordering and must not replace these reason codes with packet-level aliases.

## Manual Go/No-Go Risk Policy

The risk layer recommends one of the existing Phase 1 states. It must choose
the narrowest safe state and fail closed when material inputs are missing.

| State | Risk Policy Standard |
| --- | --- |
| `go_for_manual_review` | Evidence, executable price, spread, slippage, fee, settlement, lockup, and exposure checks are complete enough for a human to review. This is not approval to trade. |
| `no_go` | Packet is complete and shows insufficient net edge, excessive cost, weak liquidity, unacceptable settlement risk, or poor exposure quality. |
| `research` | A specific cost, fee, depth, settlement, resolution, exposure, or source gap can be answered by safe readonly follow-up. |
| `watch` | No current manual review is justified, but a named price, liquidity, evidence, or settlement trigger may change the packet. |
| `blocked` | The packet violates Phase 1 boundaries or has unresolvable cost, execution-like, settlement, capital lockup, correlation, exposure, or source-risk problems. |

When uncertain, choose the safer state:

- choose `research` over `go_for_manual_review` when an answerable input is
  missing;
- choose `watch` over `go_for_manual_review` when timing or price triggers are
  not yet satisfied;
- choose `no_go` over `watch` when a complete packet shows poor economics;
- choose `blocked` over `research` when the gap cannot be resolved safely or
  would require execution, auth, wallet, account, or exchange mutation.

## Required Risk Packet Section

Every Phase 1 probability-event packet should include a risk section in this
shape:

```text
risk_capital_settlement:
  paper_only: true
  report_only: true
  readonly: true
  selected_side:
  executable_price:
  executable_price_timestamp_utc:
  gross_edge_probability:
  spread_probability:
  slippage_probability:
  taker_fee_probability:
  fill_risk_probability:
  settlement_drag_probability:
  total_cost_probability:
  net_edge_probability:
  liquidity_status:
  depth_status:
  settlement_delay_status:
  expected_settlement_delay_hours:
  capital_lockup_status:
  expected_capital_lockup_hours:
  correlation_status:
  exposure_status:
  reason_codes:
  manual_go_no_go_status:
  required_follow_ups:
  blocked_reasons:
```

The section is complete only when the cost fields reconcile to net edge and the
manual status is supported by reason codes.

## Net Edge Convention

Use side-aware net edge. The cost term should include spread, slippage, taker
fee, fill-risk, and settlement or lockup drag where those estimates are
available.

```text
YES net edge = forecast_probability - executable_yes_price - total_cost_probability
NO net edge = (1 - forecast_probability) - executable_no_price - total_cost_probability
```

Positive net edge is necessary but not sufficient for `go_for_manual_review`.
The packet must still pass evidence quality, liquidity, settlement, capital
lockup, correlation, exposure, redaction, and readonly boundary checks.

## Packet-Level Blocker Reason Codes

Use explicit reason codes instead of vague risk summaries. Recommended Phase 1
risk codes include:

- `phase1_boundary_violation`
- `executable_price_missing`
- `midpoint_only_edge`
- `stale_quote`
- `spread_too_wide`
- `depth_insufficient`
- `slippage_unbounded`
- `fee_schedule_unverified`
- `cost_adjusted_edge_negative`
- `settlement_source_unclear`
- `settlement_delay_unbounded`
- `capital_lockup_material`
- `resolution_rule_ambiguous`
- `duplicate_market_exposure`
- `correlated_event_cluster`
- `category_concentration`
- `source_hierarchy_dependency`
- `manual_review_followup_required`

Reason codes should be specific enough for a reviewer to know what changed
would allow the packet to be reopened.

These are packet-level policy labels, not the accepted reason enum for
`PortfolioProbabilityEventReadinessReport`. A packet adapter may map module
evidence into a higher-level explanation, but it must preserve the exact module
reason codes above in the report payload and must not feed these aliases back
into the module constructor.

## Definition Of Done

This documentation node is satisfied when Phase 1 probability-event packets can
show:

- cost-adjusted net edge rather than raw forecast edge;
- separate spread, slippage, and taker fee assumptions;
- settlement delay and capital lockup visibility;
- correlation and exposure review;
- manual go/no-go status with reason codes;
- explicit preservation of paper-only, report-only, readonly boundaries.

Anything beyond this policy, including live execution design, wallet handling,
capital allocation, account-state reads, or automated order lifecycle work, is
outside Phase 1 and requires a later separately authorized phase.
