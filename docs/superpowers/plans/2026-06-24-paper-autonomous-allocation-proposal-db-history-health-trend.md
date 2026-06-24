# Paper Autonomous Allocation Proposal DB History Health Trend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. The reducer, loader, CLI/docs, and scope-test lanes are intentionally separable so multiple workers can develop in parallel without editing the same files.

**Goal:** Add a paper-only/report-only/read-only trend node over persisted paper autonomous allocation proposal DB-history health snapshots so the pipeline can monitor drift, streaks, duplicates, and repeated reasons over time without producing investment rankings, approval workflow decisions, or any live execution signal.

**Architecture:** Build a pure reducer over a sequence of exact `PaperAutonomousAllocationProposalDbHistoryHealthReport` values. A tiny shared helper should own the one-SELECT chronological prefix-window DB-history rebuild so the existing health loader and the new health-trend loader cannot drift. The new trend loader should reuse that shared helper, derive prefix-window health reports in memory, and pass those health reports into the trend reducer. A new env-only CLI command prints aggregate trend fields. The node remains read-only and consumes only persisted final allocation proposal reports; it must not read upstream screening/queue tables, write reports, mutate exchange state, or create orders.

**Tech Stack:** Python 3.12, argparse CLI, frozen dataclasses, `Decimal` for notional fields, existing allocation proposal DB-history/history-health reducers and load modules, psycopg read-only autocommit connection in CLI boundary only, pytest, CodeGraph, and local OpenCode reviews using `zhipuai-coding-plan/glm-5.2` with variant `max`.

## Global Constraints

- Preserve Phase 1 boundary: no live trading, no automatic live investing, no auth, no key handling, no wallet handling, no account handling, no account reads, no order instruction, no order construction, no order signing, no order submission, no order cancellation, no order replacement, no execution authorization, no approval workflow, no live-execution signal, no exchange mutation, no investment ranking, and no financial advice.
- The planned command is `paper-autonomous-allocation-proposal-db-history-health-trend --limit 25`.
- The command accepts only `--limit`; it must reject `--dsn`, `--table`, `--persist`, `--fast`, `--live`, `--auth`, `--wallet`, `--private-key`, `--api-key`, `--account`, `--order`, `--trade`, `--execute`, `--submit`, and `--approve`.
- All DB targets come from `POLYMARKET_ALPHA_LAB_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_*` env config.
- The node reads only persisted final allocation proposal reports through the existing allocation proposal store loader. It must not read upstream screening/queue tables, repair missing reports, create reports, or write any reports.
- The reducer must be pure: no `psycopg`, Supabase clients, `os.environ`, CLI imports, network clients, filesystem writes, or printing.
- The loader must not connect, close, commit, rollback, insert, update, delete, create tables, create indexes, or mutate supplied connections.
- The CLI default DB path may connect with `psycopg.connect(dsn, autocommit=True)`, call the loader once, close once, and never commit or rollback.
- Validate `--limit` before env reads, runner calls, DB connects, or client construction.
- Require allocation proposal DB enabled and DSN present before runner or DB connect.
- Operator output must be aggregate-only: no DSN, table name, schema tail, payload JSON, report hash, market question, market slug, account, wallet, key, or order material.
- Keep Decimal-only posture; do not introduce float arithmetic for notional or ratio fields.
- Rebuild prefix windows entirely in memory from one chronological proposal-report sequence. Do not add a new persistence table, a second DB roundtrip per prefix, or a loader that reads health rows from storage.
- The trend node must consume exact `PaperAutonomousAllocationProposalDbHistoryHealthReport` values, not ad hoc dicts or JSON payloads.
- Use `.venv/bin/python -m pytest`, not bare `pytest`.
- Do not use fast mode.
- Completed implementation must pass focused tests, full tests, `compileall`, `git diff --check`, secret scan over tracked source/docs/tests, CodeGraph sync/status, and OpenCode post-node review before commit/push.

## File Structure

