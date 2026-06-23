from __future__ import annotations

import ast
from pathlib import Path

import pytest

from polymarket_alpha_lab.cli import main


REPO_ROOT = Path(__file__).resolve().parents[1]
CLI_PATH = REPO_ROOT / "src" / "polymarket_alpha_lab" / "cli.py"
README_PATH = REPO_ROOT / "README.md"
COMMAND = "paper-research-packet-operator-flow-db-history-gate"
RUN_HELPER = "_run_paper_research_packet_operator_flow_db_history_gate"
SUMMARY_PRINTER = "_print_paper_research_packet_operator_flow_db_history_gate_summary"

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
    "--strategy-candidate-research-queue-db-dsn",
    "strategy_candidate_research_queue_db_dsn",
    "--strategy-candidate-research-queue-db-table",
    "strategy_candidate_research_queue_db_table",
    "--strategy-candidate-research-queue-db-enabled",
    "strategy_candidate_research_queue_db_enabled",
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
    "--signing-key",
    "signing_key",
    "--api-key",
    "api_key",
    "--account",
    "account",
    "--exchange",
    "exchange",
    "--order",
    "order",
    "--relayer",
    "relayer",
    "--network",
    "network",
    "--fast",
    "fast",
}

RUNTIME_FORBIDDEN_FLAGS = (
    "--account",
    "--api-key",
    "--auth",
    "--db-dsn",
    "--dsn",
    "--exchange",
    "--fast",
    "--live",
    "--order",
    "--paper-research-packet-db-dsn",
    "--paper-research-packet-db-table",
    "--paper-research-packet-operator-flow-db-dsn",
    "--paper-research-packet-operator-flow-db-table",
    "--paper-research-packet-quality-db-dsn",
    "--paper-research-packet-quality-db-table",
    "--persist",
    "--private-key",
    "--relayer",
    "--signing-key",
    "--table",
    "--trade",
    "--wallet",
)

FORBIDDEN_SOURCE_ESCAPE_FRAGMENTS = {
    "account",
    "auth",
    "cancel",
    "clientfactory",
    "direct",
    "exchange",
    "fast",
    "insert",
    "live",
    "mutation",
    "order",
    "paperexecution",
    "privatekey",
    "relayer",
    "sign",
    "signing",
    "sink",
    "submit",
    "trade",
    "wallet",
}

ALLOWED_RUN_HELPER_IMPORTS = {
    "polymarket_alpha_lab.paper_research_packet_operator_flow_db_history",
    "polymarket_alpha_lab.paper_research_packet_operator_flow_db_history_gate",
    "polymarket_alpha_lab.paper_research_packet_operator_flow_db_history_gate_load",
    "psycopg",
}

SUMMARY_REQUIRED_FIELDS = {
    "gate_status",
    "recommended_next_step",
    "source_report_count",
    "source_history_status",
    "latest_flow_status",
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
    "allocated_notional",
    "requested_notional",
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


def test_gate_parser_surface_is_limit_only_and_readonly() -> None:
    tree = parse_cli()
    parser_variable = _command_parser_variable(tree, COMMAND)
    surface = _parser_argument_surface(tree, parser_variable)

    assert surface == EXPECTED_PARSER_ARGUMENT_SURFACE
    assert not (surface & FORBIDDEN_PARSER_ARGUMENT_SURFACE)


def test_gate_cli_rejects_direct_db_live_auth_wallet_and_fast_flags(
    capsys: pytest.CaptureFixture[str],
) -> None:
    for flag in RUNTIME_FORBIDDEN_FLAGS:
        with pytest.raises(SystemExit) as exc_info:
            main([COMMAND, flag, "forbidden-value"])

        assert exc_info.value.code == 2
        captured = capsys.readouterr()
        assert f"unrecognized arguments: {flag}" in captured.err


def test_gate_run_helper_stays_on_readonly_env_db_history_source_path() -> None:
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
    assert "PaperResearchPacketOperatorFlowDbHistoryConfig" in references
    assert "PaperResearchPacketOperatorFlowDbHistoryGateConfig" in references
    assert "load_paper_research_packet_operator_flow_db_history_gate_report" in references
    assert "connect" in references
    assert "close" in references
    assert not (references & forbidden_calls)


def test_gate_summary_printer_is_aggregate_only_without_sensitive_details() -> None:
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


def test_readme_documents_exact_gate_command_and_paper_readonly_decision_support() -> None:
    readme = README_PATH.read_text(encoding="utf-8")

    assert COMMAND in readme
    assert (
        "The gate is a paper-only/read-only decision-support signal. It does not "
        "place orders, sign messages, read wallets/accounts, or mutate exchange "
        "state. Only a `pass` gate should be treated by downstream paper automation "
        "as eligible to advance."
    ) in readme
