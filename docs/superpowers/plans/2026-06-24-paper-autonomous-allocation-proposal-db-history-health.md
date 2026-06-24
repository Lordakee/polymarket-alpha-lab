# Paper Autonomous Allocation Proposal DB History Health Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. The reducer, loader, CLI/docs, and scope-test lanes are intentionally separable so multiple workers can develop in parallel without editing the same files.

**Goal:** Add a paper-only/report-only/read-only health and trend node over persisted paper autonomous allocation proposal DB history. The node should summarize recent allocation proposal history stability for operators and later autonomous cycle throttling, without producing investment rankings, approval workflow decisions, or any live execution signal.

**Architecture:** Build a pure reducer over a sequence of existing `PaperAutonomousAllocationProposalDbHistoryReport` values. A tiny loader loads final allocation proposal reports once, builds deterministic prefix-window DB-history reports in memory, and passes those source history reports into the health reducer. A new env-only CLI command prints aggregate health and trend fields. The node is read-only and consumes final allocation proposal history only; it must not read upstream screening/queue tables, write reports, mutate exchange state, or create orders.

**Tech Stack:** Python 3.12, argparse CLI, frozen dataclasses, `Decimal` for notional fields, existing allocation proposal DB-history reducer/load modules, psycopg read-only autocommit connection in CLI boundary only, pytest, CodeGraph, and local OpenCode reviews using `zhipuai-coding-plan/glm-5.2` with variant `max`.

## Global Constraints

- Preserve Phase 1 boundary: no live trading, no automatic live investing, no auth, no key handling, no wallet handling, no account handling, no account reads, no order instruction, no order construction, no order signing, no order submission, no order cancellation, no order replacement, no execution authorization, no approval workflow, no live-execution signal, no exchange mutation, no investment ranking, and no financial advice.
- The planned command is `paper-autonomous-allocation-proposal-db-history-health --limit 25`.
- The command accepts only `--limit`; it must reject `--dsn`, `--table`, `--persist`, `--fast`, `--live`, `--auth`, `--wallet`, `--private-key`, `--api-key`, `--account`, `--order`, `--trade`, `--execute`, `--submit`, and `--approve`.
- All DB targets come from `POLYMARKET_ALPHA_LAB_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_*` env config.
- The node reads only persisted final allocation proposal reports through existing allocation proposal DB-history readback. It must not read upstream screening/queue tables, repair missing reports, create reports, or write any reports.
- The reducer must be pure: no `psycopg`, Supabase clients, `os.environ`, CLI imports, network clients, filesystem writes, or printing.
- The loader must not connect, close, commit, rollback, insert, update, delete, create tables, create indexes, or mutate supplied connections.
- The CLI default DB path may connect with `psycopg.connect(dsn, autocommit=True)`, call the loader once, close once, and never commit or rollback.
- Validate `--limit` before env reads, runner calls, DB connects, or client construction.
- Require allocation proposal DB enabled and DSN present before runner or DB connect.
- Operator output must be aggregate-only: no DSN, table name, schema tail, payload JSON, report hash, market question, market slug, account, wallet, key, or order material.
- Keep Decimal-only posture; do not introduce float arithmetic for notional or ratio fields.
- Use `.venv/bin/python -m pytest`, not bare `pytest`.
- Do not use fast mode.
- Completed implementation must pass focused tests, full tests, `compileall`, `git diff --check`, secret scan over tracked source/docs/tests, CodeGraph sync/status, and OpenCode post-node review before commit/push.

## File Structure

- Create `src/polymarket_alpha_lab/paper_autonomous_allocation_proposal_db_history_health.py`: pure health/trend reducer.
- Create `src/polymarket_alpha_lab/paper_autonomous_allocation_proposal_db_history_health_load.py`: read-only loader composition.
- Modify `src/polymarket_alpha_lab/cli.py`: add runner alias, subparser, command branch, helper, summary printer, and redacted error path.
- Modify `src/polymarket_alpha_lab/__init__.py`: export public health reducer types and builder only.
- Modify `README.md` and `docs/paper-autonomous-allocation-proposal.md`: document the read-only health command and negative boundary language.
- Add tests:
  - `tests/test_paper_autonomous_allocation_proposal_db_history_health.py`
  - `tests/test_paper_autonomous_allocation_proposal_db_history_health_load.py`
  - `tests/test_cli_paper_autonomous_allocation_proposal_db_history_health.py`
  - `tests/test_cli_paper_autonomous_allocation_proposal_db_history_health_scope.py`
  - `tests/test_paper_autonomous_allocation_proposal_db_history_health_scope.py`
  - Modify docs/export scope tests that own allocation proposal public API allowlists.

## Parallel Development Lanes

