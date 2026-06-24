# Paper Autonomous Allocation Proposal DB History Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a paper-only/report-only/read-only DB-history readback node over persisted `PaperAutonomousAllocationProposalReport` rows.

**Architecture:** Mirror the existing `paper-research-packet-operator-flow-db-history` pattern. A pure reducer summarizes already-loaded allocation proposal reports; a tiny loader reads newest-first persisted proposal rows and reverses them into chronological order; a new env-only CLI command reads the final allocation proposal DB and prints aggregate history fields without writing anything.

**Tech Stack:** Python 3.12, argparse CLI, frozen dataclasses, `Decimal`-only paper notional values, existing allocation proposal store/config modules, psycopg read-only autocommit connection, pytest, CodeGraph, Claude Code plan/code review using `claude-opus-4-8` with effort `max` and OpenCode `zhipuai-coding-plan/glm-5.2`/`max` fallback.

## Global Constraints

- Preserve Phase 1 boundary: no live trading, no automatic live investing, no auth, no key handling, no wallet handling, no account handling, no account reads, no order instruction, no order construction, no order signing, no order submission, no order cancellation, no order replacement, no execution authorization, no approval workflow, no live-execution signal, no exchange mutation, no investment ranking, and no financial advice.
- The new command is `paper-autonomous-allocation-proposal-db-history --limit 25`.
- The new command accepts only `--limit`; it must reject `--dsn`, `--table`, `--persist`, `--fast`, `--live`, `--auth`, `--wallet`, `--private-key`, `--api-key`, `--account`, `--order`, `--trade`, `--execute`, `--submit`, and `--approve`.
- All DB targets come from `POLYMARKET_ALPHA_LAB_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_*` env config.
- The node reads only persisted final allocation proposal reports. It must not read upstream screening/queue tables, repair or create missing upstream reports, or write any reports.
- The default and persist allocation proposal commands remain unchanged except for shared type aliases or helper wiring needed by the new command.
- The DB-history command must validate `--limit` before env reads, runner calls, DB connects, or client construction.
- The DB-history command must require allocation proposal DB enabled and DSN present before runner or DB connect.
- The read path must use `psycopg.connect(dsn, autocommit=True)`, call the loader once, close once, and never commit or rollback.
- Operator output must be aggregate-only: no DSN, table name, schema tail, payload JSON, report hash, market question, market slug, account, wallet, key, or order material.
- Use existing store function `load_paper_autonomous_allocation_proposal_reports`; do not add a migration, writer, env config, or second table.
- Use `.venv/bin/python -m pytest`, not bare `pytest`.
- Do not use fast mode.

---

## File Structure

- Create `src/polymarket_alpha_lab/paper_autonomous_allocation_proposal_db_history.py`: pure reducer, config/report dataclasses, deterministic status/reason-code summaries.
- Create `src/polymarket_alpha_lab/paper_autonomous_allocation_proposal_db_history_load.py`: readback loader that consumes a DB-API connection and calls the existing final proposal store loader.
- Modify `src/polymarket_alpha_lab/cli.py`: add runner type alias, subparser, command branch, helper, summary printer, and redacted error path.
- Modify `src/polymarket_alpha_lab/__init__.py`: export public reducer types and builder.
- Modify `README.md` and `docs/paper-autonomous-allocation-proposal.md`: document the new read-only history command and keep boundary wording negative.
- Add tests:
  - `tests/test_paper_autonomous_allocation_proposal_db_history.py`
  - `tests/test_paper_autonomous_allocation_proposal_db_history_load.py`
  - `tests/test_cli_paper_autonomous_allocation_proposal_db_history.py`
  - `tests/test_paper_autonomous_allocation_proposal_db_history_scope.py`
  - Modify `tests/test_docs_paper_autonomous_allocation_proposal_scope.py` with required DB-history phrases and guarded-term coverage.

---

### Task 1: Pure Allocation Proposal DB-History Reducer

