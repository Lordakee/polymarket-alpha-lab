# Paper Autonomous Allocation Proposal DB History Metrics Evaluation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) for tracking.

**Goal:** Add a paper-only/report-only/read-only evaluation layer over persisted paper autonomous allocation proposal history metrics so the system can translate raw utilization, fill, concentration, churn, and edge metrics into deterministic pass/watch/blocked status and operator diagnostics before any live execution work.

**Architecture:** Build a pure evaluation reducer that consumes exactly one `PaperAutonomousAllocationProposalDbHistoryMetricsReport` and produces a summary status report over its latest metrics and deltas. A tiny loader composes the existing metrics loader with the evaluation reducer. An env-only CLI command prints aggregate status, diagnostics, and recommended next step only.

**Tech Stack:** Python 3.12, argparse CLI, frozen dataclasses, `Decimal` arithmetic only, existing allocation proposal metrics/loader modules, psycopg read-only autocommit connection at the CLI boundary only, pytest, CodeGraph, and local OpenCode reviews using `zhipuai-coding-plan/glm-5.2` with variant `max`.

## Global Constraints

- Preserve Phase 1 boundary: no live trading, no automatic live investing, no auth, no key handling, no wallet handling, no account handling, no account reads, no order instruction, no order construction, no order signing, no order submission, no order cancellation, no order replacement, no execution authorization, no approval workflow, no live-execution signal, no exchange mutation, no investment ranking, and no financial advice.
- The planned command is `paper-autonomous-allocation-proposal-db-history-metrics-evaluation --limit 25`.
- The command accepts only `--limit`; it must reject `--dsn`, `--table`, `--persist`, `--fast`, `--live`, `--auth`, `--wallet`, `--private-key`, `--api-key`, `--account`, `--order`, `--trade`, `--execute`, `--submit`, and `--approve`.
- All DB targets come from `POLYMARKET_ALPHA_LAB_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_*` env config.
- The node reads only persisted final allocation proposal reports through existing allocation proposal store readback, builds metrics through the existing metrics loader, and evaluates the resulting metrics report. It must not read upstream screening/queue tables, repair missing reports, create missing reports, write reports, persist evaluation reports, or call any market data source.
- The evaluation report is research diagnostics over paper artifacts only. It is not financial advice, not investment ranking, not trade recommendations, not order instructions, not approvals, and not live-execution signals.
- The evaluation reducer must be pure: no `psycopg`, Supabase clients, `os.environ`, CLI imports, network clients, filesystem reads or writes, `open(`, or printing.
- The loader must not connect, close, commit, rollback, insert, update, delete, create tables, create indexes, or mutate supplied connections.
- The CLI default DB path may connect with `psycopg.connect(dsn, autocommit=True)`, call the metrics loader once, close once, and never commit or rollback.
- Validate `--limit` before env reads, runner calls, DB connects, or client construction.
- Require allocation proposal DB enabled and DSN present before runner or DB connect.
- Operator output must be aggregate-only: no DSN, table name, schema tail, payload JSON, report hash, market question, market slug, account, wallet, key, or order material.
- Use `Decimal("0.000001")` quantization for ratios and notional outputs. Do not introduce float arithmetic.
- Treat absent edge or metric data honestly: when a metric input is missing, evaluate only the metrics that exist and report missing inputs as diagnostics, not as failures or synthetic values.
- The v0 evaluation config must expose exactly these thresholds:
  - `min_source_report_count`
  - `max_latest_age_seconds`
  - `max_budget_utilization`
  - `min_requested_fill_ratio`
  - `max_concentration_share`
  - `max_churn_share`
  - `min_edge_coverage`
  - `max_expected_edge_notional_share`
- The v0 evaluation must produce deterministic reason codes drawn from an explicit allowlist, with separate status buckets for `blocked`, `watch`, and `pass`.
- The v0 evaluation must derive `evaluation_status` deterministically from reason codes, in this priority: `blocked` if any blocked reason is present, else `watch` if any watch reason is present, else `pass`.
- The v0 recommended next step mapping must be:
  - `pass`: `review_paper_autonomous_allocation_proposal`
  - `watch`: `hold_paper_autonomous_allocation_proposal`
  - `blocked`: `block_paper_autonomous_allocation_proposal`
