from __future__ import annotations

import builtins
import importlib
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from types import ModuleType, SimpleNamespace
from typing import Any

from polymarket_alpha_lab.team_research_assignment_history_cli_format import (
    format_team_research_assignment_history_cli_stdout,
)


@dataclass(frozen=True)
class StatusRow:
    assignment_status: str
    report_count: int


def test_format_team_research_assignment_history_cli_stdout_formats_summary_without_market_details() -> None:
    report = SimpleNamespace(
        config_version="team-research-assignment-history-v0",
        history_status="observed",
        report_count=3,
        required_report_count=2,
        first_report_generated_at=datetime(2026, 7, 1, 8, 30, tzinfo=UTC),
        latest_report_generated_at=datetime(2026, 7, 1, 9, 45, 15, tzinfo=UTC),
        status_rows=(
            StatusRow(assignment_status="ready", report_count=1),
            StatusRow(assignment_status="watch", report_count=1),
            StatusRow(assignment_status="blocked", report_count=1),
        ),
        latest_assignment_status="ready",
        latest_assignment_count=3,
        latest_assigned_count=3,
        latest_watch_count=0,
        latest_blocked_count=0,
        assignment_count_delta=1,
        assigned_count_delta=2,
        watch_count_delta=0,
        blocked_count_delta=-1,
        duplicate_latest_generated_at=False,
        reason_codes=(),
        market_slug="secret-btc-alpha",
        question="Will this secret market question leak?",
        rows=(
            SimpleNamespace(
                market_slug="secret-btc-alpha",
                question="Will this secret market question leak?",
            ),
        ),
        paper_only=True,
        report_only=True,
        readonly=True,
    )

    stdout = format_team_research_assignment_history_cli_stdout(report)

    assert stdout == (
        "team-research-assignment-history: "
        "config_version=team-research-assignment-history-v0 "
        "history_status=observed "
        "report_count=3 "
        "required_report_count=2 "
        "first_report_generated_at=2026-07-01T08:30:00+00:00 "
        "latest_report_generated_at=2026-07-01T09:45:15+00:00 "
        "status_rows=ready:1,watch:1,blocked:1 "
        "latest_assignment_status=ready "
        "latest_assignment_count=3 "
        "latest_assigned_count=3 "
        "latest_watch_count=0 "
        "latest_blocked_count=0 "
        "assignment_count_delta=1 "
        "assigned_count_delta=2 "
        "watch_count_delta=0 "
        "blocked_count_delta=-1 "
        "duplicate_latest_generated_at=False "
        "reason_codes=none "
        "paper_only=True "
        "report_only=True "
        "readonly=True\n"
    )
    assert "secret-btc-alpha" not in stdout
    assert "secret market question" not in stdout


def test_format_team_research_assignment_history_cli_stdout_prints_none_for_empty_or_none_values() -> None:
    empty_report = SimpleNamespace(
        config_version="team-research-assignment-history-v0",
        history_status="blocked",
        report_count=0,
        required_report_count=2,
        first_report_generated_at=None,
        latest_report_generated_at=None,
        status_rows=(),
        latest_assignment_status=None,
        latest_assignment_count=0,
        latest_assigned_count=0,
        latest_watch_count=0,
        latest_blocked_count=0,
        assignment_count_delta=0,
        assigned_count_delta=0,
        watch_count_delta=0,
        blocked_count_delta=0,
        duplicate_latest_generated_at=False,
        reason_codes=(),
        paper_only=True,
        report_only=True,
        readonly=True,
    )
    none_report = SimpleNamespace(
        **{**empty_report.__dict__, "status_rows": None, "reason_codes": None},
    )

    empty_stdout = format_team_research_assignment_history_cli_stdout(empty_report)
    none_stdout = format_team_research_assignment_history_cli_stdout(none_report)

    assert "first_report_generated_at=none" in empty_stdout
    assert "config_version=team-research-assignment-history-v0" in empty_stdout
    assert "latest_report_generated_at=none" in empty_stdout
    assert "latest_assignment_status=none" in empty_stdout
    assert "status_rows=none" in empty_stdout
    assert "reason_codes=none" in empty_stdout
    assert "status_rows=none" in none_stdout
    assert "reason_codes=none" in none_stdout


def test_formatter_imports_no_db_env_cli_network_or_filesystem_modules(
    monkeypatch: Any,
) -> None:
    disallowed_import_roots = {
        "asyncpg",
        "dotenv",
        "os",
        "pathlib",
        "polymarket_alpha_lab.cli",
        "psycopg",
        "psycopg2",
        "requests",
        "socket",
        "sqlite3",
        "subprocess",
    }
    imported_names: list[str] = []
    original_import = builtins.__import__

    def tracking_import(
        name: str,
        globals: dict[str, Any] | None = None,
        locals: dict[str, Any] | None = None,
        fromlist: tuple[str, ...] = (),
        level: int = 0,
    ) -> ModuleType:
        if level == 0:
            imported_names.append(name)
        return original_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", tracking_import)
    sys.modules.pop(
        "polymarket_alpha_lab.team_research_assignment_history_cli_format",
        None,
    )

    importlib.import_module(
        "polymarket_alpha_lab.team_research_assignment_history_cli_format",
    )

    imported_roots = {name.partition(".")[0] for name in imported_names}
    assert imported_roots.isdisjoint(disallowed_import_roots)
    assert "polymarket_alpha_lab.cli" not in imported_names
