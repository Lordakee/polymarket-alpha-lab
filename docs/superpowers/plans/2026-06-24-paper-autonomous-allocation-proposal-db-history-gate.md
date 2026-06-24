# Paper Autonomous Allocation Proposal DB History Gate Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a paper-only/report-only/read-only gate over persisted paper autonomous allocation proposal DB history.

**Architecture:** Mirror the existing `paper-research-packet-operator-flow-db-history-gate` pattern. A pure reducer consumes one already-built `PaperAutonomousAllocationProposalDbHistoryReport` and emits a deterministic gate report; a tiny loader composes the existing allocation-proposal DB-history loader with the gate reducer; a new env-only CLI command reads the final allocation proposal DB and prints aggregate gate fields without writing anything.

**Tech Stack:** Python 3.12, argparse CLI, frozen dataclasses, `Decimal` fields preserved from allocation history summaries, existing `paper_autonomous_allocation_proposal_db_history` reducer/load modules, psycopg read-only autocommit connection, pytest, CodeGraph, and OpenCode plan/code review using `zhipuai-coding-plan/glm-5.2` with variant `max`.

## Global Constraints

- Preserve Phase 1 boundary: no live trading, no automatic live investing, no auth, no key handling, no wallet handling, no account handling, no account reads, no order instruction, no order construction, no order signing, no order submission, no order cancellation, no order replacement, no execution authorization, no approval workflow, no live-execution signal, no exchange mutation, no investment ranking, and no financial advice.
- The new command is `paper-autonomous-allocation-proposal-db-history-gate --limit 25`.
- The new command accepts only `--limit`; it must reject `--dsn`, `--table`, `--persist`, `--fast`, `--live`, `--auth`, `--wallet`, `--private-key`, `--api-key`, `--account`, `--order`, `--trade`, `--execute`, `--submit`, and `--approve`.
- All DB targets come from `POLYMARKET_ALPHA_LAB_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_*` env config.
- The node reads only persisted final allocation proposal reports through the allocation proposal DB-history readback. It must not read upstream screening/queue tables, repair or create missing upstream reports, or write any reports.
- The default, persist, and DB-history allocation proposal commands remain unchanged except for shared type aliases or helper wiring needed by the new command.
- The DB-history gate command must validate `--limit` before env reads, runner calls, DB connects, or client construction.
- The DB-history gate command must require allocation proposal DB enabled and DSN present before runner or DB connect.
- The read path must use `psycopg.connect(dsn, autocommit=True)`, call the gate loader once, close once, and never commit or rollback.
- Operator output must be aggregate-only: no DSN, table name, schema tail, payload JSON, report hash, market question, market slug, account, wallet, key, or order material.
- Use existing loader function `load_paper_autonomous_allocation_proposal_db_history_report`; do not add a migration, writer, env config, or second table.
- Use `.venv/bin/python -m pytest`, not bare `pytest`.
- Do not use fast mode.

---

## File Structure

- Create `src/polymarket_alpha_lab/paper_autonomous_allocation_proposal_db_history_gate.py`: pure gate reducer, config/report dataclasses, deterministic gate status/reason-code summaries.
- Create `src/polymarket_alpha_lab/paper_autonomous_allocation_proposal_db_history_gate_load.py`: read-only loader composition that consumes a DB-API connection and calls the existing allocation proposal DB-history loader.
- Modify `src/polymarket_alpha_lab/cli.py`: add runner type alias, subparser, command branch, helper, summary printer, and redacted error path.
- Modify `src/polymarket_alpha_lab/paper_autonomous_allocation_proposal_store.py` and `src/polymarket_alpha_lab/supabase_paper_autonomous_allocation_proposal_config.py`: allow optional schema-qualified allocation proposal report table names so schema-tail redaction paths can be exercised without changing the read-only gate behavior.
- Modify `src/polymarket_alpha_lab/__init__.py`: export public gate reducer types and builder.
- Modify `README.md` and `docs/paper-autonomous-allocation-proposal.md`: document the new read-only gate command and keep boundary wording negative.
- Add tests:
  - `tests/test_paper_autonomous_allocation_proposal_db_history_gate.py`
  - `tests/test_paper_autonomous_allocation_proposal_db_history_gate_load.py`
  - `tests/test_cli_paper_autonomous_allocation_proposal_db_history_gate.py`
  - `tests/test_cli_paper_autonomous_allocation_proposal_db_history_gate_scope.py`
  - `tests/test_paper_autonomous_allocation_proposal_db_history_gate_scope.py`
  - Modify `tests/test_docs_paper_autonomous_allocation_proposal_scope.py`
  - Modify `tests/test_paper_autonomous_allocation_proposal_store.py`
  - Modify `tests/test_supabase_paper_autonomous_allocation_proposal_config.py`
  - Modify `tests/test_init.py`
  - Modify existing proposal/export scope tests that maintain `EXPECTED_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_EXPORTS`.

---

### Task 1: Pure Allocation Proposal DB-History Gate Reducer

**Files:**
- Create: `src/polymarket_alpha_lab/paper_autonomous_allocation_proposal_db_history_gate.py`
- Test: `tests/test_paper_autonomous_allocation_proposal_db_history_gate.py`
- Test: `tests/test_paper_autonomous_allocation_proposal_db_history_gate_scope.py`
- Modify: `src/polymarket_alpha_lab/__init__.py`
- Modify: `tests/test_init.py`
- Modify: existing scope tests containing `EXPECTED_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_EXPORTS`

**Interfaces:**
- Consumes:
  - `PaperAutonomousAllocationProposalDbHistoryReport`
  - `PaperAutonomousAllocationProposalDbHistoryReasonCodeRow`
  - `PaperAutonomousAllocationProposalDbHistoryStatusRow`
- Produces:
  - `DEFAULT_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_GATE_CONFIG_VERSION = "paper-autonomous-allocation-proposal-db-history-gate-v0"`
  - `PaperAutonomousAllocationProposalDbHistoryGateConfig`
  - `PaperAutonomousAllocationProposalDbHistoryGateReasonCodeCount`
  - `PaperAutonomousAllocationProposalDbHistoryGateReport`
  - `build_paper_autonomous_allocation_proposal_db_history_gate_report(history_report, *, config, generated_at)`

- [ ] **Step 1: Write failing reducer tests**

Create `tests/test_paper_autonomous_allocation_proposal_db_history_gate.py` with helpers that build exact `PaperAutonomousAllocationProposalDbHistoryReport` values:

```python
from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from importlib import import_module
import inspect

import pytest

from polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history import (
    PaperAutonomousAllocationProposalDbHistoryReasonCodeRow,
    PaperAutonomousAllocationProposalDbHistoryReport,
    PaperAutonomousAllocationProposalDbHistoryStatusRow,
)


GENERATED_AT = datetime(2026, 6, 24, 18, 0, tzinfo=UTC)
LATEST_AT = datetime(2026, 6, 24, 17, 30, tzinfo=UTC)
PROPOSAL_STATUSES = ("pass", "watch", "blocked")


def _api():
    return import_module(
        "polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_gate",
    )


def _config(**overrides):
    values = {
        "config_version": "paper-autonomous-allocation-proposal-db-history-gate-v0",
        "min_history_report_count": 3,
        "max_latest_age_seconds": 86_400,
        "max_consecutive_latest_watch_count": 0,
        "max_consecutive_latest_blocked_count": 0,
        "max_duplicate_generated_at_count": 0,
    }
    values.update(overrides)
    return _api().PaperAutonomousAllocationProposalDbHistoryGateConfig(**values)


def _source_reason(history_status: str, latest_proposal_status: str) -> str:
    if history_status == "blocked":
        return "blocked_allocation_proposal_report_threshold_exceeded"
    if history_status == "watch":
        return "watch_allocation_proposal_report_threshold_exceeded"
    if latest_proposal_status == "blocked":
        return "blocked_allocation_proposal_report_threshold_exceeded"
    if latest_proposal_status == "watch":
        return "watch_allocation_proposal_report_threshold_exceeded"
    return "paper_autonomous_allocation_proposal_db_history_passed"


def _history_report(
    *,
    generated_at: datetime = GENERATED_AT,
    history_status: str = "pass",
    report_count: int = 3,
    latest_report_generated_at: datetime | None = LATEST_AT,
    latest_proposal_status: str | None = "pass",
    duplicate_generated_at_count: int = 0,
    consecutive_latest_pass_count: int = 3,
    consecutive_latest_watch_count: int = 0,
    consecutive_latest_blocked_count: int = 0,
    reason_codes: tuple[str, ...] | None = None,
) -> PaperAutonomousAllocationProposalDbHistoryReport:
    if report_count == 0:
        return PaperAutonomousAllocationProposalDbHistoryReport(
            generated_at=generated_at,
            config_version="paper-autonomous-allocation-proposal-db-history-v0",
            history_status=history_status,
            report_count=0,
            first_report_generated_at=None,
            latest_report_generated_at=None,
            latest_proposal_status=None,
            latest_screening_gate_status=None,
            latest_queue_risk_status=None,
            latest_allocation_input_count=None,
            latest_allocation_row_count=None,
            latest_allocated_count=None,
            latest_total_allocated_paper_notional=None,
            proposal_status_rows=tuple(
                PaperAutonomousAllocationProposalDbHistoryStatusRow(status, 0)
                for status in PROPOSAL_STATUSES
            ),
            duplicate_generated_at_count=0,
            consecutive_latest_pass_count=0,
            consecutive_latest_watch_count=0,
            consecutive_latest_blocked_count=0,
            latest_reason_codes=(),
            reason_code_rows=(),
            reason_codes=(
                reason_codes
                if reason_codes is not None
                else ("insufficient_paper_autonomous_allocation_proposal_history",)
            ),
        )

    if latest_proposal_status is None:
        raise AssertionError("test helper requires latest_proposal_status")
    status_counts = {
        "pass": report_count,
        "watch": 0,
        "blocked": 0,
    }
    if latest_proposal_status == "watch":
        status_counts = {
            "pass": report_count - consecutive_latest_watch_count,
            "watch": consecutive_latest_watch_count,
            "blocked": 0,
        }
    elif latest_proposal_status == "blocked":
        status_counts = {
            "pass": report_count - consecutive_latest_blocked_count,
            "watch": 0,
            "blocked": consecutive_latest_blocked_count,
        }

    source_reason = _source_reason(history_status, latest_proposal_status)
    normalized_reason_codes = (
        reason_codes if reason_codes is not None else (source_reason,)
    )
    latest_reason_codes = (
        ("paper_autonomous_allocation_proposal_passed",)
        if latest_proposal_status == "pass"
        else (f"allocation_proposal_{latest_proposal_status}",)
    )

    return PaperAutonomousAllocationProposalDbHistoryReport(
        generated_at=generated_at,
        config_version="paper-autonomous-allocation-proposal-db-history-v0",
        history_status=history_status,
        report_count=report_count,
        first_report_generated_at=latest_report_generated_at - timedelta(hours=2),
        latest_report_generated_at=latest_report_generated_at,
        latest_proposal_status=latest_proposal_status,
        latest_screening_gate_status="pass",
        latest_queue_risk_status="pass",
        latest_allocation_input_count=2,
        latest_allocation_row_count=2,
        latest_allocated_count=1,
        latest_total_allocated_paper_notional=Decimal("25.000000"),
        proposal_status_rows=tuple(
            PaperAutonomousAllocationProposalDbHistoryStatusRow(
                status,
                status_counts[status],
            )
            for status in PROPOSAL_STATUSES
        ),
        duplicate_generated_at_count=duplicate_generated_at_count,
        consecutive_latest_pass_count=consecutive_latest_pass_count,
        consecutive_latest_watch_count=consecutive_latest_watch_count,
        consecutive_latest_blocked_count=consecutive_latest_blocked_count,
        latest_reason_codes=latest_reason_codes,
        reason_code_rows=tuple(
            PaperAutonomousAllocationProposalDbHistoryReasonCodeRow(
                reason_code,
                report_count,
            )
            for reason_code in normalized_reason_codes
        ),
        reason_codes=normalized_reason_codes,
    )
```

Also include this builder helper because later tests call `_gate_report(...)` directly:

```python
def _gate_report(
    history_report: PaperAutonomousAllocationProposalDbHistoryReport,
    **config_overrides,
):
    return _api().build_paper_autonomous_allocation_proposal_db_history_gate_report(
        history_report,
        config=_config(**config_overrides),
        generated_at=GENERATED_AT,
    )
```

Required test cases:

```python
def test_allocation_proposal_db_history_gate_passes_clean_recent_history():
    api = _api()
    source = _history_report()

    report = api.build_paper_autonomous_allocation_proposal_db_history_gate_report(
        source,
        config=_config(),
        generated_at=GENERATED_AT,
    )

    assert type(report) is api.PaperAutonomousAllocationProposalDbHistoryGateReport
    assert report.config_version == (
        "paper-autonomous-allocation-proposal-db-history-gate-v0"
    )
    assert report.gate_status == "pass"
    assert report.recommended_next_step == (
        "allow_paper_autonomous_allocation_proposal_history_review"
    )
    assert report.source_report_count == 3
    assert report.source_history_status == "pass"
    assert report.latest_proposal_status == "pass"
    assert report.latest_screening_gate_status == "pass"
    assert report.latest_queue_risk_status == "pass"
    assert report.latest_allocation_input_count == 2
    assert report.latest_allocation_row_count == 2
    assert report.latest_allocated_count == 1
    assert report.latest_total_allocated_paper_notional == Decimal("25.000000")
    assert report.latest_source_generated_at == LATEST_AT
    assert report.latest_source_age_seconds == 1_800
    assert report.reason_code_counts == (
        api.PaperAutonomousAllocationProposalDbHistoryGateReasonCodeCount(
            "paper_autonomous_allocation_proposal_db_history_gate_passed",
            1,
        ),
    )
    assert report.reason_codes == (
        "paper_autonomous_allocation_proposal_db_history_gate_passed",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
```