- Create `src/polymarket_alpha_lab/paper_autonomous_allocation_proposal_db_history_prefix_load.py`: shared read-only helper that loads final allocation proposal reports once and rebuilds deterministic chronological prefix-window DB-history reports.
- Create `src/polymarket_alpha_lab/paper_autonomous_allocation_proposal_db_history_health_trend.py`: pure trend reducer over a sequence of health reports.
- Create `src/polymarket_alpha_lab/paper_autonomous_allocation_proposal_db_history_health_trend_load.py`: read-only loader composition that reuses the shared prefix helper, derives prefix-window DB-history health reports, and reduces them to a trend report.
- Modify `src/polymarket_alpha_lab/paper_autonomous_allocation_proposal_db_history_health_load.py`: refactor the existing health loader to reuse the shared prefix helper instead of owning a second copy of prefix-window rebuild logic.
- Modify `src/polymarket_alpha_lab/cli.py`: add runner alias, subparser, command branch, helper, summary printer, and redacted error path.
- Modify `src/polymarket_alpha_lab/__init__.py`: export public trend reducer types and builder only.
- Modify `README.md` and `docs/paper-autonomous-allocation-proposal.md`: document the read-only health-trend command and keep boundary wording negative.
- Add tests:
  - `tests/test_paper_autonomous_allocation_proposal_db_history_prefix_load.py`
  - `tests/test_paper_autonomous_allocation_proposal_db_history_health_trend.py`
  - Modify `tests/test_paper_autonomous_allocation_proposal_db_history_health_load.py`
  - `tests/test_paper_autonomous_allocation_proposal_db_history_health_trend_load.py`
  - `tests/test_cli_paper_autonomous_allocation_proposal_db_history_health_trend.py`
  - `tests/test_cli_paper_autonomous_allocation_proposal_db_history_health_trend_scope.py`
  - `tests/test_paper_autonomous_allocation_proposal_db_history_health_trend_scope.py`
  - Modify `tests/test_docs_paper_autonomous_allocation_proposal_scope.py`
  - Modify `tests/test_init.py`
  - Modify existing scope tests that own `EXPECTED_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_EXPORTS`:
    - `tests/test_analytics_history_scope.py`
    - `tests/test_analytics_scope.py`
    - `tests/test_forecast_evidence_scope.py`
    - `tests/test_manual_review_queue_scope.py`
    - `tests/test_proposal_evidence_comparison_history_batch_health_scope.py`
    - `tests/test_proposal_evidence_comparison_history_scope.py`
    - `tests/test_proposal_evidence_comparison_scope.py`
    - `tests/test_proposal_packet_scope.py`
    - `tests/test_proposal_review_coverage_scope.py`
    - `tests/test_proposal_review_diagnostics_scope.py`
    - `tests/test_proposal_review_dossier_batch_scope.py`
    - `tests/test_proposal_review_dossier_scope.py`
    - `tests/test_proposal_review_quality_scope.py`
    - `tests/test_proposal_review_scope.py`
    - `tests/test_proposal_review_summary_scope.py`

## Parallel Development Lanes

- **Lane A, pure reducer:** Own only `paper_autonomous_allocation_proposal_db_history_health_trend.py`, its reducer tests, and the reducer scope test.
- **Lane B, shared prefix + loader:** Own `paper_autonomous_allocation_proposal_db_history_prefix_load.py`, `paper_autonomous_allocation_proposal_db_history_health_load.py`, `paper_autonomous_allocation_proposal_db_history_health_trend_load.py`, and their loader tests. Use a stubbed existing proposal-store loader or stubbed builders where needed to avoid real DB access.
- **Lane C, CLI:** Own only `cli.py` plus CLI and CLI scope tests. Depend on agreed reducer/loader symbol names but do not edit reducer internals.
- **Lane D, docs/exports:** Own `__init__.py`, README/docs, `tests/test_init.py`, and existing scope allowlists.
- **Lane E, verification/review:** Own test execution, CodeGraph sync/status, secret scan, OpenCode review collection, and final staging audit. This lane must not edit source unless review finds a concrete issue.

Avoid overlapping file edits across lanes. If a lane needs a shared interface change, pause and update this plan before implementation.

Before dispatching Lanes B and C, freeze this shared loader interface exactly:

```python
load_paper_autonomous_allocation_proposal_db_history_prefix_reports(
    connection,
    *,
    limit: int | None,
    table_name: str,
    history_config: PaperAutonomousAllocationProposalDbHistoryConfig,
) -> tuple[PaperAutonomousAllocationProposalDbHistoryReport, ...]
```

This helper is internal-only and must not be added to package-root exports.

Also freeze this shared loader interface exactly:

```python
load_paper_autonomous_allocation_proposal_db_history_health_trend_report(
    connection,
    *,
    limit: int | None,
    table_name: str,
    history_config: PaperAutonomousAllocationProposalDbHistoryConfig,
    health_config: PaperAutonomousAllocationProposalDbHistoryHealthConfig,
    trend_config: PaperAutonomousAllocationProposalDbHistoryHealthTrendConfig,
    generated_at: datetime,
)
```

Any change to this function name or keyword signature requires a plan update before parallel work continues.

Also freeze these CLI entry-point names before Lanes C and D start:

```python
PaperAutonomousAllocationProposalDbHistoryHealthTrendRunner
_run_paper_autonomous_allocation_proposal_db_history_health_trend
_print_paper_autonomous_allocation_proposal_db_history_health_trend_summary
```

Any change to those symbol names requires a plan update before parallel work continues.

---

### Task 1: Pure DB-History Health Trend Reducer

**Files:**
- Create: `src/polymarket_alpha_lab/paper_autonomous_allocation_proposal_db_history_health_trend.py`
- Test: `tests/test_paper_autonomous_allocation_proposal_db_history_health_trend.py`
- Test: `tests/test_paper_autonomous_allocation_proposal_db_history_health_trend_scope.py`

**Interfaces:**
- Consumes a sequence of exact `PaperAutonomousAllocationProposalDbHistoryHealthReport` values.
- Produces:
  - `DEFAULT_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_HEALTH_TREND_CONFIG_VERSION = "paper-autonomous-allocation-proposal-db-history-health-trend-v0"`
  - `PaperAutonomousAllocationProposalDbHistoryHealthTrendConfig`
  - `PaperAutonomousAllocationProposalDbHistoryHealthTrendReasonCodeRow`
  - `PaperAutonomousAllocationProposalDbHistoryHealthTrendSnapshotSummary`
  - `PaperAutonomousAllocationProposalDbHistoryHealthTrendReport`
  - `build_paper_autonomous_allocation_proposal_db_history_health_trend_report(health_reports, *, config, generated_at)`

- [ ] **Step 1: Write failing reducer tests**

Cover:
- Empty input yields a valid empty trend report with `source_health_report_count == 0`, all streaks/count deltas absent or zero as appropriate, and no AttributeError on real report printing.
- Non-empty input preserves chronological ordering by `(generated_at, input_position)` after deterministic normalization.
- `latest_health_status` tracks the latest health snapshot status.
- `health_status_counts` deterministically cover `pass`, `watch`, and `blocked` in status order as a full three-row tuple.
- `consecutive_latest_watch_count` and `consecutive_latest_blocked_count` match latest suffix streaks.
- `duplicate_generated_at_count` counts duplicate `generated_at` timestamps across supplied health snapshots.
- `history_report_count_first`, `history_report_count_latest`, and `history_report_count_delta` are computed correctly.
- `pass_report_count_first/latest/delta`, `watch_report_count_first/latest/delta`, and `blocked_report_count_first/latest/delta` are computed correctly.
- `latest_allocated_count_first/latest/delta` are computed correctly as `int | None`.
- `latest_total_allocated_paper_notional_first/latest/delta` are computed correctly as `Decimal | None`, quantized exactly, and reject float corruption.
- `latest_source_age_seconds_first/latest/delta` and `max_source_age_seconds_first/latest/delta` are computed correctly as `int | None`.
- `latest_reason_code_counts`, `total_reason_code_counts`, `repeated_reason_code_counts`, and per-reason `reason_code_rows` are deterministic and derived from source health `reason_codes`, counting source-report presence not repeated string occurrence within one snapshot.
- Dataclasses are frozen and hard-enforce `paper_only is True`, `report_only is True`, and `readonly is True`.
- Exact-type validation rejects health report subclasses, config subclasses, datetime subclasses, naive datetimes, bool-as-int counts, floats, and corrupted direct constructor values.

- [ ] **Step 2: Implement the reducer**

Status model:

```python
HEALTH_STATUSES = ("pass", "watch", "blocked")
```

Recommended report fields:

```python
generated_at: datetime
config_version: str
source_health_report_count: int
first_generated_at: datetime | None
latest_generated_at: datetime | None
latest_health_status: str | None
health_status_counts: tuple[tuple[str, int], ...]
consecutive_latest_watch_count: int
consecutive_latest_blocked_count: int
duplicate_generated_at_count: int
history_report_count_first: int | None
history_report_count_latest: int | None
history_report_count_delta: int | None
pass_report_count_first: int | None
pass_report_count_latest: int | None
pass_report_count_delta: int | None
watch_report_count_first: int | None
watch_report_count_latest: int | None
watch_report_count_delta: int | None
blocked_report_count_first: int | None
blocked_report_count_latest: int | None
blocked_report_count_delta: int | None
latest_allocated_count_first: int | None
latest_allocated_count_latest: int | None
latest_allocated_count_delta: int | None
latest_total_allocated_paper_notional_first: Decimal | None
latest_total_allocated_paper_notional_latest: Decimal | None
latest_total_allocated_paper_notional_delta: Decimal | None
latest_source_age_seconds_first: int | None
latest_source_age_seconds_latest: int | None
latest_source_age_seconds_delta: int | None
max_source_age_seconds_first: int | None
max_source_age_seconds_latest: int | None
max_source_age_seconds_delta: int | None
latest_reason_code_counts: tuple[tuple[str, int], ...]
total_reason_code_counts: tuple[tuple[str, int], ...]
repeated_reason_code_counts: tuple[tuple[str, int], ...]
reason_code_rows: tuple[PaperAutonomousAllocationProposalDbHistoryHealthTrendReasonCodeRow, ...]
source_summaries: tuple[PaperAutonomousAllocationProposalDbHistoryHealthTrendSnapshotSummary, ...]
```

Normalization and derivation rules:
- Accept only `list` or `tuple` inputs, then normalize to exact `PaperAutonomousAllocationProposalDbHistoryHealthReport` values.
- Sort summaries by `(generated_at, input_position)` so equal timestamps remain deterministic.
- `source_health_report_count == len(source_summaries)`.
- `health_status_counts` counts snapshot-level `health_status` values only.
- `pass_report_count_*`, `watch_report_count_*`, and `blocked_report_count_*` derive from the first/latest source health report scalar fields and therefore summarize underlying source-history counts, not snapshot-level trend status counts.
- For empty input, all `*_first`, `*_latest`, and `*_delta` fields are `None`; all count/streak/duplicate fields are zero; all tuple summaries are empty.
- Use `DECIMAL_QUANTUM = Decimal("0.000001")` for every Decimal field and every Decimal delta in this node.
- `*_delta` for `Decimal` fields is `latest - first` and must preserve Decimal-only posture.
- `*_delta` for integer fields is `latest - first`.
- `latest_reason_code_counts` counts the latest snapshot `reason_codes`.
- `total_reason_code_counts` counts total appearances across snapshots.
- `repeated_reason_code_counts` includes only reason codes with total count > 1.
- `reason_code_rows` should carry `reason_code`, `total_count`, `latest_count`, and `snapshot_count`.
- No status or recommendation should be invented beyond what source health snapshots already expose; this is a trend report, not another gate.

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
  tests/test_paper_autonomous_allocation_proposal_db_history_health_trend.py \
  tests/test_paper_autonomous_allocation_proposal_db_history_health_trend_scope.py -q
