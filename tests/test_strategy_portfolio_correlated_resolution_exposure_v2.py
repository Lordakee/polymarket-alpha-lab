from __future__ import annotations

import ast
import importlib
import inspect
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 7, 15, 30, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.strategy_portfolio_correlated_resolution_exposure_v2",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": (
            module.DEFAULT_STRATEGY_PORTFOLIO_CORRELATED_RESOLUTION_EXPOSURE_V2_CONFIG_VERSION
        ),
        "cluster_watch_exposure_usdc": d("100.000000"),
        "cluster_block_exposure_usdc": d("150.000000"),
        "source_family_watch_exposure_usdc": d("120.000000"),
        "source_family_block_exposure_usdc": d("180.000000"),
    }
    values.update(overrides)
    return module.StrategyPortfolioCorrelatedResolutionExposureV2Config(**values)


def position(**overrides: object):
    module = api()
    values = {
        "position_id": "p-weather",
        "market_id": "m-hurricane-landfall",
        "event_slug": "hurricane-landfall-2026",
        "category": "weather",
        "cluster_id": "hurricane-season",
        "resolution_source_family": "weather-center",
        "notional_usdc": d("20.000000"),
        "max_loss_usdc": d("5.000000"),
    }
    values.update(overrides)
    return module.StrategyPortfolioCorrelatedResolutionExposureV2Position(**values)


def report(
    *positions: object,
    cfg: object | None = None,
    generated_at: datetime = GENERATED_AT,
):
    module = api()
    return module.build_strategy_portfolio_correlated_resolution_exposure_v2_report(
        positions,
        config=cfg or config(),
        generated_at=generated_at.astimezone(timezone(timedelta(hours=-4))),
    )


