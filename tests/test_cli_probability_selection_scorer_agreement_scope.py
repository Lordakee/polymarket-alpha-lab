from __future__ import annotations

import ast
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CLI_PATH = REPO_ROOT / "src" / "polymarket_alpha_lab" / "cli.py"
COMMAND = "probability-selection-scorer-agreement"
HELPER = "_run_probability_selection_scorer_agreement"
SUMMARY = "_print_probability_selection_scorer_agreement_summary"
AGREEMENT_CONFIG_VERSION = "probability-selection-scorer-agreement-v0"

EXPECTED_PARSER_ARGUMENT_SURFACE = {
    "--limit",
    "limit",
}

FORBIDDEN_PARSER_ARGUMENT_SURFACE = {
    "--persist",
    "persist",
    "--dsn",
    "dsn",
    "--db-dsn",
    "db_dsn",
    "--table",
    "table",
    "--db-table",
    "db_table",
    "--selection-db-dsn",
    "selection_db_dsn",
    "--selection-db-table",
    "selection_db_table",
    "--scorer-db-dsn",
    "scorer_db_dsn",
    "--scorer-db-table",
    "scorer_db_table",
    "--paper-probability-selection-summary-db-dsn",
    "paper_probability_selection_summary_db_dsn",
    "--paper-probability-selection-summary-db-table",
    "paper_probability_selection_summary_db_table",
    "--autonomous-market-scorer-db-dsn",
    "autonomous_market_scorer_db_dsn",
    "--autonomous-market-scorer-db-table",
    "autonomous_market_scorer_db_table",
    "--input",
    "input_path",
    "--output",
    "output_path",
    "--file",
    "file",
    "--sink",
    "sink",
    "--config",
    "config",
    "--config-version",
    "config_version",
    "--live",
    "live",
    "--wallet",
    "wallet",
    "--order",
    "order",
    "--execute",
    "execute",
    "--auth",
    "auth",
    "--private-key",
    "private_key",
    "--account",
    "account",
}

FORBIDDEN_PHASE_ESCAPE_FRAGMENTS = {
    "account",
    "auth",
    "cancel",
    "client",
    "clientfactory",
    "exchange",
    "file",
    "insert",
    "jsonl",
    "live",
    "mongo",
    "mutation",
    "order",
    "persist",
    "privatekey",
    "redis",
    "sign",
    "sink",
    "sqlite",
    "sqlalchemy",
    "submit",
    "wallet",
    "write",
}

EXPECTED_BRANCH_CALLS = {
    "from_autonomous_market_scorer_db_env",
    "from_paper_probability_selection_summary_db_env",
    "_redacted_probability_selection_scorer_agreement_error",
    HELPER,
    SUMMARY,
}

FORBIDDEN_BRANCH_CALLS = {
    "_raise_redacted_db_sink_error",
    "_raise_redacted_multi_db_sink_error",
    "_run_autonomous_market_scorer_history",
    "_run_paper_probability_selection_summary_history",
    "_run_paper_probability_selection_summary_report",
    "_print_autonomous_market_scorer_history_summary",
    "_print_paper_probability_selection_summary_history_summary",
    "insert_autonomous_market_scorer_report",
    "insert_paper_probability_selection_summary_report",
    "PolymarketPublicClient",
    "run_market_scan",
    "run_strategy_cycle",
    "run_strategy_loop",
}

EXPECTED_HELPER_IMPORT_MODULES = {
    "polymarket_alpha_lab.probability_selection_scorer_agreement",
    "polymarket_alpha_lab.probability_selection_scorer_agreement_load",
    "psycopg",
}

EXPECTED_HELPER_CALLS = {
    "ProbabilitySelectionScorerAgreementConfig",
    "load_probability_selection_scorer_agreement_report",
    "connect",
    "close",
}

