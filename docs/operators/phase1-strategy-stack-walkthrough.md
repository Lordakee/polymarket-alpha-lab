# Phase 1 Strategy Stack Operator Walkthrough

This walkthrough describes the manual operator path for reviewing a Phase 1
Polymarket strategy packet from market discovery through post-settlement
calibration. It is paper-only, report-only, and readonly. It does not authorize
live trading, investment advice, trade instructions, position advice, position
sizing, wallet handling, account authentication, order signing, order
submission, order cancellation, order replacement, exchange mutation, account
mutation, or any automated execution behavior.

Polymarket markets are probability events, not ordinary asset-price trades. The
operator is reviewing whether the research stack has produced a coherent
probability-event decision packet. The packet may compare a forecast probability
to executable market prices, but that comparison remains decision support for a
separate human review. It is not a trading signal, not a recommendation, and not
an instruction to buy, sell, allocate, size, or execute.

Use this walkthrough with
[Phase 1 Probability Event Go/No-Go Runbook](phase1-probability-event-go-no-go-runbook.md).

## Operator Goal

The operator's job is to walk the packet through the full strategy stack and
decide whether the packet is complete enough for a manual go/no-go review. The
operator does not convert a stack result into an automated order, position,
allocation, strategy-weight change, or execution request.

The practical outcomes are:

- `ready_for_manual_go_no_go`: the full stack is complete enough for a separate
  human go/no-go decision;
- `no_go`: the stack is complete and rejects the paper candidate;
- `research`: a named evidence, forecast, cost, source, or risk gap needs
  follow-up;
- `watch`: a named market, source, freshness, or settlement trigger should be
  monitored before a later review;
- `blocked`: the packet violates Phase 1 boundaries or cannot be reviewed
  safely.

## Phase 1 Boundary Check

Confirm the boundary before reviewing any edge, EV, or risk metric.

Pass conditions:

- packet flags are paper-only, report-only, and readonly where supported;
- all market data, source data, forecasts, costs, and risk metrics are public or
  local report evidence;
- any persistence is local Supabase/Postgres report evidence only;
- the packet does not request live order placement, order routing, signing,
  cancellation, replacement, wallet access, private-key access, account
  authentication, account reads, or exchange/account mutation;
- the packet does not present an investment recommendation, trade instruction,
  position-sizing instruction, strategy-weight tuning instruction, or financial
  advice;
- the packet says any real-world action is outside the automated system
  boundary and requires separate human judgment.

Fail closed to `blocked` if the packet asks the system to buy, sell, place,
submit, sign, cancel, replace, allocate, size, authenticate, use a wallet, read
an account, or mutate exchange state.

## Walkthrough Map

The Phase 1 stack should be reviewed in this order:

1. market discovery;
2. forecast context;
3. source coverage;
4. freshness SLA;
5. cost, EV, and Kelly-style sizing diagnostics;
6. portfolio risk;
7. manual go/no-go;
8. post-settlement calibration.

Each step depends on the prior steps. Do not promote a packet because a later
metric looks attractive if an earlier probability-event definition, source, or
freshness gate is incomplete.

## Step 1: Market Discovery

Start by confirming the market is a well-defined probability event.

Required checks:

- market reference, slug, question, outcome labels, close time, and expected
  resolution timing are present;
- the packet identifies the event category and specialist research route;
- the resolution rules are summarized and sourceable;
- the official source hierarchy is explicit;
- the candidate reason explains why this market entered review;
- the market is pending or otherwise relevant for research, not stale beyond
  useful review;
- YES and NO outcomes are treated as complementary event probabilities rather
  than ordinary long/short asset-price exposure.

Operator questions:

- What event must happen for each outcome to resolve?
- Which source or resolution rule decides the event?
- Is the uncertainty about an event outcome, or is the packet accidentally
  treating a probability market like a spot-price instrument?
- Is there any ambiguity in the question wording, close time, or resolution
  source that would make the forecast non-auditable?

Route to `blocked` if the market definition or resolution source cannot be made
auditable. Route to `research` when the gap is specific and answerable.

## Step 2: Forecast Context

Review the probability forecast before reviewing price edge. The forecast must
explain why the research estimate differs from the market-implied probability.

forecast_probability always denotes canonical Decimal P(YES), regardless of selected_side; selected_side identifies the paper-review side being evaluated and never reorients forecast_probability; P(NO) is 1 - P(YES).

Required checks:

- forecast probability is canonical event `P(YES)` and is not reoriented to the
  selected paper-review side;
- confidence, uncertainty range, and forecast timestamp are present;
- specialist team route and forecast rationale are included;
- major assumptions are listed separately from observed facts;
- known base rates, comparable events, or historical calibration notes are
  labeled as context, not proof;
- forecast reasoning maps directly to the market's resolution rules;
- memory use is marked `allow`, `throttle`, or `block` and does not override
  weak fresh evidence.

Operator questions:

- Does the forecast estimate the event probability that will settle the market?
- Are assumptions, source facts, and team judgment separable?
- Would the same forecast still make sense if the market price were hidden?
- Does the forecast avoid ranking, recommending, or instructing a position?

