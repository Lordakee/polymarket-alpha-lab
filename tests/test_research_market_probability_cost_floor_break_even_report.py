from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime
from decimal import Decimal
import json

import pytest

import polymarket_alpha_lab.research_market_probability_cost_floor_break_even_report as api
from polymarket_alpha_lab.research_market_probability_cost_floor_break_even_report import (
    ResearchMarketProbabilityCostFloorBreakEvenConfig,
    ResearchMarketProbabilityCostFloorBreakEvenInput,
    ResearchMarketProbabilityCostFloorBreakEvenReasonCodeCount,
    ResearchMarketProbabilityCostFloorBreakEvenReport,
    ResearchMarketProbabilityCostFloorBreakEvenRow,
    build_research_market_probability_cost_floor_break_even_report,
)


NOW = datetime(2026, 1, 1, tzinfo=UTC)


def d(value: str) -> Decimal:
    return Decimal(value)


def case(
    *,
    market_probability: Decimal = d("0.450000"),
    research_probability_floor: Decimal = d("0.500000"),
    fee_probability_cost: Decimal = d("0.005000"),
    slippage_probability_cost: Decimal = d("0.005000"),
    impact_probability_cost: Decimal = d("0.000000"),
) -> ResearchMarketProbabilityCostFloorBreakEvenInput:
    return ResearchMarketProbabilityCostFloorBreakEvenInput(
        market_probability=market_probability,
        research_probability_floor=research_probability_floor,
        fee_probability_cost=fee_probability_cost,
        slippage_probability_cost=slippage_probability_cost,
        impact_probability_cost=impact_probability_cost,
    )


def report(
    *rows: ResearchMarketProbabilityCostFloorBreakEvenInput,
    generated_at: datetime = NOW,
    config: ResearchMarketProbabilityCostFloorBreakEvenConfig | None = None,
) -> ResearchMarketProbabilityCostFloorBreakEvenReport:
    return build_research_market_probability_cost_floor_break_even_report(
        rows,
        generated_at=generated_at,
        config=config,
    )


def test_rows_compute_break_even_statuses_and_sorted_rollups() -> None:
    result = report(
        case(),
        case(
            market_probability=d("0.450000"),
            research_probability_floor=d("0.460000"),
            fee_probability_cost=d("0.005000"),
        ),
        case(
            market_probability=d("0.480000"),
            research_probability_floor=d("0.470000"),
            fee_probability_cost=d("0.005000"),
        ),
    )

    assert tuple(row.status for row in result.rows) == ("block", "watch", "pass")

    blocked, watched, passed = result.rows
    assert blocked.total_probability_cost == d("0.010000")
    assert blocked.break_even_probability == d("0.490000")
    assert blocked.break_even_margin == d("-0.020000")
    assert blocked.reason_codes == ("probability_floor_below_break_even",)

    assert watched.total_probability_cost == d("0.010000")
    assert watched.break_even_probability == d("0.460000")
    assert watched.break_even_margin == d("0.000000")
    assert watched.reason_codes == ("thin_probability_margin",)

    assert passed.total_probability_cost == d("0.010000")
    assert passed.break_even_probability == d("0.460000")
    assert passed.break_even_margin == d("0.040000")
    assert passed.reason_codes == ("probability_cost_floor_break_even_pass",)

    assert result.report_status == "block"
    assert result.case_count == d("3.000000")
    assert result.pass_count == d("1.000000")
    assert result.watch_count == d("1.000000")
    assert result.block_count == d("1.000000")
    assert result.below_break_even_count == d("1.000000")
    assert result.impossible_break_even_count == d("0.000000")
    assert result.min_break_even_margin == d("-0.020000")
    assert result.max_total_probability_cost == d("0.010000")
    assert result.reason_code_counts == (
        ResearchMarketProbabilityCostFloorBreakEvenReasonCodeCount(
            "probability_floor_below_break_even",
            d("1.000000"),
        ),
        ResearchMarketProbabilityCostFloorBreakEvenReasonCodeCount(
            "thin_probability_margin",
            d("1.000000"),
        ),
        ResearchMarketProbabilityCostFloorBreakEvenReasonCodeCount(
            "probability_cost_floor_break_even_pass",
            d("1.000000"),
        ),
    )


def test_empty_input_returns_pass_status_and_zero_decimal_rollups() -> None:
    result = report()

    assert result.report_status == "pass"
    assert result.rows == ()
    assert result.reason_code_counts == ()
    assert result.case_count == d("0.000000")
    assert result.pass_count == d("0.000000")
    assert result.watch_count == d("0.000000")
    assert result.block_count == d("0.000000")
    assert result.below_break_even_count == d("0.000000")
    assert result.impossible_break_even_count == d("0.000000")
    assert result.min_break_even_margin == d("0.000000")
    assert result.max_total_probability_cost == d("0.000000")


def test_payload_is_deterministic_safe_json_with_decimal_strings_and_digest() -> None:
    first = report(case())
    second = report(case())

    assert first.payload == second.payload
    payload = first.payload
    json.dumps(payload, sort_keys=True)
    assert payload["generated_at"] == "2026-01-01T00:00:00+00:00"
    assert payload["case_count"] == "1.000000"
    assert payload["rows"][0]["market_probability"] == "0.450000"
    assert payload["rows"][0]["break_even_probability"] == "0.460000"
    assert payload["rows"][0]["break_even_margin"] == "0.040000"
    assert payload["reason_code_counts"][0]["count"] == "1.000000"
    assert payload["derived_validation_digest"] == first.derived_validation_digest
    assert len(first.derived_validation_digest) == 64
    _assert_no_decimal_objects(payload)
    _assert_no_non_decimal_public_numbers(first)
    _assert_no_forbidden_public_leakage(payload)