FORBIDDEN_HELPER_CALLS = {
    "commit",
    "rollback",
    "insert",
    "insert_autonomous_market_scorer_report",
    "insert_autonomous_market_scorer_report_with_psycopg",
    "insert_paper_probability_selection_summary_report",
    "insert_paper_probability_selection_summary_report_with_psycopg",
    "open",
    "write",
    "write_text",
    "write_bytes",
}

FORBIDDEN_HELPER_IMPORT_MODULES = {
    "json",
    "jsonlines",
    "pymongo",
    "redis",
    "sqlalchemy",
    "sqlite3",
}

EXPECTED_SUMMARY_REPORT_FIELDS = {
    "generated_at",
    "config_version",
    "selection_generated_at",
    "scorer_generated_at",
    "selected_count",
    "scorer_candidate_count",
    "selected_market_overlap_count",
    "selected_condition_overlap_count",
    "rejected_but_scored_count",
    "scored_but_unselected_count",
    "scorer_gate_status",
    "agreement_status",
    "recommended_next_step",
    "reason_codes",
    "reason_code_divergence_counts",
    "paper_only",
    "report_only",
    "readonly",
}

FORBIDDEN_SUMMARY_REFERENCES = {
    "rows",
    "score_rows",
    "source_reports",
    "payload",
    "payload_json",
    "report_sha256",
    "question",
    "market_slug",
    "condition_id",
    "dsn",
    "table",
    "table_name",
    "enabled",
    "wallet",
    "order",
    "account",
    "private_key",
}

