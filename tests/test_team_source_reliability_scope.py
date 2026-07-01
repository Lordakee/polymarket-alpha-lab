from __future__ import annotations

import ast
from pathlib import Path

import polymarket_alpha_lab


MODULE_PATH = Path("src/polymarket_alpha_lab/team_source_reliability.py")
PACKAGE_ROOT_PATH = Path("src/polymarket_alpha_lab/__init__.py")


EXPECTED_EXPORTS = {
    "TeamSourceReliabilityConfig",
    "TeamSourceReliabilityReport",
    "TeamSourceReliabilityRow",
    "build_team_source_reliability_report",
}


def _source() -> str:
    return MODULE_PATH.read_text(encoding="utf-8")


def _called_name(node: ast.Call) -> str:
    parts: list[str] = []
    value: ast.AST | None = node.func
    while isinstance(value, ast.Attribute):
        parts.append(value.attr)
        value = value.value
    if isinstance(value, ast.Name):
        parts.append(value.id)
    return ".".join(reversed(parts))


def test_team_source_reliability_module_stays_pure_report_only() -> None:
    lowered = _source().lower()

    for banned in (
        "psycopg",
        "supabase",
        "os.environ",
        "dotenv",
        "requests",
        "urllib",
        "httpx",
        "aiohttp",
        "socket",
        "network",
        "subprocess",
        "cli",
        "wallet",
        "account",
        "order",
        "trade",
        "execute",
        "submit",
        "cancel",
        "replace",
        "auth",
        "private_key",
        "api_key",
        "credential",
        "open(",
        ".read_text(",
        ".write_text(",
        "path(",
        "importlib",
        "__import__",
        "eval(",
        "exec(",
        "print(",
    ):
        assert banned not in lowered


def test_team_source_reliability_uses_only_allowed_imports_and_calls() -> None:
    tree = ast.parse(_source())
    imports: list[str] = []
    forbidden_calls: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.append(node.module or "")
        elif isinstance(node, ast.Call):
            called_name = _called_name(node)
            if called_name in {
                "open",
                "print",
                "eval",
                "exec",
                "__import__",
            }:
                forbidden_calls.append(called_name)

    assert forbidden_calls == []
    assert set(imports) <= {
        "__future__",
        "dataclasses",
        "datetime",
        "decimal",
        "typing",
        "polymarket_alpha_lab.team_forecast_db_row",
        "polymarket_alpha_lab.team_taxonomy",
    }


def test_team_source_reliability_exports_are_module_local_only() -> None:
    package_source = PACKAGE_ROOT_PATH.read_text(encoding="utf-8")

    for name in EXPECTED_EXPORTS:
        assert name not in package_source
        assert name not in polymarket_alpha_lab.__all__
        assert not hasattr(polymarket_alpha_lab, name)
    assert "team_source_reliability" not in package_source
    assert "team_source_reliability" not in polymarket_alpha_lab.__all__