- **Lane A, pure reducer:** Own only `paper_autonomous_allocation_proposal_db_history_health.py`, its reducer tests, and the reducer scope test.
- **Lane B, loader:** Own only `paper_autonomous_allocation_proposal_db_history_health_load.py` and loader tests. Use a stubbed existing DB-history loader where needed to avoid real DB access.
- **Lane C, CLI:** Own only `cli.py` plus CLI and CLI scope tests. Depend on agreed reducer/loader symbol names but do not edit reducer internals.
- **Lane D, docs/exports:** Own `__init__.py`, README/docs, `tests/test_init.py`, and existing scope allowlists.
- **Lane E, verification/review:** Own test execution, CodeGraph sync/status, secret scan, OpenCode review collection, and final staging audit. This lane must not edit source unless review finds a concrete issue.

Avoid overlapping file edits across lanes. If a lane needs a shared interface change, pause and update this plan before implementation.

Before dispatching Lanes B and C, freeze this shared loader interface exactly:

```python
load_paper_autonomous_allocation_proposal_db_history_health_report(
    connection,
    *,
    limit: int | None,
    table_name: str,
    history_config: PaperAutonomousAllocationProposalDbHistoryConfig,
    health_config: PaperAutonomousAllocationProposalDbHistoryHealthConfig,
    generated_at: datetime,
)
```

Any change to this function name or keyword signature requires a plan update before parallel work continues.

---

### Task 1: Pure DB-History Health Reducer

**Files:**
- Create: `src/polymarket_alpha_lab/paper_autonomous_allocation_proposal_db_history_health.py`
- Test: `tests/test_paper_autonomous_allocation_proposal_db_history_health.py`
- Test: `tests/test_paper_autonomous_allocation_proposal_db_history_health_scope.py`

**Interfaces:**
- Consumes a sequence of exact `PaperAutonomousAllocationProposalDbHistoryReport` values.
- Produces:
  - `DEFAULT_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_HEALTH_CONFIG_VERSION = "paper-autonomous-allocation-proposal-db-history-health-v0"`
  - `PaperAutonomousAllocationProposalDbHistoryHealthConfig`
  - `PaperAutonomousAllocationProposalDbHistoryHealthReasonCodeCount`
  - `PaperAutonomousAllocationProposalDbHistoryHealthReport`
  - `build_paper_autonomous_allocation_proposal_db_history_health_report(history_reports, *, config, generated_at)`

- [ ] **Step 1: Write failing reducer tests**

Cover:
- Empty input blocks with `insufficient_allocation_proposal_db_history_health_samples`.
- Fewer than `min_history_report_count` blocks.
- All recent pass history yields `health_status == "pass"` and `recommended_next_step == "allow_allocation_proposal_history_health_review"`.
- Any latest blocked source history blocks.
- Excess recent watch share yields `health_status == "watch"` and `recommended_next_step == "throttle_allocation_proposal_history_health_review"`.
- Excess recent blocked share yields `health_status == "blocked"` and `recommended_next_step == "block_allocation_proposal_history_health_review"`.
- Stale latest source history yields watch.
- Source history with `latest_report_generated_at is None` yields `health_status == "blocked"` with reason `missing_latest_allocation_proposal_db_history_timestamp`.
- Duplicate source `latest_report_generated_at` values yield watch.
- Latest allocated count and latest total allocated paper notional are copied from the newest source report as `int | None` and `Decimal | None`.
- Trend fields are deterministic and Decimal-only:
  - `pass_report_count`
  - `watch_report_count`
  - `blocked_report_count`
  - `latest_history_status`
  - `latest_proposal_status`
  - `latest_allocated_count`
  - `latest_total_allocated_paper_notional`
  - `max_source_age_seconds`
  - `latest_source_age_seconds`
  - `duplicate_latest_report_generated_at_count`
  - `reason_code_counts`
  - `reason_codes`
- Dataclasses are frozen and hard-enforce `paper_only is True`, `report_only is True`, and `readonly is True`.
- Exact-type validation rejects source report subclasses, config subclasses, datetime subclasses, naive datetimes, bool-as-int thresholds, floats, and corrupted direct constructor values.

- [ ] **Step 2: Implement the reducer**

Status precedence:

```python
if blocked_reasons:
    health_status = "blocked"
elif watch_reasons:
    health_status = "watch"
else:
    health_status = "pass"
```

Required blocked reasons:
- `insufficient_allocation_proposal_db_history_health_samples`
- `latest_allocation_proposal_db_history_blocked`
- `blocked_allocation_proposal_db_history_share_threshold_exceeded`
- `missing_latest_allocation_proposal_db_history_timestamp`

