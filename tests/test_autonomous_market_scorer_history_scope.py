"""Scope tests for the autonomous market scorer history reducer."""

from __future__ import annotations

import ast
from pathlib import Path


SOURCE = Path("src/polymarket_alpha_lab/autonomous_market_scorer_history.py")


def test_history_module_has_no_forbidden_surfaces() -> None:
    text = SOURCE.read_text()
    lowered = text.lower()
    forbidden = [
        "psycopg",
        "requests",
        "httpx",
        "urllib",
        "subprocess",
        "socket",
        "asyncio",
        "live",
        "auth",
        "wallet",
        "private_key",
        "private-key",
        "order",
        "signing",
        "exchange",
        "mutation",
        "submit_order",
        "cancel_order",
        "replace_order",
        "execute",
        "approve",
        "trade",
        "sqlite",
        "jsonl",
        "redis",
        "mongo",
        "sqlalchemy",
        "open",
        "write",
        "print(",
    ]
    for token in forbidden:
        assert token not in lowered, f"forbidden token found: {token}"


def test_history_module_imports_only_pure_stdlib_helpers() -> None:
    tree = ast.parse(SOURCE.read_text())
    forbidden_roots = {
        "asyncio",
        "httpx",
        "psycopg",
        "pymongo",
        "redis",
        "requests",
        "socket",
        "sqlalchemy",
        "sqlite3",
        "subprocess",
        "urllib",
    }

    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name.split(".", maxsplit=1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imports.add(node.module.split(".", maxsplit=1)[0])

    assert not imports.intersection(forbidden_roots)


def test_history_module_does_not_call_file_network_or_process_surfaces() -> None:
    tree = ast.parse(SOURCE.read_text())
    forbidden_call_names = {
        "connect",
        "delete",
        "execute",
        "open",
        "patch",
        "post",
        "put",
        "remove",
        "replace",
        "request",
        "run",
        "send",
        "submit",
        "unlink",
        "write",
        "write_bytes",
        "write_text",
    }

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        function = node.func
        if isinstance(function, ast.Name):
            call_name = function.id
        elif isinstance(function, ast.Attribute):
            call_name = function.attr
        else:
            continue

        assert call_name not in forbidden_call_names, (
            f"forbidden call surface found: {call_name}"
        )