**Files:**
- Create: `src/polymarket_alpha_lab/paper_autonomous_allocation_proposal_db_history.py`
- Test: `tests/test_paper_autonomous_allocation_proposal_db_history.py`
- Test: `tests/test_paper_autonomous_allocation_proposal_db_history_scope.py`
- Modify: `src/polymarket_alpha_lab/__init__.py`

**Interfaces:**
- Consumes: `PaperAutonomousAllocationProposalReport`, `PROPOSAL_STATUSES` from `paper_autonomous_allocation_proposal`.
- Produces:
  - `DEFAULT_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_CONFIG_VERSION = "paper-autonomous-allocation-proposal-db-history-v0"`
  - `PaperAutonomousAllocationProposalDbHistoryConfig` with defaults `config_version=DEFAULT_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_CONFIG_VERSION`, `min_report_count=3`, `max_blocked_proposal_report_count=0`, `max_watch_proposal_report_count=0`, and `max_duplicate_generated_at_count=0`
  - `PaperAutonomousAllocationProposalDbHistoryStatusRow`
  - `PaperAutonomousAllocationProposalDbHistoryReasonCodeRow`
  - `PaperAutonomousAllocationProposalDbHistoryReport`
  - `build_paper_autonomous_allocation_proposal_db_history_report(...)`

- [ ] **Step 1: Write failing reducer tests**

Create `tests/test_paper_autonomous_allocation_proposal_db_history.py` with local report builders that use real `PaperAutonomousAllocationProposalReport` objects from the allocation proposal module. Cover:

```python
def test_allocation_proposal_db_history_summarizes_chronological_reports() -> None:
    reports = (
        _proposal_report(generated_at=T3, proposal_status="watch", reason_codes=("allocation_capped",)),
        _proposal_report(generated_at=T1, proposal_status="pass", reason_codes=("paper_autonomous_allocation_proposal_passed",)),
        _proposal_report(generated_at=T2, proposal_status="pass", reason_codes=("paper_autonomous_allocation_proposal_passed",)),
    )

    history = build_paper_autonomous_allocation_proposal_db_history_report(
        reports,
        config=PaperAutonomousAllocationProposalDbHistoryConfig(),
        generated_at=NOW,
    )

    assert history.history_status == "watch"
    assert history.report_count == 3
    assert history.first_report_generated_at == T1
    assert history.latest_report_generated_at == T3
    assert history.latest_proposal_status == "watch"
    assert history.latest_screening_gate_status == "pass"
    assert history.latest_queue_risk_status == "pass"
    assert history.latest_allocation_input_count == 2
    assert history.latest_allocation_row_count == 2
    assert history.latest_allocated_count == 1
    assert history.latest_total_allocated_paper_notional == Decimal("25.000000")
    assert [(row.proposal_status, row.status_count) for row in history.proposal_status_rows] == [
        ("pass", 2),
        ("watch", 1),
        ("blocked", 0),
    ]
    assert history.consecutive_latest_watch_count == 1
    assert history.latest_reason_codes == ("allocation_capped",)
    assert [(row.reason_code, row.report_count) for row in history.reason_code_rows] == [
        ("paper_autonomous_allocation_proposal_passed", 2),
        ("allocation_capped", 1),
    ]
```

Also cover:

```python
def test_allocation_proposal_db_history_blocks_insufficient_history() -> None:
    history = build_paper_autonomous_allocation_proposal_db_history_report(
        (),
        config=PaperAutonomousAllocationProposalDbHistoryConfig(min_report_count=2),
        generated_at=NOW,
    )
    assert history.history_status == "blocked"
    assert history.reason_codes == ("insufficient_paper_autonomous_allocation_proposal_history",)
```

And cover duplicate timestamps:

```python
def test_allocation_proposal_db_history_flags_duplicate_generated_at() -> None:
    reports = (
        _proposal_report(generated_at=T1, proposal_status="pass"),
        _proposal_report(generated_at=T1, proposal_status="pass"),
        _proposal_report(generated_at=T2, proposal_status="pass"),
    )
    history = build_paper_autonomous_allocation_proposal_db_history_report(
        reports,
        config=PaperAutonomousAllocationProposalDbHistoryConfig(),
        generated_at=NOW,
    )
    assert history.history_status == "watch"
    assert history.duplicate_generated_at_count == 1
    assert history.reason_codes == (
        "duplicate_generated_at_threshold_exceeded",
    )
```

