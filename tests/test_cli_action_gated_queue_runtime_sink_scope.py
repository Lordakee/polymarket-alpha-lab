from __future__ import annotations

import ast
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src" / "polymarket_alpha_lab"
CLI_PATH = SRC_ROOT / "cli.py"
RUNNER_PATH = SRC_ROOT / "runner.py"

RUN_DSN_ARG_FRAGMENTS = (
    "dsn",
    "database",
    "database-url",
    "db-url",
    "postgres",
    "postgresql",
    "supabase",
    "connection",
)

RUNNER_FORBIDDEN_IMPORT_FRAGMENTS = (
    "psycopg",
    "supabase",
    "database",
    "_db",
    "db_",
    ".db",
)

FORBIDDEN_RUNTIME_SURFACE_FRAGMENTS = (
    "live",
    "auth",
    "wallet",
    "privatekey",
    "account",
    "order",
    "submission",
    "cancel",
    "signing",
    "signature",
    "signer",
)


def _source(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _parse(path: Path) -> ast.Module:
    return ast.parse(_source(path), filename=str(path))


def _normalize(value: str) -> str:
    return "".join(character for character in value.lower() if character.isalnum())


def _action_gated_queue_related(value: str) -> bool:
    lowered = value.lower().replace("-", "_")
    normalized = _normalize(value)
    return (
        ("action_gated" in lowered or "actiongated" in normalized)
        and "queue" in lowered
    )


def _runtime_wiring_related(value: str) -> bool:
    lowered = value.lower().replace("-", "_")
    return _action_gated_queue_related(value) and any(
        fragment in lowered
        for fragment in ("sink", "source", "db", "psycopg", "supabase")
    )


def _import_references(tree: ast.Module) -> tuple[str, ...]:
    references: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                references.append(alias.name)
                if alias.asname is not None:
                    references.append(alias.asname)
        elif isinstance(node, ast.ImportFrom):
            if node.module is not None:
                references.append(node.module)
            for alias in node.names:
                references.append(alias.name)
                if alias.asname is not None:
                    references.append(alias.asname)
    return tuple(references)


def _run_parser_variable(tree: ast.Module) -> str:
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        if not isinstance(node.value, ast.Call):
            continue
        call = node.value
        if not isinstance(call.func, ast.Attribute):
            continue
        if call.func.attr != "add_parser":
            continue
        if not call.args:
            continue
        command = call.args[0]
        if not isinstance(command, ast.Constant) or command.value != "run":
            continue
        for target in node.targets:
            if isinstance(target, ast.Name):
                return target.id
    raise AssertionError("run subparser variable not found")


def _parser_option_strings(tree: ast.Module, parser_name: str) -> tuple[str, ...]:
    option_strings: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if not isinstance(node.func, ast.Attribute):
            continue
        if node.func.attr != "add_argument":
            continue
        if not isinstance(node.func.value, ast.Name):
            continue
        if node.func.value.id != parser_name:
            continue
        for arg in node.args:
            if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                if arg.value.startswith("-"):
                    option_strings.append(arg.value)
    return tuple(option_strings)


def _command_name_from_test(test: ast.AST) -> str | None:
    if not isinstance(test, ast.Compare):
        return None
    if len(test.ops) != 1 or not isinstance(test.ops[0], ast.Eq):
        return None
    if len(test.comparators) != 1:
        return None
    left = test.left
    right = test.comparators[0]

    if _is_args_command(left) and isinstance(right, ast.Constant):
        if isinstance(right.value, str):
            return right.value
    if _is_args_command(right) and isinstance(left, ast.Constant):
        if isinstance(left.value, str):
            return left.value
    return None


def _is_args_command(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Attribute)
        and node.attr == "command"
        and isinstance(node.value, ast.Name)
        and node.value.id == "args"
    )


def _command_blocks(tree: ast.Module) -> tuple[tuple[str, ast.If], ...]:
    blocks: list[tuple[str, ast.If]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.If):
            continue
        command = _command_name_from_test(node.test)
        if command is not None:
            blocks.append((command, node))
    return tuple(blocks)


def _identifier_values(tree: ast.Module) -> tuple[str, ...]:
    values: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            values.append(node.name)
        elif isinstance(node, ast.Name):
            values.append(node.id)
        elif isinstance(node, ast.Attribute):
            values.append(node.attr)
        elif isinstance(node, ast.arg):
            values.append(node.arg)
        elif isinstance(node, ast.keyword) and node.arg is not None:
            values.append(node.arg)
        elif isinstance(node, ast.alias):
            values.append(node.name)
            if node.asname is not None:
                values.append(node.asname)
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            if node.value.startswith("--"):
                values.append(node.value)
    return tuple(values)


def test_runner_has_no_database_adapter_or_env_imports():
    tree = _parse(RUNNER_PATH)
    violations = tuple(
        reference
        for reference in _import_references(tree)
        if any(
            fragment in reference.lower()
            for fragment in RUNNER_FORBIDDEN_IMPORT_FRAGMENTS
        )
    )

    assert violations == ()


def test_cli_run_command_does_not_add_dsn_or_database_arguments():
    tree = _parse(CLI_PATH)
    run_parser = _run_parser_variable(tree)
    run_options = _parser_option_strings(tree, run_parser)
    violations = tuple(
        option
        for option in run_options
        if any(fragment in option.lower() for fragment in RUN_DSN_ARG_FRAGMENTS)
    )

    assert violations == ()


def test_action_gated_queue_runtime_sink_wiring_stays_under_run_command():
    tree = _parse(CLI_PATH)
    source = _source(CLI_PATH)
    violations: list[tuple[str, int, str]] = []

    for command, node in _command_blocks(tree):
        if command == "run":
            continue
        block_source = ast.get_source_segment(source, node) or ""
        if _runtime_wiring_related(block_source):
            violations.append((command, node.lineno, block_source.splitlines()[0]))

    assert violations == []


def test_action_gated_queue_runtime_names_expose_no_live_trading_surface():
    violations: list[tuple[str, str, str]] = []
    for path in (CLI_PATH, RUNNER_PATH):
        tree = _parse(path)
        for value in _identifier_values(tree) + _import_references(tree):
            if not _runtime_wiring_related(value):
                continue
            normalized = _normalize(value)
            matches = tuple(
                fragment
                for fragment in FORBIDDEN_RUNTIME_SURFACE_FRAGMENTS
                if fragment in normalized
            )
            if matches:
                violations.append((path.name, value, ",".join(matches)))

    assert violations == []
