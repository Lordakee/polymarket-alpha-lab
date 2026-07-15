# Strategy Team Architecture Implementation Backlog

This backlog is a no-code review output for the current Phase 1 strategy and
team architecture. It is scoped to paper-only/report-only/readonly work and
does not propose live trading, authentication, wallet handling, private-key
handling, account reads, order construction, order signing, order submission,
order cancellation, order replacement, or exchange mutation.

## Review Basis

- Current docs: `docs/phase-1-multi-team-operating-model.md`,
  `docs/phase-1-team-memory.md`, `docs/strategy_pipeline.md`,
  `docs/strategy-candidate-decision-matrix.md`,
  `docs/paper-autonomous-screening-decision-support-gate.md`,
  `docs/action-gated-queue-decision-support.md`, and
  `docs/strategy-recommendation-layer.md`.
- Current orchestration and reducers: `src/polymarket_alpha_lab/strategy_cycle.py`,
  `src/polymarket_alpha_lab/cost_aware_event_strategy.py`,
  `src/polymarket_alpha_lab/paper_autonomous_candidate_selection.py`,
  `src/polymarket_alpha_lab/team_research_assignment.py`,
  `src/polymarket_alpha_lab/team_market_router.py`, and
  `src/polymarket_alpha_lab/team_memory_readiness_digest.py`.
- Current source-quality and memory surfaces include
  `src/polymarket_alpha_lab/strategy_candidate_source_quality_margin_gate_v2.py`,
  `src/polymarket_alpha_lab/strategy_source_coverage_quorum_v9.py`,
  `src/polymarket_alpha_lab/strategy_source_verified_edge_gate_v2.py`,
  `src/polymarket_alpha_lab/team_source_reliability.py`,
  `src/polymarket_alpha_lab/team_source_quorum.py`,
  `src/polymarket_alpha_lab/strategy_team_memory_decision_prior.py`, and
  `src/polymarket_alpha_lab/strategy_team_memory_source_feedback_v5.py`.

## Backlog

### Sequenced Next Steps

The next implementation pass should preserve a manual-first path and avoid
optimizing later-stage automation before the screening, source, memory, and
persistence contracts are explicit.

1. **Probability-event intake and screening:** normalize executable YES/NO
   prices, forecast probability, gross edge, costs, liquidity, resolution risk,
   and event-side reason codes before any specialist or selection step.
2. **Specialist-team routing:** assign a primary team and optional advisory
   teams from the taxonomy only after the candidate has a complete
   probability-event screen; unrouted markets become blocked operator work
   items.
3. **Long-term memory policy:** attach `allow`, `throttle`, or `block` memory
   state to each routed candidate as context for human review, not as an
   investment rank, size, or approval mechanism.
4. **Source-quality review:** evaluate official anchor freshness, independent
   source-family coverage, contradiction status, resolution-rule clarity, and
   specialist quorum before treating edge as actionable.
5. **Cost-aware manual-first decisioning:** compare gross edge to total cost,
   depth, spread, and capital lockup, then produce `pass`, `watch`, or
   `blocked` operator packets; do not create order intent, account fields, or
   execution instructions.
6. **Local Supabase persistence:** persist only the paper evidence, gate
   decisions, memory policy, source gaps, cost diagnostics, and operator packet
   history needed for auditability in local Supabase/Postgres.

### P0 - Connect the Manual-First Strategy Screen

**Goal:** make the operator-facing path explicit from Polymarket probability
event intake through specialist review, source-quality gates, cost-aware
decisioning, candidate selection, and manual review.

- Sequence this first because every downstream team, memory, source-quality,
  and persistence node needs the same probability-event row contract.
- Add an implementation node that wires `strategy_cycle.py` outputs into the
  existing decision matrix and selection sequence without changing the Phase 1
  boundary: `strategy_candidate_decision_matrix.py`,
  `strategy_candidate_research_queue.py`,
  `paper_autonomous_candidate_selection.py`, and
  `paper_autonomous_screening_decision_support_gate.py`.
- Preserve the current side-aware probability-event standard: executable YES/NO
  prices, forecast probability, net edge after costs, spread/depth, resolution
  risk, and reason codes.