Run:

```bash
.venv/bin/python -m pytest tests/test_paper_autonomous_allocation_proposal_db_history.py -q
```

Expected before implementation: import/module failure.

- [ ] **Step 2: Implement minimal reducer**

Create `paper_autonomous_allocation_proposal_db_history.py` with frozen dataclasses and hard-flag validation. The report fields are:

```python
generated_at: datetime
config_version: str
history_status: str
report_count: int
first_report_generated_at: datetime | None
latest_report_generated_at: datetime | None
latest_proposal_status: str | None
latest_screening_gate_status: str | None
latest_queue_risk_status: str | None
latest_allocation_input_count: int | None
latest_allocation_row_count: int | None
latest_allocated_count: int | None
latest_total_allocated_paper_notional: Decimal | None
proposal_status_rows: tuple[PaperAutonomousAllocationProposalDbHistoryStatusRow, ...]
duplicate_generated_at_count: int
consecutive_latest_pass_count: int
consecutive_latest_watch_count: int
consecutive_latest_blocked_count: int
latest_reason_codes: tuple[str, ...]
reason_code_rows: tuple[PaperAutonomousAllocationProposalDbHistoryReasonCodeRow, ...]
reason_codes: tuple[str, ...]
paper_only: bool = True
report_only: bool = True
readonly: bool = True
```

Use these reason-code semantics:

```python
insufficient_paper_autonomous_allocation_proposal_history
blocked_allocation_proposal_report_threshold_exceeded
watch_allocation_proposal_report_threshold_exceeded
duplicate_generated_at_threshold_exceeded
paper_autonomous_allocation_proposal_db_history_passed
```

Status logic:

```python
if report_count < config.min_report_count: "blocked"
elif blocked_count > config.max_blocked_proposal_report_count: "blocked"
elif watch_count > config.max_watch_proposal_report_count: "watch"
elif duplicate_generated_at_count > config.max_duplicate_generated_at_count: "watch"
else: "pass"
```

Reason-code logic is not an `elif` chain. Collect every exceeded threshold independently into `reason_codes`, then sort/dedupe the result. Only emit `paper_autonomous_allocation_proposal_db_history_passed` when no threshold reason exists.

- [ ] **Step 3: Add scope tests**

Create `tests/test_paper_autonomous_allocation_proposal_db_history_scope.py` with AST/string checks:

```python
FORBIDDEN_FRAGMENTS = (
    "private_key",
    "wallet",
    "submit_order",
    "cancel_order",
    "replace_order",
    "requests.",
    "httpx.",
    "urllib.",
    "subprocess",
    "open(",
    "print(",
)
```

Assert the reducer imports only standard library dataclass/datetime/decimal and `paper_autonomous_allocation_proposal`. Limit raw fragment scanning for `"open("` and `"print("` to `src/polymarket_alpha_lab/paper_autonomous_allocation_proposal_db_history.py`; do not scan CLI, loader, or package export files with those raw fragments. Check signing, account, and order fragments through AST import/name/call guards or word-boundary regexes instead of raw substrings so ordinary words such as assignment or account-for cannot trigger false positives.

- [ ] **Step 4: Export public API**

Modify `src/polymarket_alpha_lab/__init__.py` to import and include in `__all__`:

```python
DEFAULT_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_CONFIG_VERSION
PaperAutonomousAllocationProposalDbHistoryConfig
PaperAutonomousAllocationProposalDbHistoryReasonCodeRow
PaperAutonomousAllocationProposalDbHistoryReport
PaperAutonomousAllocationProposalDbHistoryStatusRow
build_paper_autonomous_allocation_proposal_db_history_report
```

- [ ] **Step 5: Verify Task 1**

Run:

```bash
.venv/bin/python -m pytest \
  tests/test_paper_autonomous_allocation_proposal_db_history.py \
  tests/test_paper_autonomous_allocation_proposal_db_history_scope.py \
  tests/test_init.py -q
```

Expected: all selected tests pass.

---

### Task 2: DB-History Loader And Read-Only Helper Tests

**Files:**
- Create: `src/polymarket_alpha_lab/paper_autonomous_allocation_proposal_db_history_load.py`
- Test: `tests/test_paper_autonomous_allocation_proposal_db_history_load.py`
- Later consumed by: `src/polymarket_alpha_lab/cli.py`

**Interfaces:**
- Consumes: `load_paper_autonomous_allocation_proposal_reports(connection, limit=..., table_name=...)`.
- Produces:

```python
def load_paper_autonomous_allocation_proposal_db_history_report(
    connection: object,
    *,
    config_version: str | None = None,
    proposal_status: str | None = None,
    screening_gate_status: str | None = None,
    allocation_config_version: str | None = None,
    limit: int | None,
    table_name: str,
    config: PaperAutonomousAllocationProposalDbHistoryConfig,
    generated_at: datetime,
) -> PaperAutonomousAllocationProposalDbHistoryReport:
```

- [ ] **Step 1: Write failing loader test**

Create `tests/test_paper_autonomous_allocation_proposal_db_history_load.py` and monkeypatch `load_paper_autonomous_allocation_proposal_reports` plus `build_paper_autonomous_allocation_proposal_db_history_report` in the loader module. Assert:

```python
loaded_reports = ("newest", "oldest")
builder receives ("oldest", "newest")
store receives limit, table_name, config_version, proposal_status, screening_gate_status, allocation_config_version
config type is exact PaperAutonomousAllocationProposalDbHistoryConfig
```

Run:

```bash
.venv/bin/python -m pytest tests/test_paper_autonomous_allocation_proposal_db_history_load.py -q
```

Expected before implementation: module import failure.

- [ ] **Step 2: Implement loader**

Implementation is intentionally tiny:

```python
loaded_reports = load_paper_autonomous_allocation_proposal_reports(...)
chronological_reports = tuple(reversed(tuple(loaded_reports)))
return build_paper_autonomous_allocation_proposal_db_history_report(
    chronological_reports,
    config=config,
    generated_at=generated_at,
)
```

Validate `type(config) is PaperAutonomousAllocationProposalDbHistoryConfig`.

- [ ] **Step 3: Verify Task 2**

Run:

```bash
.venv/bin/python -m pytest \
  tests/test_paper_autonomous_allocation_proposal_db_history.py \
  tests/test_paper_autonomous_allocation_proposal_db_history_load.py -q
```

Expected: all selected tests pass.

---

### Task 3: CLI Command And Read-Only DB Path

**Files:**
- Modify: `src/polymarket_alpha_lab/cli.py`
- Test: `tests/test_cli_paper_autonomous_allocation_proposal_db_history.py`

**Interfaces:**
- Consumes: `from_paper_autonomous_allocation_proposal_db_env`, `PaperAutonomousAllocationProposalDbHistoryConfig`, and `load_paper_autonomous_allocation_proposal_db_history_report`.
- Produces:
  - `paper-autonomous-allocation-proposal-db-history` subparser with only `--limit`
  - `PaperAutonomousAllocationProposalDbHistoryRunner = Callable[..., object]`
  - `_run_paper_autonomous_allocation_proposal_db_history(...)`
  - `_print_paper_autonomous_allocation_proposal_db_history_summary(report)`

- [ ] **Step 1: Write failing CLI tests**

Create `tests/test_cli_paper_autonomous_allocation_proposal_db_history.py` mirroring operator-flow history tests. Required tests:

```python
def test_allocation_proposal_db_history_cli_requires_enabled_db_config(...)
def test_allocation_proposal_db_history_cli_rejects_non_positive_limit_before_env_runner_or_connect(...)
def test_allocation_proposal_db_history_helper_rejects_invalid_limit_before_runner_or_connect(...)
def test_allocation_proposal_db_history_cli_uses_injected_runner_and_prints_summary(...)
def test_allocation_proposal_db_history_helper_default_load_path_uses_autocommit_and_closes_only(...)
def test_allocation_proposal_db_history_helper_raises_on_missing_psycopg(...)
def test_allocation_proposal_db_history_cli_runner_failure_redacts_dsn_table_payloads_questions_hashes(...)
def test_allocation_proposal_db_history_cli_rejects_db_persist_fast_live_auth_wallet_account_order_and_execution_flags(...)
```

Expected summary lines:

```text
paper-autonomous-allocation-proposal-db-history: history_status=watch report_count=3 first_report_generated_at=2026-06-24T08:00:00+00:00 latest_report_generated_at=2026-06-24T12:00:00+00:00 latest_proposal_status=watch latest_screening_gate_status=pass latest_queue_risk_status=pass latest_allocation_input_count=2 latest_allocation_row_count=2 latest_allocated_count=1 latest_total_allocated_paper_notional=25.000000 pass=2 watch=1 blocked=0 duplicate_generated_at_count=1 consecutive_latest_pass_count=0 consecutive_latest_watch_count=1 consecutive_latest_blocked_count=0
proposal_status_rows: pass=2 watch=1 blocked=0
latest_reason_codes: allocation_capped
reason_code_rows: paper_autonomous_allocation_proposal_passed=2 allocation_capped=1
reason_codes: duplicate_generated_at_threshold_exceeded watch_allocation_proposal_report_threshold_exceeded
```

Run:

```bash
.venv/bin/python -m pytest tests/test_cli_paper_autonomous_allocation_proposal_db_history.py -q
```

Expected before implementation: parser/runner missing failures.

- [ ] **Step 2: Add parser and main dependency injection**

In `cli.py`, add:

```python
PaperAutonomousAllocationProposalDbHistoryRunner = Callable[..., object]
```

Add `paper_autonomous_allocation_proposal_db_history_runner: PaperAutonomousAllocationProposalDbHistoryRunner | None = None` to `main(...)`.

Add subparser:

```python
allocation_proposal_db_history = subparsers.add_parser(
    "paper-autonomous-allocation-proposal-db-history",
)
allocation_proposal_db_history.add_argument("--limit", type=int, default=25)
```

- [ ] **Step 3: Add command branch**

Add branch before the existing allocation proposal branch:

```python
if args.command == "paper-autonomous-allocation-proposal-db-history":
    command_name = "paper-autonomous-allocation-proposal-db-history"
    try:
        if isinstance(args.limit, bool) or type(args.limit) is not int or args.limit < 1:
            raise ValueError(f"{command_name} limit must be positive")
        db_config = from_paper_autonomous_allocation_proposal_db_env()
        if not db_config.enabled:
            raise ValueError(f"{command_name} requires autonomous allocation proposal DB to be enabled")
        dsn = db_config.dsn
        if dsn is None:
            raise ValueError(f"{command_name} requires an autonomous allocation proposal DB DSN")
        report = _run_paper_autonomous_allocation_proposal_db_history(
            dsn=dsn,
            table_name=db_config.table_name,
            limit=args.limit,
            runner=paper_autonomous_allocation_proposal_db_history_runner,
        )
        _print_paper_autonomous_allocation_proposal_db_history_summary(report)
        return 0
    except Exception as exc:
        print(f"{command_name} failed: {exc}", file=sys.stderr)
        return 1
```

- [ ] **Step 4: Add read-only helper**

Add `_run_paper_autonomous_allocation_proposal_db_history` matching operator-flow:

```python
generated_at = datetime.now(UTC)
config = PaperAutonomousAllocationProposalDbHistoryConfig()
if runner is not None: return runner(...)
import psycopg
connection = psycopg.connect(dsn, autocommit=True)
try:
    return load_paper_autonomous_allocation_proposal_db_history_report(...)
finally:
    connection.close()
```

Follow the operator-flow history helper's import guard: catch `ModuleNotFoundError` for missing `psycopg` and raise a helpful `RuntimeError` telling the operator to install the postgres extra. Reuse the existing `_redacted_paper_research_packet_db_history_error(...)` helper for read failures because it already redacts DSN, table name and tail, payloads, questions, and sha256 values.

