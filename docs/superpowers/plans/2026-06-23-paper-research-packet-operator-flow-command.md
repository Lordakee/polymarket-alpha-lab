# Paper Research Packet Operator Flow Command Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a paper-only CLI command that runs the persisted paper research packet flow end-to-end: packet generation, packet quality persistence, and quality history readback.

**Architecture:** The command is an orchestration layer in `src/polymarket_alpha_lab/cli.py`. It reuses existing helpers rather than adding new domain logic: `_run_paper_research_packet(..., persist=True)`, `_run_paper_research_packet_quality(..., persist=True)`, and `_run_paper_research_packet_quality_db_history(...)`.

**Tech Stack:** Python CLI via `argparse`, existing Supabase/Postgres env config helpers, existing pytest CLI and AST scope test patterns.

## Global Constraints

- Phase 1 boundary: paper-only, report-only, readonly where applicable.
- No live trading, no authentication, no wallet/private-key handling, no signing, no order submission, no order cancellation, and no relayer/exchange mutation surfaces.
- Do not add DSN/table/enabled CLI flags; DB configuration must remain env-driven.
- Do not add financial advice or trade instruction copy.
- Preserve Decimal-only domain math; do not introduce floats.
- Reuse existing helper APIs instead of duplicating reducers or DB persistence logic.
- The operator flow must persist derived packet and quality reports, then read quality history using the quality DB in read-only/autocommit mode through the existing helper.

---

### Task 1: Add `paper-research-packet-operator-flow`

**Files:**
- Modify: `src/polymarket_alpha_lab/cli.py`
- Create: `tests/test_cli_paper_research_packet_operator_flow.py`
- Create: `tests/test_cli_paper_research_packet_operator_flow_scope.py`
- Modify: `README.md`

**Interfaces:**
- Consumes: `_run_paper_research_packet(...) -> tuple[object, bool]`, `_run_paper_research_packet_quality(...) -> object`, `_run_paper_research_packet_quality_db_history(...) -> object`
- Produces: CLI command `paper-research-packet-operator-flow` and summary printer `_print_paper_research_packet_operator_flow_summary(packet_report, packet_persisted, quality_report, quality_persisted, history_report)`

- [ ] **Step 1: Write the failing CLI behavior test**

Create `tests/test_cli_paper_research_packet_operator_flow.py` with tests that call:

```python
main(
    [
        "paper-research-packet-operator-flow",
        "--source-config-version",
        "queue-v1",
        "--action-status",
        "research_ready",
        "--research-status",
        "ready",
        "--limit",
        "25",
        "--packet-config-version",
        "paper-research-packet-v1",
        "--max-packet-rows",
        "7",
        "--min-score",
        "0.070000",
        "--quality-history-limit",
        "12",
    ],
    strategy_candidate_research_queue_loader=fake_loader,
    paper_research_packet_builder=fake_packet_builder,
    paper_research_packet_db_sink=fake_packet_sink,
    paper_research_packet_quality_runner=fake_quality_runner,
    paper_research_packet_quality_db_history_runner=fake_history_runner,
    client_factory=forbidden_client_factory,
)
```

Expected assertions:
- `fake_packet_sink` is called with the packet DB DSN/table from env.
- `fake_quality_runner` is called with the packet DB DSN/table from env and uses a `PaperResearchPacketQualityConfig`.
- `fake_history_runner` is called with the quality DB DSN/table from env, `limit=12`, and uses a `PaperResearchPacketQualityHistoryConfig`.
- Output contains `paper-research-packet-operator-flow:`, `packet_persisted=True`, `quality_persisted=True`, `quality_status=pass`, and `history_status=watch`.
- Output and stderr redact all source/packet/quality DSNs and table names.

- [ ] **Step 2: Write the failing AST scope test**

Create `tests/test_cli_paper_research_packet_operator_flow_scope.py` mirroring the existing scope-test helpers. Expected parser surface:

```python
{
    "--source-config-version",
    "source_config_version",
    "--action-status",
    "action_status",
    "--research-status",
    "research_status",
    "--limit",
    "limit",
    "--packet-config-version",
    "packet_config_version",
    "--max-packet-rows",
    "max_packet_rows",
    "--min-score",
    "min_score",
    "--quality-history-limit",
    "quality_history_limit",
}
```

Forbidden parser and branch fragments include `--dsn`, `--db-dsn`, `--table`, `auth`, `wallet`, `privatekey`, `order`, `submit`, `cancel`, `exchange`, `live`, and account/client construction.

- [ ] **Step 3: Verify RED**

Run:

```bash
.venv/bin/python -m pytest tests/test_cli_paper_research_packet_operator_flow.py tests/test_cli_paper_research_packet_operator_flow_scope.py -q
```

Expected: FAIL because `paper-research-packet-operator-flow` is not registered.

- [ ] **Step 4: Implement the minimal CLI orchestration**

In `src/polymarket_alpha_lab/cli.py`:
- Add parser `paper-research-packet-operator-flow`.
- Add injectable runner type alias only if needed; prefer the existing injected helpers already passed to `main`.
- Add a branch that validates `--limit` and `--quality-history-limit` as positive non-bool integers.
- Call `_run_paper_research_packet(..., persist=True, ...)`.
- Load packet DB config and quality DB config from env once the packet step has passed.
- Call `_run_paper_research_packet_quality(..., persist=True, quality_db_config=quality_db_config, ...)`.
- Call `_run_paper_research_packet_quality_db_history(..., dsn=quality_db_config.dsn, table_name=quality_db_config.table_name, limit=args.quality_history_limit, ...)`.
- Print a compact operator-flow summary and then reuse the existing packet, quality, and quality-history summary printers.
- On errors, print `paper-research-packet-operator-flow failed: ...` with existing redaction helpers.

- [ ] **Step 5: Verify GREEN**

Run:

```bash
.venv/bin/python -m pytest tests/test_cli_paper_research_packet_operator_flow.py tests/test_cli_paper_research_packet_operator_flow_scope.py -q
```

Expected: PASS.

- [ ] **Step 6: Update README**

Add a short command block under “Paper Research Packet Operator Commands”:

```bash
.venv/bin/polymarket-alpha-lab paper-research-packet-operator-flow --limit 100 --quality-history-limit 100
```

State that it is paper-only/report-only, persists packet and quality reports using env-driven DB configs, and prints a combined packet/quality/history operator summary.

- [ ] **Step 7: Run final verification and commit**

Run:

```bash
.venv/bin/python -m compileall -q src tests
.venv/bin/python -m pytest tests/test_cli_paper_research_packet_operator_flow.py tests/test_cli_paper_research_packet_operator_flow_scope.py tests/test_cli_paper_research_packet_quality.py tests/test_cli_paper_research_packet_quality_db_history.py -q
.venv/bin/python -m pytest -q
git diff --check
git diff --check --cached
codegraph sync
```

Then request OpenCode review with `zhipuai-coding-plan/glm-5.2 --variant max`, fix any Critical/Important findings, commit, and push to `origin/main`.
