"""Scope tests for paper order lifecycle DB history modules."""

from __future__ import annotations

import ast
from pathlib import Path


MODULE_PATHS = (
    Path("src/polymarket_alpha_lab/paper_order_lifecycle_db_history.py"),
    Path("src/polymarket_alpha_lab/paper_order_lifecycle_db_history_load.py"),
)

FORBIDDEN_IMPORTS = {
    "polymarket_alpha_lab.auth",
    "polymarket_alpha_lab.live_broker",
    "polymarket_alpha_lab.paper_order_lifecycle_psycopg",
    "polymarket_alpha_lab.reconciliation",
    "polymarket_alpha_lab.wallet",
    "psycopg",
    "py_clob_client",
    "requests",
}

FORBIDDEN_CALL_NAMES = {
    "authenticate",
    "cancel_order",
    "commit",
    "create_order",
    "place_order",
    "replace_order",
    "rollback",
    "submit_order",
}

FORBIDDEN_SQL_VERBS = ("INSERT", "UPDATE", "DELETE", "UPSERT", "MERGE")


def _tree(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def _imported_names(tree: ast.Module) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            names.add(node.module)
    return names


def _called_names(tree: ast.Module) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                names.add(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                names.add(node.func.attr)
    return names


def test_history_modules_stay_report_only_and_avoid_live_imports_or_connection_ownership() -> None:
    for path in MODULE_PATHS:
        source = path.read_text(encoding="utf-8")
        tree = _tree(path)

        imported_names = _imported_names(tree)
        assert imported_names.isdisjoint(FORBIDDEN_IMPORTS)
        assert _called_names(tree).isdisjoint(FORBIDDEN_CALL_NAMES)
        assert all(verb not in source.upper() for verb in FORBIDDEN_SQL_VERBS)
        assert "float(" not in source
