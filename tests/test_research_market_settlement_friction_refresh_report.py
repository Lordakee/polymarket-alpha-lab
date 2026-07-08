from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime
from decimal import Decimal
import json

import pytest

import polymarket_alpha_lab.research_market_settlement_friction_refresh_report as api
from polymarket_alpha_lab.research_market_settlement_friction_refresh_report import (
    ResearchMarketSettlementFrictionRefreshConfig,
    ResearchMarketSettlementFrictionRefreshInput,
    ResearchMarketSettlementFrictionRefreshReport,
    ResearchMarketSettlementFrictionRefreshRow,
    build_research_market_settlement_friction_refresh_report,
    research_market_settlement_friction_refresh_report_payload,
)


NOW = datetime(2026, 1, 1, tzinfo=UTC)


def d(value: str) -> Decimal:
    return Decimal(value)


def friction_input(
    *,
    aggregate_key: str = "macro-rates",
    settlement_cost_assumption_ratio: Decimal = d("0.010000"),
    evidence_age_hours: Decimal = d("6.000000"),
    fee_spread_interaction_ratio: Decimal = d("0.010000"),
    liquidity_confidence: Decimal = d("0.900000"),
    manual_recheck_urgency: Decimal = d("0.100000"),
) -> ResearchMarketSettlementFrictionRefreshInput:
    return ResearchMarketSettlementFrictionRefreshInput(
        aggregate_key=aggregate_key,
        settlement_cost_assumption_ratio=settlement_cost_assumption_ratio,
        evidence_age_hours=evidence_age_hours,
        fee_spread_interaction_ratio=fee_spread_interaction_ratio,
        liquidity_confidence=liquidity_confidence,
        manual_recheck_urgency=manual_recheck_urgency,
    )


def build_report(
    *inputs: ResearchMarketSettlementFrictionRefreshInput,
    config: ResearchMarketSettlementFrictionRefreshConfig | None = None,
) -> ResearchMarketSettlementFrictionRefreshReport:
    return build_research_market_settlement_friction_refresh_report(
        inputs,
        generated_at=NOW,
        config=config,
    )


def test_refresh_report_scores_pass_watch_and_block_friction_readiness() -> None:
    report = build_report(
        friction_input(),
        friction_input(
            aggregate_key="sports-mix",
            settlement_cost_assumption_ratio=d("0.030000"),
            evidence_age_hours=d("18.000000"),
            fee_spread_interaction_ratio=d("0.040000"),
            liquidity_confidence=d("0.600000"),
            manual_recheck_urgency=d("0.400000"),
        ),
        friction_input(
            aggregate_key="policy-close",
            settlement_cost_assumption_ratio=d("0.080000"),
            evidence_age_hours=d("60.000000"),
            fee_spread_interaction_ratio=d("0.090000"),
            liquidity_confidence=d("0.300000"),
            manual_recheck_urgency=d("0.850000"),
        ),
    )

    assert report.status == "block"
    assert report.entry_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert tuple(row.status for row in report.rows) == ("pass", "watch", "block")
    assert tuple(row.aggregate_key for row in report.rows) == (
        "macro-rates",
        "sports-mix",
        "policy-close",
    )

    passed, watched, blocked = report.rows
    assert passed.friction_pressure_score == d("0.150000")
    assert passed.reason_codes == ("settlement_friction_refresh_pass",)
    assert watched.friction_pressure_score == d("0.500000")
    assert watched.reason_codes == (
        "settlement_cost_assumption_watch",
        "evidence_age_watch",
        "fee_spread_interaction_watch",
        "liquidity_confidence_watch",
        "manual_recheck_urgency_watch",
    )
    assert blocked.friction_pressure_score == d("1.000000")
    assert blocked.reason_codes == (
        "settlement_cost_assumption_block",
        "evidence_age_block",
        "fee_spread_interaction_block",
        "liquidity_confidence_block",
        "manual_recheck_urgency_block",
    )

    assert report.settlement_cost_watch_count == d("1.000000")
    assert report.settlement_cost_block_count == d("1.000000")
    assert report.evidence_age_watch_count == d("1.000000")
    assert report.evidence_age_block_count == d("1.000000")
    assert report.fee_spread_interaction_watch_count == d("1.000000")
    assert report.fee_spread_interaction_block_count == d("1.000000")
    assert report.liquidity_confidence_watch_count == d("1.000000")
    assert report.liquidity_confidence_block_count == d("1.000000")
    assert report.manual_recheck_urgency_watch_count == d("1.000000")
    assert report.manual_recheck_urgency_block_count == d("1.000000")
    assert report.reason_code_counts[0].reason_code == "settlement_friction_refresh_pass"
    assert report.reason_code_counts[0].count == d("1.000000")


