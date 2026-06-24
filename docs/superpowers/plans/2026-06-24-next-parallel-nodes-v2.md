# Next Parallel Implementation Nodes v2 (2026-06-24)

> Updated after current-tree audit at commit `d44931e`.

## Status Audit

The following previously selected modules already exist on `main` in the current checkout:

- `paper_autonomous_allocation_proposal_db_history_metrics_evaluation.py`
- `paper_autonomous_allocation_proposal_db_history_metrics_evaluation_load.py`
- CLI wiring for `paper-autonomous-allocation-proposal-db-history-metrics-evaluation`
- `paper_research_packet_operator_flow_db_history_gate.py`
- `paper_research_packet_operator_flow_db_history_gate_load.py`
- `paper_research_packet_quality_history.py`
- `paper_research_packet_quality_history_load.py`
- `paper_research_packet_db_history.py`
- `paper_research_packet_db_history_load.py`

Because those are already present, the next useful work should avoid duplication and should push the system toward the autonomous pipeline’s next missing layer.

## New Parallel Batch

1. **Autonomous screening gate transition reducer**
   - New module: `src/polymarket_alpha_lab/paper_autonomous_screening_decision_support_gate_transition.py`
   - Scope: pure adjacent transition reducer over chronological `PaperAutonomousScreeningDecisionSupportGateReport` inputs.
   - Deliverables:
     - deterministic status-transition and reason-code-change rows
     - frozen config/report dataclasses
     - focused behavior tests and scope tests
   - Why now: the current autonomous screening surface ends at gate snapshots; the system still lacks a paper-only/read-only transition view over those snapshots.

2. **Autonomous screening gate transition trend reducer**
   - New module: `src/polymarket_alpha_lab/paper_autonomous_screening_decision_support_gate_transition_trend.py`
   - Scope: pure trend reducer over the transition report family.
   - Deliverables:
     - trend summary over pass/watch/blocked prevalence and transition stability
     - frozen config/report dataclasses
     - focused behavior tests and scope tests
   - Why now: once the transition reducer exists, the next natural operator-facing layer is stability/trend without touching CLI/runtime wiring.

3. **Future paper-only proposal/broker abstraction design node**
   - Source: `docs/superpowers/specs/2026-06-13-automated-investment-roadmap.md`
   - Deliverables:
     - new design doc under `docs/superpowers/specs/`
   - Why now: the roadmap names the future execution shape but the repo still lacks a local paper-only design spec for the proposal/broker boundary.

4. **Verification/review ledger node**
   - Deliverables:
     - `.superpowers/sdd/progress.md` entry
     - full-suite verification
     - post-node review gate before push
   - Why now: durable progress tracking and review gates are required by the repo workflow.

## Parallel Safety

- Node 1 should own only the new transition module, its focused tests, and its scope tests.
- Node 2 should own only the new transition-trend module, its focused tests, and its scope tests.
- Node 3 should own only a new spec doc file.
- Node 4 should own only ledger/verification/review artifacts.

## Exit Criteria

- Each new module remains pure/report-only/read-only.
- Focused tests pass per node.
- Full test suite passes after the batch.
- Post-node review passes through local opencode (`zhipuai-coding-plan/glm-5.2`, variant `max`).
- Completed work is committed and pushed before expanding scope further.
