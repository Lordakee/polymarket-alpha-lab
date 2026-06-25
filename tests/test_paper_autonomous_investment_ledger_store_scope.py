from __future__ import annotations

import ast
from pathlib import Path


ROW_SOURCE = Path(
    "src/polymarket_alpha_lab/paper_autonomous_investment_ledger_db_row.py",
)
STORE_SOURCE = Path(
    "src/polymarket_alpha_lab/paper_autonomous_investment_ledger_store.py",
)

ALLOWED_ROW_IMPORTS = {
    "__future__",
    "dataclasses",
    "datetime",
    "decimal",
    "hashlib",
    "json",
    "polymarket_alpha_lab.json_recovery",
    "polymarket_alpha_lab.paper_autonomous_investment_ledger",
    "re",
    "typing",
}
ALLOWED_STORE_IMPORTS = {
    "__future__",
    "dataclasses",
    "polymarket_alpha_lab.paper_autonomous_investment_ledger_db_row",
    "re",
    "typing",
}
FORBIDDEN_IMPORT_FRAGMENTS = {
    "account",
    "aiohttp",
    "api",
    "auth",
    "cancel",
    "client",
    "eth_account",
    "execute",
    "httpx",
    "order",
    "private",
    "psycopg",
    "py_clob_client",
    "requests",
    "sign",
    "socket",
    "sqlalchemy",
    "sqlite3",
    "submit",
    "supabase",
    "urllib",
    "wallet",
    "web3",
    "websocket",
    "websockets",
}
FORBIDDEN_CALL_NAMES = {
    "__import__",
    "compile",
    "eval",
    "exec",
    "input",
    "open",
    "print",
    "read",
    "write",
}


def normalize_identifier(value: str) -> str:
    return "".join(character for character in value.lower() if character.isalnum())


def parse_module(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"))


def imported_modules(tree: ast.Module) -> list[str]:
    modules = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            assert node.level == 0
            modules.append(node.module or "")
    return modules


def test_ledger_db_row_imports_only_allowed_boundaries() -> None:
    tree = parse_module(ROW_SOURCE)

    assert set(imported_modules(tree)) <= ALLOWED_ROW_IMPORTS


def test_ledger_store_imports_only_generic_dbapi_boundaries() -> None:
    tree = parse_module(STORE_SOURCE)

    assert set(imported_modules(tree)) <= ALLOWED_STORE_IMPORTS


def test_ledger_row_and_store_do_not_import_forbidden_live_surfaces() -> None:
    for path in (ROW_SOURCE, STORE_SOURCE):
        tree = parse_module(path)
        for module_name in imported_modules(tree):
            normalized_module = normalize_identifier(module_name)
            for fragment in FORBIDDEN_IMPORT_FRAGMENTS:
                assert normalize_identifier(fragment) not in normalized_module, (
                    path,
                    module_name,
                    fragment,
                )


def test_ledger_row_and_store_do_not_perform_io_or_dynamic_execution() -> None:
    for path in (ROW_SOURCE, STORE_SOURCE):
        tree = parse_module(path)
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                assert node.func.id not in FORBIDDEN_CALL_NAMES, (path, node.func.id)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                assert node.func.attr not in FORBIDDEN_CALL_NAMES, (path, node.func.attr)


def test_ledger_store_does_not_manage_transactions_or_environment() -> None:
    text = STORE_SOURCE.read_text(encoding="utf-8").lower()

    for forbidden in (
        "commit(",
        "rollback(",
        "os.environ",
        "getenv",
        "psycopg",
        "supabase",
        "private_key",
        "wallet",
        "submit_order",
        "cancel_order",
        "replace_order",
    ):
        assert forbidden not in text