- Use `.venv/bin/python -m pytest`, not bare `pytest`.
- Do not use fast mode.
- Completed implementation must pass focused tests, full tests, `compileall`, `git diff --check`, tracked secret scan, CodeGraph sync/status, and OpenCode post-node review before commit/push.
- This is a Codex implementation node. Follow `AGENTS.md` Codex Node Push Policy after the post-node review gate passes.

---

## File Structure

- Create `src/polymarket_alpha_lab/paper_autonomous_allocation_proposal_db_history_metrics_evaluation.py`: pure evaluation reducer, config/report/diagnostic dataclasses.
- Create `src/polymarket_alpha_lab/paper_autonomous_allocation_proposal_db_history_metrics_evaluation_load.py`: read-only loader composition from existing metrics loader to evaluation reducer.
- Modify `src/polymarket_alpha_lab/cli.py`: add runner alias, subparser, command branch, helper, summary printer, and redacted error path.
- Modify `src/polymarket_alpha_lab/__init__.py`: export public evaluation reducer types and builder only.
- Modify `README.md` and `docs/paper-autonomous-allocation-proposal.md`: document the read-only evaluation command and negative boundary language.
- Modify root-export allowlist scope tests that define `EXPECTED_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_EXPORTS`.
- Add tests:
  - `tests/test_paper_autonomous_allocation_proposal_db_history_metrics_evaluation.py`
  - `tests/test_paper_autonomous_allocation_proposal_db_history_metrics_evaluation_scope.py`
  - `tests/test_paper_autonomous_allocation_proposal_db_history_metrics_evaluation_load.py`
  - `tests/test_cli_paper_autonomous_allocation_proposal_db_history_metrics_evaluation.py`
  - `tests/test_cli_paper_autonomous_allocation_proposal_db_history_metrics_evaluation_scope.py`

## Parallel Development Lanes

- **Lane A, pure evaluation reducer:** Own only `paper_autonomous_allocation_proposal_db_history_metrics_evaluation.py`, `tests/test_paper_autonomous_allocation_proposal_db_history_metrics_evaluation.py`, and `tests/test_paper_autonomous_allocation_proposal_db_history_metrics_evaluation_scope.py`.
- **Lane B, loader:** Own only `paper_autonomous_allocation_proposal_db_history_metrics_evaluation_load.py` and `tests/test_paper_autonomous_allocation_proposal_db_history_metrics_evaluation_load.py`.
- **Lane C, CLI:** Own only `cli.py`, `tests/test_cli_paper_autonomous_allocation_proposal_db_history_metrics_evaluation.py`, and `tests/test_cli_paper_autonomous_allocation_proposal_db_history_metrics_evaluation_scope.py`.
- **Lane D, docs/exports:** Own `__init__.py`, README/docs, `tests/test_init.py`, `tests/test_docs_paper_autonomous_allocation_proposal_scope.py`, and the root-export allowlist scope tests listed in File Structure.
- **Lane E, verification/review:** Own verification commands, CodeGraph sync/status, secret scan, OpenCode review collection, and final staging audit. This lane must not edit source unless review finds a concrete issue.

Avoid overlapping file edits across lanes. If a lane needs a shared interface change, pause and update this plan before implementation continues.

Freeze this shared evaluation interface exactly:

```python
DEFAULT_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_METRICS_EVALUATION_CONFIG_VERSION = (
    "paper-autonomous-allocation-proposal-db-history-metrics-evaluation-v0"
)

DEFAULT_DECIMAL_CONTEXT = Context(prec=64)

build_paper_autonomous_allocation_proposal_db_history_metrics_evaluation_report(
    metrics_report: object,
    *,
    config: PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationConfig,
    generated_at: datetime,
) -> PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationReport

PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationReasonCodeCount(
    reason_code: str,
    report_count: int,
)

ALLOWED_REASON_CODES = (
    "missing_paper_autonomous_allocation_proposal_metrics_source_history",
    "stale_paper_autonomous_allocation_proposal_metrics_latest_report",
    "metrics_budget_utilization_watch",
    "metrics_requested_fill_ratio_watch",
    "metrics_concentration_market_watch",
    "metrics_concentration_event_watch",
    "metrics_concentration_theme_watch",
    "metrics_concentration_correlation_group_watch",
    "metrics_churn_share_watch",
    "metrics_edge_coverage_watch",
    "metrics_edge_quality_watch",
    "paper_autonomous_allocation_proposal_metrics_evaluation_passed",
)

Metrics latest_source_age_seconds must be derived deterministically from generated_at minus latest_report_generated_at.
Both values must be timezone-aware UTC, age must be int((generated_at_utc - latest_report_generated_at_utc).total_seconds()), and the reducer must reject negative age.
```

