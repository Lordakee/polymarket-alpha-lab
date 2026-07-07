from __future__ import annotations

import ast
import builtins
import importlib
import inspect
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from types import ModuleType, SimpleNamespace
from typing import Any

import pytest

from polymarket_alpha_lab.candidate_decision_score_history_cli_format import (
    format_candidate_decision_score_history_cli_stdout,
)


@dataclass(frozen=True)
class CountRow:
    name: str
    count: int


@dataclass(frozen=True)
class HistoryReport:
    generated_at: datetime
    status: str
    report_count: int
    latest_generated_at: datetime | None
    action_counts: tuple[tuple[str, int], ...]
    reason_counts: tuple[CountRow, ...]
    primary_team_counts: dict[str, int]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


def test_format_candidate_decision_score_history_cli_stdout_formats_public_aggregate_summary() -> None:
    report = HistoryReport(
        generated_at=datetime(2026, 7, 7, 13, 15, tzinfo=UTC),
        status="observed",
        report_count=5,
        latest_generated_at=datetime(2026, 7, 7, 13, 10, 30, tzinfo=UTC),
        action_counts=(
            ("paper_recommend", 2),
            ("research_more", 1),
            ("watch", 1),
            ("reject", 1),
        ),
        reason_counts=(
            CountRow("candidate_decision_paper_recommend", 2),
            CountRow("net_edge_missing", 1),
        ),
        primary_team_counts={"macro": 3, "energy": 2},
    )

    stdout = format_candidate_decision_score_history_cli_stdout(report)

    assert stdout == (
        "candidate-decision-score-history: "
        "generated_at=2026-07-07T13:15:00+00:00 "
        "status=observed "
        "report_count=5 "
        "latest_generated_at=2026-07-07T13:10:30+00:00 "
        "action_counts=paper_recommend:2,research_more:1,watch:1,reject:1 "
        "reason_counts=candidate_decision_paper_recommend:2,net_edge_missing:1 "
        "primary_team_counts=macro:3,energy:2 "
        "paper_only=True "
        "report_only=True "
        "readonly=True\n"
    )
    for sensitive_value in (
        "secret-market-id",
        "secret-candidate-id",
        "Will the hidden question leak?",
        "secret-market-slug",
        "validation-digest",
        "source-report-ref",
    ):
        assert sensitive_value not in stdout


def test_format_candidate_decision_score_history_cli_stdout_ignores_sensitive_duck_typed_attributes() -> None:
    report = SimpleNamespace(
        generated_at=datetime(2026, 7, 7, 13, 15, tzinfo=UTC),
        status="empty",
        report_count=0,
        latest_generated_at=None,
        action_counts=(),
        reason_counts=None,
        primary_team_counts=(),
        market_id="secret-market-id",
        candidate_id="secret-candidate-id",
        normalized_market_question="Will the hidden question leak?",
        market_slug="secret-market-slug",
        question="Will the hidden question leak?",
        payload={"market_id": "secret-market-id"},
        derived_validation_digest="validation-digest",
        source_report_refs=("source-report-ref",),
        table_name="private_table",
        dsn="postgresql://private-host/db",
        host="private-host",
        paper_only=True,
        report_only=True,
        readonly=True,
    )

    stdout = format_candidate_decision_score_history_cli_stdout(report)

    assert stdout == (
        "candidate-decision-score-history: "
        "generated_at=2026-07-07T13:15:00+00:00 "
        "status=empty "
        "report_count=0 "
        "latest_generated_at=none "
        "action_counts=none "
        "reason_counts=none "
        "primary_team_counts=none "
        "paper_only=True "
        "report_only=True "
        "readonly=True\n"
    )
    forbidden_public_fragments = (
        "secret-market-id",
        "secret-candidate-id",
        "hidden question",
        "secret-market-slug",
        "validation-digest",
        "source-report-ref",
        "private_table",
        "private-host",
    )
    for fragment in forbidden_public_fragments:
        assert fragment not in stdout


@pytest.mark.parametrize("flag_name", ("paper_only", "report_only", "readonly"))
def test_format_candidate_decision_score_history_cli_stdout_fails_closed_on_false_hard_flags(
    flag_name: str,
) -> None:
    report = SimpleNamespace(
        generated_at=datetime(2026, 7, 7, 13, 15, tzinfo=UTC),
        status="observed",
        report_count=1,
        latest_generated_at=datetime(2026, 7, 7, 13, 10, tzinfo=UTC),
        action_counts={"watch": 1},
        reason_counts={"candidate_decision_watch": 1},
        primary_team_counts={"macro": 1},
        paper_only=True,
        report_only=True,
        readonly=True,
    )
    setattr(report, flag_name, False)

    with pytest.raises(ValueError, match=f"report must be {flag_name}"):
        format_candidate_decision_score_history_cli_stdout(report)


