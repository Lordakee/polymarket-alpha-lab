from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, fields, replace
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "strategy_sizing_risk_budget_v4.py"
)
ZERO = Decimal("0.000000")


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.strategy_sizing_risk_budget_v4",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": "strategy-sizing-risk-budget-v4-test",
        "nav": d("100000.000000"),
        "max_nav_share": d("0.050000"),
        "full_size_expected_value": d("0.100000"),
        "min_expected_value": d("0.020000"),
        "watch_expected_value": d("0.050000"),
        "max_resolution_risk": d("0.600000"),
        "watch_resolution_risk": d("0.350000"),
        "watch_capacity_headroom_share": d("0.150000"),
    }
    values.update(overrides)
    return module.StrategySizingRiskBudgetV4Config(**values)


def candidate(**overrides: object):
    module = api()
    values = {
        "market_id": "market_alpha",
        "market_reference": "public-market-alpha",
        "correlation_cluster_id": "macro_cluster",
        "expected_value": d("0.120000"),
        "liquidity_capacity": d("3000.000000"),
        "team_allocated_notional": d("3500.000000"),
        "team_allocation_cap": d("5000.000000"),
        "cluster_allocated_notional": d("7000.000000"),
        "cluster_allocation_cap": d("10000.000000"),
        "resolution_risk": d("0.200000"),
        "reason_codes": ("screened_market",),
    }
    values.update(overrides)
    return module.StrategySizingRiskBudgetV4Candidate(**values)


def decision(*, row=None, cfg=None):
    module = api()
    return module.build_strategy_sizing_risk_budget_v4(
        row if row is not None else candidate(),
        config=cfg if cfg is not None else config(),
    )