Also cover:

```python
@pytest.mark.parametrize(
    ("source", "expected_reason"),
    (
        (
            _history_report(history_status="blocked", reason_codes=("z_source_blocked",)),
            "source_allocation_proposal_db_history_blocked",
        ),
        (
            _history_report(report_count=2, consecutive_latest_pass_count=2),
            "insufficient_allocation_proposal_db_history",
        ),
        (
            _history_report(
                latest_proposal_status="blocked",
                consecutive_latest_pass_count=0,
                consecutive_latest_blocked_count=1,
                reason_codes=("z_latest_blocked",),
            ),
            "latest_allocation_proposal_blocked",
        ),
    ),
)
def test_allocation_proposal_db_history_gate_blocks_for_blocked_inputs(source, expected_reason):
    report = _gate_report(source)
    assert report.gate_status == "blocked"
    assert report.recommended_next_step == (
        "block_paper_autonomous_allocation_proposal_history_review"
    )
    assert expected_reason in report.reason_codes
```

```python
@pytest.mark.parametrize(
    ("source", "expected_reason"),
    (
        (
            _history_report(history_status="watch", reason_codes=("z_source_watch",)),
            "source_allocation_proposal_db_history_watch",
        ),
        (
            _history_report(
                latest_proposal_status="watch",
                consecutive_latest_pass_count=0,
                consecutive_latest_watch_count=1,
                reason_codes=("z_latest_watch",),
            ),
            "latest_allocation_proposal_watch",
        ),
        (
            _history_report(duplicate_generated_at_count=1),
            "duplicate_allocation_proposal_generated_at_threshold_exceeded",
        ),
    ),
)
def test_allocation_proposal_db_history_gate_watches_for_watch_inputs(source, expected_reason):
    report = _gate_report(source)
    assert report.gate_status == "watch"
    assert report.recommended_next_step == (
        "throttle_paper_autonomous_allocation_proposal_history_review"
    )
    assert expected_reason in report.reason_codes
```

```python
def test_allocation_proposal_db_history_gate_watches_stale_latest_timestamp():
    source = _history_report(
        latest_report_generated_at=GENERATED_AT - timedelta(seconds=86_401),
    )
    report = _gate_report(source)
    assert report.gate_status == "watch"
    assert report.latest_source_age_seconds == 86_401
    assert report.reason_codes == ("stale_allocation_proposal_db_history",)
```

```python
def test_allocation_proposal_db_history_gate_enforces_consecutive_thresholds():
    watch_source = _history_report(
        latest_proposal_status="watch",
        consecutive_latest_pass_count=0,
        consecutive_latest_watch_count=2,
        reason_codes=("z_latest_watch",),
    )
    blocked_source = _history_report(
        latest_proposal_status="blocked",
        consecutive_latest_pass_count=0,
        consecutive_latest_blocked_count=2,
        reason_codes=("z_latest_blocked",),
    )

    watch_report = _gate_report(
        watch_source,
        max_consecutive_latest_watch_count=1,
    )
    blocked_report = _gate_report(
        blocked_source,
        max_consecutive_latest_blocked_count=1,
    )

    assert watch_report.gate_status == "watch"
    assert "latest_allocation_proposal_watch" in watch_report.reason_codes
    assert (
        "consecutive_allocation_proposal_watch_threshold_exceeded"
        in watch_report.reason_codes
    )
    assert blocked_report.gate_status == "blocked"
    assert "latest_allocation_proposal_blocked" in blocked_report.reason_codes
    assert (
        "consecutive_allocation_proposal_blocked_threshold_exceeded"
        in blocked_report.reason_codes
    )
```

```python
def test_allocation_proposal_db_history_gate_missing_latest_timestamp_blocks():
    source = _history_report(report_count=0)
    report = _gate_report(source, min_history_report_count=0)
    assert report.gate_status == "blocked"
    assert report.latest_source_generated_at is None
    assert report.latest_source_age_seconds is None
    assert "missing_latest_allocation_proposal_history_timestamp" in report.reason_codes
```

Run:

```bash
.venv/bin/python -m pytest tests/test_paper_autonomous_allocation_proposal_db_history_gate.py -q
```

Expected before implementation: module import failure.

- [ ] **Step 2: Implement minimal pure gate reducer**

Create `src/polymarket_alpha_lab/paper_autonomous_allocation_proposal_db_history_gate.py` by adapting the operator-flow gate pattern to allocation-proposal history fields.

Use exact constants:

```python
DEFAULT_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_GATE_CONFIG_VERSION = (
    "paper-autonomous-allocation-proposal-db-history-gate-v0"
)

PROPOSAL_STATUSES = ("pass", "watch", "blocked")
NEXT_STEP_BY_STATUS = {
    "pass": "allow_paper_autonomous_allocation_proposal_history_review",
    "watch": "throttle_paper_autonomous_allocation_proposal_history_review",
    "blocked": "block_paper_autonomous_allocation_proposal_history_review",
}
PASS_REASON_CODE = "paper_autonomous_allocation_proposal_db_history_gate_passed"
BLOCKED_REASON_CODES = frozenset(
    (
        "insufficient_allocation_proposal_db_history",
        "source_allocation_proposal_db_history_blocked",
        "latest_allocation_proposal_blocked",
        "consecutive_allocation_proposal_blocked_threshold_exceeded",
        "missing_latest_allocation_proposal_history_timestamp",
    ),
)
WATCH_REASON_CODES = frozenset(
    (
        "source_allocation_proposal_db_history_watch",
        "latest_allocation_proposal_watch",
        "consecutive_allocation_proposal_watch_threshold_exceeded",
        "duplicate_allocation_proposal_generated_at_threshold_exceeded",
        "stale_allocation_proposal_db_history",
    ),
)
```

Config dataclass:

```python
@dataclass(frozen=True)
class PaperAutonomousAllocationProposalDbHistoryGateConfig:
    config_version: str = (
        DEFAULT_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_GATE_CONFIG_VERSION
    )
    min_history_report_count: int = 3
    max_latest_age_seconds: int = 86400
    max_consecutive_latest_watch_count: int = 0
    max_consecutive_latest_blocked_count: int = 0
    max_duplicate_generated_at_count: int = 0
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
```

