# Paper Autonomous Allocation Proposal DB History Health Trend Gate Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a paper-only/report-only/readonly DB-history health-trend gate that converts allocation proposal health-trend observability into an aggregate pass/watch/blocked review gate without live trading, auth, wallets, accounts, orders, persistence, or investment ranking.

**Architecture:** The new reducer consumes exactly one `PaperAutonomousAllocationProposalDbHistoryHealthTrendReport`, derives gate reason codes from trend sample size, latest health status, latest streaks, duplicate timestamps, stale source age, and adverse health deltas, then emits a frozen aggregate gate report. The loader composes the existing read-only health-trend loader with the new gate reducer. The CLI mirrors the existing `paper-autonomous-allocation-proposal-db-history-health-trend` path: env-only DB config, `--limit` only, lazy `psycopg`, close-only cleanup, redacted failures, and aggregate-only output.

**Tech Stack:** Python 3.12 stdlib dataclasses, `datetime.UTC`, `Decimal`, existing `psycopg` optional extra for read-only DB access, existing pytest suite, CodeGraph, local OpenCode review using `zhipuai-coding-plan/glm-5.2` with `--variant max`.

## Global Constraints

- Phase 1 only: no live trading, no automatic live investing, no auth, no key handling, no wallet handling, no account handling, no account reads, no order construction, no order signing, no order submission, no order cancellation, no order replacement, no exchange mutation, no execution authorization, no approval workflow, no financial advice, and no investment ranking.
- The new node must be `paper_only=True`, `report_only=True`, and `readonly=True` on every public config/report/row dataclass.
- The reducer must not import DB, env, CLI, network, Supabase, psycopg, filesystem, print/open, auth, account, wallet, order, execution, approval, trading, or persistence modules.
- The loader must not write, commit, rollback, close, open cursors directly, execute SQL directly, insert, update, delete, upsert, persist, or import Supabase/env/CLI/migration modules.
- The CLI command accepts only `--limit`; it must reject `--dsn`, `--table`, `--persist`, `--fast`, `--live`, `--auth`, `--wallet`, `--private-key`, `--api-key`, `--account`, `--order`, `--trade`, `--execute`, `--submit`, and `--approve`.
- The CLI helper validates `--limit` before reading env, invoking a runner, importing `psycopg`, or connecting.
- Operator output must be aggregate-only: no DSN, table/schema tail, payload JSON, report hash, market slug, question, side, action, recommendation score, allocation rows, ranked list, account identifier, wallet material, or order-like language.
- No persistence for derived health-trend gate reports in this node. Persisting derived reports requires a later explicit DB schema and identity node.
- Use `.venv/bin/python -m pytest`, not bare `pytest`.
- Use CodeGraph before grep/find when locating code in this repo.
- Do not commit `.superpowers/`.
- Review gates for this node use local OpenCode directly, read-only, with `zhipuai-coding-plan/glm-5.2` and `--variant max`; do not route this node's plan or code reviews to Claude Code.
- This is an active Codex implementation node. The opencode/Sisyphus remote-pin workflow does not apply while Codex is active; after verification and OpenCode approval, push the completed focused Codex node to GitHub per `AGENTS.md` Codex Node Push Policy.

---

## File Structure

- Create `src/polymarket_alpha_lab/paper_autonomous_allocation_proposal_db_history_health_trend_gate.py`
  - Pure reducer and public dataclasses.
  - Exports only: default config version, config, reason-code count row, report, builder.
- Create `src/polymarket_alpha_lab/paper_autonomous_allocation_proposal_db_history_health_trend_gate_load.py`
  - Read-only composition: existing trend loader -> new gate reducer.
- Modify `src/polymarket_alpha_lab/cli.py`
  - New runner type, `main(...)` injection parameter, parser, command branch, `_run_*` helper, and summary printer.
- Modify `src/polymarket_alpha_lab/__init__.py`
  - Package-root exports for the public reducer API only.
- Create tests:
  - `tests/test_paper_autonomous_allocation_proposal_db_history_health_trend_gate.py`
  - `tests/test_paper_autonomous_allocation_proposal_db_history_health_trend_gate_scope.py`
  - `tests/test_paper_autonomous_allocation_proposal_db_history_health_trend_gate_load.py`
  - `tests/test_cli_paper_autonomous_allocation_proposal_db_history_health_trend_gate.py`
  - `tests/test_cli_paper_autonomous_allocation_proposal_db_history_health_trend_gate_scope.py`
- Modify docs/tests:
  - `README.md`
  - `docs/paper-autonomous-allocation-proposal.md`
  - `tests/test_docs_paper_autonomous_allocation_proposal_scope.py`
  - `tests/test_init.py`
  - All files matching `rg -l "EXPECTED_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_EXPORTS" tests/*_scope.py`

## Interfaces

Reducer module:

```python
DEFAULT_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_HEALTH_TREND_GATE_CONFIG_VERSION = (
    "paper-autonomous-allocation-proposal-db-history-health-trend-gate-v0"
)

class PaperAutonomousAllocationProposalDbHistoryHealthTrendGateConfig:
    config_version: str = DEFAULT...
    min_source_health_report_count: int = 3
    max_consecutive_latest_watch_count: int = 0
    max_consecutive_latest_blocked_count: int = 0
    max_duplicate_generated_at_count: int = 0
    max_latest_source_age_seconds: int = 86_400
    max_watch_report_count_delta: int = 0
    max_blocked_report_count_delta: int = 0
    max_repeated_reason_code_count: int = 0
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

class PaperAutonomousAllocationProposalDbHistoryHealthTrendGateReasonCodeCount:
    reason_code: str
    report_count: int
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

class PaperAutonomousAllocationProposalDbHistoryHealthTrendGateReport:
    generated_at: datetime
    config_version: str
    source_config_version: str
    source_generated_at: datetime
    gate_status: str
    recommended_next_step: str
    reason_code_counts: tuple[PaperAutonomousAllocationProposalDbHistoryHealthTrendGateReasonCodeCount, ...]
    source_health_report_count: int
    latest_health_status: str | None
    latest_health_generated_at: datetime | None
    latest_source_age_seconds: int | None
    duplicate_generated_at_count: int
    consecutive_latest_watch_count: int
    consecutive_latest_blocked_count: int
    watch_report_count_delta: int | None
    blocked_report_count_delta: int | None
    latest_allocated_count_delta: int | None
    latest_total_allocated_paper_notional_delta: Decimal | None
    latest_reason_code_counts: tuple[tuple[str, int], ...]
    repeated_reason_code_counts: tuple[tuple[str, int], ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

def build_paper_autonomous_allocation_proposal_db_history_health_trend_gate_report(
    trend_report: object,
    *,
    config: PaperAutonomousAllocationProposalDbHistoryHealthTrendGateConfig,
    generated_at: datetime,
) -> PaperAutonomousAllocationProposalDbHistoryHealthTrendGateReport: ...
```

