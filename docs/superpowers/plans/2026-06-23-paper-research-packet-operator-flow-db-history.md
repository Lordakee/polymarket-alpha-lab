# Paper Research Packet Operator Flow DB History Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a read-only operator-flow DB history command that summarizes persisted paper research packet operator-flow reports for later autonomous screening stability gates.

**Architecture:** Follow the existing paper research packet quality DB history shape: a pure reducer summarizes already-built report dataclasses, a small loader reads persisted reports and reverses DB-descending rows into chronological order, and the CLI wires env-only DB config into a concise stdout summary. This remains Phase 1 paper/report/read-only infrastructure and does not introduce live trading, auth, wallet, signing, account, exchange, order, or relayer behavior.

**Tech Stack:** Python frozen dataclasses, Decimal-safe reducers, argparse CLI, psycopg read-only autocommit connection in the default load path, pytest, CodeGraph.

## Global Constraints

- Work in `/home/ubuntu/polymarket-alpha-lab` on branch `main`; the user has explicitly authorized continuing and pushing completed reviewed nodes.
- `.codegraph/` exists; use CodeGraph before grep/find/manual source reads when locating or understanding code.
- Use TDD for new behavior: write failing tests first, run them to verify red, then implement.
- Use `.venv/bin/python -m pytest`, not bare `pytest`.
- Use `apply_patch` for manual source edits.
- Use frozen dataclasses and exact-type validation matching existing reducers.
- Keep Phase 1 boundaries: paper-only, report-only, readonly.
- Do not add live trading, wallet, private keys, signing, orders, relayer, account, exchange, auth, or network mutation.
- Do not give financial advice or trade instructions.
- Do not add CLI DSN/table/persist flags for the operator-flow history command; reuse existing operator-flow DB env variables only.
- DB/env/psycopg usage belongs only in boundary modules and CLI helpers, never in pure reducers.
- Pure reducers must not import psycopg, os/env modules, or DB store modules.
- Preserve Decimal-only posture; do not introduce float arithmetic.
- Redact DSN, schema/table names, table tails, payload JSON, questions, and hashes from CLI failure output.
- Reviews are performed by local OpenCode using model `zhipuai-coding-plan/glm-5.2` with `--variant max`.
- Completed reviewed nodes must be committed, CodeGraph-synced, pushed to GitHub, and recorded in `.superpowers/sdd/progress.md`.

---

## File Structure

- Create `src/polymarket_alpha_lab/paper_research_packet_operator_flow_db_history.py`.
  Pure reducer for persisted operator-flow report history. Owns config, row/report dataclasses, validation, chronological sorting, status counts, duplicate timestamp counts, consecutive latest status counts, reason-code counts, and final `history_status`.
- Create `src/polymarket_alpha_lab/paper_research_packet_operator_flow_db_history_load.py`.
  Boundary loader that calls `load_paper_research_packet_operator_flow_reports(...)`, reverses the DB-descending output, and calls the pure reducer.
- Modify `src/polymarket_alpha_lab/cli.py`.
  Add command `paper-research-packet-operator-flow-db-history`, a default load helper, dependency injection point, env-only config wiring, redacted failures, and summary printing.
- Modify `README.md`.
  Document the command and its env-only operator-flow DB config.
- Test `tests/test_paper_research_packet_operator_flow_db_history.py`.
- Test `tests/test_paper_research_packet_operator_flow_db_history_load.py`.
- Test `tests/test_cli_paper_research_packet_operator_flow_db_history.py`.
- Optionally modify `tests/test_cli_paper_research_packet_operator_flow_scope.py` only if there is an existing scope/forbidden-flags test pattern that should cover the new command.

---

### Task 1: Pure Operator-Flow DB History Reducer

**Files:**
- Create: `src/polymarket_alpha_lab/paper_research_packet_operator_flow_db_history.py`
- Test: `tests/test_paper_research_packet_operator_flow_db_history.py`

