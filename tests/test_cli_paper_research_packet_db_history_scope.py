from __future__ import annotations

import ast
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CLI_PATH = REPO_ROOT / "src" / "polymarket_alpha_lab" / "cli.py"
COMMAND = "paper-research-packet-db-history"
HELPER = "_run_paper_research_packet_db_history"
SUMMARY = "_print_paper_research_packet_db_history_summary"
HISTORY_CONFIG_VERSION = "paper-research-packet-db-history-v0"
HISTORY_CONFIG_CONSTANT = "DEFAULT_PAPER_RESEARCH_PACKET_DB_HISTORY_CONFIG_VERSION"

EXPECTED_PARSER_ARGUMENT_SURFACE = {
    "--limit",
    "limit",
}

FORBIDDEN_PARSER_ARGUMENT_SURFACE = {
    "--dsn",
    "dsn",
    "--db-dsn",
    "db_dsn",
    "--paper-research-packet-db-dsn",
    "paper_research_packet_db_dsn",
    "--paper-research-packet-db-table",
    "paper_research_packet_db_table",
    "--paper-research-packet-db-enabled",
    "paper_research_packet_db_enabled",
    "--source-config-version",
    "source_config_version",
    "--action-status",
    "action_status",
    "--research-status",
    "research_status",
    "--packet-config-version",
    "packet_config_version",
    "--max-packet-rows",
    "max_packet_rows",
    "--min-score",
    "min_score",
    "--persist",
    "persist",
    "--config-version",
    "config_version",
    "--table",
    "table",
}

FORBIDDEN_PHASE_ONE_ESCAPE_FRAGMENTS = {
    "account",
    "auth",
    "cancel",
    "clientfactory",
    "exchange",
    "insert",
    "live",
    "mutation",
    "order",
    "persist",
    "privatekey",
    "sign",
    "sink",
    "submit",
    "wallet",
    "write",
}

EXPECTED_BRANCH_CALLS = {
    "from_paper_research_packet_db_env",
    HELPER,
    SUMMARY,
}

FORBIDDEN_BRANCH_CALLS = {
    "from_strategy_candidate_research_queue_db_env",
    "_run_paper_research_packet",
    "_print_paper_research_packet_summary",
}

EXPECTED_HELPER_IMPORT_MODULES = {
    "polymarket_alpha_lab.paper_research_packet_db_history_load",
    "psycopg",
}

EXPECTED_HELPER_CALLS = {
    "PaperResearchPacketDbHistoryConfig",
    "load_paper_research_packet_db_history_report",
    "connect",
    "close",
}

FORBIDDEN_HELPER_CALLS = {
    "commit",
    "rollback",
    "insert",
    "insert_paper_research_packet_report_with_psycopg",
    "from_paper_research_packet_db_env",
    "from_strategy_candidate_research_queue_db_env",
    "load_paper_strategy_candidate_research_queue_reports_with_psycopg",
}

FORBIDDEN_HELPER_IMPORT_MODULES = {
    "polymarket_alpha_lab.paper_research_packet_psycopg",
    "polymarket_alpha_lab.strategy_candidate_research_queue_psycopg_read",
    "polymarket_alpha_lab.strategy_candidate_research_packet_source",
}

EXPECTED_SUMMARY_REPORT_FIELDS = {
    "report_count",
    "first_report_generated_at",
    "latest_report_generated_at",
    "duplicate_generated_at_count",
    "latest_packet_config_version",
    "latest_input_row_count",
    "latest_packet_row_count",
    "latest_included_count",
    "latest_skipped_count",
    "latest_high_priority_count",
    "latest_medium_priority_count",
    "latest_low_priority_count",
    "latest_top_packet_rank",
    "latest_top_packet_market_slug",
    "latest_top_packet_side",
    "latest_top_packet_research_priority",
    "latest_top_packet_recommendation_score",
    "latest_top_packet_net_edge",
    "latest_top_packet_allocated_notional",
    "latest_top_packet_requested_notional",
    "latest_top_packet_reason_codes",
}

FORBIDDEN_SUMMARY_REFERENCES = {
    "question",
    "required_checks",
    "packet_rows",
    "payload_json",
    "report_sha256",
    "dsn",
    "table_name",
    "enabled",
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


def _is_args_command(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Attribute)
        and node.attr == "command"
        and isinstance(node.value, ast.Name)
        and node.value.id == "args"
    )


def _is_command_literal(node: ast.AST, command: str) -> bool:
    return isinstance(node, ast.Constant) and node.value == command


def _command_test_matches(test: ast.AST, command: str) -> bool:
    if isinstance(test, ast.BoolOp):
        return any(_command_test_matches(value, command) for value in test.values)
    if not isinstance(test, ast.Compare) or len(test.ops) != 1:
        return False
    if not isinstance(test.ops[0], ast.Eq) or len(test.comparators) != 1:
        return False
    comparator = test.comparators[0]
    return (
        _is_args_command(test.left)
        and _is_command_literal(comparator, command)
    ) or (
        _is_command_literal(test.left, command)
        and _is_args_command(comparator)
    )