def assert_no_float_values(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError(f"unexpected float value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_values(item)
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_no_float_values(item)


def test_sizes_paper_notional_from_nav_ev_capacity_team_cluster_and_resolution() -> None:
    result = decision()

    assert result.config_version == "strategy-sizing-risk-budget-v4-test"
    assert result.market_id == "market_alpha"
    assert result.redacted_market_reference == "public-market-alpha"
    assert result.correlation_cluster_id == "macro_cluster"
    assert result.nav_limit == d("5000.000000")
    assert result.expected_value_multiplier == d("1.000000")
    assert result.resolution_risk_multiplier == d("0.800000")
    assert result.liquidity_capacity == d("3000.000000")
    assert result.team_capacity_headroom == d("1500.000000")
    assert result.cluster_capacity_headroom == d("3000.000000")
    assert result.binding_capacity == d("1500.000000")
    assert result.paper_notional == d("1200.000000")
    assert result.sizing_status == "pass"
    assert result.risk_budget_reason_codes == (
        "screened_market",
        "strategy_sizing_risk_budget_v4_pass",
        "expected_value_pass",
        "liquidity_capacity_available",
        "team_allocation_cap_limited",
        "market_correlation_cluster_capacity_available",
        "resolution_risk_contained",
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True


def test_blocks_when_expected_value_cluster_or_resolution_risk_breaches_budget() -> None:
    blocked = decision(
        row=candidate(
            expected_value=d("0.010000"),
            liquidity_capacity=d("9000.000000"),
            team_allocated_notional=d("1000.000000"),
            team_allocation_cap=d("10000.000000"),
            cluster_allocated_notional=d("10000.000000"),
            cluster_allocation_cap=d("10000.000000"),
            resolution_risk=d("0.750000"),
        ),
    )

    assert blocked.nav_limit == d("5000.000000")
    assert blocked.expected_value_multiplier == d("0.100000")
    assert blocked.resolution_risk_multiplier == d("0.250000")
    assert blocked.cluster_capacity_headroom == ZERO
    assert blocked.binding_capacity == ZERO
    assert blocked.paper_notional == ZERO
    assert blocked.sizing_status == "blocked"
    assert blocked.risk_budget_reason_codes == (
        "screened_market",
        "strategy_sizing_risk_budget_v4_block",
        "expected_value_below_minimum",
        "liquidity_capacity_available",
        "team_allocation_capacity_available",
        "market_correlation_cluster_cap_exhausted",
        "resolution_risk_high",
    )


def test_watches_low_expected_value_or_elevated_resolution_without_blocking() -> None:
    watched = decision(
        row=candidate(
            expected_value=d("0.040000"),
            liquidity_capacity=d("900.000000"),
            team_allocated_notional=d("1000.000000"),
            team_allocation_cap=d("9000.000000"),
            cluster_allocated_notional=d("2000.000000"),
            cluster_allocation_cap=d("9000.000000"),
            resolution_risk=d("0.400000"),
        ),
    )

    assert watched.expected_value_multiplier == d("0.400000")
    assert watched.resolution_risk_multiplier == d("0.600000")
    assert watched.binding_capacity == d("900.000000")
    assert watched.paper_notional == d("216.000000")
    assert watched.sizing_status == "watch"
    assert watched.risk_budget_reason_codes == (
        "screened_market",
        "strategy_sizing_risk_budget_v4_watch",
        "expected_value_watch",
        "liquidity_capacity_limited",
        "team_allocation_capacity_available",
        "market_correlation_cluster_capacity_available",
        "resolution_risk_watch",
    )


def test_payload_uses_decimal_strings_redacts_sensitive_references_and_no_floats() -> None:
    module = api()
    result = decision(
        row=candidate(
            market_reference="secret-wallet-token-market",
            expected_value=d("0.080000"),
            resolution_risk=d("0.250000"),
        ),
    )

    payload = module.strategy_sizing_risk_budget_v4_payload(result)
    rendered = repr(payload).lower()
    assert payload["market_id"] == "market_alpha"
    assert payload["redacted_market_reference"].startswith("market_ref_")
    assert payload["paper_notional"] == "900.000000"
    assert payload["sizing_status"] == "pass"
    assert payload["risk_budget_reason_codes"] == list(result.risk_budget_reason_codes)
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert "secret" not in rendered
    assert "wallet" not in rendered
    assert "token" not in rendered
    assert_no_float_values(payload)


def test_validation_rejects_bad_types_precision_duplicates_and_flags() -> None:
    module = api()

    with pytest.raises(ValueError, match="config"):
        module.build_strategy_sizing_risk_budget_v4(candidate(), config=object())

    with pytest.raises(ValueError, match="row"):
        module.build_strategy_sizing_risk_budget_v4(object(), config=config())

    with pytest.raises(ValueError, match="expected_value must be a Decimal"):
        candidate(expected_value=0.12)

    with pytest.raises(ValueError, match="liquidity_capacity must be finite"):
        candidate(liquidity_capacity=Decimal("NaN"))

    with pytest.raises(ValueError, match="resolution_risk must be exactly Decimal"):
        candidate(resolution_risk=_DecimalSubclass("0.200000"))

    with pytest.raises(ValueError, match="resolution_risk must be a probability Decimal"):
        candidate(resolution_risk=d("1.000001"))

    with pytest.raises(ValueError, match="team_allocated_notional cannot exceed"):
        candidate(team_allocated_notional=d("5000.000001"))

    with pytest.raises(ValueError, match="cluster_allocated_notional cannot exceed"):
        candidate(cluster_allocated_notional=d("10000.000001"))

    with pytest.raises(ValueError, match="ordered"):
        candidate(reason_codes={"alpha_reason", "beta_reason"})

    with pytest.raises(ValueError, match="reducer-owned"):
        candidate(reason_codes=("strategy_sizing_risk_budget_v4_block",))

    with pytest.raises(ValueError, match="paper_only must be True"):
        module.StrategySizingRiskBudgetV4Config(paper_only=False)

    result = decision()
    with pytest.raises(FrozenInstanceError):
        result.sizing_status = "watch"  # type: ignore[misc]

    with pytest.raises(ValueError, match="readonly must be True"):
        replace(result, readonly=False)

    with pytest.raises(ValueError, match="status terminal"):
        replace(result, risk_budget_reason_codes=("screened_market",))


def test_decimal_fields_are_exact_decimal_instances() -> None:
    result = decision()

    for item in fields(result):
        if item.name in {
            "config_version",
            "market_id",
            "redacted_market_reference",
            "correlation_cluster_id",
            "sizing_status",
            "risk_budget_reason_codes",
            "paper_only",
            "report_only",
            "readonly",
        }:
            continue
        assert type(getattr(result, item.name)) is Decimal


def test_payload_requires_decision_type_and_hard_flags() -> None:
    module = api()
    result = decision()

    with pytest.raises(ValueError, match="decision must be"):
        module.strategy_sizing_risk_budget_v4_payload(object())

    with pytest.raises(ValueError, match="report_only must be True"):
        module.strategy_sizing_risk_budget_v4_payload(replace(result, report_only=False))


def test_module_scope_has_no_live_trading_persistence_network_or_sensitive_surfaces() -> None:
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    imports: list[str] = []
    forbidden_import_fragments = (
        "api",
        "auth",
        "broker",
        "client",
        "db",
        "http",
        "network",
        "psycopg",
        "request",
        "socket",
        "sql",
        "supabase",
        "urllib",
        "wallet",
    )
    forbidden_call_names = {
        "open",
        "read",
        "write",
        "connect",
        "execute",
        "fetch",
        "request",
        "submit",
        "cancel",
        "sign",
        "recommend",
    }
    forbidden_attr_fragments = (
        "account",
        "advice",
        "auth",
        "broker",
        "cancel",
        "client",
        "connect",
        "db",
        "execute",
        "fetch",
        "file",
        "network",
        "persist",
        "request",
        "sign",
        "submit",
        "trade",
        "wallet",
        "write",
    )
    forbidden_attr_names = {
        "open",
        "read",
        "read_text",
        "read_bytes",
        "write",
        "write_text",
        "write_bytes",
    }

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            assert node.level == 0
            imports.append(node.module or "")
        elif isinstance(node, ast.Call):
            callee_name = None
            if isinstance(node.func, ast.Name):
                callee_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                callee_name = node.func.attr
            assert callee_name not in forbidden_call_names
        elif isinstance(node, ast.Attribute):
            lowered = node.attr.lower()
            assert lowered not in forbidden_attr_names
            assert not any(fragment in lowered for fragment in forbidden_attr_fragments)

    assert imports
    for module_name in imports:
        assert not module_name.startswith("polymarket_alpha_lab.")
        lowered = module_name.lower()
        assert not any(fragment in lowered for fragment in forbidden_import_fragments)
