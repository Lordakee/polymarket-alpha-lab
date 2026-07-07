from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, tzinfo
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.strategy_recommendation_category_budget_pressure_gate_v2"
GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)


class _NoneOffsetTimezone(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


def api() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values = {
        "category_budget_notional": d("200.000000"),
        "correlated_event_cluster_notional_cap": d("120.000000"),
        "max_liquidity_capacity_utilization": d("0.500000"),
        "category_exposure_watch_ratio": d("0.750000"),
        "correlated_event_watch_ratio": d("0.600000"),
        "liquidity_capacity_watch_ratio": d("0.800000"),
        "min_independent_source_count": d("4"),
        "source_block_count": d("1"),
    }
    values.update(overrides)
    return module.StrategyRecommendationCategoryBudgetPressureGateV2Config(**values)


def recommendation(**overrides: object) -> Any:
    module = api()
    values = {
        "recommendation_id": "rec-alpha",
        "category": "sports",
        "requested_notional": d("40.000000"),
        "current_category_paper_exposure": d("80.000000"),
        "correlated_event_cluster_exposure": d("20.000000"),
        "independent_source_count": d("4"),
        "liquidity_capacity": d("200.000000"),
        "source_reference": "research-note-1",
    }
    values.update(overrides)
    return module.StrategyRecommendationCategoryBudgetPressureGateV2Input(**values)


def report(*rows: Any, cfg: Any | None = None) -> Any:
    module = api()
    return module.build_strategy_recommendation_category_budget_pressure_gate_v2(
        rows,
        config=cfg or config(),
        generated_at=GENERATED_AT,
    )


def assert_numeric_fields_are_decimal(value: object) -> None:
    for field in fields(value):
        item = getattr(value, field.name)
        if type(item) is bool:
            continue
        assert type(item) is not float
        assert type(item) is not int
        if isinstance(item, tuple):
            for nested in item:
                if is_dataclass(nested):
                    assert_numeric_fields_are_decimal(nested)


def assert_no_float_values(value: object) -> None:
    assert type(value) is not float
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_values(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_float_values(item)


def test_gate_reduces_and_blocks_category_pressure_deterministically() -> None:
    result = report(
        recommendation(
            recommendation_id="rec-sports",
            category="sports",
            requested_notional=d("40.000000"),
            current_category_paper_exposure=d("80.000000"),
            correlated_event_cluster_exposure=d("20.000000"),
            independent_source_count=d("4"),
            liquidity_capacity=d("200.000000"),
        ),
        recommendation(
            recommendation_id="rec-macro",
            category="macro",
            requested_notional=d("80.000000"),
            current_category_paper_exposure=d("150.000000"),
            correlated_event_cluster_exposure=d("40.000000"),
            independent_source_count=d("2"),
            liquidity_capacity=d("100.000000"),
        ),
        recommendation(
            recommendation_id="rec-climate",
            category="climate",
            requested_notional=d("25.000000"),
            current_category_paper_exposure=d("210.000000"),
            correlated_event_cluster_exposure=d("130.000000"),
            independent_source_count=d("0"),
            liquidity_capacity=d("0.000000"),
        ),
    )

    assert is_dataclass(result)
    assert result.generated_at == GENERATED_AT
    assert result.config_version == (
        "strategy-recommendation-category-budget-pressure-gate-v2"
    )
    assert result.recommendation_count == d("3")
    assert result.pass_count == d("1")
    assert result.watch_count == d("1")
    assert result.blocked_count == d("1")
    assert result.total_requested_notional == d("145.000000")
    assert result.total_approved_notional == d("65.000000")
    assert result.total_reduction_notional == d("80.000000")
    assert result.gate_status == "blocked"
    assert result.reason_codes == (
        "category_paper_exposure_blocked",
        "category_paper_exposure_watch",
        "category_paper_exposure_reduced",
        "correlated_event_cluster_blocked",
        "correlated_event_cluster_watch",
        "source_coverage_blocked",
        "source_coverage_weak",
        "liquidity_capacity_blocked",
        "liquidity_capacity_watch",
        "liquidity_capacity_reduced",
        "recommendation_budget_blocked",
        "recommendation_budget_reduced",
        "recommendation_budget_pass",
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True
    assert_numeric_fields_are_decimal(result)

    assert tuple(row.recommendation_id for row in result.results) == (
        "rec-climate",
        "rec-macro",
        "rec-sports",
    )

    blocked = result.results[0]
    assert blocked.category == "climate"
    assert blocked.category_exposure_after_requested == d("235.000000")
    assert blocked.category_pressure_ratio == d("1.175000")
    assert blocked.remaining_category_budget == d("0.000000")
    assert blocked.remaining_correlated_event_budget == d("0.000000")
    assert blocked.liquidity_allocation_capacity == d("0.000000")
    assert blocked.source_coverage_ratio == d("0.000000")
    assert blocked.approved_notional == d("0.000000")
    assert blocked.reduction_notional == d("25.000000")
    assert blocked.gate_status == "blocked"
    assert blocked.reason_codes == (
        "category_paper_exposure_blocked",
        "correlated_event_cluster_blocked",
        "source_coverage_blocked",
        "liquidity_capacity_blocked",
        "recommendation_budget_blocked",
    )

    watched = result.results[1]
    assert watched.category == "macro"
    assert watched.category_pressure_ratio == d("1.150000")
    assert watched.correlated_event_pressure_ratio == d("1.000000")
    assert watched.source_coverage_ratio == d("0.500000")
    assert watched.liquidity_allocation_capacity == d("50.000000")
    assert watched.liquidity_capacity_utilization_ratio == d("1.600000")
    assert watched.approved_notional == d("25.000000")
    assert watched.reduction_notional == d("55.000000")
    assert watched.gate_status == "watch"
    assert watched.reason_codes == (
        "category_paper_exposure_watch",
        "category_paper_exposure_reduced",
        "correlated_event_cluster_watch",
        "source_coverage_weak",
        "liquidity_capacity_watch",
        "liquidity_capacity_reduced",
        "recommendation_budget_reduced",
    )

    passed = result.results[2]
    assert passed.gate_status == "pass"
    assert passed.approved_notional == d("40.000000")
    assert passed.reduction_notional == d("0.000000")
    assert passed.reason_codes == ("recommendation_budget_pass",)


def test_empty_report_is_blocked_readonly_and_decimal_zeroed() -> None:
    result = report()

    assert result.recommendation_count == d("0")
    assert result.pass_count == d("0")
    assert result.watch_count == d("0")
    assert result.blocked_count == d("0")
    assert result.total_requested_notional == d("0.000000")
    assert result.total_approved_notional == d("0.000000")
    assert result.total_reduction_notional == d("0.000000")
    assert result.gate_status == "blocked"
    assert result.reason_codes == (
        "strategy_recommendation_category_budget_pressure_gate_v2_empty",
    )
    assert result.results == ()
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True


def test_payload_helper_is_json_ready_and_redacts_source_references() -> None:
    module = api()
    result = report(
        recommendation(
            source_reference="https://example.test/feed?token=secret",
        ),
    )

    payload = module.strategy_recommendation_category_budget_pressure_gate_v2_payload(
        result,
    )
    encoded = json.dumps(payload, sort_keys=True, allow_nan=False)

    assert payload["generated_at"] == "2026-07-06T12:00:00+00:00"
    assert payload["recommendation_count"] == "1"
    assert payload["results"][0]["approved_notional"] == "40.000000"
    assert payload["results"][0]["redacted_source_reference"] == "<redacted>"
    assert "token=secret" not in encoded
    assert_no_float_values(payload)
    assert (
        module.strategy_recommendation_category_budget_pressure_gate_v2_payload(payload)
        == payload
    )

    with pytest.raises(ValueError, match="readonly"):
        module.strategy_recommendation_category_budget_pressure_gate_v2_payload(
            {**payload, "readonly": False},
        )

    with pytest.raises(ValueError, match="unsafe"):
        module.strategy_recommendation_category_budget_pressure_gate_v2_payload(
            {**payload, "wallet": {"address": "0x0"}},
        )

    with pytest.raises(ValueError, match="float"):
        module.strategy_recommendation_category_budget_pressure_gate_v2_payload(
            {**payload, "total_approved_notional": 1.0},
        )


def test_inputs_config_and_datetimes_reject_invalid_values() -> None:
    module = api()

    with pytest.raises(ValueError, match="requested_notional must be a Decimal"):
        recommendation(requested_notional=1)
    with pytest.raises(ValueError, match="category must be a non-empty canonical string"):
        recommendation(category=" sports")
    with pytest.raises(ValueError, match="independent_source_count must be an integer"):
        recommendation(independent_source_count=d("1.5"))
    with pytest.raises(ValueError, match="paper_only must be True"):
        recommendation(paper_only=False)
    with pytest.raises(ValueError, match="source_block_count must not exceed"):
        config(source_block_count=d("5"))
    with pytest.raises(ValueError, match="category_exposure_watch_ratio must be"):
        config(category_exposure_watch_ratio=d("1.100000"))

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        module.build_strategy_recommendation_category_budget_pressure_gate_v2(
            (recommendation(),),
            config=config(),
            generated_at=datetime(2026, 7, 6, 12, 0),
        )

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        module.build_strategy_recommendation_category_budget_pressure_gate_v2(
            (recommendation(),),
            config=config(),
            generated_at=datetime(2026, 7, 6, 12, 0, tzinfo=_NoneOffsetTimezone()),
        )

    with pytest.raises(ValueError, match="recommendation_id values must be unique"):
        report(recommendation(), recommendation())

    result = report(recommendation())
    with pytest.raises(FrozenInstanceError):
        result.results[0].category = "macro"


def test_tamper_evident_result_and_report_validation_recomputes_fields() -> None:
    result = report(recommendation())
    row = result.results[0]

    with pytest.raises(ValueError, match="approved_notional must match"):
        replace(row, approved_notional=row.approved_notional + d("0.000001"))

    with pytest.raises(ValueError, match="reduction_notional must match"):
        replace(row, reduction_notional=row.reduction_notional + d("0.000001"))

    with pytest.raises(ValueError, match="gate_status must match"):
        replace(row, gate_status="blocked")

    with pytest.raises(ValueError, match="total_approved_notional must match"):
        replace(
            result,
            total_approved_notional=result.total_approved_notional + d("0.000001"),
        )

    with pytest.raises(ValueError, match="results must be sorted deterministically"):
        replace(
            result,
            results=(
                recommendation_result("zeta", "macro"),
                recommendation_result("alpha", "sports"),
            ),
        )


def recommendation_result(recommendation_id: str, category: str) -> Any:
    return report(
        recommendation(recommendation_id=recommendation_id, category=category),
    ).results[0]


def test_module_is_pure_readonly_report_only_and_contains_no_io_surfaces() -> None:
    path = Path(
        "src/polymarket_alpha_lab/"
        "strategy_recommendation_category_budget_pressure_gate_v2.py",
    )
    tree = ast.parse(path.read_text(encoding="utf-8"))
    source = path.read_text(encoding="utf-8").lower()

    banned_imports = {
        "asyncio",
        "http",
        "os",
        "pathlib",
        "requests",
        "socket",
        "sqlite3",
        "subprocess",
        "supabase",
        "urllib",
    }
    banned_calls = {
        "open",
        "connect",
        "request",
        "urlopen",
        "submit",
        "post",
        "send",
        "login",
    }
    banned_attributes = banned_calls | {"commit", "rollback", "session"}
    forbidden_terms = (
        "live trading",
        "auth",
        "wallet",
        "broker",
        "order placement",
        "database",
        "supabase",
    )

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            assert not ({alias.name.split(".")[0] for alias in node.names} & banned_imports)
        elif isinstance(node, ast.ImportFrom):
            assert (node.module or "").split(".")[0] not in banned_imports
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in banned_calls
        elif isinstance(node, ast.Attribute):
            assert node.attr not in banned_attributes

    assert [term for term in forbidden_terms if term in source] == []
