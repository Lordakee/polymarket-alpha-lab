# CLI Default Cycle Snapshot Source Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Wire `polymarket-alpha-lab run` so DB-enabled cycle snapshot persistence uses the pure default source when no test/source injection is supplied.

**Architecture:** Keep runner and DB adapters unchanged. The CLI imports `build_strategy_cycle_snapshot_source_report` and selects `cycle_snapshot_source or build_strategy_cycle_snapshot_source_report` only inside the `run` command when cycle snapshot DB config is enabled. Explicit test injection remains higher priority; DB-disabled runs still pass `None` source/sink into the loop runner.

**Tech Stack:** Python CLI module, pytest, existing Supabase env config, existing psycopg sink wrapper, OpenCode review.

---

### File Structure

- Modify: `src/polymarket_alpha_lab/cli.py`
  - Import the pure source function.
  - Replace the current enabled-DB-without-source error with default-source selection.
  - Keep DSN/table redaction and sink wrapping unchanged.
- Modify: `tests/test_cli.py`
  - Change the old rejection test into a default-source wiring test.
  - Keep the injected-source test to prove injection still wins.
- Create: `docs/superpowers/plans/2026-06-19-cli-default-cycle-snapshot-source-node.md`
  - Durable node plan.

### Task 1: RED Test

**Files:**
- Modify: `tests/test_cli.py`

- [ ] **Step 1: Import the pure source builder**

Add:

```python
from polymarket_alpha_lab.strategy_cycle_snapshot_source import (
    build_strategy_cycle_snapshot_source_report,
)
```

- [ ] **Step 2: Replace the rejection test**

Replace `test_run_cli_rejects_enabled_cycle_snapshot_db_without_source` with a test that:

- enables `POLYMARKET_ALPHA_LAB_CYCLE_SNAPSHOT_DB_ENABLED=true`;
- sets a fake DSN and table name;
- passes no `cycle_snapshot_source` injection to `main`;
- uses a fake loop runner that receives a non-`None` source and sink;
- asserts `kwargs["cycle_snapshot_source"] is build_strategy_cycle_snapshot_source_report`;
- calls the received source with a minimal real `PaperStrategyCycleReport`, not `object()`, because the default source structurally rejects non-cycle-report objects;
- calls the received sink with the returned snapshot;
- asserts the fake DB sink receives the real DSN value internally and the table name;
- asserts the real DSN value is absent from stdout and stderr;
- asserts the CLI returns `0` and prints `cycle_snapshots_persisted=1`.

- [ ] **Step 3: Run RED**

Run:

```bash
.venv/bin/python -m pytest tests/test_cli.py::test_run_cli_uses_default_cycle_snapshot_source_when_db_enabled_without_injection -q
```

Expected before implementation: FAIL because CLI still raises `cycle snapshot DB persistence requires a cycle snapshot source`.

### Task 2: CLI Wiring

**Files:**
- Modify: `src/polymarket_alpha_lab/cli.py`

- [ ] **Step 1: Import default source**

Add near cycle snapshot imports:

```python
from polymarket_alpha_lab.strategy_cycle_snapshot_source import (
    build_strategy_cycle_snapshot_source_report,
)
```

- [ ] **Step 2: Select default source when DB is enabled**

Change the `run` branch from:

```python
if cycle_snapshot_source is None:
    raise ValueError(...)
...
run_cycle_snapshot_source = cycle_snapshot_source
```

to:

```python
run_cycle_snapshot_source = (
    cycle_snapshot_source or build_strategy_cycle_snapshot_source_report
)
```

Keep the DSN `None` check and DB sink wrapper unchanged.

- [ ] **Step 3: Run focused GREEN**

Run:

```bash
.venv/bin/python -m pytest tests/test_cli.py::test_run_cli_uses_default_cycle_snapshot_source_when_db_enabled_without_injection tests/test_cli.py::test_run_cli_wires_cycle_snapshot_db_sink_when_env_enabled -q
```

Expected: PASS.

### Task 3: Verification, Review, Commit, Push

- [ ] **Step 1: Focused and adjacent tests**

Run:

```bash
.venv/bin/python -m pytest tests/test_cli.py tests/test_strategy_cycle_snapshot_source.py tests/test_runner.py -q
```

- [ ] **Step 2: Full gates**

Run:

```bash
.venv/bin/python -m pytest -q
.venv/bin/python -m compileall -q src tests
git diff --check
codegraph sync
codegraph status .
```

- [ ] **Step 3: Secret scan**

Run a narrow staged/diff scan over this node's changed files. Do not inspect Supabase `.env`.

- [ ] **Step 4: OpenCode post-stage review**

Use `opencode run -m zhipuai-coding-plan/glm-5.2 --variant max --dir /home/ubuntu/polymarket-alpha-lab -- "<read-only review prompt>"`.

Review prompt must require no file modifications and check:

- DB-disabled run remains inert;
- DB-enabled run defaults to the pure source when no source is injected;
- injected source still wins;
- DSN is never printed;
- no runner, DB schema, wallet/auth/order/live trading surfaces are changed.

- [ ] **Step 5: Commit and push**

Stage only:

```text
docs/superpowers/plans/2026-06-19-cli-default-cycle-snapshot-source-node.md
src/polymarket_alpha_lab/cli.py
tests/test_cli.py
```

Stage, commit, and push as Codex after OpenCode has completed its read-only review. OpenCode/Sisyphus must not stage, commit, or push for this node unless the user separately authorizes that tool to do so; this plan keeps the whole completion gate in Codex because the user explicitly asked Codex to push completed nodes.

```bash
git commit -m "Use default cycle snapshot source in CLI run"
git push origin main
```