```

---

### Task 2: Shared Prefix Helper and Read-Only Loader Composition

**Files:**
- Create: `src/polymarket_alpha_lab/paper_autonomous_allocation_proposal_db_history_prefix_load.py`
- Modify: `src/polymarket_alpha_lab/paper_autonomous_allocation_proposal_db_history_health_load.py`
- Test: `tests/test_paper_autonomous_allocation_proposal_db_history_prefix_load.py`
- Modify: `tests/test_paper_autonomous_allocation_proposal_db_history_health_load.py`
- Create: `src/polymarket_alpha_lab/paper_autonomous_allocation_proposal_db_history_health_trend_load.py`
- Test: `tests/test_paper_autonomous_allocation_proposal_db_history_health_trend_load.py`

**Interfaces:**
- Produces `load_paper_autonomous_allocation_proposal_db_history_prefix_reports(connection, *, limit, table_name, history_config)`.
- Refactors `load_paper_autonomous_allocation_proposal_db_history_health_report(...)` to consume that shared helper instead of rebuilding prefix-window history reports inline.
- Produces `load_paper_autonomous_allocation_proposal_db_history_health_trend_report(connection, *, limit, table_name, history_config, health_config, trend_config, generated_at)`.
- Loads final allocation proposal reports once via `load_paper_autonomous_allocation_proposal_reports(connection, limit=limit, table_name=table_name)`, reverses the DB-descending output into chronological order, builds prefix-window `PaperAutonomousAllocationProposalDbHistoryReport` values from the first sufficient prefix onward with `build_paper_autonomous_allocation_proposal_db_history_report(...)`, builds matching prefix-window `PaperAutonomousAllocationProposalDbHistoryHealthReport` values with each source history report’s `generated_at`, then builds one final trend report from that exact health-report sequence.

- [ ] **Step 1: Write failing loader tests**

Cover:
- The shared prefix helper delegates `connection`, `limit`, and `table_name` to the existing final proposal report store loader exactly once.
- The shared prefix helper builds prefix-window DB-history reports from the first sufficient prefix onward with the supplied `history_config` and each window’s latest proposal `generated_at`.
- The existing health loader still returns the same exact health report semantics after being refactored to consume the shared prefix helper.
- Delegates `connection`, `limit`, and `table_name` to the existing final proposal report store loader exactly once.
- Builds prefix-window DB-history reports from the first sufficient prefix onward with the supplied `history_config` and each window’s latest proposal `generated_at`.
- Builds prefix-window health reports from those source history reports with the supplied `health_config` and each source history report’s `generated_at`.
- Builds the trend report from the exact health report sequence and `trend_config`.
- When fewer proposal reports than `history_config.min_report_count` are loaded, the shared prefix helper yields an empty history-report sequence, the trend loader builds one blocked boundary health report from empty source history with the supplied `generated_at`, and the resulting trend report contains that single boundary snapshot so insufficient history remains visible to the operator.
- Rejects non-exact `history_config`, `health_config`, and `trend_config` before reading.
- Does not call `commit`, `rollback`, `close`, `cursor`, `execute`, `insert`, `update`, or `delete` on the supplied connection directly.
- Does not import env config, CLI, psycopg, Supabase clients, or network modules.

- [ ] **Step 2: Implement loader**

Keep it small and boundary-free. The shared prefix helper owns the only copy of prefix-window history rebuild logic:

```python
proposal_reports = tuple(
    reversed(
        tuple(
            load_paper_autonomous_allocation_proposal_reports(
                connection,
                limit=limit,
                table_name=table_name,
            ),
        ),
    ),
)
history_reports = []
for i in range(history_config.min_report_count - 1, len(proposal_reports)):
    history_reports.append(
        build_paper_autonomous_allocation_proposal_db_history_report(
            proposal_reports[: i + 1],
            config=history_config,
            generated_at=proposal_reports[i].generated_at,
        ),
    )
return tuple(history_reports)
```

The trend loader should then compose health snapshots explicitly and completely:

```python
history_reports = load_paper_autonomous_allocation_proposal_db_history_prefix_reports(
    connection,
    limit=limit,
    table_name=table_name,
    history_config=history_config,
)
health_reports = []
source_history_reports = []
for history_report in history_reports:
    source_history_reports.append(history_report)
    health_reports.append(
        build_paper_autonomous_allocation_proposal_db_history_health_report(
            tuple(source_history_reports),
            config=health_config,
            generated_at=history_report.generated_at,
        ),
    )
return build_paper_autonomous_allocation_proposal_db_history_health_trend_report(
    tuple(health_reports),
    config=trend_config,
    generated_at=generated_at,
)
```

Use one SELECT plus pure in-memory reducer calls only. Do not add a writer, migration, new DB table, or a second DB round-trip per prefix. The existing health loader and the new trend loader must both depend on the shared prefix helper so prefix semantics live in one place only.

Run:

```bash
.venv/bin/python -m pytest \
  tests/test_paper_autonomous_allocation_proposal_db_history_prefix_load.py \
  tests/test_paper_autonomous_allocation_proposal_db_history_health_load.py \
  tests/test_paper_autonomous_allocation_proposal_db_history_health_trend_load.py -q