- Defer any new learning, weighting, or persistence expansion until the selected
  candidate row already carries source quality, team route, memory policy, cost
  reason codes, and a manual operator next step.
- Acceptance checks: selected rows require source quality pass/watch context,
  cost-aware report context, team route, memory policy, and an operator next
  step; no selected row becomes an order intent or execution instruction.

### P0 - Make Team Memory a First-Class Gate

**Goal:** ensure long-term specialist memory can inform research context but
cannot rank investments, size positions, approve trades, or bypass source and
cost gates.

- Sequence this immediately after the manual-first screen so memory policy is
  attached to the routed candidate contract before operator packets and
  persistence history are expanded.
- Extend the implementation plan around `team_research_assignment.py`,
  `team_memory_readiness_digest.py`, `team_research_assignment_db_source.py`,
  and `strategy_team_memory_decision_prior.py`.
- Carry `allow`, `throttle`, and `block` memory policy into downstream operator
  packets and selection explanations, while keeping the current assignment rule
  that missing or blocked memory blocks assignment.
- Treat memory as an explainability and readiness input only: `allow` permits
  normal human review, `throttle` requires explicit manual follow-up, and
  `block` prevents assignment until the memory gap is resolved.
- Acceptance checks: every routed candidate has one primary specialist team,
  optional secondary teams, a memory policy, memory reason codes, and a clear
  manual follow-up when memory is throttled or blocked.

### P0 - Consolidate Specialist-Team Taxonomy and Routing

**Goal:** make the medium-scale specialist team model operationally consistent
across routing, assignment, diagnostics, memory, and future backlog nodes.

- Sequence this before source-quality and cost-aware refinements that depend on
  specialist ownership, quorum, and category-specific resolution-risk review.
- Use `strategy_team_taxonomy.py`, `team_taxonomy.py`, `team_market_router.py`,
  `team_research_assignment.py`, and `team_research_work_packet.py` as the
  implementation anchors.
- Add routing review coverage for politics, BTC, ETH, macro rates, equity
  indices, gold, oil, soccer, basketball, and other sports categories already
  documented in the Phase 1 operating model.
- Acceptance checks: each market category maps to a stable primary team,
  secondary teams remain advisory only, and unrouted markets become blocked
  operator work items rather than defaulting into a generalist path.

### P1 - Promote Source Quality Before Edge

**Goal:** enforce the docs rule that weak sources cannot be offset by large
forecast-vs-price edge.

- Sequence this before final candidate selection because source quality decides
  whether edge may proceed to `pass`, remain `watch`, or become `blocked`.
- Build the implementation node around
  `strategy_candidate_source_quality_margin_gate_v2.py`,
  `strategy_source_coverage_quorum_v9.py`,
  `strategy_source_verified_edge_gate_v2.py`,
  `team_source_reliability.py`, `team_source_quorum.py`, and
  `strategy_source_reliability_weighting_v3.py`.
- Normalize source evidence into official anchor age, independent source-family
  count, contradiction review status, resolution rule clarity, and specialist
  quorum fields before candidate selection.
- Emit source-gap tasks before cost or selection promotion when official
  anchors are stale, independent coverage is thin, contradictions are open, or
  resolution rules are unclear.
- Acceptance checks: decision-matrix candidate status requires adequate source
  quality or records explicit watch/blocked reason codes; source gaps produce
  research tasks via `strategy_team_source_gap_backlog_v10.py`.

### P1 - Tighten Cost-Aware Decisioning

**Goal:** keep strategy screening cost-aware and probability-event specific.

- Sequence this after source-quality review so expensive or illiquid candidates
  are rejected only after the evidence basis is visible and auditable.
- Use `cost_aware_event_strategy.py`, `cost_aware_snapshot_builder.py`,
  `liquidity_gate.py`, `cost_sensitivity.py`, and
  `strategy_resolution_delay_capital_lockup_penalty_v2.py` as implementation
  anchors.
- Ensure candidate rows preserve gross edge, total cost per share, net edge,
  executable price, depth, spread, resolution risk, and cost reason codes.
- Keep the output manual-first: cost diagnostics support operator review and
  candidate status only, with no order sizing, signing, submission, or
  execution-ready payload.
