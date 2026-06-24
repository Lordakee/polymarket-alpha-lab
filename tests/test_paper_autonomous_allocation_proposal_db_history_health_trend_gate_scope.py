from __future__ import annotations

import ast
from pathlib import Path

MODULE = Path(
    "src/polymarket_alpha_lab/"
    "paper_autonomous_allocation_proposal_db_history_health_trend_gate.py",
)


def test_health_trend_gate_module_has_no_db_env_cli_or_live_trading_surface():
    source = MODULE.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported_modules = []
    call_names = []
    attribute_names = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.append(node.module)
        elif isinstance(node, ast.Call):
            function = node.func
            if isinstance(function, ast.Name):
                call_names.append(function.id)
            elif isinstance(function, ast.Attribute):
                call_names.append(function.attr)
        elif isinstance(node, ast.Attribute):
            attribute_names.append(node.attr)
    assert set(imported_modules) <= {
        "__future__",
        "dataclasses",
        "datetime",
        "decimal",
        "polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_health_trend",
    }
    banned = {
        "psycopg",
        "supabase",
        "environ",
        "requests",
        "httpx",
        "urllib",
        "client",
        "exchange",
        "auth",
        "wallet",
        "account",
        "order",
        "trade",
        "execute",
        "submit",
        "approve",
        "sign",
        "cancel",
        "replace",
        "insert",
        "update",
        "delete",
        "upsert",
        "persist",
        "commit",
        "rollback",
        "cursor",
        "print",
        "open",
    }
    lower_source = source.lower()
    for token in banned:
        assert token not in lower_source
    assert not (banned & set(name.lower() for name in call_names))
    assert not (banned & set(name.lower() for name in attribute_names))
