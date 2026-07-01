from __future__ import annotations

import builtins
import importlib
import sys
from types import ModuleType, SimpleNamespace
from typing import Any

from polymarket_alpha_lab.team_research_assignment_cli_format import (
    format_team_research_assignment_cli_stdout,
)


def test_format_team_research_assignment_cli_stdout_formats_populated_report() -> None:
    report = SimpleNamespace(
        assignment_status="watch",
        recommended_next_step="review_team_research_assignments",
        assignment_count=2,
        assigned_count=1,
        watch_count=1,
        blocked_count=0,
        team_summaries=(
            SimpleNamespace(
                team_id="crypto_btc",
                assignment_count=1,
                assigned_count=1,
                watch_count=0,
                blocked_count=0,
                memory_readiness_status="pass",
                memory_use_policy="allow",
            ),
            SimpleNamespace(
                team_id="politics",
                assignment_count=1,
                assigned_count=0,
                watch_count=1,
                blocked_count=0,
                memory_readiness_status="watch",
                memory_use_policy="throttle",
            ),
        ),
        rows=(
            SimpleNamespace(
                research_rank=1,
                market_slug="btc-alpha",
                team_id="crypto_btc",
                category_id="finance.crypto.btc",
                assignment_status="assigned",
                memory_use_policy="allow",
            ),
            SimpleNamespace(
                research_rank=2,
                market_slug="politics-alpha",
                team_id="politics",
                category_id="politics",
                assignment_status="watch",
                memory_use_policy="throttle",
            ),
        ),
        reason_codes=("team_research_assignment_watch",),
        paper_only=True,
        report_only=True,
        readonly=True,
    )

    stdout = format_team_research_assignment_cli_stdout(report)

    assert stdout == (
        "team-research-assignment: "
        "assignment_status=watch "
        "recommended_next_step=review_team_research_assignments "
        "assignment_count=2 "
        "assigned_count=1 "
        "watch_count=1 "
        "blocked_count=0 "
        "team_summaries=crypto_btc:1:1/0/0:pass:allow,"
        "politics:1:0/1/0:watch:throttle "
        "rows=1:btc-alpha:crypto_btc:finance.crypto.btc:assigned:allow,"
        "2:politics-alpha:politics:politics:watch:throttle "
        "reason_codes=team_research_assignment_watch "
        "paper_only=True "
        "report_only=True "
        "readonly=True\n"
    )


def test_format_team_research_assignment_cli_stdout_prints_none_for_empty_values() -> None:
    report = SimpleNamespace(
        assignment_status="pass",
        recommended_next_step="allow_team_research_assignments",
        assignment_count=0,
        assigned_count=0,
        watch_count=0,
        blocked_count=0,
        team_summaries=(),
        rows=(),
        reason_codes=(),
        paper_only=True,
        report_only=True,
        readonly=True,
    )

    stdout = format_team_research_assignment_cli_stdout(report)

    assert "team_summaries=none" in stdout
    assert "rows=none" in stdout
    assert "reason_codes=none" in stdout


def test_format_team_research_assignment_cli_stdout_prints_none_for_none_values() -> None:
    report = SimpleNamespace(
        assignment_status="blocked",
        recommended_next_step="block_team_research_assignments",
        assignment_count=0,
        assigned_count=0,
        watch_count=0,
        blocked_count=0,
        team_summaries=None,
        rows=None,
        reason_codes=None,
        paper_only=True,
        report_only=True,
        readonly=True,
    )

    stdout = format_team_research_assignment_cli_stdout(report)

    assert "team_summaries=none" in stdout
    assert "rows=none" in stdout
    assert "reason_codes=none" in stdout


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
    sys.modules.pop("polymarket_alpha_lab.team_research_assignment_cli_format", None)

    importlib.import_module("polymarket_alpha_lab.team_research_assignment_cli_format")

    imported_roots = {name.partition(".")[0] for name in imported_names}
    assert imported_roots.isdisjoint(disallowed_import_roots)
    assert "polymarket_alpha_lab.cli" not in imported_names
