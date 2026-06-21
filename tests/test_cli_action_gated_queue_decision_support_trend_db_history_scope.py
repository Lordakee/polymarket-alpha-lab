from __future__ import annotations

import ast
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CLI_PATH = REPO_ROOT / "src" / "polymarket_alpha_lab" / "cli.py"
COMMAND = "action-gated-queue-decision-support-trend-db-history"
HELPER = "_run_action_gated_queue_decision_support_trend_db_history"
SUMMARY = "_print_action_gated_queue_decision_support_trend_db_history_summary"

EXPECTED_PARSER_ARGUMENT_SURFACE = {
    "--limit",
    "limit",
    "--latest-risk-status",
    "latest_risk_status",
}

FORBIDDEN_CLI_ARGUMENT_SURFACE = {
    "--dsn",
    "dsn",
    "--db-dsn",
    "db_dsn",
    "--action-gated-queue-decision-support-trend-db-dsn",
    "action_gated_queue_decision_support_trend_db_dsn",
    "--action-gated-queue-decision-support-trend-db-reports-table",
    "action_gated_queue_decision_support_trend_db_reports_table",
    "--action-gated-queue-decision-support-trend-db-sources-table",
    "action_gated_queue_decision_support_trend_db_sources_table",
    "--action-gated-queue-decision-support-trend-db-enabled",
    "action_gated_queue_decision_support_trend_db_enabled",
    "--source-limit",
    "source_limit",
    "--source-risk-status",
    "source_risk_status",
    "--persist",
    "persist",
}

EXPECTED_BRANCH_CALLS = {
    "from_action_gated_strategy_recommendation_queue_decision_support_trend_db_env",
    HELPER,
    SUMMARY,
    "_raise_redacted_db_read_error",
}

NORMAL_BRANCH_CALLS = {
    "ValueError",
    "print",
}

FORBIDDEN_BRANCH_CALLS = {
    "from_action_gated_strategy_recommendation_queue_decision_support_db_env",
    "_run_action_gated_queue_decision_support_trend",
    "_print_action_gated_queue_decision_support_trend_summary",
    "_raise_redacted_db_sink_error",
}

EXPECTED_HELPER_CALLS = {
    (
        "load_paper_action_gated_strategy_recommendation_queue_decision_support_"
        "trend_db_rows_with_psycopg"
    ),
    (
        "build_paper_action_gated_strategy_recommendation_queue_decision_support_"
        "trend_db_history_report"
    ),
}

EXPECTED_HELPER_IMPORT_MODULES = {
    (
        "polymarket_alpha_lab.action_gated_strategy_recommendation_queue_"
        "decision_support_trend_db_history"
    ),
    (
        "polymarket_alpha_lab.action_gated_strategy_recommendation_queue_"
        "decision_support_trend_psycopg"
    ),
}

FORBIDDEN_HELPER_CALLS = {
    "from_action_gated_strategy_recommendation_queue_decision_support_db_env",
    "load_paper_action_gated_strategy_recommendation_queue_decision_support_reports_with_psycopg",
    "build_paper_action_gated_strategy_recommendation_queue_decision_support_trend_report",
    "insert_paper_action_gated_strategy_recommendation_queue_decision_support_trend_db_rows",
    (
        "insert_paper_action_gated_strategy_recommendation_queue_decision_support_"
        "trend_db_rows_with_psycopg"
    ),
    "connect",
    "_connect",
    "commit",
    "rollback",
    "close",
}

FORBIDDEN_HELPER_IMPORT_MODULES = {
    "polymarket_alpha_lab.action_gated_strategy_recommendation_queue_decision_support_psycopg",
    "polymarket_alpha_lab.action_gated_strategy_recommendation_queue_decision_support_trend",
    "psycopg",
}

FORBIDDEN_HELPER_REFERENCE_FRAGMENTS = {
    "persist",
}

EXPECTED_SUMMARY_REPORT_FIELDS = {
    "trend_count",
    "total_source_snapshot_count",
    "first_trend_generated_at",
    "latest_trend_generated_at",
    "latest_risk_status",
    "risk_status_counts",
    "ready_notional_delta",
    "top_priority_score_delta",
    "average_priority_score_delta",
    "source_queue_count_delta",
    "duplicate_generated_at_count",
    "consecutive_latest_watch_count",
    "consecutive_latest_blocked_count",
    "latest_reason_code_counts",
}

FORBIDDEN_SUMMARY_REFERENCES = {
    "payload_json",
    "priority_payload",
    "priority_payload_json",
    "risk_payload",
    "risk_payload_json",
    "dsn",
    "reports_table_name",
    "sources_table_name",
    "enabled",
    "snapshot_sha256",
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


def _report_attribute_names(nodes: list[ast.stmt]) -> set[str]:
    names: set[str] = set()
    for statement in nodes:
        for node in ast.walk(statement):
            if (
                isinstance(node, ast.Attribute)
                and isinstance(node.value, ast.Name)
                and node.value.id == "report"
            ):
                names.add(node.attr)
    return names


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
    normalized_references = {normalize_identifier(reference) for reference in references}
    for fragment in fragments:
        normalized_fragment = normalize_identifier(fragment)
        matches = tuple(
            sorted(
                reference
                for reference in references
                if normalized_fragment in normalize_identifier(reference)
            ),
        )
        assert not matches, (fragment, matches, normalized_references)


def test_action_gated_queue_decision_support_trend_db_history_parser_surface_is_env_driven(
) -> None:
    tree = parse_cli()
    parser_variable = _command_parser_variable(tree, COMMAND)
    surface = _parser_argument_surface(tree, parser_variable)

    assert surface == EXPECTED_PARSER_ARGUMENT_SURFACE
    assert not surface & FORBIDDEN_CLI_ARGUMENT_SURFACE


def test_action_gated_queue_decision_support_trend_db_history_branch_is_trend_db_readonly() -> None:
    tree = parse_cli()
    branch = _single_command_branch(tree, COMMAND)
    references = _node_references(branch)
    call_names = _node_call_names(branch)

    assert EXPECTED_BRANCH_CALLS <= call_names
    assert call_names <= EXPECTED_BRANCH_CALLS | NORMAL_BRANCH_CALLS
    assert not call_names & FORBIDDEN_BRANCH_CALLS
    assert (
        "action-gated-queue-decision-support-trend-db-history limit must be positive"
        in references
    )


def test_trend_db_history_helper_uses_trend_db_history_loader_only(
) -> None:
    tree = parse_cli()
    body = _function_body(tree, HELPER)
    references = _node_references(body)
    call_names = _node_call_names(body)
    import_modules = _node_import_modules(body)

    assert EXPECTED_HELPER_CALLS <= call_names
    assert EXPECTED_HELPER_IMPORT_MODULES <= import_modules
    assert not call_names & FORBIDDEN_HELPER_CALLS
    assert not import_modules & FORBIDDEN_HELPER_IMPORT_MODULES
    assert "action-gated-queue-decision-support-trend-db-history-v0" in references
    _assert_no_forbidden_fragments(references, FORBIDDEN_HELPER_REFERENCE_FRAGMENTS)


def test_action_gated_queue_decision_support_trend_db_history_summary_is_aggregate_only() -> None:
    tree = parse_cli()
    body = _function_body(tree, SUMMARY)
    references = _node_references(body)
    report_fields = _report_attribute_names(body)

    assert EXPECTED_SUMMARY_REPORT_FIELDS <= report_fields
    assert report_fields <= EXPECTED_SUMMARY_REPORT_FIELDS
    assert not references & FORBIDDEN_SUMMARY_REFERENCES
