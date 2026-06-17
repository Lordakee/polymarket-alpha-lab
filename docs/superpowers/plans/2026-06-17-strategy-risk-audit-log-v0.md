# Strategy Risk Audit Log v0 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an opt-in local JSONL log for Strategy Risk Audit reports and wire it into `strategy-audit` plus `run --strategy-audit-preflight`.

**Architecture:** Keep `strategy_risk_audit.py` pure. Add a new `strategy_risk_audit_log.py` module that only serializes/deserializes already-built `PaperStrategyRiskAuditReport` values and exposes its class through that module's own `__all__`. Do not export the log class from the package root, because the package-root Strategy Risk Audit API is deliberately limited to pure report math. Wire CLI persistence through an optional `--strategy-audit-log` path, preserving default behavior and all Phase 1 boundaries.

**Tech Stack:** Python stdlib `dataclasses`, `json`, `pathlib`, existing `json_recovery.from_jsonable`, pytest, existing CLI injection hooks.

---

### Task 1: RED Log Module Tests

**Files:**
- Create: `tests/test_strategy_risk_audit_log.py`
- Later create: `src/polymarket_alpha_lab/strategy_risk_audit_log.py`

- [ ] **Step 1: Add round-trip and validation tests**

Create `tests/test_strategy_risk_audit_log.py` with tests that import the not-yet-created `PaperStrategyRiskAuditLog`:

```python
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from polymarket_alpha_lab.strategy_risk_audit import (
    PaperStrategyRiskAuditGateResult,
    PaperStrategyRiskAuditReport,
)
from polymarket_alpha_lab.strategy_risk_audit_log import PaperStrategyRiskAuditLog


GENERATED_AT = datetime(2026, 6, 17, 14, 0, tzinfo=UTC)


def _report(status="audit_ready") -> PaperStrategyRiskAuditReport:
    statuses = {
        "audit_ready": ("pass", 6, 0, 0),
        "insufficient_evidence": ("incomplete", 0, 0, 6),
        "blocked_by_risk": ("fail", 0, 6, 0),
    }
    gate_status, pass_count, fail_count, incomplete_count = statuses[status]
    return PaperStrategyRiskAuditReport(
        generated_at=GENERATED_AT,
        config_version="strategy-risk-audit-v0",
        status=status,
        gate_count=6,
        pass_count=pass_count,
        fail_count=fail_count,
        incomplete_count=incomplete_count,
        gate_results=(
            PaperStrategyRiskAuditGateResult(
                "paper_history",
                gate_status,
                "mature",
                observed_value="cycle_count=25",
                threshold="min_cycle_count=20",
            ),
            PaperStrategyRiskAuditGateResult(
                "settlement_evidence",
                gate_status,
                "settled",
                observed_value=12,
                threshold=10,
            ),
            PaperStrategyRiskAuditGateResult(
                "forecast_quality",
                gate_status,
                "calibrated",
                observed_value=Decimal("0.120000"),
                threshold=Decimal("0.300000"),
            ),
            PaperStrategyRiskAuditGateResult(
                "cost_discipline",
                gate_status,
                "costs",
                observed_value=Decimal("0.020000"),
                threshold=Decimal("0.050000"),
            ),
            PaperStrategyRiskAuditGateResult(
                "nav_drawdown",
                gate_status,
                "drawdown",
                observed_value=Decimal("0.010000"),
                threshold=Decimal("0.050000"),
            ),
            PaperStrategyRiskAuditGateResult(
                "open_exposure",
                gate_status,
                "exposure",
                observed_value="open_position_count=1",
                threshold="max_no_exit_depth_count=0",
            ),
        ),
    )


def test_strategy_risk_audit_log_round_trips_reports_and_skips_blank_lines(tmp_path):
    path = tmp_path / "nested" / "strategy-audits.jsonl"
    report = _report()

    PaperStrategyRiskAuditLog(path).append(report)
    with path.open("a", encoding="utf-8") as handle:
        handle.write("\n")

    assert PaperStrategyRiskAuditLog.read(path) == (report,)


def test_strategy_risk_audit_log_empty_file_returns_empty_tuple(tmp_path):
    path = tmp_path / "strategy-audits.jsonl"
    path.touch()

    assert PaperStrategyRiskAuditLog.read(path) == ()


def test_strategy_risk_audit_log_invalid_json_reports_line_number(tmp_path):
    path = tmp_path / "strategy-audits.jsonl"
    path.write_text("\nnot json\n", encoding="utf-8")

    with pytest.raises(ValueError, match="strategy risk audit log line 2"):
        PaperStrategyRiskAuditLog.read(path)


def test_strategy_risk_audit_log_rejects_invalid_append_without_creating_file(tmp_path):
    path = tmp_path / "strategy-audits.jsonl"

    with pytest.raises(ValueError, match="report must be a PaperStrategyRiskAuditReport"):
        PaperStrategyRiskAuditLog(path).append(object())  # type: ignore[arg-type]

    assert not path.exists()
```