Loader module:

```python
def load_paper_autonomous_allocation_proposal_db_history_health_trend_gate_report(
    connection: object,
    *,
    limit: int | None,
    table_name: str,
    history_config: PaperAutonomousAllocationProposalDbHistoryConfig,
    health_config: PaperAutonomousAllocationProposalDbHistoryHealthConfig,
    trend_config: PaperAutonomousAllocationProposalDbHistoryHealthTrendConfig,
    gate_config: PaperAutonomousAllocationProposalDbHistoryHealthTrendGateConfig,
    generated_at: datetime,
) -> PaperAutonomousAllocationProposalDbHistoryHealthTrendGateReport: ...
```

CLI command:

```bash
.venv/bin/polymarket-alpha-lab paper-autonomous-allocation-proposal-db-history-health-trend-gate --limit 25
```

Summary line prefix:

```text
paper-autonomous-allocation-proposal-db-history-health-trend-gate:
```

---

### Task 1: Pure Health-Trend Gate Reducer

**Files:**
- Create: `src/polymarket_alpha_lab/paper_autonomous_allocation_proposal_db_history_health_trend_gate.py`
- Test: `tests/test_paper_autonomous_allocation_proposal_db_history_health_trend_gate.py`
- Test: `tests/test_paper_autonomous_allocation_proposal_db_history_health_trend_gate_scope.py`

**Interfaces:**
- Consumes: `PaperAutonomousAllocationProposalDbHistoryHealthTrendReport`.
- Produces: `PaperAutonomousAllocationProposalDbHistoryHealthTrendGateConfig`, `PaperAutonomousAllocationProposalDbHistoryHealthTrendGateReasonCodeCount`, `PaperAutonomousAllocationProposalDbHistoryHealthTrendGateReport`, and `build_paper_autonomous_allocation_proposal_db_history_health_trend_gate_report(...)`.

- [ ] **Step 1: Write reducer tests for pass/watch/blocked status derivation**

Create helper functions in `tests/test_paper_autonomous_allocation_proposal_db_history_health_trend_gate.py`:

```python
from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from importlib import import_module

import pytest

from polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_health_trend import (
    PaperAutonomousAllocationProposalDbHistoryHealthTrendReasonCodeRow,
    PaperAutonomousAllocationProposalDbHistoryHealthTrendReport,
    PaperAutonomousAllocationProposalDbHistoryHealthTrendSnapshotSummary,
)

GENERATED_AT = datetime(2026, 6, 24, 18, 0, tzinfo=UTC)
SOURCE_AT = datetime(2026, 6, 24, 17, 45, tzinfo=UTC)

def d(value: str) -> Decimal:
    return Decimal(value)

def _api():
    return import_module(
        "polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_health_trend_gate",
    )

def _config(**overrides):
    values = {
        "config_version": "paper-autonomous-allocation-proposal-db-history-health-trend-gate-v0",
        "min_source_health_report_count": 3,
        "max_consecutive_latest_watch_count": 0,
        "max_consecutive_latest_blocked_count": 0,
        "max_duplicate_generated_at_count": 0,
        "max_latest_source_age_seconds": 86_400,
        "max_watch_report_count_delta": 0,
        "max_blocked_report_count_delta": 0,
        "max_repeated_reason_code_count": 0,
    }
    values.update(overrides)
    return _api().PaperAutonomousAllocationProposalDbHistoryHealthTrendGateConfig(**values)

def _trend_report(
    *,
    source_count: int = 3,
    latest_health_status: str | None = "pass",
    consecutive_watch: int = 0,
    consecutive_blocked: int = 0,
    duplicate_generated_at_count: int = 0,
    latest_source_age_seconds: int | None = 300,
    watch_delta: int | None = 0,
    blocked_delta: int | None = 0,
    repeated_reason_counts: tuple[tuple[str, int], ...] = (),
) -> PaperAutonomousAllocationProposalDbHistoryHealthTrendReport:
    latest_at = SOURCE_AT if latest_health_status is not None else None
    status_counts = (
        ("pass", source_count if latest_health_status == "pass" else max(source_count - 1, 0)),
        ("watch", 1 if latest_health_status == "watch" else 0),
        ("blocked", 1 if latest_health_status == "blocked" else 0),
    )
    source_summaries = tuple(
        PaperAutonomousAllocationProposalDbHistoryHealthTrendSnapshotSummary(
            index + 1,
            SOURCE_AT - timedelta(minutes=source_count - index),
            "pass" if index + 1 < source_count else (latest_health_status or "blocked"),
            index + 3,
            index + 3,
            0,
            0,
            1,
            d("10.000000"),
            latest_source_age_seconds,
            latest_source_age_seconds,
            ("paper_autonomous_allocation_proposal_db_history_health_passed",),
        )
        for index in range(source_count)
    )
    return PaperAutonomousAllocationProposalDbHistoryHealthTrendReport(
        generated_at=SOURCE_AT,
        config_version="paper-autonomous-allocation-proposal-db-history-health-trend-v0",
        source_health_report_count=source_count,
        first_generated_at=source_summaries[0].generated_at if source_summaries else None,
        latest_generated_at=latest_at,
        latest_health_status=latest_health_status,
        health_status_counts=status_counts,
        consecutive_latest_watch_count=consecutive_watch,
        consecutive_latest_blocked_count=consecutive_blocked,
        duplicate_generated_at_count=duplicate_generated_at_count,
        history_report_count_first=3 if source_count else None,
        history_report_count_latest=source_count + 2 if source_count else None,
        history_report_count_delta=max(source_count - 1, 0) if source_count else None,
        pass_report_count_first=3 if source_count else None,
        pass_report_count_latest=3 if source_count else None,
        pass_report_count_delta=0 if source_count else None,
        watch_report_count_first=0 if source_count else None,
        watch_report_count_latest=watch_delta if watch_delta is not None else None,
        watch_report_count_delta=watch_delta,
        blocked_report_count_first=0 if source_count else None,
        blocked_report_count_latest=blocked_delta if blocked_delta is not None else None,
        blocked_report_count_delta=blocked_delta,
        latest_allocated_count_first=1 if source_count else None,
        latest_allocated_count_latest=2 if source_count else None,
        latest_allocated_count_delta=1 if source_count else None,
        latest_total_allocated_paper_notional_first=d("10.000000") if source_count else None,
        latest_total_allocated_paper_notional_latest=d("20.000000") if source_count else None,
        latest_total_allocated_paper_notional_delta=d("10.000000") if source_count else None,
        latest_source_age_seconds_first=latest_source_age_seconds if source_count else None,
        latest_source_age_seconds_latest=latest_source_age_seconds if source_count else None,
        latest_source_age_seconds_delta=0 if source_count else None,
        max_source_age_seconds_first=latest_source_age_seconds if source_count else None,
        max_source_age_seconds_latest=latest_source_age_seconds if source_count else None,
        max_source_age_seconds_delta=0 if source_count else None,
        latest_reason_code_counts=(),
        total_reason_code_counts=repeated_reason_counts,
        repeated_reason_code_counts=repeated_reason_counts,
        reason_code_rows=tuple(
            PaperAutonomousAllocationProposalDbHistoryHealthTrendReasonCodeRow(code, count, 0, count)
            for code, count in repeated_reason_counts
        ),
        source_summaries=source_summaries,
    )
```

