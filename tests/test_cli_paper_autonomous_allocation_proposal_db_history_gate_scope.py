from __future__ import annotations

import ast
from pathlib import Path

import pytest

from polymarket_alpha_lab.cli import main


REPO_ROOT = Path(__file__).resolve().parents[1]
CLI_PATH = REPO_ROOT / "src" / "polymarket_alpha_lab" / "cli.py"
COMMAND = "paper-autonomous-allocation-proposal-db-history-gate"
RUN_HELPER = "_run_paper_autonomous_allocation_proposal_db_history_gate"
SUMMARY_PRINTER = "_print_paper_autonomous_allocation_proposal_db_history_gate_summary"

EXPECTED_PARSER_ARGUMENT_SURFACE = {
    "--limit",
    "limit",
}

FORBIDDEN_PARSER_ARGUMENT_SURFACE = {
    "--dsn",
    "dsn",
    "--db-dsn",
    "db_dsn",
    "--table",
    "table",
    "--db-table",
    "db_table",
    "--persist",
    "persist",
    "--paper-autonomous-allocation-proposal-db-dsn",
    "paper_autonomous_allocation_proposal_db_dsn",
    "--paper-autonomous-allocation-proposal-db-table",
    "paper_autonomous_allocation_proposal_db_table",
    "--paper-autonomous-allocation-proposal-db-enabled",
    "paper_autonomous_allocation_proposal_db_enabled",
    "--live",
    "live",
    "--execute",
    "execute",
    "--trade",
    "trade",
    "--auth",
    "auth",
    "--wallet",
    "wallet",
    "--private-key",
    "private_key",
    "--api-key",
    "api_key",
    "--account",
    "account",
    "--order",
    "order",
    "--submit",
    "submit",
    "--approve",
    "approve",
    "--fast",
    "fast",
}

RUNTIME_FORBIDDEN_FLAGS = (
    "--account",
    "--api-key",
    "--approve",
    "--auth",
    "--db-dsn",
    "--db-table",
    "--dsn",
    "--execute",
    "--fast",
    "--live",
    "--order",
    "--paper-autonomous-allocation-proposal-db-dsn",
    "--paper-autonomous-allocation-proposal-db-table",
    "--persist",
    "--private-key",
    "--submit",
    "--table",
    "--trade",
    "--wallet",
)

FORBIDDEN_SOURCE_ESCAPE_FRAGMENTS = {
    "account",
    "auth",
    "clientfactory",
    "db_dsn",
    "db_table",
    "delete",
    "dsn",
    "execute",
    "fast",
    "insert",
    "live",
    "market_slug",
    "order",
    "persist",
    "private",
    "question",
    "sha256",
    "submit",
    "table",
    "trade",
    "wallet",
}

ALLOWED_RUN_HELPER_IMPORTS = {
    "polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history",
    "polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_gate",
    "polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_gate_load",
    "psycopg",
}

SUMMARY_REQUIRED_FIELDS = {
    "gate_status",
    "recommended_next_step",
    "source_report_count",
    "source_history_status",
    "latest_proposal_status",
    "latest_screening_gate_status",
    "latest_queue_risk_status",
    "latest_allocation_input_count",
    "latest_allocation_row_count",
    "latest_allocated_count",
    "latest_total_allocated_paper_notional",
    "duplicate_generated_at_count",
    "latest_source_age_seconds",
    "reason_code_counts",
}

SUMMARY_FORBIDDEN_DETAIL_FRAGMENTS = {
    "dsn",
    "table",
    "payload",
    "hash",
    "sha256",
    "question",
    "market_slug",
    "account",
    "wallet",
    "key",
    "order",
    "trade",
    "execute",
    "submit",
    "approve",
}


def normalize_identifier(value: str) -> str:
    return "".join(character for character in value.lower() if character.isalnum())


def parse_cli() -> ast.AST:
    return ast.parse(CLI_PATH.read_text(encoding="utf-8"), filename=str(CLI_PATH))


def call_or_attribute_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Call):
        return call_or_attribute_name(node.func)
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return None


def _is_command_literal(node: ast.AST, command: str) -> bool:
    return isinstance(node, ast.Constant) and node.value == command


def _command_parser_variable(tree: ast.AST, command: str) -> str:
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if not isinstance(target, ast.Name):
            continue
        call = node.value
        if not isinstance(call, ast.Call):
            continue
        if call_or_attribute_name(call) != "add_parser":
            continue
        if call.args and _is_command_literal(call.args[0], command):
            return target.id
    raise AssertionError(f"missing parser variable for {command}")


def _explicit_dest(call: ast.Call) -> str | None:
    for keyword in call.keywords:
        if (
            keyword.arg == "dest"
            and isinstance(keyword.value, ast.Constant)
            and isinstance(keyword.value.value, str)
        ):
            return keyword.value.value
    return None