- [ ] **Step 2: Run RED tests**

Run:

```bash
.venv/bin/python -m pytest tests/test_strategy_risk_audit_log.py -q
```

Expected: collection fails with `ModuleNotFoundError` for `strategy_risk_audit_log`.

### Task 2: GREEN Log Module

**Files:**
- Create: `src/polymarket_alpha_lab/strategy_risk_audit_log.py`
- Test: `tests/test_strategy_risk_audit_log.py`

- [ ] **Step 1: Implement the JSONL log module**

Create `src/polymarket_alpha_lab/strategy_risk_audit_log.py` with:

```python
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from polymarket_alpha_lab.json_recovery import from_jsonable
from polymarket_alpha_lab.strategy_risk_audit import PaperStrategyRiskAuditReport

__all__ = ("PaperStrategyRiskAuditLog",)


@dataclass(frozen=True)
class PaperStrategyRiskAuditLog:
    """Append/read local Strategy Risk Audit JSONL reports."""

    path: Path | str

    def __post_init__(self) -> None:
        object.__setattr__(self, "path", _normalize_log_path(self.path))

    def append(self, report: PaperStrategyRiskAuditReport) -> None:
        if type(report) is not PaperStrategyRiskAuditReport:
            raise ValueError("report must be a PaperStrategyRiskAuditReport")
        line = json.dumps(
            _json_ready(asdict(report)),
            allow_nan=False,
            sort_keys=True,
        ) + "\n"
        _validate_log_parent(self.path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(line)

    @staticmethod
    def read(path: Path | str) -> tuple[PaperStrategyRiskAuditReport, ...]:
        target = Path(path)
        records: list[PaperStrategyRiskAuditReport] = []
        with target.open("r", encoding="utf-8") as handle:
            for line_number, raw_line in enumerate(handle, start=1):
                stripped = raw_line.strip()
                if not stripped:
                    continue
                try:
                    row = json.loads(stripped)
                except json.JSONDecodeError as exc:
                    raise ValueError(
                        "strategy risk audit log line "
                        f"{line_number} is not valid JSON: {exc}",
                    ) from exc
                records.append(from_jsonable(PaperStrategyRiskAuditReport, row))
        return tuple(records)


def _normalize_log_path(path: Path | str) -> Path:
    if not isinstance(path, (Path, str)):
        raise ValueError("path must be a Path or string")
    if isinstance(path, str) and not path.strip():
        raise ValueError("path must be nonblank")
    target = Path(path)
    if target.exists() and target.is_dir():
        raise ValueError("path must be a file path")
    return target


def _validate_log_parent(path: Path) -> None:
    if path.parent.exists() and not path.parent.is_dir():
        raise ValueError("log parent must be a directory")


def _json_ready(value: Any) -> Any:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        return {key: _json_ready(item) for key, item in value.items()}
    return value
```

- [ ] **Step 2: Preserve the pure audit package-root API**

Do not modify `src/polymarket_alpha_lab/__init__.py` or
`tests/test_init.py` for this log module. `tests/test_strategy_risk_audit_scope.py`
expects package-root `PaperStrategyRiskAudit*` exports to stay limited to the
pure Strategy Risk Audit report API.

- [ ] **Step 3: Run GREEN tests**

Run:

```bash
.venv/bin/python -m pytest tests/test_strategy_risk_audit_log.py tests/test_strategy_risk_audit_scope.py -q
```

Expected: pass.

### Task 3: RED CLI Persistence Tests

**Files:**
- Modify: `tests/test_cli.py`
- Later modify: `src/polymarket_alpha_lab/cli.py`

- [ ] **Step 1: Add CLI tests for explicit audit logging**

Add tests near the existing strategy-audit and run-preflight CLI tests:

```python
from polymarket_alpha_lab.strategy_risk_audit_log import PaperStrategyRiskAuditLog
```

Test cases:

- `test_strategy_audit_cli_appends_strategy_audit_log_without_client`
  - run `strategy-audit --strategy-audit-log <path>` with local inputs
  - assert exit `0`
  - assert `PaperStrategyRiskAuditLog.read(path)` returns one report with
    `gate_count == 6`
  - forbidden `client_factory` must not be constructed