**Interfaces:**
- Consumes: `PaperResearchPacketOperatorFlowReport` and `FLOW_STATUSES` from `polymarket_alpha_lab.paper_research_packet_operator_flow`.
- Produces:
  - `DEFAULT_PAPER_RESEARCH_PACKET_OPERATOR_FLOW_DB_HISTORY_CONFIG_VERSION: str`
  - `PaperResearchPacketOperatorFlowDbHistoryConfig`
  - `PaperResearchPacketOperatorFlowDbHistoryStatusRow`
  - `PaperResearchPacketOperatorFlowDbHistoryReasonCodeRow`
  - `PaperResearchPacketOperatorFlowDbHistoryReport`
  - `build_paper_research_packet_operator_flow_db_history_report(operator_flow_reports: object, *, config: PaperResearchPacketOperatorFlowDbHistoryConfig, generated_at: datetime) -> PaperResearchPacketOperatorFlowDbHistoryReport`

- [ ] **Step 1: Write failing tests for empty, insufficient, pass, watch, blocked, duplicates, consecutive latest counts, deterministic reason codes, frozen dataclasses, exact types, and hard flags**

Required baseline helper shape in the test:

```python
from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from importlib import import_module

import pytest

from polymarket_alpha_lab.paper_research_packet_operator_flow import (
    PaperResearchPacketOperatorFlowReport,
)

GENERATED_AT = datetime(2026, 6, 23, 18, 0, tzinfo=UTC)
SOURCE_AT = datetime(2026, 6, 23, 12, 0, tzinfo=UTC)
FLOW_STATUSES = ("pass", "watch", "blocked")

def d(value: str) -> Decimal:
    return Decimal(value)

def _api():
    return import_module("polymarket_alpha_lab.paper_research_packet_operator_flow_db_history")

def _config(**overrides):
    values = {
        "config_version": "paper-research-packet-operator-flow-db-history-v0",
        "min_report_count": 3,
        "max_blocked_flow_report_count": 0,
        "max_watch_flow_report_count": 0,
        "max_duplicate_generated_at_count": 0,
    }
    values.update(overrides)
    return _api().PaperResearchPacketOperatorFlowDbHistoryConfig(**values)

def _flow_report(
    *,
    generated_at: datetime = SOURCE_AT,
    flow_status: str = "pass",
    reason_codes: tuple[str, ...] | None = None,
) -> PaperResearchPacketOperatorFlowReport:
    reason_codes = reason_codes or (f"operator_flow_{flow_status}",)
    quality_status = "pass"
    history_status = "pass"
    quality_blocked_count = 0
    quality_watch_count = 0
    quality_pass_count = 3
    if flow_status == "blocked":
        quality_status = "blocked"
        quality_blocked_count = 1
        quality_watch_count = 0
        quality_pass_count = 2
    elif flow_status == "watch":
        quality_status = "watch"
        quality_blocked_count = 0
        quality_watch_count = 1
        quality_pass_count = 2
    return PaperResearchPacketOperatorFlowReport(
        generated_at=generated_at,
        config_version="paper-research-packet-operator-flow-v0",
        flow_status=flow_status,
        packet_generated_at=generated_at - timedelta(minutes=12),
        packet_config_version="paper-research-packet-v0",
        packet_persisted=True,
        packet_row_count=1,
        included_count=1,
        skipped_count=0,
        quality_generated_at=generated_at - timedelta(minutes=6),
        quality_config_version="paper-research-packet-quality-v0",
        quality_source_generated_at=generated_at - timedelta(minutes=12),
        quality_source_config_version="paper-research-packet-v0",
        quality_source_age_seconds=360,
        quality_included_share=d("1.000000"),
        quality_skipped_share=d("0.000000"),
        quality_persisted=True,
        quality_status=quality_status,
        quality_check_count=3,
        quality_pass_count=quality_pass_count,
        quality_watch_count=quality_watch_count,
        quality_blocked_count=quality_blocked_count,
        history_generated_at=generated_at - timedelta(minutes=1),
        history_config_version="paper-research-packet-quality-history-v0",
        history_source_report_count=3,
        history_first_source_generated_at=generated_at - timedelta(hours=2),
        history_latest_source_generated_at=generated_at - timedelta(minutes=6),
        history_latest_quality_status=quality_status,
        history_latest_source_age_seconds=360,
        history_latest_included_share=d("1.000000"),
        history_latest_skipped_share=d("0.000000"),
        history_duplicate_generated_at_count=0,
        history_status=history_status,
        reason_codes=tuple(sorted(reason_codes)),
    )

def _history(*reports: PaperResearchPacketOperatorFlowReport, **config_overrides):
    return _api().build_paper_research_packet_operator_flow_db_history_report(
        reports,
        config=_config(**config_overrides),
        generated_at=GENERATED_AT,
    )
```

