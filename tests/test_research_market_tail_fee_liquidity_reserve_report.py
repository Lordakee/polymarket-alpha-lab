from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime
from decimal import Decimal
from importlib import import_module
import json
from types import ModuleType
from typing import Any

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab."
    "research_market_tail_fee_liquidity_reserve_report"
)
GENERATED_AT = datetime(2026, 7, 9, 20, 0, tzinfo=UTC)
OBSERVED_AT = datetime(2026, 7, 9, 19, 45, tzinfo=UTC)


class DecimalSubclass(Decimal):
    pass


class DateTimeSubclass(datetime):
    pass


def api() -> ModuleType:
    try:
        return import_module(MODULE_NAME)
    except ModuleNotFoundError as exc:
        if exc.name == MODULE_NAME:
            pytest.fail(f"{MODULE_NAME} must exist")
        raise


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> object:
    values: dict[str, object] = {
        "watch_required_reserve_rate": d("0.050000"),
        "block_required_reserve_rate": d("0.120000"),
        "watch_min_reserve_coverage_ratio": d("1.500000"),
        "block_min_reserve_coverage_ratio": d("1.000000"),
    }
    values.update(overrides)
    return api().ResearchMarketTailFeeLiquidityReserveConfig(**values)


def sample(
    private_signal_reference: str,
    *,
    observed_at: datetime = OBSERVED_AT,
    tail_probability: Decimal = d("0.100000"),
    tail_loss_rate: Decimal = d("0.100000"),
    taker_fee_rate: Decimal = d("0.005000"),
    liquidity_shortfall_rate: Decimal = d("0.002000"),
    liquidity_haircut_rate: Decimal = d("0.500000"),
    available_reserve_rate: Decimal = d("0.050000"),
) -> object:
    return api().ResearchMarketTailFeeLiquidityReserveInput(
        private_signal_reference=private_signal_reference,
        observed_at=observed_at,
        tail_probability=tail_probability,
        tail_loss_rate=tail_loss_rate,
        taker_fee_rate=taker_fee_rate,
        liquidity_shortfall_rate=liquidity_shortfall_rate,
        liquidity_haircut_rate=liquidity_haircut_rate,
        available_reserve_rate=available_reserve_rate,
    )


def build_report(*inputs: object, cfg: object | None = None) -> object:
    module = api()
    return module.build_research_market_tail_fee_liquidity_reserve_report(
        inputs,
        config=cfg or config(),
        generated_at=GENERATED_AT,
    )


def test_builds_ranked_pass_watch_block_rows_with_decimal_only_outputs() -> None:
    report = build_report(
        sample("pass-row"),
        sample(
            "watch-row",
            tail_probability=d("0.200000"),
            tail_loss_rate=d("0.200000"),
            taker_fee_rate=d("0.010000"),
            liquidity_shortfall_rate=d("0.000000"),
            liquidity_haircut_rate=d("0.000000"),
            available_reserve_rate=d("0.100000"),
        ),
        sample(
            "block-row",
            tail_probability=d("0.400000"),
            tail_loss_rate=d("0.250000"),
            taker_fee_rate=d("0.020000"),
            liquidity_shortfall_rate=d("0.020000"),
            liquidity_haircut_rate=d("0.500000"),
            available_reserve_rate=d("0.090000"),
        ),
    )

    assert type(report) is api().ResearchMarketTailFeeLiquidityReserveReport
    assert report.generated_at == GENERATED_AT
    assert report.input_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.average_required_reserve_rate == d("0.072667")
    assert report.max_required_reserve_rate == d("0.150000")
    assert report.min_reserve_coverage_ratio == d("0.600000")
    assert report.status == "block"
    assert tuple(row.status for row in report.rows) == ("block", "watch", "pass")
    assert tuple(row.rank for row in report.rows) == (
        d("1.000000"),
        d("2.000000"),
        d("3.000000"),
    )

    block_row, watch_row, pass_row = report.rows
    assert block_row.tail_loss_component_rate == d("0.100000")
    assert block_row.fee_reserve_rate == d("0.020000")
    assert block_row.liquidity_reserve_rate == d("0.030000")
    assert block_row.required_reserve_rate == d("0.150000")
    assert block_row.reserve_coverage_ratio == d("0.600000")
    assert block_row.reason_codes == (
        "tail_fee_liquidity_reserve_block",
        "required_reserve_rate_block",
        "reserve_coverage_ratio_block",
        "tail_loss_component_applied",
        "fee_reserve_applied",
        "liquidity_reserve_applied",
    )
    assert watch_row.required_reserve_rate == d("0.050000")
    assert watch_row.reserve_coverage_ratio == d("2.000000")
    assert watch_row.reason_codes == (
        "tail_fee_liquidity_reserve_watch",
        "required_reserve_rate_watch",
        "tail_loss_component_applied",
        "fee_reserve_applied",
    )
    assert pass_row.required_reserve_rate == d("0.018000")
    assert pass_row.reserve_coverage_ratio == d("2.777778")
    assert pass_row.reason_codes == (
        "tail_fee_liquidity_reserve_pass",
        "tail_loss_component_applied",
        "fee_reserve_applied",
        "liquidity_reserve_applied",
    )
    assert all(row.paper_only and row.report_only and row.readonly for row in report.rows)


