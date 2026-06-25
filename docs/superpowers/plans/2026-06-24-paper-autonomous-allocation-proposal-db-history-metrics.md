# Paper Autonomous Allocation Proposal DB History Metrics Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a paper-only/report-only/read-only metrics node over persisted paper autonomous allocation proposal reports so the system can quantify allocation quality, concentration, utilization, and churn before any live execution work.

**Architecture:** Build a pure reducer over recovered `PaperAutonomousAllocationProposalReport` values loaded from the existing persisted allocation proposal DB. The reducer operates before the existing DB-history reducer compresses away allocation rows, so it can compute per-window and latest-snapshot metrics from `allocation_report.rows`. A tiny loader composes the existing proposal store readback with the reducer, and an env-only CLI command prints aggregate-only risk/performance metrics.

**Tech Stack:** Python 3.12, argparse CLI, frozen dataclasses, `Decimal` arithmetic only, existing allocation proposal report/store modules, psycopg read-only autocommit connection at the CLI boundary only, pytest, CodeGraph, and local OpenCode reviews using `zhipuai-coding-plan/glm-5.2` with variant `max`.

## Global Constraints

- Preserve Phase 1 boundary: no live trading, no automatic live investing, no auth, no key handling, no wallet handling, no account handling, no account reads, no order instruction, no order construction, no order signing, no order submission, no order cancellation, no order replacement, no execution authorization, no approval workflow, no live-execution signal, no exchange mutation, no investment ranking, and no financial advice.
- The planned command is `paper-autonomous-allocation-proposal-db-history-metrics --limit 25`.
- The command accepts only `--limit`; it must reject `--dsn`, `--table`, `--persist`, `--fast`, `--live`, `--auth`, `--wallet`, `--private-key`, `--api-key`, `--account`, `--order`, `--trade`, `--execute`, `--submit`, and `--approve`.
- All DB targets come from `POLYMARKET_ALPHA_LAB_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_*` env config.
- The node reads only persisted final allocation proposal reports through existing allocation proposal store readback. It must not read upstream screening/queue tables, repair missing reports, create missing reports, write reports, persist metrics reports, or call any market data source.
- Metrics are research diagnostics over paper artifacts only. They are not financial advice, not investment ranking, not trade recommendations, not order instructions, not approvals, and not live-execution signals.
- The reducer must be pure: no `psycopg`, Supabase clients, `os.environ`, CLI imports, network clients, filesystem reads or writes, `open(`, or printing.
- The loader must not connect, close, commit, rollback, insert, update, delete, create tables, create indexes, or mutate supplied connections.
- The CLI default DB path may connect with `psycopg.connect(dsn, autocommit=True)`, call the loader once, close once, and never commit or rollback.
- Validate `--limit` before env reads, runner calls, DB connects, or client construction.
- Require allocation proposal DB enabled and DSN present before runner or DB connect.
- Operator output must be aggregate-only: no DSN, table name, schema tail, payload JSON, report hash, market question, market slug, account, wallet, key, or order material.
- Use `Decimal("0.000001")` quantization for ratios and notional outputs. Do not introduce float arithmetic.
- Treat absent edge data honestly: do not fabricate expected value when `net_probability_edge` is missing. Report edge coverage and expected-value fields only over rows where edge is present.
- The v0 loader intentionally aggregates across all persisted proposal statuses and config versions selected by the DB table and `--limit`; it does not filter by proposal status, proposal config version, screening gate status, or allocation config version.
- Use `.venv/bin/python -m pytest`, not bare `pytest`.
- Do not use fast mode.
- Completed implementation must pass focused tests, full tests, `compileall`, `git diff --check`, tracked secret scan, CodeGraph sync/status, and OpenCode post-node review before commit/push.
- This is a Codex implementation node. Follow `AGENTS.md` Codex Node Push Policy after the post-node review gate passes; the OMO/Sisyphus remote-pin workflow is explicitly marked opencode-only and does not govern Codex node completion.

---

## File Structure