Required test expectations:

```python
def test_operator_flow_db_history_empty_and_insufficient_reports_are_blocked():
    api = _api()
    empty = _history()
    assert empty.history_status == "blocked"
    assert empty.report_count == 0
    assert empty.first_report_generated_at is None
    assert empty.latest_report_generated_at is None
    assert empty.latest_flow_status is None
    assert empty.latest_packet_row_count is None
    assert empty.latest_quality_status is None
    assert empty.latest_history_status is None
    assert empty.flow_status_rows == tuple(
        api.PaperResearchPacketOperatorFlowDbHistoryStatusRow(status, 0)
        for status in FLOW_STATUSES
    )
    assert empty.duplicate_generated_at_count == 0
    assert empty.consecutive_latest_pass_count == 0
    assert empty.consecutive_latest_watch_count == 0
    assert empty.consecutive_latest_blocked_count == 0
    assert empty.latest_reason_codes == ()
    assert empty.reason_code_rows == ()
    assert empty.reason_codes == (
        "insufficient_paper_research_packet_operator_flow_history",
    )
    assert empty.paper_only is True
    assert empty.report_only is True
    assert empty.readonly is True

    report = _flow_report()
    insufficient = _history(report)
    assert insufficient.history_status == "blocked"
    assert insufficient.report_count == 1
    assert insufficient.first_report_generated_at == report.generated_at
    assert insufficient.latest_report_generated_at == report.generated_at
    assert insufficient.latest_flow_status == "pass"
    assert insufficient.latest_packet_row_count == 1
    assert insufficient.latest_quality_status == "pass"
    assert insufficient.latest_history_status == "pass"
    assert insufficient.latest_reason_codes == ("operator_flow_pass",)
    assert insufficient.reason_codes == (
        "insufficient_paper_research_packet_operator_flow_history",
    )

def test_operator_flow_db_history_passes_and_sorts_chronologically():
    first = _flow_report(generated_at=SOURCE_AT)
    middle = _flow_report(generated_at=SOURCE_AT + timedelta(hours=1))
    latest = _flow_report(generated_at=SOURCE_AT + timedelta(hours=2))
    history = _history(latest, first, middle)
    assert history.history_status == "pass"
    assert history.report_count == 3
    assert history.first_report_generated_at == first.generated_at
    assert history.latest_report_generated_at == latest.generated_at
    assert history.latest_flow_status == "pass"
    assert history.flow_status_rows == (
        _api().PaperResearchPacketOperatorFlowDbHistoryStatusRow("pass", 3),
        _api().PaperResearchPacketOperatorFlowDbHistoryStatusRow("watch", 0),
        _api().PaperResearchPacketOperatorFlowDbHistoryStatusRow("blocked", 0),
    )
    assert history.consecutive_latest_pass_count == 3
    assert history.consecutive_latest_watch_count == 0
    assert history.consecutive_latest_blocked_count == 0
    assert history.latest_reason_codes == ("operator_flow_pass",)
    assert history.reason_code_rows == (
        _api().PaperResearchPacketOperatorFlowDbHistoryReasonCodeRow(
            "operator_flow_pass",
            3,
        ),
    )
    assert history.reason_codes == (
        "paper_research_packet_operator_flow_db_history_passed",
    )

def test_operator_flow_db_history_status_precedence_blocks_over_watch():
    history = _history(
        _flow_report(generated_at=SOURCE_AT),
        _flow_report(
            generated_at=SOURCE_AT + timedelta(hours=1),
            flow_status="watch",
            reason_codes=("operator_flow_watch",),
        ),
        _flow_report(
            generated_at=SOURCE_AT + timedelta(hours=2),
            flow_status="blocked",
            reason_codes=("operator_flow_blocked",),
        ),
    )
    assert history.history_status == "blocked"
    assert history.latest_flow_status == "blocked"
    assert history.flow_status_rows == (
        _api().PaperResearchPacketOperatorFlowDbHistoryStatusRow("pass", 1),
        _api().PaperResearchPacketOperatorFlowDbHistoryStatusRow("watch", 1),
        _api().PaperResearchPacketOperatorFlowDbHistoryStatusRow("blocked", 1),
    )
    assert history.consecutive_latest_blocked_count == 1
    assert history.reason_codes == (
        "blocked_operator_flow_report_threshold_exceeded",
        "watch_operator_flow_report_threshold_exceeded",
    )

def test_operator_flow_db_history_watches_duplicate_generated_at():
    duplicate_at = SOURCE_AT + timedelta(hours=1)
    history = _history(
        _flow_report(generated_at=SOURCE_AT),
        _flow_report(generated_at=duplicate_at),
        _flow_report(generated_at=duplicate_at),
    )
    assert history.history_status == "watch"
    assert history.duplicate_generated_at_count == 1
    assert history.reason_codes == ("duplicate_generated_at_threshold_exceeded",)

def test_operator_flow_db_history_counts_latest_consecutive_status_only():
    history = _history(
        _flow_report(generated_at=SOURCE_AT, flow_status="watch", reason_codes=("operator_flow_watch",)),
        _flow_report(generated_at=SOURCE_AT + timedelta(hours=1)),
        _flow_report(generated_at=SOURCE_AT + timedelta(hours=2), flow_status="watch", reason_codes=("operator_flow_watch",)),
        _flow_report(generated_at=SOURCE_AT + timedelta(hours=3), flow_status="watch", reason_codes=("operator_flow_watch",)),
        min_report_count=4,
        max_watch_flow_report_count=4,
    )
    assert history.history_status == "pass"
    assert history.consecutive_latest_pass_count == 0
    assert history.consecutive_latest_watch_count == 2
    assert history.consecutive_latest_blocked_count == 0
```