Add a focused CLI/helper test for the missing-postgres path by setting `sys.modules["psycopg"]` to an object that makes import fail, or by monkeypatching the import path consistently with existing CLI tests. Expected message must include `psycopg is required` and must not leak the DSN.

Add a focused redaction-helper wiring test by monkeypatching `cli._redacted_paper_research_packet_db_history_error` to record `exc`, `dsn`, and `table_name`, return `RuntimeError("sentinel redacted history error")`, and raising from an injected runner. Assert the helper was called with the allocation proposal DB DSN/table and that stderr contains the sentinel message. Keep the existing output-redaction test as the behavioral guard.

- [ ] **Step 5: Add summary printer**

Add `_print_paper_autonomous_allocation_proposal_db_history_summary(report)` near other paper autonomous printers. It must print only aggregate fields and row counts. Use existing `_format_optional_datetime`, `_format_optional_int`, and `_format_optional_decimal` patterns if present; otherwise implement local formatting consistent with existing summary printers.

- [ ] **Step 6: Verify Task 3**

Run:

```bash
.venv/bin/python -m pytest tests/test_cli_paper_autonomous_allocation_proposal_db_history.py -q
```

Expected: all selected tests pass.

---

### Task 4: Docs And Boundary Tests

**Files:**
- Modify: `README.md`
- Modify: `docs/paper-autonomous-allocation-proposal.md`
- Modify if needed: `tests/test_docs_paper_autonomous_allocation_proposal_scope.py`

**Interfaces:**
- Produces operator-facing documentation for the new read-only DB-history command.

- [ ] **Step 1: Write or extend docs scope tests**

If `tests/test_docs_paper_autonomous_allocation_proposal_scope.py` currently scans the whole allocation section, add required phrases:

```python
"paper-autonomous-allocation-proposal-db-history --limit 25"
"reads only persisted final allocation proposal reports"
"does not write reports"
"does not read upstream tables"
```

Also extend forbidden flag phrase coverage for the new command if the helper has command-specific expectations.

Extend `test_readme_places_allocation_section_after_screening_gate_block` so it asserts:

```python
allocation_command_start < persist_command_start < db_history_command_start < next_section_start
```

- [ ] **Step 2: Update docs**

Add a short "DB History Readback" subsection in both README and `docs/paper-autonomous-allocation-proposal.md`:

```bash
.venv/bin/polymarket-alpha-lab paper-autonomous-allocation-proposal-db-history --limit 25
```

Required wording:

- env-only, read-only, paper-only/report-only/readonly
- accepts only `--limit`
- reads the final allocation proposal DB configured by env
- does not write reports
- does not read upstream screening/queue tables
- does not place orders, approve execution, read accounts, or mutate exchange state
- prints aggregate history status, proposal-status counts, latest aggregate allocation counts, duplicate timestamp count, and reason-code summaries

Do not include sample DSNs, real table names beyond env variable names already present, payload JSON, market questions, or market slugs.

In `README.md`, insert the new command marker inside the existing allocation section after the persist command marker and before `## Level 1B Node 1 Status`, preserving `tests/test_docs_paper_autonomous_allocation_proposal_scope.py::test_readme_places_allocation_section_after_screening_gate_block`. Every new line containing guarded terms such as live, auth, key, wallet, account, order, trade, approve, execute, submit, cancel, replace, sign, or financial advice must include negative boundary wording such as `no`, `not`, `does not`, `must not`, `read-only`, `paper-only/report-only/read-only`, or `no-write`.

- [ ] **Step 3: Verify Task 4**

Run:

```bash
.venv/bin/python -m pytest tests/test_docs_paper_autonomous_allocation_proposal_scope.py -q
```

Expected: docs tests pass.

---

### Task 5: Integrated Verification, Review, Commit, Push, Handoff

**Files:**
- Update local scratch ledger: `.superpowers/sdd/progress.md`
- Create review output under `.superpowers/reviews/` only; do not commit scratch files.