def test_payload_is_deterministic_decimal_only_and_tamper_evident() -> None:
    report = build_report(
        friction_input(aggregate_key="zeta"),
        friction_input(
            aggregate_key="alpha",
            settlement_cost_assumption_ratio=d("0.050000"),
            evidence_age_hours=d("24.000000"),
        ),
    )

    payload = research_market_settlement_friction_refresh_report_payload(report)
    payload_again = research_market_settlement_friction_refresh_report_payload(report)

    assert payload == payload_again
    assert json.dumps(payload, sort_keys=True)
    assert payload["entry_count"] == "2.000000"
    assert payload["rows"][0]["aggregate_key"] == "alpha"
    assert payload["rows"][0]["settlement_cost_assumption_ratio"] == "0.050000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert len(report.derived_validation_digest) == 64
    assert all(character in "0123456789abcdef" for character in report.derived_validation_digest)
    assert_no_decimal_objects(payload)
    assert_no_non_decimal_public_numbers(report)

    tampered = {
        field.name: getattr(report, field.name)
        for field in fields(ResearchMarketSettlementFrictionRefreshReport)
    }
    tampered["derived_validation_digest"] = "0" * 64
    with pytest.raises(ValueError, match="derived_validation_digest"):
        ResearchMarketSettlementFrictionRefreshReport(**tampered)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report.rows[0], friction_pressure_score=d("0.900000"))


def test_report_only_surface_is_frozen_strict_and_public_safe() -> None:
    report = build_report((friction_input())[0:] if False else friction_input())

    with pytest.raises(FrozenInstanceError):
        report.status = "watch"  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadRow(ResearchMarketSettlementFrictionRefreshRow):
            pass

    with pytest.raises(ValueError, match="settlement_cost_assumption_ratio"):
        friction_input(settlement_cost_assumption_ratio=1)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="status"):
        replace(report.rows[0], status="blocked")

    with pytest.raises(ValueError, match="paper_only"):
        ResearchMarketSettlementFrictionRefreshInput(
            aggregate_key="manual-review",
            settlement_cost_assumption_ratio=d("0.010000"),
            evidence_age_hours=d("1.000000"),
            fee_spread_interaction_ratio=d("0.010000"),
            liquidity_confidence=d("0.900000"),
            manual_recheck_urgency=d("0.100000"),
            paper_only=False,
        )

    assert api.STATUSES == ("pass", "watch", "block")
    assert "blocked" not in api.STATUSES
    assert_public_surface_has_no_execution_terms()


def assert_no_decimal_objects(value: object) -> None:
    if isinstance(value, Decimal):
        raise AssertionError("payload contains Decimal object")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_decimal_objects(item)
    if isinstance(value, list):
        for item in value:
            assert_no_decimal_objects(item)


def assert_no_non_decimal_public_numbers(value: object) -> None:
    if isinstance(value, Decimal):
        return
    if type(value) is bool or value is None or isinstance(value, (str, datetime)):
        return
    if type(value) is int or isinstance(value, float):
        raise AssertionError(f"non-Decimal public numeric value {value!r}")
    if isinstance(value, tuple):
        for item in value:
            assert_no_non_decimal_public_numbers(item)
        return
    if hasattr(value, "__dataclass_fields__"):
        for field in fields(value):
            assert_no_non_decimal_public_numbers(getattr(value, field.name))


def assert_public_surface_has_no_execution_terms() -> None:
    forbidden_terms = (
        "auth",
        "wallet",
        "network",
        "database",
        "persist",
        "mutation",
        "order",
        "buy",
        "sell",
        "trade",
        "position",
        "recommend",
        "sizing",
        "live",
    )
    for public_name in api.__all__:
        lowered = public_name.lower()
        assert not any(term in lowered for term in forbidden_terms)
    for cls in (
        ResearchMarketSettlementFrictionRefreshConfig,
        ResearchMarketSettlementFrictionRefreshInput,
        ResearchMarketSettlementFrictionRefreshRow,
        ResearchMarketSettlementFrictionRefreshReport,
    ):
        for field in fields(cls):
            lowered = field.name.lower()
            assert not any(term in lowered for term in forbidden_terms)
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