Also include validation tests:
- dataclasses are frozen and reject hard flag overrides.
- config rejects non-positive `min_report_count` and negative thresholds.
- status/reason rows reject invalid statuses/counts.
- builder rejects non-list/tuple report collections, non-operator-flow reports, operator-flow subclasses, config subclasses, and datetime subclasses.
- reducer normalizes timezone-aware datetimes without mutating source report objects.

- [ ] **Step 2: Run test to verify RED**

Run:

```bash
.venv/bin/python -m pytest tests/test_paper_research_packet_operator_flow_db_history.py -q
```

Expected: fails because `polymarket_alpha_lab.paper_research_packet_operator_flow_db_history` does not exist.

- [ ] **Step 3: Implement minimal reducer**

Implementation requirements:
- Use `@dataclass(frozen=True)` for all public dataclasses.
- Use `FLOW_STATUSES` order exactly: `("pass", "watch", "blocked")`.
- Status row fields: `flow_status: str`, `status_count: int`, hard flags.
- Reason row fields: `reason_code: str`, `report_count: int`, hard flags.
- Report fields:
  - `generated_at: datetime`
  - `config_version: str`
  - `history_status: str`
  - `report_count: int`
  - `first_report_generated_at: datetime | None`
  - `latest_report_generated_at: datetime | None`
  - `latest_flow_status: str | None`
  - `latest_packet_row_count: int | None`
  - `latest_quality_status: str | None`
  - `latest_history_status: str | None`
  - `flow_status_rows: tuple[PaperResearchPacketOperatorFlowDbHistoryStatusRow, ...]`
  - `duplicate_generated_at_count: int`
  - `consecutive_latest_pass_count: int`
  - `consecutive_latest_watch_count: int`
  - `consecutive_latest_blocked_count: int`
  - `latest_reason_codes: tuple[str, ...]`
  - `reason_code_rows: tuple[PaperResearchPacketOperatorFlowDbHistoryReasonCodeRow, ...]`
  - `reason_codes: tuple[str, ...]`
  - hard flags