def _derived_argparse_dest(option_strings: tuple[str, ...]) -> str | None:
    optional_strings = tuple(option for option in option_strings if option.startswith("-"))
    if not optional_strings:
        return None
    long_options = tuple(option for option in optional_strings if option.startswith("--"))
    option = (long_options or optional_strings)[0]
    return option.lstrip("-").replace("-", "_")


def _parser_argument_surface(tree: ast.AST, parser_variable: str) -> set[str]:
    surface: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if call_or_attribute_name(node) != "add_argument":
            continue
        func = node.func
        if (
            not isinstance(func, ast.Attribute)
            or not isinstance(func.value, ast.Name)
            or func.value.id != parser_variable
        ):
            continue

        option_strings = tuple(
            arg.value
            for arg in node.args
            if isinstance(arg, ast.Constant) and isinstance(arg.value, str)
        )
        surface.update(option_strings)
        dest = _explicit_dest(node) or _derived_argparse_dest(option_strings)
        if dest is not None:
            surface.add(dest)
    return surface


def _function_def(tree: ast.AST, name: str) -> ast.FunctionDef:
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    raise AssertionError(f"missing function {name}")


def _string_constants(node: ast.AST) -> set[str]:
    return {
        child.value
        for child in ast.walk(node)
        if isinstance(child, ast.Constant) and isinstance(child.value, str)
    }


def _imported_module_names(node: ast.AST) -> set[str]:
    names: set[str] = set()
    for child in ast.walk(node):
        if isinstance(child, ast.Import):
            names.update(alias.name for alias in child.names)
        if isinstance(child, ast.ImportFrom) and child.module is not None:
            names.add(child.module)
    return names


def _referenced_names(node: ast.AST) -> set[str]:
    references: set[str] = set()
    for child in ast.walk(node):
        if isinstance(child, ast.Name):
            references.add(child.id)
        elif isinstance(child, ast.Attribute):
            references.add(child.attr)
        elif isinstance(child, ast.Constant) and isinstance(child.value, str):
            references.add(child.value)
    return references


def _assert_no_forbidden_fragments(references: set[str], fragments: set[str]) -> None:
    for fragment in fragments:
        normalized_fragment = normalize_identifier(fragment)
        matches = tuple(
            sorted(
                reference
                for reference in references
                if normalized_fragment in normalize_identifier(reference)
            ),
        )
        assert not matches, (fragment, matches)


def test_allocation_proposal_db_history_gate_parser_accepts_only_limit() -> None:
    tree = parse_cli()
    parser_variable = _command_parser_variable(tree, COMMAND)
    surface = _parser_argument_surface(tree, parser_variable)

    assert surface == EXPECTED_PARSER_ARGUMENT_SURFACE
    assert not (surface & FORBIDDEN_PARSER_ARGUMENT_SURFACE)


def test_allocation_proposal_db_history_gate_cli_rejects_direct_db_live_auth_wallet_and_fast_flags(
    capsys: pytest.CaptureFixture[str],
) -> None:
    for flag in RUNTIME_FORBIDDEN_FLAGS:
        with pytest.raises(SystemExit) as exc_info:
            main([COMMAND, flag, "forbidden-value"])

        assert exc_info.value.code == 2
        captured = capsys.readouterr()
        assert "unrecognized arguments" in captured.err


def test_allocation_proposal_db_history_gate_helper_uses_only_allocation_history_gate_loader_and_psycopg() -> None:
    tree = parse_cli()
    helper = _function_def(tree, RUN_HELPER)
    imports = _imported_module_names(helper)
    references = _referenced_names(helper)
    forbidden_calls = {
        "commit",
        "rollback",
        "insert",
        "persist",
        "update",
        "delete",
        "execute",
        "executemany",
        "cursor",
    }

    assert imports <= ALLOWED_RUN_HELPER_IMPORTS
    assert "PaperAutonomousAllocationProposalDbHistoryConfig" in references
    assert "PaperAutonomousAllocationProposalDbHistoryGateConfig" in references
    assert (
        "load_paper_autonomous_allocation_proposal_db_history_gate_report"
        in references
    )
    assert "connect" in references
    assert "close" in references
    assert not (references & forbidden_calls)


def test_allocation_proposal_db_history_gate_summary_is_aggregate_only() -> None:
    tree = parse_cli()
    printer = _function_def(tree, SUMMARY_PRINTER)
    strings = _string_constants(printer)
    references = _referenced_names(printer)
    rendered_text = " ".join(strings)

    for field_name in SUMMARY_REQUIRED_FIELDS:
        assert field_name in references or field_name in rendered_text
    _assert_no_forbidden_fragments(
        strings | references,
        SUMMARY_FORBIDDEN_DETAIL_FRAGMENTS,
    )