- Create `src/polymarket_alpha_lab/paper_autonomous_allocation_proposal_db_history_metrics.py`: pure metrics reducer, metric rows, config/report dataclasses.
- Create `src/polymarket_alpha_lab/paper_autonomous_allocation_proposal_db_history_metrics_load.py`: read-only loader composition from the existing proposal store to the metrics reducer.
- Modify `src/polymarket_alpha_lab/cli.py`: add runner alias, subparser, command branch, helper, summary printer, and redacted error path.
- Modify `src/polymarket_alpha_lab/__init__.py`: export public metrics reducer types and builder only.
- Modify `README.md` and `docs/paper-autonomous-allocation-proposal.md`: document the read-only metrics command and negative boundary language.
- Modify root-export allowlist scope tests that define `EXPECTED_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_EXPORTS`:
  - `tests/test_analytics_history_scope.py`
  - `tests/test_analytics_scope.py`
  - `tests/test_forecast_evidence_scope.py`
  - `tests/test_manual_review_queue_scope.py`
  - `tests/test_proposal_packet_scope.py`
  - `tests/test_proposal_review_scope.py`
  - `tests/test_proposal_review_summary_scope.py`
  - `tests/test_proposal_review_quality_scope.py`
  - `tests/test_proposal_review_diagnostics_scope.py`
  - `tests/test_proposal_review_coverage_scope.py`
  - `tests/test_proposal_review_dossier_scope.py`
  - `tests/test_proposal_review_dossier_batch_scope.py`
  - `tests/test_proposal_evidence_comparison_scope.py`
  - `tests/test_proposal_evidence_comparison_history_scope.py`
  - `tests/test_proposal_evidence_comparison_history_batch_health_scope.py`
- Add tests:
  - `tests/test_paper_autonomous_allocation_proposal_db_history_metrics.py`
  - `tests/test_paper_autonomous_allocation_proposal_db_history_metrics_load.py`
  - `tests/test_cli_paper_autonomous_allocation_proposal_db_history_metrics.py`
  - `tests/test_cli_paper_autonomous_allocation_proposal_db_history_metrics_scope.py`
  - `tests/test_paper_autonomous_allocation_proposal_db_history_metrics_scope.py`
- Modify existing docs/export/scope tests that maintain allocation proposal command lists, required doc phrases, public API exports, or forbidden-surface allowlists.

## Parallel Development Lanes

- **Lane A, pure reducer:** Own only `paper_autonomous_allocation_proposal_db_history_metrics.py`, `tests/test_paper_autonomous_allocation_proposal_db_history_metrics.py`, and `tests/test_paper_autonomous_allocation_proposal_db_history_metrics_scope.py`.
- **Lane B, loader:** Own only `paper_autonomous_allocation_proposal_db_history_metrics_load.py` and `tests/test_paper_autonomous_allocation_proposal_db_history_metrics_load.py`.
- **Lane C, CLI:** Own only `cli.py`, `tests/test_cli_paper_autonomous_allocation_proposal_db_history_metrics.py`, and `tests/test_cli_paper_autonomous_allocation_proposal_db_history_metrics_scope.py`.
- **Lane D, docs/exports:** Own `__init__.py`, README/docs, `tests/test_init.py`, `tests/test_docs_paper_autonomous_allocation_proposal_scope.py`, and the root-export allowlist scope tests listed in File Structure.
- **Lane E, verification/review:** Own verification commands, CodeGraph sync/status, secret scan, OpenCode review collection, and final staging audit. This lane must not edit source unless review finds a concrete issue.

Avoid overlapping file edits across lanes. If a lane needs a shared interface change, pause and update this plan before implementation continues.

Freeze this shared reducer interface exactly:

```python
DEFAULT_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_METRICS_CONFIG_VERSION = (
    "paper-autonomous-allocation-proposal-db-history-metrics-v0"
)

build_paper_autonomous_allocation_proposal_db_history_metrics_report(
    proposal_reports: object,
    *,
    config: PaperAutonomousAllocationProposalDbHistoryMetricsConfig,
    generated_at: datetime,
) -> PaperAutonomousAllocationProposalDbHistoryMetricsReport
```

Freeze this shared loader interface exactly:

```python
load_paper_autonomous_allocation_proposal_db_history_metrics_report(
    connection,
    *,
    limit: int | None,
    table_name: str,
    config: PaperAutonomousAllocationProposalDbHistoryMetricsConfig,
    generated_at: datetime,
)
```

