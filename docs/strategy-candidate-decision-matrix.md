# Strategy Candidate Decision Matrix

This document defines the paper-only, report-only, readonly decision process
for screening Polymarket probability events into strategy actions. It is an
operator-facing strategy guide, not live trading authorization, order intent,
position advice, or position sizing.

The central rule is that information quality comes before price edge. A market
with an attractive forecast-vs-price gap is not a candidate if the evidence is
stale, weakly sourced, hard to verify, or vulnerable to ambiguous resolution.

forecast_probability always denotes canonical Decimal P(YES), regardless of selected_side; selected_side identifies the paper-review side being evaluated and never reorients forecast_probability; P(NO) is 1 - P(YES).

## Screening Flow

Use this sequence for every probability-event market before assigning an
action:

1. Capture the market question, outcomes, close time, resolution rules, and
   official resolution source.
2. Verify information quality with fresh, source-traceable evidence. Prefer
   official Polymarket data for market structure and authoritative primary
   sources for event facts.
3. Build a canonical `P(YES)` forecast and compare the derived side probability
   with executable YES/NO prices, not only displayed midpoint or stale
   last-trade prices.
4. Subtract estimated trading costs, including spread, fees, slippage,
   partial-fill risk, settlement timing, and capital tie-up.
5. Check liquidity and executable depth at the intended paper notional.
6. Review resolution risk, including unclear rules, source hierarchy gaps,
   disputed outcomes, stale close timing, and off-platform dependencies.
7. Apply team memory and calibration context before assigning one of the
   candidate, research, watch, or blocked actions.

## Decision Matrix

| Dimension | Promote Toward Candidate | Route to Research or Watch | Block |
| --- | --- | --- | --- |
| Information quality | Fresh, traceable evidence from reliable primary or high-quality secondary sources; source timestamps are known. | Evidence is plausible but incomplete, stale, single-sourced, or missing a freshness check. | Evidence cannot be traced, is contradicted by stronger sources, or relies on unverifiable claims. |
| Forecast-vs-price edge | Team forecast differs from executable market price by enough gross edge to survive costs and uncertainty. | Gross edge is plausible but thin, source-sensitive, or dependent on a pending update. | No positive edge after reasonable uncertainty adjustments, or forecast cannot be justified. |
| Trading costs | Estimated spread, fees, slippage, settlement drag, and capital cost leave positive net edge. | Cost estimate is incomplete, unstable, or close to consuming the edge. | Costs consume the edge or cannot be estimated from executable market data. |
| Liquidity | Order book depth supports the intended paper size with acceptable spread and fill assumptions. | Depth exists but is thin, fragmented, volatile, or size-constrained. | Market is too illiquid, crossed/stale, closed, or has insufficient executable depth. |
| Resolution risk | Rules, outcome definitions, and official source hierarchy are clear enough for clean adjudication. | Rules are mostly clear but depend on late official updates, manual interpretation, or proxy evidence. | Resolution terms are ambiguous, disputed, missing, or likely to depend on unreliable sources. |
| Team memory and calibration | Responsible team has adequate settled samples, acceptable calibration, and reusable source-quality memory for the event type. | Team memory is sparse, stale, biased, or mixed; require reviewer escalation or lower reliance. | Memory gates are blocked, calibration is materially poor, or prior failures match the current setup. |

## Edge Standard

Forecast edge must be side-aware:

- YES gross edge equals the team's event probability forecast minus the
  executable YES price.
- NO gross edge equals one minus the team's event probability forecast minus
  the executable NO price.
- Net edge equals gross edge minus estimated spread, fees, slippage,
  partial-fill cost, settlement timing drag, and any explicit capital-cost
  adjustment.

Do not promote a market only because the midpoint looks mispriced. Candidate
status requires executable-price evidence and a written reason the forecast is
better informed than the current market price.

## Information Quality Gate

Information quality is the first pass/fail gate. A research packet should
record:

- source URL, API endpoint, or named official source;
- source family and retrieval timestamp in UTC;
- whether the source is primary, secondary, derived, or commentary;
- freshness caveats and known missing facts;
- contradictions between sources and the stronger source used;
- why the source set is sufficient for the market's resolution path.

When source quality is weak, the correct action is research, watch, or blocked,
even if the raw edge appears large.

## Cost and Liquidity Gate

Cost and liquidity checks should use executable market data whenever available:

- bid/ask and spread by side;
- depth available at the intended paper notional;
- expected fill ratio and price impact;
- fee and settlement assumptions;
- whether the market is stale, inactive, close to closing, or unusually
  volatile.

Thin markets can still be useful research candidates, but they should not be
promoted as strategy candidates unless the edge survives realistic fill and
cost assumptions.

## Resolution Risk Gate

Resolution risk should be explicit before a market advances. Review:

- exact rule text and any linked resolution source;
- whether the outcome depends on a single official publication, a third-party
  feed, a human adjudicator, or a proxy metric;
- whether the event has ambiguous wording, edge-case thresholds, time-zone
  sensitivity, delayed reporting, revisions, or dispute history;
- whether close time and resolution timing create stale-evidence or
  settlement-lag risk.

If the team cannot explain how the market resolves and what evidence will prove
the outcome, the market is blocked until that gap is closed.

## Team Memory and Calibration

Long-term team memory is used to improve research quality, not to authorize
execution. Before a market becomes a candidate, check whether the responsible
team has:

- enough settled examples in the same category or event archetype;
- acceptable calibration, bias, and error patterns for similar forecasts;
- source-reliability memory for the sources used in the current packet;
- known failure modes from prior postmortems;
- reviewer capacity for markets where memory is sparse or stale.

Strong memory can reduce redundant research, but it does not override weak
sources, negative net edge, poor liquidity, or unclear resolution rules.

## Action States

| Action | Use When | Required Next Step |
| --- | --- | --- |
| `candidate` | Information quality is strong, net forecast-vs-price edge survives costs, liquidity is usable, resolution risk is acceptable, and team calibration is adequate. | Add to the paper candidate set with source trace, side, forecast, executable price, net edge, liquidity status, resolution notes, and owner. |
| `research` | There may be edge, but a concrete evidence, cost, liquidity, resolution, or calibration gap remains answerable. | Assign a specialist owner, required sources, and recheck deadline; do not treat as candidate until the gap is closed. |
| `watch` | No current candidate decision is justified, but future price moves, source updates, liquidity changes, or event milestones may create a decision point. | Record trigger conditions, refresh cadence, and the next source or price check. |
| `blocked` | The market has unresolvable evidence gaps, unacceptable resolution risk, insufficient liquidity, negative net edge, blocked memory gates, or violates the Phase 1 boundary. | Record the blocking reason and only reopen after the specific blocker changes. |

## Review Discipline

Every candidate decision should leave enough context for replay:

- the forecast, market price, cost estimate, and net edge at decision time;
- source evidence and freshness;
- resolution-risk notes;
- liquidity and executable-depth notes;
- team calibration or memory status;
- the action state and reason codes.

This keeps candidate selection auditable and helps the team compare later
outcomes with the original forecast, evidence, and decision logic.