- Chronological sort must sort by `(generated_at, original_input_index)`.
- Duplicate timestamp count is sum of extra rows over one for each duplicate `generated_at`.
- Reason-code rows count each distinct report-level reason code once per report and sort by `(-report_count, reason_code)`.
- Latest consecutive counts walk backward from the latest chronological report and count only rows with the same latest `flow_status`.
- `history_status` logic:
  - fewer than `config.min_report_count` -> `blocked`
  - blocked count greater than `config.max_blocked_flow_report_count` -> `blocked`
  - watch count greater than `config.max_watch_flow_report_count` -> `watch`
  - duplicate count greater than `config.max_duplicate_generated_at_count` -> `watch`
  - otherwise `pass`
- `reason_codes` logic:
  - insufficient -> `("insufficient_paper_research_packet_operator_flow_history",)`
  - blocked count threshold -> include `"blocked_operator_flow_report_threshold_exceeded"`
  - watch count threshold -> include `"watch_operator_flow_report_threshold_exceeded"`
  - duplicate threshold -> include `"duplicate_generated_at_threshold_exceeded"`
  - no threshold findings -> include `"paper_research_packet_operator_flow_db_history_passed"`
  - final tuple must be sorted and unique.
- Validate exact public dataclass types and hard flags.
- Validate source report consistency enough to reject broken hard flags, noncanonical config versions, invalid counts, invalid flow statuses, noncanonical reason codes, duplicate/unsorted reason code tuples, and incoherent packet/quality/history timeline.

- [ ] **Step 4: Run focused tests until green**

Run:

```bash
.venv/bin/python -m pytest tests/test_paper_research_packet_operator_flow_db_history.py -q
```

Expected: all tests pass.

---

### Task 2: Operator-Flow DB History Loader

**Files:**
- Create: `src/polymarket_alpha_lab/paper_research_packet_operator_flow_db_history_load.py`
- Test: `tests/test_paper_research_packet_operator_flow_db_history_load.py`

**Interfaces:**
- Consumes Task 1 public reducer API.
- Consumes `load_paper_research_packet_operator_flow_reports` from `polymarket_alpha_lab.paper_research_packet_operator_flow_store`.
- Produces `load_paper_research_packet_operator_flow_db_history_report(connection: object, *, config_version: str | None = None, flow_status: str | None = None, limit: int | None, table_name: str, config: PaperResearchPacketOperatorFlowDbHistoryConfig, generated_at: datetime) -> PaperResearchPacketOperatorFlowDbHistoryReport`.

- [ ] **Step 1: Write failing loader tests**

Required tests:
- injected fake store receives `connection`, `config_version`, `flow_status`, `limit`, `table_name`.
- returned DB-descending reports are reversed before reaching the reducer.
- config must be exact `PaperResearchPacketOperatorFlowDbHistoryConfig`; subclass and object are rejected before store call.
- loader does not call `commit`, `rollback`, or `close`; it only delegates to store and reducer.

