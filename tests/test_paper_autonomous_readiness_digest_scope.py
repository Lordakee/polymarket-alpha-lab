from __future__ import annotations

import ast
from importlib import import_module
import inspect
from pathlib import Path


REDUCER_PATH = Path("src/polymarket_alpha_lab/paper_autonomous_readiness_digest.py")
LOADER_PATH = Path("src/polymarket_alpha_lab/paper_autonomous_readiness_digest_load.py")


def test_readiness_digest_reducer_is_pure_phase_boundary_node() -> None:
    module = import_module("polymarket_alpha_lab.paper_autonomous_readiness_digest")
    source = inspect.getsource(module).lower()
    tree = ast.parse(REDUCER_PATH.read_text(encoding="utf-8"))
    imported_modules: set[str] = set()
    call_names: set[str] = set()
    attribute_names: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported_modules.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module is not None:
                imported_modules.add(node.module)
        elif isinstance(node, ast.Call):
            function = node.func
            if isinstance(function, ast.Name):
                call_names.add(function.id.lower())
            elif isinstance(function, ast.Attribute):
                call_names.add(function.attr.lower())
        elif isinstance(node, ast.Attribute):
            attribute_names.add(node.attr.lower())

    assert imported_modules <= {
        "__future__",
        "dataclasses",
        "datetime",
    }
    for banned in (
        "psycopg",
        "supabase",
        "os.environ",
        "requests",
        "httpx",
        "urllib",
        "private_key",
        "wallet",
        "account",
        "submit_order",
        "cancel_order",
        "replace_order",
        "execute",
        "approve",
        "trade",
        "open(",
        "print(",
    ):
        assert banned not in source
    forbidden_calls = {
        "__import__",
        "compile",
        "connect",
        "cursor",
        "delete",
        "eval",
        "exec",
        "execute",
        "get",
        "globals",
        "hasattr",
        "input",
        "insert",
        "locals",
        "open",
        "post",
        "print",
        "read",
        "request",
        "rollback",
        "send",
        "sign",
        "submit",
        "update",
        "upsert",
        "write",
    }
    forbidden_attributes = {
        "account",
        "api_key",
        "auth",
        "broker",
        "cancel",
        "client",
        "credential",
        "dsn",
        "environ",
        "exchange",
        "live",
        "order",
        "persist",
        "private_key",
        "submit",
        "supabase",
        "trade",
        "wallet",
    }
    assert not (forbidden_calls & call_names)
    assert not (forbidden_attributes & attribute_names)


def test_readiness_digest_loader_is_dependency_injected_without_static_upstream_imports() -> None:
    tree = ast.parse(LOADER_PATH.read_text(encoding="utf-8"))
    imported_modules: set[str] = set()
    call_names: set[str] = set()
    attribute_names: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported_modules.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module is not None:
                imported_modules.add(node.module)
        elif isinstance(node, ast.Call):
            function = node.func
            if isinstance(function, ast.Name):
                call_names.add(function.id.lower())
            elif isinstance(function, ast.Attribute):
                call_names.add(function.attr.lower())
        elif isinstance(node, ast.Attribute):
            attribute_names.add(node.attr.lower())

    assert imported_modules <= {
        "__future__",
        "collections.abc",
        "datetime",
        "polymarket_alpha_lab.paper_autonomous_readiness_digest",
    }
    assert "load_paper_autonomous_readiness_gate_report" not in LOADER_PATH.read_text(
        encoding="utf-8",
    )
    forbidden_calls = {
        "commit",
        "connect",
        "cursor",
        "delete",
        "execute",
        "executemany",
        "insert",
        "open",
        "rollback",
        "update",
        "upsert",
    }
    forbidden_attributes = {
        "account",
        "auth",
        "cancel",
        "client",
        "exchange",
        "order",
        "private_key",
        "sign",
        "submit",
        "trade",
        "wallet",
    }
    assert not (forbidden_calls & call_names)
    assert not (forbidden_attributes & attribute_names)
