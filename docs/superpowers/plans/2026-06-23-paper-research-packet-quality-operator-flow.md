# Paper Research Packet Quality Operator Flow Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Wire paper research packet quality reports into the operator workflow by adding optional CLI persistence and a persisted quality history CLI.

**Architecture:** Keep Phase 1 read/report boundaries intact: source packet quality reads the latest persisted packet report, optional quality persistence writes only the derived quality report, and history reads persisted quality reports through the existing pure reducer. CLI code owns operator orchestration; store/load modules remain DB-API boundaries; pure reducers remain free of DB, env, CLI, client, or network imports.

**Tech Stack:** Python 3, argparse CLI, frozen dataclasses, Decimal-only domain math, DB-API/psycopg adapters, Supabase/Postgres migrations already present, pytest.

## Global Constraints

- Phase 1 only: paper-only, report-only, readonly where applicable.
- No live trading, auth, wallet, private keys, signing, orders, relayer, exchange, or network mutation.
- Do not add DSN or table CLI flags; use environment configs only.
- `paper-research-packet-quality` keeps reading exactly one latest source packet report and still has no `--limit`.
- `paper-research-packet-quality --persist` may persist the derived quality report only when quality DB env config is enabled.
- `paper-research-packet-quality-db-history` is read-only and may expose `--limit`, defaulting to `100`.
- Redact source packet DB DSN/table and quality DB DSN/table, plus payload/question/hash fragments, in user-facing CLI errors.
- Use `.venv/bin/python -m pytest`, not bare `pytest`.
- Reviews go to local OpenCode with model `zhipuai-coding-plan/glm-5.2` and variant/thinking `max`.

---

### Task 1: Add Optional Quality CLI Persistence

**Files:**
- Modify: `src/polymarket_alpha_lab/cli.py`
- Modify: `tests/test_cli_paper_research_packet_quality.py`
- Modify: `tests/test_cli_paper_research_packet_quality_scope.py`

**Interfaces:**
- Consumes: `from_paper_research_packet_db_env()`, `from_paper_research_packet_quality_db_env()`, `_run_paper_research_packet_quality(...)`, and `insert_paper_research_packet_quality_report(...)`.
- Produces: `paper-research-packet-quality --persist`, printing the existing summary plus a persistence marker without exposing DSN/table values.

- [ ] **Step 1: Write failing tests**

Add tests proving `--persist` is accepted, uses quality DB env config, opens the quality DB connection, inserts the already-built quality report, commits exactly once on success, closes exactly once, redacts quality DB secrets on failure, and does not add `--limit`.

Run:

```bash
.venv/bin/python -m pytest tests/test_cli_paper_research_packet_quality.py tests/test_cli_paper_research_packet_quality_scope.py -q
```

Expected: the new persistence tests fail because `--persist` is currently rejected.

- [ ] **Step 2: Implement minimal CLI support**

In `src/polymarket_alpha_lab/cli.py`, add `--persist` to the `paper-research-packet-quality` parser. After `_run_paper_research_packet_quality(...)` succeeds, if `args.persist` is true, load `from_paper_research_packet_quality_db_env()`, require enabled config and DSN, connect with `psycopg.connect(dsn)`, call `insert_paper_research_packet_quality_report(connection, report, table_name=quality_config.table_name)`, commit on success, rollback on failure, and close in `finally`.

- [ ] **Step 3: Verify green**

Run:

```bash
.venv/bin/python -m pytest tests/test_cli_paper_research_packet_quality.py tests/test_cli_paper_research_packet_quality_scope.py -q
```

Expected: all selected tests pass.

### Task 2: Add Quality DB History CLI

**Files:**
- Modify: `src/polymarket_alpha_lab/cli.py`
- Create: `tests/test_cli_paper_research_packet_quality_db_history.py`
- Create: `tests/test_cli_paper_research_packet_quality_db_history_scope.py`

**Interfaces:**
- Consumes: `from_paper_research_packet_quality_db_env()`, `PaperResearchPacketQualityHistoryConfig`, and `load_paper_research_packet_quality_history_report(...)`.
- Produces: `paper-research-packet-quality-db-history --limit 100`, printing history status, source report count, first/latest source timestamps, latest quality status/source age/included/skipped share, status rows, duplicate timestamp count, recurring reason rows, and reason codes.

- [ ] **Step 1: Write failing CLI tests**

Add injected-runner and default DB path tests. The runner should receive `dsn`, `table_name`, `limit`, `config`, and `generated_at`; default DB path should connect with `autocommit=True`, call the DB history loader, close, and never commit or rollback.

Run:

```bash
.venv/bin/python -m pytest tests/test_cli_paper_research_packet_quality_db_history.py -q
```

Expected: fails because the command does not exist.

- [ ] **Step 2: Add command and helper**

In `src/polymarket_alpha_lab/cli.py`, add the parser, runner type, `main(...)` injection parameter, `_run_paper_research_packet_quality_db_history(...)`, and `_print_paper_research_packet_quality_db_history_summary(...)`. Validate `limit > 0` before connecting.

- [ ] **Step 3: Add scope tests**

Ensure the command rejects source generation, persistence, live, auth, wallet, order, exchange, relayer, and DSN/table CLI flags while accepting only `--limit`.

Run:

```bash
.venv/bin/python -m pytest tests/test_cli_paper_research_packet_quality_db_history.py tests/test_cli_paper_research_packet_quality_db_history_scope.py -q
```

Expected: all selected tests pass.

### Task 3: Update Operator Docs

**Files:**
- Modify: `README.md`
- Modify: `docs/superpowers/plans/2026-06-23-paper-research-packet-quality-operator-flow.md`

**Interfaces:**
- Consumes: final CLI behavior from Tasks 1 and 2.
- Produces: operator-facing docs for `paper-research-packet-quality --persist` and `paper-research-packet-quality-db-history --limit 100`.

- [ ] **Step 1: Update README**

Replace the old note saying no quality DB-history CLI exists. Document source packet DB env, optional quality DB env for `--persist`, and read-only quality history env.

- [ ] **Step 2: Verify docs do not imply live trading**

Run:

```bash
rg -n "live trading|private key|wallet|order|auth|exchange|relayer" README.md docs/superpowers/plans/2026-06-23-paper-research-packet-quality-operator-flow.md
```

Expected: matches only appear in explicit "No live..." boundary statements.

### Task 4: Review, Hardening, And Push

**Files:**
- Modify only if findings require it.

**Interfaces:**
- Consumes: complete diff from Tasks 1-3.
- Produces: reviewed, tested, pushed main branch.

- [ ] **Step 1: Run focused and full verification**

Run:

```bash
.venv/bin/python -m pytest tests/test_cli_paper_research_packet_quality.py tests/test_cli_paper_research_packet_quality_scope.py tests/test_cli_paper_research_packet_quality_db_history.py tests/test_cli_paper_research_packet_quality_db_history_scope.py tests/test_paper_research_packet_quality_history_load.py -q
.venv/bin/python -m compileall -q src tests
.venv/bin/python -m pytest -q
git diff --check
```

- [ ] **Step 2: OpenCode review**

Run an OpenCode review against the branch diff using model `zhipuai-coding-plan/glm-5.2` with variant `max`. Fix Critical and Important findings before proceeding.

- [ ] **Step 3: Sync CodeGraph, commit, push**

Run:

```bash
codegraph sync
git add src tests README.md docs/superpowers/plans/2026-06-23-paper-research-packet-quality-operator-flow.md
git commit -m "feat: wire packet quality operator flow"
git push origin main
```