Required watch reasons:
- `latest_allocation_proposal_db_history_watch`
- `watch_allocation_proposal_db_history_share_threshold_exceeded`
- `stale_allocation_proposal_db_history`
- `duplicate_allocation_proposal_history_timestamp_threshold_exceeded`

Required pass reason:
- `paper_autonomous_allocation_proposal_db_history_health_passed`

Default config:

```python
min_history_report_count = 3
max_watch_history_report_count = 0
max_blocked_history_report_count = 0
max_duplicate_latest_report_generated_at_count = 0
max_latest_age_seconds = 86400
```

Reason-code counts should count source report presence, not occurrences within a single source report, and should sort by `report_count` descending then `reason_code` ascending.

Timestamp age handling:
- If any source history report has `latest_report_generated_at is None`, emit `missing_latest_allocation_proposal_db_history_timestamp`, set `health_status == "blocked"`, and set `latest_source_age_seconds` and `max_source_age_seconds` to `None`.
- Otherwise compute age fields from the reducer `generated_at` against each source history report's `latest_report_generated_at`.

- [ ] **Step 3: Add reducer scope tests**

AST/string checks must prove the reducer has no DB/env/network/execution surfaces and no guarded tokens:
- `psycopg`
- `supabase`
- `os.environ`
- `requests`
- `httpx`
- `urllib`
- `private_key`
- `wallet`
- `account`
- `submit_order`
- `cancel_order`
- `replace_order`
- `execute`
- `approve`
- `trade`
- `open(`
- `print(`

Run:

```bash
.venv/bin/python -m pytest \
  tests/test_paper_autonomous_allocation_proposal_db_history_health.py \
  tests/test_paper_autonomous_allocation_proposal_db_history_health_scope.py -q
```

---

### Task 2: Read-Only Loader Composition

**Files:**
- Create: `src/polymarket_alpha_lab/paper_autonomous_allocation_proposal_db_history_health_load.py`
- Test: `tests/test_paper_autonomous_allocation_proposal_db_history_health_load.py`

**Interfaces:**
- Produces `load_paper_autonomous_allocation_proposal_db_history_health_report(connection, *, limit, table_name, history_config, health_config, generated_at)`.
- Loads final allocation proposal reports once via `load_paper_autonomous_allocation_proposal_reports(connection, limit=limit, table_name=table_name)`, reverses the DB-descending output into chronological order if needed, builds prefix-window `PaperAutonomousAllocationProposalDbHistoryReport` values with `build_paper_autonomous_allocation_proposal_db_history_report(proposal_reports[:i + 1], config=history_config, generated_at=proposal_reports[i].generated_at)`, then builds the health report from that exact sequence of source history reports.

- [ ] **Step 1: Write failing loader tests**

Cover:
- Delegates `connection`, `limit`, and `table_name` to the existing final proposal report store loader exactly once.
- Builds prefix-window DB-history source reports with the supplied `history_config` and each window's latest proposal `generated_at`.
- Builds a health report from the exact prefix-window source history values and `health_config`.
- Rejects non-exact `history_config` and `health_config` before reading.
- Does not call `commit`, `rollback`, `close`, `cursor`, `execute`, `insert`, `update`, or `delete` on supplied connection directly.
- Does not import env config, CLI, psycopg, Supabase clients, or network modules.

- [ ] **Step 2: Implement loader**

Keep it small and boundary-free. The windowing contract is fixed to prefix windows over chronological final proposal reports:

```python
window_i = proposal_reports[: i + 1]
source_history_i = build_paper_autonomous_allocation_proposal_db_history_report(
    window_i,
    config=history_config,
    generated_at=proposal_reports[i].generated_at,
)
```

This is one SELECT plus pure in-memory reducer calls. Do not add a writer, migration, new DB table, or second DB round-trip per window.

Run:

```bash
.venv/bin/python -m pytest tests/test_paper_autonomous_allocation_proposal_db_history_health_load.py -q
```

---

### Task 3: CLI Health Command

**Files:**
- Modify: `src/polymarket_alpha_lab/cli.py`
- Test: `tests/test_cli_paper_autonomous_allocation_proposal_db_history_health.py`
- Test: `tests/test_cli_paper_autonomous_allocation_proposal_db_history_health_scope.py`

**Interfaces:**
- Adds command `paper-autonomous-allocation-proposal-db-history-health`.
- Adds injectable runner alias `PaperAutonomousAllocationProposalDbHistoryHealthRunner`.
- Adds helper `_run_paper_autonomous_allocation_proposal_db_history_health(...)`.
- Adds aggregate-only printer `_print_paper_autonomous_allocation_proposal_db_history_health_summary(...)`.

- [ ] **Step 1: Write CLI tests**

