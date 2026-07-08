from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime, timezone, timedelta
from decimal import Decimal
import importlib
import json

import pytest


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


def module():
    return importlib.import_module(
        "polymarket_alpha_lab.research_market_cost_curve_sufficiency_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def cost_curve(
    *,
    research_case_key: str = "abstract_case_pass",
    observed_at: datetime = datetime(2026, 7, 8, 11, 45, tzinfo=UTC),
    spread_pct: Decimal = d("0.020000"),
    taker_fee_pct: Decimal = d("0.010000"),
    depth_slope_pct_per_100: Decimal = d("0.040000"),
    deposit_friction_pct: Decimal = d("0.005000"),
    settlement_friction_pct: Decimal = d("0.005000"),
    gas_friction_pct: Decimal = d("0.005000"),
    top_liquidity_share: Decimal = d("0.350000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
):
    api = module()
    return api.MarketCostCurveSufficiencyInput(
        research_case_key=research_case_key,
        observed_at=observed_at,
        spread_pct=spread_pct,
        taker_fee_pct=taker_fee_pct,
        depth_slope_pct_per_100=depth_slope_pct_per_100,
        deposit_friction_pct=deposit_friction_pct,
        settlement_friction_pct=settlement_friction_pct,
        gas_friction_pct=gas_friction_pct,
        top_liquidity_share=top_liquidity_share,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(*rows: object, config: object | None = None):
    api = module()
    return api.build_market_cost_curve_sufficiency_report(
        rows,
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
        config=(
            config
            if config is not None
            else api.MarketCostCurveSufficiencyConfig()
        ),
    )


def test_empty_input_is_report_only_block_with_zero_digest_surface() -> None:
    api = module()

    built = report()

    assert isinstance(built, api.MarketCostCurveSufficiencyReport)
    assert built.generated_at == GENERATED_AT
    assert built.generated_at.tzinfo is UTC
    assert built.config_version == "research-market-cost-curve-sufficiency-report-v1"
    assert built.report_status == "block"
    assert built.input_count == d("0.000000")
    assert built.pass_count == d("0.000000")
    assert built.watch_count == d("0.000000")
    assert built.block_count == d("0.000000")
    assert built.average_sufficiency_score == d("0.000000")
    assert built.rows == ()
    assert built.reason_codes == ("cost_curve_sufficiency_empty",)
    assert built.paper_only is True
    assert built.report_only is True
    assert built.readonly is True
    assert len(built.derived_validation_digest) == 64


def test_pass_watch_and_block_statuses_cover_required_cost_curve_inputs() -> None:
    built = report(
        cost_curve(research_case_key="case_pass"),
        cost_curve(
            research_case_key="case_watch",
            spread_pct=d("0.070000"),
            taker_fee_pct=d("0.035000"),
            depth_slope_pct_per_100=d("0.090000"),
            deposit_friction_pct=d("0.018000"),
            settlement_friction_pct=d("0.017000"),
            gas_friction_pct=d("0.016000"),
            top_liquidity_share=d("0.700000"),
        ),
        cost_curve(
            research_case_key="case_block",
            spread_pct=d("0.120000"),
            taker_fee_pct=d("0.070000"),
            depth_slope_pct_per_100=d("0.180000"),
            deposit_friction_pct=d("0.035000"),
            settlement_friction_pct=d("0.040000"),
            gas_friction_pct=d("0.032000"),
            top_liquidity_share=d("0.910000"),
        ),
    )

    rows = {row.research_case_key: row for row in built.rows}
    assert built.report_status == "block"
    assert built.input_count == d("3.000000")
    assert built.pass_count == d("1.000000")
    assert built.watch_count == d("1.000000")
    assert built.block_count == d("1.000000")
    assert built.max_total_friction_pct == d("0.297000")
    assert built.max_top_liquidity_share == d("0.910000")

    assert rows["case_pass"].status == "pass"
    assert rows["case_pass"].total_friction_pct == d("0.045000")
    assert rows["case_pass"].reason_codes == ("cost_curve_sufficiency_pass",)
    assert rows["case_watch"].status == "watch"
    assert rows["case_watch"].sufficiency_score == d("0.650000")
    assert rows["case_watch"].reason_codes == (
        "spread_watch",
        "taker_fee_watch",
        "depth_slope_watch",
        "deposit_friction_watch",
        "settlement_friction_watch",
        "gas_friction_watch",
        "liquidity_concentration_watch",
    )
    assert rows["case_block"].status == "block"
    assert rows["case_block"].sufficiency_score == d("0.000000")
    assert rows["case_block"].reason_codes == (
        "spread_block",
        "taker_fee_block",
        "depth_slope_block",
        "deposit_friction_block",
        "settlement_friction_block",
        "gas_friction_block",
        "liquidity_concentration_block",
    )


def test_payload_digest_are_deterministic_and_omit_raw_market_source_ids() -> None:
    api = module()
    first = report(
        cost_curve(research_case_key="z_case", spread_pct=d("0.030000")),
        cost_curve(research_case_key="a_case", spread_pct=d("0.025000")),
    )
    second = report(
        cost_curve(research_case_key="a_case", spread_pct=d("0.025000")),
        cost_curve(research_case_key="z_case", spread_pct=d("0.030000")),
    )

    payload = api.market_cost_curve_sufficiency_report_payload(first)

    assert first == second
    assert payload == api.market_cost_curve_sufficiency_report_payload(second)
    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["input_count"] == "2.000000"
    assert payload["rows"][0]["research_case_key"] == "a_case"
    assert payload["rows"][0]["spread_pct"] == "0.025000"
    assert payload["derived_validation_digest"] == first.derived_validation_digest
    json.dumps(payload, sort_keys=True)
    _assert_no_runtime_objects(payload)
    _assert_no_raw_or_execution_terms(payload)


def test_dataclasses_are_frozen_decimal_only_and_reject_tampering() -> None:
    api = module()
    built = report(cost_curve())

    for record in (
        api.MarketCostCurveSufficiencyConfig(),
        cost_curve(),
        built.rows[0],
        built.reason_code_counts[0],
        built,
    ):
        assert hasattr(record, "__dataclass_fields__")
        assert record.__dataclass_params__.frozen
        _assert_no_non_decimal_public_numbers(record)

    with pytest.raises(FrozenInstanceError):
        built.report_status = "watch"  # type: ignore[misc]

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(built, derived_validation_digest="0" * 64)

    with pytest.raises(ValueError, match="sufficiency_score"):
        replace(built.rows[0], sufficiency_score=d("0.100000"))

    with pytest.raises(ValueError, match="Decimal"):
        cost_curve(spread_pct=0.02)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        cost_curve(observed_at=datetime(2026, 7, 8, 11, 45))


def test_hard_flags_status_contract_and_safe_public_surface_are_enforced() -> None:
    api = module()

    assert api.STATUSES == ("pass", "watch", "block")

    for cls in (
        api.MarketCostCurveSufficiencyConfig,
        api.MarketCostCurveSufficiencyInput,
        api.MarketCostCurveSufficiencyRow,
        api.MarketCostCurveSufficiencyReasonCodeCount,
        api.MarketCostCurveSufficiencyReport,
    ):
        with pytest.raises(TypeError, match="subclassing"):
            type("BadSubclass", (cls,), {})
        for field in fields(cls):
            lowered = field.name.lower()
            assert not any(
                term in lowered
                for term in (
                    "market_id",
                    "market_slug",
                    "source_id",
                    "token_id",
                    "condition_id",
                    "wallet",
                    "auth",
                    "order",
                    "trade",
                    "private",
                )
            )

    with pytest.raises(ValueError, match="paper_only"):
        api.MarketCostCurveSufficiencyConfig(paper_only=False)

    with pytest.raises(ValueError, match="readonly"):
        cost_curve(readonly=False)  # type: ignore[call-arg]

    with pytest.raises(ValueError, match="status"):
        replace(report(cost_curve()).rows[0], status="blocked")

    with pytest.raises(ValueError, match="duplicate research_case_key"):
        report(cost_curve(research_case_key="dupe"), cost_curve(research_case_key="dupe"))

    for public_name in api.__all__:
        lowered = public_name.lower()
        assert not any(
            term in lowered
            for term in (
                "wallet",
                "auth",
                "order",
                "trade",
                "private",
                "execution",
                "market_id",
                "market_slug",
                "source_id",
                "token_id",
                "condition_id",
            )
        )

    for forbidden_name in (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "sqlite3",
        "sqlalchemy",
        "psycopg",
        "web3",
        "ccxt",
    ):
        assert not hasattr(api, forbidden_name)


def _assert_no_runtime_objects(value: object) -> None:
    if isinstance(value, (Decimal, datetime)):
        raise AssertionError(f"payload contains runtime object: {value!r}")
    if isinstance(value, float):
        raise AssertionError(f"payload contains float: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_runtime_objects(item)
    if isinstance(value, list):
        for item in value:
            _assert_no_runtime_objects(item)


def _assert_no_non_decimal_public_numbers(value: object) -> None:
    if isinstance(value, Decimal):
        assert type(value) is Decimal
        return
    if type(value) is bool or value is None or isinstance(value, (str, datetime)):
        return
    if type(value) is int or isinstance(value, float):
        raise AssertionError(f"public numeric value is not Decimal: {value!r}")
    if isinstance(value, tuple):
        for item in value:
            _assert_no_non_decimal_public_numbers(item)
        return
    if hasattr(value, "__dataclass_fields__"):
        for field in fields(value):
            _assert_no_non_decimal_public_numbers(getattr(value, field.name))


def _assert_no_raw_or_execution_terms(value: object) -> None:
    unsafe_terms = (
        "market_id",
        "market_slug",
        "source_id",
        "token_id",
        "condition_id",
        "wallet",
        "auth",
        "order",
        "trade",
        "private",
        "secret",
        "execution",
        "live",
    )
    if isinstance(value, dict):
        for key, item in value.items():
            lowered = key.lower()
            assert not any(term in lowered for term in unsafe_terms)
            _assert_no_raw_or_execution_terms(item)
    elif isinstance(value, list):
        for item in value:
            _assert_no_raw_or_execution_terms(item)
    elif isinstance(value, str):
        lowered = value.lower()
        assert not any(term in lowered for term in unsafe_terms)