- [ ] **Step 1: Run focused verification**

Run:

```bash
.venv/bin/python -m pytest \
  tests/test_paper_autonomous_allocation_proposal_db_history.py \
  tests/test_paper_autonomous_allocation_proposal_db_history_load.py \
  tests/test_cli_paper_autonomous_allocation_proposal_db_history.py \
  tests/test_paper_autonomous_allocation_proposal_db_history_scope.py \
  tests/test_docs_paper_autonomous_allocation_proposal_scope.py \
  tests/test_init.py -q
```

- [ ] **Step 2: Run full verification**

Run:

```bash
.venv/bin/python -m pytest -q
.venv/bin/python -m compileall -q src tests
git diff --check
codegraph status .
```

- [ ] **Step 3: Submit implementation to Claude Code review**

Run from repo root:

```bash
claude -p --model claude-opus-4-8 --effort max \
  "Read-only review only. Do not modify files. Review the current git diff for the paper-autonomous-allocation-proposal-db-history node. Check Phase 1 boundaries, read-only DB behavior, CLI redaction, no live/auth/order/account surfaces, and test adequacy. Report Critical/Important/Minor findings with file/line references. If no Critical/Important findings, say so clearly." \
  > .superpowers/reviews/claude-allocation-proposal-db-history-review.md 2>&1
```

If Claude Code cannot run, times out twice, or reports model/provider failure, run fallback:

```bash
opencode run --model zhipuai-coding-plan/glm-5.2 --variant max \
  "Read-only review only. Do not modify files. Review the current git diff for the paper-autonomous-allocation-proposal-db-history node. Check Phase 1 boundaries, read-only DB behavior, CLI redaction, no live/auth/order/account surfaces, and test adequacy. Report Critical/Important/Minor findings with file/line references. If no Critical/Important findings, say so clearly." \
  > .superpowers/reviews/opencode-allocation-proposal-db-history-review.md 2>&1
```

Fix any Critical/Important findings and rerun the focused/full verification and review.

- [ ] **Step 4: Commit and push**

Stage only production, test, and docs files. Do not stage `.superpowers/`.

```bash
git add src/polymarket_alpha_lab/paper_autonomous_allocation_proposal_db_history.py \
  src/polymarket_alpha_lab/paper_autonomous_allocation_proposal_db_history_load.py \
  src/polymarket_alpha_lab/cli.py \
  src/polymarket_alpha_lab/__init__.py \
  tests/test_paper_autonomous_allocation_proposal_db_history.py \
  tests/test_paper_autonomous_allocation_proposal_db_history_load.py \
  tests/test_cli_paper_autonomous_allocation_proposal_db_history.py \
  tests/test_paper_autonomous_allocation_proposal_db_history_scope.py \
  tests/test_docs_paper_autonomous_allocation_proposal_scope.py \
  README.md \
  docs/paper-autonomous-allocation-proposal.md \
  docs/superpowers/plans/2026-06-24-paper-autonomous-allocation-proposal-db-history.md
git commit -m "feat: add allocation proposal DB history"
git push origin main
```

- [ ] **Step 5: Handoff Summary**

Write a concise Handoff Summary with:

- repo state
- commit SHA and push status
- verified commands
- review tool and verdict
- uncommitted files
- recommended next node

Expected next node after this one: `paper-autonomous-allocation-proposal-db-history-gate`.

---

## Plan Self-Review

- Spec coverage: the plan covers pure reducer, loader, CLI, docs, exports, verification, review, commit, push, and handoff. It preserves the paper-only/report-only/read-only boundary and does not introduce live trading/auth/order/account surfaces.
- Placeholder scan: no task contains placeholder markers or unbounded "add tests" language without concrete test names and assertions.
- Type consistency: all produced names use the `PaperAutonomousAllocationProposalDbHistory*` prefix and match the planned CLI command `paper-autonomous-allocation-proposal-db-history`.
- Scope decision: this plan intentionally does not add a history gate. That is the next node after persisted history readback is available and reviewed.
