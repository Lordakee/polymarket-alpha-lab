from __future__ import annotations

import ast
from pathlib import Path


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "probability_selection_scorer_agreement.py"
)

FORBIDDEN_TERMS = (
    "allocate",
    "allocation",
    "approve",
    "auth",
    "cancel",
    "execute",
    "exchange",
    "live",
    "mutation",
    "order",
    "private-key",
    "private_key",
    "replace",
    "rank",
    "ranking",
    "signing",
    "size",
    "sizing",
    "trade",
    "wallet",
    "jsonl",
    "mongo",
    "redis",
    "sqlalchemy",
    "sqlite",
    "supabase",
)

FORBIDDEN_IMPORT_ROOTS = (
    "httpx",
    "jsonlines",
    "mongo",
    "pymongo",
    "redis",
    "requests",
    "sqlalchemy",
    "sqlite3",
    "socket",
    "subprocess",
    "urllib",
)

FORBIDDEN_CALL_NAMES = (
    "cancel_order",
    "execute_order",
    "open",
    "replace_order",
    "submit_order",
    "write",
    "write_text",
    "write_bytes",
)


def _source() -> str:
    return MODULE_PATH.read_text(encoding="utf-8")


def _referenced_names(source: str) -> set[str]:
    tree = ast.parse(source)
    references: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            references.add(node.id.lower())
        elif isinstance(node, ast.Attribute):
            references.add(node.attr.lower())
        elif isinstance(node, ast.arg):
            references.add(node.arg.lower())
        elif isinstance(node, (ast.AsyncFunctionDef, ast.FunctionDef)):
            references.add(node.name.lower())
        elif isinstance(node, ast.alias):
            references.add(node.name.lower())
            if node.asname is not None:
                references.add(node.asname.lower())

    return references


def _import_roots_and_call_names(source: str) -> tuple[set[str], set[str]]:
    tree = ast.parse(source)
    import_roots: set[str] = set()
    call_names: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                import_roots.add(alias.name.split(".", 1)[0])
        elif isinstance(node, ast.ImportFrom):
            module_name = node.module or ""
            import_roots.add(module_name.split(".", 1)[0])
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                call_names.add(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                call_names.add(node.func.attr)

    return import_roots, call_names


def test_agreement_audit_module_bans_live_trading_and_durable_persistence_terms() -> None:
    references = _referenced_names(_source())

    for term in FORBIDDEN_TERMS:
        assert term not in references


def test_agreement_audit_scope_policy_catches_order_style_attributes() -> None:
    references = _referenced_names(
        """
class Client:
    def submit_order(self):
        pass
""",
    )

    assert "submit_order" in references
    assert "submit_order" in FORBIDDEN_CALL_NAMES


def test_agreement_audit_module_bans_durable_persistence_imports_and_file_writes() -> None:
    import_roots, call_names = _import_roots_and_call_names(_source())

    for root_name in import_roots:
        assert root_name not in FORBIDDEN_IMPORT_ROOTS
    for call_name in call_names:
        assert call_name not in FORBIDDEN_CALL_NAMES


def test_agreement_audit_scope_policy_catches_file_write_calls() -> None:
    _, call_names = _import_roots_and_call_names(
        """
from pathlib import Path

Path("x").write_text("x")
Path("x").write_bytes(b"x")
""",
    )

    assert "write_text" in call_names
    assert "write_bytes" in call_names
    assert "write_text" in FORBIDDEN_CALL_NAMES
    assert "write_bytes" in FORBIDDEN_CALL_NAMES


def test_agreement_audit_scope_policy_catches_network_and_process_imports() -> None:
    import_roots, _ = _import_roots_and_call_names(
        """
import requests
import httpx
import urllib.request
import socket
import subprocess
""",
    )

    assert {"requests", "httpx", "urllib", "socket", "subprocess"} <= import_roots
    assert {"requests", "httpx", "urllib", "socket", "subprocess"} <= set(
        FORBIDDEN_IMPORT_ROOTS,
    )
