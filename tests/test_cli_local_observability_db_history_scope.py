from __future__ import annotations

import ast
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CLI_PATH = REPO_ROOT / "src" / "polymarket_alpha_lab" / "cli.py"
COMMAND = "local-observability-trends-db-history"
HELPER = "_run_local_observability_trends_db_history"
SUMMARY = "_print_local_observability_trends_db_history_summary"

EXPECTED_PARSER_ARGUMENT_SURFACE = {
    "--limit",
    "limit",
}

FORBIDDEN_CLI_DB_FLAG_FRAGMENTS = {
    "--dsn",
    "--db-dsn",
    "--local-observability-trends-db-dsn",
    "--local-observability-trends-db-table",
    "--local-observability-trends-db-enabled",
}

FORBIDDEN_PHASE_ONE_ESCAPE_FRAGMENTS = {
    "account",
    "auth",
    "cancel",
    "exchange",
    "insert",
    "live",
    "mutation",
    "order",
    "persist",
    "privatekey",
    "secret",
    "sign",
    "sink",
    "submit",
    "wallet",
    "write",
}

EXPECTED_BRANCH_CALLS = {
    "from_local_observability_trends_db_env",
    HELPER,
    SUMMARY,
    "_raise_redacted_db_read_error",
}

EXPECTED_HELPER_CALLS = {
    "load_local_observability_trends_db_history_report",
    "connect",
    "commit",
    "rollback",
    "close",
    "validate_local_postgres_dsn",
}

EXPECTED_HELPER_IMPORT_MODULES = {
    "polymarket_alpha_lab.local_observability_trends_db_history_load",
    "psycopg",
}

EXPECTED_SUMMARY_STATUS_ROW_REFERENCES = {
    "  status_rows: strategy_evidence=",
    "strategy_evidence_status_rows",
    "outcome_status_rows",
    "nav_status_rows",
    "cost_status_rows",
}

FORBIDDEN_SUMMARY_REFERENCES = {
    "payload_json",
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


def test_local_observability_trends_db_history_parser_surface_is_env_driven() -> None:
    tree = parse_cli()
    parser_variable = _command_parser_variable(tree, COMMAND)
    surface = _parser_argument_surface(tree, parser_variable)

    assert surface == EXPECTED_PARSER_ARGUMENT_SURFACE
    assert not surface & FORBIDDEN_CLI_DB_FLAG_FRAGMENTS


def test_local_observability_trends_db_history_branch_stays_readonly_and_scoped() -> None:
    tree = parse_cli()
    branch = _single_command_branch(tree, COMMAND)
    references = _node_references(branch)
    call_names = _node_call_names(branch)

    assert EXPECTED_BRANCH_CALLS <= call_names
    assert "local-observability-trends-db-history limit must be positive" in references
    _assert_no_forbidden_fragments(references, FORBIDDEN_PHASE_ONE_ESCAPE_FRAGMENTS)


def test_local_observability_trends_db_history_helper_uses_readonly_db_loader_only() -> None:
    tree = parse_cli()
    body = _function_body(tree, HELPER)
    references = _node_references(body)
    call_names = _node_call_names(body)

    assert EXPECTED_HELPER_CALLS <= call_names
    assert EXPECTED_HELPER_IMPORT_MODULES <= _node_import_modules(body)
    config_version = "local-observability-trends-db-history-v0"
    assert config_version in references
    _assert_no_forbidden_fragments(references, FORBIDDEN_PHASE_ONE_ESCAPE_FRAGMENTS)


def test_local_observability_trends_db_history_helper_validates_dsn_before_connect() -> None:
    body = _function_body(parse_cli(), HELPER)
    validator_lines: list[int] = []
    connect_lines: list[int] = []
    for statement in body:
        for node in ast.walk(statement):
            if not isinstance(node, ast.Call):
                continue
            call_name = call_or_attribute_name(node)
            if call_name == "validate_local_postgres_dsn":
                validator_lines.append(node.lineno)
            elif call_name == "connect":
                connect_lines.append(node.lineno)

    assert validator_lines, HELPER
    assert connect_lines, HELPER
    assert min(validator_lines) < min(connect_lines)


def test_local_observability_trends_db_history_summary_is_aggregate_only() -> None:
    tree = parse_cli()
    body = _function_body(tree, SUMMARY)
    references = _node_references(body)

    assert EXPECTED_SUMMARY_STATUS_ROW_REFERENCES <= references
    assert not references & FORBIDDEN_SUMMARY_REFERENCES
