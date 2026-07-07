from __future__ import annotations

from dataclasses import FrozenInstanceError, fields
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import json

import pytest

import polymarket_alpha_lab.research_market_microstructure_warning_report as api
from polymarket_alpha_lab.research_market_microstructure_warning_report import (
    ResearchMarketMicrostructureObservation,
    ResearchMarketMicrostructureWarningConfig,
    ResearchMarketMicrostructureWarningReport,
    ResearchMarketMicrostructureWarningRow,
    build_research_market_microstructure_warning_report,
)


NOW = datetime(2026, 1, 1, tzinfo=UTC)


def _observation(
    *,
    observed_at: datetime = NOW,
    available_depth: Decimal = Decimal("1500.000000"),
    spread_width: Decimal = Decimal("0.010000"),
    book_balance_ratio: Decimal = Decimal("0.500000"),
    fee_to_edge_ratio: Decimal = Decimal("0.100000"),
    minutes_to_settlement: Decimal = Decimal("300.000000"),
    research_reviewed: bool = True,
) -> ResearchMarketMicrostructureObservation:
    return ResearchMarketMicrostructureObservation(
        observed_at=observed_at,
        available_depth=available_depth,
        spread_width=spread_width,
        book_balance_ratio=book_balance_ratio,
        fee_to_edge_ratio=fee_to_edge_ratio,
        minutes_to_settlement=minutes_to_settlement,
        research_reviewed=research_reviewed,
    )


def _report(
    observations: tuple[ResearchMarketMicrostructureObservation, ...],
    *,
    config: ResearchMarketMicrostructureWarningConfig | None = None,
) -> ResearchMarketMicrostructureWarningReport:
    return build_research_market_microstructure_warning_report(
        observations,
        generated_at=NOW,
        config=config,
    )


def test_microstructure_report_passes_when_all_domains_are_inside_thresholds() -> None:
    report = _report((_observation(),))

    row = report.rows[0]
    assert report.warning_status == "pass"
    assert report.observation_count == Decimal("1.000000")
    assert report.pass_count == Decimal("1.000000")
    assert report.watch_count == Decimal("0.000000")
    assert report.block_count == Decimal("0.000000")
    assert row.sequence_number == Decimal("1.000000")
    assert row.warning_status == "pass"
    assert row.warning_count == Decimal("0.000000")
    assert row.reason_codes == ("microstructure_pass",)
    assert row.paper_only is True
    assert row.report_only is True
    assert row.readonly is True


def test_warning_report_blocks_when_all_microstructure_domains_are_flagged() -> None:
    report = _report(
        (
            _observation(
                available_depth=Decimal("500.000000"),
                spread_width=Decimal("0.080000"),
                book_balance_ratio=Decimal("0.850000"),
                fee_to_edge_ratio=Decimal("0.500000"),
                minutes_to_settlement=Decimal("60.000000"),
            ),
        ),
    )

    row = report.rows[0]
    assert report.warning_status == "block"
    assert report.block_count == Decimal("1.000000")
    assert report.insufficient_depth_count == Decimal("1.000000")
    assert report.abnormal_spread_count == Decimal("1.000000")
    assert report.book_skew_count == Decimal("1.000000")
    assert report.fee_friction_count == Decimal("1.000000")
    assert report.near_settlement_liquidity_risk_count == Decimal("1.000000")
    assert row.warning_status == "block"
    assert row.warning_count == Decimal("5.000000")
    assert row.depth_insufficient is True
    assert row.spread_abnormal is True
    assert row.book_skew is True
    assert row.fee_friction is True
    assert row.near_settlement_liquidity_risk is True
    assert row.reason_codes == (
        "depth_insufficient",
        "spread_abnormal",
        "book_skew",
        "fee_friction",
        "near_settlement_liquidity_risk",
    )


def test_warning_report_watches_isolated_abnormal_spread() -> None:
    report = _report((_observation(spread_width=Decimal("0.070000")),))

    row = report.rows[0]
    assert report.warning_status == "watch"
    assert report.watch_count == Decimal("1.000000")
    assert row.warning_status == "watch"
    assert row.warning_count == Decimal("1.000000")
    assert row.spread_abnormal is True
    assert row.reason_codes == ("spread_abnormal",)