- `test_run_cli_strategy_audit_preflight_appends_blocked_audit_log_before_client`
  - fake audit runner returns `blocked_by_risk`
  - pass `--strategy-audit-log <path>`
  - assert exit `1`
  - assert log has one `blocked_by_risk` report
  - forbidden `client_factory` and `loop_runner` must not be called

- `test_run_cli_json_config_sets_strategy_audit_log_path`
  - config contains `"strategy_audit_preflight": true` and `"strategy_audit_log": "<path>"`
  - fake audit runner returns `audit_ready`
  - assert exit `0`
  - assert log has one `audit_ready` report

- `test_run_cli_strategy_audit_log_is_inert_without_preflight`
  - pass `run --strategy-audit-log <path>` without preflight
  - assert exit `0`
  - assert log path does not exist

- [ ] **Step 2: Run RED CLI tests**

Run:

```bash
.venv/bin/python -m pytest tests/test_cli.py -k "strategy_audit_log" -q
```

Expected: fail because the CLI does not recognize `--strategy-audit-log` yet.

### Task 4: GREEN CLI Persistence

**Files:**
- Modify: `src/polymarket_alpha_lab/cli.py`
- Modify: `strategy.example.json`
- Test: `tests/test_cli.py`

- [ ] **Step 1: Wire the CLI flag and JSON config**

In `cli.py`:

- import `PaperStrategyRiskAuditLog`
- add `--strategy-audit-log` to `strategy-audit`
- add `--strategy-audit-log` to `run`
- add `"strategy_audit_log": "strategy_audit_log"` to `_apply_json_config`
- include `"strategy_audit_log"` in the Path conversion set

- [ ] **Step 2: Append audit reports at the two existing report-build points**

In the `strategy-audit` command branch, after `_run_strategy_audit(...)` returns
and before printing, append when `args.strategy_audit_log is not None`.

In the `run` branch, inside the preflight block after `_run_strategy_audit(...)`
returns and before status evaluation, append when
`args.strategy_audit_log is not None`.

Do not call `client_factory()` before this preflight append.

- [ ] **Step 3: Update example config conservatively**

Add:

```json
"strategy_audit_log": "artifacts/strategy-audits.jsonl"
```

Keep `"strategy_audit_preflight": false` so copying the example still does not
write audit logs until the user opts in.

- [ ] **Step 4: Run GREEN CLI tests**

Run:

```bash
.venv/bin/python -m pytest tests/test_cli.py -k "strategy_audit_log or run_cli_strategy_audit_preflight or json_config_enables_strategy_audit_preflight" -q
```

Expected: pass.

### Task 5: Docs, Verification, Review, Commit

**Files:**
- Modify: `README.md`
- Modify: `docs/superpowers/specs/2026-06-17-strategy-audit-cli-v0.md`
- Modify: `docs/superpowers/specs/2026-06-17-continuous-run-strategy-audit-preflight-v0.md`
- Modify: `docs/research/validation-gates.md` if needed

- [ ] **Step 1: Document the optional log**

Update docs to say `--strategy-audit-log` writes a local JSONL evidence artifact
only when explicitly supplied, and does not imply approval, ranking,
recommendation, trade instruction, financial advice, or live execution.

- [ ] **Step 2: Run targeted tests**

Run:

```bash
.venv/bin/python -m pytest tests/test_strategy_risk_audit_log.py tests/test_cli.py tests/test_strategy_risk_audit_scope.py -q
```

Expected: pass.

- [ ] **Step 3: Run full verification**

Run:

```bash
.venv/bin/python -m pytest -q
git diff --check
rg -n "ghp_[A-Za-z0-9_]{20,}|sk-[A-Za-z0-9]{20,}|xox[baprs]-[A-Za-z0-9-]{20,}|AKIA[0-9A-Z]{16}|-----BEGIN (RSA |EC |OPENSSH |)PRIVATE KEY-----" --glob '!docs/superpowers/plans/**' --glob '!docs/superpowers/specs/**' .
codegraph sync && codegraph status .
```

Expected: pytest passes, diff check exits `0`, secret scan exits `1` with no
matches, CodeGraph is up to date.

- [ ] **Step 4: Run Claude post-stage audit**

Stage the diff and run Claude Code with `claude-opus-4-8`, effort `max`, asking
for Phase 1 boundary, CLI ordering, JSON config, tests, docs, and regression
risk review. Fix any Critical/Important findings.

- [ ] **Step 5: Commit locally**

Commit:

```bash
git commit -m "feat: log strategy audit reports"
```

Do not push `origin/main` unless the user explicitly overrides the repository
rule keeping it pinned.
