"""Scope tests for paper_broker_store module."""

from __future__ import annotations

import ast
from pathlib import Path


SOURCE = Path("src/polymarket_alpha_lab/paper_broker_store.py")


def _source_text() -> str:
    assert SOURCE.exists(), "paper broker store module must exist"
    return SOURCE.read_text()


def test_store_module_has_no_forbidden_surfaces() -> None:
    text = _source_text()
    forbidden = [
        "psycopg",
        "supabase",
        "os.environ",
        "requests",
        "httpx",
        "urllib",
        "subprocess",
        "socket",
        "asyncio",
        "private_key",
        "wallet",
        "account",
        "auth",
        "live_trading",
        "live trading",
        "submit_order",
        "place_order",
        "cancel_order",
        "replace_order",
        "approve",
        "open(",
        "print(",
    ]
    for token in forbidden:
        assert token not in text, f"forbidden token found: {token}"


def test_store_imports_are_generic_db_api_only() -> None:
    tree = ast.parse(_source_text())
    forbidden_modules = {
        "asyncio",
        "httpx",
        "os",
        "polymarket",
        "psycopg",
        "requests",
        "socket",
        "subprocess",
        "supabase",
        "urllib",
    }

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_names = {alias.name.split(".", maxsplit=1)[0] for alias in node.names}
            assert imported_names.isdisjoint(forbidden_modules)
        elif isinstance(node, ast.ImportFrom):
            module = "" if node.module is None else node.module
            root = module.split(".", maxsplit=1)[0]
            assert root not in forbidden_modules


def test_store_does_not_read_environment_or_construct_live_order_clients() -> None:
    tree = ast.parse(_source_text())
    forbidden_names = {
        "account",
        "auth",
        "cancel_order",
        "client",
        "environ",
        "getenv",
        "place_order",
        "private_key",
        "replace_order",
        "submit_order",
        "wallet",
    }

    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            assert node.id not in forbidden_names
        elif isinstance(node, ast.Attribute):
            assert node.attr not in forbidden_names