If the forecast is price-led, vague, stale, or disconnected from the resolution
criteria, route to `research` or `no_go`. If it asks for live execution or
sizing, route to `blocked`.

## Step 3: Source Coverage

Source coverage determines whether the forecast has enough evidence to support
manual review.

Minimum coverage:

- at least one primary or official source when one exists;
- corroborating secondary sources when primary evidence is incomplete;
- source timestamps and retrieval timestamps;
- source hierarchy and source reliability notes;
- contradiction summary with stronger-source tie-breakers;
- explicit missing-source list;
- redaction status for credentials, tokens, DSNs, wallet/account material, and
  order-like values.

Operator questions:

- Which claims are backed by official or primary sources?
- Which claims rely on secondary commentary or inference?
- Are contradictions resolved by source hierarchy, or still open?
- Are missing facts important enough to change the event probability?

Do not pass a packet on source count alone. A thin but official source can be
better than many weak secondary sources; a stale official source can still be
insufficient when the event changes quickly.

## Step 4: Freshness SLA

Freshness is a probability-event requirement. The correct evidence window
depends on the event type, time to close, resolution cadence, and expected news
flow.

Review checklist:

- each material source has an observed timestamp and retrieval timestamp;
- the packet states the applicable freshness SLA for the event type;
- prices, spreads, depth, and order book context are fresh enough for the packet
  generation time;
- fast-moving events identify watch triggers and refresh deadlines;
- slow-moving events explain why older evidence remains valid;
- stale facts are labeled as stale, not silently reused;
- no packet is promoted when the decisive source could have changed after the
  last refresh.

Suggested operator standard:

| Event Pattern | Freshness Expectation |
| --- | --- |
| Breaking news, live sports, rapidly changing politics, or intraday macro events | Refresh immediately before manual review and add watch triggers. |
| Scheduled releases, earnings-like events, or official announcements | Refresh against the official calendar and source before review. |
| Slow policy, regulatory, or long-horizon events | Use a documented SLA and verify no material update has occurred. |
| Near-close or near-resolution markets | Refresh event evidence and executable market context before any manual decision. |

Route to `watch` when a concrete future update is imminent. Route to `research`
when the packet lacks timestamped evidence. Route to `blocked` when freshness
cannot be established safely.

## Step 5: Cost, EV, and Kelly Diagnostics

Review cost-adjusted edge only after the probability-event definition, forecast,
coverage, and freshness checks pass.

Required checks:

- executable YES and NO price context is present, or the packet explains why it
  is unavailable;
- gross edge compares forecast probability to side-aware executable price;
- cost includes spread, fees, expected slippage, fill risk, liquidity depth,
  settlement timing, lockup drag, and resolution-risk adjustment where
  applicable;
- net EV remains positive after cost and uncertainty adjustments before it can
  advance to manual review;
- Kelly-style diagnostics, if present, are labeled as research diagnostics only;
- any Kelly fraction is capped, stress-tested, and never converted into a
  position-size instruction;
- midpoint-only edge, stale order book context, or optimistic full-fill
  assumptions are rejected.

```text
YES side probability = forecast_probability
NO side probability = 1 - forecast_probability
```

Operator questions:

- Is the market price executable, or just a displayed midpoint?
- Does the net edge survive realistic friction and uncertainty?
- Is the Kelly diagnostic being used to understand edge quality rather than to
  size a position?
- Would the packet still be acceptable if spread, slippage, or settlement drag
  worsened?

Fail to `no_go` when cost-adjusted EV is insufficient. Route to `research` when
cost, depth, or settlement evidence is incomplete. Route to `blocked` if any
metric becomes a live sizing or execution instruction.

## Step 6: Portfolio Risk

Portfolio risk is reviewed as paper risk evidence only. It does not authorize
capital allocation or position sizing.

Required checks:

- paper notional exposure is labeled as simulated or paper-only;
- event, category, source, timing, and settlement-risk concentrations are
  visible;
- correlated markets and duplicate event exposure are identified;
- pending settlement, dispute windows, and capital-lockup exposure are shown;
- drawdown, NAV, and concentration metrics are based on paper evidence only;
- portfolio risk status does not override weak market-level evidence;
- the packet avoids instructions to rebalance, allocate, increase, decrease, or
  hedge a real position.

Operator questions:

- Does this candidate concentrate risk in one event family, information source,
  resolution mechanism, or settlement window?
- Are correlated markets counted separately and together?
- Does portfolio risk change the packet status to `watch`, `research`, or
  `no_go` even if standalone EV is positive?
- Are all risk views descriptive rather than executable?

Route to `no_go` for unacceptable concentration, unresolved settlement backlog,
or paper drawdown risk. Route to `research` when correlation, pending exposure,
or settlement risk cannot be traced.

## Step 7: Manual Go/No-Go

Only after the full stack is complete should the operator assign a manual
go/no-go readiness status.

Manual decision standards:

| Status | Operator Standard |
| --- | --- |
| `ready_for_manual_go_no_go` | Market definition, forecast context, source coverage, freshness, cost-adjusted EV, and portfolio risk are complete enough for separate human go/no-go review. This is not an execution instruction. |
| `no_go` | The packet is complete and shows insufficient edge, weak evidence, unacceptable cost, poor liquidity, excessive risk, or unfavorable settlement/resolution risk. |
| `research` | A named gap has an owner and deadline before review can continue. |
| `watch` | A named trigger, source refresh, price movement, or resolution update could justify later review. |
| `blocked` | The packet violates Phase 1 boundaries or cannot be reviewed safely. |

The manual decision record should include:

- packet id and generated timestamp;
- selected market and outcome side under review;
- forecast probability, confidence, and uncertainty range;
- source coverage status and freshness status;
- cost-adjusted EV status and Kelly diagnostic status;
- portfolio risk status;
- settlement and resolution-risk notes;
- reason codes;
- required follow-ups or watch triggers;
- explicit paper-only, report-only, and readonly flags.

When uncertain between statuses, choose the safer status. Choose `research` over
`ready_for_manual_go_no_go`, `watch` over premature rejection when a concrete
near-term trigger matters, and `blocked` over `research` when the issue cannot
be resolved inside Phase 1 boundaries.

## Step 8: Post-Settlement Calibration

After the market resolves, use the settled outcome for calibration evidence.
Post-settlement calibration is descriptive learning, not retroactive approval
and not a transition to live execution.

Calibration compares canonical `P(YES)` with an actual YES target of `1` and actual NO target of `0`, regardless of which paper-review side was selected.

Persisted `actual_outcome` uses the string enum `yes` or `no`; calibration maps `yes` to Decimal target `1` and `no` to Decimal target `0`; `selected_side` never changes that mapping.

Required checks:

- resolution outcome and final source are recorded;
- final settlement timing, dispute window, and any resolution ambiguity are
  noted;
- original forecast probability, confidence, uncertainty range, and source
  state are preserved;
- realized outcome is compared to the original forecast without rewriting the
  original packet;
- calibration notes distinguish forecast error, source error, freshness error,
  cost error, liquidity error, and resolution-rule error;
- team memory updates, if allowed, summarize lessons without storing secrets,
  account data, wallet material, or execution artifacts;
- unresolved, disputed, or ambiguous settlement is marked as incomplete
  calibration evidence.

Operator questions:

- Did the event resolve according to the expected source hierarchy?
- Was the original forecast directionally and probabilistically calibrated?
- Did evidence quality, freshness, or source coverage explain the result?
- Did cost, spread, settlement lag, or liquidity make the paper edge worse than
  expected?
- Should future packets adjust research discipline, or only record this as a
  normal probabilistic miss?

Post-settlement calibration should improve future probability-event research
quality. It must not produce live trading permission, account access, order
paths, position sizing, strategy-weight tuning, recommendations, trade
instructions, or financial advice.

## Operator Packet Checklist

Use this compact checklist before marking the stack complete:

```text
packet_id:
generated_at_utc:
paper_only: true
report_only: true
readonly: true

market_discovery:
  market_ref:
  question:
  outcomes:
  close_time_utc:
  resolution_source:
  probability_event_confirmed:
  discovery_status:

forecast_context:
  selected_side:
  forecast_probability:
  confidence:
  uncertainty_range:
  specialist_team:
  memory_policy:
  forecast_status:

source_coverage:
  primary_sources:
  secondary_sources:
  missing_sources:
  contradiction_summary:
  redaction_status:
  coverage_status:

freshness_sla:
  event_freshness_sla:
  latest_source_observed_at_utc:
  latest_market_context_at_utc:
  stale_facts:
  watch_triggers:
  freshness_status:

cost_ev_kelly:
  executable_yes_price:
  executable_no_price:
  gross_edge_probability:
  total_cost_probability:
  net_edge_probability:
  ev_status:
  kelly_diagnostic_status:

portfolio_risk:
  paper_exposure_status:
  concentration_status:
  correlation_status:
  settlement_backlog_status:
  portfolio_risk_status:

manual_go_no_go:
  operator_status:
  reason_codes:
  required_follow_ups:
  boundary_notes:

post_settlement_calibration:
  settlement_status:
  resolved_outcome:
  final_resolution_source:
  calibration_status:
  lessons_for_future_research:
```

## Escalation Rules

Escalate to `blocked` when:

- any step requires authentication, wallet/account access, private keys, account
  reads, order ids, signing, submission, cancellation, replacement, or exchange
  mutation;
- the packet frames Polymarket as ordinary asset-price trading instead of
  probability-event research;
- the packet presents recommendation, ranking, trade instruction, financial
  advice, strategy-weight tuning, allocation, or position sizing;
- the market's resolution source cannot be identified;
- source evidence is unsafe, untraceable, materially contradicted, or
  unrecoverably stale;
- cost, EV, Kelly, or portfolio risk outputs are converted into executable
  instructions;
- local persistence boundaries or redaction boundaries are violated.