- Acceptance checks: candidate selection rejects missing net edge, insufficient
  executable depth, edge below threshold, and cost assumptions that consume the
  apparent probability edge.

### P1 - Persist Paper Evidence in Local Supabase

**Goal:** make the architecture backlog explicit that durable history for the
specialist-team screen belongs in local Supabase/Postgres only.

- Sequence this after the candidate row, team route, memory policy,
  source-quality fields, and cost diagnostics are stable enough to persist
  without creating churn in migrations or schemas prematurely.
- Use the existing local Supabase persistence plans and DB-source docs as
  implementation anchors, including team assignment history, readiness digest
  persistence, source-gap persistence, action-gated queue history, and paper
  strategy cycle report history.
- Persist paper evidence only: probability-event screen inputs, gate outcomes,
  source-quality reason codes, memory policy, cost diagnostics, manual operator
  packet status, and audit timestamps.
- Keep all raw DSNs validated through `validate_local_postgres_dsn` before use;
  do not introduce alternate stores, hosted database assumptions, JSONL/file
  journals as durable substitutes, or generic database abstraction layers.
- Acceptance checks: every persisted row is paper-only/report-only/readonly
  evidence, every write path targets local Supabase/Postgres, and readbacks can
  reconstruct why a candidate was `pass`, `watch`, or `blocked`.

### P2 - Add Cross-Team Learning and Source Feedback Loop

**Goal:** turn settled paper outcomes and source review results into durable
team learning inputs without creating automated strategy-weight tuning.

- Sequence this only after local persistence exists for paper outcomes, source
  reviews, and operator packet decisions; otherwise feedback cannot be audited
  back to the source and cost decisions that produced it.
- Anchor implementation in `strategy_team_learning_feedback_v3.py`,
  `strategy_team_memory_source_feedback_v5.py`,
  `strategy_team_forecast_calibration_memory_digest.py`,
  `team_memory_source_reliability_scorecard_digest.py`, and
  `team_specialist_outcome_feedback_priority_v2.py`.
- Feed settled outcomes, source reliability changes, and specialist error
  patterns back into memory readiness and operator review queues.
- Keep feedback diagnostic and human-readable: it can prioritize review,
  summarize error patterns, and update readiness context, but it cannot tune
  strategy weights or promote candidates automatically.
- Acceptance checks: learning outputs are report-only diagnostics with reason
  codes, calibration notes, and human improvement summaries; they do not alter
  live weights, create allocation instructions, or authorize execution.

### P2 - Build Manual Review Packets for Operators

**Goal:** make the manual-first execution boundary visible at the last mile.

- Sequence this after screening, team routing, memory, source-quality,
  cost-aware decisioning, and persistence contracts are stable so the packet is
  a readout of prior gates rather than a parallel decision engine.
- Use `team_research_work_packet.py`,
  `strategy_research_packet_human_review_brief_v10.py`,
  `action_gated_strategy_recommendation_queue.py`,
  `paper_autonomous_screening_decision_support_gate.py`, and
  `paper_autonomous_readiness_digest.py`.
- Produce an operator packet that shows team owner, source quality, memory
  policy, forecast-vs-price edge, costs, liquidity, resolution risk, selected
  side, reason codes, and the required manual next step.
- Make the packet the final manual-first artifact: it should explain what a
  human must review next, not encode execution parameters or imply automation
  approval.
- Acceptance checks: every final status is `pass`, `watch`, or `blocked` for
  paper review only; the packet contains no account, wallet, key, order, or
  live execution fields.

## Implementation Guardrails

- Keep durable persistence local Supabase/Postgres only and validate raw DSNs
  through `validate_local_postgres_dsn` before opening any DB connection.
- Keep reducers pure where current modules are pure; keep DB stores and CLI
  wiring at the process boundary.
- Add focused tests per node before implementation, including hard
  `paper_only=True`, `report_only=True`, and `readonly=True` checks wherever the
  target dataclasses expose those flags.
- Do not edit `paper_autonomous_candidate_selection.py` or
  `market_research_macro_cpi_revision_digest.py` as part of this review output;
  they are referenced only as existing implementation anchors.
