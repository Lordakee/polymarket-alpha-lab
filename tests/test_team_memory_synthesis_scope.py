from __future__ import annotations

import ast
from pathlib import Path

import polymarket_alpha_lab


MODULE_PATH = Path("src/polymarket_alpha_lab/team_memory_synthesis.py")
PACKAGE_ROOT_PATH = Path("src/polymarket_alpha_lab/__init__.py")


def _source() -> str:
    return MODULE_PATH.read_text(encoding="utf-8")


def test_team_memory_synthesis_module_stays_pure_and_paper_only() -> None:
    source = _source()
    lowered = source.lower()

    banned_terms = (
        "psycopg",
        "supabase",
        "os.environ",
        "dotenv",
        "requests",
        "urllib",
        "httpx",
        "aiohttp",
        "socket",
        "subprocess",
        "click",
        "argparse",
        "typer",
        "wallet",
        "private_key",
        "api_key",
        "auth",
        "credential",
        "order",
        "execution",
        "submit",
        "cancel",
        "replace_order",
        "open(",
        ".read_text(",
        ".write_text(",
        "path(",
        "importlib",
        "__import__",
        "eval(",
        "exec(",
    )

    for term in banned_terms:
        assert term not in lowered


def test_team_memory_synthesis_uses_only_allowed_import_surfaces() -> None:
    tree = ast.parse(_source())
    imports: list[str] = []
    dynamic_calls: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.append(node.module or "")
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id in {"eval", "exec", "__import__", "open"}:
                dynamic_calls.append(node.func.id)

    assert dynamic_calls == []
    assert set(imports) <= {
        "__future__",
        "collections",
        "dataclasses",
        "datetime",
        "decimal",
        "typing",
        "polymarket_alpha_lab.team_forecast_db_row",
        "polymarket_alpha_lab.team_paper_guard",
    }


def test_team_memory_synthesis_exports_are_module_local_only() -> None:
    package_source = PACKAGE_ROOT_PATH.read_text(encoding="utf-8")
    forbidden_exports = (
        "TeamMemorySynthesisConfig",
        "TeamMemoryReferenceRow",
        "TeamMemorySynthesisReport",
        "build_team_memory_synthesis_report",
        "team_memory_synthesis",
    )

    for name in forbidden_exports:
        assert name not in package_source
        assert name not in polymarket_alpha_lab.__all__

    for name in forbidden_exports[:-1]:
        assert not hasattr(polymarket_alpha_lab, name)