Add tests:

```python
def test_trend_report_helper_builds_valid_source_report():
    report = _trend_report()
    assert report.source_health_report_count == 3
    assert report.latest_health_status == "pass"
    assert report.latest_source_age_seconds_latest == 300

def test_health_trend_gate_passes_clean_source_trend():
    report = _api().build_paper_autonomous_allocation_proposal_db_history_health_trend_gate_report(
        _trend_report(),
        config=_config(),
        generated_at=GENERATED_AT,
    )
    assert report.gate_status == "pass"
    assert report.recommended_next_step == (
        "allow_paper_autonomous_allocation_proposal_db_history_health_trend_review"
    )
    assert report.reason_codes == (
        "paper_autonomous_allocation_proposal_db_history_health_trend_gate_passed",
    )
    assert report.source_health_report_count == 3
    assert report.latest_health_status == "pass"
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

@pytest.mark.parametrize(
    ("trend", "expected_reason"),
    (
        (_trend_report(source_count=1), "insufficient_allocation_proposal_db_history_health_trend_samples"),
        (_trend_report(latest_health_status="blocked", consecutive_blocked=1), "latest_allocation_proposal_db_history_health_trend_blocked"),
        (_trend_report(latest_health_status=None, source_count=0), "missing_latest_allocation_proposal_db_history_health_trend_timestamp"),
    ),
)
def test_health_trend_gate_blocks_for_blocking_trend_inputs(trend, expected_reason):
    report = _api().build_paper_autonomous_allocation_proposal_db_history_health_trend_gate_report(
        trend,
        config=_config(),
        generated_at=GENERATED_AT,
    )
    assert report.gate_status == "blocked"
    assert report.recommended_next_step == (
        "block_paper_autonomous_allocation_proposal_db_history_health_trend_review"
    )
    assert expected_reason in report.reason_codes

@pytest.mark.parametrize(
    ("trend", "expected_reason"),
    (
        (_trend_report(latest_health_status="watch", consecutive_watch=1), "latest_allocation_proposal_db_history_health_trend_watch"),
        (_trend_report(duplicate_generated_at_count=1), "duplicate_allocation_proposal_db_history_health_trend_timestamp_threshold_exceeded"),
        (_trend_report(watch_delta=1), "worsening_allocation_proposal_db_history_health_trend_watch_count"),
        (_trend_report(blocked_delta=1), "worsening_allocation_proposal_db_history_health_trend_blocked_count"),
        (_trend_report(repeated_reason_counts=(("stale_allocation_proposal_db_history", 2),)), "repeated_allocation_proposal_db_history_health_trend_reason_threshold_exceeded"),
        (_trend_report(latest_source_age_seconds=86_401), "stale_allocation_proposal_db_history_health_trend"),
    ),
)
def test_health_trend_gate_watches_for_watch_trend_inputs(trend, expected_reason):
    report = _api().build_paper_autonomous_allocation_proposal_db_history_health_trend_gate_report(
        trend,
        config=_config(),
        generated_at=GENERATED_AT,
    )
    assert report.gate_status == "watch"
    assert report.recommended_next_step == (
        "throttle_paper_autonomous_allocation_proposal_db_history_health_trend_review"
    )
    assert expected_reason in report.reason_codes
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
.venv/bin/python -m pytest -q tests/test_paper_autonomous_allocation_proposal_db_history_health_trend_gate.py
```

Expected: FAIL with `ModuleNotFoundError` for `paper_autonomous_allocation_proposal_db_history_health_trend_gate`.

- [ ] **Step 3: Implement reducer**

Create the module with these constants and functions:

```python
NEXT_STEP_BY_STATUS = {
    "pass": "allow_paper_autonomous_allocation_proposal_db_history_health_trend_review",
    "watch": "throttle_paper_autonomous_allocation_proposal_db_history_health_trend_review",
    "blocked": "block_paper_autonomous_allocation_proposal_db_history_health_trend_review",
}
PASS_REASON_CODE = "paper_autonomous_allocation_proposal_db_history_health_trend_gate_passed"
BLOCKED_REASON_CODES = frozenset((
    "insufficient_allocation_proposal_db_history_health_trend_samples",
    "latest_allocation_proposal_db_history_health_trend_blocked",
    "consecutive_allocation_proposal_db_history_health_trend_blocked_threshold_exceeded",
    "missing_latest_allocation_proposal_db_history_health_trend_timestamp",
))
WATCH_REASON_CODES = frozenset((
    "latest_allocation_proposal_db_history_health_trend_watch",
    "consecutive_allocation_proposal_db_history_health_trend_watch_threshold_exceeded",
    "duplicate_allocation_proposal_db_history_health_trend_timestamp_threshold_exceeded",
    "repeated_allocation_proposal_db_history_health_trend_reason_threshold_exceeded",
    "worsening_allocation_proposal_db_history_health_trend_watch_count",
    "worsening_allocation_proposal_db_history_health_trend_blocked_count",
    "stale_allocation_proposal_db_history_health_trend",
))
```

