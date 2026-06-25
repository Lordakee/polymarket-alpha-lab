from __future__ import annotations

import ast
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
HISTORY_MODULE = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "paper_execution_reconciliation_db_history.py"
)
LOAD_MODULE = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "paper_execution_reconciliation_db_history_load.py"
)

ALLOWED_HISTORY_PROJECT_IMPORTS = {
    "polymarket_alpha_lab.paper_execution_reconciliation",
}
ALLOWED_LOAD_PROJECT_IMPORTS = {
    "polymarket_alpha_lab.paper_execution_reconciliation_db_history",
    "polymarket_alpha_lab.paper_execution_reconciliation_store",
}
ALLOWED_STDLIB_IMPORTS = {
    "__future__",
    "collections",
    "dataclasses",
    "datetime",
    "decimal",
    "typing",
}
FORBIDDEN_HISTORY_NAME_FRAGMENTS = {
    "account",
    "auth",
    "client",
    "connection",
    "cursor",
    "env",
    "exchange",
    "http",
    "key",
    "network",
    "order",
    "pathlib",
    "private",
    "psycopg",
    "request",
    "secret",
    "socket",
    "subprocess",
    "supabase",
    "wallet",
}
FORBIDDEN_LOAD_NAME_FRAGMENTS = {
    "account",
    "auth",
    "client",
    "env",
    "exchange",
    "http",
    "key",
    "network",
    "order",
    "pathlib",
    "private",
    "psycopg",
    "request",
    "secret",
    "socket",
    "subprocess",
    "supabase",
    "wallet",
}
FORBIDDEN_CALLS = {
    "__import__",
    "compile",
    "eval",
    "exec",
    "input",
    "open",
    "print",
}
FORBIDDEN_STRING_TOKENS = {
    "account",
    "auth",
    "client",
    "env",
    "exchange",
    "http",
    "key",
    "network",
    "private",
    "psycopg",
    "request",
    "secret",
    "socket",
    "subprocess",
    "supabase",
    "wallet",
}


def _normalize_identifier(value: str) -> str:
    return "".join(character for character in value.lower() if character.isalnum())


def _parse_module(path: Path) -> ast.AST:
    return ast.parse(path.read_text(encoding="utf-8"))


def _imported_modules(tree: ast.AST) -> tuple[str, ...]:
    modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            assert node.level == 0
            modules.append(node.module or "")
    return tuple(modules)


def _assert_import_scope(
    path: Path,
    *,
    allowed_project_imports: set[str],
) -> None:
    tree = _parse_module(path)
    imported_modules = _imported_modules(tree)
    project_imports = {
        module
        for module in imported_modules
        if module.startswith("polymarket_alpha_lab.")
    }

    assert project_imports == allowed_project_imports
    for module in imported_modules:
        if module.startswith("polymarket_alpha_lab."):
            continue
        assert module.split(".", 1)[0] in ALLOWED_STDLIB_IMPORTS, module


def _assert_no_forbidden_operations(
    tree: ast.AST,
    *,
    forbidden_name_fragments: set[str],
) -> None:
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            if isinstance(node.value, float):
                raise AssertionError("float literal is forbidden")
            if isinstance(node.value, str):
                normalized_string = _normalize_identifier(node.value)
                for token in FORBIDDEN_STRING_TOKENS:
                    assert token not in normalized_string, (node.value, token)
        elif isinstance(node, ast.Name):
            normalized_name = _normalize_identifier(node.id)
            for fragment in forbidden_name_fragments:
                assert fragment not in normalized_name, (node.id, fragment)
        elif isinstance(node, ast.Attribute):
            normalized_attribute = _normalize_identifier(node.attr)
            for fragment in forbidden_name_fragments:
                assert fragment not in normalized_attribute, (node.attr, fragment)
        elif isinstance(node, ast.Call):
            callee_name = ""
            if isinstance(node.func, ast.Name):
                callee_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                callee_name = node.func.attr
            assert callee_name not in FORBIDDEN_CALLS, callee_name
            normalized_callee = _normalize_identifier(callee_name)
            for fragment in forbidden_name_fragments:
                assert fragment not in normalized_callee, (callee_name, fragment)


def test_history_module_import_scope_is_pure() -> None:
    _assert_import_scope(
        HISTORY_MODULE,
        allowed_project_imports=ALLOWED_HISTORY_PROJECT_IMPORTS,
    )


def test_history_module_has_no_forbidden_operations() -> None:
    _assert_no_forbidden_operations(
        _parse_module(HISTORY_MODULE),
        forbidden_name_fragments=FORBIDDEN_HISTORY_NAME_FRAGMENTS,
    )


def test_load_module_import_scope_uses_only_report_loader_and_builder() -> None:
    _assert_import_scope(
        LOAD_MODULE,
        allowed_project_imports=ALLOWED_LOAD_PROJECT_IMPORTS,
    )


def test_load_module_does_not_manage_transactions_or_auth() -> None:
    _assert_no_forbidden_operations(
        _parse_module(LOAD_MODULE),
        forbidden_name_fragments=FORBIDDEN_LOAD_NAME_FRAGMENTS,
    )


def test_scope_guard_catches_escape_hatches() -> None:
    tree = ast.parse(
        """
def bad(value):
    print(value)
    open('/tmp/reconciliation-history', 'w')
    __import__('os')
    return 1.25
""",
    )

    with pytest.raises(AssertionError):
        _assert_no_forbidden_operations(
            tree,
            forbidden_name_fragments=FORBIDDEN_HISTORY_NAME_FRAGMENTS,
        )