Freeze these CLI entry-point names exactly:

```python
PaperAutonomousAllocationProposalDbHistoryMetricsRunner
_run_paper_autonomous_allocation_proposal_db_history_metrics
_print_paper_autonomous_allocation_proposal_db_history_metrics_summary
```

---

### Task 1: Pure Metrics Reducer

**Files:**
- Create: `src/polymarket_alpha_lab/paper_autonomous_allocation_proposal_db_history_metrics.py`
- Test: `tests/test_paper_autonomous_allocation_proposal_db_history_metrics.py`
- Test: `tests/test_paper_autonomous_allocation_proposal_db_history_metrics_scope.py`

**Interfaces:**
- Consumes exact `PaperAutonomousAllocationProposalReport` values.
- Produces:
  - `DEFAULT_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_METRICS_CONFIG_VERSION`
  - `PaperAutonomousAllocationProposalDbHistoryMetricsConfig`
  - `PaperAutonomousAllocationProposalDbHistoryMetricsConcentrationRow`
  - `PaperAutonomousAllocationProposalDbHistoryMetricsCapReasonRow`
  - `PaperAutonomousAllocationProposalDbHistoryMetricsSnapshotSummary`
  - `PaperAutonomousAllocationProposalDbHistoryMetricsReport`
  - `build_paper_autonomous_allocation_proposal_db_history_metrics_report(...)`

- [ ] **Step 1: Write failing reducer tests**

Cover these cases:
- Empty input yields `source_report_count == 0`, empty rows/summaries, and `None` for all first/latest/delta metrics.
- Input reports are sorted chronologically by `(generated_at, input_position)` unless already sorted.
- Direct constructor values are frozen and reject invalid hard flags.
- Config rejects noncanonical `config_version` and bool/non-int threshold values.
- Reducer rejects non-exact config types and non-exact proposal report values.
- Latest snapshot metrics:
  - `latest_proposal_status`
  - `latest_allocation_input_count`
  - `latest_allocation_row_count`
  - `latest_allocated_count`
  - `latest_capped_count`
  - `latest_no_budget_count`
  - `latest_non_recommend_count`
  - `latest_skipped_count`
  - `latest_total_requested_paper_notional`
  - `latest_total_allocated_paper_notional`
  - `latest_remaining_paper_budget`
  - `latest_total_paper_budget`
  - `latest_budget_utilization`
  - `latest_requested_fill_ratio`
  - `latest_allocated_row_share`
  - `latest_capped_row_share`
  - `latest_no_budget_row_share`
  - `latest_non_recommend_row_share`
  - `latest_skipped_row_share`
- First/latest/delta metrics for total requested notional, total allocated notional, budget utilization, requested fill ratio, and allocated count.
- Latest largest concentration rows for `market`, `event`, `theme`, and `correlation_group`, with absent group IDs represented as no row for that group type.
- Concentration share equals grouped allocated notional divided by latest total allocated notional; when total allocated notional is zero, concentration share is `None`.
- Cap reason rows count presence of `market_cap`, `event_cap`, `theme_cap`, `correlation_cap`, `total_budget_cap`, `capped`, and `no_budget` across latest allocation rows.
- Previous-to-latest churn by `(market_slug, side)`:
  - `latest_added_market_side_count`
  - `latest_removed_market_side_count`
  - `latest_persisted_market_side_count`
  - `latest_notional_turnover`
- Edge coverage:
  - `latest_allocated_edge_count`
  - `latest_allocated_edge_share`
  - `latest_expected_edge_notional`
  - `latest_expected_edge_notional_share`
  Only allocated rows with `net_probability_edge is not None` participate in expected-edge notional.
- All Decimal fields are exact `Decimal` values, quantized to `0.000001`, and no float values are accepted.

- [ ] **Step 2: Implement reducer dataclasses**

Use frozen dataclasses:

```python
@dataclass(frozen=True)
class PaperAutonomousAllocationProposalDbHistoryMetricsConfig:
    config_version: str = DEFAULT_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_METRICS_CONFIG_VERSION
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
```