Gate reason code derivation must be:

```python
def _gate_reason_codes(
    *,
    trend_report: PaperAutonomousAllocationProposalDbHistoryHealthTrendReport,
    config: PaperAutonomousAllocationProposalDbHistoryHealthTrendGateConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if trend_report.source_health_report_count < config.min_source_health_report_count:
        reason_codes.append("insufficient_allocation_proposal_db_history_health_trend_samples")
    if trend_report.latest_generated_at is None:
        reason_codes.append("missing_latest_allocation_proposal_db_history_health_trend_timestamp")
    if trend_report.latest_health_status == "blocked":
        reason_codes.append("latest_allocation_proposal_db_history_health_trend_blocked")
    if trend_report.consecutive_latest_blocked_count > config.max_consecutive_latest_blocked_count:
        reason_codes.append("consecutive_allocation_proposal_db_history_health_trend_blocked_threshold_exceeded")
    if trend_report.latest_health_status == "watch":
        reason_codes.append("latest_allocation_proposal_db_history_health_trend_watch")
    if trend_report.consecutive_latest_watch_count > config.max_consecutive_latest_watch_count:
        reason_codes.append("consecutive_allocation_proposal_db_history_health_trend_watch_threshold_exceeded")
    if trend_report.duplicate_generated_at_count > config.max_duplicate_generated_at_count:
        reason_codes.append("duplicate_allocation_proposal_db_history_health_trend_timestamp_threshold_exceeded")
    if (
        trend_report.latest_source_age_seconds_latest is not None
        and trend_report.latest_source_age_seconds_latest > config.max_latest_source_age_seconds
    ):
        reason_codes.append("stale_allocation_proposal_db_history_health_trend")
    if (
        trend_report.watch_report_count_delta is not None
        and trend_report.watch_report_count_delta > config.max_watch_report_count_delta
    ):
        reason_codes.append("worsening_allocation_proposal_db_history_health_trend_watch_count")
    if (
        trend_report.blocked_report_count_delta is not None
        and trend_report.blocked_report_count_delta > config.max_blocked_report_count_delta
    ):
        reason_codes.append("worsening_allocation_proposal_db_history_health_trend_blocked_count")
    if any(count > config.max_repeated_reason_code_count for _, count in trend_report.repeated_reason_code_counts):
        reason_codes.append("repeated_allocation_proposal_db_history_health_trend_reason_threshold_exceeded")
    if not reason_codes:
        reason_codes.append(PASS_REASON_CODE)
    return tuple(sorted(set(reason_codes)))
```

Status derivation must be:

```python
def _gate_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in BLOCKED_REASON_CODES for reason_code in reason_codes):
        return "blocked"
    if any(reason_code in WATCH_REASON_CODES for reason_code in reason_codes):
        return "watch"
    return "pass"
```

The builder body must echo source-trend fields exactly:

```python
def build_paper_autonomous_allocation_proposal_db_history_health_trend_gate_report(
    trend_report: object,
    *,
    config: PaperAutonomousAllocationProposalDbHistoryHealthTrendGateConfig,
    generated_at: datetime,
) -> PaperAutonomousAllocationProposalDbHistoryHealthTrendGateReport:
    if type(trend_report) is not PaperAutonomousAllocationProposalDbHistoryHealthTrendReport:
        raise ValueError(
            "trend_report must be a "
            "PaperAutonomousAllocationProposalDbHistoryHealthTrendReport",
        )
    if type(config) is not PaperAutonomousAllocationProposalDbHistoryHealthTrendGateConfig:
        raise ValueError(
            "config must be a "
            "PaperAutonomousAllocationProposalDbHistoryHealthTrendGateConfig",
        )
    generated_at_utc = _as_utc("generated_at", generated_at)
    _validate_hard_flags("config", config)
    reason_codes = _gate_reason_codes(trend_report=trend_report, config=config)
    gate_status = _gate_status(reason_codes)
    reason_code_counts = tuple(
        PaperAutonomousAllocationProposalDbHistoryHealthTrendGateReasonCodeCount(
            reason_code=reason_code,
            report_count=1,
        )
        for reason_code in reason_codes
    )
    return PaperAutonomousAllocationProposalDbHistoryHealthTrendGateReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        source_config_version=trend_report.config_version,
        source_generated_at=trend_report.generated_at,
        gate_status=gate_status,
        recommended_next_step=NEXT_STEP_BY_STATUS[gate_status],
        reason_code_counts=reason_code_counts,
        source_health_report_count=trend_report.source_health_report_count,
        latest_health_status=trend_report.latest_health_status,
        latest_health_generated_at=trend_report.latest_generated_at,
        latest_source_age_seconds=trend_report.latest_source_age_seconds_latest,
        duplicate_generated_at_count=trend_report.duplicate_generated_at_count,
        consecutive_latest_watch_count=trend_report.consecutive_latest_watch_count,
        consecutive_latest_blocked_count=trend_report.consecutive_latest_blocked_count,
        watch_report_count_delta=trend_report.watch_report_count_delta,
        blocked_report_count_delta=trend_report.blocked_report_count_delta,
        latest_allocated_count_delta=trend_report.latest_allocated_count_delta,
        latest_total_allocated_paper_notional_delta=(
            trend_report.latest_total_allocated_paper_notional_delta
        ),
        latest_reason_code_counts=trend_report.latest_reason_code_counts,
        repeated_reason_code_counts=trend_report.repeated_reason_code_counts,
        reason_codes=reason_codes,
    )
```

`report_count=1` is intentional because the gate reducer emits one aggregate gate report with a deduplicated reason set. `reason_code_counts` must be built from the same sorted `reason_codes` tuple so ordering is deterministic.

- [ ] **Step 4: Add reducer validation tests**

Add tests for:

```python
def test_health_trend_gate_reason_code_counts_are_deterministic_and_positive():
    trend = _trend_report(
        latest_health_status="blocked",
        consecutive_blocked=2,
        duplicate_generated_at_count=1,
        blocked_delta=1,
        repeated_reason_counts=(("latest_allocation_proposal_db_history_blocked", 2),),
    )
    report = _api().build_paper_autonomous_allocation_proposal_db_history_health_trend_gate_report(
        trend,
        config=_config(min_source_health_report_count=4, max_consecutive_latest_blocked_count=1),
        generated_at=GENERATED_AT,
    )
    assert report.gate_status == "blocked"
    assert report.reason_codes == tuple(row.reason_code for row in report.reason_code_counts)
    assert all(row.report_count == 1 for row in report.reason_code_counts)
    assert "paper_autonomous_allocation_proposal_db_history_health_trend_gate_passed" not in report.reason_codes
```

Add frozen/exact-type tests:

```python
def test_health_trend_gate_dataclasses_are_frozen_and_validate_hard_flags():
    api = _api()
    config = _config()
    report = api.build_paper_autonomous_allocation_proposal_db_history_health_trend_gate_report(
        _trend_report(),
        config=config,
        generated_at=GENERATED_AT,
    )
    with pytest.raises(FrozenInstanceError):
        config.config_version = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.gate_status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="config .*paper_only"):
        replace(config, paper_only=False)
    with pytest.raises(ValueError, match="gate report .*readonly"):
        replace(report, readonly=False)
```

- [ ] **Step 5: Add reducer scope test**

Create `tests/test_paper_autonomous_allocation_proposal_db_history_health_trend_gate_scope.py`:

```python
from __future__ import annotations

import ast
from pathlib import Path

MODULE = Path("src/polymarket_alpha_lab/paper_autonomous_allocation_proposal_db_history_health_trend_gate.py")

def test_health_trend_gate_module_has_no_db_env_cli_or_live_trading_surface():
    source = MODULE.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported_modules = []
    call_names = []
    attribute_names = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.append(node.module)
        elif isinstance(node, ast.Call):
            function = node.func
            if isinstance(function, ast.Name):
                call_names.append(function.id)
            elif isinstance(function, ast.Attribute):
                call_names.append(function.attr)
        elif isinstance(node, ast.Attribute):
            attribute_names.append(node.attr)
    assert set(imported_modules) <= {
        "__future__",
        "dataclasses",
        "datetime",
        "decimal",
        "polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_health_trend",
    }
    banned = {
        "psycopg", "supabase", "environ", "requests", "httpx", "urllib",
        "client", "exchange", "auth", "wallet", "account", "order",
        "trade", "execute", "submit", "approve", "sign", "cancel", "replace",
        "insert", "update", "delete", "upsert", "persist", "commit", "rollback",
        "cursor", "print", "open",
    }
    lower_source = source.lower()
    for token in banned:
        assert token not in lower_source
    assert not (banned & set(name.lower() for name in call_names))
    assert not (banned & set(name.lower() for name in attribute_names))
```

- [ ] **Step 6: Run reducer tests**

Run:

```bash
.venv/bin/python -m pytest -q \
  tests/test_paper_autonomous_allocation_proposal_db_history_health_trend_gate.py \
  tests/test_paper_autonomous_allocation_proposal_db_history_health_trend_gate_scope.py
```

Expected: PASS.

---

### Task 2: Read-Only Loader Composition

**Files:**
- Create: `src/polymarket_alpha_lab/paper_autonomous_allocation_proposal_db_history_health_trend_gate_load.py`
- Test: `tests/test_paper_autonomous_allocation_proposal_db_history_health_trend_gate_load.py`

**Interfaces:**
- Consumes: existing `load_paper_autonomous_allocation_proposal_db_history_health_trend_report(...)` and Task 1 reducer.
- Produces: `load_paper_autonomous_allocation_proposal_db_history_health_trend_gate_report(...)`.

- [ ] **Step 1: Write loader tests**

Create module stubs like the previous loader test and assert:

```python
def test_loader_composes_health_trend_loader_and_gate_reducer(monkeypatch):
    history_config = PaperAutonomousAllocationProposalDbHistoryConfig()
    health_config = PaperAutonomousAllocationProposalDbHistoryHealthConfig()
    trend_config = PaperAutonomousAllocationProposalDbHistoryHealthTrendConfig()
    gate_config = PaperAutonomousAllocationProposalDbHistoryHealthTrendGateConfig()
    trend_report = object()
    expected_gate_report = object()
    trend_loader_calls = []
    gate_builder_calls = []

    def fake_trend_loader(connection, *, limit, table_name, history_config, health_config, trend_config, generated_at):
        trend_loader_calls.append({
            "connection": connection,
            "limit": limit,
            "table_name": table_name,
            "history_config": history_config,
            "health_config": health_config,
            "trend_config": trend_config,
            "generated_at": generated_at,
        })
        return trend_report

    def fake_gate_builder(received_trend_report, *, config, generated_at):
        gate_builder_calls.append({
            "trend_report": received_trend_report,
            "config": config,
            "generated_at": generated_at,
        })
        return expected_gate_report
```

Expected assertions:

```python
assert result is expected_gate_report
assert trend_loader_calls == [{
    "connection": connection,
    "limit": 25,
    "table_name": "paper_autonomous_allocation_proposal_reports_test",
    "history_config": history_config,
    "health_config": health_config,
    "trend_config": trend_config,
    "generated_at": GENERATED_AT,
}]
assert gate_builder_calls == [{
    "trend_report": trend_report,
    "config": gate_config,
    "generated_at": GENERATED_AT,
}]
```

- [ ] **Step 2: Implement loader**

Implementation body:

```python
def load_paper_autonomous_allocation_proposal_db_history_health_trend_gate_report(
    connection: object,
    *,
    limit: int | None,
    table_name: str,
    history_config: PaperAutonomousAllocationProposalDbHistoryConfig,
    health_config: PaperAutonomousAllocationProposalDbHistoryHealthConfig,
    trend_config: PaperAutonomousAllocationProposalDbHistoryHealthTrendConfig,
    gate_config: PaperAutonomousAllocationProposalDbHistoryHealthTrendGateConfig,
    generated_at: datetime,
) -> PaperAutonomousAllocationProposalDbHistoryHealthTrendGateReport:
    if type(history_config) is not PaperAutonomousAllocationProposalDbHistoryConfig:
        raise ValueError("history_config must be a PaperAutonomousAllocationProposalDbHistoryConfig")
    if type(health_config) is not PaperAutonomousAllocationProposalDbHistoryHealthConfig:
        raise ValueError("health_config must be a PaperAutonomousAllocationProposalDbHistoryHealthConfig")
    if type(trend_config) is not PaperAutonomousAllocationProposalDbHistoryHealthTrendConfig:
        raise ValueError("trend_config must be a PaperAutonomousAllocationProposalDbHistoryHealthTrendConfig")
    if type(gate_config) is not PaperAutonomousAllocationProposalDbHistoryHealthTrendGateConfig:
        raise ValueError("gate_config must be a PaperAutonomousAllocationProposalDbHistoryHealthTrendGateConfig")
    trend_report = load_paper_autonomous_allocation_proposal_db_history_health_trend_report(
        connection,
        limit=limit,
        table_name=table_name,
        history_config=history_config,
        health_config=health_config,
        trend_config=trend_config,
        generated_at=generated_at,
    )
    return build_paper_autonomous_allocation_proposal_db_history_health_trend_gate_report(
        trend_report,
        config=gate_config,
        generated_at=generated_at,
    )
```

- [ ] **Step 3: Add loader boundary tests**

Tests must prove:

```python
def test_loader_rejects_non_exact_configs_before_trend_read(...): ...
def test_loader_does_not_manage_connection_lifecycle_or_write(...): ...
def test_loader_module_has_no_db_lifecycle_env_cli_or_live_trading_surface(...): ...
```

The AST banned names set must include:

```python
{
    "psycopg", "supabase", "environ", "migration", "commit", "rollback",
    "cursor", "execute", "executemany", "insert", "update", "delete",
    "upsert", "persist", "auth", "client", "exchange", "network",
    "wallet", "account", "order", "execution", "approval", "trade",
    "sign", "submit", "cancel", "replace",
}
```

- [ ] **Step 4: Run loader tests**

Run:

```bash
.venv/bin/python -m pytest -q tests/test_paper_autonomous_allocation_proposal_db_history_health_trend_gate_load.py
```

Expected: PASS.

---

### Task 3: CLI Wiring

**Files:**
- Modify: `src/polymarket_alpha_lab/cli.py`
- Test: `tests/test_cli_paper_autonomous_allocation_proposal_db_history_health_trend_gate.py`
- Test: `tests/test_cli_paper_autonomous_allocation_proposal_db_history_health_trend_gate_scope.py`

**Interfaces:**
- Consumes: Task 2 loader and Task 1 gate report fields.
- Produces: new CLI command and summary printer.

- [ ] **Step 1: Write CLI tests for injected runner and summary**

Add tests patterned on the existing health-trend CLI tests:

```python
def test_allocation_proposal_db_history_health_trend_gate_command_uses_injected_runner(capsys):
    runner_calls = []
    report = SimpleNamespace(
        gate_status="pass",
        recommended_next_step="allow_paper_autonomous_allocation_proposal_db_history_health_trend_review",
        source_health_report_count=3,
        latest_health_status="pass",
        latest_source_age_seconds=300,
        duplicate_generated_at_count=0,
        consecutive_latest_watch_count=0,
        consecutive_latest_blocked_count=0,
        watch_report_count_delta=0,
        blocked_report_count_delta=0,
        reason_code_counts=(SimpleNamespace(reason_code="paper_autonomous_allocation_proposal_db_history_health_trend_gate_passed", report_count=1),),
    )
    def runner(**kwargs):
        runner_calls.append(kwargs)
        return report
    result = cli.main(
        ["paper-autonomous-allocation-proposal-db-history-health-trend-gate", "--limit", "7"],
        paper_autonomous_allocation_proposal_db_history_health_trend_gate_runner=runner,
    )
    assert result == 0
    assert runner_calls[0]["limit"] == 7
    out = capsys.readouterr().out
    assert "paper-autonomous-allocation-proposal-db-history-health-trend-gate:" in out
    assert "gate_status=pass" in out
    assert "recommended_next_step=allow_paper_autonomous_allocation_proposal_db_history_health_trend_review" in out
    assert "persisted=" not in out
```

- [ ] **Step 2: Implement CLI parser, branch, helper, printer**

Add:

```python
PaperAutonomousAllocationProposalDbHistoryHealthTrendGateRunner = Callable[..., object]
```

Add `main(...)` parameter:

```python
paper_autonomous_allocation_proposal_db_history_health_trend_gate_runner: (
    PaperAutonomousAllocationProposalDbHistoryHealthTrendGateRunner | None
) = None,
```

Add parser:

```python
paper_autonomous_allocation_proposal_db_history_health_trend_gate = subparsers.add_parser(
    "paper-autonomous-allocation-proposal-db-history-health-trend-gate",
)
paper_autonomous_allocation_proposal_db_history_health_trend_gate.add_argument(
    "--limit",
    type=int,
    default=25,
    dest="limit",
)
```

Add `_run_paper_autonomous_allocation_proposal_db_history_health_trend_gate(...)` next to the health-trend helper. It must construct `history_config`, `health_config`, `trend_config`, `gate_config`, use injected runner if present, otherwise lazy-import `psycopg`, connect with `autocommit=True`, call the Task 2 loader, redact exceptions, and close the connection only.

Printer fields:

```python
summary_parts = [
    "paper-autonomous-allocation-proposal-db-history-health-trend-gate:",
    f"gate_status={report.gate_status}",
    f"recommended_next_step={report.recommended_next_step}",
    f"source_health_report_count={report.source_health_report_count}",
    f"latest_health_status={_none_or_value(report.latest_health_status)}",
    f"latest_source_age_seconds={_none_or_value(report.latest_source_age_seconds)}",
    f"duplicate_generated_at_count={report.duplicate_generated_at_count}",
    f"consecutive_latest_watch_count={report.consecutive_latest_watch_count}",
    f"consecutive_latest_blocked_count={report.consecutive_latest_blocked_count}",
    f"watch_report_count_delta={_none_or_value(report.watch_report_count_delta)}",
    f"blocked_report_count_delta={_none_or_value(report.blocked_report_count_delta)}",
    f"reason_code_counts={reason_code_counts or 'none'}",
]
```

- [ ] **Step 3: Add CLI default-path and redaction tests**

Tests must cover:

```python
def test_health_trend_gate_helper_validates_limit_before_runner_or_imports(...): ...
def test_health_trend_gate_helper_uses_psycopg_autocommit_and_closes_once(...): ...
def test_health_trend_gate_default_path_redacts_dsn_and_table_on_loader_error(...): ...
def test_health_trend_gate_summary_suppresses_sensitive_fields(...): ...
```

Sensitive-field test object must include extra attributes:

```python
dsn = "postgresql://user:secret@example.invalid/db"
table_name = "private_schema.paper_autonomous_allocation_proposal_reports"
payload_json = {"market_slug": "secret-market", "question": "secret question"}
report_sha256 = "a" * 64
allocation_rows_json = [{"side": "YES", "action": "buy"}]
recommendation_score = "0.99"
```

Assert none appear in stdout.

- [ ] **Step 4: Add CLI scope test**

The scope test must assert:

```python
FORBIDDEN_FLAGS = (
    "--dsn", "--table", "--persist", "--fast", "--live", "--auth",
    "--wallet", "--private-key", "--api-key", "--account", "--order",
    "--trade", "--execute", "--submit", "--approve",
)
```

Each flag should fail argparse before env/runner/connect.

- [ ] **Step 5: Run CLI tests**

Run:

```bash
.venv/bin/python -m pytest -q \
  tests/test_cli_paper_autonomous_allocation_proposal_db_history_health_trend_gate.py \
  tests/test_cli_paper_autonomous_allocation_proposal_db_history_health_trend_gate_scope.py
```

Expected: PASS.

---

### Task 4: Exports, Docs, and Scope Allowlists

**Files:**
- Modify: `src/polymarket_alpha_lab/__init__.py`
- Modify: `tests/test_init.py`
- Modify: `README.md`
- Modify: `docs/paper-autonomous-allocation-proposal.md`
- Modify: `tests/test_docs_paper_autonomous_allocation_proposal_scope.py`
- Modify: every `tests/*_scope.py` file containing `EXPECTED_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_EXPORTS`

**Interfaces:**
- Consumes: Task 1 public reducer API.
- Produces: package-root public API and guarded docs.

- [ ] **Step 1: Update package exports**

Add imports to `src/polymarket_alpha_lab/__init__.py`:

```python
from polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_health_trend_gate import (
    PaperAutonomousAllocationProposalDbHistoryHealthTrendGateConfig,
    PaperAutonomousAllocationProposalDbHistoryHealthTrendGateReasonCodeCount,
    PaperAutonomousAllocationProposalDbHistoryHealthTrendGateReport,
    build_paper_autonomous_allocation_proposal_db_history_health_trend_gate_report,
)
```

Add those four names to `__all__`. Do not export:

```python
DEFAULT_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_HEALTH_TREND_GATE_CONFIG_VERSION
PaperAutonomousAllocationProposalDbHistoryHealthTrendGateRunner
load_paper_autonomous_allocation_proposal_db_history_health_trend_gate_report
_run_paper_autonomous_allocation_proposal_db_history_health_trend_gate
_print_paper_autonomous_allocation_proposal_db_history_health_trend_gate_summary
```

- [ ] **Step 2: Update `tests/test_init.py`**

Add expected exports and binding assertions:

```python
assert lab.PaperAutonomousAllocationProposalDbHistoryHealthTrendGateConfig is PaperAutonomousAllocationProposalDbHistoryHealthTrendGateConfig
assert lab.PaperAutonomousAllocationProposalDbHistoryHealthTrendGateReasonCodeCount is PaperAutonomousAllocationProposalDbHistoryHealthTrendGateReasonCodeCount
assert lab.PaperAutonomousAllocationProposalDbHistoryHealthTrendGateReport is PaperAutonomousAllocationProposalDbHistoryHealthTrendGateReport
assert lab.build_paper_autonomous_allocation_proposal_db_history_health_trend_gate_report is build_paper_autonomous_allocation_proposal_db_history_health_trend_gate_report
```

Add forbidden exports listed above.

- [ ] **Step 3: Update all broad scope export allowlists**

Run:

```bash
rg -l "EXPECTED_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_EXPORTS" tests/*_scope.py
```

Every returned file must be inspected before editing to confirm whether the allowlist participates in an equality assertion, subset assertion, or larger composed export set. Update the allowlist and `src/polymarket_alpha_lab/__init__.py` in lockstep so equality-style scope tests cannot drift.

In every returned file, add exactly:

```python
"PaperAutonomousAllocationProposalDbHistoryHealthTrendGateConfig",
"PaperAutonomousAllocationProposalDbHistoryHealthTrendGateReasonCodeCount",
"PaperAutonomousAllocationProposalDbHistoryHealthTrendGateReport",
"build_paper_autonomous_allocation_proposal_db_history_health_trend_gate_report",
```

- [ ] **Step 4: Update docs**

Add this README block after DB History Health Trend:

```markdown
DB History Health Trend Gate:

Command: `.venv/bin/polymarket-alpha-lab paper-autonomous-allocation-proposal-db-history-health-trend-gate --limit 25`

The DB history health trend gate command is env-only, read-only,
paper-only/report-only/readonly, and no-write. It accepts only `--limit`.
It reads the final allocation proposal DB configured by env, derives the DB
history health trend from persisted final allocation proposal history, and
prints one aggregate gate report.

It does not write reports and does not read upstream screening/queue tables.
It does not place orders, approve execution, read accounts, or mutate exchange state.
The health-trend gate status is not permission to trade.
It is not financial advice, not investment ranking, and not an approval workflow.
It prints aggregate health-trend gate status, recommended next step, latest
health status, sample counts, duplicate timestamp count, latest streak counts,
health-delta signals, and reason-code counts.
```

Add an equivalent `## DB History Health Trend Gate` section to `docs/paper-autonomous-allocation-proposal.md`.

- [ ] **Step 5: Update docs scope test**

Add required heading/phrases:

```python
"## DB History Health Trend Gate",
"paper-autonomous-allocation-proposal-db-history-health-trend-gate --limit 25",
"health-trend gate status is not permission to trade",
"prints aggregate health-trend gate status, recommended next step, latest health status, sample counts, duplicate timestamp count, latest streak counts, health-delta signals, and reason-code counts",
```

- [ ] **Step 6: Run export/docs tests**

Run:

