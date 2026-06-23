# Paper Research Packet Operator Flow CLI Persistence Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Wire `paper-research-packet-operator-flow` to optionally persist its pure operator-flow report through env-only Supabase/Postgres configuration.

**Architecture:** Keep the source -> packet -> quality -> history -> operator-flow sequence intact. Validate the operator-flow DB env before upstream writes when it is enabled, then persist the built operator-flow report before printing the unchanged summary line. Keep all DB configuration env-based; no CLI DSN/table/persist flags are added.

**Tech Stack:** Python CLI module, pytest monkeypatching, frozen dataclass reports, optional lazy psycopg adapter, README and `.env.example` documentation, CodeGraph, local OpenCode review with `zhipuai-coding-plan/glm-5.2 --variant max`.

## Global Constraints

- Phase 1 only: paper-only, report-only, readonly.
- No live trading, auth, wallet, private-key, signing, order, cancellation, replacement, relayer, account, exchange, or network mutation surface.
- Do not add DSN/table/persist CLI flags for operator-flow persistence.
- Persistence must be env-gated and default disabled.
- Preserve the existing first stdout line exactly.
- On sink failure, do not print a partial success summary.
- Redact source, packet, quality, and operator-flow DSNs/table names plus payload/question/hash fields from errors.
- Use `.venv/bin/python -m pytest`, not bare `pytest`.
- Use CodeGraph before grep/find/manual source reads while implementing.
- Run `codegraph sync` after code changes.
- OpenCode review is mandatory after tests pass; use local OpenCode with `zhipuai-coding-plan/glm-5.2`, `--variant max`, and a hard read-only prompt.

---

## File Structure

- Modify `src/polymarket_alpha_lab/cli.py`
  - Import `from_paper_research_packet_operator_flow_db_env`.
  - Add an injectable `paper_research_packet_operator_flow_db_sink`.
  - Validate operator-flow DB config before packet/quality writes when enabled.
  - Persist the built operator-flow report before printing.
  - Extend operator-flow error redaction to include operator-flow DB DSN/table.
- Modify `tests/test_cli_paper_research_packet_operator_flow.py`
  - Add env helpers/imports for operator-flow DB config.
  - Add persistence, default-disabled, preflight-DSN, and sink-failure redaction coverage.
- Modify `tests/test_cli_paper_research_packet_operator_flow_scope.py`
  - Keep the parser surface unchanged.
  - Add operator-flow DB flag names to forbidden parser/runtime checks.
- Modify `README.md`
  - Document optional env-driven operator-flow report persistence and unchanged stdout/no CLI flags.
- Modify `.env.example`
  - Add packet, quality, and operator-flow DB env placeholders.
- Modify `tests/test_supabase_cycle_snapshot_config.py`
  - Keep the exact `.env.example` whitelist in sync with the new packet, quality, and operator-flow DB env placeholders.

---

### Task 1: CLI Env-Gated Operator-Flow Persistence

**Files:**
- Modify: `src/polymarket_alpha_lab/cli.py`
- Modify: `tests/test_cli_paper_research_packet_operator_flow.py`
- Modify: `tests/test_cli_paper_research_packet_operator_flow_scope.py`

**Interfaces:**
- Consumes:
  - `from_paper_research_packet_operator_flow_db_env(env=None)`
  - `insert_paper_research_packet_operator_flow_report_with_psycopg(dsn, report, *, table_name=...)`
  - existing `build_paper_research_packet_operator_flow_report(...)`
- Produces:
  - `paper_research_packet_operator_flow_db_sink: Callable[..., object] | None` injection point on `main(...)`
  - env-only operator-flow report persistence after pure report construction
  - unchanged stdout line:
    `paper-research-packet-operator-flow: packet_persisted=True packet_row_count=2 quality_status=watch quality_persisted=True history_status=pass history_source_report_count=4`

- [ ] **Step 1: Write failing persistence test**

Add this behavior to `tests/test_cli_paper_research_packet_operator_flow.py`:

```python
def test_operator_flow_cli_persists_operator_flow_report_when_env_enabled_without_changing_stdout(...):
    # Set source, packet, quality, and operator-flow DB env vars.
    # Use fake loader, packet builder, packet sink, quality runner,
    # quality insert, history runner, operator-flow builder, and
    # fake_operator_flow_db_sink.
    # Assert event order:
    # load-source -> build-packet -> persist-packet -> build-quality ->
    # persist-quality -> history -> operator-flow -> persist-operator-flow
    # Assert fake_operator_flow_db_sink receives:
    # dsn == operator_flow_dsn
    # report is operator_flow_report
    # table_name == operator_flow_table
    # Assert first stdout line remains exactly unchanged.
    # Assert no DSN/table secret appears in stdout/stderr.
```

