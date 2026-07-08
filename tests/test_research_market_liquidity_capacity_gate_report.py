from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime
from decimal import Decimal
import json

import pytest

import polymarket_alpha_lab.research_market_liquidity_capacity_gate_report as api
from polymarket_alpha_lab.research_market_liquidity_capacity_gate_report import (
    ResearchMarketLiquidityCapacityGateConfig,
    ResearchMarketLiquidityCapacityGateReport,
    ResearchMarketLiquidityCapacityObservation,
    ResearchMarketLiquidityCapacityRow,
    build_research_market_liquidity_capacity_gate_report,
)


NOW = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


def d(value: str) -> Decimal:
    return Decimal(value)


def observation(
    *,
    market_slug: str = "event-alpha",
    spread_pressure: Decimal = d("0.020000"),
    book_depth_score: Decimal = d("0.900000"),
    fee_friction: Decimal = d("0.010000"),
    settlement_friction: Decimal = d("0.020000"),
    evidence_count: Decimal = d("3.000000"),
    reason_codes: tuple[str, ...] = ("manual_snapshot",),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchMarketLiquidityCapacityObservation:
    return ResearchMarketLiquidityCapacityObservation(
        market_slug=market_slug,
        observed_at=NOW,
        spread_pressure=spread_pressure,
        book_depth_score=book_depth_score,
        fee_friction=fee_friction,
        settlement_friction=settlement_friction,
        evidence_count=evidence_count,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def config(
    *,
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchMarketLiquidityCapacityGateConfig:
    return ResearchMarketLiquidityCapacityGateConfig(
        max_pass_spread_pressure=d("0.030000"),
        max_watch_spread_pressure=d("0.070000"),
        min_pass_book_depth_score=d("0.800000"),
        min_watch_book_depth_score=d("0.500000"),
        max_pass_fee_friction=d("0.015000"),
        max_watch_fee_friction=d("0.040000"),
        max_pass_settlement_friction=d("0.020000"),
        max_watch_settlement_friction=d("0.060000"),
        min_evidence_count=d("1.000000"),
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_report(
    *observations: ResearchMarketLiquidityCapacityObservation,
    gate_config: ResearchMarketLiquidityCapacityGateConfig | None = None,
) -> ResearchMarketLiquidityCapacityGateReport:
    return build_research_market_liquidity_capacity_gate_report(
        observations,
        generated_at=NOW,
        config=gate_config or config(),
    )


def test_capacity_gate_reports_aggregate_manual_review_readiness() -> None:
    report = build_report(
        observation(
            market_slug="liquid-pass",
            spread_pressure=d("0.020000"),
            book_depth_score=d("0.900000"),
            fee_friction=d("0.010000"),
            settlement_friction=d("0.020000"),
        ),
        observation(
            market_slug="spread-watch",
            spread_pressure=d("0.050000"),
            book_depth_score=d("0.700000"),
            fee_friction=d("0.012000"),
            settlement_friction=d("0.015000"),
        ),
        observation(
            market_slug="thin-block",
            spread_pressure=d("0.080000"),
            book_depth_score=d("0.400000"),
            fee_friction=d("0.050000"),
            settlement_friction=d("0.070000"),
        ),
    )

    assert type(report) is ResearchMarketLiquidityCapacityGateReport
    assert report.generated_at == NOW
    assert report.gate_status == "block"
    assert report.market_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.average_readiness_score == d("0.889417")
    assert report.max_spread_pressure == d("0.080000")
    assert report.min_book_depth_score == d("0.400000")
    assert report.max_fee_friction == d("0.050000")
    assert report.max_settlement_friction == d("0.070000")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert tuple((row.gate_status, row.market_slug) for row in report.rows) == (
        ("block", "thin-block"),
        ("watch", "spread-watch"),
        ("pass", "liquid-pass"),
    )

    block_row = report.rows[0]
    assert type(block_row) is ResearchMarketLiquidityCapacityRow
    assert block_row.readiness_score == d("0.800000")
    assert block_row.reason_codes == (
        "book_depth_block",
        "fee_friction_block",
        "manual_snapshot",
        "settlement_friction_block",
        "spread_pressure_block",
    )

    pass_row = report.rows[-1]
    assert pass_row.readiness_score == d("0.962500")
    assert pass_row.reason_codes == (
        "book_depth_sufficient",
        "capacity_gate_pass",
        "fee_friction_pass",
        "manual_snapshot",
        "settlement_friction_pass",
        "spread_pressure_pass",
    )


def test_capacity_gate_payload_digest_is_deterministic_and_json_ready() -> None:
    observations = (
        observation(market_slug="liquid-pass"),
        observation(
            market_slug="spread-watch",
            spread_pressure=d("0.050000"),
            book_depth_score=d("0.700000"),
        ),
    )
    report = build_report(*observations)
    reordered = build_report(*reversed(observations))

    assert report.derived_validation_digest == reordered.derived_validation_digest
    assert len(report.derived_validation_digest) == 64
    payload = report.payload
    json.dumps(payload, sort_keys=True)
    assert payload["market_count"] == "2.000000"
    assert payload["rows"][0]["spread_pressure"] == "0.050000"
    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    _assert_no_decimal_objects(payload)
    _assert_no_non_decimal_public_numbers(report)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, gate_status="pass")


def test_capacity_gate_blocks_missing_evidence_and_empty_observations() -> None:
    report = build_report(
        observation(
            market_slug="missing-evidence",
            evidence_count=d("0.000000"),
        ),
    )

    assert report.gate_status == "block"
    assert report.block_count == d("1.000000")
    assert report.rows[0].gate_status == "block"
    assert report.rows[0].reason_codes == ("insufficient_evidence", "manual_snapshot")

    empty = build_report()
    assert empty.gate_status == "block"
    assert empty.market_count == d("0.000000")
    assert empty.reason_codes == ("empty_observations",)


def test_capacity_gate_enforces_decimal_only_inputs_and_safety_flags() -> None:
    with pytest.raises(ValueError, match="spread_pressure"):
        observation(spread_pressure=0.02)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="book_depth_score"):
        observation(book_depth_score=d("1.000001"))
    with pytest.raises(ValueError, match="max_watch_fee_friction"):
        replace(config(), max_watch_fee_friction=d("1.000001"))
    with pytest.raises(ValueError, match="paper_only"):
        observation(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        config(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(build_report(observation()), readonly=False)


def test_capacity_gate_dataclasses_are_frozen_and_public_surface_is_readonly() -> None:
    item = observation()
    report = build_report(item)

    with pytest.raises(FrozenInstanceError):
        item.market_slug = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.rows[0].gate_status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.rows = ()  # type: ignore[misc]

    for public_name in api.__all__:
        lowered = public_name.lower()
        assert "order" not in lowered
        assert "wallet" not in lowered
        assert "network" not in lowered
        assert "live" not in lowered
        assert "trade" not in lowered

    for cls in (
        ResearchMarketLiquidityCapacityGateConfig,
        ResearchMarketLiquidityCapacityObservation,
        ResearchMarketLiquidityCapacityRow,
        ResearchMarketLiquidityCapacityGateReport,
    ):
        for field in fields(cls):
            lowered = field.name.lower()
            assert "order" not in lowered
            assert "wallet" not in lowered
            assert "network" not in lowered
            assert "live" not in lowered
            assert "trade" not in lowered

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