def test_frozen_dataclasses_decimal_only_and_digest_tamper_checks() -> None:
    result = report(case())

    for value in (
        ResearchMarketProbabilityCostFloorBreakEvenConfig(),
        case(),
        result.rows[0],
        result.reason_code_counts[0],
        result,
    ):
        assert hasattr(value, "__dataclass_fields__")
        with pytest.raises(FrozenInstanceError):
            value.paper_only = False  # type: ignore[misc]

    with pytest.raises(ValueError, match="market_probability"):
        case(market_probability=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="research_probability_floor"):
        case(research_probability_floor=d("1.000001"))
    with pytest.raises(ValueError, match="fee_probability_cost"):
        case(fee_probability_cost=d("-0.000001"))
    with pytest.raises(ValueError, match="total_probability_cost"):
        case(
            fee_probability_cost=d("0.400000"),
            slippage_probability_cost=d("0.400000"),
            impact_probability_cost=d("0.300001"),
        )
    with pytest.raises(ValueError, match="paper_only"):
        ResearchMarketProbabilityCostFloorBreakEvenConfig(paper_only=False)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(result, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="rows"):
        replace(result, rows=())


def test_row_constructor_rejects_inconsistent_watch_reason_codes() -> None:
    with pytest.raises(ValueError, match="reason_codes"):
        ResearchMarketProbabilityCostFloorBreakEvenRow(
            market_probability=d("0.500000"),
            research_probability_floor=d("0.490000"),
            fee_probability_cost=d("0.000000"),
            slippage_probability_cost=d("0.000000"),
            impact_probability_cost=d("0.000000"),
            total_probability_cost=d("0.000000"),
            break_even_probability=d("0.500000"),
            break_even_margin=d("-0.010000"),
            status="watch",
            reason_codes=("thin_probability_margin",),
        )


def test_impossible_break_even_blocks_without_identifier_or_surface_leakage() -> None:
    result = report(
        case(
            market_probability=d("0.990000"),
            research_probability_floor=d("1.000000"),
            fee_probability_cost=d("0.020000"),
            slippage_probability_cost=d("0.000000"),
        ),
    )

    assert result.report_status == "block"
    assert result.impossible_break_even_count == d("1.000000")
    assert result.rows[0].break_even_probability == d("1.010000")
    assert result.rows[0].reason_codes == (
        "break_even_probability_above_one",
        "probability_floor_below_break_even",
    )
    _assert_no_forbidden_public_leakage(result.payload)


def test_static_module_surface_is_report_only_readonly_and_safe() -> None:
    unsafe_terms = (
        "candidate_id",
        "raw_candidate",
        "market_id",
        "market_slug",
        "question",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
        "token",
        "wallet",
        "order",
        "trade",
        "sizing",
        "recommendation",
        "auth",
        "network",
        "live",
    )
    for public_name in api.__all__:
        lowered = public_name.lower()
        assert not any(term in lowered for term in unsafe_terms)

    for cls in (
        ResearchMarketProbabilityCostFloorBreakEvenConfig,
        ResearchMarketProbabilityCostFloorBreakEvenInput,
        ResearchMarketProbabilityCostFloorBreakEvenRow,
        ResearchMarketProbabilityCostFloorBreakEvenReasonCodeCount,
        ResearchMarketProbabilityCostFloorBreakEvenReport,
    ):
        for field in fields(cls):
            lowered = field.name.lower()
            assert not any(term in lowered for term in unsafe_terms)

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

    assert set(api.STATUSES) == {"pass", "watch", "block"}
    with pytest.raises(ValueError, match="unsafe public"):
        ResearchMarketProbabilityCostFloorBreakEvenConfig(
            config_version="wallet_config",
        )


def _assert_no_decimal_objects(value: object) -> None:
    if isinstance(value, Decimal):
        raise AssertionError("payload contains a Decimal object")
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_decimal_objects(item)
    if isinstance(value, list):
        for item in value:
            _assert_no_decimal_objects(item)


def _assert_no_non_decimal_public_numbers(value: object) -> None:
    if isinstance(value, Decimal):
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


def _assert_no_forbidden_public_leakage(value: object) -> None:
    forbidden_fragments = (
        "candidate_id",
        "raw_candidate",
        "market_id",
        "market_slug",
        "question",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
        "token",
        "wallet",
        "order",
        "trade",
        "sizing",
        "recommendation",
        "auth",
        "network",
        "live",
        "://",
    )
    if isinstance(value, dict):
        for key, item in value.items():
            lowered_key = key.lower()
            assert not any(term in lowered_key for term in forbidden_fragments)
            _assert_no_forbidden_public_leakage(item)
        return
    if isinstance(value, list):
        for item in value:
            _assert_no_forbidden_public_leakage(item)
        return
    if isinstance(value, str):
        lowered_value = value.lower()
        assert not any(term in lowered_value for term in forbidden_fragments)
