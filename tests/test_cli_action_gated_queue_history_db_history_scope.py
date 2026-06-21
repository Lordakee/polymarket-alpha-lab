from __future__ import annotations

import ast
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CLI_PATH = REPO_ROOT / "src" / "polymarket_alpha_lab" / "cli.py"
COMMAND = "action-gated-queue-history-db-history"
HELPER = "_run_action_gated_queue_history_db_history"
SUMMARY = "_print_action_gated_queue_history_db_history_summary"

EXPECTED_PARSER_ARGUMENT_SURFACE = {
    "--limit",
    "limit",
    "--latest-action-status",
    "latest_action_status",
}

FORBIDDEN_CLI_ARGUMENT_SURFACE = {
    "--dsn",
    "dsn",
    "--db-dsn",
    "db_dsn",
    "--action-gated-queue-history-db-dsn",
    "action_gated_queue_history_db_dsn",
    "--action-gated-queue-history-db-table",
    "action_gated_queue_history_db_table",
    "--action-gated-queue-history-db-enabled",
    "action_gated_queue_history_db_enabled",
    "--source-config-version",
    "source_config_version",
    "--action-status",
    "action_status",
    "--persist",
    "persist",
}

EXPECTED_BRANCH_CALLS = {
    "from_action_gated_strategy_recommendation_queue_history_db_env",
    HELPER,
    SUMMARY,
    "_raise_redacted_db_read_error",
}

NORMAL_BRANCH_CALLS = {
    "ValueError",
    "print",
}

FORBIDDEN_BRANCH_CALLS = {
    "from_action_gated_strategy_recommendation_queue_db_env",
    "_run_action_gated_queue_history",
    "_print_action_gated_queue_history_summary",
    "_raise_redacted_db_sink_error",
}

EXPECTED_HELPER_CALLS = {
    "load_paper_action_gated_strategy_recommendation_queue_history_reports_with_psycopg",
    "build_paper_action_gated_strategy_recommendation_queue_history_db_history_report",
}

EXPECTED_HELPER_IMPORT_MODULES = {
    "polymarket_alpha_lab.action_gated_strategy_recommendation_queue_history_db_history",
    "polymarket_alpha_lab.action_gated_strategy_recommendation_queue_history_psycopg",
}

FORBIDDEN_HELPER_CALLS = {
    "from_action_gated_strategy_recommendation_queue_db_env",
    "load_paper_action_gated_strategy_recommendation_queue_reports_with_psycopg",
    "build_paper_action_gated_strategy_recommendation_queue_history_report",
    "insert_paper_action_gated_strategy_recommendation_queue_history_report",
    "insert_paper_action_gated_strategy_recommendation_queue_history_report_with_psycopg",
    "connect",
    "_connect",
    "commit",
    "rollback",
    "close",
}

FORBIDDEN_HELPER_IMPORT_MODULES = {
    "polymarket_alpha_lab.action_gated_strategy_recommendation_queue_psycopg",
    "polymarket_alpha_lab.action_gated_strategy_recommendation_queue_history",
    "psycopg",
}

FORBIDDEN_HELPER_REFERENCE_FRAGMENTS = {
    "persist",
}

EXPECTED_SUMMARY_REPORT_FIELDS = {
    "history_report_count",
    "first_history_generated_at",
    "latest_history_generated_at",
    "latest_source_report_count",
    "latest_action_status",
    "latest_recommended_next_step",
    "action_status_counts",
    "duplicate_generated_at_count",
    "consecutive_latest_research_ready_count",
    "consecutive_latest_watch_count",
    "consecutive_latest_blocked_count",
    "latest_total_ready_notional",
    "latest_ready_notional_delta",
    "latest_status_transition_count",
    "latest_reason_code_counts",
}

FORBIDDEN_SUMMARY_REFERENCES = {
    "payload",
    "payload_json",
    "dsn",
    "table_name",
    "enabled",
    "report_sha256",
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
        or _is_args_command(comparator)
        and _is_command_literal(test.left, command)
    )


def _command_branch(tree: ast.AST, command: str) -> ast.If:
    for node in ast.walk(tree):
        if isinstance(node, ast.If) and _command_test_matches(node.test, command):
            return node
    raise AssertionError(f"command branch not found: {command}")


def _function_def(tree: ast.AST, name: str) -> ast.FunctionDef:
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    raise AssertionError(f"function not found: {name}")


def _function_body(tree: ast.AST, name: str) -> list[ast.stmt]:
    return _function_def(tree, name).body