```

---

### Task 3: CLI Health Trend Command

**Files:**
- Modify: `src/polymarket_alpha_lab/cli.py`
- Test: `tests/test_cli_paper_autonomous_allocation_proposal_db_history_health_trend.py`
- Test: `tests/test_cli_paper_autonomous_allocation_proposal_db_history_health_trend_scope.py`

**Interfaces:**
- Adds command `paper-autonomous-allocation-proposal-db-history-health-trend`.
- Adds:
  - `PaperAutonomousAllocationProposalDbHistoryHealthTrendRunner`
  - `_run_paper_autonomous_allocation_proposal_db_history_health_trend(...)`
  - `_print_paper_autonomous_allocation_proposal_db_history_health_trend_summary(report)`

- [ ] **Step 1: Write failing CLI tests**

Cover:
- `--limit` validation happens before env reads, runner invocation, psycopg import, and DB connect.
- Command requires allocation proposal DB enabled and DSN present from env before default load path.
- Injected runner path receives only aggregate-safe fields plus exact config objects and `generated_at`.
- Default load path imports psycopg lazily, uses `psycopg.connect(dsn, autocommit=True)`, calls the new loader once, and closes once without commit/rollback.
- Errors are redacted through the existing `_redacted_paper_research_packet_db_history_error` helper.
- Printed summary uses only real trend reducer fields and does not expose DSN, table, schema tail, payload JSON, hashes, market slugs, or account material.
- Command rejects write/live/auth/order/account flags through existing CLI scope behavior.

- [ ] **Step 2: Implement CLI wiring**

Follow the existing `paper-autonomous-allocation-proposal-db-history-health` command pattern exactly:
- reuse allocation proposal DB env config
- instantiate:
  - `PaperAutonomousAllocationProposalDbHistoryConfig()`
  - `PaperAutonomousAllocationProposalDbHistoryHealthConfig()`
  - `PaperAutonomousAllocationProposalDbHistoryHealthTrendConfig()`
- default path calls the new loader once
- summary printer prints only aggregate fields from the real reducer schema

Recommended summary fields:
- `trend_count`
- `latest_health_status`
- `history_report_count_delta`
- `pass_report_count_delta`
- `watch_report_count_delta`
- `blocked_report_count_delta`
- `latest_allocated_count_delta`
- `latest_total_allocated_paper_notional_delta`
- `duplicate_generated_at_count`
- `consecutive_latest_watch_count`
- `consecutive_latest_blocked_count`
- `latest_reason_code_counts`

Run:

```bash
.venv/bin/python -m pytest \
  tests/test_cli_paper_autonomous_allocation_proposal_db_history_health_trend.py \
  tests/test_cli_paper_autonomous_allocation_proposal_db_history_health_trend_scope.py -q
```

---

### Task 4: Exports, Docs, and Scope Allow Lists

**Files:**
- Modify: `src/polymarket_alpha_lab/__init__.py`
- Modify: `README.md`
- Modify: `docs/paper-autonomous-allocation-proposal.md`
- Modify: `tests/test_init.py`
- Modify:
  - `tests/test_analytics_history_scope.py`
  - `tests/test_analytics_scope.py`
  - `tests/test_docs_paper_autonomous_allocation_proposal_scope.py`
  - `tests/test_forecast_evidence_scope.py`
  - `tests/test_manual_review_queue_scope.py`
  - `tests/test_proposal_evidence_comparison_history_batch_health_scope.py`
  - `tests/test_proposal_evidence_comparison_history_scope.py`
  - `tests/test_proposal_evidence_comparison_scope.py`
  - `tests/test_proposal_packet_scope.py`
  - `tests/test_proposal_review_coverage_scope.py`
  - `tests/test_proposal_review_diagnostics_scope.py`
  - `tests/test_proposal_review_dossier_batch_scope.py`
  - `tests/test_proposal_review_dossier_scope.py`
  - `tests/test_proposal_review_quality_scope.py`
  - `tests/test_proposal_review_scope.py`
  - `tests/test_proposal_review_summary_scope.py`

**Interfaces:**
- Export from package root:
  - `PaperAutonomousAllocationProposalDbHistoryHealthTrendConfig`
  - `PaperAutonomousAllocationProposalDbHistoryHealthTrendReasonCodeRow`
  - `PaperAutonomousAllocationProposalDbHistoryHealthTrendSnapshotSummary`
  - `PaperAutonomousAllocationProposalDbHistoryHealthTrendReport`
  - `build_paper_autonomous_allocation_proposal_db_history_health_trend_report`
- Do not export loader, CLI runner aliases, printers, or internal constants unless already standard.

- [ ] **Step 1: Write failing export/doc tests**

Cover:
- New public exports appear in `lab.__all__`.
- Loader and CLI internals remain unexported.
- Allocation proposal docs mention the new command after the DB history health section.
- Docs keep negative boundary wording: read-only, no writes, no upstream screening/queue table reads, no live trading, no approval workflow, no financial advice.

- [ ] **Step 2: Implement exports and docs**

Docs should add a new section:

```bash
.venv/bin/polymarket-alpha-lab paper-autonomous-allocation-proposal-db-history-health-trend --limit 25
```

Section content should say:
- env-only, read-only, paper-only/report-only/readonly, no-write
- reads only persisted final allocation proposal history through DB history readback semantics
- does not write reports and does not read upstream screening/queue tables
- does not place orders, approve execution, read accounts, or mutate exchange state
- trend output is operator monitoring only, not permission to trade, not financial advice, not investment ranking, and not an approval workflow

Run:

```bash
.venv/bin/python -m pytest \
  tests/test_docs_paper_autonomous_allocation_proposal_scope.py \
  tests/test_init.py \
  tests/test_analytics_history_scope.py \
  tests/test_analytics_scope.py \
  tests/test_forecast_evidence_scope.py \
  tests/test_manual_review_queue_scope.py \
  tests/test_proposal_evidence_comparison_history_batch_health_scope.py \
  tests/test_proposal_evidence_comparison_history_scope.py \
  tests/test_proposal_evidence_comparison_scope.py \
  tests/test_proposal_packet_scope.py \
  tests/test_proposal_review_coverage_scope.py \
  tests/test_proposal_review_diagnostics_scope.py \
  tests/test_proposal_review_dossier_batch_scope.py \
  tests/test_proposal_review_dossier_scope.py \
  tests/test_proposal_review_quality_scope.py \
  tests/test_proposal_review_scope.py \
  tests/test_proposal_review_summary_scope.py -q
