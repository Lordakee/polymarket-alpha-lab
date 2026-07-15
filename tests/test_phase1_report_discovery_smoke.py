from __future__ import annotations

import ast
import importlib
import inspect
from dataclasses import fields, is_dataclass
from pathlib import Path
from typing import Any

import pytest


EXPECTED_PHASE1_REPORT_MODULES = (
    "polymarket_alpha_lab.forecast_context_readiness_report",
    "polymarket_alpha_lab.information_freshness_refresh_sla_readiness_report",
    "polymarket_alpha_lab.input_failure_degradation_readiness_report",
    "polymarket_alpha_lab.portfolio_probability_event_readiness_report",
    "polymarket_alpha_lab.post_settlement_calibration_experience_feedback_report",
    "polymarket_alpha_lab.probability_event_cost_adjusted_position_recommendation_report",
    "polymarket_alpha_lab.probability_event_market_signal_risk_readiness_report",
    "polymarket_alpha_lab.strategy_phase1_readiness_aggregator",
)

PHASE1_REPORT_MODULES = EXPECTED_PHASE1_REPORT_MODULES

PACKAGE = "polymarket_alpha_lab"
SOURCE_ROOT = Path(__file__).resolve().parents[1] / "src" / PACKAGE
FORBIDDEN_IMPORT_ROOTS = {
    "httpx",
    "psycopg",
    "requests",
    "socket",
    "sqlalchemy",
    "subprocess",
    "supabase",
    "urllib",
    "web3",
}
FORBIDDEN_TOP_LEVEL_CALLS = {
    "open",
    "Path",
    "connect",
    "request",
    "run",
}


def test_phase1_report_module_catalog_matches_current_node() -> None:
    assert PHASE1_REPORT_MODULES == EXPECTED_PHASE1_REPORT_MODULES


@pytest.mark.parametrize("module_name", PHASE1_REPORT_MODULES)
def test_phase1_report_modules_import_without_io_side_effects(module_name: str) -> None:
    module = importlib.import_module(module_name)

    assert module.__name__ == module_name


@pytest.mark.parametrize("module_name", PHASE1_REPORT_MODULES)
def test_phase1_report_builders_and_dataclasses_are_discoverable(
    module_name: str,
) -> None:
    module = importlib.import_module(module_name)

    builders = _public_builders(module)
    dataclasses = _public_dataclasses(module)

    assert builders, f"{module_name} should expose at least one public build_* function"
    assert dataclasses, f"{module_name} should expose public dataclasses"
    for builder in builders:
        signature = inspect.signature(builder)
        assert signature.return_annotation is not inspect.Signature.empty


@pytest.mark.parametrize("module_name", PHASE1_REPORT_MODULES)
def test_phase1_report_dataclass_flags_remain_paper_report_only_readonly(
    module_name: str,
) -> None:
    module = importlib.import_module(module_name)

    flagged_dataclasses = [
        data_class
        for data_class in _public_dataclasses(module)
        if _has_all_flag_fields(data_class)
    ]

    assert flagged_dataclasses, f"{module_name} should expose flag-bearing dataclasses"
    for data_class in flagged_dataclasses:
        defaults = {field.name: field.default for field in fields(data_class)}
        assert defaults["paper_only"] is True
        assert defaults["report_only"] is True
        assert defaults["readonly"] is True


@pytest.mark.parametrize("module_name", PHASE1_REPORT_MODULES)
def test_phase1_report_modules_do_not_expose_io_or_execution_imports(
    module_name: str,
) -> None:
    module_basename = module_name.rsplit(".", maxsplit=1)[-1]
    tree = ast.parse((SOURCE_ROOT / f"{module_basename}.py").read_text(encoding="utf-8"))

    assert _forbidden_import_roots(tree).isdisjoint(FORBIDDEN_IMPORT_ROOTS)
    assert _top_level_call_names(tree).isdisjoint(FORBIDDEN_TOP_LEVEL_CALLS)


def test_report_discovery_registry_stays_readonly_paper_report_only() -> None:
    module = importlib.import_module(f"{PACKAGE}.report_discovery")

    output = module.format_report_discovery()

    assert "read-only" in output.lower()
    assert "paper/report-only" in output.lower()
    assert "Phase 1 readiness reports" in output
    for forbidden in (
        "persist",
        "dsn",
        "supabase",
        "private-key",
        "wallet",
        "order",
        "auth",
        "live",
    ):
        assert forbidden not in output.lower()


def _public_builders(module: Any) -> tuple[Any, ...]:
    return tuple(
        value
        for name, value in vars(module).items()
        if name.startswith("build_") and inspect.isfunction(value) and value.__module__ == module.__name__
    )


def _public_dataclasses(module: Any) -> tuple[type[Any], ...]:
    return tuple(
        value
        for name, value in vars(module).items()
        if not name.startswith("_")
        and isinstance(value, type)
        and is_dataclass(value)
        and value.__module__ == module.__name__
    )


def _has_all_flag_fields(data_class: type[Any]) -> bool:
    field_names = {field.name for field in fields(data_class)}
    return {"paper_only", "report_only", "readonly"}.issubset(field_names)


def _forbidden_import_roots(tree: ast.AST) -> set[str]:
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".", maxsplit=1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            roots.add(node.module.split(".", maxsplit=1)[0])
    return roots


def _top_level_call_names(tree: ast.Module) -> set[str]:
    names: set[str] = set()
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                if isinstance(child.func, ast.Name):
                    names.add(child.func.id)
                elif isinstance(child.func, ast.Attribute):
                    names.add(child.func.attr)
    return names