Patch `polymarket_alpha_lab.paper_research_packet_operator_flow_db_history_load.load_paper_research_packet_operator_flow_reports` in tests after importing the loader module.

- [ ] **Step 2: Run test to verify RED**

Run:

```bash
.venv/bin/python -m pytest tests/test_paper_research_packet_operator_flow_db_history_load.py -q
```

Expected: fails because the loader module does not exist.

- [ ] **Step 3: Implement loader**

Required module body:

```python
"""Readback loader for persisted paper research packet operator-flow DB history."""

from __future__ import annotations

from datetime import datetime

from polymarket_alpha_lab.paper_research_packet_operator_flow_db_history import (
    PaperResearchPacketOperatorFlowDbHistoryConfig,
    PaperResearchPacketOperatorFlowDbHistoryReport,
    build_paper_research_packet_operator_flow_db_history_report,
)
from polymarket_alpha_lab.paper_research_packet_operator_flow_store import (
    load_paper_research_packet_operator_flow_reports,
)

__all__ = ("load_paper_research_packet_operator_flow_db_history_report",)

def load_paper_research_packet_operator_flow_db_history_report(
    connection: object,
    *,
    config_version: str | None = None,
    flow_status: str | None = None,
    limit: int | None,
    table_name: str,
    config: PaperResearchPacketOperatorFlowDbHistoryConfig,
    generated_at: datetime,
) -> PaperResearchPacketOperatorFlowDbHistoryReport:
    if type(config) is not PaperResearchPacketOperatorFlowDbHistoryConfig:
        raise ValueError("config must be a PaperResearchPacketOperatorFlowDbHistoryConfig")

    loaded_reports = load_paper_research_packet_operator_flow_reports(
        connection,
        config_version=config_version,
        flow_status=flow_status,
        limit=limit,
        table_name=table_name,
    )
    chronological_reports = tuple(reversed(tuple(loaded_reports)))
    return build_paper_research_packet_operator_flow_db_history_report(
        chronological_reports,
        config=config,
        generated_at=generated_at,
    )
```

- [ ] **Step 4: Run focused tests until green**

Run:

```bash
.venv/bin/python -m pytest tests/test_paper_research_packet_operator_flow_db_history_load.py -q
```

Expected: all tests pass.

---

### Task 3: CLI Command And Runtime Read Path

**Files:**
- Modify: `src/polymarket_alpha_lab/cli.py`
- Test: `tests/test_cli_paper_research_packet_operator_flow_db_history.py`

**Interfaces:**
- Consumes Task 1 `PaperResearchPacketOperatorFlowDbHistoryConfig`.
- Consumes Task 2 `load_paper_research_packet_operator_flow_db_history_report`.
- Consumes existing env config `from_paper_research_packet_operator_flow_db_env`.
- Adds optional injectable `paper_research_packet_operator_flow_db_history_runner` to `main(...)`.
- Adds helper `_run_paper_research_packet_operator_flow_db_history(...)`.
- Adds printer `_print_paper_research_packet_operator_flow_db_history_summary(report)`.

- [ ] **Step 1: Use CodeGraph to inspect local CLI import/type-alias/command/helper patterns**

Run before editing:

```bash
codegraph explore "paper_research_packet_quality_db_history_runner _run_paper_research_packet_quality_db_history _print_paper_research_packet_quality_history_summary from_paper_research_packet_operator_flow_db_env"
```

- [ ] **Step 2: Write failing CLI tests**

Required command constant:

```python
COMMAND = "paper-research-packet-operator-flow-db-history"
```

Test cases must cover:
- command requires existing operator-flow DB env enabled and does not construct Polymarket client when disabled.
- `--limit 0` and negative limit fail before env, runner, or psycopg connect.
- helper rejects non-positive/non-int/bool/string limit before runner/connect.
- injected runner path passes `dsn`, `table_name`, `limit`, exact config type, UTC `generated_at`; stdout redacts DSN/table.
- default helper path calls `psycopg.connect(dsn, autocommit=True)`, calls loader with `limit`, `table_name`, config, UTC generated_at, closes connection once, and never commits/rolls back.
- runner failure output redacts DSN, full schema/table name, table tail, `payload_json`, market question, and sha256 hash.
- no `--dsn`, `--table`, or `--persist` flags are accepted for this command.

