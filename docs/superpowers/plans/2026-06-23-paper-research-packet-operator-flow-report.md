# Paper Research Packet Operator Flow Report Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a pure, durable report reducer for the paper research packet operator flow so later CLI, Supabase, and history nodes can depend on a stable schema instead of parsing printed text.

**Architecture:** Create a focused pure module that consumes the existing packet, quality, and quality-history reports and returns a frozen operator-flow report. The reducer owns status precedence and reason-code normalization; it must not import CLI, DB, env, network, auth, or live trading surfaces.

**Tech Stack:** Python dataclasses, standard-library `datetime`, existing paper research packet reducer modules, pytest.

## Global Constraints

- Phase 1 only: no live trading, auth, wallet, private keys, signing, orders, relayer, exchange, or network mutation.
- Pure reducer only: no DB, env, psycopg, CLI, network, or client imports in `src/polymarket_alpha_lab/paper_research_packet_operator_flow.py`.
- Keep hard flags exact and true: `paper_only=True`, `report_only=True`, `readonly=True`.
- Use frozen dataclasses and exact type checks; reject subclasses for reducer inputs and config.
- Keep reason codes deterministic and sorted.
- Do not add DSN/table CLI flags.
- Use `.venv/bin/python -m pytest`, not bare `pytest`.
- Run `codegraph sync` after code changes.

---

### Task 1: Pure Operator Flow Report Reducer

**Files:**
- Create: `src/polymarket_alpha_lab/paper_research_packet_operator_flow.py`
- Create: `tests/test_paper_research_packet_operator_flow.py`

**Interfaces:**
- Consumes: `PaperResearchPacketReport`, `PaperResearchPacketQualityReport`, `PaperResearchPacketQualityHistoryReport`.
- Produces: `PaperResearchPacketOperatorFlowConfig`, `PaperResearchPacketOperatorFlowReport`, `build_paper_research_packet_operator_flow_report(...)`.

- [ ] **Step 1: Write failing public API and default tests**

```python
def test_public_exports_include_report_config_builder_and_default_version() -> None:
    module = importlib.import_module(
        "polymarket_alpha_lab.paper_research_packet_operator_flow",
    )

    assert module.DEFAULT_PAPER_RESEARCH_PACKET_OPERATOR_FLOW_CONFIG_VERSION == (
        "paper-research-packet-operator-flow-v0"
    )
    assert {
        "DEFAULT_PAPER_RESEARCH_PACKET_OPERATOR_FLOW_CONFIG_VERSION",
        "PaperResearchPacketOperatorFlowConfig",
        "PaperResearchPacketOperatorFlowReport",
        "build_paper_research_packet_operator_flow_report",
    }.issubset(set(module.__all__))
```

- [ ] **Step 2: Run public API test to verify RED**

Run:

```bash
.venv/bin/python -m pytest tests/test_paper_research_packet_operator_flow.py::test_public_exports_include_report_config_builder_and_default_version -q
```

Expected: FAIL because the module does not exist yet.

- [ ] **Step 3: Add minimal module skeleton**

Create `src/polymarket_alpha_lab/paper_research_packet_operator_flow.py` with the default config version constant, frozen config/report dataclasses, and public `__all__`.

- [ ] **Step 4: Add failing builder tests**

Cover:
- valid pass report construction from existing packet, quality, and quality-history reports
- UTC normalization for `generated_at` and source report timestamps
- `blocked` precedence over `watch`
- `watch` precedence over `pass`
- deterministic reason-code ordering
- exact type rejection for config and all report inputs
- rejection when any hard flag is not exactly `True`
- pure module import scan rejecting DB/env/psycopg/CLI/network/client imports

- [ ] **Step 5: Run builder tests to verify RED**

Run:

```bash
.venv/bin/python -m pytest tests/test_paper_research_packet_operator_flow.py -q
```

Expected: FAIL on missing builder behavior.

- [ ] **Step 6: Implement minimal reducer**

Implement:

```python
def build_paper_research_packet_operator_flow_report(
    *,
    packet_report: PaperResearchPacketReport,
    packet_persisted: bool,
    quality_report: PaperResearchPacketQualityReport,
    quality_persisted: bool,
    quality_history_report: PaperResearchPacketQualityHistoryReport,
    config: PaperResearchPacketOperatorFlowConfig,
    generated_at: datetime,
) -> PaperResearchPacketOperatorFlowReport:
    ...
```

Status logic:
- `blocked` when packet was not persisted, quality was not persisted, packet quality status is `blocked`, or quality-history status is `blocked`.
- `watch` when packet quality status is `watch` or quality-history status is `watch`.
- `pass` otherwise.

Reason codes:
- `packet_not_persisted`
- `quality_not_persisted`
- `packet_quality_blocked`
- `packet_quality_watch`
- `packet_quality_history_blocked`
- `packet_quality_history_watch`
- `operator_flow_passed`

- [ ] **Step 7: Verify focused GREEN**

Run:

```bash
.venv/bin/python -m pytest tests/test_paper_research_packet_operator_flow.py -q
```

Expected: all tests in the new test file pass.

- [ ] **Step 8: Verify affected reducers**

Run:

```bash
.venv/bin/python -m pytest tests/test_paper_research_packet.py tests/test_paper_research_packet_quality.py tests/test_paper_research_packet_quality_history.py tests/test_paper_research_packet_operator_flow.py -q
```

Expected: all selected tests pass.

- [ ] **Step 9: Commit**

Run:

```bash
git add docs/superpowers/plans/2026-06-23-paper-research-packet-operator-flow-report.md src/polymarket_alpha_lab/paper_research_packet_operator_flow.py tests/test_paper_research_packet_operator_flow.py
git commit -m "feat: add operator flow pure report reducer"
```