def test_payload_serializes_decimal_strings_without_identifiers_or_action_language() -> None:
    report = _report(
        (
            _observation(),
            _observation(
                available_depth=Decimal("500.000000"),
                spread_width=Decimal("0.080000"),
                book_balance_ratio=Decimal("0.850000"),
                fee_to_edge_ratio=Decimal("0.500000"),
                minutes_to_settlement=Decimal("60.000000"),
            ),
        ),
    )

    payload = report.payload
    json.dumps(payload, sort_keys=True)
    assert payload["observation_count"] == "2.000000"
    assert payload["rows"][0]["available_depth"] == "1500.000000"
    assert payload["rows"][1]["warning_count"] == "5.000000"
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert isinstance(payload["derived_validation_digest"], str)
    assert len(payload["derived_validation_digest"]) == 64
    _assert_no_decimal_objects(payload)
    _assert_no_non_decimal_public_numbers(report)
    _assert_public_payload_has_no_identifiers_or_action_language(payload)


def test_dataclasses_are_frozen_and_reject_subclassing() -> None:
    report = _report((_observation(),))

    with pytest.raises(FrozenInstanceError):
        report.warning_status = "watch"  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadConfig(ResearchMarketMicrostructureWarningConfig):
            pass


def test_strict_type_validation_rejects_non_decimal_inputs() -> None:
    with pytest.raises(ValueError, match="available_depth"):
        ResearchMarketMicrostructureObservation(
            observed_at=NOW,
            available_depth=1500,  # type: ignore[arg-type]
            spread_width=Decimal("0.010000"),
            book_balance_ratio=Decimal("0.500000"),
            fee_to_edge_ratio=Decimal("0.100000"),
            minutes_to_settlement=Decimal("300.000000"),
            research_reviewed=True,
        )

    with pytest.raises(ValueError, match="max_spread_width"):
        ResearchMarketMicrostructureWarningConfig(
            max_spread_width=0.05,  # type: ignore[arg-type]
        )

    with pytest.raises(ValueError, match="generated_at"):
        build_research_market_microstructure_warning_report(
            (_observation(),),
            generated_at=datetime(2026, 1, 1),
        )

    with pytest.raises(ValueError, match="observed_at"):
        build_research_market_microstructure_warning_report(
            (_observation(observed_at=NOW + timedelta(minutes=1)),),
            generated_at=NOW,
        )


def test_report_rejects_tampering_and_unsafe_public_surfaces() -> None:
    report = _report((_observation(),))

    with pytest.raises(ValueError, match="derived_validation_digest"):
        dataclass_values = {
            field.name: getattr(report, field.name)
            for field in fields(ResearchMarketMicrostructureWarningReport)
        }
        dataclass_values["derived_validation_digest"] = "0" * 64
        ResearchMarketMicrostructureWarningReport(**dataclass_values)

    forbidden_terms = (
        "auth",
        "wallet",
        "network",
        "database",
        "mutation",
        "order",
        "buy",
        "sell",
        "trade",
        "position",
        "recommend",
    )
    for public_name in api.__all__:
        lowered = public_name.lower()
        assert not any(term in lowered for term in forbidden_terms)

    for cls in (
        ResearchMarketMicrostructureObservation,
        ResearchMarketMicrostructureWarningConfig,
        ResearchMarketMicrostructureWarningRow,
        ResearchMarketMicrostructureWarningReport,
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


def _assert_public_payload_has_no_identifiers_or_action_language(value: object) -> None:
    forbidden_terms = (
        "market_id",
        "market_slug",
        "condition_id",
        "token_id",
        "source",
        "auth",
        "wallet",
        "network",
        "database",
        "mutation",
        "order",
        "buy",
        "sell",
        "trade",
        "position",
        "recommend",
    )
    if isinstance(value, dict):
        for key, item in value.items():
            lowered = key.lower()
            assert not any(term in lowered for term in forbidden_terms)
            _assert_public_payload_has_no_identifiers_or_action_language(item)
        return
    if isinstance(value, list):
        for item in value:
            _assert_public_payload_has_no_identifiers_or_action_language(item)
        return
    if isinstance(value, str):
        lowered = value.lower()
        assert not any(term in lowered for term in forbidden_terms)