```bash
.venv/bin/python -m pytest -q \
  tests/test_init.py \
  tests/test_docs_paper_autonomous_allocation_proposal_scope.py \
  $(rg -l "EXPECTED_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_EXPORTS" tests/*_scope.py)
```

Expected: PASS.

---

### Task 5: Verification, Review, Commit, Push, and Handoff

**Files:**
- No source files owned by this task unless review feedback requires fixes.

**Interfaces:**
- Consumes: Tasks 1-4.
- Produces: verified node, OpenCode code review, next-stage plan review, commit/push, Handoff Summary.

- [ ] **Step 1: Run focused verification**

Run:

```bash
.venv/bin/python -m pytest -q \
  tests/test_paper_autonomous_allocation_proposal_db_history_health_trend_gate.py \
  tests/test_paper_autonomous_allocation_proposal_db_history_health_trend_gate_scope.py \
  tests/test_paper_autonomous_allocation_proposal_db_history_health_trend_gate_load.py \
  tests/test_cli_paper_autonomous_allocation_proposal_db_history_health_trend_gate.py \
  tests/test_cli_paper_autonomous_allocation_proposal_db_history_health_trend_gate_scope.py \
  tests/test_init.py \
  tests/test_docs_paper_autonomous_allocation_proposal_scope.py
```

Expected: PASS.

- [ ] **Step 2: Run previous-node regression**

Run:

```bash
.venv/bin/python -m pytest -q \
  tests/test_paper_autonomous_allocation_proposal_db_history_health_trend.py \
  tests/test_paper_autonomous_allocation_proposal_db_history_health_trend_load.py \
  tests/test_cli_paper_autonomous_allocation_proposal_db_history_health_trend.py \
  tests/test_cli_paper_autonomous_allocation_proposal_db_history_health_trend_scope.py
```

Expected: PASS.

- [ ] **Step 3: Run broad verification**

Run:

```bash
.venv/bin/python -m pytest -q
.venv/bin/python -m compileall src/polymarket_alpha_lab
git diff --check
codegraph sync .
```

Expected: all pass.

- [ ] **Step 4: Run tracked secret scan**

Run:

```bash
git grep -n -I -E '(ghp_[A-Za-z0-9_]+|github_pat_[A-Za-z0-9_]+|sk-[A-Za-z0-9_-]+|AKIA[0-9A-Z]{16}|PRIVATE KEY|BEGIN RSA|BEGIN OPENSSH|POLYMARKET_.*(KEY|SECRET|TOKEN)|SUPABASE_.*(KEY|SECRET|TOKEN))' -- ':!docs/superpowers/plans/*.md'
```

Expected: no output and exit code 1. If the command finds tracked secrets, stop and fix before review.

- [ ] **Step 5: OpenCode code review**

Create a diff file:

```bash
git diff -- . ':(exclude).superpowers' > /tmp/pal-health-trend-gate-review.diff
```

Run local OpenCode with the required reviewer model:

```bash
opencode run \
  -m zhipuai-coding-plan/glm-5.2 \
  --variant max \
  --dir /home/ubuntu/polymarket-alpha-lab \
  --file=/tmp/pal-health-trend-gate-review.diff \
  -- \
  "Read-only code review only. Review the attached diff and the current working tree for the paper autonomous allocation proposal DB-history health-trend gate node. Focus on Critical/Important bugs, plan deviations, Phase 1 boundary drift, live/auth/order/wallet/account surfaces, DB writes, misleading operator output, redaction issues, export/API problems, and missing tests. DO NOT modify/create/delete ANY file; output ONLY verdict + findings."
```

- [ ] **Step 6: Prepare next-stage plan for OpenCode before push**

Before commit/push, create the next-stage plan draft and send it to local OpenCode with:

```bash
opencode run \
  -m zhipuai-coding-plan/glm-5.2 \
  --variant max \
  --dir /home/ubuntu/polymarket-alpha-lab \
  --file=/tmp/pal-next-stage-plan.md \
  -- \
  "Read-only plan review only. Review the attached next-stage plan for the Polymarket Alpha Lab autonomous allocation proposal pipeline. Verify objective, approach, tech stack, Phase 1 boundaries, tests, and whether it should follow this health-trend gate node. DO NOT modify/create/delete ANY file; output ONLY verdict + findings."
```

- [ ] **Step 7: Commit and push if all gates pass**

Stage only intended files:

```bash
git add README.md docs src tests
git status --short
git commit -m "Add allocation proposal DB history health trend gate node"
git push origin main
```

Confirm:

```bash
git rev-parse HEAD
git rev-parse origin/main
git status --short
```

Expected: `HEAD` equals `origin/main`; `.superpowers/` may remain untracked and must not be committed.

- [ ] **Step 8: Write Handoff Summary**

Include:

```markdown
Handoff Summary:
- Repo state: branch, HEAD SHA, origin/main SHA, clean/dirty state, untracked `.superpowers/` status.
- Completed node: files/modules added and command added.
- Verified commands: focused pytest, regression pytest, full pytest, compileall, git diff --check, codegraph sync, tracked secret scan, OpenCode review result.
- Uncommitted files: list exact files or state only `.superpowers/`.
- Next step: the next plan or implementation node.
```

Do not paste large diffs or long logs.

---

## Self-Review

Spec coverage:
- User asked for plan before implementation, multiple subagents, timely subagent cleanup, GitHub push at node completion, and Handoff Summary. Current repository rules route all plan/code reviews to local OpenCode, so this plan includes OpenCode plan-review, subagent lane decomposition, OpenCode code-review, OpenCode next-plan review, push, and Handoff Summary.
- User asked to move toward automatic screening/judgment/investment but remain in current safe Phase 1 boundaries. This node adds a judgment gate over health trends while explicitly avoiding live trading, auth, accounts, wallets, orders, and investment ranking.
- User said all data should be in DB. Current architecture persists canonical allocation proposal reports and derives this gate read-only; persistence for derived reports is explicitly deferred to a later schema/identity node.

Placeholder scan:
- No `TBD`, `TODO`, `implement later`, or unspecified error handling remains.

Type consistency:
- Reducer, loader, CLI runner, package exports, and tests use the same `PaperAutonomousAllocationProposalDbHistoryHealthTrendGate...` prefix.
- The loader consumes exact config types from the existing history, health, trend modules and the new gate module.
- CLI command name consistently uses `paper-autonomous-allocation-proposal-db-history-health-trend-gate`.