REDACTION_FORBIDDEN_REFERENCES = {
    "payload",
    "payload_json",
    "report_sha256",
    "question",
    "market_slug",
    "condition_id",
    "wallet",
    "order",
    "account",
    "private_key",
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


def _parser_call(tree: ast.AST, command: str) -> ast.Call:
    parser_variable = _command_parser_variable(tree, command)
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if isinstance(target, ast.Name) and target.id == parser_variable:
            assert isinstance(node.value, ast.Call)
            return node.value
    raise AssertionError(f"missing parser call for {command}")


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


def _attribute_names(nodes: list[ast.stmt]) -> set[str]:
    names: set[str] = set()
    for statement in nodes:
        for node in ast.walk(statement):
            if isinstance(node, ast.Attribute):
                names.add(node.attr)
    return names


def _connect_calls(nodes: list[ast.stmt]) -> list[ast.Call]:
    calls: list[ast.Call] = []
    for statement in nodes:
        for node in ast.walk(statement):
            if isinstance(node, ast.Call) and call_or_attribute_name(node) == "connect":
                calls.append(node)
    return calls


def _assert_connect_calls_are_autocommit(calls: list[ast.Call]) -> None:
    assert calls
    for call in calls:
        autocommit_keywords = [
            keyword
            for keyword in call.keywords
            if keyword.arg == "autocommit"
        ]
        assert len(autocommit_keywords) == 1
        value = autocommit_keywords[0].value
        assert isinstance(value, ast.Constant)
        assert value.value is True


def _has_close_call_in_finally(nodes: list[ast.stmt]) -> bool:
    for statement in nodes:
        for node in ast.walk(statement):
            if not isinstance(node, ast.Try):
                continue
            for final_statement in node.finalbody:
                for final_node in ast.walk(final_statement):
                    if (
                        isinstance(final_node, ast.Call)
                        and call_or_attribute_name(final_node) == "close"
                    ):
                        return True
    return False


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


def _assert_summary_uses_sanitized_reason_formatting(call_names: set[str]) -> None:
    assert "_safe_reason_codes_for_cli" in call_names
    safe_count_formatters = {
        name
        for name in call_names
        if "safe" in normalize_identifier(name)
        and "reasoncode" in normalize_identifier(name)
    }
    assert safe_count_formatters


def test_agreement_parser_surface_is_env_db_only_without_persist_or_writes() -> None:
    tree = parse_cli()
    parser_variable = _command_parser_variable(tree, COMMAND)
    surface = _parser_argument_surface(tree, parser_variable)
    parser_call = _parser_call(tree, COMMAND)
    allow_abbrev = {
        keyword.arg: keyword.value.value
        for keyword in parser_call.keywords
        if isinstance(keyword.value, ast.Constant)
    }

    assert surface == EXPECTED_PARSER_ARGUMENT_SURFACE
    assert allow_abbrev["allow_abbrev"] is False
    assert not (surface & FORBIDDEN_PARSER_ARGUMENT_SURFACE)
    _assert_no_forbidden_fragments(surface, FORBIDDEN_PHASE_ESCAPE_FRAGMENTS)


def test_agreement_branch_uses_env_configs_redacted_error_helper_and_summary() -> None:
    tree = parse_cli()
    branch = _single_command_branch(tree, COMMAND)
    call_names = _node_call_names(branch)
    references = _node_references(branch)

    assert EXPECTED_BRANCH_CALLS <= call_names
    assert not (FORBIDDEN_BRANCH_CALLS & call_names)
    assert "probability_selection_scorer_agreement_runner" in references
    assert "probability_selection_scorer_agreement_db_sink" not in references
    _assert_no_forbidden_fragments(
        references,
        FORBIDDEN_PHASE_ESCAPE_FRAGMENTS - {"file"},
    )


def test_agreement_helper_loads_source_reports_and_builds_report_readonly() -> None:
    tree = parse_cli()
    helper = _function_body(tree, HELPER)
    call_names = _node_call_names(helper)
    import_modules = _node_import_modules(helper)
    references = _node_references(helper)

    assert EXPECTED_HELPER_CALLS <= call_names
    assert EXPECTED_HELPER_IMPORT_MODULES <= import_modules
    assert not (FORBIDDEN_HELPER_CALLS & call_names)
    assert not (FORBIDDEN_HELPER_IMPORT_MODULES & import_modules)
    assert AGREEMENT_CONFIG_VERSION in references
    _assert_connect_calls_are_autocommit(_connect_calls(helper))
    assert _has_close_call_in_finally(helper)
    _assert_no_forbidden_fragments(references, FORBIDDEN_PHASE_ESCAPE_FRAGMENTS)


def test_agreement_failures_are_redacted_without_payload_or_identity_fields() -> None:
    tree = parse_cli()
    redaction_helper = _function_body(
        tree,
        "_redacted_probability_selection_scorer_agreement_error",
    )
    call_names = _node_call_names(redaction_helper)
    references = _node_references(redaction_helper)

    assert "_redact_db_dsn" in call_names
    assert "_redact_db_table_name_and_tail" in call_names
    assert "_redact_paper_research_packet_sensitive_fields" in call_names
    for forbidden in REDACTION_FORBIDDEN_REFERENCES:
        forbidden_key = normalize_identifier(forbidden)
        assert all(
            forbidden_key not in normalize_identifier(reference)
            for reference in references
        )
    _assert_no_forbidden_fragments(
        references,
        FORBIDDEN_PHASE_ESCAPE_FRAGMENTS - {"table"},
    )


def test_agreement_summary_is_aggregate_only_with_safe_reason_formatting() -> None:
    tree = parse_cli()
    summary = _function_body(tree, SUMMARY)
    references = _node_references(summary)
    call_names = _node_call_names(summary)
    report_fields = _report_attribute_names(summary)
    attribute_names = _attribute_names(summary)

    assert EXPECTED_SUMMARY_REPORT_FIELDS <= report_fields
    assert report_fields <= EXPECTED_SUMMARY_REPORT_FIELDS
    _assert_summary_uses_sanitized_reason_formatting(call_names)
    assert "market_slug" not in attribute_names
    assert "condition_id" not in attribute_names
    for forbidden in FORBIDDEN_SUMMARY_REFERENCES:
        forbidden_key = normalize_identifier(forbidden)
        assert all(
            forbidden_key not in normalize_identifier(reference)
            for reference in references
        )
    _assert_no_forbidden_fragments(references, FORBIDDEN_PHASE_ESCAPE_FRAGMENTS)
