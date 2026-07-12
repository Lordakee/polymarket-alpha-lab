from __future__ import annotations

import ast
import importlib
import inspect
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal

import pytest


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.portfolio_probability_event_exposure_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def exposure(
    market_id: str,
    domain: str,
    team: str,
    yes_probability_exposure: str,
    no_probability_exposure: str,
    settlement_window_seconds: str,
    liquidity_depth_usdc: str,
    correlation_bucket: str,
):
    module = api()
    return module.PortfolioProbabilityEventExposureInput(
        market_id=market_id,
        domain=domain,
        team=team,
        yes_probability_exposure=d(yes_probability_exposure),
        no_probability_exposure=d(no_probability_exposure),
        settlement_window_seconds=d(settlement_window_seconds),
        liquidity_depth_usdc=d(liquidity_depth_usdc),
        correlation_bucket=correlation_bucket,
    )


def report(*rows):
    module = api()
    return module.build_portfolio_probability_event_exposure_report(
        rows,
        config=module.PortfolioProbabilityEventExposureConfig(),
    )


def assert_public_numeric_fields_are_decimal(instance: object) -> None:
    for field in fields(instance):
        value = getattr(instance, field.name)
        if type(value) is bool:
            continue
        assert type(value) is not float
        assert type(value) is not int
        if isinstance(value, tuple):
            for item in value:
                if is_dataclass(item):
                    assert_public_numeric_fields_are_decimal(item)


def test_report_reduces_probability_event_exposure_by_domain_and_correlation():
    result = report(
        exposure(
            "market-alpha",
            "macro",
            "rates-team",
            "120.500000",
            "20.000000",
            "7200",
            "250.000000",
            "fed-cycle",
        ),
        exposure(
            "market-beta",
            "macro",
            "rates-team",
            "30.000000",
            "90.000000",
            "1800",
            "200.000000",
            "fed-cycle",
        ),
        exposure(
            "market-gamma",
            "crypto",
            "btc-team",
            "10.000000",
            "15.000000",
            "300",
            "5.000000",
            "btc-spot",
        ),
    )

    assert is_dataclass(result)
    assert result.config_version == "portfolio-probability-event-exposure-report-v0"
    assert result.market_count == d("3")
    assert result.total_yes_probability_exposure == d("160.500000")
    assert result.total_no_probability_exposure == d("125.000000")
    assert result.net_probability_exposure == d("35.500000")
    assert result.max_domain_concentration == d("0.912434")
    assert result.max_correlation_concentration == d("0.912434")
    assert result.blocker_count == d("2")
    assert result.attention_count == d("1")
    assert result.clear_count == d("0")
    assert result.report_status == "block"
    assert result.reason_codes == (
        "domain_concentration_block",
        "correlation_concentration_block",
        "low_liquidity_depth",
        "settlement_window_block",
        "settlement_window_watch",
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True
    assert_public_numeric_fields_are_decimal(result)

    assert tuple(row.market_id for row in result.rows) == (
        "market-alpha",
        "market-beta",
        "market-gamma",
    )
    blocked, concentration_blocked, liquidity_watch = result.rows
    assert blocked.net_probability_exposure == d("100.500000")
    assert blocked.absolute_net_probability_exposure == d("100.500000")
    assert blocked.domain_concentration == d("0.912434")
    assert blocked.correlation_concentration == d("0.912434")
    assert blocked.settlement_window_risk_band == "block"
    assert blocked.report_status == "block"
    assert blocked.reason_codes == (
        "domain_concentration_block",
        "correlation_concentration_block",
        "settlement_window_block",
    )

    assert concentration_blocked.net_probability_exposure == d("-60.000000")
    assert concentration_blocked.domain_concentration == d("0.912434")
    assert concentration_blocked.correlation_concentration == d("0.912434")
    assert concentration_blocked.settlement_window_risk_band == "watch"
    assert concentration_blocked.report_status == "block"
    assert concentration_blocked.reason_codes == (
        "domain_concentration_block",
        "correlation_concentration_block",
        "settlement_window_watch",
    )

    assert liquidity_watch.net_probability_exposure == d("-5.000000")
    assert liquidity_watch.settlement_window_risk_band == "clear"
    assert liquidity_watch.report_status == "watch"
    assert liquidity_watch.reason_codes == ("low_liquidity_depth",)


def test_empty_report_is_readonly_paper_only_and_decimal_zeroed():
    result = report()

    assert result.market_count == d("0")
    assert result.total_yes_probability_exposure == d("0.000000")
    assert result.total_no_probability_exposure == d("0.000000")
    assert result.net_probability_exposure == d("0.000000")
    assert result.max_domain_concentration == d("0.000000")
    assert result.max_correlation_concentration == d("0.000000")
    assert result.blocker_count == d("0")
    assert result.attention_count == d("0")
    assert result.clear_count == d("0")
    assert result.report_status == "clear"
    assert result.reason_codes == ("probability_event_exposure_clear",)
    assert result.rows == ()
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True
    assert_public_numeric_fields_are_decimal(result)


def test_direct_constructors_revalidate_consistency_decimal_boundary_and_flags():
    module = api()
    result = report(
        exposure(
            "market-alpha",
            "macro",
            "rates-team",
            "120.500000",
            "20.000000",
            "7200",
            "250.000000",
            "fed-cycle",
        ),
    )

    rebuilt_row = module.PortfolioProbabilityEventExposureRow(
        **{field.name: getattr(result.rows[0], field.name) for field in fields(result.rows[0])},
    )
    assert rebuilt_row == result.rows[0]

    with pytest.raises(ValueError, match="yes_probability_exposure"):
        exposure(
            "market-alpha",
            "macro",
            "rates-team",
            "1.000000",
            "0.000000",
            "60",
            "1.000000",
            "bucket",
        ).__class__(
            market_id="market-alpha",
            domain="macro",
            team="rates-team",
            yes_probability_exposure=1,
            no_probability_exposure=d("0.000000"),
            settlement_window_seconds=d("60"),
            liquidity_depth_usdc=d("1.000000"),
            correlation_bucket="bucket",
        )
    with pytest.raises(ValueError, match="rows"):
        module.build_portfolio_probability_event_exposure_report(
            (object(),),
            config=module.PortfolioProbabilityEventExposureConfig(),
        )
    with pytest.raises(ValueError, match="config"):
        module.build_portfolio_probability_event_exposure_report((), config=object())
    with pytest.raises(ValueError, match="paper_only"):
        replace(result, paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(result.rows[0], readonly=False)
    with pytest.raises(FrozenInstanceError):
        result.report_status = "block"


def test_report_module_stays_leaf_readonly_report_only_paper_only():
    import polymarket_alpha_lab.portfolio_probability_event_exposure_report as module

    source = inspect.getsource(module)
    tree = ast.parse(source)
    project_imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            imported = node.module or ""
            if imported.startswith("polymarket_alpha_lab."):
                project_imports.add(imported)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith("polymarket_alpha_lab."):
                    project_imports.add(alias.name)

    assert project_imports == set()
    lowered = source.lower()
    for forbidden in (
        ".read(",
        ".write(",
        "open(",
        "path",
        "logging",
        "logger",
        "client",
        "requests",
        "urllib",
        "http",
        "network",
        "auth",
        "wallet",
        "private_key",
        "database",
        "postgres",
        "supabase",
        "order",
        "trade",
    ):
        assert forbidden not in lowered