def test_format_candidate_decision_score_history_cli_stdout_fails_closed_when_hard_flags_are_missing() -> None:
    report = SimpleNamespace(
        generated_at=datetime(2026, 7, 7, 13, 15, tzinfo=UTC),
        status="observed",
        report_count=1,
        latest_generated_at=datetime(2026, 7, 7, 13, 10, tzinfo=UTC),
        action_counts={"watch": 1},
        reason_counts={"candidate_decision_watch": 1},
        primary_team_counts={"macro": 1},
    )

    with pytest.raises(ValueError, match="report must be paper_only"):
        format_candidate_decision_score_history_cli_stdout(report)


def test_format_candidate_decision_score_history_cli_stdout_rejects_unsafe_public_count_labels() -> None:
    report = SimpleNamespace(
        generated_at=datetime(2026, 7, 7, 13, 15, tzinfo=UTC),
        status="observed",
        report_count=1,
        latest_generated_at=datetime(2026, 7, 7, 13, 10, tzinfo=UTC),
        action_counts={"cancel_live_order": 1},
        reason_counts=(),
        primary_team_counts=(),
        paper_only=True,
        report_only=True,
        readonly=True,
    )

    with pytest.raises(ValueError, match="unsafe public summary value"):
        format_candidate_decision_score_history_cli_stdout(report)


def test_format_candidate_decision_score_history_cli_stdout_allows_authority_reason_codes() -> None:
    report = SimpleNamespace(
        generated_at=datetime(2026, 7, 7, 13, 15, tzinfo=UTC),
        status="observed",
        report_count=2,
        latest_generated_at=datetime(2026, 7, 7, 13, 10, tzinfo=UTC),
        action_counts={"research_more": 2},
        reason_counts=(
            ("resolution_authoritative_source_present", 1),
            ("evidence_authority_low", 1),
        ),
        primary_team_counts={"macro": 2},
        paper_only=True,
        report_only=True,
        readonly=True,
    )

    stdout = format_candidate_decision_score_history_cli_stdout(report)

    assert "resolution_authoritative_source_present:1" in stdout
    assert "evidence_authority_low:1" in stdout


def test_format_candidate_decision_score_history_cli_stdout_rejects_authorization_labels() -> None:
    report = SimpleNamespace(
        generated_at=datetime(2026, 7, 7, 13, 15, tzinfo=UTC),
        status="observed",
        report_count=1,
        latest_generated_at=datetime(2026, 7, 7, 13, 10, tzinfo=UTC),
        action_counts={"watch": 1},
        reason_counts={"authorization_token_present": 1},
        primary_team_counts=(),
        paper_only=True,
        report_only=True,
        readonly=True,
    )

    with pytest.raises(ValueError, match="unsafe public summary value"):
        format_candidate_decision_score_history_cli_stdout(report)


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
        "polymarket_alpha_lab.candidate_decision_score_history_cli_format",
        None,
    )

    importlib.import_module(
        "polymarket_alpha_lab.candidate_decision_score_history_cli_format",
    )

    imported_roots = {name.partition(".")[0] for name in imported_names}
    assert imported_roots.isdisjoint(disallowed_import_roots)
    assert "polymarket_alpha_lab.cli" not in imported_names


def test_formatter_source_has_no_forbidden_imports_or_sensitive_public_surfaces() -> None:
    module = importlib.import_module(
        "polymarket_alpha_lab.candidate_decision_score_history_cli_format",
    )
    source = inspect.getsource(module)
    tree = ast.parse(source)
    forbidden_import_roots = {
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
    forbidden_calls = {
        "connect",
        "getenv",
        "open",
        "run",
        "Popen",
        "Client",
    }
    forbidden_public_surfaces = {
        "market_id",
        "candidate_id",
        "normalized_market_question",
        "market_slug",
        "question",
        "payload",
        "digest",
        "dsn",
        "host",
        "table_name",
        "source_report_refs",
    }

    imported_roots: set[str] = set()
    call_names: set[str] = set()
    public_names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.partition(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_roots.add(node.module.partition(".")[0])
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                call_names.add(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                call_names.add(node.func.attr)
        elif isinstance(node, ast.FunctionDef) and not node.name.startswith("_"):
            public_names.add(node.name)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and not target.id.startswith("_"):
                    public_names.add(target.id)

    assert imported_roots.isdisjoint(forbidden_import_roots)
    assert call_names.isdisjoint(forbidden_calls)
    for public_name in public_names:
        for forbidden_surface in forbidden_public_surfaces:
            assert forbidden_surface not in public_name