```python
@dataclass(frozen=True)
class PaperAutonomousAllocationProposalDbHistoryMetricsConcentrationRow:
    group_type: str
    group_id: str
    allocated_paper_notional: Decimal
    allocated_paper_notional_share: Decimal | None
    row_count: int
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
```

```python
@dataclass(frozen=True)
class PaperAutonomousAllocationProposalDbHistoryMetricsCapReasonRow:
    reason_code: str
    row_count: int
    allocated_paper_notional: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
```

```python
@dataclass(frozen=True)
class PaperAutonomousAllocationProposalDbHistoryMetricsSnapshotSummary:
    input_position: int
    generated_at: datetime
    proposal_status: str
    allocation_input_count: int
    allocation_row_count: int
    allocated_count: int
    capped_count: int
    no_budget_count: int
    non_recommend_count: int
    skipped_count: int
    total_requested_paper_notional: Decimal
    total_allocated_paper_notional: Decimal
    remaining_paper_budget: Decimal
    total_paper_budget: Decimal
    budget_utilization: Decimal | None
    requested_fill_ratio: Decimal | None
    allocated_row_share: Decimal | None
    capped_row_share: Decimal | None
    no_budget_row_share: Decimal | None
    non_recommend_row_share: Decimal | None
    skipped_row_share: Decimal | None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
```

`PaperAutonomousAllocationProposalDbHistoryMetricsReport` should include:
- `generated_at`, `config_version`, `source_report_count`
- `first_report_generated_at`, `latest_report_generated_at`
- all latest snapshot fields listed in Step 1
- first/latest/delta fields for requested notional, allocated notional, budget utilization, requested fill ratio, and allocated count
- `latest_largest_concentration_rows`
- `latest_cap_reason_rows`
- churn fields listed in Step 1
- edge coverage fields listed in Step 1
- `source_summaries`
- hard flags

- [ ] **Step 3: Implement arithmetic and deterministic sorting**

Rules:
- Use `Decimal("0.000001")` and `Context(prec=64)`.
- Every division, multiplication, addition, subtraction, and absolute notional change must run inside `with localcontext(DECIMAL_CONTEXT)`.
- Top-level report `generated_at` and snapshot summary `generated_at` fields must normalize timezone-aware datetimes to UTC in `__post_init__`, and must reject naive datetimes.
- `_optional_ratio(numerator, denominator)` returns `None` when denominator is `0`, otherwise quantized ratio.
- `_decimal_delta(first, latest)` returns `None` if either side is `None`.
- `latest_proposal_status` is sourced from the latest `PaperAutonomousAllocationProposalReport.proposal_status`.
- Row share denominators:
  - row shares use `allocation_row_count`
  - notional shares use `total_allocated_paper_notional`
  - edge share uses `allocated_count`
- Concentration grouping:
  - `market`: `row.market_slug`
  - `event`: `row.event_id` when not `None`
  - `theme`: `row.theme_id` when not `None`
  - `correlation_group`: `row.correlation_group` when not `None`
- Concentration rows sort by `(group_type, -allocated_paper_notional, group_id)`, but report only the largest row per `group_type`.
- Cap reason rows count only reason codes in this allowlist: `capped`, `no_budget`, `market_cap`, `event_cap`, `theme_cap`, `correlation_cap`, and `total_budget_cap`. They must ignore non-cap row reasons such as `non_recommend`, `skipped`, `nonpositive_edge`, `nonpositive_executable_paper_shares`, and `nonpositive_price`.
- Cap reason rows sort by `(-row_count, reason_code)`.
- Churn keys are `(market_slug, side)` for rows with `allocated_paper_notional > 0`.
- Notional turnover is the sum of absolute allocated-notional changes across the union of previous and latest market-side keys.
- When `source_report_count < 2`, churn counts are `0` and `latest_notional_turnover` is `Decimal("0.000000")`.
- Expected-edge notional is the sum of `allocated_paper_notional * net_probability_edge` for allocated rows where `net_probability_edge is not None`.

- [ ] **Step 4: Add reducer scope tests**