Run:

```bash
.venv/bin/python -m pytest tests/test_cli_paper_research_packet_operator_flow.py::test_operator_flow_cli_persists_operator_flow_report_when_env_enabled_without_changing_stdout -q
```

Expected: FAIL because `main(...)` has no `paper_research_packet_operator_flow_db_sink` injection and the CLI does not load/persist the operator-flow DB config.

- [ ] **Step 2: Add default-disabled and preflight RED tests**

Add:

```python
def test_operator_flow_cli_skips_operator_flow_sink_when_env_disabled(...):
    # Leave operator-flow DB env absent or disabled.
    # Pass a forbidden paper_research_packet_operator_flow_db_sink.
    # Assert command succeeds, stdout is unchanged, and sink is not called.

def test_operator_flow_cli_requires_operator_flow_dsn_before_upstream_persistence_when_enabled(...):
    # Set valid source/packet/quality DB envs.
    # Set operator-flow enabled=true with no DSN.
    # Pass forbidden loader/builder/sinks/runners.
    # Assert exit code 1, no helper calls, stderr includes the operator-flow DSN env var,
    # and no DSN secret value is printed.
```

Run:

```bash
.venv/bin/python -m pytest tests/test_cli_paper_research_packet_operator_flow.py::test_operator_flow_cli_skips_operator_flow_sink_when_env_disabled tests/test_cli_paper_research_packet_operator_flow.py::test_operator_flow_cli_requires_operator_flow_dsn_before_upstream_persistence_when_enabled -q
```

Expected: FAIL until CLI config loading and injection are implemented.

- [ ] **Step 3: Implement minimal CLI persistence path**

Modify `src/polymarket_alpha_lab/cli.py`:

```python
from polymarket_alpha_lab.supabase_paper_research_packet_operator_flow_config import (
    from_paper_research_packet_operator_flow_db_env,
)
```

Add the CLI-only callable alias near adjacent aliases:

```python
PaperResearchPacketOperatorFlowDbSink = Callable[..., object]
```

Add nullable `main(...)` injection near packet/quality injections:

```python
paper_research_packet_operator_flow_db_sink: (
    PaperResearchPacketOperatorFlowDbSink | None
) = None,
```

Inside the `paper-research-packet-operator-flow` branch:

```python
operator_flow_db_config = from_paper_research_packet_operator_flow_db_env()
operator_flow_dsn = operator_flow_db_config.dsn
if operator_flow_db_config.enabled and operator_flow_dsn is None:
    raise ValueError(
        "POLYMARKET_ALPHA_LAB_PAPER_RESEARCH_PACKET_OPERATOR_FLOW_DB_DSN "
        "must be set when DB is enabled",
    )
```

After `operator_flow_report = build_paper_research_packet_operator_flow_report(...)` and before printing:

```python
if operator_flow_db_config.enabled:
    if paper_research_packet_operator_flow_db_sink is None:
        from polymarket_alpha_lab.paper_research_packet_operator_flow_psycopg import (
            insert_paper_research_packet_operator_flow_report_with_psycopg,
        )

        operator_flow_sink = (
            insert_paper_research_packet_operator_flow_report_with_psycopg
        )
    else:
        operator_flow_sink = paper_research_packet_operator_flow_db_sink
    operator_flow_sink(
        dsn=operator_flow_dsn,
        report=operator_flow_report,
        table_name=operator_flow_db_config.table_name,
    )
```

Wrap the branch with existing error handling, passing operator-flow DSN/table into the redactor.

- [ ] **Step 4: Extend redaction coverage**

Add:

```python
def test_operator_flow_cli_redacts_operator_flow_sink_failure_across_all_databases(...):
    # Set all four DB env groups.
    # Let packet and quality persistence succeed.
    # Make operator-flow sink raise a message containing all DSNs,
    # all schema-qualified table names and tails, payload_json=..., question=...,
    # report_sha256=64 hex chars, and another bare 64-char hash.
    # Assert stderr contains redacted placeholders and none of the original secrets.
    # Assert no stdout success summary is printed.
```

Modify `_redacted_paper_research_packet_operator_flow_error(...)` to accept:

```python
operator_flow_dsn: str | None
operator_flow_table_name: str | None
```

and redact all four DSNs/tables.

Run:

```bash
.venv/bin/python -m pytest tests/test_cli_paper_research_packet_operator_flow.py::test_operator_flow_cli_redacts_operator_flow_sink_failure_across_all_databases -q
```

Expected: PASS after the redaction update.

- [ ] **Step 5: Lock parser/scope invariants**

In `tests/test_cli_paper_research_packet_operator_flow_scope.py`, add these entries to `FORBIDDEN_PARSER_ARGUMENT_SURFACE`:

```python
"--paper-research-packet-operator-flow-db-dsn",
"paper_research_packet_operator_flow_db_dsn",
"--paper-research-packet-operator-flow-db-table",
"paper_research_packet_operator_flow_db_table",
"--paper-research-packet-operator-flow-db-enabled",
"paper_research_packet_operator_flow_db_enabled",
```

Add at least these runtime forbidden flags:

```python
"--paper-research-packet-operator-flow-db-dsn",
"--paper-research-packet-operator-flow-db-table",
```

Run:

```bash
.venv/bin/python -m pytest tests/test_cli_paper_research_packet_operator_flow.py tests/test_cli_paper_research_packet_operator_flow_scope.py -q
```

Expected: all operator-flow CLI tests pass.

- [ ] **Step 6: Verify Task 1**

Run:

```bash
.venv/bin/python -m pytest tests/test_cli_paper_research_packet_operator_flow.py tests/test_cli_paper_research_packet_operator_flow_scope.py -q
.venv/bin/python -m pytest tests/test_cli_paper_research_packet.py tests/test_cli_paper_research_packet_quality.py tests/test_cli_paper_research_packet_quality_db_history.py -q
.venv/bin/python -m pytest tests/test_paper_research_packet_operator_flow*.py tests/test_supabase_paper_research_packet_operator_flow_config.py -q
.venv/bin/python -m compileall -q src tests
git diff --check -- src/polymarket_alpha_lab/cli.py tests/test_cli_paper_research_packet_operator_flow.py tests/test_cli_paper_research_packet_operator_flow_scope.py
```

Expected: all selected tests pass, compileall exits 0, and diff check is clean.

---

### Task 2: Operator-Flow Persistence Docs And Env Example

**Files:**
- Modify: `README.md`
- Modify: `.env.example`
- Modify: `tests/test_supabase_cycle_snapshot_config.py`

**Interfaces:**
- Consumes:
  - `POLYMARKET_ALPHA_LAB_PAPER_RESEARCH_PACKET_DB_ENABLED`
  - `POLYMARKET_ALPHA_LAB_PAPER_RESEARCH_PACKET_DB_DSN`
  - `POLYMARKET_ALPHA_LAB_PAPER_RESEARCH_PACKET_DB_TABLE`
  - `POLYMARKET_ALPHA_LAB_PAPER_RESEARCH_PACKET_QUALITY_DB_ENABLED`
  - `POLYMARKET_ALPHA_LAB_PAPER_RESEARCH_PACKET_QUALITY_DB_DSN`
  - `POLYMARKET_ALPHA_LAB_PAPER_RESEARCH_PACKET_QUALITY_DB_TABLE`
  - `POLYMARKET_ALPHA_LAB_PAPER_RESEARCH_PACKET_OPERATOR_FLOW_DB_ENABLED`
  - `POLYMARKET_ALPHA_LAB_PAPER_RESEARCH_PACKET_OPERATOR_FLOW_DB_DSN`
  - `POLYMARKET_ALPHA_LAB_PAPER_RESEARCH_PACKET_OPERATOR_FLOW_DB_TABLE`
- Produces:
  - operator-facing documentation that persistence is env-only, default disabled, and stdout unchanged.

- [ ] **Step 1: Inspect current docs locations**

Run:

```bash
rg -n "paper-research-packet-operator-flow|PAPER_RESEARCH_PACKET" README.md .env.example
```

Expected: README has the command section; `.env.example` lacks the complete packet/quality/operator-flow group.

- [ ] **Step 2: Update README**

In the `paper-research-packet-operator-flow` section, add a short paragraph:

```markdown
Operator-flow report persistence is optional and env-driven. Set
`POLYMARKET_ALPHA_LAB_PAPER_RESEARCH_PACKET_OPERATOR_FLOW_DB_ENABLED=true`
and `POLYMARKET_ALPHA_LAB_PAPER_RESEARCH_PACKET_OPERATOR_FLOW_DB_DSN` to persist
the final operator-flow report after packet, quality, and quality-history steps
complete. `POLYMARKET_ALPHA_LAB_PAPER_RESEARCH_PACKET_OPERATOR_FLOW_DB_TABLE`
can override the default table. There are still no DSN/table CLI flags, and the
command's summary stdout line is unchanged.
```

- [ ] **Step 3: Update `.env.example`**

Add this group, preserving existing style:

```dotenv
POLYMARKET_ALPHA_LAB_PAPER_RESEARCH_PACKET_DB_ENABLED=
POLYMARKET_ALPHA_LAB_PAPER_RESEARCH_PACKET_DB_DSN=
POLYMARKET_ALPHA_LAB_PAPER_RESEARCH_PACKET_DB_TABLE=
POLYMARKET_ALPHA_LAB_PAPER_RESEARCH_PACKET_QUALITY_DB_ENABLED=
POLYMARKET_ALPHA_LAB_PAPER_RESEARCH_PACKET_QUALITY_DB_DSN=
POLYMARKET_ALPHA_LAB_PAPER_RESEARCH_PACKET_QUALITY_DB_TABLE=
POLYMARKET_ALPHA_LAB_PAPER_RESEARCH_PACKET_OPERATOR_FLOW_DB_ENABLED=
POLYMARKET_ALPHA_LAB_PAPER_RESEARCH_PACKET_OPERATOR_FLOW_DB_DSN=
POLYMARKET_ALPHA_LAB_PAPER_RESEARCH_PACKET_OPERATOR_FLOW_DB_TABLE=
```

- [ ] **Step 4: Verify Task 2**

Run:

```bash
rg -n "PAPER_RESEARCH_PACKET_OPERATOR_FLOW_DB|no DSN/table CLI flags|summary stdout line is unchanged" README.md .env.example
.venv/bin/python -m pytest tests/test_supabase_cycle_snapshot_config.py::test_env_example_documents_supported_db_variable_names_only -q
git diff --check -- README.md .env.example
```

Expected: the new documentation/env names are present, the `.env.example` whitelist test passes, and whitespace is clean.

---

### Task 3: Integrated Verification, Review, And Push

**Files:**
- Modify only Task 1-2 files if findings require fixes.

**Interfaces:**
- Consumes: completed CLI persistence and docs diff.
- Produces: reviewed, tested, pushed commit.

- [ ] **Step 1: Run focused verification**

Run:

```bash
.venv/bin/python -m pytest tests/test_cli_paper_research_packet_operator_flow.py tests/test_cli_paper_research_packet_operator_flow_scope.py -q
.venv/bin/python -m pytest tests/test_cli_paper_research_packet.py tests/test_cli_paper_research_packet_quality.py tests/test_cli_paper_research_packet_quality_db_history.py -q
.venv/bin/python -m pytest tests/test_paper_research_packet_operator_flow*.py tests/test_supabase_paper_research_packet_operator_flow_config.py -q
```

Expected: all pass.

- [ ] **Step 2: Run full gate**

Run:

```bash
.venv/bin/python -m compileall -q src tests
.venv/bin/python -m pytest -q
git diff --check
codegraph sync
```

Expected: compileall exits 0, full pytest passes, diff check clean, CodeGraph sync completes.

- [ ] **Step 3: OpenCode review**

Generate a review package from the staged diff and run:

```bash
opencode run "Read-only review..." -f <review-package> --dir /home/ubuntu/polymarket-alpha-lab -m zhipuai-coding-plan/glm-5.2 --variant max
```

Expected: no Critical or Important findings.

- [ ] **Step 4: Commit, push, and ledger**

Run:

```bash
git add README.md .env.example src/polymarket_alpha_lab/cli.py tests/test_cli_paper_research_packet_operator_flow.py tests/test_cli_paper_research_packet_operator_flow_scope.py docs/superpowers/plans/2026-06-23-paper-research-packet-operator-flow-cli-persistence.md
git add tests/test_supabase_cycle_snapshot_config.py
git commit -m "feat: persist operator-flow reports from CLI"
git push origin main
```

Append one local ledger line:

```text
Paper research packet operator flow CLI persistence: complete (commit <sha7>, OpenCode review clean, full pytest <N> passed 1 skipped, pushed origin/main).
```

Expected: `origin/main` points to the new commit and the worktree is clean except ignored `.superpowers/sdd/progress.md`.
