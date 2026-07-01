from __future__ import annotations

import builtins
import importlib
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from types import ModuleType, SimpleNamespace
from typing import Any

from polymarket_alpha_lab.team_diagnostics_snapshot_history_gate_cli_format import (
    format_team_diagnostics_snapshot_history_gate_cli_stdout,
)


@dataclass(frozen=True)
class ReasonCodeCount:
    reason_code: str
    report_count: int


@dataclass(frozen=True)
class GateReport:
    gate_status: str
    recommended_next_step: str
    source_config_version: str
    source_generated_at: datetime | None
    source_snapshot_count: int
    source_required_snapshot_count: int
    source_status: str
    source_span_seconds: int
    source_status_counts: tuple[tuple[str, int], ...] | None
    source_reason_codes: tuple[str, ...] | None
    latest_snapshot_age_seconds: int | None
    reason_code_counts: tuple[ReasonCodeCount, ...] | None
    evidence_quality_average_delta: Decimal
    memory_eligible_delta: int
    settled_calibration_delta: int
    duplicate_latest_generated_at: bool
    reason_codes: tuple[str, ...] | None
    generated_at: datetime = datetime(2026, 7, 1, 10, 15, tzinfo=UTC)
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


def test_format_team_diagnostics_snapshot_history_gate_cli_stdout_formats_populated_report() -> None:
    report = GateReport(
        gate_status="watch",
        recommended_next_step="collect_more_snapshots",
        source_config_version="team-diagnostics-snapshot-history-v0",
        source_generated_at=datetime(2026, 7, 1, 9, 59, tzinfo=UTC),
        source_snapshot_count=2,
        source_required_snapshot_count=3,
        source_status="insufficient_history",
        source_span_seconds=7200,
        source_status_counts=(("observed", 1), ("insufficient_history", 1)),
        source_reason_codes=("insufficient_history",),
        latest_snapshot_age_seconds=900,
        reason_code_counts=(
            ReasonCodeCount("insufficient_history", 1),
            ReasonCodeCount("duplicate_latest_generated_at", 1),
        ),
        evidence_quality_average_delta=Decimal("0.125"),
        memory_eligible_delta=-1,
        settled_calibration_delta=4,
        duplicate_latest_generated_at=True,
        reason_codes=("insufficient_history", "duplicate_latest_generated_at"),
    )

    stdout = format_team_diagnostics_snapshot_history_gate_cli_stdout(report)

    assert stdout.startswith("team-diagnostics-snapshot-history-gate:")
    assert stdout == (
        "team-diagnostics-snapshot-history-gate: "
        "gate_status=watch "
        "recommended_next_step=collect_more_snapshots "
        "source_config_version=team-diagnostics-snapshot-history-v0 "
        "source_generated_at=2026-07-01T09:59:00+00:00 "
        "source_snapshot_count=2 "
        "source_required_snapshot_count=3 "
        "source_status=insufficient_history "
        "source_span_seconds=7200 "
        "source_status_counts=observed:1,insufficient_history:1 "
        "source_reason_codes=insufficient_history "
        "latest_snapshot_age_seconds=900 "
        "reason_code_counts=insufficient_history:1,duplicate_latest_generated_at:1 "
        "evidence_quality_average_delta=0.125 "
        "memory_eligible_delta=-1 "
        "settled_calibration_delta=4 "
        "duplicate_latest_generated_at=True "
        "reason_codes=insufficient_history,duplicate_latest_generated_at "
        "paper_only=True "
        "report_only=True "
        "readonly=True\n"
    )


def test_format_team_diagnostics_snapshot_history_gate_cli_stdout_prints_none_for_empty_reason_collections() -> None:
    report = GateReport(
        gate_status="pass",
        recommended_next_step="continue",
        source_config_version="team-diagnostics-snapshot-history-v0",
        source_generated_at=None,
        source_snapshot_count=3,
        source_required_snapshot_count=2,
        source_status="observed",
        source_span_seconds=0,
        source_status_counts=(),
        source_reason_codes=(),
        latest_snapshot_age_seconds=None,
        reason_code_counts=(),
        evidence_quality_average_delta=Decimal("0"),
        memory_eligible_delta=0,
        settled_calibration_delta=0,
        duplicate_latest_generated_at=False,
        reason_codes=(),
    )

    stdout = format_team_diagnostics_snapshot_history_gate_cli_stdout(report)

    assert "latest_snapshot_age_seconds=none" in stdout
    assert "source_generated_at=none" in stdout
    assert "source_status_counts=none" in stdout
    assert "source_reason_codes=none" in stdout
    assert "reason_code_counts=none" in stdout
    assert "reason_codes=none" in stdout


def test_format_team_diagnostics_snapshot_history_gate_cli_stdout_prints_none_for_none_reason_collections() -> None:
    report = SimpleNamespace(
        gate_status="pass",
        recommended_next_step="continue",
        source_config_version="team-diagnostics-snapshot-history-v0",
        source_generated_at=None,
        source_snapshot_count=3,
        source_required_snapshot_count=2,
        source_status="observed",
        source_span_seconds=0,
        source_status_counts=None,
        source_reason_codes=None,
        latest_snapshot_age_seconds=None,
        reason_code_counts=None,
        evidence_quality_average_delta=Decimal("0"),
        memory_eligible_delta=0,
        settled_calibration_delta=0,
        duplicate_latest_generated_at=False,
        reason_codes=None,
        paper_only=True,
        report_only=True,
        readonly=True,
    )

    stdout = format_team_diagnostics_snapshot_history_gate_cli_stdout(report)

    assert "reason_code_counts=none" in stdout
    assert "reason_codes=none" in stdout


def test_format_team_diagnostics_snapshot_history_gate_cli_stdout_uses_production_count_field() -> None:
    from polymarket_alpha_lab.team_diagnostics_snapshot_history_gate import (
        TeamDiagnosticsSnapshotHistoryGateReasonCodeCount,
    )

    report = GateReport(
        gate_status="pass",
        recommended_next_step="continue",
        source_config_version="team-diagnostics-snapshot-history-v0",
        source_generated_at=datetime(2026, 7, 1, 9, 59, tzinfo=UTC),
        source_snapshot_count=3,
        source_required_snapshot_count=3,
        source_status="observed",
        source_span_seconds=7200,
        source_status_counts=(("observed", 3),),
        source_reason_codes=(),
        latest_snapshot_age_seconds=60,
        reason_code_counts=(
            TeamDiagnosticsSnapshotHistoryGateReasonCodeCount(
                reason_code="team_diagnostics_snapshot_history_gate_passed",
                count=1,
            ),
        ),
        evidence_quality_average_delta=Decimal("0"),
        memory_eligible_delta=0,
        settled_calibration_delta=0,
        duplicate_latest_generated_at=False,
        reason_codes=("team_diagnostics_snapshot_history_gate_passed",),
    )

    stdout = format_team_diagnostics_snapshot_history_gate_cli_stdout(report)

    assert (
        "reason_code_counts=team_diagnostics_snapshot_history_gate_passed:1"
        in stdout
    )


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
    sys.modules.pop(
        "polymarket_alpha_lab.team_diagnostics_snapshot_history_gate_cli_format",
        None,
    )

    importlib.import_module(
        "polymarket_alpha_lab.team_diagnostics_snapshot_history_gate_cli_format",
    )

    assert set(imported_roots).isdisjoint(disallowed_import_roots)
