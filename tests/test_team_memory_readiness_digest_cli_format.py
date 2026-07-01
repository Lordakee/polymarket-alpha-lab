from __future__ import annotations

import builtins
import importlib
import sys
from dataclasses import dataclass
from types import ModuleType, SimpleNamespace
from typing import Any

from polymarket_alpha_lab.team_memory_readiness_digest_cli_format import (
    format_team_memory_readiness_digest_cli_stdout,
)


@dataclass(frozen=True)
class SourceStatus:
    team_id: str
    gate_status: str
    recommended_next_step: str
    source_config_version: str
    latest_snapshot_age_seconds: int | None
    source_snapshot_count: int
    source_required_snapshot_count: int
    source_status: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


@dataclass(frozen=True)
class ReasonCodeCount:
    reason_code: str
    count: int


@dataclass(frozen=True)
class DigestReport:
    digest_status: str
    recommended_next_step: str
    team_count: int
    pass_count: int
    watch_count: int
    blocked_count: int
    source_statuses: tuple[SourceStatus, ...] | None
    source_config_versions: tuple[tuple[str, str], ...] | None
    reason_code_counts: tuple[ReasonCodeCount, ...] | None
    reason_codes: tuple[str, ...] | None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


def test_format_team_memory_readiness_digest_cli_stdout_formats_populated_report() -> None:
    report = DigestReport(
        digest_status="watch",
        recommended_next_step="throttle_team_memory_readiness_use",
        team_count=3,
        pass_count=1,
        watch_count=1,
        blocked_count=1,
        source_statuses=(
            SourceStatus(
                team_id="team-alpha",
                gate_status="pass",
                recommended_next_step="allow_team_memory_readiness_use",
                source_config_version="team-diagnostics-snapshot-history-gate-v0",
                latest_snapshot_age_seconds=45,
                source_snapshot_count=4,
                source_required_snapshot_count=3,
                source_status="observed",
            ),
            SourceStatus(
                team_id="team-beta",
                gate_status="watch",
                recommended_next_step="collect_more_snapshots",
                source_config_version="team-diagnostics-snapshot-history-gate-v1",
                latest_snapshot_age_seconds=None,
                source_snapshot_count=2,
                source_required_snapshot_count=3,
                source_status="insufficient_history",
            ),
        ),
        source_config_versions=(
            ("team-alpha", "team-diagnostics-snapshot-history-gate-v0"),
            ("team-beta", "team-diagnostics-snapshot-history-gate-v1"),
        ),
        reason_code_counts=(
            ReasonCodeCount("team_memory_readiness_digest_blocked_sources_present", 1),
            ReasonCodeCount("team_memory_readiness_digest_watch_sources_present", 1),
        ),
        reason_codes=(
            "team_memory_readiness_digest_watch_sources_present",
            "team_memory_readiness_digest_blocked_sources_present",
        ),
    )

    stdout = format_team_memory_readiness_digest_cli_stdout(report)

    assert stdout.startswith("team-memory-readiness-digest:")
    assert stdout == (
        "team-memory-readiness-digest: "
        "digest_status=watch "
        "recommended_next_step=throttle_team_memory_readiness_use "
        "team_count=3 "
        "pass_count=1 "
        "watch_count=1 "
        "blocked_count=1 "
        "source_statuses=team-alpha:pass:45:4/3,team-beta:watch:none:2/3 "
        "source_config_versions=team-alpha:team-diagnostics-snapshot-history-gate-v0,"
        "team-beta:team-diagnostics-snapshot-history-gate-v1 "
        "reason_code_counts=team_memory_readiness_digest_blocked_sources_present:1,"
        "team_memory_readiness_digest_watch_sources_present:1 "
        "reason_codes=team_memory_readiness_digest_watch_sources_present,"
        "team_memory_readiness_digest_blocked_sources_present "
        "paper_only=True "
        "report_only=True "
        "readonly=True\n"
    )


def test_format_team_memory_readiness_digest_cli_stdout_prints_none_for_empty_collections() -> None:
    report = DigestReport(
        digest_status="blocked",
        recommended_next_step="block_team_memory_readiness_use",
        team_count=0,
        pass_count=0,
        watch_count=0,
        blocked_count=0,
        source_statuses=(),
        source_config_versions=(),
        reason_code_counts=(),
        reason_codes=(),
    )

    stdout = format_team_memory_readiness_digest_cli_stdout(report)

    assert "source_statuses=none" in stdout
    assert "source_config_versions=none" in stdout
    assert "reason_code_counts=none" in stdout
    assert "reason_codes=none" in stdout


def test_format_team_memory_readiness_digest_cli_stdout_prints_none_for_none_collections() -> None:
    report = DigestReport(
        digest_status="blocked",
        recommended_next_step="block_team_memory_readiness_use",
        team_count=0,
        pass_count=0,
        watch_count=0,
        blocked_count=0,
        source_statuses=None,
        source_config_versions=None,
        reason_code_counts=None,
        reason_codes=None,
    )

    stdout = format_team_memory_readiness_digest_cli_stdout(report)

    assert "source_statuses=none" in stdout
    assert "source_config_versions=none" in stdout
    assert "reason_code_counts=none" in stdout
    assert "reason_codes=none" in stdout


def test_format_team_memory_readiness_digest_cli_stdout_accepts_mapping_and_tuple_rows() -> None:
    report = SimpleNamespace(
        digest_status="pass",
        recommended_next_step="allow_team_memory_readiness_use",
        team_count=1,
        pass_count=1,
        watch_count=0,
        blocked_count=0,
        source_statuses=(
            {
                "team_id": "team-alpha",
                "gate_status": "pass",
                "latest_snapshot_age_seconds": 12,
                "source_snapshot_count": 3,
                "source_required_snapshot_count": 3,
            },
        ),
        source_config_versions=(("team-alpha", "team-diagnostics-snapshot-history-gate-v0"),),
        reason_code_counts=(("team_memory_readiness_digest_passed", 1),),
        reason_codes=("team_memory_readiness_digest_passed",),
        paper_only=True,
        report_only=True,
        readonly=True,
    )

    stdout = format_team_memory_readiness_digest_cli_stdout(report)

    assert "source_statuses=team-alpha:pass:12:3/3" in stdout
    assert (
        "source_config_versions=team-alpha:team-diagnostics-snapshot-history-gate-v0"
        in stdout
    )
    assert "reason_code_counts=team_memory_readiness_digest_passed:1" in stdout


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
        "polymarket_alpha_lab.team_memory_readiness_digest_cli_format",
        None,
    )

    importlib.import_module(
        "polymarket_alpha_lab.team_memory_readiness_digest_cli_format",
    )

    assert set(imported_roots).isdisjoint(disallowed_import_roots)