Expected summary output shape:

```text
paper-research-packet-operator-flow-db-history: history_status=watch report_count=3 first_report_generated_at=2026-06-23T08:00:00+00:00 latest_report_generated_at=2026-06-23T12:00:00+00:00 latest_flow_status=watch latest_packet_row_count=3 latest_quality_status=watch latest_history_status=pass pass=2 watch=1 blocked=0 duplicate_generated_at_count=1 consecutive_latest_pass_count=0 consecutive_latest_watch_count=1 consecutive_latest_blocked_count=0
flow_status_rows: pass=2 watch=1 blocked=0
latest_reason_codes: operator_flow_watch
reason_code_rows: operator_flow_pass=2 operator_flow_watch=1
reason_codes: duplicate_generated_at_threshold_exceeded
```

- [ ] **Step 3: Run CLI tests to verify RED**

Run:

```bash
.venv/bin/python -m pytest tests/test_cli_paper_research_packet_operator_flow_db_history.py -q
```

Expected: fail because command/runner/helper/printer are missing.

- [ ] **Step 4: Implement CLI changes**

Implementation requirements:
- Add imports for the new config/report only where existing quality history imports live.
- Add type alias for `PaperResearchPacketOperatorFlowDbHistoryRunner` matching existing runner patterns.
- Add `paper_research_packet_operator_flow_db_history_runner: PaperResearchPacketOperatorFlowDbHistoryRunner | None = None` after `paper_research_packet_operator_flow_db_sink` in `main`.
- Add parser:

```python
paper_research_packet_operator_flow_db_history = subparsers.add_parser(
    "paper-research-packet-operator-flow-db-history",
)
paper_research_packet_operator_flow_db_history.add_argument(
    "--limit",
    type=int,
    default=25,
)
```

- Do not add DSN/table/persist/config-version/flow-status flags.
- Branch behavior:
  - validate `args.limit` positive before env.
  - load `from_paper_research_packet_operator_flow_db_env()`.
  - require `config.enabled`.
  - call `_run_paper_research_packet_operator_flow_db_history(...)`.
  - use `PaperResearchPacketOperatorFlowDbHistoryConfig()`.
  - pass `datetime.now(UTC)`.
  - catch failures via existing redacted DB read error helper or equivalent redaction path.
  - print summary.
- Helper default path:
  - validate limit before runner/connect.
  - if runner injected, call it with keyword args `dsn`, `table_name`, `limit`, `config`, `generated_at`.
  - otherwise import `psycopg`, connect with `autocommit=True`, call Task 2 loader, close connection in `finally`.
  - no commit/rollback.
- Summary printer:
  - First line preserves command prefix and includes all scalar fields listed above.
  - Second line prints `flow_status_rows: pass=N watch=N blocked=N`.
  - Third line prints `latest_reason_codes: none` when empty, otherwise space-separated codes.
  - Fourth line prints `reason_code_rows: none` when empty, otherwise `reason_code=count` space-separated in reducer order.
  - Fifth line prints `reason_codes: ...`.
- Ensure failures do not leak DSN/table/payload/question/hash, using existing redaction helper patterns.

- [ ] **Step 5: Run focused CLI tests until green**

Run:

```bash
.venv/bin/python -m pytest tests/test_cli_paper_research_packet_operator_flow_db_history.py -q
```

Expected: all tests pass.

---

### Task 4: Documentation And Command Surface Check

**Files:**
- Modify: `README.md`
- Optionally modify: `.env.example` only if it does not already document the operator-flow DB env variables.
- Optionally modify: `tests/test_cli_paper_research_packet_operator_flow_scope.py` only if an existing command-scope test file already enumerates operator-flow commands.

