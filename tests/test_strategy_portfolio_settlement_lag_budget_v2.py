from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.strategy_portfolio_settlement_lag_budget_v2"
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "strategy_portfolio_settlement_lag_budget_v2.py"
)
GENERATED_AT = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


def api() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def cfg(**overrides: object) -> Any:
    module = api()
    values = {
        "settlement_lag_budget_notional": d("500.000000"),
        "annual_cost_drag_rate": d("0.120000"),
        "expected_lag_watch_days": d("3.000000"),
        "expected_lag_blocked_days": d("7.000000"),
        "category_concentration_watch_ratio": d("0.500000"),
        "category_concentration_blocked_ratio": d("0.700000"),
        "liquidity_lockup_watch_ratio": d("0.300000"),
        "liquidity_lockup_blocked_ratio": d("0.600000"),
        "cost_drag_watch_ratio": d("0.001000"),
        "cost_drag_blocked_ratio": d("0.002000"),
        "risk_budget_watch_ratio": d("0.750000"),
        "risk_budget_blocked_ratio": d("1.000000"),
    }
    values.update(overrides)
    return module.StrategyPortfolioSettlementLagBudgetV2Config(**values)


def exposure(**overrides: object) -> Any:
    module = api()
    values = {
        "exposure_id": "exposure-alpha",
        "category": "sports",
        "pending_resolution_notional": d("100.000000"),
        "expected_lag_days": d("1.000000"),
        "liquidity_lockup_ratio": d("0.100000"),
    }
    values.update(overrides)
    return module.StrategyPortfolioSettlementLagBudgetV2Input(**values)


def report(*rows: Any, config: Any | None = None) -> Any:
    module = api()
    return module.build_strategy_portfolio_settlement_lag_budget_v2(
        rows,
        config=config or cfg(),
        generated_at=GENERATED_AT,
    )


def walk(value: object) -> tuple[object, ...]:
    if isinstance(value, dict):
        return tuple(value.values()) + tuple(item for value in value.values() for item in walk(value))
    if isinstance(value, list):
        return tuple(value) + tuple(item for value in value for item in walk(value))
    return (value,)


def assert_numeric_fields_are_decimal(value: object) -> None:
    for field in fields(value):
        item = getattr(value, field.name)
        if type(item) is bool:
            continue
        assert type(item) is not int
        assert type(item) is not float
        if isinstance(item, tuple):
            for nested in item:
                if is_dataclass(nested):
                    assert_numeric_fields_are_decimal(nested)


