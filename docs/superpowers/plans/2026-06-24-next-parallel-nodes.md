# Next Parallel Implementation Nodes (2026-06-24)

> Created from repo state at commit `d44931e` and the existing roadmap/plans.

## Selected Batch

These nodes are intentionally non-overlapping so they can be developed in parallel.

1. **Allocation proposal DB-history metrics evaluation node**
   - Plan source: `docs/superpowers/plans/2026-06-24-paper-autonomous-allocation-proposal-db-history-metrics-evaluation.md`
   - Deliverables:
     - pure evaluation reducer
     - read-only loader composition
     - CLI command wiring
     - docs/exports alignment
   - Why now: it converts already-persisted allocation proposal history metrics into deterministic `pass/watch/blocked` diagnostics and recommended next step, which is the last missing operator-facing readiness signal before any further autonomous-allocation refinement work.

2. **Research packet quality DB-history node**
   - Plan source: `docs/superpowers/plans/2026-06-23-paper-research-packet-next-phase.md`
   - Deliverables:
     - pure packet quality reducer
     - pure packet DB-history readback reducer and loader
   - Why now: it strengthens the research-packet evidence layer without touching CLI/runtime wiring yet, and it remains pure/report-only.

3. **Future proposal/broker abstraction design node**
   - Source: `docs/superpowers/specs/2026-06-13-automated-investment-roadmap.md`
   - Deliverables:
     - new design doc under `docs/superpowers/specs/` for a future paper-only proposal/broker abstraction
   - Why now: the roadmap already names the future execution shape (`TradeProposal -> RiskGate -> Broker -> OrderLifecycleManager -> Reconciler -> AuditJournal`), but no local spec yet formalizes the paper-only boundary, staged promotion gates, or module-local interfaces.

4. **Node verification/review ledger node**
   - Source: repo workflow rules in `AGENTS.md`
   - Deliverables:
     - progress ledger entry
     - final verification/review package after the above nodes land
   - Why now: durable progress tracking prevents duplicate agent work across compactions and matches the repo’s established agent workflow.

## Parallel Safety

- Node 1 should own the new evaluation reducer/loader/tests/docs scope files and the CLI integration surface.
- Node 2 should own only `paper_research_packet_quality*.py`, `paper_research_packet_db_history*.py`, and their scoped tests.
- Node 3 should own only a new design doc file.
- Node 4 should own only `.superpowers/sdd/progress.md` and review/verification artifacts until final review.

## Exit Criteria

- Focused tests pass per node.
- Full test suite passes after each implementation batch.
- Post-node review passes through local opencode (`zhipuai-coding-plan/glm-5.2`, variant `max`).
- Completed node is committed and pushed to GitHub before the next batch expands scope.
