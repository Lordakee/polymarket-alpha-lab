# Phase 1 Recommendation Explainability

Date: 2026-07-12
Status: Phase 1 documentation node
Scope: Polymarket probability-event paper recommendation review

This document defines how Phase 1 recommendation explanations should describe
the eight review factors used by the paper recommendation layer:

- `edge`
- `cost`
- `liquidity`
- `freshness`
- `source_quorum`
- `resolution_clarity`
- `team_confidence`
- `manual_blockers`

It is documentation only. It does not authorize source changes, runtime
collection, schema changes, CLI changes, Supabase changes, execution/auth work,
wallet handling, account access, order handling, or live trading. Every
recommendation explanation remains paper-only, report-only, and readonly.

## Explainability Goal

Phase 1 recommendation explanations exist so a human reviewer can understand
why a probability-event candidate was promoted, watched, rejected, or blocked
inside the paper/report workflow.

An explanation should make four things explicit:

- which factor helped or hurt the paper recommendation;
- which supplied evidence supports the factor;
- which manual checks are still required before any operator decision;
- which blocker, if any, prevents the candidate from advancing in Phase 1.

The explanation must not turn score, rank, readiness, priority, paper notional,
or queue position into a trade instruction, investment recommendation, order
intent, execution approval, or capital-deployment instruction.

## Factor Summary

| Factor | Meaning | Manual Review Focus | Blocking Conditions |
| --- | --- | --- | --- |
| `edge` | Side-aware forecast advantage after comparing the team's supplied probability view with the supplied executable YES/NO price. | Confirm the side, forecast probability, market price, and net edge are tied to the same outcome and timestamp. | Missing side, missing forecast, missing executable price, negative or unexplained net edge, or edge based only on midpoint/indicative pricing. |
| `cost` | Friction that reduces gross edge, including spread, fees, slippage, fill risk, settlement drag, timing cost, and paper capital carry where supplied. | Confirm cost inputs are explicit, current, side-aware, and included in net edge instead of listed separately. | Costs are unavailable, stale, assumed to be zero without support, excluded from net edge, or large enough to erase the paper edge. |
| `liquidity` | Whether supplied depth, spread, and executable paper shares can support the paper review size without hiding fill or exit risk. | Check order-book timestamp, visible depth, spread width, requested paper shares, fill ratio, and any shallow-depth penalty. | No current depth, crossed/stale book, insufficient executable paper shares, excessive spread, or unsupported full-fill assumption. |
| `freshness` | Age and timeliness of market data, source evidence, cost inputs, forecast context, and settlement/resolution evidence. | Compare each evidence timestamp with the event timeline and the review time; require refresh when stale evidence could change the decision. | Missing timestamps, stale quote/source/cost/settlement context, failed refresh evidence, or event status that changed after the packet was assembled. |
| `source_quorum` | Whether enough independent and relevant sources support the market facts, forecast rationale, and resolution evidence. | Verify source families, official-source priority, corroboration, contradictions, and whether missing sources are named. | Single unsupported source, missing required official source, unresolved contradiction, source family collapse, or unverifiable evidence. |
| `resolution_clarity` | Whether the outcome definition, official resolution rules, and settlement path are clear enough to audit after the event. | Confirm the market question, outcomes, close time, official source hierarchy, ambiguity notes, and proof needed for each outcome. | Ambiguous outcome definition, missing or conflicting resolution rules, unclear official source, unsupported settlement path, or unresolvable dispute risk. |
| `team_confidence` | Specialist-team confidence in the forecast and evidence interpretation, including uncertainty, calibration context, and disagreement. | Review primary team ownership, confidence rationale, uncertainty range, calibration evidence, memory policy, and secondary-team disagreement. | Missing team owner, unsupported confidence, hidden disagreement, blocked/throttled memory without explanation, or confidence that overrides weak evidence. |
| `manual_blockers` | Explicit human-review blockers that prevent Phase 1 promotion even when other factor scores look favorable. | Confirm blocker owner, required follow-up, review deadline if applicable, and whether the blocker is resolvable inside readonly Phase 1 work. | Any unresolved unsafe boundary issue, missing required input, redaction failure, unowned research gap, non-auditable evidence, or request for live/actionable behavior. |

## Manual Review Method

Human reviewers should read the explanation in factor order, but status should
fail closed: one blocking factor is enough to keep the recommendation out of
`go_for_manual_review` or any downstream paper promotion.

Use this sequence:

1. Confirm `paper_only`, `report_only`, and `readonly` are true where the
   packet exposes hard flags.
2. Confirm the selected side, forecast, executable price, and cost inputs all
   describe the same market outcome.