def test_builds_phase1_settlement_lag_budget_report() -> None:
    result = report(
        exposure(
            exposure_id="sports-a",
            category="sports",
            pending_resolution_notional=d("200.000000"),
            expected_lag_days=d("4.000000"),
            liquidity_lockup_ratio=d("0.500000"),
        ),
        exposure(
            exposure_id="sports-b",
            category="sports",
            pending_resolution_notional=d("100.000000"),
            expected_lag_days=d("2.000000"),
            liquidity_lockup_ratio=d("0.200000"),
        ),
        exposure(
            exposure_id="macro-a",
            category="macro",
            pending_resolution_notional=d("50.000000"),
            expected_lag_days=d("9.000000"),
            liquidity_lockup_ratio=d("0.800000"),
        ),
        exposure(
            exposure_id="culture-a",
            category="culture",
            pending_resolution_notional=d("50.000000"),
            expected_lag_days=d("1.000000"),
            liquidity_lockup_ratio=d("0.100000"),
        ),
    )

    assert is_dataclass(result)
    assert result.generated_at == GENERATED_AT
    assert result.config_version == "strategy-portfolio-settlement-lag-budget-v2"
    assert result.exposure_count == d("4")
    assert result.category_count == d("3")
    assert result.pass_count == d("1")
    assert result.watch_count == d("0")
    assert result.blocked_count == d("2")
    assert result.pending_resolution_notional == d("400.000000")
    assert result.weighted_expected_lag_days == d("3.750000")
    assert result.largest_category == "sports"
    assert result.largest_category_pending_notional == d("300.000000")
    assert result.largest_category_concentration_ratio == d("0.750000")
    assert result.liquidity_lockup_notional == d("165.000000")
    assert result.liquidity_lockup_ratio == d("0.412500")
    assert result.cost_drag_notional == d("0.493150")
    assert result.cost_drag_ratio == d("0.001233")
    assert result.risk_budget_notional == d("500.000000")
    assert result.risk_budget_usage_ratio == d("0.800000")
    assert result.digest_status == "blocked"
    assert result.reason_codes == (
        "category_concentration_blocked",
        "cost_drag_blocked",
        "cost_drag_watch",
        "expected_lag_blocked",
        "expected_lag_watch",
        "liquidity_lockup_blocked",
        "liquidity_lockup_watch",
        "risk_budget_usage_watch",
        "settlement_lag_budget_blocked",
        "settlement_lag_budget_pass",
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True
    assert_numeric_fields_are_decimal(result)

    assert tuple(row.category for row in result.rows) == ("sports", "macro", "culture")

    sports = result.rows[0]
    assert sports.rank == d("1")
    assert sports.exposure_count == d("2")
    assert sports.pending_resolution_notional == d("300.000000")
    assert sports.weighted_expected_lag_days == d("3.333333")
    assert sports.category_concentration_ratio == d("0.750000")
    assert sports.liquidity_lockup_notional == d("120.000000")
    assert sports.liquidity_lockup_ratio == d("0.400000")
    assert sports.cost_drag_notional == d("0.328767")
    assert sports.cost_drag_ratio == d("0.001096")
    assert sports.risk_budget_usage_ratio == d("0.600000")
    assert sports.budget_status == "blocked"
    assert sports.reason_codes == (
        "category_concentration_blocked",
        "cost_drag_watch",
        "expected_lag_watch",
        "liquidity_lockup_watch",
        "settlement_lag_budget_blocked",
    )

    macro = result.rows[1]
    assert macro.rank == d("2")
    assert macro.budget_status == "blocked"
    assert macro.cost_drag_notional == d("0.147945")
    assert macro.cost_drag_ratio == d("0.002959")
    assert macro.reason_codes == (
        "cost_drag_blocked",
        "expected_lag_blocked",
        "liquidity_lockup_blocked",
        "settlement_lag_budget_blocked",
    )

    clear = result.rows[2]
    assert clear.rank == d("3")
    assert clear.budget_status == "pass"
    assert clear.reason_codes == ("settlement_lag_budget_pass",)


def test_empty_report_is_pass_decimal_zeroed_and_report_only() -> None:
    result = report()

    assert result.exposure_count == d("0")
    assert result.category_count == d("0")
    assert result.pass_count == d("0")
    assert result.watch_count == d("0")
    assert result.blocked_count == d("0")
    assert result.pending_resolution_notional == d("0.000000")
    assert result.weighted_expected_lag_days == d("0.000000")
    assert result.largest_category is None
    assert result.liquidity_lockup_notional == d("0.000000")
    assert result.cost_drag_notional == d("0.000000")
    assert result.risk_budget_usage_ratio == d("0.000000")
    assert result.digest_status == "pass"
    assert result.reason_codes == ("strategy_portfolio_settlement_lag_budget_v2_empty",)
    assert result.rows == ()
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True


def test_payload_helper_serializes_decimal_strings_and_rejects_unsafe_payloads() -> None:
    module = api()
    result = report(exposure())

    payload = module.strategy_portfolio_settlement_lag_budget_v2_payload(result)
    encoded = json.dumps(payload, sort_keys=True, allow_nan=False)

    assert payload["generated_at"] == "2026-07-07T12:00:00+00:00"
    assert payload["exposure_count"] == "1"
    assert payload["rows"][0]["rank"] == "1"
    assert payload["rows"][0]["cost_drag_notional"] == "0.032877"
    assert module.strategy_portfolio_settlement_lag_budget_v2_payload(payload) == payload
    assert not any(isinstance(item, float) for item in walk(payload))
    assert "token=secret" not in encoded

    with pytest.raises(ValueError, match="readonly"):
        module.strategy_portfolio_settlement_lag_budget_v2_payload(
            {**payload, "readonly": False},
        )
    with pytest.raises(ValueError, match="unsafe"):
        module.strategy_portfolio_settlement_lag_budget_v2_payload(
            {**payload, "wallet": {"reference": "0x0"}},
        )
    with pytest.raises(ValueError, match="Decimal"):
        module.strategy_portfolio_settlement_lag_budget_v2_payload(
            {**payload, "exposure_count": 1},
        )
    with pytest.raises(ValueError, match="float"):
        module.strategy_portfolio_settlement_lag_budget_v2_payload(
            {**payload, "risk_budget_usage_ratio": 0.5},
        )


def test_validation_rejects_non_decimal_values_flags_duplicates_and_tampering() -> None:
    module = api()

    with pytest.raises(ValueError, match="pending_resolution_notional must be a Decimal"):
        exposure(pending_resolution_notional=1)
    with pytest.raises(ValueError, match="expected_lag_days must be a Decimal"):
        exposure(expected_lag_days=1.0)
    with pytest.raises(ValueError, match="liquidity_lockup_ratio must be exactly Decimal"):
        exposure(liquidity_lockup_ratio=_DecimalSubclass("0.100000"))
    with pytest.raises(ValueError, match="exposure_id must be a canonical nonblank string"):
        exposure(exposure_id=" exposure-alpha ")
    with pytest.raises(ValueError, match="paper_only"):
        exposure(paper_only=False)
    with pytest.raises(ValueError, match="watch thresholds must not exceed blocked"):
        cfg(expected_lag_watch_days=d("8.000000"), expected_lag_blocked_days=d("7.000000"))
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        module.build_strategy_portfolio_settlement_lag_budget_v2(
            (),
            config=cfg(),
            generated_at=datetime(2026, 7, 7, 12, 0),
        )
    with pytest.raises(ValueError, match="duplicate exposure_id"):
        report(
            exposure(exposure_id="duplicate-a"),
            exposure(exposure_id="duplicate-a", category="macro"),
        )
    with pytest.raises(ValueError, match="config must be"):
        module.build_strategy_portfolio_settlement_lag_budget_v2(
            (),
            config=object(),
            generated_at=GENERATED_AT,
        )

    result = report(exposure(exposure_id="one"), exposure(exposure_id="two", category="macro"))
    with pytest.raises(FrozenInstanceError):
        result.rows[0].category = "changed"
    with pytest.raises(ValueError, match="pending_resolution_notional must match rows"):
        replace(result, pending_resolution_notional=d("99.000000"))
    with pytest.raises(ValueError, match="rows must use deterministic sort"):
        replace(result, rows=tuple(reversed(result.rows)))
    with pytest.raises(ValueError, match="digest_status must match rows"):
        replace(result, digest_status="blocked")
    with pytest.raises(ValueError, match="readonly"):
        replace(result.rows[0], readonly=False)


def test_module_surface_is_local_report_only_and_omits_execution_paths() -> None:
    module = api()
    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source.lower()
    tree = ast.parse(source)

    assert module.__all__ == (
        "DEFAULT_STRATEGY_PORTFOLIO_SETTLEMENT_LAG_BUDGET_V2_CONFIG_VERSION",
        "StrategyPortfolioSettlementLagBudgetV2Config",
        "StrategyPortfolioSettlementLagBudgetV2Input",
        "StrategyPortfolioSettlementLagBudgetV2CategoryBudget",
        "StrategyPortfolioSettlementLagBudgetV2Report",
        "build_strategy_portfolio_settlement_lag_budget_v2",
        "strategy_portfolio_settlement_lag_budget_v2_payload",
    )
    for exported_name in module.__all__:
        exported = getattr(module, exported_name)
        if isinstance(exported, type):
            assert is_dataclass(exported)
            assert exported.__dataclass_params__.frozen

    for forbidden in (
        "live",
        "trading",
        "auth",
        "wallet",
        "broker",
        "private_key",
        "requests",
        "httpx",
        "urllib",
        "socket",
        "sqlite",
        "psycopg",
        "supabase",
        "sqlalchemy",
        "subprocess",
        "open(",
        ".read(",
        ".write(",
    ):
        assert forbidden not in lowered

    imported_modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported_modules.append(node.module or "")
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in {"float", "open"}

    assert set(imported_modules) <= {
        "__future__",
        "collections.abc",
        "dataclasses",
        "datetime",
        "decimal",
        "typing",
    }