```

---

### Task 5: Verification, Review, Commit, Push

- [ ] Run focused integrated tests:

```bash
.venv/bin/python -m pytest \
  tests/test_paper_autonomous_allocation_proposal_db_history_prefix_load.py \
  tests/test_paper_autonomous_allocation_proposal_db_history_health_load.py \
  tests/test_paper_autonomous_allocation_proposal_db_history_health_trend.py \
  tests/test_paper_autonomous_allocation_proposal_db_history_health_trend_scope.py \
  tests/test_paper_autonomous_allocation_proposal_db_history_health_trend_load.py \
  tests/test_cli_paper_autonomous_allocation_proposal_db_history_health_trend.py \
  tests/test_cli_paper_autonomous_allocation_proposal_db_history_health_trend_scope.py \
  tests/test_docs_paper_autonomous_allocation_proposal_scope.py \
  tests/test_init.py \
  tests/test_analytics_history_scope.py \
  tests/test_analytics_scope.py \
  tests/test_forecast_evidence_scope.py \
  tests/test_manual_review_queue_scope.py \
  tests/test_proposal_evidence_comparison_history_batch_health_scope.py \
  tests/test_proposal_evidence_comparison_history_scope.py \
  tests/test_proposal_evidence_comparison_scope.py \
  tests/test_proposal_packet_scope.py \
  tests/test_proposal_review_coverage_scope.py \
  tests/test_proposal_review_diagnostics_scope.py \
  tests/test_proposal_review_dossier_batch_scope.py \
  tests/test_proposal_review_dossier_scope.py \
  tests/test_proposal_review_quality_scope.py \
  tests/test_proposal_review_scope.py \
  tests/test_proposal_review_summary_scope.py -q
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
opencode run "Read-only review only. DO NOT modify, create, delete, stage, commit, or push ANY file. Review the current git diff for the paper-autonomous-allocation-proposal-db-history-health-trend node. Check Phase 1 boundaries, read-only DB behavior, CLI redaction, no live/auth/order/account surfaces, package exports and scope tests, docs boundary wording, trend semantics, Decimal-only behavior, and test adequacy. Report Critical/Important/Minor findings with file/line references. If no Critical/Important findings, say so clearly." -m zhipuai-coding-plan/glm-5.2 --variant max
```

If OpenCode cannot be invoked after a real attempt, pause and re-check the local review tooling before proceeding; do not silently switch review routes.

Fix all Critical and Important findings before commit.

- [ ] Update `.superpowers/sdd/progress.md` with the completed node summary if that file exists; otherwise note the skipped progress update in the handoff.
- [ ] Stage only intended tracked implementation/docs/tests/plan files. Do not stage `.superpowers/reviews/`.
- [ ] Commit with:

```bash
git commit -m "feat: add allocation proposal DB history health trend"
```

- [ ] Push only when the active implementation agent is Codex and the user has explicitly authorized node pushes in this session.

```bash
git push origin main
```