Freeze this shared loader interface exactly (note: the frozen evaluation loader must internally create `PaperAutonomousAllocationProposalDbHistoryMetricsConfig()` and forward the same `generated_at` to the existing metrics loader):

```python
load_paper_autonomous_allocation_proposal_db_history_metrics_evaluation_report(
    connection,
    *,
    limit: int | None,
    table_name: str,
    config: PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationConfig,
    generated_at: datetime,
)
```

Internally this loader must call:
```python
metrics_report = load_paper_autonomous_allocation_proposal_db_history_metrics_report(
    connection,
    limit=limit,
    table_name=table_name,
    config=PaperAutonomousAllocationProposalDbHistoryMetricsConfig(),
    generated_at=generated_at,
)
```

Freeze these CLI entry-point names exactly:

```python
PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationRunner
_run_paper_autonomous_allocation_proposal_db_history_metrics_evaluation
_print_paper_autonomous_allocation_proposal_db_history_metrics_evaluation_summary
```

---

### Task 1: Pure Evaluation Reducer

**Files:**
- Create: `src/polymarket_alpha_lab/paper_autonomous_allocation_proposal_db_history_metrics_evaluation.py`
- Test: `tests/test_paper_autonomous_allocation_proposal_db_history_metrics_evaluation.py`
- Test: `tests/test_paper_autonomous_allocation_proposal_db_history_metrics_evaluation_scope.py`

**Interfaces:**
- Consumes exactly one `PaperAutonomousAllocationProposalDbHistoryMetricsReport`.
- Produces:
  - `DEFAULT_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_METRICS_EVALUATION_CONFIG_VERSION`
  - `PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationConfig`
  - `PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationReasonCodeCount`
  - `PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationDiagnostics`
  - `PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationReport`
  - `build_paper_autonomous_allocation_proposal_db_history_metrics_evaluation_report(...)`

- [ ] **Step 1: Write failing evaluation tests**

Cover these cases:
- Empty/absent metrics input yields `source_report_count == 0`, empty diagnostics, `evaluation_status == "blocked"`, and `recommended_next_step == "block_paper_autonomous_allocation_proposal"`.
- Default config rejects noncanonical `config_version`, booleans, non-numeric values, negative thresholds, and overridable fields that are not numeric or Decimal.
- `build` rejects non-exact config and non-exact metrics report types.
- Pass/watch/blocked status is deterministic based on reason code priority.
- Reason codes are deduplicated, sorted, and drawn from the allowlist only.
- Diagnostics report which thresholds were evaluated and whether the field existed.
- Budget utilization above `max_budget_utilization` triggers `metrics_budget_utilization_watch`.
- Requested fill ratio below `min_requested_fill_ratio` triggers `metrics_requested_fill_ratio_watch`.
- Evaluate each concentration group present in the metrics report independently against `max_concentration_share`, emitting the matching group reason code for every breach. Select the single largest concentration group for diagnostics using the breached set first (if any), then all available groups, breaking ties by descending share and alphabetical group type. `largest_concentration_group_type` must be the canonical metrics group value, not the reason-code string.
- Churn share above `max_churn_share` triggers `metrics_churn_share_watch`, where churn share equals `latest_notional_turnover / latest_total_allocated_paper_notional` when denominator is positive, else `None`.
- Edge coverage below `min_edge_coverage` triggers `metrics_edge_coverage_watch`.
- `generated_at < latest_report_generated_at` must raise before any status assignment.
- When `latest_report_generated_at` is absent, `latest_source_age_seconds` must be `None` and the age-related reason check must be skipped.
- `top_reason_codes` must equal the first `top_reason_code_limit` entries from the deterministic sorted reason codes. Default `top_reason_code_limit` is `6`.
- Expected edge notional share above `max_expected_edge_notional_share` triggers `metrics_edge_quality_watch`.
- Missing `latest_total_allocated_paper_notional` disables notional-dependent checks.
- Missing edge inputs disable edge checks and leave edge diagnostics present but absent-valued.
- All Decimal fields are exact `Decimal` values, quantized to `0.000001`, and no float values are accepted.

