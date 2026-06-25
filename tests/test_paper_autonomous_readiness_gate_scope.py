from __future__ import annotations

import ast
from importlib import import_module
import inspect
from pathlib import Path


MODULE_PATH = Path("src/polymarket_alpha_lab/paper_autonomous_readiness_gate.py")
ALLOWED_IMPORTS = {
    "__future__",
    "dataclasses",
    "datetime",
    (
        "polymarket_alpha_lab."
        "paper_autonomous_allocation_proposal_db_history_health_trend_gate"
    ),
    (
        "polymarket_alpha_lab."
        "paper_autonomous_investment_ledger_db_history_health_trend_gate"
    ),
    (
        "polymarket_alpha_lab."
        "paper_autonomous_screening_decision_support_gate_db_history_health"
    ),
}


def test_readiness_gate_module_is_pure_phase1_reducer() -> None:
    module = import_module("polymarket_alpha_lab.paper_autonomous_readiness_gate")
    source = inspect.getsource(module).lower()
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
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

    assert imported_modules <= ALLOWED_IMPORTS
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


def test_readiness_gate_readme_documents_phase1_boundary() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")
    section = readme.split("Paper Autonomous Readiness Gate", maxsplit=1)[1].split(
        "## Level 1B Node 1 Status",
        maxsplit=1,
    )[0]

    for required in (
        "pure Python reducer",
        "screening decision-support gate DB-history health",
        "allocation proposal DB-history health trend gate",
        "investment-ledger DB-history health trend gate",
        "paper-only/report-only/readonly",
        "does not connect to Supabase or Postgres",
        "does not read env",
        "does not expose CLI flags",
        "does not persist reports",
        "does not authorize trading",
        "does not alter strategy behavior",
        "trigger allocation",
        "stop execution paths",
        "operator-facing paper review",
        "not order instruction",
        "not execution authorization",
    ):
        assert required in section

    for forbidden in (
        "--dsn",
        "--db-dsn",
        "--table",
        "--db-table",
        "--persist",
        "--live",
    ):
        assert forbidden not in section