def assert_no_float_or_int_values(value: Any) -> None:
    if type(value) in (float, int):
        raise AssertionError(f"unsafe numeric JSON value: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_or_int_values(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_float_or_int_values(item)


def test_empty_input_returns_empty_report_only_zero_decimal_report() -> None:
    module = api()

    exposure_report = report()

    assert isinstance(
        exposure_report,
        module.StrategyPortfolioCorrelatedResolutionExposureV2Report,
    )
    assert is_dataclass(exposure_report)
    assert exposure_report.__dataclass_params__.frozen
    assert exposure_report.generated_at == GENERATED_AT
    assert exposure_report.generated_at.tzinfo is UTC
    assert exposure_report.config_version == (
        "strategy-portfolio-correlated-resolution-exposure-v2"
    )
    assert exposure_report.report_status == "empty"
    assert exposure_report.position_count == d("0.000000")
    assert exposure_report.cluster_count == d("0.000000")
    assert exposure_report.source_family_count == d("0.000000")
    assert exposure_report.pass_count == d("0.000000")
    assert exposure_report.watch_count == d("0.000000")
    assert exposure_report.block_count == d("0.000000")
    assert exposure_report.max_cluster_exposure_usdc == d("0.000000")
    assert exposure_report.max_source_family_exposure_usdc == d("0.000000")
    assert exposure_report.total_max_loss_usdc == d("0.000000")
    assert exposure_report.rows == ()
    assert exposure_report.reason_code_counts == ()
    assert len(exposure_report.derived_validation_digest) == 64
    assert exposure_report.paper_only is True
    assert exposure_report.report_only is True
    assert exposure_report.readonly is True

    payload = module.strategy_portfolio_correlated_resolution_exposure_v2_public_payload(
        exposure_report,
    )
    assert payload["report_status"] == "empty"
    assert payload["position_count"] == "0.000000"
    assert payload["rows"] == []
    assert payload["reason_code_counts"] == []
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_float_or_int_values(payload)
    json.dumps(payload, sort_keys=True)


def test_report_flags_shared_clusters_and_source_families_with_deterministic_rows() -> None:
    sec_alpha = position(
        position_id="p-sec-alpha",
        market_id="m-crypto-etf-approval",
        event_slug="crypto-etf-approval",
        category="crypto",
        cluster_id="crypto-etf",
        resolution_source_family="sec-filings",
        notional_usdc=d("110.000000"),
        max_loss_usdc=d("45.000000"),
    )
    sec_beta = position(
        position_id="p-sec-beta",
        market_id="m-court-ruling",
        event_slug="court-ruling",
        category="legal",
        cluster_id="court-ruling",
        resolution_source_family="sec-filings",
        notional_usdc=d("80.000000"),
        max_loss_usdc=d("35.000000"),
    )
    election_alpha = position(
        position_id="p-election-alpha",
        market_id="m-senate-control",
        event_slug="senate-control-2026",
        category="politics",
        cluster_id="election-cycle",
        resolution_source_family="state-board",
        notional_usdc=d("70.000000"),
        max_loss_usdc=d("50.000000"),
    )
    election_beta = position(
        position_id="p-election-beta",
        market_id="m-house-control",
        event_slug="house-control-2026",
        category="politics",
        cluster_id="election-cycle",
        resolution_source_family="polling-consortium",
        notional_usdc=d("60.000000"),
        max_loss_usdc=d("25.000000"),
    )
    weather = position()

    forward = report(
        weather,
        sec_beta,
        election_beta,
        sec_alpha,
        election_alpha,
    )
    reverse = report(
        election_alpha,
        sec_alpha,
        election_beta,
        sec_beta,
        weather,
    )

    assert forward == reverse
    assert forward.report_status == "block"
    assert forward.position_count == d("5.000000")
    assert forward.cluster_count == d("4.000000")
    assert forward.source_family_count == d("4.000000")
    assert forward.pass_count == d("1.000000")
    assert forward.watch_count == d("2.000000")
    assert forward.block_count == d("2.000000")
    assert forward.max_cluster_exposure_usdc == d("130.000000")
    assert forward.max_source_family_exposure_usdc == d("190.000000")
    assert forward.total_max_loss_usdc == d("160.000000")
    assert tuple(row.position_id for row in forward.rows) == (
        "p-sec-alpha",
        "p-sec-beta",
        "p-election-alpha",
        "p-election-beta",
        "p-weather",
    )
    assert tuple(row.status for row in forward.rows) == (
        "block",
        "block",
        "watch",
        "watch",
        "pass",
    )

    top_row = forward.rows[0]
    assert top_row.cluster_exposure_usdc == d("110.000000")
    assert top_row.source_family_exposure_usdc == d("190.000000")
    assert top_row.reason_codes == (
        "source_family_exposure_block",
        "cluster_exposure_watch",
        "shared_resolution_source_family",
    )
    assert forward.rows[2].cluster_exposure_usdc == d("130.000000")
    assert forward.rows[2].source_family_exposure_usdc == d("70.000000")
    assert forward.rows[2].reason_codes == (
        "cluster_exposure_watch",
        "shared_event_cluster",
    )
    assert forward.rows[-1].reason_codes == ("correlated_exposure_within_limits",)

    assert tuple((item.reason_code, item.count) for item in forward.reason_code_counts) == (
        ("source_family_exposure_block", d("2.000000")),
        ("cluster_exposure_watch", d("3.000000")),
        ("shared_resolution_source_family", d("2.000000")),
        ("shared_event_cluster", d("2.000000")),
        ("correlated_exposure_within_limits", d("1.000000")),
    )
    assert all(len(row.derived_validation_digest) == 64 for row in forward.rows)
    assert len(forward.derived_validation_digest) == 64


def test_public_payload_is_safe_decimal_only_and_digest_backed() -> None:
    module = api()
    exposure_report = report(
        position(
            position_id="p-sec-alpha",
            market_id="m-crypto-etf-approval",
            event_slug="crypto-etf-approval",
            category="crypto",
            cluster_id="crypto-etf",
            resolution_source_family="sec-filings",
            notional_usdc=d("110.000000"),
            max_loss_usdc=d("45.000000"),
        ),
        position(
            position_id="p-sec-beta",
            market_id="m-court-ruling",
            event_slug="court-ruling",
            category="legal",
            cluster_id="court-ruling",
            resolution_source_family="sec-filings",
            notional_usdc=d("80.000000"),
            max_loss_usdc=d("35.000000"),
        ),
    )

    payload = module.strategy_portfolio_correlated_resolution_exposure_v2_public_payload(
        exposure_report,
    )

    assert payload["generated_at"] == "2026-07-07T15:30:00+00:00"
    assert payload["report_status"] == "block"
    assert payload["position_count"] == "2.000000"
    assert payload["max_source_family_exposure_usdc"] == "190.000000"
    assert payload["total_max_loss_usdc"] == "80.000000"
    assert payload["rows"][0]["notional_usdc"] == "110.000000"
    assert payload["rows"][0]["source_family_exposure_usdc"] == "190.000000"
    assert payload["rows"][0]["paper_only"] is True
    assert payload["reason_code_counts"][0] == {
        "reason_code": "source_family_exposure_block",
        "count": "2.000000",
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    assert_no_float_or_int_values(payload)
    json.dumps(payload, sort_keys=True)
    with pytest.raises(ValueError, match="int"):
        module._json_ready({"unsafe_count": 1})


def test_frozen_dataclasses_validate_decimals_flags_uniqueness_and_digests() -> None:
    module = api()
    cfg = config()
    valid = position()
    exposure_report = report(valid)

    for instance in (
        cfg,
        valid,
        exposure_report.rows[0],
        exposure_report.reason_code_counts[0],
        exposure_report,
    ):
        assert is_dataclass(instance)
        assert instance.__dataclass_params__.frozen
        assert instance.paper_only is True
        assert instance.report_only is True
        assert instance.readonly is True
        with pytest.raises(FrozenInstanceError):
            instance.paper_only = False  # type: ignore[misc]
        for field in fields(instance):
            value = getattr(instance, field.name)
            if type(value) in (int, float):
                raise AssertionError(f"{field.name} was not Decimal-only")

    with pytest.raises(ValueError, match="notional_usdc must be a Decimal"):
        position(notional_usdc="1.000000")
    with pytest.raises(ValueError, match="notional_usdc must be a Decimal"):
        position(notional_usdc=_DecimalSubclass("1.000000"))
    with pytest.raises(ValueError, match="max_loss_usdc must be nonnegative"):
        position(max_loss_usdc=d("-0.000001"))
    with pytest.raises(ValueError, match="position_id must be a string"):
        replace(valid, position_id=_StringSubclass("subclass-position"))
    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(valid, paper_only=False)
    with pytest.raises(ValueError, match="cluster watch threshold must be <= block"):
        config(
            cluster_watch_exposure_usdc=d("151.000000"),
            cluster_block_exposure_usdc=d("150.000000"),
        )
    with pytest.raises(ValueError, match="position_id values must be unique"):
        report(valid, replace(valid, market_id="different-market"))
    with pytest.raises(ValueError, match="market_id values must be unique"):
        report(valid, replace(valid, position_id="different-position"))
    with pytest.raises(ValueError, match="config must be"):
        module.build_strategy_portfolio_correlated_resolution_exposure_v2_report(
            (valid,),
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="derived_validation_digest mismatch"):
        replace(exposure_report.rows[0], derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="derived_validation_digest mismatch"):
        replace(exposure_report, derived_validation_digest="0" * 64)


def test_module_has_no_live_trading_auth_wallet_network_or_db_surface() -> None:
    module = api()
    source = inspect.getsource(module)
    tree = ast.parse(source)
    imported_roots: set[str] = set()
    called_names: set[str] = set()
    unsafe_fragments = (
        "auth",
        "wallet",
        "order",
        "network",
        "database",
        "persist",
        "sign",
        "trade",
    )

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".")[0])
        elif isinstance(node, ast.Call):
            function = node.func
            if isinstance(function, ast.Name):
                called_names.add(function.id)
            elif isinstance(function, ast.Attribute):
                called_names.add(function.attr)

    assert imported_roots <= {
        "__future__",
        "dataclasses",
        "datetime",
        "decimal",
        "hashlib",
        "json",
        "typing",
    }
    assert not (called_names & {"open", "connect", "request", "post", "put"})
    for exported_name in module.__all__:
        assert not any(fragment in exported_name.lower() for fragment in unsafe_fragments)
    for dataclass_type_name in (
        "StrategyPortfolioCorrelatedResolutionExposureV2Config",
        "StrategyPortfolioCorrelatedResolutionExposureV2Position",
        "StrategyPortfolioCorrelatedResolutionExposureV2Row",
        "StrategyPortfolioCorrelatedResolutionExposureV2ReasonCodeCount",
        "StrategyPortfolioCorrelatedResolutionExposureV2Report",
    ):
        dataclass_type = getattr(module, dataclass_type_name)
        for field in fields(dataclass_type):
            assert not any(
                fragment in field.name.lower()
                for fragment in unsafe_fragments
            )
