from __future__ import annotations

import ast
from pathlib import Path

import polymarket_alpha_lab


MODULE_PATH = Path("src/polymarket_alpha_lab/team_event_template_performance.py")
PACKAGE_ROOT_PATH = Path("src/polymarket_alpha_lab/__init__.py")

EXPECTED_EXPORTS = {
    "TeamEventTemplatePerformanceConfig",
    "TeamEventTemplatePerformanceReport",
    "TeamEventTemplatePerformanceRow",
    "build_team_event_template_performance_report",
}
FORBIDDEN_IMPORT_ROOTS = {
    "asyncio",
    "httpx",
    "os",
    "psycopg",
    "requests",
    "socket",
    "subprocess",
    "supabase",
    "urllib",
}
FORBIDDEN_CALL_NAMES = {
    "__import__",
    "eval",
    "exec",
    "open",
    "print",
}
FORBIDDEN_SOURCE_FRAGMENTS = (
    "api_key",
    "auth",
    "cancel",
    "cli",
    "credential",
    "dotenv",
    "environ",
    "execute",
    "http",
    "live",
    "network",
    "open(",
    "order",
    "private_key",
    "psycopg",
    "read_text",
    "replace",
    "request",
    "socket",
    "submit",
    "supabase",
    "trade",
    "urllib",
    "wallet",
    "write_text",
)


def _source() -> str:
    return MODULE_PATH.read_text(encoding="utf-8")


def _call_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return None


def _violations(source: str) -> tuple[str, ...]:
    tree = ast.parse(source)
    violations: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            names = [node.module] if node.module is not None else []
        else:
            names = []
        for name in names:
            root = name.split(".", maxsplit=1)[0]
            if root in FORBIDDEN_IMPORT_ROOTS:
                violations.append(f"forbidden import {name}")

        if isinstance(node, ast.Call):
            call_name = _call_name(node.func)
            if call_name in FORBIDDEN_CALL_NAMES:
                violations.append(f"forbidden call {call_name}")

    lowered_source = source.lower()
    for fragment in FORBIDDEN_SOURCE_FRAGMENTS:
        if fragment in lowered_source:
            violations.append(f"forbidden source fragment {fragment}")

    return tuple(sorted(set(violations)))


def test_team_event_template_performance_module_stays_pure_report_only_scope() -> None:
    assert _violations(_source()) == ()


def test_scope_guard_catches_persistence_network_live_auth_order_surfaces() -> None:
    bad_source = """
import os
import psycopg
from supabase import create_client

def leak():
    print(os.environ)
    open("x")
    submit_order()
    live_network_auth = "bad"
    return create_client
"""

    violations = _violations(bad_source)

    assert violations
    assert any("forbidden import psycopg" in violation for violation in violations)
    assert any("forbidden import supabase" in violation for violation in violations)
    assert any("forbidden call open" in violation for violation in violations)
    assert any("forbidden source fragment auth" in violation for violation in violations)
    assert any("forbidden source fragment order" in violation for violation in violations)


def test_team_event_template_performance_exports_are_module_local_only() -> None:
    package_source = PACKAGE_ROOT_PATH.read_text(encoding="utf-8")

    assert "team_event_template_performance" not in package_source
    assert "team_event_template_performance" not in polymarket_alpha_lab.__all__

    for name in EXPECTED_EXPORTS:
        assert name not in package_source
        assert name not in polymarket_alpha_lab.__all__
        assert not hasattr(polymarket_alpha_lab, name)