- [ ] **Step 2: Implement evaluation dataclasses**

Use frozen dataclasses:

```python
@dataclass(frozen=True)
class PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationConfig:
    config_version: str = DEFAULT_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_METRICS_EVALUATION_CONFIG_VERSION
    min_source_report_count: int = 1
    max_latest_age_seconds: int = 86_400
    max_budget_utilization: Decimal = Decimal("0.900000")
    min_requested_fill_ratio: Decimal = Decimal("0.300000")
    max_concentration_share: Decimal = Decimal("0.600000")
    max_churn_share: Decimal = Decimal("0.600000")
    min_edge_coverage: Decimal = Decimal("0.250000")
    max_expected_edge_notional_share: Decimal = Decimal("0.100000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
```

```python
@dataclass(frozen=True)
class PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationDiagnostics:
    evaluated_min_source_report_count: bool
    evaluated_latest_age: bool
    evaluated_budget_utilization: bool
    evaluated_requested_fill_ratio: bool
    evaluated_concentration: bool
    evaluated_churn: bool
    evaluated_edge_coverage: bool
    evaluated_edge_quality: bool
    source_report_count: int
    latest_source_age_seconds: int | None
    latest_budget_utilization: Decimal | None
    latest_requested_fill_ratio: Decimal | None
    largest_concentration_group_type: str | None
    largest_concentration_share: Decimal | None
    top_reason_codes: tuple[str, ...]
    top_reason_code_limit: int
    churn_share: Decimal | None
    latest_allocated_edge_share: Decimal | None
    latest_expected_edge_notional_share: Decimal | None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
```

```python
@dataclass(frozen=True)
class PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationReport:
    generated_at: datetime
    config_version: str
    evaluation_status: str
    recommended_next_step: str
    source_report_count: int
    latest_report_generated_at: datetime | None
    reason_code_counts: tuple[
        PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    diagnostics: PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationDiagnostics
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
```

`PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationReport` should include:
- `generated_at`, `config_version`, `evaluation_status`, `recommended_next_step`
- `source_report_count`, `latest_report_generated_at`
- `reason_code_counts`, `reason_codes`
- `diagnostics`
- `top_reason_codes`
- hard flags

`top_reason_codes` means the first `top_reason_code_limit` operator-facing reason codes from the deterministic sorted reason-code tuple. Default `top_reason_code_limit` is `6`.

- [ ] **Step 3: Implement deterministic reason/status logic**

Rules:
- Use `Decimal("0.000001")` and `DEFAULT_DECIMAL_CONTEXT = Context(prec=64)`.
- Every comparison involving ratios or shares must run inside `with localcontext(DEFAULT_DECIMAL_CONTEXT)` where arithmetic is needed.
- Top-level report `generated_at` must normalize timezone-aware datetimes to UTC in `__post_init__` and reject naive datetimes.
- Evaluate missing-source case first.
- Evaluate stale latest timestamp second.
- Evaluate the remaining metrics only when the required inputs exist.
- Map `recommended_next_step` exactly to the v0 mapping.
- `reason_code_counts` must be a deterministic tuple sorted by `(-report_count, reason_code)`.

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
  tests/test_paper_autonomous_allocation_proposal_db_history_metrics_evaluation.py \
  tests/test_paper_autonomous_allocation_proposal_db_history_metrics_evaluation_scope.py