AST/string checks must prove the reducer has no DB/env/network/execution surfaces and no guarded tokens:
- `psycopg`
- `supabase`
- `os.environ`
- `requests`
- `httpx`
- `urllib`
- `subprocess`
- `socket`
- `asyncio`
- `import io`
- `import sys`
- `import logging`
- `import pathlib`
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
.venv/bin/python -m pytest -q \
  tests/test_paper_autonomous_allocation_proposal_db_history_metrics.py \
  tests/test_paper_autonomous_allocation_proposal_db_history_metrics_scope.py
```

---

### Task 2: Read-Only Metrics Loader

**Files:**
- Create: `src/polymarket_alpha_lab/paper_autonomous_allocation_proposal_db_history_metrics_load.py`
- Test: `tests/test_paper_autonomous_allocation_proposal_db_history_metrics_load.py`

**Interfaces:**
- Produces `load_paper_autonomous_allocation_proposal_db_history_metrics_report(connection, *, limit, table_name, config, generated_at)`.
- Calls `load_paper_autonomous_allocation_proposal_reports(connection, limit=limit, table_name=table_name)` exactly once.
- Reverses the store newest-first return value into chronological order before calling the reducer.
- Does not pass filters in this first node; filter support is out of scope.
- The docs must tell operators that v0 aggregates across all persisted proposal statuses and config versions selected by the table and limit.

- [ ] **Step 1: Write failing loader tests**

Cover:
- Passes connection, limit, and table name to `load_paper_autonomous_allocation_proposal_reports`.
- Reverses newest-first loaded reports into chronological reducer input.
- Passes exact config and generated_at to reducer.
- Rejects non-exact config before store read.
- Does not call cursor directly.
- Does not close, commit, rollback, insert, update, delete, create, or write through supplied connection.
- Module imports only `datetime`, proposal store loader, and metrics reducer symbols.

- [ ] **Step 2: Implement the loader**

Implementation shape:

```python
loaded_reports = load_paper_autonomous_allocation_proposal_reports(
    connection,
    limit=limit,
    table_name=table_name,
)
chronological_reports = tuple(reversed(tuple(loaded_reports)))
return build_paper_autonomous_allocation_proposal_db_history_metrics_report(
    chronological_reports,
    config=config,
    generated_at=generated_at,
)
```

Run:

```bash
.venv/bin/python -m pytest -q \
  tests/test_paper_autonomous_allocation_proposal_db_history_metrics_load.py
```

---

### Task 3: CLI Command Wiring

**Files:**
- Modify: `src/polymarket_alpha_lab/cli.py`
- Test: `tests/test_cli_paper_autonomous_allocation_proposal_db_history_metrics.py`
- Test: `tests/test_cli_paper_autonomous_allocation_proposal_db_history_metrics_scope.py`

**Interfaces:**
- Adds CLI command `paper-autonomous-allocation-proposal-db-history-metrics`.
- Adds runner alias `PaperAutonomousAllocationProposalDbHistoryMetricsRunner`.
- Adds helper `_run_paper_autonomous_allocation_proposal_db_history_metrics`.
- Adds summary printer `_print_paper_autonomous_allocation_proposal_db_history_metrics_summary`.

- [ ] **Step 1: Write failing CLI tests**

Cover:
- Disabled allocation proposal DB env fails before runner, connect, or client construction.
- Non-positive limit fails before env read, runner, connect, or client construction.
- Missing DSN fails before runner or connect.
- Runner path receives `dsn`, `table_name`, `limit`, exact `PaperAutonomousAllocationProposalDbHistoryMetricsConfig`, and timezone-aware generated_at.
- Default path imports psycopg lazily, connects with `autocommit=True`, calls loader once, closes connection once.
- `ModuleNotFoundError("psycopg")` returns the standard postgres-extra message.
- Connect or loader failures redact DSN and table/schema-tail values.
- Summary output includes only aggregate fields:
  - `source_report_count`
  - `latest_proposal_status`
  - `latest_budget_utilization`
  - `latest_requested_fill_ratio`
  - `latest_total_allocated_paper_notional`
  - `latest_largest_market_share`
  - `latest_added_market_side_count`
  - `latest_removed_market_side_count`
  - `latest_notional_turnover`
  - `latest_allocated_edge_share`
  - `latest_expected_edge_notional`
- Summary output does not include DSN, table name, schema tail, payload JSON, hash, market slug, market question, wallet, account, key, order, or trade material.
- Parser rejects forbidden flags listed in Global Constraints, including `--fast`.
- `allow_abbrev=False` rejects abbreviated flags such as `--lim`.
- CLI scope tests must explicitly forbid these raw fragments or names outside approved parser/help text: `subprocess`, `socket`, `requests`, `httpx`, `urllib`, `supabase`, `private_key`, `wallet`, `submit_order`, `cancel_order`, `replace_order`, `trade`, and `approve`. The CLI may use argparse, env config helpers, lazy `psycopg`, the metrics reducer config, and the metrics loader.

- [ ] **Step 2: Implement parser and command branch**

Add a subparser near adjacent allocation proposal DB-history commands:

```python
paper_autonomous_allocation_proposal_db_history_metrics = subparsers.add_parser(
    "paper-autonomous-allocation-proposal-db-history-metrics",
    allow_abbrev=False,
)
paper_autonomous_allocation_proposal_db_history_metrics.add_argument(
    "--limit",
    type=int,
    default=25,
)
```

Command branch must mirror DB-history readback:
- validate `limit`
- read `from_paper_autonomous_allocation_proposal_db_env()`
- require enabled and DSN
- call `_run_paper_autonomous_allocation_proposal_db_history_metrics`
- wrap failures through existing redaction helper
- print aggregate summary

- [ ] **Step 3: Implement helper and printer**

Helper must:
- build default `PaperAutonomousAllocationProposalDbHistoryMetricsConfig`
- support injected runner for tests
- lazily import loader and psycopg
- connect autocommit
- close in finally
- never commit/rollback

Printer must compute `latest_largest_market_share` by selecting the `market` row from `report.latest_largest_concentration_rows`; print `none` when absent.

Run:

```bash
.venv/bin/python -m pytest -q \
  tests/test_cli_paper_autonomous_allocation_proposal_db_history_metrics.py \
  tests/test_cli_paper_autonomous_allocation_proposal_db_history_metrics_scope.py