def _node_references(node_or_nodes: ast.AST | list[ast.AST]) -> set[str]:
    nodes = node_or_nodes if isinstance(node_or_nodes, list) else [node_or_nodes]
    references: set[str] = set()
    for node in nodes:
        for child in ast.walk(node):
            if isinstance(child, ast.Name):
                references.add(child.id)
            elif isinstance(child, ast.Attribute):
                references.add(child.attr)
            elif isinstance(child, ast.Constant) and isinstance(child.value, str):
                references.add(child.value)
    return references


def _call_names(node_or_nodes: ast.AST | list[ast.AST]) -> set[str]:
    nodes = node_or_nodes if isinstance(node_or_nodes, list) else [node_or_nodes]
    names: set[str] = set()
    for node in nodes:
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                name = call_or_attribute_name(child)
                if name is not None:
                    names.add(name)
    return names


def _import_modules(node_or_nodes: ast.AST | list[ast.AST]) -> set[str]:
    nodes = node_or_nodes if isinstance(node_or_nodes, list) else [node_or_nodes]
    modules: set[str] = set()
    for node in nodes:
        for child in ast.walk(node):
            if isinstance(child, ast.Import):
                modules.update(alias.name for alias in child.names)
            elif isinstance(child, ast.ImportFrom) and child.module is not None:
                modules.add(child.module)
    return modules


def _literal_strings(node_or_nodes: ast.AST | list[ast.AST]) -> set[str]:
    nodes = node_or_nodes if isinstance(node_or_nodes, list) else [node_or_nodes]
    values: set[str] = set()
    for node in nodes:
        for child in ast.walk(node):
            if isinstance(child, ast.Constant) and isinstance(child.value, str):
                values.add(child.value)
    return values


def _parser_assignment(tree: ast.AST) -> ast.Assign:
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        if not any(
            isinstance(target, ast.Name)
            and target.id == "action_gated_queue_history_db_history"
            for target in node.targets
        ):
            continue
        if COMMAND in _literal_strings(node):
            return node
    raise AssertionError("parser assignment not found")


def _parser_block(tree: ast.AST) -> list[ast.stmt]:
    main_def = _function_def(tree, "main")
    body = main_def.body
    for index, node in enumerate(body):
        if node is _parser_assignment(tree):
            block = [node]
            for following in body[index + 1 :]:
                if (
                    isinstance(following, ast.Assign)
                    and any(isinstance(target, ast.Name) for target in following.targets)
                ):
                    break
                block.append(following)
            return block
    raise AssertionError("parser block not found")


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


def test_action_gated_queue_history_db_history_parser_surface_is_env_driven() -> None:
    tree = parse_cli()
    parser_block = _parser_block(tree)
    references = _node_references(parser_block)

    assert COMMAND in references
    assert EXPECTED_PARSER_ARGUMENT_SURFACE <= references
    assert not (FORBIDDEN_CLI_ARGUMENT_SURFACE & references)


def test_action_gated_queue_history_db_history_branch_is_read_only() -> None:
    tree = parse_cli()
    branch = _command_branch(tree, COMMAND)
    calls = _call_names(branch)
    references = _node_references(branch)

    assert EXPECTED_BRANCH_CALLS <= calls
    assert not (FORBIDDEN_BRANCH_CALLS & calls)
    assert "action_gated_queue_history_db_history_runner" in references
    assert "action_gated_queue_history_builder" not in references
    assert "action_gated_queue_history_db_sink" not in references


def test_action_gated_queue_history_db_history_helper_imports_persisted_history_only() -> None:
    tree = parse_cli()
    body = _function_body(tree, HELPER)
    calls = _call_names(body)
    imports = _import_modules(body)
    references = _node_references(body)

    assert EXPECTED_HELPER_CALLS <= calls
    assert EXPECTED_HELPER_IMPORT_MODULES <= imports
    assert not (FORBIDDEN_HELPER_CALLS & calls)
    assert not (FORBIDDEN_HELPER_IMPORT_MODULES & imports)
    for forbidden in FORBIDDEN_HELPER_REFERENCE_FRAGMENTS:
        assert forbidden not in references


def test_action_gated_queue_history_db_history_summary_is_aggregate_only() -> None:
    tree = parse_cli()
    body = _function_body(tree, SUMMARY)
    references = _node_references(body)
    report_fields = _report_attribute_names(body)

    assert EXPECTED_SUMMARY_REPORT_FIELDS <= report_fields
    assert report_fields <= EXPECTED_SUMMARY_REPORT_FIELDS
    for forbidden in FORBIDDEN_SUMMARY_REFERENCES:
        forbidden_key = normalize_identifier(forbidden)
        assert all(
            forbidden_key not in normalize_identifier(reference)
            for reference in references
        )
