from __future__ import annotations

import ast
from pathlib import Path

import pytest

from polymarket_alpha_lab.cli import main


REPO_ROOT = Path(__file__).resolve().parents[1]
CLI_PATH = REPO_ROOT / "src" / "polymarket_alpha_lab" / "cli.py"
COMMAND = "paper-research-packet-operator-flow"

EXPECTED_PARSER_ARGUMENT_SURFACE = {
    "--source-config-version",
    "source_config_version",
    "--action-status",
    "action_status",
    "--research-status",
    "research_status",
    "--limit",
    "limit",
    "--packet-config-version",
    "packet_config_version",
    "--max-packet-rows",
    "max_packet_rows",
    "--min-score",
    "min_score",
    "--quality-history-limit",
    "quality_history_limit",
}

FORBIDDEN_PARSER_ARGUMENT_SURFACE = {
    "--dsn",
    "dsn",
    "--db-dsn",
    "db_dsn",
    "--table",
    "table",
    "--strategy-candidate-research-queue-db-dsn",
    "strategy_candidate_research_queue_db_dsn",
    "--strategy-candidate-research-queue-db-table",
    "strategy_candidate_research_queue_db_table",
    "--strategy-candidate-research-queue-db-enabled",
    "strategy_candidate_research_queue_db_enabled",
    "--paper-research-packet-db-dsn",
    "paper_research_packet_db_dsn",
    "--paper-research-packet-db-table",
    "paper_research_packet_db_table",
    "--paper-research-packet-db-enabled",
    "paper_research_packet_db_enabled",
    "--paper-research-packet-quality-db-dsn",
    "paper_research_packet_quality_db_dsn",
    "--paper-research-packet-quality-db-table",
    "paper_research_packet_quality_db_table",
    "--paper-research-packet-quality-db-enabled",
    "paper_research_packet_quality_db_enabled",
    "--paper-research-packet-operator-flow-db-dsn",
    "paper_research_packet_operator_flow_db_dsn",
    "--paper-research-packet-operator-flow-db-table",
    "paper_research_packet_operator_flow_db_table",
    "--paper-research-packet-operator-flow-db-enabled",
    "paper_research_packet_operator_flow_db_enabled",
    "--source-limit",
    "source_limit",
    "--history-limit",
    "history_limit",
    "--persist",
    "persist",
    "--config-version",
    "config_version",
    "--quality-config-version",
    "quality_config_version",
    "--history-config-version",
    "history_config_version",
    "--live",
    "live",
    "--execute",
    "execute",
    "--trade",
    "trade",
    "--order",
    "order",
    "--exchange",
    "exchange",
    "--relayer",
    "relayer",
    "--network",
    "network",
    "--wallet",
    "wallet",
    "--private-key",
    "private_key",
    "--signing-key",
    "signing_key",
    "--api-key",
    "api_key",
    "--auth",
    "auth",
    "--fast",
    "fast",
}

FORBIDDEN_PHASE_ONE_ESCAPE_FRAGMENTS = {
    "account",
    "auth",
    "cancel",
    "clientfactory",
    "exchange",
    "fast",
    "insert",
    "live",
    "mutation",
    "order",
    "persist",
    "privatekey",
    "sign",
    "sink",
    "submit",
    "trade",
    "wallet",
    "write",
}

RUNTIME_FORBIDDEN_FLAGS = (
    "--api-key",
    "--auth",
    "--dsn",
    "--fast",
    "--live",
    "--paper-research-packet-operator-flow-db-dsn",
    "--paper-research-packet-operator-flow-db-table",
    "--paper-research-packet-db-table",
    "--paper-research-packet-quality-db-dsn",
    "--persist",
    "--private-key",
    "--table",
    "--trade",
    "--wallet",
)


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


def test_operator_flow_parser_surface_is_exactly_intended_operator_controls() -> None:
    tree = parse_cli()
    parser_variable = _command_parser_variable(tree, COMMAND)
    surface = _parser_argument_surface(tree, parser_variable)

    assert surface == EXPECTED_PARSER_ARGUMENT_SURFACE
    assert not (surface & FORBIDDEN_PARSER_ARGUMENT_SURFACE)
    _assert_no_forbidden_fragments(surface, FORBIDDEN_PHASE_ONE_ESCAPE_FRAGMENTS)


def test_operator_flow_cli_rejects_db_auth_fast_and_live_trading_flags(
    capsys: pytest.CaptureFixture[str],
) -> None:
    for flag in RUNTIME_FORBIDDEN_FLAGS:
        with pytest.raises(SystemExit) as exc_info:
            main([COMMAND, flag, "forbidden-value"])

        assert exc_info.value.code == 2
        captured = capsys.readouterr()
        assert f"unrecognized arguments: {flag}" in captured.err
