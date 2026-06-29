from __future__ import annotations

import ast
from dataclasses import fields, is_dataclass
from decimal import Decimal
from pathlib import Path
from typing import get_type_hints

import pytest


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "probability_selection_scorer_agreement_trend.py"
)

FORBIDDEN_TEXT = (
    "POLYMARKET_ALPHA_LAB_",
    "argparse",
    "click",
    "commit(",
    "create_order",
    "delete ",
    "dsn",
    "execute(",
    "hostaddr",
    "httpx",
    "insert ",
    "jsonl",
    "mongo",
    "open(",
    "os.environ",
    "pathlib",
    "private-key",
    "private_key",
    "psycopg",
    "redis",
    "requests",
    "rollback(",
    "signing",
    "sqlalchemy",
    "sqlite",
    "submit_order",
    "supabase",
    "update ",
    "urllib",
    "wallet",
)

FORBIDDEN_IMPORT_ROOTS = (
    "argparse",
    "click",
    "httpx",
    "json",
    "jsonlines",
    "os",
    "pathlib",
    "psycopg",
    "pymongo",
    "redis",
    "requests",
    "socket",
    "sqlalchemy",
    "sqlite3",
    "subprocess",
    "urllib",
)

FORBIDDEN_CALL_NAMES = (
    "cancel_order",
    "commit",
    "connect",
    "execute",
    "open",
    "replace_order",
    "rollback",
    "submit_order",
    "write",
    "write_bytes",
    "write_text",
)


def _source() -> str:
    return MODULE_PATH.read_text(encoding="utf-8")


def _tree() -> ast.Module:
    return ast.parse(_source())


def _api():
    from polymarket_alpha_lab import probability_selection_scorer_agreement_trend

    return probability_selection_scorer_agreement_trend


def test_agreement_trend_source_has_no_durable_store_or_live_trading_surface() -> None:
    source = _source().lower()

    for token in FORBIDDEN_TEXT:
        assert token not in source, f"forbidden token found: {token}"


def test_agreement_trend_imports_and_calls_stay_pure() -> None:
    import_roots: set[str] = set()
    call_names: set[str] = set()

    for node in ast.walk(_tree()):
        if isinstance(node, ast.Import):
            for alias in node.names:
                import_roots.add(alias.name.split(".", 1)[0])
        elif isinstance(node, ast.ImportFrom):
            module_name = node.module or ""
            import_roots.add(module_name.split(".", 1)[0])
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                call_names.add(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                call_names.add(node.func.attr)

    assert import_roots.isdisjoint(FORBIDDEN_IMPORT_ROOTS)
    assert call_names.isdisjoint(FORBIDDEN_CALL_NAMES)


def test_agreement_trend_public_surface_is_report_only() -> None:
    exported = set(_api().__all__)

    assert exported == {
        "DEFAULT_PROBABILITY_SELECTION_SCORER_AGREEMENT_TREND_CONFIG_VERSION",
        "ProbabilitySelectionScorerAgreementTrendConfig",
        "ProbabilitySelectionScorerAgreementTrendReport",
        "build_probability_selection_scorer_agreement_trend_report",
    }
    for exported_name in exported:
        lowered = exported_name.lower()
        for forbidden in ("dsn", "table", "persist", "sink", "live", "wallet", "order"):
            assert forbidden not in lowered


def test_agreement_trend_dataclasses_are_frozen_with_true_hard_flags() -> None:
    config_type = _api().ProbabilitySelectionScorerAgreementTrendConfig
    report_type = _api().ProbabilitySelectionScorerAgreementTrendReport

    assert is_dataclass(config_type)
    assert is_dataclass(report_type)
    assert config_type.__dataclass_params__.frozen is True
    assert report_type.__dataclass_params__.frozen is True

    config_fields = {field.name: field.default for field in fields(config_type)}
    report_fields = {field.name: field.default for field in fields(report_type)}
    for field_name in ("paper_only", "report_only", "readonly"):
        assert config_fields[field_name] is True
        assert report_fields[field_name] is True

    for field_name in ("paper_only", "report_only", "readonly"):
        with pytest.raises(ValueError, match=field_name):
            config_type(**{field_name: False})


def test_agreement_trend_uses_decimal_for_average_counts_and_never_float_literals() -> None:
    tree = _tree()

    assert any(
        isinstance(node, ast.Name) and node.id == "Decimal"
        for node in ast.walk(tree)
    )
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, float):
            raise AssertionError(f"float literal found: {node.value}")

    report_annotations = get_type_hints(_api().ProbabilitySelectionScorerAgreementTrendReport)
    assert report_annotations["average_selected_count"] is Decimal
    assert report_annotations["average_scorer_candidate_count"] is Decimal
