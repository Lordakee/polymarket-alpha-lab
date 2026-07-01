from __future__ import annotations

import ast
from pathlib import Path


MODULE_PATH = Path("src/polymarket_alpha_lab/team_forecast_calibration.py")
PACKAGE_INIT_PATH = Path("src/polymarket_alpha_lab/__init__.py")

FORBIDDEN_IMPORT_ROOTS = {
    "os",
    "psycopg",
    "requests",
    "socket",
    "subprocess",
    "supabase",
    "urllib",
}
FORBIDDEN_CALL_NAMES = {
    "auth",
    "cancel",
    "execute",
    "open",
    "order",
    "print",
    "replace",
    "submit",
    "trade",
}
FORBIDDEN_NAME_FRAGMENTS = (
    "account",
    "auth",
    "cancel",
    "cli",
    "environ",
    "execute",
    "network",
    "order",
    "psycopg",
    "submit",
    "supabase",
    "trade",
    "wallet",
)


def _module_source() -> str:
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
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            names = []
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif node.module is not None:
                names = [node.module]
            for name in names:
                root = name.split(".", maxsplit=1)[0]
                if root in FORBIDDEN_IMPORT_ROOTS:
                    violations.append(f"forbidden import {name}")

        if isinstance(node, ast.Call):
            call_name = _call_name(node.func)
            if call_name in FORBIDDEN_CALL_NAMES:
                violations.append(f"forbidden call {call_name}")

        if isinstance(node, ast.Attribute):
            lowered = node.attr.lower()
            for fragment in FORBIDDEN_NAME_FRAGMENTS:
                if fragment in lowered:
                    violations.append(f"forbidden attribute {node.attr}")

        if isinstance(node, ast.Name):
            lowered = node.id.lower()
            for fragment in FORBIDDEN_NAME_FRAGMENTS:
                if fragment in lowered:
                    violations.append(f"forbidden name {node.id}")

    lowered_source = source.lower()
    for fragment in FORBIDDEN_NAME_FRAGMENTS:
        if fragment in lowered_source:
            violations.append(f"forbidden source fragment {fragment}")

    return tuple(sorted(set(violations)))


def test_team_forecast_calibration_module_stays_pure_report_scope() -> None:
    source = _module_source()

    assert _violations(source) == ()


def test_scope_guard_catches_persistence_network_cli_and_trading_terms() -> None:
    bad_source = """
import os
import psycopg
from supabase import create_client

def leak():
    print(os.environ)
    open("x")
    submit_order()
    cancel_trade()
    wallet_account = "bad"
    return create_client
"""

    violations = _violations(bad_source)

    assert violations
    assert any("forbidden import psycopg" in violation for violation in violations)
    assert any("forbidden import supabase" in violation for violation in violations)
    assert any("forbidden call print" in violation for violation in violations)
    assert any("forbidden call open" in violation for violation in violations)
    assert any("forbidden source fragment wallet" in violation for violation in violations)


def test_team_forecast_calibration_is_not_package_root_exported() -> None:
    source = PACKAGE_INIT_PATH.read_text(encoding="utf-8")

    assert "team_forecast_calibration" not in source
    assert "TeamForecastCalibration" not in source
    assert "build_team_forecast_calibration_report" not in source
