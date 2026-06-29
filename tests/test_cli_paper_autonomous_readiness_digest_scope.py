from __future__ import annotations

import ast
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CLI_PATH = REPO_ROOT / "src" / "polymarket_alpha_lab" / "cli.py"
COMMAND = "paper-autonomous-readiness-digest"
HELPER = "_run_paper_autonomous_readiness_digest"
SUMMARY = "_print_paper_autonomous_readiness_digest_summary"
READINESS_DB_ENV = "from_paper_autonomous_readiness_gate_db_env"
DIGEST_DB_ENV = "from_paper_autonomous_readiness_digest_db_env"
AGREEMENT_DB_ENV = "from_probability_selection_scorer_agreement_db_env"
LOCAL_POSTGRES_DSN_VALIDATOR = "validate_local_postgres_dsn"
DEFAULT_DIGEST_DB_SINK = "insert_paper_autonomous_readiness_digest_report_with_psycopg"
FORBIDDEN_MUTATING_OR_PRIVATE_REFS = (
    "commit",
    "rollback",
    "insert",
    "update",
    "upsert",
    "delete",
    "open",
    "write",
    "wallet",
    "order",
    "auth",
    "private_key",
    "PolymarketPublicClient",
    "fast",
)


def _parse_cli() -> ast.AST:
    return ast.parse(CLI_PATH.read_text(encoding="utf-8"), filename=str(CLI_PATH))


def _is_args_command(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Attribute)
        and node.attr == "command"
        and isinstance(node.value, ast.Name)
        and node.value.id == "args"
    )


def _command_test_matches(test: ast.AST) -> bool:
    if isinstance(test, ast.BoolOp):
        return any(_command_test_matches(value) for value in test.values)
    if not isinstance(test, ast.Compare) or len(test.ops) != 1:
        return False
    if not isinstance(test.ops[0], ast.Eq) or len(test.comparators) != 1:
        return False
    comparator = test.comparators[0]
    return (
        _is_args_command(test.left)
        and isinstance(comparator, ast.Constant)
        and comparator.value == COMMAND
    ) or (
        isinstance(test.left, ast.Constant)
        and test.left.value == COMMAND
        and _is_args_command(comparator)
    )


def _command_branch(tree: ast.AST) -> list[ast.stmt]:
    branches = [
        node.body
        for node in ast.walk(tree)
        if isinstance(node, ast.If) and _command_test_matches(node.test)
    ]
    assert len(branches) == 1
    return branches[0]


def _function_body(tree: ast.AST, name: str) -> list[ast.stmt]:
    functions = [
        node.body
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == name
    ]
    assert len(functions) == 1
    return functions[0]


def _references(nodes: list[ast.stmt]) -> set[str]:
    values: set[str] = set()
    for statement in nodes:
        for node in ast.walk(statement):
            if isinstance(node, ast.Name):
                values.add(node.id)
            elif isinstance(node, ast.Attribute):
                values.add(node.attr)
            elif isinstance(node, ast.arg):
                values.add(node.arg)
            elif isinstance(node, ast.keyword) and node.arg is not None:
                values.add(node.arg)
            elif isinstance(node, ast.ImportFrom) and node.module is not None:
                values.add(node.module)
            elif isinstance(node, ast.Constant) and isinstance(node.value, str):
                values.add(node.value)
    return values


def _function_def(tree: ast.AST, name: str) -> ast.FunctionDef:
    functions = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == name
    ]
    assert len(functions) == 1
    return functions[0]


def _is_persist_gate_test(test: ast.AST) -> bool:
    if isinstance(test, ast.BoolOp):
        return any(_is_persist_gate_test(value) for value in test.values)
    if isinstance(test, ast.UnaryOp):
        return _is_persist_gate_test(test.operand)
    return (
        isinstance(test, ast.Attribute)
        and test.attr == "persist"
        and isinstance(test.value, ast.Name)
        and test.value.id == "args"
    )


def _persist_refs_outside_cli_gates(nodes: list[ast.stmt]) -> list[ast.AST]:
    violations: list[ast.AST] = []

    def visit(node: ast.AST, *, in_gate_test: bool = False) -> None:
        next_in_gate = in_gate_test
        if isinstance(node, ast.If):
            visit(node.test, in_gate_test=_is_persist_gate_test(node.test))
            for child in node.body + node.orelse:
                visit(child, in_gate_test=False)
            return
        if (
            isinstance(node, ast.Attribute)
            and node.attr == "persist"
            and isinstance(node.value, ast.Name)
            and node.value.id == "args"
            and not next_in_gate
        ):
            violations.append(node)
        for child in ast.iter_child_nodes(node):
            visit(child, in_gate_test=next_in_gate)

    for statement in nodes:
        visit(statement)
    return violations


