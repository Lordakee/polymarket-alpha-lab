from __future__ import annotations

import ast
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CLI_PATH = REPO_ROOT / "src" / "polymarket_alpha_lab" / "cli.py"
COMMAND = "strategy-audit-db-history"

EXPECTED_PARSER_ARGUMENT_SURFACE = {
    "--limit",
    "limit",
}

FORBIDDEN_CLI_DB_FLAG_FRAGMENTS = {
    "--strategy-risk-audit-db-dsn",
    "--strategy-risk-audit-db-table",
    "--strategy-risk-audit-db-enabled",
}

FORBIDDEN_PHASE_ONE_ESCAPE_FRAGMENTS = {
    "account",
    "auth",
    "cancel",
    "client",
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
    "from_strategy_risk_audit_db_env",
    "_run_strategy_audit_db_history",
    "_print_strategy_audit_history_summary",
    "_raise_redacted_db_read_error",
}

EXPECTED_HELPER_CALLS = {
    "PaperStrategyRiskAuditHistoryConfig",
    "load_strategy_audit_db_history_report",
    "connect",
    "commit",
    "rollback",
    "close",
}

EXPECTED_HELPER_IMPORT_MODULES = {
    "polymarket_alpha_lab.strategy_audit_db_history_load",
    "psycopg",
}

FORBIDDEN_SUMMARY_REFERENCES = {
    "payload_json",
    "observed_value",
    "threshold",
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
            if not isinstance(node, ast.Call):
                continue
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
        if not call.args or not _is_command_literal(call.args[0], command):
            continue
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


def _assert_no_forbidden_phase_one_escape(references: set[str]) -> None:
    normalized_references = {
        normalize_identifier(reference) for reference in references
    }
    for fragment in FORBIDDEN_PHASE_ONE_ESCAPE_FRAGMENTS:
        normalized_fragment = normalize_identifier(fragment)
        matching_references = tuple(
            sorted(
                reference
                for reference in normalized_references
                if normalized_fragment in reference
            )
        )
        assert matching_references == (), (fragment, matching_references)


def test_strategy_audit_db_history_parser_surface_is_exactly_read_only():
    tree = parse_cli()
    parser_variable = _command_parser_variable(tree, COMMAND)
    surface = _parser_argument_surface(tree, parser_variable)

    assert surface == EXPECTED_PARSER_ARGUMENT_SURFACE
    for fragment in FORBIDDEN_CLI_DB_FLAG_FRAGMENTS:
        assert fragment not in surface
    _assert_no_forbidden_phase_one_escape(surface)


def test_strategy_audit_db_history_branch_stays_read_only():
    tree = parse_cli()
    branch = _single_command_branch(tree, COMMAND)
    call_names = _node_call_names(branch)
    references = _node_references(branch)

    assert EXPECTED_BRANCH_CALLS.issubset(call_names)
    _assert_no_forbidden_phase_one_escape(references)


def test_strategy_audit_db_history_helper_uses_only_read_path_wiring():
    tree = parse_cli()
    helper = _function_body(tree, "_run_strategy_audit_db_history")
    call_names = _node_call_names(helper)
    import_modules = _node_import_modules(helper)
    references = _node_references(helper)

    assert EXPECTED_HELPER_CALLS.issubset(call_names)
    assert import_modules == EXPECTED_HELPER_IMPORT_MODULES
    assert "strategy-audit-db-history-v0" in references
    _assert_no_forbidden_phase_one_escape(references)


def test_strategy_audit_db_history_summary_stays_aggregate_only():
    tree = parse_cli()
    summary = _function_body(tree, "_print_strategy_audit_history_summary")
    references = _node_references(summary)
    normalized_references = {normalize_identifier(value) for value in references}

    for fragment in FORBIDDEN_SUMMARY_REFERENCES:
        assert fragment not in references
        assert normalize_identifier(fragment) not in normalized_references
    _assert_no_forbidden_phase_one_escape(references)
