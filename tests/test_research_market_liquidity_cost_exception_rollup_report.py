from __future__ import annotations

import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab.research_market_liquidity_cost_exception_rollup_report"
)
GENERATED_AT = datetime(2026, 7, 8, 16, 0, tzinfo=UTC)
OBSERVED_AT = datetime(2026, 7, 8, 15, 58, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def api():
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": (
            module.DEFAULT_RESEARCH_MARKET_LIQUIDITY_COST_EXCEPTION_ROLLUP_REPORT_CONFIG_VERSION
        ),
        "watch_depth_deterioration_ratio": d("0.200000"),
        "block_depth_deterioration_ratio": d("0.500000"),
        "watch_spread_stress_score": d("0.300000"),
        "block_spread_stress_score": d("0.700000"),
        "watch_fee_age_seconds": d("3600.000000"),
        "block_fee_age_seconds": d("14400.000000"),
        "watch_settlement_friction_score": d("0.250000"),
        "block_settlement_friction_score": d("0.650000"),
        "watch_quote_age_seconds": d("60.000000"),
        "block_quote_age_seconds": d("300.000000"),
        "watch_manual_review_urgency": d("0.300000"),
        "block_manual_review_urgency": d("0.700000"),
        "block_component_count_threshold": d("3.000000"),
    }
    values.update(overrides)
    return module.ResearchMarketLiquidityCostExceptionRollupConfig(**values)


