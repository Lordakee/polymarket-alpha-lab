from __future__ import annotations

import ast
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "probability_selection_scorer_agreement_trend_gate.py"
)

EXPECTED_PUBLIC_SURFACE = {
    "DEFAULT_PROBABILITY_SELECTION_SCORER_AGREEMENT_TREND_GATE_CONFIG_VERSION",
    "ProbabilitySelectionScorerAgreementTrendGateConfig",
    "ProbabilitySelectionScorerAgreementTrendGateReasonCodeCount",
    "ProbabilitySelectionScorerAgreementTrendGateReport",
    "build_probability_selection_scorer_agreement_trend_gate_report",
}

EXPECTED_IMPORT_MODULES = {
    "__future__",
    "dataclasses",
    "datetime",
    "decimal",
    "polymarket_alpha_lab.probability_selection_scorer_agreement_trend",
}

FORBIDDEN_IMPORT_MODULES = {
    "argparse",
    "json",
    "jsonlines",
    "os",
    "pathlib",
    "psycopg",
    "pymongo",
    "redis",
    "requests",
    "sqlalchemy",
    "sqlite3",
    "urllib",
}

FORBIDDEN_CALLS = {
    "connect",
    "commit",
    "rollback",
    "cursor",
    "execute",
    "fetchall",
    "insert",
    "open",
    "read_text",
    "write",
    "write_text",
    "write_bytes",
}

FORBIDDEN_FRAGMENTS = {
    "account",
    "auth",
    "cancel",
    "client",
    "clientfactory",
    "clob",
    "database",
    "dsn",
    "env",
    "exchange",
    "file",
    "http",
    "jsonl",
    "live",
    "mongo",
    "mutation",
    "order",
    "persist",
    "privatekey",
    "psycopg",
    "redis",
    "sign",
    "sink",
    "sqlite",
    "sqlalchemy",
    "submit",
    "table",
    "wallet",
    "write",
}


def normalize_identifier(value: str) -> str:
    return "".join(character for character in value.lower() if character.isalnum())


def parse_module() -> ast.Module:
    return ast.parse(MODULE_PATH.read_text(encoding="utf-8"), filename=str(MODULE_PATH))


def call_or_attribute_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Call):
        return call_or_attribute_name(node.func)
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return None


def _import_modules(tree: ast.AST) -> set[str]:
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            modules.add(node.module or "")
    return modules


def _call_names(tree: ast.AST) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            name = call_or_attribute_name(node)
            if name is not None:
                names.add(name)
    return names


def _references(tree: ast.AST) -> set[str]:
    refs: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            refs.add(node.name)
        elif isinstance(node, ast.Name):
            refs.add(node.id)
        elif isinstance(node, ast.Attribute):
            refs.add(node.attr)
        elif isinstance(node, ast.arg):
            refs.add(node.arg)
        elif isinstance(node, ast.keyword) and node.arg is not None:
            refs.add(node.arg)
        elif isinstance(node, ast.alias):
            refs.add(node.name)
            if node.asname is not None:
                refs.add(node.asname)
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            refs.add(node.value)
    return refs


def _class_names(tree: ast.AST) -> set[str]:
    return {node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)}


def _function_names(tree: ast.AST) -> set[str]:
    return {node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)}


def _exported_names(tree: ast.AST) -> set[str]:
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        if not any(isinstance(target, ast.Name) and target.id == "__all__" for target in node.targets):
            continue
        assert isinstance(node.value, (ast.Tuple, ast.List))
        return {
            element.value
            for element in node.value.elts
            if isinstance(element, ast.Constant) and isinstance(element.value, str)
        }
    raise AssertionError("missing __all__")


def _dataclass_frozen_classes(tree: ast.AST) -> set[str]:
    frozen: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        for decorator in node.decorator_list:
            if not isinstance(decorator, ast.Call):
                continue
            if call_or_attribute_name(decorator) != "dataclass":
                continue
            for keyword in decorator.keywords:
                if (
                    keyword.arg == "frozen"
                    and isinstance(keyword.value, ast.Constant)
                    and keyword.value.value is True
                ):
                    frozen.add(node.name)
    return frozen


def _assert_no_forbidden_fragments(references: set[str]) -> None:
    for fragment in FORBIDDEN_FRAGMENTS:
        normalized_fragment = normalize_identifier(fragment)
        matches = tuple(
            sorted(
                reference
                for reference in references
                if normalized_fragment in normalize_identifier(reference)
            ),
        )
        assert not matches, (fragment, matches)


def test_agreement_trend_gate_module_has_expected_public_surface() -> None:
    tree = parse_module()

    assert _exported_names(tree) == EXPECTED_PUBLIC_SURFACE
    assert EXPECTED_PUBLIC_SURFACE - {
        "DEFAULT_PROBABILITY_SELECTION_SCORER_AGREEMENT_TREND_GATE_CONFIG_VERSION",
    } <= (_class_names(tree) | _function_names(tree))


def test_agreement_trend_gate_module_is_pure_and_readonly() -> None:
    tree = parse_module()
    imports = _import_modules(tree)
    call_names = _call_names(tree)
    references = _references(tree)

    assert imports == EXPECTED_IMPORT_MODULES
    assert not (imports & FORBIDDEN_IMPORT_MODULES)
    assert not (call_names & FORBIDDEN_CALLS)
    _assert_no_forbidden_fragments(references)


def test_agreement_trend_gate_dataclasses_are_frozen_and_hard_flagged() -> None:
    tree = parse_module()
    references = _references(tree)
    frozen_classes = _dataclass_frozen_classes(tree)

    assert {
        "ProbabilitySelectionScorerAgreementTrendGateConfig",
        "ProbabilitySelectionScorerAgreementTrendGateReasonCodeCount",
        "ProbabilitySelectionScorerAgreementTrendGateReport",
    } <= frozen_classes
    for hard_flag in ("paper_only", "report_only", "readonly"):
        assert hard_flag in references
    assert "_validate_hard_flags" in references


def test_agreement_trend_gate_uses_exact_source_report_type() -> None:
    tree = parse_module()
    references = _references(tree)

    assert "ProbabilitySelectionScorerAgreementTrendReport" in references
    assert "type" in references
    assert "source_report must be exactly ProbabilitySelectionScorerAgreementTrendReport" in references