```

---

### Task 2: Read-Only Evaluation Loader

**Files:**
- Create: `src/polymarket_alpha_lab/paper_autonomous_allocation_proposal_db_history_metrics_evaluation_load.py`
- Test: `tests/test_paper_autonomous_allocation_proposal_db_history_metrics_evaluation_load.py`

**Interfaces:**
- Produces `load_paper_autonomous_allocation_proposal_db_history_metrics_evaluation_report(connection, *, limit, table_name, config, generated_at)`.
- Calls the frozen metrics loader exactly once with `connection`, `limit`, `table_name`, `config=PaperAutonomousAllocationProposalDbHistoryMetricsConfig()`, and the same `generated_at` forwarded to the evaluation loader.
- Passes the returned metrics report directly into the evaluation reducer.
- The docs must tell operators that v0 evaluates persisted metrics built from the same DB-selected proposal history.

- [ ] **Step 1: Write failing loader tests**

Cover:
- Passes `connection`, `limit`, `table_name`, `PaperAutonomousAllocationProposalDbHistoryMetricsConfig()`, and `generated_at` to the metrics loader exactly once.
- Passes the metrics report, exact config, and timezone-aware generated_at to the evaluation reducer.
- Rejects non-exact evaluation config before metrics loader call.
- Does not call cursor directly.
- Does not close, commit, rollback, insert, update, delete, create, or write through supplied connection.
- Module imports only `datetime`, the metrics config type, the metrics loader, and evaluation reducer symbols.

- [ ] **Step 2: Implement the loader**

Implementation shape:

```python
metrics_report = load_paper_autonomous_allocation_proposal_db_history_metrics_report(
    connection,
    limit=limit,
    table_name=table_name,
    config=PaperAutonomousAllocationProposalDbHistoryMetricsConfig(),
    generated_at=generated_at,
)
return build_paper_autonomous_allocation_proposal_db_history_metrics_evaluation_report(
    metrics_report,
    config=config,
    generated_at=generated_at,
)
```

Run:

```bash
.venv/bin/python -m pytest -q \
  tests/test_paper_autonomous_allocation_proposal_db_history_metrics_evaluation_load.py
```

---

### Task 3: CLI Command Wiring

**Files:**
- Modify: `src/polymarket_alpha_lab/cli.py`
- Test: `tests/test_cli_paper_autonomous_allocation_proposal_db_history_metrics_evaluation.py`
- Test: `tests/test_cli_paper_autonomous_allocation_proposal_db_history_metrics_evaluation_scope.py`

**Interfaces:**
- Adds CLI command `paper-autonomous-allocation-proposal-db-history-metrics-evaluation`.
- Adds runner alias `PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationRunner`.
- Adds helper `_run_paper_autonomous_allocation_proposal_db_history_metrics_evaluation`.
- Adds summary printer `_print_paper_autonomous_allocation_proposal_db_history_metrics_evaluation_summary`.

- [ ] **Step 1: Write failing CLI tests**

Cover:
- Disabled allocation proposal DB env fails before runner, connect, or client construction.
- Non-positive limit fails before env read, runner, connect, or client construction.
- Missing DSN fails before runner or connect.
- Runner path receives `dsn`, `table_name`, `limit`, exact evaluation config, and timezone-aware generated_at.
- Default path imports psycopg lazily, connects with `autocommit=True`, calls loader once, closes connection once.
- `ModuleNotFoundError("psycopg")` returns the standard postgres-extra message.
- Connect or loader failures redact DSN and table/schema-tail values.
- Summary output includes only aggregate fields:
  - `evaluation_status`
  - `recommended_next_step`
  - `source_report_count`
  - `latest_report_generated_at`
  - `top_reason_codes`
  - `top_reason_code_limit`
  - `evaluated_budget_utilization`
  - `evaluated_requested_fill_ratio`
  - `evaluated_concentration`
  - `evaluated_churn`
  - `evaluated_edge_coverage`
  - `evaluated_edge_quality`
- Summary output does not include DSN, table name, schema tail, payload JSON, hash, market slug, market question, wallet, account, key, or trade material.
- Parser rejects forbidden flags listed in Global Constraints, including `--fast`.
- `allow_abbrev=False` rejects abbreviated flags such as `--lim`.
- CLI scope tests must explicitly forbid these raw fragments or names outside approved parser/help text: `subprocess`, `socket`, `requests`, `httpx`, `urllib`, `supabase`, `private_key`, `wallet`, `submit_order`, `cancel_order`, `replace_order`, `trade`, and `approve`.

- [ ] **Step 2: Implement parser and command branch**

Add a subparser adjacent to the allocation proposal DB-history metrics command:

```python
paper_autonomous_allocation_proposal_db_history_metrics_evaluation = subparsers.add_parser(
    "paper-autonomous-allocation-proposal-db-history-metrics-evaluation",
    allow_abbrev=False,
)
paper_autonomous_allocation_proposal_db_history_metrics_evaluation.add_argument(
    "--limit",
    type=int,
    default=25,
)
```

Command branch must mirror DB-history readback:
- validate `limit`
- read `from_paper_autonomous_allocation_proposal_db_env()`
- require enabled and DSN
- call `_run_paper_autonomous_allocation_proposal_db_history_metrics_evaluation`
- wrap failures through existing redaction helper
- print aggregate summary

- [ ] **Step 3: Implement helper and printer**

Helper must:
- build default evaluation config
- support injected runner for tests
- lazily import loader and psycopg
- connect autocommit
- close in finally
- never commit/rollback

Printer must:
- select the largest concentration share from diagnostics
- print `none` when absent

Run:

```bash
.venv/bin/python -m pytest -q \
  tests/test_cli_paper_autonomous_allocation_proposal_db_history_metrics_evaluation.py \
  tests/test_cli_paper_autonomous_allocation_proposal_db_history_metrics_evaluation_scope.py
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
- Public API exports only evaluation reducer types and builder:
  - `PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationConfig`
  - `PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationReasonCodeCount`
  - `PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationDiagnostics`
  - `PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationReport`
  - `build_paper_autonomous_allocation_proposal_db_history_metrics_evaluation_report`

