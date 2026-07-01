from __future__ import annotations

import ast
from pathlib import Path


MODULE_PATH = Path("src/polymarket_alpha_lab/team_diagnostics_bundle.py")

FORBIDDEN_IMPORT_ROOTS = {
    "argparse",
    "os",
    "pathlib",
    "psycopg",
    "requests",
    "socket",
    "sqlalchemy",
    "sqlite3",
    "subprocess",
    "urllib",
}
FORBIDDEN_CALLS = {
    "connect",
    "getenv",
    "open",
    "read_text",
    "write_text",
}
FORBIDDEN_TEXT = (
    "private_key",
    "wallet",
    "account",
    "order",
    "cancel",
    "replace",
    "sign",
    "exchange_mutation",
    "live_trading",
    "sqlite",
    "redis",
    "mongo",
)


def _source() -> str:
    return MODULE_PATH.read_text(encoding="utf-8")


def test_team_diagnostics_bundle_module_exists_at_expected_scope() -> None:
    assert MODULE_PATH.exists()


def test_team_diagnostics_bundle_has_no_forbidden_imports() -> None:
    tree = ast.parse(_source())
    imported_roots: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imported_roots.add(node.module.split(".", 1)[0])

    assert imported_roots.isdisjoint(FORBIDDEN_IMPORT_ROOTS)


def test_team_diagnostics_bundle_has_no_file_env_network_or_cli_calls() -> None:
    tree = ast.parse(_source())
    called_names: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                called_names.add(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                called_names.add(node.func.attr)

    assert called_names.isdisjoint(FORBIDDEN_CALLS)


def test_team_diagnostics_bundle_source_is_report_only_pure_surface() -> None:
    lower_source = _source().lower()

    for forbidden in FORBIDDEN_TEXT:
        assert forbidden not in lower_source
    assert "paper_only" in lower_source
    assert "report_only" in lower_source
    assert "readonly" in lower_source