3. Check that net edge survives cost, liquidity, freshness, and uncertainty
   adjustments.
4. Check source quorum and resolution clarity before relying on the edge score.
5. Check team confidence only after evidence and resolution facts are
   auditable.
6. Review `manual_blockers` last and let any unresolved blocker dominate the
   final paper status.

When evidence is incomplete but answerable through public readonly research,
route the candidate to `research` or `watch`. When the gap cannot be resolved
inside the Phase 1 boundary, route it to `blocked`.

## Status Guidance

Recommendation explanations should use narrow, review-oriented language:

| Status | Explanation Standard |
| --- | --- |
| `go_for_manual_review` | All eight factors are complete enough for human review, and no factor creates an unresolved blocker. |
| `research` | A specific readonly research gap exists, with the missing factor and follow-up clearly named. |
| `watch` | Evidence is not currently strong enough, but a named refresh trigger or event update could change the packet. |
| `blocked` | A required factor is unsafe, unavailable, unauditable, or outside the Phase 1 readonly boundary. |
| `reject` or `no_go` | The supplied evidence is complete enough to reject the paper candidate because edge, cost, liquidity, clarity, confidence, or blocker evidence is unfavorable. |

Use the safer status when factors disagree. `manual_blockers` dominates every
other factor. `resolution_clarity` and `source_quorum` should dominate raw
`edge` because a large apparent edge is not useful when the outcome or evidence
cannot be audited.

## Blocking Rules

A recommendation explanation must be `blocked` when any of these conditions is
present:

- hard safety flags are missing or not true;
- the packet asks for live trading, order handling, account access,
  authentication, signing, wallet handling, exchange mutation, or capital
  deployment;
- a required factor is missing and cannot be recovered through public readonly
  research;
- cost, liquidity, or freshness evidence is stale or absent enough to make the
  net edge unreliable;
- source quorum fails because required official evidence is missing,
  contradictory, or unverifiable;
- resolution clarity fails because the market outcome cannot be mapped to an
  auditable rule or source hierarchy;
- team confidence is unsupported, hides disagreement, or attempts to override
  weak evidence;
- redaction fails for credentials, tokens, wallet/account material, private
  identifiers, raw DSNs, or order-like sensitive values.

Blocked status is a paper/report status. It must not trigger recovery by
reading live accounts, querying wallets, fetching private order state, mutating
exchange state, or changing runtime configuration.

## Readonly Boundary

Allowed Phase 1 explanation activity:

- summarize supplied paper recommendation rows, reports, reason codes, and
  review packets;
- describe how the eight factors affected rank, queue status, readiness,
  priority, or paper recommendation state;
- name missing public evidence, stale inputs, unresolved contradictions, and
  manual follow-ups;
- preserve hard `paper_only=True`, `report_only=True`, and `readonly=True`
  flags where the underlying report exposes them;
- reference local report history or local Supabase/Postgres readback only at a
  documentation level when that surface already exists.

Forbidden Phase 1 explanation activity:

- live trading, investment advice, trade instructions, or capital deployment;
- position sizing or allocation approval outside paper/report diagnostics;
- account authentication, hosted account reads, wallet/private-key handling, or
  private order-state inspection;
- order signing, order submission, order cancellation, order replacement, or
  exchange mutation;
- creating new runtime collectors, CLI behavior, schemas, Supabase wiring,
  execution/auth paths, or live trading paths;
- treating score, edge, readiness, queue rank, or paper notional as an
  executable signal.

## Explanation Template

Use this structure when a Phase 1 report needs a human-readable explanation:

```text
recommendation_explanation:
  market_ref:
  selected_side:
  generated_at_utc:
  paper_only: true
  report_only: true
  readonly: true

  factors:
    edge:
      status:
      summary:
      manual_review:
      blocker:
    cost:
      status:
      summary:
      manual_review:
      blocker:
    liquidity:
      status:
      summary:
      manual_review:
      blocker:
    freshness:
      status:
      summary:
      manual_review:
      blocker:
    source_quorum:
      status:
      summary:
      manual_review:
      blocker:
    resolution_clarity:
      status:
      summary:
      manual_review:
      blocker:
    team_confidence:
      status:
      summary:
      manual_review:
      blocker:
    manual_blockers:
      status:
      summary:
      manual_review:
      blocker:

  final_review_status:
  dominant_factor:
  reason_codes:
  required_follow_ups:
  readonly_boundary_notes:
```

`summary` should explain the evidence, not merely repeat a score. `blocker`
should be empty only when the factor has no unresolved blocker. `dominant_factor`
should name the factor that most strongly explains the final review status,
especially when a blocker overrides otherwise favorable edge or score evidence.