Keep loader, runner, CLI helper, and printer names out of package-root exports:
- `PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationRunner`
- `load_paper_autonomous_allocation_proposal_db_history_metrics_evaluation_report`
- `_run_paper_autonomous_allocation_proposal_db_history_metrics_evaluation`
- `_print_paper_autonomous_allocation_proposal_db_history_metrics_evaluation_summary`

- [ ] **Step 1: Write/update failing export and docs tests**

Update docs scope expectations to require these phrases in both README and docs:
- `paper-autonomous-allocation-proposal-db-history-metrics-evaluation --limit 25`
- `reads only persisted final allocation proposal reports`
- `builds metrics and evaluates aggregate allocation diagnostics`
- `does not write reports`
- `does not read upstream screening/queue tables`
- `not financial advice`
- `not investment ranking`
- `not automatic live investing`
- `not order instruction`
- `not execution authorization`
- `v0 evaluates persisted metrics built from the same DB-selected proposal history`

In `tests/test_docs_paper_autonomous_allocation_proposal_scope.py`, update each relevant tuple explicitly:
- `REQUIRED_PHRASES`
- `REQUIRED_README_PHRASES`
- `REQUIRED_README_PHASE_1_PHRASES`
- the command-name tuple around the existing DB-history metrics command

- [ ] **Step 2: Update exports**

Add imports and `__all__` entries in the existing allocation proposal export section.

Add the same public evaluation reducer names to every `EXPECTED_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_EXPORTS` allowlist file listed in File Structure. Do not weaken `FORBIDDEN_PUBLIC_EXPORT_FRAGMENTS`.

- [ ] **Step 3: Update docs**

Add a `DB History Metrics Evaluation` section after `DB History Metrics` and before `DB History Gate`.

Required wording:
- The command is env-only, read-only, paper-only/report-only/readonly, and no-write.
- It accepts only `--limit`.
- It reads the final allocation proposal DB configured by env.
- It reads only persisted final allocation proposal reports, builds metrics from them, and evaluates the resulting aggregate allocation diagnostics.
- In v0 it evaluates persisted metrics built from the same DB-selected proposal history selected by the table and `--limit`.
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
  tests/test_paper_autonomous_allocation_proposal_db_history_metrics_evaluation.py \
  tests/test_paper_autonomous_allocation_proposal_db_history_metrics_evaluation_scope.py \
  tests/test_paper_autonomous_allocation_proposal_db_history_metrics_evaluation_load.py \
  tests/test_cli_paper_autonomous_allocation_proposal_db_history_metrics_evaluation.py \
  tests/test_cli_paper_autonomous_allocation_proposal_db_history_metrics_evaluation_scope.py \
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
- Review focus: Phase 1 boundary, read-only data source, Decimal-only evaluation, no fabricated thresholds, CLI redaction, tests/docs consistency, no live/auth/order/account surfaces.

- [ ] **Step 4: Commit, Codex-policy push, and handoff**

If review has no Critical or Important findings:

```bash
git add <intended files only>
git diff --cached --check
git commit -m "Add allocation proposal history metrics evaluation node"
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
