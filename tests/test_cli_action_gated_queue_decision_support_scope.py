from __future__ import annotations

import ast
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CLI_PATH = REPO_ROOT / "src" / "polymarket_alpha_lab" / "cli.py"
COMMAND = "action-gated-queue-decision-support"

EXPECTED_PARSER_ARGUMENT_SURFACE = {
    "--source-config-version",
    "source_config_version",
    "--action-status",
    "action_status",
    "--limit",
    "limit",
    "--max-total-ready-notional",
    "max_total_ready_notional",
    "--max-single-queue-ready-notional",
    "max_single_queue_ready_notional",
    "--max-ready-candidate-count",
    "max_ready_candidate_count",
    "--max-total-candidate-count",
    "max_total_candidate_count",
    "--throttle-utilization-threshold",
    "throttle_utilization_threshold",
}

FORBIDDEN_LIVE_SURFACE_FRAGMENTS = {
    "account",
    "auth",
    "cancel",
    "client",
    "clientfactory",
    "exchange",
    "insert",
    "live",
    "order",
    "privatekey",
    "sign",
    "sink",
    "submit",
    "wallet",
}

EXPECTED_BRANCH_CALLS = {
    "_run_action_gated_queue_decision_support",
    "_print_action_gated_queue_decision_support_summary",
}

EXPECTED_RUN_HELPER_CALLS = {
    "from_action_gated_strategy_recommendation_queue_db_env",
    "PaperActionGatedStrategyRecommendationQueueReadOptions",
    "PaperActionGatedStrategyRecommendationQueueRiskConfig",
}

EXPECTED_DEFAULT_WIRING_NAMES = {
    "load_paper_action_gated_strategy_recommendation_queue_reports_with_psycopg",
    "build_paper_action_gated_strategy_recommendation_queue_priority_report",
    "build_paper_action_gated_strategy_recommendation_queue_risk_report",
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


def _assert_no_forbidden_surface(references: set[str]) -> None:
    normalized_references = {
        normalize_identifier(reference) for reference in references
    }
    for fragment in FORBIDDEN_LIVE_SURFACE_FRAGMENTS:
        normalized_fragment = normalize_identifier(fragment)
        matching_references = tuple(
            sorted(
                reference
                for reference in normalized_references
                if normalized_fragment in reference
            )
        )
        assert matching_references == (), (fragment, matching_references)


def test_action_gated_queue_decision_support_parser_surface_is_exactly_read_only():
    tree = parse_cli()
    parser_variable = _command_parser_variable(tree, COMMAND)
    surface = _parser_argument_surface(tree, parser_variable)

    assert surface == EXPECTED_PARSER_ARGUMENT_SURFACE
    _assert_no_forbidden_surface(surface)


def test_action_gated_queue_decision_support_branch_is_read_only_report_only():
    tree = parse_cli()
    branch = _single_command_branch(tree, COMMAND)
    call_names = _node_call_names(branch)

    assert EXPECTED_BRANCH_CALLS.issubset(call_names)
    _assert_no_forbidden_surface(_node_references(branch))


def test_action_gated_queue_decision_support_helper_uses_only_loader_and_builders():
    tree = parse_cli()
    helper = _function_body(tree, "_run_action_gated_queue_decision_support")
    call_names = _node_call_names(helper)
    references = _node_references(helper)

    assert EXPECTED_RUN_HELPER_CALLS.issubset(call_names)
    assert EXPECTED_DEFAULT_WIRING_NAMES.issubset(references)
    _assert_no_forbidden_surface(references)


def test_action_gated_queue_decision_support_summary_prints_aggregate_fields_only():
    tree = parse_cli()
    summary = _function_body(
        tree,
        "_print_action_gated_queue_decision_support_summary",
    )
    references = _node_references(summary)

    assert "payload_json" not in references
    assert "dsn" not in {normalize_identifier(value) for value in references}
    _assert_no_forbidden_surface(references)
