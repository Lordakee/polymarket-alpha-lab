from __future__ import annotations

import ast
import importlib
import inspect


def _read_module() -> object:
    return importlib.import_module(
        "polymarket_alpha_lab.autonomous_market_scorer_load",
    )


def test_autonomous_market_scorer_load_module_stays_env_only_readonly() -> None:
    read_module = _read_module()
    source = inspect.getsource(read_module).lower()

    forbidden_terms = (
        "live",
        "auth",
        "wallet",
        "private_key",
        "private-key",
        "order",
        "signing",
        "exchange",
        "sqlite",
        "jsonl",
        "redis",
        "mongo",
        "sqlalchemy",
        ".open(",
        " open(",
        ".write(",
        " write(",
        ".write_bytes(",
        " write_bytes(",
        ".write_text(",
        " write_text(",
        "insert",
        ".commit(",
        " commit(",
        ".rollback(",
        " rollback(",
    )

    assert all(term not in source for term in forbidden_terms)


def test_autonomous_market_scorer_load_module_only_calls_read_safe_operations() -> None:
    read_module = _read_module()
    tree = ast.parse(inspect.getsource(read_module))
    call_names: set[str] = set()
    imported_names: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            function = node.func
            if isinstance(function, ast.Name):
                call_names.add(function.id)
            elif isinstance(function, ast.Attribute):
                call_names.add(function.attr)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                imported_names.add(alias.name.lower())
        elif isinstance(node, ast.ImportFrom):
            if node.module is not None:
                imported_names.add(node.module.lower())

    forbidden_calls = {
        "commit",
        "rollback",
        "execute",
        "executemany",
        "execute_batch",
        "execute_values",
        "open",
        "write",
        "write_bytes",
        "write_text",
    }
    forbidden_import_fragments = (
        "sqlite",
        "redis",
        "mongo",
        "sqlalchemy",
    )

    assert call_names.isdisjoint(forbidden_calls)
    assert all(
        fragment not in imported_name
        for imported_name in imported_names
        for fragment in forbidden_import_fragments
    )
