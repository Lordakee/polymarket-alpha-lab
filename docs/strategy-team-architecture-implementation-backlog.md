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

### P0 - Connect the Manual-First Strategy Screen

**Goal:** make the operator-facing path explicit from Polymarket probability
event intake through specialist review, source-quality gates, cost-aware
decisioning, candidate selection, and manual review.

- Add an implementation node that wires `strategy_cycle.py` outputs into the
  existing decision matrix and selection sequence without changing the Phase 1
  boundary: `strategy_candidate_decision_matrix.py`,
  `strategy_candidate_research_queue.py`,
  `paper_autonomous_candidate_selection.py`, and
  `paper_autonomous_screening_decision_support_gate.py`.
- Preserve the current side-aware probability-event standard: executable YES/NO
  prices, forecast probability, net edge after costs, spread/depth, resolution
  risk, and reason codes.
- Acceptance checks: selected rows require source quality pass/watch context,
  cost-aware report context, team route, memory policy, and an operator next
  step; no selected row becomes an order intent or execution instruction.

### P0 - Make Team Memory a First-Class Gate

**Goal:** ensure long-term specialist memory can inform research context but
cannot rank investments, size positions, approve trades, or bypass source and
cost gates.

- Extend the implementation plan around `team_research_assignment.py`,
  `team_memory_readiness_digest.py`, `team_research_assignment_db_source.py`,
  and `strategy_team_memory_decision_prior.py`.
- Carry `allow`, `throttle`, and `block` memory policy into downstream operator
  packets and selection explanations, while keeping the current assignment rule
  that missing or blocked memory blocks assignment.
- Acceptance checks: every routed candidate has one primary specialist team,
  optional secondary teams, a memory policy, memory reason codes, and a clear
  manual follow-up when memory is throttled or blocked.

### P1 - Consolidate Specialist-Team Taxonomy and Routing

**Goal:** make the medium-scale specialist team model operationally consistent
across routing, assignment, diagnostics, memory, and future backlog nodes.

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

- Build the implementation node around
  `strategy_candidate_source_quality_margin_gate_v2.py`,
  `strategy_source_coverage_quorum_v9.py`,
  `strategy_source_verified_edge_gate_v2.py`,
  `team_source_reliability.py`, `team_source_quorum.py`, and
  `strategy_source_reliability_weighting_v3.py`.
- Normalize source evidence into official anchor age, independent source-family
  count, contradiction review status, resolution rule clarity, and specialist
  quorum fields before candidate selection.
- Acceptance checks: decision-matrix candidate status requires adequate source
  quality or records explicit watch/blocked reason codes; source gaps produce
  research tasks via `strategy_team_source_gap_backlog_v10.py`.

### P1 - Tighten Cost-Aware Decisioning

**Goal:** keep strategy screening cost-aware and probability-event specific.

- Use `cost_aware_event_strategy.py`, `cost_aware_snapshot_builder.py`,
  `liquidity_gate.py`, `cost_sensitivity.py`, and
  `strategy_resolution_delay_capital_lockup_penalty_v2.py` as implementation
  anchors.
- Ensure candidate rows preserve gross edge, total cost per share, net edge,
  executable price, depth, spread, resolution risk, and cost reason codes.
- Acceptance checks: candidate selection rejects missing net edge, insufficient
  executable depth, edge below threshold, and cost assumptions that consume the
  apparent probability edge.

### P2 - Add Cross-Team Learning and Source Feedback Loop

**Goal:** turn settled paper outcomes and source review results into durable
team learning inputs without creating automated strategy-weight tuning.

- Anchor implementation in `strategy_team_learning_feedback_v3.py`,
  `strategy_team_memory_source_feedback_v5.py`,
  `strategy_team_forecast_calibration_memory_digest.py`,
  `team_memory_source_reliability_scorecard_digest.py`, and
  `team_specialist_outcome_feedback_priority_v2.py`.
- Feed settled outcomes, source reliability changes, and specialist error
  patterns back into memory readiness and operator review queues.
- Acceptance checks: learning outputs are report-only diagnostics with reason
  codes, calibration notes, and human improvement summaries; they do not alter
  live weights, create allocation instructions, or authorize execution.

### P2 - Build Manual Review Packets for Operators

**Goal:** make the manual-first execution boundary visible at the last mile.

- Use `team_research_work_packet.py`,
  `strategy_research_packet_human_review_brief_v10.py`,
  `action_gated_strategy_recommendation_queue.py`,
  `paper_autonomous_screening_decision_support_gate.py`, and
  `paper_autonomous_readiness_digest.py`.
- Produce an operator packet that shows team owner, source quality, memory
  policy, forecast-vs-price edge, costs, liquidity, resolution risk, selected
  side, reason codes, and the required manual next step.
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