def _single_command_branch(tree: ast.AST, command: str) -> list[ast.stmt]:
    branches = [
        node.body
        for node in ast.walk(tree)
        if isinstance(node, ast.If) and _command_test_matches(node.test, command)
    ]
    assert len(branches) == 1, (command, len(branches))
    return branches[0]


def _function_body(tree: ast.AST, name: str) -> list[ast.stmt]:
    functions = [
        node.body
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == name
    ]
    assert len(functions) == 1, (name, len(functions))
    return functions[0]


def _node_references(nodes: list[ast.stmt]) -> set[str]:
    references: set[str] = set()
    for statement in nodes:
        for node in ast.walk(statement):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                references.add(node.name)
            elif isinstance(node, ast.Name):
                references.add(node.id)
            elif isinstance(node, ast.Attribute):
                references.add(node.attr)
            elif isinstance(node, ast.arg):
                references.add(node.arg)
            elif isinstance(node, ast.keyword) and node.arg is not None:
                references.add(node.arg)
            elif isinstance(node, ast.alias):
                references.add(node.name)
                if node.asname is not None:
                    references.add(node.asname)
            elif isinstance(node, ast.Constant) and isinstance(node.value, str):
                references.add(node.value)
    return references


def _node_call_names(nodes: list[ast.stmt]) -> set[str]:
    call_names: set[str] = set()
    for statement in nodes:
        for node in ast.walk(statement):
            if isinstance(node, ast.Call):
                name = call_or_attribute_name(node)
                if name is not None:
                    call_names.add(name)
    return call_names


def _node_import_modules(nodes: list[ast.stmt]) -> set[str]:
    modules: set[str] = set()
    for statement in nodes:
        for node in ast.walk(statement):
            if isinstance(node, ast.Import):
                modules.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                assert node.level == 0
                modules.add(node.module or "")
    return modules


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


def _report_attribute_names(body: list[ast.stmt]) -> set[str]:
    names: set[str] = set()
    for node in body:
        for child in ast.walk(node):
            if (
                isinstance(child, ast.Attribute)
                and isinstance(child.value, ast.Name)
                and child.value.id == "report"
            ):
                names.add(child.attr)
    return names


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


def test_packet_db_history_parser_surface_is_exactly_limit_only() -> None:
    tree = parse_cli()
    parser_variable = _command_parser_variable(tree, COMMAND)
    surface = _parser_argument_surface(tree, parser_variable)

    assert surface == EXPECTED_PARSER_ARGUMENT_SURFACE
    assert not (surface & FORBIDDEN_PARSER_ARGUMENT_SURFACE)
    _assert_no_forbidden_fragments(surface, FORBIDDEN_PHASE_ONE_ESCAPE_FRAGMENTS)


def test_packet_db_history_branch_is_packet_db_read_only() -> None:
    tree = parse_cli()
    branch = _single_command_branch(tree, COMMAND)
    call_names = _node_call_names(branch)
    references = _node_references(branch)

    assert EXPECTED_BRANCH_CALLS <= call_names
    assert not (FORBIDDEN_BRANCH_CALLS & call_names)
    assert "paper_research_packet_db_history_runner" in references
    assert "paper_research_packet_builder" not in references
    assert "paper_research_packet_db_sink" not in references
    _assert_no_forbidden_fragments(references, FORBIDDEN_PHASE_ONE_ESCAPE_FRAGMENTS)


def test_packet_db_history_helper_uses_task2_loader_and_readonly_connection() -> None:
    tree = parse_cli()
    helper = _function_body(tree, HELPER)
    call_names = _node_call_names(helper)
    import_modules = _node_import_modules(helper)
    references = _node_references(helper)

    assert EXPECTED_HELPER_CALLS <= call_names
    assert import_modules == EXPECTED_HELPER_IMPORT_MODULES
    assert not (FORBIDDEN_HELPER_CALLS & call_names)
    assert not (FORBIDDEN_HELPER_IMPORT_MODULES & import_modules)
    assert HISTORY_CONFIG_CONSTANT in references
    _assert_no_forbidden_fragments(references, FORBIDDEN_PHASE_ONE_ESCAPE_FRAGMENTS)


def test_packet_db_history_summary_is_aggregate_and_top_packet_only() -> None:
    tree = parse_cli()
    summary = _function_body(tree, SUMMARY)
    references = _node_references(summary)
    report_fields = _report_attribute_names(summary)

    assert EXPECTED_SUMMARY_REPORT_FIELDS <= report_fields
    assert report_fields <= EXPECTED_SUMMARY_REPORT_FIELDS
    for forbidden in FORBIDDEN_SUMMARY_REFERENCES:
        forbidden_key = normalize_identifier(forbidden)
        assert all(
            forbidden_key not in normalize_identifier(reference)
            for reference in references
        )
    _assert_no_forbidden_fragments(references, FORBIDDEN_PHASE_ONE_ESCAPE_FRAGMENTS)
