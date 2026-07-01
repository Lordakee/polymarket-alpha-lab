from __future__ import annotations

import builtins
import importlib
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from types import ModuleType, SimpleNamespace
from typing import Any

from polymarket_alpha_lab.team_diagnostics_snapshot_history_cli_format import (
    format_team_diagnostics_snapshot_history_cli_stdout,
)


@dataclass(frozen=True)
class HistoryReport:
    status: str
    snapshot_count: int
    required_snapshot_count: int
    earliest_generated_at: datetime | None
    latest_generated_at: datetime | None
    span_seconds: int
    status_counts: tuple[tuple[str, int], ...]
    evidence_quality_average_delta: Decimal
    memory_eligible_delta: int
    settled_calibration_delta: int
    duplicate_latest_generated_at: bool
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


def test_format_team_diagnostics_snapshot_history_cli_stdout_formats_populated_report() -> None:
    report = HistoryReport(
        status="insufficient_history",
        snapshot_count=2,
        required_snapshot_count=3,
        earliest_generated_at=datetime(2026, 7, 1, 8, 30, tzinfo=UTC),
        latest_generated_at=datetime(2026, 7, 1, 9, 45, 15, tzinfo=UTC),
        span_seconds=4515,
        status_counts=(("pass", 1), ("watch", 2)),
        evidence_quality_average_delta=Decimal("0.125"),
        memory_eligible_delta=-1,
        settled_calibration_delta=4,
        duplicate_latest_generated_at=True,
        reason_codes=("insufficient_history", "duplicate_latest_generated_at"),
    )

    stdout = format_team_diagnostics_snapshot_history_cli_stdout(report)

    assert stdout.startswith("team-diagnostics-snapshot-history:")
    assert stdout == (
        "team-diagnostics-snapshot-history: "
        "status=insufficient_history "
        "snapshot_count=2 "
        "required_snapshot_count=3 "
        "earliest_generated_at=2026-07-01T08:30:00+00:00 "
        "latest_generated_at=2026-07-01T09:45:15+00:00 "
        "span_seconds=4515 "
        "status_counts=pass:1,watch:2 "
        "evidence_quality_average_delta=0.125 "
        "memory_eligible_delta=-1 "
        "settled_calibration_delta=4 "
        "duplicate_latest_generated_at=True "
        "reason_codes=insufficient_history,duplicate_latest_generated_at "
        "paper_only=True "
        "report_only=True "
        "readonly=True\n"
    )


def test_format_team_diagnostics_snapshot_history_cli_stdout_prints_none_for_empty_reason_codes() -> None:
    report = HistoryReport(
        status="observed",
        snapshot_count=3,
        required_snapshot_count=2,
        earliest_generated_at=None,
        latest_generated_at=None,
        span_seconds=0,
        status_counts=(),
        evidence_quality_average_delta=Decimal("0"),
        memory_eligible_delta=0,
        settled_calibration_delta=0,
        duplicate_latest_generated_at=False,
        reason_codes=(),
        paper_only=True,
        report_only=True,
        readonly=True,
    )

    stdout = format_team_diagnostics_snapshot_history_cli_stdout(report)

    assert "reason_codes=none" in stdout
    assert "status_counts=none" in stdout
    assert "earliest_generated_at=none" in stdout
    assert "latest_generated_at=none" in stdout


def test_format_team_diagnostics_snapshot_history_cli_stdout_prints_none_for_none_collections() -> None:
    report = SimpleNamespace(
        status="observed",
        snapshot_count=1,
        required_snapshot_count=2,
        earliest_generated_at=None,
        latest_generated_at=None,
        span_seconds=0,
        status_counts=None,
        evidence_quality_average_delta=Decimal("0"),
        memory_eligible_delta=0,
        settled_calibration_delta=0,
        duplicate_latest_generated_at=False,
        reason_codes=None,
        paper_only=True,
        report_only=True,
        readonly=True,
    )

    stdout = format_team_diagnostics_snapshot_history_cli_stdout(report)

    assert "status_counts=none" in stdout
    assert "reason_codes=none" in stdout


def test_formatter_imports_no_db_env_network_or_filesystem_modules(
    monkeypatch: Any,
) -> None:
    disallowed_import_roots = {
        "asyncpg",
        "dotenv",
        "os",
        "pathlib",
        "psycopg",
        "psycopg2",
        "requests",
        "socket",
        "sqlite3",
        "subprocess",
    }
    imported_roots: list[str] = []
    original_import = builtins.__import__

    def tracking_import(
        name: str,
        globals: dict[str, Any] | None = None,
        locals: dict[str, Any] | None = None,
        fromlist: tuple[str, ...] = (),
        level: int = 0,
    ) -> ModuleType:
        if level == 0:
            imported_roots.append(name.partition(".")[0])
        return original_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", tracking_import)
    sys.modules.pop("polymarket_alpha_lab.team_diagnostics_snapshot_history_cli_format", None)

    importlib.import_module("polymarket_alpha_lab.team_diagnostics_snapshot_history_cli_format")

    assert set(imported_roots).isdisjoint(disallowed_import_roots)
