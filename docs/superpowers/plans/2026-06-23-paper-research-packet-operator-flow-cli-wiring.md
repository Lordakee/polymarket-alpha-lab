# Paper Research Packet Operator Flow CLI Wiring Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Wire the existing `paper-research-packet-operator-flow` CLI success path to build and print the pure `PaperResearchPacketOperatorFlowReport` without changing observable stdout or adding persistence.

**Architecture:** Keep the existing source -> packet -> quality -> history call sequence intact. After all three reports succeed, build a `PaperResearchPacketOperatorFlowReport` from the materialized reports and persistence booleans, then make the operator-flow summary printer consume that report.

**Tech Stack:** Python CLI module, pytest monkeypatching, existing pure operator-flow reducer.

## Global Constraints

- Phase 1 only: no live trading, auth, wallet, private keys, signing, orders, relayer, exchange, or network mutation.
- Do not add DSN/table/persist CLI flags.
- Do not introduce DB/env/psycopg changes in this node.
- Preserve the current operator-flow stdout line exactly.
- Preserve current redaction behavior and failure short-circuiting.
- Use `.venv/bin/python -m pytest`, not bare `pytest`.
- Run `codegraph sync` after code changes.
- OpenCode review is mandatory after tests pass with `zhipuai-coding-plan/glm-5.2 --variant max`.

---

### Task 1: Build Pure Report In CLI Success Path

**Files:**
- Modify: `src/polymarket_alpha_lab/cli.py`
- Modify: `tests/test_cli_paper_research_packet_operator_flow.py`

**Interfaces:**
- Consumes: `build_paper_research_packet_operator_flow_report(...)`, `PaperResearchPacketOperatorFlowConfig`.
- Produces: unchanged CLI stdout, plus an internal pure report object used by `_print_paper_research_packet_operator_flow_summary(...)`.

- [ ] **Step 1: Write failing CLI test**

Extend `test_operator_flow_cli_uses_injected_helpers_persists_reports_and_prints_status_summary` so it monkeypatches a fake `build_paper_research_packet_operator_flow_report` on `polymarket_alpha_lab.cli`, records the packet/quality/history reports and persistence booleans, returns a simple object with summary fields, and asserts it was called once.

Expected fake builder kwargs:

```python
{
    "packet_report": packet_report,
    "packet_persisted": True,
    "quality_report": quality_report,
    "quality_persisted": True,
    "quality_history_report": history_report,
    "config": PaperResearchPacketOperatorFlowConfig(...),
    "generated_at": datetime(..., tzinfo=UTC),
}
```

- [ ] **Step 2: Run focused RED**

Run:

```bash
.venv/bin/python -m pytest tests/test_cli_paper_research_packet_operator_flow.py::test_operator_flow_cli_uses_injected_helpers_persists_reports_and_prints_status_summary -q
```

Expected: FAIL because `cli.py` does not expose or call the pure operator-flow builder.

- [ ] **Step 3: Implement minimal CLI wiring**

Modify `src/polymarket_alpha_lab/cli.py` to:
- import `PaperResearchPacketOperatorFlowConfig` and `build_paper_research_packet_operator_flow_report`;
- build the pure report after `_run_paper_research_packet_quality_db_history(...)` succeeds;
- pass that pure report into `_print_paper_research_packet_operator_flow_summary(...)`;
- keep stage-specific summary printers unchanged.

- [ ] **Step 4: Run focused GREEN**

Run:

```bash
.venv/bin/python -m pytest tests/test_cli_paper_research_packet_operator_flow.py::test_operator_flow_cli_uses_injected_helpers_persists_reports_and_prints_status_summary -q
```

Expected: PASS and stdout remains unchanged.

- [ ] **Step 5: Run CLI operator-flow regression tests**

Run:

```bash
.venv/bin/python -m pytest tests/test_cli_paper_research_packet_operator_flow.py tests/test_cli_paper_research_packet_operator_flow_scope.py -q
```

Expected: PASS; failure redaction paths remain unchanged.
