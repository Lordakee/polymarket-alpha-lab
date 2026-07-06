from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, replace
from decimal import Decimal

import pytest

from polymarket_alpha_lab.strategy_event_catalyst_validation_v10 import (
    StrategyEventCatalystValidationV10Input,
    StrategyEventCatalystValidationV10Result,
    build_strategy_event_catalyst_validation_v10,
    strategy_event_catalyst_validation_v10_payload,
)


def d(value: str) -> Decimal:
    return Decimal(value)


def catalyst_input(
    *,
    catalyst_type: str = "election_call",
    expected_event_time_minutes: Decimal = d("120.000000"),
    confirmed_source_count: Decimal = d("2.000000"),
    rumor_source_count: Decimal = d("1.000000"),
    official_confirmation_score: Decimal = d("0.900000"),
    market_move_bps: Decimal = d("85.000000"),
    time_to_resolution_minutes: Decimal = d("480.000000"),
    reason_codes: tuple[str, ...] = (),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> StrategyEventCatalystValidationV10Input:
    return StrategyEventCatalystValidationV10Input(
        catalyst_type=catalyst_type,
        expected_event_time_minutes=expected_event_time_minutes,
        confirmed_source_count=confirmed_source_count,
        rumor_source_count=rumor_source_count,
        official_confirmation_score=official_confirmation_score,
        market_move_bps=market_move_bps,
        time_to_resolution_minutes=time_to_resolution_minutes,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_result(
    value: StrategyEventCatalystValidationV10Input | None = None,
) -> StrategyEventCatalystValidationV10Result:
    return build_strategy_event_catalyst_validation_v10(value or catalyst_input())


def field_values(instance):
    return {field.name: getattr(instance, field.name) for field in fields(instance)}


def test_confirmed_catalyst_adds_positive_confidence_adjustment_without_live_action():
    result = build_result(
        catalyst_input(
            catalyst_type="court_ruling",
            reason_codes=("research_packet_ready",),
        ),
    )

    assert type(result) is StrategyEventCatalystValidationV10Result
    assert result.catalyst_type == "court_ruling"
    assert result.catalyst_status == "confirmed"
    assert result.confidence_adjustment == d("0.100000")
    assert result.research_action == "document_confirmed_catalyst_and_update_research_view"
    assert result.reason_codes == (
        "official_confirmation_high",
        "confirmed_source_quorum_met",
        "market_move_supports_catalyst",
        "catalyst_timing_before_resolution",
        "research_packet_ready",
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True


def test_timing_mismatch_blocks_confidence_lift_even_with_confirmation():
    result = build_result(
        catalyst_input(
            expected_event_time_minutes=d("600.000000"),
            time_to_resolution_minutes=d("120.000000"),
            confirmed_source_count=d("4.000000"),
            official_confirmation_score=d("1.000000"),
            market_move_bps=d("150.000000"),
        ),
    )

    assert result.catalyst_status == "timing_mismatch"
    assert result.confidence_adjustment == d("-0.100000")
    assert result.research_action == "exclude_catalyst_until_timing_is_resolved"
    assert result.reason_codes == (
        "event_expected_after_resolution",
        "official_confirmation_high",
        "confirmed_source_quorum_met",
        "market_move_supports_catalyst",
    )


def test_rumor_cluster_with_market_move_reduces_confidence_until_verified():
    result = build_result(
        catalyst_input(
            expected_event_time_minutes=d("90.000000"),
            confirmed_source_count=d("0.000000"),
            rumor_source_count=d("4.000000"),
            official_confirmation_score=d("0.200000"),
            market_move_bps=d("120.000000"),
            time_to_resolution_minutes=d("240.000000"),
        ),
    )

    assert result.catalyst_status == "rumor"
    assert result.confidence_adjustment == d("-0.040000")
    assert result.research_action == "collect_independent_confirmation_before_confidence_lift"
    assert result.reason_codes == (
        "rumor_sources_without_confirmation",
        "market_move_without_official_confirmation",
        "catalyst_timing_before_resolution",
    )


def test_probable_catalyst_requires_primary_source_verification():
    result = build_result(
        catalyst_input(
            expected_event_time_minutes=d("30.000000"),
            confirmed_source_count=d("1.000000"),
            rumor_source_count=d("2.000000"),
            official_confirmation_score=d("0.650000"),
            market_move_bps=d("40.000000"),
            time_to_resolution_minutes=d("180.000000"),
            reason_codes=("analyst_followup_open",),
        ),
    )

    assert result.catalyst_status == "probable"
    assert result.confidence_adjustment == d("0.030000")
    assert result.research_action == "verify_primary_sources_before_confidence_lift"
    assert result.reason_codes == (
        "official_confirmation_partial",
        "single_confirmed_source",
        "rumor_source_cluster",
        "catalyst_timing_before_resolution",
        "analyst_followup_open",
    )


def test_insufficient_evidence_keeps_confidence_neutral_and_readonly():
    result = build_result(
        catalyst_input(
            confirmed_source_count=d("0.000000"),
            rumor_source_count=d("0.000000"),
            official_confirmation_score=d("0.000000"),
            market_move_bps=d("-12.500000"),
        ),
    )

    assert result.catalyst_status == "insufficient_evidence"
    assert result.confidence_adjustment == d("0.000000")
    assert result.research_action == "keep_on_watchlist_without_confidence_change"
    assert result.reason_codes == (
        "no_catalyst_sources",
        "low_official_confirmation",
        "catalyst_timing_before_resolution",
    )
    assert result.market_move_bps == d("-12.500000")
    assert result.absolute_market_move_bps == d("12.500000")


def test_payload_is_json_ready_and_contains_no_decimal_objects():
    result = build_result()
    payload = strategy_event_catalyst_validation_v10_payload(result)

    assert payload == result.payload
    assert payload["catalyst_type"] == "election_call"
    assert payload["expected_event_time_minutes"] == "120.000000"
    assert payload["confirmed_source_count"] == "2.000000"
    assert payload["rumor_source_count"] == "1.000000"
    assert payload["official_confirmation_score"] == "0.900000"
    assert payload["market_move_bps"] == "85.000000"
    assert payload["absolute_market_move_bps"] == "85.000000"
    assert payload["time_to_resolution_minutes"] == "480.000000"
    assert payload["confidence_adjustment"] == "0.100000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert not any(isinstance(value, Decimal) for value in payload.values())


def test_inputs_use_decimal_only_values_and_validate_ranges():
    with pytest.raises(ValueError, match="expected_event_time_minutes must be a Decimal"):
        catalyst_input(expected_event_time_minutes=120)
    with pytest.raises(ValueError, match="confirmed_source_count must be an integer Decimal"):
        catalyst_input(confirmed_source_count=d("1.500000"))
    with pytest.raises(ValueError, match="official_confirmation_score must be between 0 and 1"):
        catalyst_input(official_confirmation_score=d("1.000001"))
    with pytest.raises(ValueError, match="time_to_resolution_minutes must be nonnegative"):
        catalyst_input(time_to_resolution_minutes=d("-0.000001"))
    with pytest.raises(ValueError, match="reason_codes must be a tuple"):
        catalyst_input(reason_codes=["manual_followup"])


def test_dataclasses_are_frozen_and_require_paper_report_readonly_flags():
    value = catalyst_input()
    result = build_result(value)
    rebuilt = StrategyEventCatalystValidationV10Result(**field_values(result))

    assert rebuilt == result
    with pytest.raises(FrozenInstanceError):
        value.catalyst_type = "other"
    with pytest.raises(FrozenInstanceError):
        result.catalyst_status = "rumor"
    with pytest.raises(ValueError, match="paper_only must be True"):
        catalyst_input(paper_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        build_strategy_event_catalyst_validation_v10(catalyst_input(readonly=False))
    with pytest.raises(ValueError, match="input must be a StrategyEventCatalystValidationV10Input"):
        build_strategy_event_catalyst_validation_v10(object())


def test_payload_rejects_unsafe_or_non_report_result_objects():
    unsafe = object.__new__(StrategyEventCatalystValidationV10Result)
    object.__setattr__(unsafe, "paper_only", False)
    object.__setattr__(unsafe, "report_only", True)
    object.__setattr__(unsafe, "readonly", True)

    with pytest.raises(ValueError, match="report must be a StrategyEventCatalystValidationV10Result"):
        strategy_event_catalyst_validation_v10_payload(object())
    with pytest.raises(ValueError, match="paper_only must be True"):
        strategy_event_catalyst_validation_v10_payload(unsafe)


def test_replace_revalidates_result_shape():
    result = build_result()

    with pytest.raises(ValueError, match="catalyst_status"):
        replace(result, catalyst_status="trade_now")
    with pytest.raises(ValueError, match="confidence_adjustment"):
        replace(result, confidence_adjustment=d("0.500000"))