**Interfaces:**
- Consumes command from Task 3.
- Produces README guidance only; no runtime behavior.

- [ ] **Step 1: Use CodeGraph or existing docs sections to locate paper research packet/operator-flow docs**

Run before editing:

```bash
codegraph explore "README paper research packet operator flow DB env paper-research-packet-operator-flow"
```

- [ ] **Step 2: Write or update documentation/surface tests first if applicable**

If there is an existing scope test for forbidden CLI flags, add assertions that `paper-research-packet-operator-flow-db-history` does not expose `--dsn`, `--table`, or `--persist`.

- [ ] **Step 3: Run doc/scope focused tests**

Run the relevant focused test if changed:

```bash
.venv/bin/python -m pytest tests/test_cli_paper_research_packet_operator_flow_scope.py -q
```

- [ ] **Step 4: Update README**

Add a short section near the existing operator-flow DB persistence docs:

```markdown
Operator-flow DB history is read-only and uses the same env-only operator-flow DB configuration as persistence:

```bash
POLYMARKET_ALPHA_LAB_PAPER_RESEARCH_PACKET_OPERATOR_FLOW_DB_ENABLED=true \
POLYMARKET_ALPHA_LAB_PAPER_RESEARCH_PACKET_OPERATOR_FLOW_DB_DSN=postgresql://... \
polymarket-alpha-lab paper-research-packet-operator-flow-db-history --limit 25
```

The command prints persisted operator-flow stability signals such as pass/watch/blocked counts, duplicate report timestamps, latest consecutive status streaks, latest reason codes, and threshold reason codes. It does not accept DSN/table/persist flags and does not perform live trading or DB writes.
```

- [ ] **Step 5: Verify docs/scope changes**

Run:

```bash
.venv/bin/python -m pytest tests/test_cli_paper_research_packet_operator_flow_scope.py -q
```

Expected: passes if the scope test exists and was modified. If no scope test was modified, report README-only change.

---

## Integration And Verification

After all tasks are integrated:

```bash
.venv/bin/python -m pytest tests/test_paper_research_packet_operator_flow_db_history.py tests/test_paper_research_packet_operator_flow_db_history_load.py -q
.venv/bin/python -m pytest tests/test_cli_paper_research_packet_operator_flow_db_history.py -q
.venv/bin/python -m pytest tests/test_paper_research_packet_operator_flow*.py tests/test_supabase_paper_research_packet_operator_flow_config.py -q
.venv/bin/python -m compileall -q src tests
.venv/bin/python -m pytest -q
git diff --check
codegraph sync
```

OpenCode review:

```bash
BASE_SHA="$(git merge-base origin/main HEAD)"
REVIEW_PACKAGE="$(/home/ubuntu/.codex/plugins/cache/superpowers-local/superpowers/6.0.3/skills/subagent-driven-development/scripts/review-package "$BASE_SHA" HEAD)"
opencode run "Read-only review of the operator-flow DB history readback node. Check Phase 1 boundaries, env-only DB config, redaction, no live trading/auth/order/signer behavior, exact-type/frozen dataclass validation, Decimal-only posture, and CLI read-only behavior. Report Critical, Important, and Minor findings." -f "$REVIEW_PACKAGE" --dir /home/ubuntu/polymarket-alpha-lab -m zhipuai-coding-plan/glm-5.2 --variant max
```

Commit and push after clean review:

```bash
git add src tests README.md docs/superpowers/plans/2026-06-23-paper-research-packet-operator-flow-db-history.md .superpowers/sdd/progress.md
git commit -m "feat: add operator-flow DB history readback"
git push origin main
```

Update ledger:

```markdown
Paper research packet operator flow DB history readback: complete (commit recorded after push, OpenCode review clean, full pytest counted after verification, pushed origin/main).
```