def test_readiness_digest_parser_surface_includes_limit_and_persist_only() -> None:
    tree = _parse_cli()
    parser_calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "add_parser"
        and any(
            isinstance(arg, ast.Constant) and arg.value == COMMAND
            for arg in node.args
        )
    ]
    assert len(parser_calls) == 1
    allow_abbrev = {
        keyword.arg: keyword.value.value
        for keyword in parser_calls[0].keywords
        if keyword.arg == "allow_abbrev" and isinstance(keyword.value, ast.Constant)
    }
    assert allow_abbrev == {"allow_abbrev": False}

    argument_calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "add_argument"
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "paper_autonomous_readiness_digest"
    ]
    argument_values: set[str] = set()
    for call in argument_calls:
        for arg in call.args:
            if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                argument_values.add(arg.value)
        for keyword in call.keywords:
            if keyword.arg == "dest" and isinstance(keyword.value, ast.Constant):
                argument_values.add(keyword.value.value)

    assert argument_values == {"--limit", "limit", "--persist", "persist"}


def test_readiness_digest_command_branch_is_readback_with_optional_persist_gate() -> None:
    branch = _command_branch(_parse_cli())
    branch_refs = _references(branch)

    assert READINESS_DB_ENV in branch_refs
    assert DIGEST_DB_ENV in branch_refs
    assert AGREEMENT_DB_ENV in branch_refs
    assert HELPER in branch_refs
    assert SUMMARY in branch_refs
    assert "paper_autonomous_readiness_digest_db_sink" in branch_refs
    assert DEFAULT_DIGEST_DB_SINK in branch_refs
    assert "_redacted_paper_readiness_digest_error" in branch_refs
    assert branch_refs & {"digest_dsn", "digest_table_name"}
    assert _persist_refs_outside_cli_gates(branch) == []
    for forbidden in (
        "client_factory",
        "run_market_scan",
        "run_strategy_cycle",
        "run_strategy_loop",
        *FORBIDDEN_MUTATING_OR_PRIVATE_REFS,
    ):
        assert forbidden not in branch_refs


def test_readiness_digest_helper_is_readonly_local_postgres_only() -> None:
    tree = _parse_cli()
    helper = _function_def(tree, HELPER)
    helper_refs = _references(helper.body)

    for expected in (
        "PaperAutonomousReadinessDigestConfig",
        "load_paper_autonomous_readiness_digest_report",
        "load_paper_autonomous_readiness_gate_reports",
        "load_probability_selection_scorer_agreement_reports",
        "ProbabilitySelectionScorerAgreementTrendConfig",
        "build_probability_selection_scorer_agreement_trend_report",
        "ProbabilitySelectionScorerAgreementTrendGateConfig",
        "build_probability_selection_scorer_agreement_trend_gate_report",
        "agreement_trend_gate_loader",
        "agreement_trend_gate_table_name",
        LOCAL_POSTGRES_DSN_VALIDATOR,
        "psycopg",
        "connect",
        "close",
    ):
        assert expected in helper_refs
    helper_arg_names = {
        arg.arg
        for arg in (*helper.args.posonlyargs, *helper.args.args, *helper.args.kwonlyargs)
    }
    for forbidden_arg in (
        "sink",
        "db_sink",
        "digest_sink",
        "digest_dsn",
        "digest_table_name",
        "digest_db_dsn",
        "digest_db_table_name",
    ):
        assert forbidden_arg not in helper_arg_names
    for forbidden in (
        "sink",
        "persist",
        "digest_sink",
        "digest_dsn",
        "digest_table_name",
        "insert_paper_autonomous_readiness_digest_report_with_psycopg",
        *FORBIDDEN_MUTATING_OR_PRIVATE_REFS,
    ):
        assert forbidden not in helper_refs


def test_readiness_digest_summary_is_aggregate_only() -> None:
    summary_refs = _references(_function_body(_parse_cli(), SUMMARY))

    for expected in (
        "digest_status",
        "recommended_next_review_action",
        "evidence",
        "source_name",
        "status",
        "reason_code_counts",
        "_safe_reason_code_for_cli",
    ):
        assert expected in summary_refs
    for forbidden in (
        "config_version",
        "source_config_versions",
        "payload",
        "payload_json",
        "market_slug",
        "question",
        "condition_id",
        "report_sha256",
        "dsn",
        "table",
        "table_name",
        "account",
        *FORBIDDEN_MUTATING_OR_PRIVATE_REFS,
    ):
        assert forbidden not in summary_refs