Report dataclass fields:

```python
generated_at: datetime
config_version: str
source_config_version: str
source_generated_at: datetime
gate_status: str
recommended_next_step: str
reason_code_counts: tuple[PaperAutonomousAllocationProposalDbHistoryGateReasonCodeCount, ...]
source_report_count: int
latest_source_generated_at: datetime | None
latest_source_age_seconds: int | None
source_history_status: str
latest_proposal_status: str | None
latest_screening_gate_status: str | None
latest_queue_risk_status: str | None
latest_allocation_input_count: int | None
latest_allocation_row_count: int | None
latest_allocated_count: int | None
latest_total_allocated_paper_notional: Decimal | None
duplicate_generated_at_count: int
consecutive_latest_pass_count: int
consecutive_latest_watch_count: int
consecutive_latest_blocked_count: int
reason_codes: tuple[str, ...]
paper_only: bool = True
report_only: bool = True
readonly: bool = True
```

Because the report adds allocation-specific fields that do not exist on the operator-flow gate, implement explicit validation for them: `latest_allocation_input_count`, `latest_allocation_row_count`, and `latest_allocated_count` must be optional nonnegative ints; `latest_total_allocated_paper_notional` must be an optional finite `Decimal`. Port `_require_optional_decimal` and `_require_optional_nonnegative_int` style checks from `paper_autonomous_allocation_proposal_db_history.py`.

Implementation must also preserve the operator-flow gate reducer discipline: reject non-exact `PaperAutonomousAllocationProposalDbHistoryReport`, non-exact `PaperAutonomousAllocationProposalDbHistoryGateConfig`, and `datetime` subclasses; normalize all aware datetimes to UTC; compute `latest_source_age_seconds` from normalized generated/source timestamps; construct `reason_code_counts` directly from the normalized `reason_codes`; and validate hard flags on config, source history, rows, and the emitted report.

Gate reason logic:

```python
if history_report.report_count < config.min_history_report_count:
    reason_codes.append("insufficient_allocation_proposal_db_history")
if history_report.history_status == "blocked":
    reason_codes.append("source_allocation_proposal_db_history_blocked")
if history_report.latest_proposal_status == "blocked":
    reason_codes.append("latest_allocation_proposal_blocked")
if history_report.consecutive_latest_blocked_count > config.max_consecutive_latest_blocked_count:
    reason_codes.append("consecutive_allocation_proposal_blocked_threshold_exceeded")
if history_report.latest_report_generated_at is None:
    reason_codes.append("missing_latest_allocation_proposal_history_timestamp")

if history_report.history_status == "watch":
    reason_codes.append("source_allocation_proposal_db_history_watch")
if history_report.latest_proposal_status == "watch":
    reason_codes.append("latest_allocation_proposal_watch")
if history_report.consecutive_latest_watch_count > config.max_consecutive_latest_watch_count:
    reason_codes.append("consecutive_allocation_proposal_watch_threshold_exceeded")
if history_report.duplicate_generated_at_count > config.max_duplicate_generated_at_count:
    reason_codes.append("duplicate_allocation_proposal_generated_at_threshold_exceeded")
if latest_source_age_seconds is not None and latest_source_age_seconds > config.max_latest_age_seconds:
    reason_codes.append("stale_allocation_proposal_db_history")
if not reason_codes:
    reason_codes.append(PASS_REASON_CODE)
return tuple(sorted(set(reason_codes)))
```

Gate reason counts are presence counts over the emitted gate reasons, so each generated row has `report_count=1` in this node. Build them from the already sorted `reason_codes` tuple so `tuple(row.reason_code for row in reason_code_counts) == reason_codes` remains deterministic. If a future node introduces true repeated reason counts, update both the sorting contract and validation together.

- [ ] **Step 3: Add validation and purity coverage**

In `tests/test_paper_autonomous_allocation_proposal_db_history_gate.py`, add tests matching the operator-flow gate coverage:

- `test_allocation_proposal_db_history_gate_reason_code_counts_are_deterministic_and_positive`: build a source with blocked history, latest blocked status, duplicate timestamp count, insufficient count, and exceeded blocked streak; assert `reason_code_counts` follow the sorted `reason_codes` order, every row has `report_count == 1`, `reason_codes` equals the tuple of row reason codes, and the pass reason is absent.
- `test_allocation_proposal_db_history_gate_dataclasses_are_frozen_and_validate_hard_flags`: instantiate config, reason-count row, and report; assert `FrozenInstanceError` on field assignment and `ValueError` when replacing `paper_only=False`, `report_only=False`, or `readonly=False`.
- `test_allocation_proposal_db_history_gate_config_rejects_invalid_thresholds`: parametrize invalid `config_version`, `min_history_report_count=-1`, `max_latest_age_seconds=-1`, `max_consecutive_latest_watch_count=-1`, `max_consecutive_latest_blocked_count=-1`, and `max_duplicate_generated_at_count=-1`.
- `test_allocation_proposal_db_history_gate_rejects_wrong_types_subclasses_and_corruption`: reject a non-history source, a source subclass, a config subclass, and a `datetime` subclass; also reject direct report corruption of `gate_status`, `recommended_next_step`, and duplicate/non-row `reason_code_counts`.
- `test_allocation_proposal_db_history_gate_normalizes_aware_datetimes`: use a UTC-04:00 source/generated time pair and assert normalized UTC `generated_at`, `latest_source_generated_at`, and `latest_source_age_seconds`.

Create `tests/test_paper_autonomous_allocation_proposal_db_history_gate_scope.py` and assert the reducer source does not contain:

```python
(
    "psycopg",
    "supabase",
    "os.environ",
    "polymarketpublicclient",
    "requests",
    "httpx",
    "wallet",
    "private_key",
    "relayer",
    "account",
    "signing",
    "exchange",
    "live_trading",
    "order",
)
```

- [ ] **Step 4: Export public API and update package scope allowlists**

Modify `src/polymarket_alpha_lab/__init__.py` and `tests/test_init.py` to import/export/assert the same package-root surface style as the existing operator-flow DB-history gate. The module itself exports its default constant, but the package root exports only these four public gate symbols:

```python
PaperAutonomousAllocationProposalDbHistoryGateConfig
PaperAutonomousAllocationProposalDbHistoryGateReasonCodeCount
PaperAutonomousAllocationProposalDbHistoryGateReport
build_paper_autonomous_allocation_proposal_db_history_gate_report
```

Modify every scope test with `EXPECTED_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_EXPORTS` to include the four new package-root gate symbols. Do not add the default gate constant to those package-root allowlists. Use:

```bash
rg -l "EXPECTED_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_EXPORTS" tests
```

Then inspect each modified file to ensure only allowlist entries changed.

