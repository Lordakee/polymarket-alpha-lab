from __future__ import annotations

import ast
import importlib
import importlib.util
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_NAME = "polymarket_alpha_lab.paper_probability_selection_summary_history"
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "paper_probability_selection_summary_history.py"
)

EXPECTED_EXPORTS = (
    "PaperProbabilitySelectionSummaryHistoryConfig",
    "PaperProbabilitySelectionSummaryHistoryReport",
    "build_paper_probability_selection_summary_history_report",
)

ALLOWED_IMPORT_ROOTS = {
    "__future__",
    "collections",
    "dataclasses",
    "datetime",
    "decimal",
    "polymarket_alpha_lab",
}

ALLOWED_FIRST_PARTY_IMPORT_MODULES = {
    "polymarket_alpha_lab.paper_probability_selection_summary",
}

FORBIDDEN_IMPORT_FRAGMENTS = {
    "account",
    "aiohttp",
    "api",
    "auth",
    "broker",
    "cancel",
    "client",
    "config",
    "db",
    "eth_account",
    "execute",
    "health",
    "httpx",
    "journal",
    "migration",
    "network",
    "order",
    "paper_execution",
    "positions",
    "private",
    "psycopg",
    "py_clob_client",
    "reconcile",
    "scorer_bridge",
    "socket",
    "sqlalchemy",
    "sqlite3",
    "store",
    "submit",
    "supabase",
    "urllib",
    "wallet",
    "web3",
    "websocket",
    "websockets",
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


def imported_first_party_modules(tree: ast.Module) -> set[str]:
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(
                alias.name
                for alias in node.names
                if alias.name.startswith("polymarket_alpha_lab")
            )
        elif isinstance(node, ast.ImportFrom):
            assert node.level == 0
            module_name = node.module or ""
            if module_name == "polymarket_alpha_lab":
                modules.update(f"{module_name}.{alias.name}" for alias in node.names)
            elif module_name.startswith("polymarket_alpha_lab."):
                modules.add(module_name)
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


def test_selection_summary_history_module_can_be_found_and_imported() -> None:
    spec = importlib.util.find_spec(MODULE_NAME)
    assert spec is not None
    assert spec.origin is not None
    assert Path(spec.origin).resolve() == MODULE_PATH

    module = importlib.import_module(MODULE_NAME)

    assert module.__name__ == MODULE_NAME


def test_selection_summary_history_imports_only_allowed_roots() -> None:
    tree = parse_module()

    for module_name in imported_modules(tree):
        root_name = module_name.split(".", 1)[0]
        assert root_name in ALLOWED_IMPORT_ROOTS, module_name


def test_selection_summary_history_uses_only_allowed_first_party_imports() -> None:
    tree = parse_module()

    assert imported_first_party_modules(tree) <= ALLOWED_FIRST_PARTY_IMPORT_MODULES


def test_selection_summary_history_does_not_import_forbidden_surfaces() -> None:
    tree = parse_module()

    for module_name in imported_modules(tree):
        normalized_module = normalize_identifier(module_name)
        for fragment in FORBIDDEN_IMPORT_FRAGMENTS:
            assert normalize_identifier(fragment) not in normalized_module, (
                module_name,
                fragment,
            )


def test_selection_summary_history_exports_only_report_api() -> None:
    tree = parse_module()

    assert module_exports(tree) == EXPECTED_EXPORTS


def test_selection_summary_history_does_not_perform_io_or_dynamic_execution() -> None:
    tree = parse_module()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in FORBIDDEN_CALL_NAMES, node.func.id
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            assert node.func.attr not in FORBIDDEN_CALL_NAMES, node.func.attr
