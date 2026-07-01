from __future__ import annotations

import ast
import textwrap
from pathlib import Path


CLI_SOURCE = Path("src/polymarket_alpha_lab/cli.py")

COMMAND_NAME = "team-diagnostics"
ALLOWED_FLAGS = {
    "--help",
    "--team-id",
    "--market-slug",
    "--forecast-id",
    "--limit",
}
FORBIDDEN_FLAGS = {
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
FORBIDDEN_IDENTIFIERS = {
    "account",
    "auth",
    "cancel_order",
    "cancel_orders",
    "create_order",
    "derive_api_key",
    "execute",
    "get_balance_allowance",
    "get_order",
    "get_orders",
    "live",
    "order",
    "persist",
    "post_order",
    "post_orders",
    "private_key",
    "replace_order",
    "sign_order",
    "submit_order",
    "wallet",
}


def test_team_diagnostics_cli_command_is_declared_in_parser_and_dispatch() -> None:
    source = CLI_SOURCE.read_text(encoding="utf-8")

    assert f'"{COMMAND_NAME}"' in _team_diagnostics_parser_block()
    assert f'args.command == "{COMMAND_NAME}"' in source


def test_team_diagnostics_cli_exposes_only_readonly_report_flags() -> None:
    command_block = _team_diagnostics_parser_block()

    for flag in ALLOWED_FLAGS - {"--help"}:
        assert flag in command_block
    for flag in FORBIDDEN_FLAGS:
        assert flag not in command_block

    lower_block = command_block.lower()
    assert "read-only" in lower_block or "readonly" in lower_block
    assert "report-only" in lower_block or "report only" in lower_block
    assert "local" in lower_block
    assert "supabase" in lower_block
    assert "postgres" in lower_block


def test_team_diagnostics_cli_branch_uses_no_live_auth_wallet_or_order_calls() -> None:
    branch_block = _team_diagnostics_branch_block()
    tree = ast.parse(textwrap.dedent(branch_block))
    identifiers: set[str] = set()
    call_names: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            identifiers.add(_normalize(node.id))
        elif isinstance(node, ast.Attribute):
            identifiers.add(_normalize(node.attr))
        elif isinstance(node, ast.arg):
            identifiers.add(_normalize(node.arg))
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                call_names.add(_normalize(node.func.id))
            elif isinstance(node.func, ast.Attribute):
                call_names.add(_normalize(node.func.attr))

    forbidden = {_normalize(value) for value in FORBIDDEN_IDENTIFIERS}
    assert identifiers.isdisjoint(forbidden)
    assert call_names.isdisjoint(forbidden)


def _team_diagnostics_parser_block() -> str:
    source = CLI_SOURCE.read_text(encoding="utf-8")
    command_index = source.find(f'"{COMMAND_NAME}"')
    assert command_index >= 0, "team-diagnostics parser is not declared"

    next_parser_index = source.find("subparsers.add_parser(", command_index + 1)
    parse_args_index = source.find("args = parser.parse_args(argv)", command_index)
    stop_index_candidates = [
        index for index in (next_parser_index, parse_args_index) if index >= 0
    ]
    assert stop_index_candidates, "team-diagnostics parser block has no end marker"
    return source[command_index : min(stop_index_candidates)]


def _team_diagnostics_branch_block() -> str:
    source = CLI_SOURCE.read_text(encoding="utf-8")
    branch_index = source.find(f'if args.command == "{COMMAND_NAME}":')
    assert branch_index >= 0, "team-diagnostics dispatch branch is not declared"

    next_branch_index = source.find("\n    if args.command ==", branch_index + 1)
    assert next_branch_index >= 0, "team-diagnostics dispatch branch has no end marker"
    return source[branch_index:next_branch_index]


def _normalize(value: str) -> str:
    return "".join(character for character in value.lower() if character.isalnum())