```

---

### Task 4: Public API Exports and Documentation

**Files:**
- Modify: `src/polymarket_alpha_lab/__init__.py`
- Modify: `tests/test_init.py`
- Modify: `README.md`
- Modify: `docs/paper-autonomous-allocation-proposal.md`
- Modify: `tests/test_docs_paper_autonomous_allocation_proposal_scope.py`
- Modify existing scope tests that enumerate allocation proposal command names or public exports.

**Interfaces:**
- Public API exports only reducer types and builder:
  - `PaperAutonomousAllocationProposalDbHistoryMetricsConfig`
  - `PaperAutonomousAllocationProposalDbHistoryMetricsConcentrationRow`
  - `PaperAutonomousAllocationProposalDbHistoryMetricsCapReasonRow`
  - `PaperAutonomousAllocationProposalDbHistoryMetricsSnapshotSummary`
- `PaperAutonomousAllocationProposalDbHistoryMetricsReport`
- `build_paper_autonomous_allocation_proposal_db_history_metrics_report`

Keep loader, runner, CLI helper, and printer names out of package-root exports:
- `PaperAutonomousAllocationProposalDbHistoryMetricsRunner`
- `load_paper_autonomous_allocation_proposal_db_history_metrics_report`
- `_run_paper_autonomous_allocation_proposal_db_history_metrics`
- `_print_paper_autonomous_allocation_proposal_db_history_metrics_summary`

- [ ] **Step 1: Write/update failing export and docs tests**

Update docs scope expectations to require these phrases in both README and docs:
- `paper-autonomous-allocation-proposal-db-history-metrics --limit 25`
- `reads only persisted final allocation proposal reports`
- `computes aggregate paper allocation risk/performance metrics`
- `does not write reports`
- `does not read upstream screening/queue tables`
- `not financial advice`
- `not investment ranking`
- `not automatic live investing`
- `not order instruction`
- `not execution authorization`
- `v0 aggregates across all persisted proposal statuses and config versions`

In `tests/test_docs_paper_autonomous_allocation_proposal_scope.py`, update each relevant tuple explicitly:
- `REQUIRED_PHRASES`
- `REQUIRED_README_PHRASES`
- `REQUIRED_README_PHASE_1_PHRASES`
- the command-name tuple in the test around the existing DB-history command sequence for `paper-autonomous-allocation-proposal-db-history`, `...-gate`, `...-health`, `...-health-trend`, and `...-health-trend-gate`

- [ ] **Step 2: Update exports**

Add imports and `__all__` entries in the existing allocation proposal export section.

Add the same public metrics reducer names to every `EXPECTED_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_EXPORTS` allowlist file listed in File Structure. Do not weaken `FORBIDDEN_PUBLIC_EXPORT_FRAGMENTS`.

- [ ] **Step 3: Update docs**

Add a `DB History Metrics` section after `DB History Gate` and before `DB History Health`.

Required wording:
- The command is env-only, read-only, paper-only/report-only/readonly, and no-write.
- It accepts only `--limit`.
- It reads the final allocation proposal DB configured by env.
- It reads only persisted final allocation proposal reports.
- It computes aggregate paper allocation risk/performance metrics: budget utilization, fill ratio, concentration, churn, cap reasons, edge coverage, and expected edge notional where edge data exists.
- In v0 it aggregates across all persisted proposal statuses and config versions selected by the table and `--limit`.
- It does not write reports and does not read upstream screening/queue tables.
- It does not place orders, approve execution, read accounts, or mutate exchange state.
- It is not financial advice, not investment ranking, not automatic live investing, not order instruction, and not execution authorization.

Run:

```bash
.venv/bin/python -m pytest -q \
  tests/test_init.py \
  tests/test_docs_paper_autonomous_allocation_proposal_scope.py