- [ ] **Step 5: Verify Task 1**

Run:

```bash
.venv/bin/python -m pytest \
  tests/test_paper_autonomous_allocation_proposal_db_history_gate.py \
  tests/test_paper_autonomous_allocation_proposal_db_history_gate_scope.py \
  tests/test_init.py -q
```

Expected: all selected tests pass.

---

### Task 2: DB-History Gate Loader

**Files:**
- Create: `src/polymarket_alpha_lab/paper_autonomous_allocation_proposal_db_history_gate_load.py`
- Test: `tests/test_paper_autonomous_allocation_proposal_db_history_gate_load.py`

**Interfaces:**
- Consumes:
  - `load_paper_autonomous_allocation_proposal_db_history_report(connection, limit=limit, table_name=table_name, config=history_config, generated_at=generated_at)`
  - `build_paper_autonomous_allocation_proposal_db_history_gate_report(history_report, config=gate_config, generated_at=generated_at)`
- Produces:

```python
def load_paper_autonomous_allocation_proposal_db_history_gate_report(
    connection: object,
    *,
    limit: int | None,
    table_name: str,
    history_config: PaperAutonomousAllocationProposalDbHistoryConfig,
    gate_config: PaperAutonomousAllocationProposalDbHistoryGateConfig,
    generated_at: datetime,
) -> PaperAutonomousAllocationProposalDbHistoryGateReport:
```

- [ ] **Step 1: Write failing loader tests**

Create `tests/test_paper_autonomous_allocation_proposal_db_history_gate_load.py`:

```python
from __future__ import annotations

from datetime import UTC, datetime

import pytest

from polymarket_alpha_lab import (
    paper_autonomous_allocation_proposal_db_history_gate_load as module_under_test,
)
from polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_gate_load import (
    load_paper_autonomous_allocation_proposal_db_history_gate_report,
)


GENERATED_AT = datetime(2026, 6, 24, 9, 0, tzinfo=UTC)


class PaperAutonomousAllocationProposalDbHistoryConfig:
    pass


class PaperAutonomousAllocationProposalDbHistoryGateConfig:
    pass


def test_loader_builds_history_then_gate(monkeypatch: pytest.MonkeyPatch) -> None:
    connection = object()
    history_config = PaperAutonomousAllocationProposalDbHistoryConfig()
    gate_config = PaperAutonomousAllocationProposalDbHistoryGateConfig()
    history_report = object()
    gate_report = object()
    history_calls = []
    gate_calls = []

    monkeypatch.setattr(
        module_under_test,
        "PaperAutonomousAllocationProposalDbHistoryConfig",
        PaperAutonomousAllocationProposalDbHistoryConfig,
    )
    monkeypatch.setattr(
        module_under_test,
        "PaperAutonomousAllocationProposalDbHistoryGateConfig",
        PaperAutonomousAllocationProposalDbHistoryGateConfig,
    )

    def fake_load_history(
        received_connection: object,
        *,
        limit: int | None,
        table_name: str,
        config: object,
        generated_at: datetime,
    ) -> object:
        history_calls.append(
            (received_connection, limit, table_name, config, generated_at),
        )
        return history_report

    def fake_build_gate(
        received_history_report: object,
        *,
        config: object,
        generated_at: datetime,
    ) -> object:
        gate_calls.append((received_history_report, config, generated_at))
        return gate_report

    monkeypatch.setattr(
        module_under_test,
        "load_paper_autonomous_allocation_proposal_db_history_report",
        fake_load_history,
    )
    monkeypatch.setattr(
        module_under_test,
        "build_paper_autonomous_allocation_proposal_db_history_gate_report",
        fake_build_gate,
    )

    result = load_paper_autonomous_allocation_proposal_db_history_gate_report(
        connection,
        limit=7,
        table_name="paper_autonomous_allocation_proposal_reports",
        history_config=history_config,
        gate_config=gate_config,
        generated_at=GENERATED_AT,
    )

    assert result is gate_report
    assert history_calls == [
        (
            connection,
            7,
            "paper_autonomous_allocation_proposal_reports",
            history_config,
            GENERATED_AT,
        ),
    ]
    assert gate_calls == [(history_report, gate_config, GENERATED_AT)]
```

Also assert exact type validation before read:

```python
def test_loader_rejects_non_exact_configs_before_history_read(monkeypatch):
    monkeypatch.setattr(module_under_test, "PaperAutonomousAllocationProposalDbHistoryConfig", PaperAutonomousAllocationProposalDbHistoryConfig)
    monkeypatch.setattr(module_under_test, "PaperAutonomousAllocationProposalDbHistoryGateConfig", PaperAutonomousAllocationProposalDbHistoryGateConfig)

    def fail_load(*args, **kwargs):
        raise AssertionError("history loader must not run before config validation")

    monkeypatch.setattr(module_under_test, "load_paper_autonomous_allocation_proposal_db_history_report", fail_load)

    with pytest.raises(ValueError, match="history_config must be"):
        load_paper_autonomous_allocation_proposal_db_history_gate_report(
            object(),
            limit=7,
            table_name="paper_autonomous_allocation_proposal_reports",
            history_config=object(),
            gate_config=PaperAutonomousAllocationProposalDbHistoryGateConfig(),
            generated_at=GENERATED_AT,
        )

    with pytest.raises(ValueError, match="gate_config must be"):
        load_paper_autonomous_allocation_proposal_db_history_gate_report(
            object(),
            limit=7,
            table_name="paper_autonomous_allocation_proposal_reports",
            history_config=PaperAutonomousAllocationProposalDbHistoryConfig(),
            gate_config=object(),
            generated_at=GENERATED_AT,
        )
```

Run:

```bash
.venv/bin/python -m pytest tests/test_paper_autonomous_allocation_proposal_db_history_gate_load.py -q
```

Expected before implementation: module import failure.

- [ ] **Step 2: Implement loader**

Create `src/polymarket_alpha_lab/paper_autonomous_allocation_proposal_db_history_gate_load.py`:

```python
"""Read-only loader composition for the allocation proposal DB-history gate."""

from __future__ import annotations

from datetime import datetime

from polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history import (
    PaperAutonomousAllocationProposalDbHistoryConfig,
)
from polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_gate import (
    PaperAutonomousAllocationProposalDbHistoryGateConfig,
    PaperAutonomousAllocationProposalDbHistoryGateReport,
    build_paper_autonomous_allocation_proposal_db_history_gate_report,
)
from polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_load import (
    load_paper_autonomous_allocation_proposal_db_history_report,
)

__all__ = ("load_paper_autonomous_allocation_proposal_db_history_gate_report",)


def load_paper_autonomous_allocation_proposal_db_history_gate_report(
    connection: object,
    *,
    limit: int | None,
    table_name: str,
    history_config: PaperAutonomousAllocationProposalDbHistoryConfig,
    gate_config: PaperAutonomousAllocationProposalDbHistoryGateConfig,
    generated_at: datetime,
) -> PaperAutonomousAllocationProposalDbHistoryGateReport:
    if type(history_config) is not PaperAutonomousAllocationProposalDbHistoryConfig:
        raise ValueError(
            "history_config must be a PaperAutonomousAllocationProposalDbHistoryConfig",
        )
    if type(gate_config) is not PaperAutonomousAllocationProposalDbHistoryGateConfig:
        raise ValueError(
            "gate_config must be a PaperAutonomousAllocationProposalDbHistoryGateConfig",
        )

    history_report = load_paper_autonomous_allocation_proposal_db_history_report(
        connection,
        limit=limit,
        table_name=table_name,
        config=history_config,
        generated_at=generated_at,
    )
    return build_paper_autonomous_allocation_proposal_db_history_gate_report(
        history_report,
        config=gate_config,
        generated_at=generated_at,
    )
```

- [ ] **Step 3: Verify Task 2**

Run:

```bash
.venv/bin/python -m pytest \
  tests/test_paper_autonomous_allocation_proposal_db_history_gate.py \
  tests/test_paper_autonomous_allocation_proposal_db_history_gate_load.py -q
```

Expected: all selected tests pass.

---

### Task 3: CLI Command And Read-Only DB Path

**Files:**
- Modify: `src/polymarket_alpha_lab/cli.py`
- Test: `tests/test_cli_paper_autonomous_allocation_proposal_db_history_gate.py`
- Test: `tests/test_cli_paper_autonomous_allocation_proposal_db_history_gate_scope.py`

**Interfaces:**
- Consumes: `from_paper_autonomous_allocation_proposal_db_env`, `PaperAutonomousAllocationProposalDbHistoryConfig`, `PaperAutonomousAllocationProposalDbHistoryGateConfig`, and `load_paper_autonomous_allocation_proposal_db_history_gate_report`.
- Produces:
  - `paper-autonomous-allocation-proposal-db-history-gate` subparser with only `--limit`
  - `PaperAutonomousAllocationProposalDbHistoryGateRunner = Callable[..., object]`
  - `_run_paper_autonomous_allocation_proposal_db_history_gate(dsn, table_name, limit, runner)`
  - `_print_paper_autonomous_allocation_proposal_db_history_gate_summary(report)`

- [ ] **Step 1: Write failing CLI tests**

Create `tests/test_cli_paper_autonomous_allocation_proposal_db_history_gate.py` by adapting `tests/test_cli_paper_research_packet_operator_flow_db_history_gate.py` to allocation proposal env/config names.

Required constants:

```python
COMMAND = "paper-autonomous-allocation-proposal-db-history-gate"
HISTORY_CONFIG_VERSION = "paper-autonomous-allocation-proposal-db-history-v0"
GATE_CONFIG_VERSION = "paper-autonomous-allocation-proposal-db-history-gate-v0"
HISTORY_MODULE = "polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history"
GATE_MODULE = "polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_gate"
GATE_LOADER_MODULE = (
    "polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_gate_load"
)
```

Required tests:

```python
test_allocation_proposal_db_history_gate_cli_requires_enabled_db_config
test_allocation_proposal_db_history_gate_cli_rejects_non_positive_limit_before_env_runner_or_connect
test_allocation_proposal_db_history_gate_helper_rejects_invalid_limit_before_runner_or_connect
test_allocation_proposal_db_history_gate_cli_uses_injected_runner_and_prints_summary
test_allocation_proposal_db_history_gate_helper_default_load_path_uses_autocommit_and_closes_only
test_allocation_proposal_db_history_gate_helper_raises_on_missing_psycopg
test_allocation_proposal_db_history_gate_helper_uses_shared_redaction_helper
test_allocation_proposal_db_history_gate_cli_runner_failure_redacts_dsn_schema_table_tail_and_payloads
test_allocation_proposal_db_history_gate_cli_rejects_db_persist_fast_live_auth_wallet_account_order_and_execution_flags
```

Expected summary lines:

```text
paper-autonomous-allocation-proposal-db-history-gate: gate_status=watch recommended_next_step=throttle_paper_autonomous_allocation_proposal_history_review source_report_count=3 source_history_status=watch latest_proposal_status=watch latest_screening_gate_status=pass latest_queue_risk_status=pass latest_allocation_input_count=2 latest_allocation_row_count=2 latest_allocated_count=1 latest_total_allocated_paper_notional=25.000000 duplicate_generated_at_count=0 latest_source_age_seconds=3600
reason_code_counts: latest_allocation_proposal_watch=1 source_allocation_proposal_db_history_watch=1
```

For this injected-runner summary test, build the fake `PaperAutonomousAllocationProposalDbHistoryGateReport` directly (or set thresholds consistently) so it contains exactly the two reason rows shown above and does not accidentally include `consecutive_allocation_proposal_watch_threshold_exceeded`.

Run:

```bash
.venv/bin/python -m pytest tests/test_cli_paper_autonomous_allocation_proposal_db_history_gate.py -q
```

Expected before implementation: parser/runner missing failures.

- [ ] **Step 1b: Add CLI scope coverage**

Create `tests/test_cli_paper_autonomous_allocation_proposal_db_history_gate_scope.py` by adapting `tests/test_cli_paper_research_packet_operator_flow_db_history_gate_scope.py` and the current allocation DB-history CLI scope constraints. Cover these concrete test names:

- `test_allocation_proposal_db_history_gate_parser_accepts_only_limit`
- `test_allocation_proposal_db_history_gate_helper_uses_only_allocation_history_gate_loader_and_psycopg`
- `test_allocation_proposal_db_history_gate_summary_is_aggregate_only`

The parser test must assert the command exposes only `--limit`. The helper-scope test must assert the helper constructs `PaperAutonomousAllocationProposalDbHistoryConfig`, `PaperAutonomousAllocationProposalDbHistoryGateConfig`, imports `load_paper_autonomous_allocation_proposal_db_history_gate_report`, connects with `autocommit=True`, closes once, and does not reference commit/rollback/cursor/write operations. The summary-scope test must assert no DSN/table/payload/hash/question/market slug/account/wallet/key/order material appears in the summary printer source; aggregate `latest_total_allocated_paper_notional` is allowed because it is already exposed by the preceding aggregate history command.

- [ ] **Step 2: Add parser and main dependency injection**

In `cli.py`, add:

```python
PaperAutonomousAllocationProposalDbHistoryGateRunner = Callable[..., object]
```

Add a `main(...)` parameter:

```python
paper_autonomous_allocation_proposal_db_history_gate_runner: (
    PaperAutonomousAllocationProposalDbHistoryGateRunner | None
) = None,
```

