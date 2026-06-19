# Cycle Snapshot DB Trend Default Load Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add no-network coverage proving `polymarket-alpha-lab cycle-snapshot-db-trend` uses the default psycopg load wrapper and store path when no trend runner is injected.

**Architecture:** This is a coverage-hardening node. The test installs a fake `psycopg` module, fake DB-API connection/cursor, and real cycle snapshot DB rows so the CLI exercises the existing env config, default psycopg wrapper, store loader, row codec, and trend builder without any real network or database.

**Tech Stack:** Python, pytest, fake `sys.modules["psycopg"]`, existing `main(...)`, real `load_paper_recommendation_cycle_snapshots_with_psycopg`, real store/row codec, real trend builder.

---

### Task 1: CLI Default Psycopg Load Coverage

**Files:**
- Modify: `tests/test_cli.py`

- [x] **Step 1: Add the CLI default-load test**

Added `test_cycle_snapshot_db_trend_cli_default_psycopg_load_path_no_network` near the existing `cycle-snapshot-db-trend` CLI tests. The test:

- Enables cycle snapshot DB config through env vars.
- Does not pass `cycle_snapshot_db_trend_runner`, so the CLI must use its default load path.
- Installs fake `psycopg` and `psycopg.types.json.Jsonb` modules.
- Returns fake DB-API rows generated from real `PaperRecommendationCycleSnapshotReport` values through the production DB row codec.
- Asserts SQL uses the configured table, source config filter, limit, and deterministic descending order.
- Asserts stdout summarizes the loaded trend and does not leak the fake DSN.

- [x] **Step 2: Run focused verification**

Run:

```bash
.venv/bin/python -m pytest tests/test_cli.py::test_cycle_snapshot_db_trend_cli_default_psycopg_load_path_no_network -q
```

Result: passed against the existing production wiring.

- [ ] **Step 3: Run adjacent gates**

Run:

```bash
.venv/bin/python -m pytest tests/test_cli.py tests/test_paper_recommendation_cycle_snapshot_psycopg.py tests/test_paper_recommendation_cycle_snapshot_store.py tests/test_paper_recommendation_cycle_snapshot_db_row.py -q
git diff --check
```

Expected: all selected tests pass and diff check is clean.

- [ ] **Step 4: Review, commit, and push when authorized**

Run OpenCode review:

```bash
opencode run -m zhipuai-coding-plan/glm-5.2 --variant max --dir /home/ubuntu/polymarket-alpha-lab -- "<read-only review prompt>"
```

If review has no critical or important issues, commit locally. Push only when the current user/project instructions explicitly authorize pushing completed nodes; this session has that authorization.

```bash
git add tests/test_cli.py docs/superpowers/plans/2026-06-19-cycle-snapshot-db-trend-default-load-node.md
git commit -m "Add cycle snapshot DB trend default load coverage"
git push origin main
```

---

## Outcome

- The new test passed against existing production code on its first run, so no `src/` production files were changed.
- The test covers the previously missing no-network CLI path:
  `main(["cycle-snapshot-db-trend", ...]) -> _run_cycle_snapshot_db_trend -> load_paper_recommendation_cycle_snapshots_with_psycopg -> store loader -> row codec -> trend builder`.
- The test remains Phase 1 safe: it uses fake DB modules only, constructs no client, submits no orders, reads no wallet/account state, and asserts the fake DSN is not printed.
