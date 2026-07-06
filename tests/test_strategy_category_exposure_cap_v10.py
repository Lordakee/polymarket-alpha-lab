from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, replace
from decimal import Decimal
from pathlib import Path

import pytest

from polymarket_alpha_lab.strategy_category_exposure_cap_v10 import (
    DEFAULT_STRATEGY_CATEGORY_EXPOSURE_CAP_V10_CONFIG_VERSION,
    StrategyCategoryExposureCapV10Input,
    StrategyCategoryExposureCapV10Report,
    evaluate_strategy_category_exposure_cap_v10,
    strategy_category_exposure_cap_v10_payload,
)


ZERO = Decimal("0.000000")
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "strategy_category_exposure_cap_v10.py"
)


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def exposure_input(
    *,
    team: str = "macro_team",
    category: str = "macro_cpi",
    current_nav_exposure: Decimal = d("0.050000"),
    candidate_position_size: Decimal = d("0.020000"),
    category_cap: Decimal = d("0.100000"),
    cluster_correlation: Decimal = d("0.100000"),
    tail_risk_tier: str = "low",
    liquidity_score: Decimal = d("0.900000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> StrategyCategoryExposureCapV10Input:
    return StrategyCategoryExposureCapV10Input(
        team=team,
        category=category,
        current_nav_exposure=current_nav_exposure,
        candidate_position_size=candidate_position_size,
        category_cap=category_cap,
        cluster_correlation=cluster_correlation,
        tail_risk_tier=tail_risk_tier,
        liquidity_score=liquidity_score,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def evaluate(
    value: StrategyCategoryExposureCapV10Input | None = None,
) -> StrategyCategoryExposureCapV10Report:
    return evaluate_strategy_category_exposure_cap_v10(value or exposure_input())


def field_values(instance: object) -> dict[str, object]:
    return {field.name: getattr(instance, field.name) for field in fields(instance)}


def assert_public_numeric_fields_are_decimal(instance: object) -> None:
    for field in fields(instance):
        value = getattr(instance, field.name)
        if type(value) is bool:
            continue
        assert type(value) is not float
        assert type(value) is not int


def test_exposure_cap_allows_full_candidate_inside_adjusted_budget() -> None:
    report = evaluate(
        exposure_input(
            team="macro_team",
            category="macro_cpi",
            current_nav_exposure=d("0.030000"),
            candidate_position_size=d("0.020000"),
            category_cap=d("0.100000"),
            cluster_correlation=d("0.000000"),
            tail_risk_tier="low",
            liquidity_score=d("1.000000"),
        ),
    )

    assert type(report) is StrategyCategoryExposureCapV10Report
    assert report.config_version == DEFAULT_STRATEGY_CATEGORY_EXPOSURE_CAP_V10_CONFIG_VERSION
    assert report.team == "macro_team"
    assert report.category == "macro_cpi"
    assert report.remaining_category_cap == d("0.070000")
    assert report.risk_multiplier == d("1.000000")
    assert report.risk_adjusted_capacity == d("0.070000")
    assert report.allowed_size == d("0.020000")
    assert report.cap_status == "pass"
    assert report.risk_action == "allow"
    assert report.reason_codes == ("category_exposure_cap_v10_passed",)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert_public_numeric_fields_are_decimal(report)


def test_exposure_cap_reduces_candidate_for_correlation_tail_and_liquidity_risk() -> None:
    report = evaluate(
        exposure_input(
            team="sports_team",
            category="nba_injuries",
            current_nav_exposure=d("0.050000"),
            candidate_position_size=d("0.040000"),
            category_cap=d("0.100000"),
            cluster_correlation=d("0.500000"),
            tail_risk_tier="high",
            liquidity_score=d("0.500000"),
        ),
    )

    assert report.remaining_category_cap == d("0.050000")
    assert report.correlation_multiplier == d("1.500000")
    assert report.tail_risk_multiplier == d("1.500000")
    assert report.liquidity_multiplier == d("1.500000")
    assert report.risk_multiplier == d("3.375000")
    assert report.risk_adjusted_capacity == d("0.014815")
    assert report.allowed_size == d("0.014815")
    assert report.cap_status == "watch"
    assert report.risk_action == "reduce"
    assert report.reason_codes == (
        "cluster_correlation_elevated",
        "tail_risk_tier_high",
        "liquidity_score_watch",
        "candidate_size_clipped_to_category_budget",
    )


def test_exposure_cap_blocks_when_category_budget_is_exhausted() -> None:
    report = evaluate(
        exposure_input(
            current_nav_exposure=d("0.120000"),
            candidate_position_size=d("0.010000"),
            category_cap=d("0.100000"),
            cluster_correlation=d("0.900000"),
            tail_risk_tier="extreme",
            liquidity_score=d("0.200000"),
        ),
    )

    assert report.remaining_category_cap == ZERO
    assert report.risk_adjusted_capacity == ZERO
    assert report.allowed_size == ZERO
    assert report.cap_status == "blocked"
    assert report.risk_action == "block"
    assert report.reason_codes == (
        "category_cap_exhausted",
        "cluster_correlation_high",
        "tail_risk_tier_extreme",
        "liquidity_score_low",
        "candidate_size_blocked_by_category_budget",
    )


def test_zero_candidate_size_is_allowable_but_keeps_context_reasons() -> None:
    report = evaluate(
        exposure_input(
            candidate_position_size=ZERO,
            cluster_correlation=d("0.850000"),
            tail_risk_tier="medium",
            liquidity_score=d("0.300000"),
        ),
    )

    assert report.allowed_size == ZERO
    assert report.cap_status == "pass"
    assert report.risk_action == "allow"
    assert report.reason_codes == (
        "cluster_correlation_high",
        "tail_risk_tier_medium",
        "liquidity_score_watch",
        "candidate_size_zero",
    )


def test_payload_is_report_only_stringifies_decimals_and_has_no_live_action_fields() -> None:
    report = evaluate()

    payload = strategy_category_exposure_cap_v10_payload(report)

    assert payload["team"] == "macro_team"
    assert payload["category"] == "macro_cpi"
    assert payload["allowed_size"] == "0.020000"
    assert payload["cap_status"] == "pass"
    assert payload["risk_action"] == "allow"
    assert payload["reason_codes"] == ["category_exposure_cap_v10_passed"]
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert "wallet" not in payload
    assert "auth" not in payload
    assert "order" not in payload


def test_rejects_non_decimal_values_bad_ranges_and_bad_flags() -> None:
    with pytest.raises(ValueError, match="current_nav_exposure"):
        replace(exposure_input(), current_nav_exposure=0)
    with pytest.raises(ValueError, match="candidate_position_size"):
        replace(exposure_input(), candidate_position_size=_DecimalSubclass("0.010000"))
    with pytest.raises(ValueError, match="cluster_correlation"):
        replace(exposure_input(), cluster_correlation=d("1.000001"))
    with pytest.raises(ValueError, match="tail_risk_tier"):
        replace(exposure_input(), tail_risk_tier="catastrophic")
    with pytest.raises(ValueError, match="category_cap"):
        replace(exposure_input(), category_cap=d("-0.010000"))
    with pytest.raises(ValueError, match="paper_only"):
        evaluate(exposure_input(paper_only=False))
    with pytest.raises(ValueError, match="readonly"):
        evaluate(exposure_input(readonly=False))


def test_dataclasses_are_frozen_public_api_rejects_bad_types_and_rebuilds() -> None:
    value = exposure_input()
    report = evaluate(value)
    rebuilt = StrategyCategoryExposureCapV10Report(**field_values(report))

    assert rebuilt == report
    with pytest.raises(FrozenInstanceError):
        value.team = "other_team"
    with pytest.raises(FrozenInstanceError):
        report.allowed_size = d("0.010000")
    with pytest.raises(ValueError, match="input"):
        evaluate_strategy_category_exposure_cap_v10(object())
    with pytest.raises(ValueError, match="report"):
        strategy_category_exposure_cap_v10_payload(object())


def test_module_has_no_live_trading_or_durable_store_surfaces() -> None:
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    banned_import_roots = {
        "builtins",
        "clob_client",
        "httpx",
        "os",
        "pathlib",
        "psycopg",
        "requests",
        "sqlite3",
        "subprocess",
        "supabase",
        "web3",
    }
    banned_calls = {"open", "remove", "unlink", "replace", "rename"}

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".", maxsplit=1)[0] not in banned_import_roots
        if isinstance(node, ast.ImportFrom) and node.module:
            assert node.module.split(".", maxsplit=1)[0] not in banned_import_roots
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in banned_calls
