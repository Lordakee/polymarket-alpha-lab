from __future__ import annotations

import ast
from pathlib import Path


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "paper_autonomous_investment_ledger_psycopg.py"
)


FORBIDDEN_IMPORT_FRAGMENTS = (
    "auth",
    "wallet",
    "private_key",
    "sign",
    "order_builder",
    "exchange",
    "py_clob_client",
)

FORBIDDEN_CALL_NAMES = (
    "cancel",
    "cancel_order",
    "create_order",
    "derive_api_key",
    "get_balance",
    "get_positions",
    "place_order",
    "post_order",
    "sign",
    "submit_order",
)


def test_paper_autonomous_investment_ledger_psycopg_stays_report_boundary() -> None:
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_names = tuple(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported_names = (node.module or "", *(alias.name for alias in node.names))
        else:
            imported_names = ()
        for imported_name in imported_names:
            normalized = imported_name.replace("_", "").lower()
            assert not any(
                fragment.replace("_", "") in normalized
                for fragment in FORBIDDEN_IMPORT_FRAGMENTS
            ), imported_name

        if isinstance(node, ast.Call):
            function = node.func
            if isinstance(function, ast.Name):
                call_name = function.id
            elif isinstance(function, ast.Attribute):
                call_name = function.attr
            else:
                call_name = ""
            normalized = call_name.replace("_", "").lower()
            assert not any(
                forbidden.replace("_", "") == normalized
                for forbidden in FORBIDDEN_CALL_NAMES
            ), call_name