def exception_input(
    rollup_key: str = "rollup-pass",
    *,
    observed_at: datetime = OBSERVED_AT,
    depth_deterioration_ratio: Decimal = d("0.050000"),
    spread_stress_score: Decimal = d("0.100000"),
    fee_age_seconds: Decimal = d("900.000000"),
    settlement_friction_score: Decimal = d("0.100000"),
    quote_age_seconds: Decimal = d("20.000000"),
    manual_review_urgency: Decimal = d("0.100000"),
    reason_codes: tuple[str, ...] = (),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
):
    module = api()
    return module.ResearchMarketLiquidityCostExceptionInput(
        rollup_key=rollup_key,
        observed_at=observed_at,
        depth_deterioration_ratio=depth_deterioration_ratio,
        spread_stress_score=spread_stress_score,
        fee_age_seconds=fee_age_seconds,
        settlement_friction_score=settlement_friction_score,
        quote_age_seconds=quote_age_seconds,
        manual_review_urgency=manual_review_urgency,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(*items: object, cfg: object | None = None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_research_market_liquidity_cost_exception_rollup_report(
        items,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_empty_input_blocks_public_safe_report_only_payload_with_digest() -> None:
    module = api()
    built = report()

    assert module.LIQUIDITY_COST_EXCEPTION_ROLLUP_STATUSES == ("pass", "watch", "block")
    assert module.__all__ == (
        "LIQUIDITY_COST_EXCEPTION_ROLLUP_STATUSES",
        "DEFAULT_RESEARCH_MARKET_LIQUIDITY_COST_EXCEPTION_ROLLUP_REPORT_CONFIG_VERSION",
        "ResearchMarketLiquidityCostExceptionInput",
        "ResearchMarketLiquidityCostExceptionReasonCodeCount",
        "ResearchMarketLiquidityCostExceptionRollupConfig",
        "ResearchMarketLiquidityCostExceptionRollupReport",
        "ResearchMarketLiquidityCostExceptionRollupRow",
        "build_research_market_liquidity_cost_exception_rollup_report",
        "research_market_liquidity_cost_exception_rollup_report_digest",
        "research_market_liquidity_cost_exception_rollup_report_payload",
    )
    assert type(built) is module.ResearchMarketLiquidityCostExceptionRollupReport
    assert is_dataclass(built)
    assert built.generated_at == GENERATED_AT
    assert built.config_version == (
        "research-market-liquidity-cost-exception-rollup-report-v0"
    )
    assert built.rollup_count == ZERO
    assert built.pass_count == ZERO
    assert built.watch_count == ZERO
    assert built.block_count == ZERO
    assert built.exception_component_count == ZERO
    assert built.block_component_count == ZERO
    assert built.average_exception_score is None
    assert built.status == "block"
    assert built.reason_codes == ("no_liquidity_cost_exception_rollups",)
    assert built.reason_code_counts == (
        module.ResearchMarketLiquidityCostExceptionReasonCodeCount(
            reason_code="no_liquidity_cost_exception_rollups",
            count=d("1.000000"),
            row_ratio=ZERO,
        ),
    )
    assert built.rows == ()
    assert built.paper_only is True
    assert built.report_only is True
    assert built.readonly is True

    payload = module.research_market_liquidity_cost_exception_rollup_report_payload(built)
    digest = module.research_market_liquidity_cost_exception_rollup_report_digest(built)

    json.dumps(payload, sort_keys=True)
    assert payload["rollup_count"] == "0.000000"
    assert payload["derived_validation_digest"] == digest
    assert len(digest) == 64
    assert_no_number_payload(payload)
    assert_no_forbidden_public_surface(payload)


def test_rollup_aggregates_depth_spread_fee_settlement_quote_and_manual_urgency() -> None:
    built = report(
        exception_input("bucket-watch", depth_deterioration_ratio=d("0.300000"), spread_stress_score=d("0.400000"), fee_age_seconds=d("7200.000000"), settlement_friction_score=d("0.300000"), quote_age_seconds=d("120.000000"), manual_review_urgency=d("0.500000"), reason_codes=("alpha",)),
        exception_input("bucket-block", depth_deterioration_ratio=d("0.600000"), spread_stress_score=d("0.800000"), fee_age_seconds=d("20000.000000"), settlement_friction_score=d("0.800000"), quote_age_seconds=d("360.000000"), manual_review_urgency=d("0.900000")),
        exception_input("bucket-pass"),
    )

    assert built.rollup_count == d("3.000000")
    assert built.pass_count == d("1.000000")
    assert built.watch_count == d("1.000000")
    assert built.block_count == d("1.000000")
    assert built.exception_component_count == d("12.000000")
    assert built.block_component_count == d("6.000000")
    assert built.average_exception_score == d("0.550888")
    assert built.max_depth_deterioration_ratio == d("0.600000")
    assert built.max_spread_stress_score == d("0.800000")
    assert built.max_fee_age_seconds == d("20000.000000")
    assert built.max_settlement_friction_score == d("0.800000")
    assert built.max_quote_age_seconds == d("360.000000")
    assert built.max_manual_review_urgency == d("0.900000")
    assert built.status == "block"
    assert built.reason_codes == (
        "liquidity_cost_exception_rollup_block",
        "depth_deterioration_block",
        "spread_stress_block",
        "fee_freshness_block",
        "settlement_friction_block",
        "quote_age_block",
        "manual_review_urgency_block",
        "depth_deterioration_watch",
        "spread_stress_watch",
        "fee_freshness_watch",
        "settlement_friction_watch",
        "quote_age_watch",
        "manual_review_urgency_watch",
    )

    block_row, pass_row, watch_row = built.rows
    assert tuple(row.rollup_key for row in built.rows) == (
        "bucket-block",
        "bucket-pass",
        "bucket-watch",
    )
    assert tuple(row.status for row in built.rows) == ("block", "pass", "watch")
    assert block_row.exception_score == d("1.000000")
    assert block_row.exception_component_count == d("6.000000")
    assert block_row.block_component_count == d("6.000000")
    assert block_row.reason_codes == (
        "depth_deterioration_block",
        "fee_freshness_block",
        "liquidity_cost_exception_block",
        "manual_review_urgency_block",
        "quote_age_block",
        "settlement_friction_block",
        "spread_stress_block",
    )
    assert pass_row.status == "pass"
    assert pass_row.exception_score == d("0.111455")
    assert pass_row.reason_codes == ("liquidity_cost_exception_pass",)
    assert watch_row.exception_score == d("0.541209")
    assert watch_row.reason_codes == (
        "depth_deterioration_watch",
        "fee_freshness_watch",
        "input_alpha",
        "liquidity_cost_exception_watch",
        "manual_review_urgency_watch",
        "quote_age_watch",
        "settlement_friction_watch",
        "spread_stress_watch",
    )


def test_payload_and_digest_are_deterministic_decimal_strings_and_digest_validated() -> None:
    module = api()
    first = report(
        exception_input("z-bucket", reason_codes=("zeta", "alpha")),
        exception_input("a-bucket"),
    )
    second = report(
        exception_input("a-bucket"),
        exception_input("z-bucket", reason_codes=("alpha", "zeta")),
    )

    first_payload = module.research_market_liquidity_cost_exception_rollup_report_payload(
        first,
    )
    second_payload = module.research_market_liquidity_cost_exception_rollup_report_payload(
        second,
    )

    assert first_payload == second_payload
    assert module.research_market_liquidity_cost_exception_rollup_report_digest(first) == (
        module.research_market_liquidity_cost_exception_rollup_report_digest(second)
    )
    assert first_payload["rows"][0]["rollup_key"] == "a-bucket"
    assert first_payload["rows"][0]["exception_score"] == "0.111455"
    assert_no_number_payload(first_payload)
    assert_no_forbidden_public_surface(first_payload)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(first, derived_validation_digest="0" * 64)


def test_validation_rejects_non_decimal_values_bad_flags_and_inconsistent_rows() -> None:
    module = api()
    built = report(exception_input())

    for value in (config(), exception_input(), built, *built.rows, *built.reason_code_counts):
        assert is_dataclass(value)
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True
        for item in fields(value):
            item_value = getattr(value, item.name)
            if item.name in {
                "paper_only",
                "report_only",
                "readonly",
                "average_exception_score",
            }:
                continue
            if item.name.endswith(
                (
                    "_count",
                    "_score",
                    "_ratio",
                    "_seconds",
                    "_urgency",
                ),
            ):
                assert type(item_value) is Decimal, item.name

    with pytest.raises(FrozenInstanceError):
        built.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        built.rows[0].exception_score = ZERO  # type: ignore[misc]
    with pytest.raises(ValueError, match="watch_depth_deterioration_ratio"):
        config(watch_depth_deterioration_ratio=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="block_fee_age_seconds"):
        config(block_fee_age_seconds=_DecimalSubclass("14400.000000"))
    with pytest.raises(ValueError, match="generated_at"):
        report(exception_input(), generated_at=datetime(2026, 7, 8, 16, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            exception_input(),
            generated_at=_DatetimeSubclass(2026, 7, 8, 16, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="rollup_key"):
        exception_input("raw-market-id-123")
    with pytest.raises(ValueError, match="depth_deterioration_ratio"):
        exception_input(depth_deterioration_ratio=d("1.100000"))
    with pytest.raises(ValueError, match="spread_stress_score"):
        exception_input(spread_stress_score=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="reason_codes"):
        exception_input(reason_codes=("Needs Review",))
    with pytest.raises(ValueError, match="paper_only"):
        replace(exception_input(), paper_only=False)
    with pytest.raises(ValueError, match="status"):
        replace(built.rows[0], status="halt")
    with pytest.raises(ValueError, match="exception_score"):
        replace(built.rows[0], exception_score=d("0.999999"))
    with pytest.raises(ValueError, match="report"):
        module.research_market_liquidity_cost_exception_rollup_report_payload(object())
    with pytest.raises(ValueError, match="readonly"):
        replace(built, readonly=False)


def test_owned_module_has_no_side_effect_decision_or_execution_surfaces() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_market_liquidity_cost_exception_rollup_report.py"
    )
    text = module_path.read_text(encoding="utf-8").lower()
    forbidden_terms = (
        "requests",
        "urllib",
        "httpx",
        "aiohttp",
        "socket",
        "subprocess",
        "pathlib",
        "open(",
        "connect(",
        "database",
        "network",
        "wallet",
        "auth",
        "order",
        "trade",
        "live",
        "buy",
        "sell",
        "recommend",
        "sizing",
    )

    assert all(term not in text for term in forbidden_terms)


def assert_no_number_payload(value: Any) -> None:
    if type(value) in (float, int) or isinstance(value, Decimal):
        raise AssertionError(f"public numeric value was not a string: {value!r}")
    if isinstance(value, dict):
        for item_value in value.values():
            assert_no_number_payload(item_value)
    elif isinstance(value, list):
        for item_value in value:
            assert_no_number_payload(item_value)


def assert_no_forbidden_public_surface(value: Any) -> None:
    fragments = (
        "raw",
        "market_id",
        "slug",
        "question",
        "candidate",
        "source",
        "url",
        "text",
        "dsn",
        "table",
        "token",
        "private",
    )
    if isinstance(value, dict):
        for key, item_value in value.items():
            lowered_key = key.lower()
            for fragment in fragments:
                assert fragment not in lowered_key, key
            assert_no_forbidden_public_surface(item_value)
    elif isinstance(value, list):
        for item_value in value:
            assert_no_forbidden_public_surface(item_value)
    elif isinstance(value, str):
        lowered = value.lower()
        assert "://" not in lowered
        for fragment in fragments:
            assert fragment not in lowered, value