```

---

### Task 5: Integrated Verification and Review

**Files:**
- No source ownership unless a concrete issue is found.

- [ ] **Step 1: Run focused tests**

```bash
.venv/bin/python -m pytest -q \
  tests/test_paper_autonomous_allocation_proposal_db_history_metrics.py \
  tests/test_paper_autonomous_allocation_proposal_db_history_metrics_scope.py \
  tests/test_paper_autonomous_allocation_proposal_db_history_metrics_load.py \
  tests/test_cli_paper_autonomous_allocation_proposal_db_history_metrics.py \
  tests/test_cli_paper_autonomous_allocation_proposal_db_history_metrics_scope.py \
  tests/test_init.py \
  tests/test_docs_paper_autonomous_allocation_proposal_scope.py
```

- [ ] **Step 2: Run full verification**

```bash
.venv/bin/python -m pytest -q
.venv/bin/python -m compileall -q src/polymarket_alpha_lab
git diff --check
git grep -nE 'ghp_[A-Za-z0-9_]{20,}|(^|[^A-Za-z0-9])sk-[A-Za-z0-9_-]{20,}|(^|[^A-Za-z0-9])eyJ[A-Za-z0-9_-]{30,}|-----BEGIN [A-Z ]*PRIVATE KEY-----' -- . ':!*.pyc' || true
codegraph sync .
git status --short --branch
```

- [ ] **Step 3: OpenCode post-node review**

Run:

```bash
opencode run -m zhipuai-coding-plan/glm-5.2 --variant max "<read-only review prompt>"
```

Prompt must include:
- Plan path.
- Current diff/commit range.
- Read-only instruction: do not modify/create/delete/stage/commit/push.
- Review focus: Phase 1 boundary, read-only data source, Decimal-only metrics, no fabricated EV, CLI redaction, tests/docs consistency, no live/auth/order/account surfaces.

- [ ] **Step 4: Commit, Codex-policy push, and handoff**

If review has no Critical or Important findings:

```bash
git add <intended files only>
git diff --cached --check
git commit -m "Add allocation proposal history metrics node"
git status --short --branch
```

Then apply the `AGENTS.md` Codex Node Push Policy. If the focused commit has a clean worktree except intentionally ignored/untracked local scratch, focused tests pass, full tests pass, `git diff --check` is clean, compile verification passes, CodeGraph is synced, secret scan is clean, and the post-node OpenCode review gate passes, push the completed Codex node:

```bash
git push origin main
git status --short --branch
```

Write a Handoff Summary containing:
- repo status
- commit and push status
- verified commands
- uncommitted/untracked files
- OpenCode review result
- next recommended stage
