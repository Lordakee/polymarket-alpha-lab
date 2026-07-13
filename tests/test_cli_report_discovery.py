from __future__ import annotations

import ast
from pathlib import Path

import pytest

from polymarket_alpha_lab.cli import main


CLI_SOURCE = Path("src/polymarket_alpha_lab/cli.py")
DISCOVERY_COMMAND = "report-discovery"
FORBIDDEN_OPTIONS = {
    "--persist",
    "--dsn",
    "--table",
    "--input",
    "--output",
    "--live",
    "--auth",
    "--wallet",
    "--order",
    "--private-key",
    "--account",
}


def test_report_discovery_lists_operator_report_groups_without_execution(
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = main([DISCOVERY_COMMAND])

    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured.err == ""
    assert "Phase 1 readiness reports" in captured.out
    assert "paper-autonomous-readiness-digest" in captured.out
    assert "team-memory-readiness-digest" in captured.out
    assert "Critical strategy rollups" in captured.out
    assert "probability-selection-scorer-agreement-trend-gate" in captured.out
    assert "Manual review packet" in captured.out
    assert "paper-research-packet-operator-flow" in captured.out
    assert "read-only" in captured.out
    assert "paper/report-only" in captured.out
    assert "persist" not in captured.out.lower()


@pytest.mark.parametrize(
    ("category", "expected", "unexpected"),
    (
        (
            "readiness",
            "Phase 1 readiness reports",
            "Manual review packet",
        ),
        (
            "strategy-rollups",
            "Critical strategy rollups",
            "Phase 1 readiness reports",
        ),
        (
            "manual-review",
            "Manual review packet",
            "Critical strategy rollups",
        ),
    ),
)
def test_report_discovery_filters_by_aggregate_category(
    category: str,
    expected: str,
    unexpected: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = main([DISCOVERY_COMMAND, "--category", category])

    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured.err == ""
    assert expected in captured.out
    assert unexpected not in captured.out


def test_report_discovery_help_exposes_only_readonly_discovery_flags(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main([DISCOVERY_COMMAND, "--help"])

    captured = capsys.readouterr()

    assert exc_info.value.code == 0
    assert "--category" in captured.out
    assert "--format" in captured.out
    assert "read-only" in captured.out.lower()
    assert "report-only" in captured.out.lower()
    for option in FORBIDDEN_OPTIONS:
        assert option not in captured.out


def test_report_discovery_cli_branch_has_no_db_execution_or_live_trading_surface() -> None:
    source = CLI_SOURCE.read_text(encoding="utf-8")
    tree = ast.parse(source)

    branch = _command_branch(tree, DISCOVERY_COMMAND)
    branch_text = ast.unparse(branch).lower()

    assert "report_discovery" in branch_text
    forbidden_tokens = {
        "from_",
        "psycopg",
        "db_env",
        "insert_",
        "load_",
        "runner",
        "persist",
        "wallet",
        "private_key",
        "order",
        "auth",
        "execute",
        "trading",
    }
    assert forbidden_tokens.isdisjoint(_identifier_tokens(branch))


def _command_branch(tree: ast.AST, command: str) -> ast.If:
    for node in ast.walk(tree):
        if not isinstance(node, ast.If):
            continue
        if ast.unparse(node.test) == f"args.command == '{command}'":
            return node
    raise AssertionError(f"{command} dispatch branch is not declared")


def _identifier_tokens(node: ast.AST) -> set[str]:
    tokens: set[str] = set()
    for child in ast.walk(node):
        if isinstance(child, ast.Name):
            tokens.add(child.id.lower())
        elif isinstance(child, ast.Attribute):
            tokens.add(child.attr.lower())
        elif isinstance(child, ast.arg):
            tokens.add(child.arg.lower())
    return tokens
