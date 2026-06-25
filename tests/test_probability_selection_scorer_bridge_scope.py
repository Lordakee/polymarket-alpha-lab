from __future__ import annotations

import ast
import importlib
import importlib.util
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_NAME = "polymarket_alpha_lab.probability_selection_scorer_bridge"
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "probability_selection_scorer_bridge.py"
)

EXPECTED_EXPORTS = ("paper_probability_selection_summary_report_to_market_data",)

ALLOWED_IMPORT_MODULES = {
    "__future__",
    "dataclasses",
    "decimal",
    "polymarket_alpha_lab.paper_probability_selection_summary",
}

FORBIDDEN_IMPORT_FRAGMENTS = {
    "account",
    "api",
    "auth",
    "client",
    "db",
    "env",
    "http",
    "journal",
    "key",
    "network",
    "order",
    "os",
    "pathlib",
    "position",
    "private",
    "psycopg",
    "request",
    "socket",
    "subprocess",
    "supabase",
    "trade",
    "urllib",
    "wallet",
    "web3",
    "websocket",
}

FORBIDDEN_CALL_NAMES = {
    "__import__",
    "compile",
    "eval",
    "exec",
    "input",
    "open",
    "print",
    "read",
    "write",
}


def normalize_identifier(value: str) -> str:
    return "".join(character for character in value.lower() if character.isalnum())


def parse_module() -> ast.Module:
    return ast.parse(MODULE_PATH.read_text(encoding="utf-8"))


def imported_modules(tree: ast.Module) -> list[str]:
    modules = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            assert node.level == 0
            modules.append(node.module or "")
    return modules


def module_exports(tree: ast.Module) -> tuple[str, ...]:
    assigned_exports = None
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id == "__all__":
                assigned_exports = ast.literal_eval(node.value)
    assert assigned_exports is not None
    return tuple(assigned_exports)


def test_probability_selection_scorer_bridge_module_can_be_found_and_imported() -> None:
    spec = importlib.util.find_spec(MODULE_NAME)
    assert spec is not None
    assert spec.origin is not None
    assert Path(spec.origin).resolve() == MODULE_PATH

    module = importlib.import_module(MODULE_NAME)

    assert module.__name__ == MODULE_NAME


def test_probability_selection_scorer_bridge_imports_only_allowed_dependencies() -> None:
    tree = parse_module()

    assert set(imported_modules(tree)) <= ALLOWED_IMPORT_MODULES


def test_probability_selection_scorer_bridge_does_not_import_forbidden_surfaces() -> None:
    tree = parse_module()

    for module_name in imported_modules(tree):
        normalized_module = normalize_identifier(module_name)
        for fragment in FORBIDDEN_IMPORT_FRAGMENTS:
            assert normalize_identifier(fragment) not in normalized_module, (
                module_name,
                fragment,
            )


def test_probability_selection_scorer_bridge_exports_only_pure_bridge_api() -> None:
    tree = parse_module()

    assert module_exports(tree) == EXPECTED_EXPORTS


def test_probability_selection_scorer_bridge_does_not_perform_io_or_dynamic_execution() -> None:
    tree = parse_module()

    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in FORBIDDEN_CALL_NAMES, node.func.id
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            assert node.func.attr not in FORBIDDEN_CALL_NAMES, node.func.attr