def test_public_payload_is_deterministic_sha256_bound_and_leak_safe() -> None:
    module = api()
    raw_private_reference = (
        "raw-candidate-alpha market_slug=hidden-market question=Will this settle? "
        "source_url=https://example.test/source token=secret"
    )
    report = build_report(sample(raw_private_reference))

    first_payload = module.research_market_tail_fee_liquidity_reserve_report_payload(report)
    second_payload = module.research_market_tail_fee_liquidity_reserve_report_payload(
        build_report(sample(raw_private_reference)),
    )
    encoded = json.dumps(first_payload, sort_keys=True)

    assert first_payload == second_payload
    assert first_payload["derived_validation_digest"] == report.derived_validation_digest
    assert len(first_payload["derived_validation_digest"]) == 64
    assert len(first_payload["rows"][0]["signal_digest"]) == 64
    assert first_payload["rows"][0]["required_reserve_rate"] == "0.018000"
    assert not any(isinstance(value, float) for value in _walk_payload_values(first_payload))
    assert raw_private_reference not in encoded
    assert "raw-candidate-alpha" not in encoded
    assert "hidden-market" not in encoded
    assert "Will this settle" not in encoded
    assert "https://example.test/source" not in encoded
    assert "secret" not in encoded
    assert module.validate_research_market_tail_fee_liquidity_reserve_public_payload(
        dict(first_payload),
    )

    with pytest.raises(TypeError, match="payload is immutable"):
        first_payload["status"] = "pass"
    with pytest.raises(TypeError, match="payload is immutable"):
        first_payload["rows"].append({})  # type: ignore[attr-defined]

    tampered = dict(first_payload)
    tampered["status"] = "watch"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_market_tail_fee_liquidity_reserve_report_payload(tampered)
    assert not module.validate_research_market_tail_fee_liquidity_reserve_public_payload(
        tampered,
    )

    unsafe_payload = dict(first_payload)
    unsafe_payload["raw_candidate_id"] = "candidate-alpha"
    with pytest.raises(ValueError, match="unsafe public field"):
        module.research_market_tail_fee_liquidity_reserve_report_payload(unsafe_payload)

    unsafe_nested = dict(first_payload)
    unsafe_nested["rows"] = [dict(first_payload["rows"][0])]
    unsafe_nested["rows"][0]["market_slug"] = "hidden-market"
    with pytest.raises(ValueError, match="unsafe public field"):
        module.research_market_tail_fee_liquidity_reserve_report_payload(unsafe_nested)


def test_empty_input_blocks_without_rows_or_private_signal_leakage() -> None:
    report = build_report()
    payload = api().research_market_tail_fee_liquidity_reserve_report_payload(report)

    assert report.status == "block"
    assert report.input_count == d("0.000000")
    assert report.pass_count == d("0.000000")
    assert report.watch_count == d("0.000000")
    assert report.block_count == d("0.000000")
    assert report.average_required_reserve_rate is None
    assert report.max_required_reserve_rate == d("0.000000")
    assert report.min_reserve_coverage_ratio is None
    assert report.reason_codes == ("missing_tail_fee_liquidity_reserve_inputs",)
    assert report.reason_code_counts[0].reason_code == (
        "missing_tail_fee_liquidity_reserve_inputs"
    )
    assert report.reason_code_counts[0].row_ratio == d("1.000000")
    assert report.rows == ()
    assert payload["rows"] == []


def test_frozen_decimal_only_flags_and_validation_contracts() -> None:
    module = api()
    report = build_report(sample("contract-check"))

    for contract in (
        module.ResearchMarketTailFeeLiquidityReserveConfig,
        module.ResearchMarketTailFeeLiquidityReserveInput,
        module.ResearchMarketTailFeeLiquidityReserveReasonCodeCount,
        module.ResearchMarketTailFeeLiquidityReserveReportRow,
        module.ResearchMarketTailFeeLiquidityReserveReport,
    ):
        assert contract.__dataclass_params__.frozen is True
        defaults = {field.name: field.default for field in fields(contract)}
        assert defaults["paper_only"] is True
        assert defaults["report_only"] is True
        assert defaults["readonly"] is True
        assert all(field.type not in (int, float) for field in fields(contract))

    assert module.STATUSES == ("pass", "watch", "block")
    with pytest.raises(FrozenInstanceError):
        report.status = "pass"  # type: ignore[misc]
    with pytest.raises(TypeError):

        class BadConfig(module.ResearchMarketTailFeeLiquidityReserveConfig):
            pass

    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="must be a Decimal"):
        sample("decimal-subclass", tail_probability=DecimalSubclass("0.100000"))
    with pytest.raises(ValueError, match="must be a datetime"):
        sample(
            "datetime-subclass",
            observed_at=DateTimeSubclass(2026, 7, 9, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="required_reserve_rate"):
        config(
            watch_required_reserve_rate=d("0.130000"),
            block_required_reserve_rate=d("0.120000"),
        )
    with pytest.raises(ValueError, match="reserve_coverage_ratio"):
        config(
            watch_min_reserve_coverage_ratio=d("0.900000"),
            block_min_reserve_coverage_ratio=d("1.000000"),
        )
    with pytest.raises(ValueError, match="status"):
        replace(report, status="blocked")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, max_required_reserve_rate=d("0.999999"))


def test_module_has_no_network_database_or_trading_surface() -> None:
    module = api()
    source = module.__loader__.get_source(module.__name__).lower()

    assert "research_market_tail_fee_liquidity_reserve_report_payload" in module.__all__
    for banned in (
        "api_key",
        "private_key",
        "wallet",
        "psycopg",
        "supabase",
        "requests",
        "httpx",
        "urllib",
        "socket",
        "open(",
        ".read(",
        ".write(",
        "place_order",
        "submit_order",
        "cancel_order",
        "sign_order",
        "live_trading",
        "recommendation",
        "sizing",
    ):
        assert banned not in source


def _walk_payload_values(value: object) -> tuple[object, ...]:
    values: list[object] = []
    if isinstance(value, dict):
        for item in value.values():
            values.extend(_walk_payload_values(item))
    elif isinstance(value, list):
        for item in value:
            values.extend(_walk_payload_values(item))
    else:
        values.append(value)
    return tuple(values)