Add subparser:

```python
paper_autonomous_allocation_proposal_db_history_gate = subparsers.add_parser(
    "paper-autonomous-allocation-proposal-db-history-gate",
)
paper_autonomous_allocation_proposal_db_history_gate.add_argument(
    "--limit",
    type=int,
    default=25,
    dest="limit",
)
```

- [ ] **Step 3: Add command branch**

Add branch before the existing allocation proposal command group:

```python
if args.command == "paper-autonomous-allocation-proposal-db-history-gate":
    command_name = "paper-autonomous-allocation-proposal-db-history-gate"
    try:
        if isinstance(args.limit, bool) or type(args.limit) is not int or args.limit < 1:
            raise ValueError(f"{command_name} limit must be positive")
        allocation_proposal_db_config = (
            from_paper_autonomous_allocation_proposal_db_env()
        )
        if not allocation_proposal_db_config.enabled:
            raise ValueError(
                f"{command_name} requires autonomous allocation proposal DB "
                "to be enabled",
            )
        dsn = allocation_proposal_db_config.dsn
        if dsn is None:
            raise ValueError(
                f"{command_name} requires an autonomous allocation proposal DB DSN",
            )
        report = _run_paper_autonomous_allocation_proposal_db_history_gate(
            dsn=dsn,
            table_name=allocation_proposal_db_config.table_name,
            limit=args.limit,
            runner=paper_autonomous_allocation_proposal_db_history_gate_runner,
        )
        _print_paper_autonomous_allocation_proposal_db_history_gate_summary(report)
        return 0
    except Exception as exc:
        print(f"{command_name} failed: {exc}", file=sys.stderr)
        return 1
```

Wrap runner/loader failures with `_redacted_paper_research_packet_db_history_error(...)` in the helper and/or command branch as in the existing operator-flow gate pattern.

- [ ] **Step 4: Add read-only helper**

Add `_run_paper_autonomous_allocation_proposal_db_history_gate`:

```python
def _run_paper_autonomous_allocation_proposal_db_history_gate(
    *,
    dsn: str,
    table_name: str,
    limit: int,
    runner: PaperAutonomousAllocationProposalDbHistoryGateRunner | None,
) -> object:
    command_name = "paper-autonomous-allocation-proposal-db-history-gate"
    if isinstance(limit, bool) or type(limit) is not int or limit < 1:
        raise ValueError(f"{command_name} limit must be positive")
    generated_at = datetime.now(UTC)

    from polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history import (
        PaperAutonomousAllocationProposalDbHistoryConfig,
    )
    from polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_gate import (
        PaperAutonomousAllocationProposalDbHistoryGateConfig,
    )

    history_config = PaperAutonomousAllocationProposalDbHistoryConfig()
    gate_config = PaperAutonomousAllocationProposalDbHistoryGateConfig()
    if runner is not None:
        try:
            return runner(
                dsn=dsn,
                table_name=table_name,
                limit=limit,
                history_config=history_config,
                gate_config=gate_config,
                generated_at=generated_at,
            )
        except Exception as exc:
            raise _redacted_paper_research_packet_db_history_error(
                exc,
                dsn=dsn,
                table_name=table_name,
            ) from None

    from polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_gate_load import (
        load_paper_autonomous_allocation_proposal_db_history_gate_report,
    )

    try:
        import psycopg
    except ModuleNotFoundError as exc:
        if exc.name != "psycopg":
            raise
        raise RuntimeError(
            "psycopg is required to use the paper autonomous allocation proposal "
            "DB history gate read adapter; install the postgres extra.",
        ) from exc
    try:
        connection = psycopg.connect(dsn, autocommit=True)
    except Exception:
        raise RuntimeError(
            "failed to connect to the paper autonomous allocation proposal database",
        ) from None
    try:
        return load_paper_autonomous_allocation_proposal_db_history_gate_report(
            connection,
            limit=limit,
            table_name=table_name,
            history_config=history_config,
            gate_config=gate_config,
            generated_at=generated_at,
        )
    except Exception as exc:
        raise _redacted_paper_research_packet_db_history_error(
            exc,
            dsn=dsn,
            table_name=table_name,
        ) from None
    finally:
        try:
            connection.close()
        except Exception:
            pass
```

- [ ] **Step 5: Add summary printer**

Add `_print_paper_autonomous_allocation_proposal_db_history_gate_summary(report)` near related paper autonomous printers:

```python
def _print_paper_autonomous_allocation_proposal_db_history_gate_summary(
    report: object,
) -> None:
    print(
        "paper-autonomous-allocation-proposal-db-history-gate: "
        f"gate_status={report.gate_status} "
        f"recommended_next_step={report.recommended_next_step} "
        f"source_report_count={report.source_report_count} "
        f"source_history_status={report.source_history_status} "
        f"latest_proposal_status={_none_or_value(report.latest_proposal_status)} "
        "latest_screening_gate_status="
        f"{_none_or_value(report.latest_screening_gate_status)} "
        f"latest_queue_risk_status={_none_or_value(report.latest_queue_risk_status)} "
        "latest_allocation_input_count="
        f"{_none_or_value(report.latest_allocation_input_count)} "
        "latest_allocation_row_count="
        f"{_none_or_value(report.latest_allocation_row_count)} "
        f"latest_allocated_count={_none_or_value(report.latest_allocated_count)} "
        "latest_total_allocated_paper_notional="
        f"{_none_or_value(report.latest_total_allocated_paper_notional)} "
        f"duplicate_generated_at_count={report.duplicate_generated_at_count} "
        f"latest_source_age_seconds={_none_or_value(report.latest_source_age_seconds)}",
    )
    reason_counts = " ".join(
        f"{row.reason_code}={row.report_count}"
        for row in report.reason_code_counts
    )
    print(f"reason_code_counts: {reason_counts or 'none'}")
```

- [ ] **Step 6: Verify Task 3**

Run:

```bash
.venv/bin/python -m pytest tests/test_cli_paper_autonomous_allocation_proposal_db_history_gate.py -q
```

Expected: all selected tests pass.

---

### Task 4: Docs And Boundary Tests

**Files:**
- Modify: `README.md`
- Modify: `docs/paper-autonomous-allocation-proposal.md`
- Modify: `tests/test_docs_paper_autonomous_allocation_proposal_scope.py`

**Interfaces:**
- Produces operator-facing documentation for the new read-only DB-history gate command.

- [ ] **Step 1: Extend docs scope tests**

In `tests/test_docs_paper_autonomous_allocation_proposal_scope.py`, add required phrases:

```python
"paper-autonomous-allocation-proposal-db-history-gate --limit 25"
"reads only persisted final allocation proposal reports through the DB history readback"
"does not write reports"
"does not read upstream screening/queue tables"
"gate status is not permission to trade"
"not an approval workflow"
"prints aggregate gate status, recommended next step, source history status, latest aggregate allocation counts, duplicate timestamp count, latest source age, and reason-code counts"
```

Extend README ordering so it asserts:

```python
allocation_command_start < persist_command_start < db_history_command_start < db_history_gate_command_start < next_section_start
```

- [ ] **Step 2: Update docs**

Add a short "DB History Gate" subsection after the DB History Readback subsection in both README and `docs/paper-autonomous-allocation-proposal.md`:

```bash
.venv/bin/polymarket-alpha-lab paper-autonomous-allocation-proposal-db-history-gate --limit 25
```

Required wording:

- env-only, read-only, paper-only/report-only/readonly, no-write
- accepts only `--limit`
- reads the final allocation proposal DB configured by env
- reads only persisted final allocation proposal reports through the DB history readback
- does not write reports
- does not read upstream screening/queue tables
- does not place orders, approve execution, read accounts, or mutate exchange state
- gate status is not permission to trade
- not financial advice, not investment ranking, not an approval workflow
- prints aggregate gate status, recommended next step, source history status, latest aggregate allocation counts, duplicate timestamp count, latest source age, and reason-code counts

Do not include sample DSNs, real table names beyond env variable names already present, payload JSON, market questions, or market slugs.

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
  tests/test_paper_autonomous_allocation_proposal_db_history_gate.py \
  tests/test_paper_autonomous_allocation_proposal_db_history_gate_load.py \
  tests/test_cli_paper_autonomous_allocation_proposal_db_history_gate.py \
  tests/test_paper_autonomous_allocation_proposal_db_history_gate_scope.py \
  tests/test_paper_autonomous_allocation_proposal_store.py \
  tests/test_supabase_paper_autonomous_allocation_proposal_config.py \
  tests/test_docs_paper_autonomous_allocation_proposal_scope.py \
  tests/test_init.py -q
```

- [ ] **Step 2: Run full verification**

Run:

```bash
.venv/bin/python -m pytest -q
.venv/bin/python -m compileall -q src tests
git diff --check
rg -n "ghp_[A-Za-z0-9_]{20,}|sk-[A-Za-z0-9]{20,}|xox[baprs]-[A-Za-z0-9-]{20,}|AKIA[0-9A-Z]{16}|-----BEGIN (RSA |OPENSSH |EC |DSA )?PRIVATE KEY-----" README.md docs src tests
codegraph sync
codegraph status .
```

- [ ] **Step 3: Submit implementation to OpenCode review**

Run from repo root:

```bash
opencode run -m zhipuai-coding-plan/glm-5.2 --variant max \
  "Read-only review only. DO NOT modify/create/delete ANY file; output ONLY verdict + findings. Review the current git diff for the paper-autonomous-allocation-proposal-db-history-gate node. Check Phase 1 boundaries, read-only DB behavior, CLI redaction, no live/auth/order/account surfaces, package exports and scope tests, docs boundary wording, and test adequacy. Report Critical/Important/Minor findings with file/line references. If no Critical/Important findings, say so clearly." \
  > .superpowers/reviews/opencode-allocation-proposal-db-history-gate-review.md 2>&1
```

Fix any Critical/Important findings and rerun focused/full verification and review.

- [ ] **Step 4: Prepare next plan before push**

Before committing this node, create the next implementation plan. The expected next node is a read-only paper allocation proposal history health/trend node, unless implementation findings show a higher-priority gap. Submit that plan to OpenCode with `zhipuai-coding-plan/glm-5.2` and variant `max`.

- [ ] **Step 5: Commit and push after Codex gates**

This plan is for Codex as the active implementation agent. OpenCode is the read-only review gate and must not stage, commit, or push. The OMO/Sisyphus remote-pin rule in `AGENTS.md` applies only to opencode/Sisyphus sessions; Codex follows the `Codex Node Push Policy`, so push only after the focused commit, focused tests, full tests, `git diff --check`, compile verification, CodeGraph sync/status, secret scan, and OpenCode post-node review all pass.

Stage only production, test, docs, and plan files. Do not stage `.superpowers/`. Before staging, re-run `rg -l "EXPECTED_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_EXPORTS" tests` and ensure every returned scope test is represented in the staging list below.

```bash
git add README.md \
  docs/paper-autonomous-allocation-proposal.md \
  docs/superpowers/plans/2026-06-24-paper-autonomous-allocation-proposal-db-history-gate.md \
  src/polymarket_alpha_lab/__init__.py \
  src/polymarket_alpha_lab/cli.py \
  src/polymarket_alpha_lab/paper_autonomous_allocation_proposal_store.py \
  src/polymarket_alpha_lab/paper_autonomous_allocation_proposal_db_history_gate.py \
  src/polymarket_alpha_lab/paper_autonomous_allocation_proposal_db_history_gate_load.py \
  src/polymarket_alpha_lab/supabase_paper_autonomous_allocation_proposal_config.py \
  tests/test_cli_paper_autonomous_allocation_proposal_db_history_gate.py \
  tests/test_cli_paper_autonomous_allocation_proposal_db_history_gate_scope.py \
  tests/test_docs_paper_autonomous_allocation_proposal_scope.py \
  tests/test_init.py \
  tests/test_paper_autonomous_allocation_proposal_store.py \
  tests/test_paper_autonomous_allocation_proposal_db_history_gate.py \
  tests/test_paper_autonomous_allocation_proposal_db_history_gate_load.py \
  tests/test_paper_autonomous_allocation_proposal_db_history_gate_scope.py \
  tests/test_supabase_paper_autonomous_allocation_proposal_config.py \
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
  tests/test_proposal_review_summary_scope.py
git commit -m "feat: gate allocation proposal DB history"
git push origin main
```

- [ ] **Step 6: Handoff Summary**

Write a concise Handoff Summary with:

- repo state
- commit SHA and push status
- verified commands
- review tool and verdict
- uncommitted files
- recommended next node

---

## Plan Self-Review

- Spec coverage: the plan covers pure reducer, loader composition, CLI, docs, package exports, scope allowlists, verification, review, next-plan preparation, commit, push, and handoff. It preserves the paper-only/report-only/read-only boundary and does not introduce live trading/auth/order/account surfaces.
- Placeholder scan: no task contains placeholder markers or unbounded "add tests" language without concrete test names and assertions.
- Type consistency: produced names use the `PaperAutonomousAllocationProposalDbHistoryGate*` prefix and match the planned CLI command `paper-autonomous-allocation-proposal-db-history-gate`.
- Scope decision: this plan intentionally does not add a writer/persistence path for the gate. The node is a read-only operator gate over the persisted allocation proposal DB history, matching the existing operator-flow DB-history gate pattern.