Cover:
- `--limit` validation happens before env reads, runner calls, DB connects, or psycopg imports.
- Command requires allocation proposal DB enabled and DSN.
- Injected runner receives `dsn`, `table_name`, `limit`, history config, health config, and UTC `generated_at`.
- Default path uses `psycopg.connect(dsn, autocommit=True)`, calls loader once, closes once, and never commits or rolls back.
- Missing psycopg returns a redacted postgres-extra error.
- Runner/loader failures redact DSN, full schema-qualified table name, schema prefix, table tail, payload JSON, market question, and hash-like material.
- Parser accepts only `--limit` and rejects guarded flags.
- Output contains only aggregate health/trend fields and reason-code counts.

- [ ] **Step 2: Implement CLI wiring**

Use the allocation proposal DB env config and existing redaction helper. Do not add DSN/table CLI flags and do not add persistence.

Run:

```bash
.venv/bin/python -m pytest \
  tests/test_cli_paper_autonomous_allocation_proposal_db_history_health.py \
  tests/test_cli_paper_autonomous_allocation_proposal_db_history_health_scope.py -q
```

---

### Task 4: Public Exports and Docs

**Files:**
- Modify: `src/polymarket_alpha_lab/__init__.py`
- Modify: `tests/test_init.py`
- Modify: existing scope allowlists that track allocation proposal public exports.
- Modify: `README.md`
- Modify: `docs/paper-autonomous-allocation-proposal.md`
- Modify: `tests/test_docs_paper_autonomous_allocation_proposal_scope.py`

- [ ] **Step 1: Export only stable public reducer symbols**

Export:
- `PaperAutonomousAllocationProposalDbHistoryHealthConfig`
- `PaperAutonomousAllocationProposalDbHistoryHealthReasonCodeCount`
- `PaperAutonomousAllocationProposalDbHistoryHealthReport`
- `build_paper_autonomous_allocation_proposal_db_history_health_report`

Do not export the default config-version constant from package root.

- [ ] **Step 2: Document boundary**

Docs must explicitly state:
- env-only
- read-only
- paper-only/report-only/readonly
- accepts only `--limit`
- reads only persisted final allocation proposal history through DB history readback
- does not read upstream screening/queue tables
- does not write reports
- does not place orders, approve execution, read accounts, or mutate exchange state
- health status is not permission to trade
- not financial advice
- not investment ranking
- not an approval workflow

---

### Task 5: Verification, Review, Commit, Push

- [ ] Run focused integrated tests:

```bash
.venv/bin/python -m pytest \
  tests/test_paper_autonomous_allocation_proposal_db_history_health.py \
  tests/test_paper_autonomous_allocation_proposal_db_history_health_scope.py \
  tests/test_paper_autonomous_allocation_proposal_db_history_health_load.py \
  tests/test_cli_paper_autonomous_allocation_proposal_db_history_health.py \
  tests/test_cli_paper_autonomous_allocation_proposal_db_history_health_scope.py \
  tests/test_docs_paper_autonomous_allocation_proposal_scope.py \
  tests/test_init.py -q
```

- [ ] Run full verification:

```bash
.venv/bin/python -m pytest -q
.venv/bin/python -m compileall -q src tests
git diff --check
rg -n "ghp_[A-Za-z0-9_]{20,}|sk-[A-Za-z0-9]{20,}|xox[baprs]-[A-Za-z0-9-]{20,}|AKIA[0-9A-Z]{16}|-----BEGIN (RSA |OPENSSH |EC |DSA )?PRIVATE KEY-----" README.md docs src tests
codegraph sync
codegraph status .
```

- [ ] Run OpenCode post-node review:

```bash
opencode run -m zhipuai-coding-plan/glm-5.2 --variant max \
  "Read-only review only. DO NOT modify/create/delete ANY file; output ONLY verdict + findings. Review the current git diff for the paper-autonomous-allocation-proposal-db-history-health node. Check Phase 1 boundaries, read-only DB behavior, CLI redaction, no live/auth/order/account surfaces, package exports and scope tests, docs boundary wording, trend metric semantics, Decimal-only behavior, and test adequacy. Report Critical/Important/Minor findings with file/line references. If no Critical/Important findings, say so clearly."
```

Fix all Critical and Important findings before commit.

- [ ] Update `.superpowers/sdd/progress.md` with the completed node summary if that file exists; otherwise note the skipped progress update in the handoff.
- [ ] Stage only intended tracked implementation/docs/tests/plan files. Do not stage `.superpowers/reviews/`.
- [ ] Commit with:

```bash
git commit -m "feat: add allocation proposal DB history health"
```

- [ ] Push only when the active implementation agent is Codex and the user has explicitly authorized node pushes in this session. If an OMO/OpenCode/Sisyphus process executes this plan without explicit user push authorization, stop at the local commit.

```bash
git push origin main
```
