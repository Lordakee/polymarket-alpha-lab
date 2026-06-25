from __future__ import annotations

import ast
from pathlib import Path


SOURCE = Path("src/polymarket_alpha_lab/paper_broker_psycopg.py")


def test_paper_broker_psycopg_stays_paper_only_and_report_boundary() -> None:
    text = SOURCE.read_text(encoding="utf-8").lower()
    tree = ast.parse(text)
    imported_modules: set[str] = set()
    call_names: set[str] = set()
    string_literals: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
        elif isinstance(node, ast.Call):
            function = node.func
            if isinstance(function, ast.Name):
                call_names.add(function.id)
            elif isinstance(function, ast.Attribute):
                call_names.add(function.attr)
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            string_literals.append(node.value.lower())

    forbidden_imports = {
        "polymarket_alpha_lab.cli",
        "polymarket_alpha_lab.runner",
        "polymarket_alpha_lab.paper_execution",
        "requests",
        "httpx",
        "urllib",
        "subprocess",
        "socket",
    }
    forbidden_calls = {
        "submit_order",
        "cancel_order",
        "replace_order",
        "place_order",
        "sign",
        "approve",
    }
    forbidden_literals = (
        "private_key",
        "wallet",
        "auth",
        "live trading",
        "submit_order",
        "cancel_order",
        "replace_order",
        "place_order",
    )

    assert imported_modules.isdisjoint(forbidden_imports)
    assert call_names.isdisjoint(forbidden_calls)
    assert all(
        forbidden not in literal
        for literal in string_literals
        for forbidden in forbidden_literals
    )
