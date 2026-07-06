from __future__ import annotations

from copy import deepcopy
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from polymarket_alpha_lab.research_packet_source_freshness_exception_gate_v2 import (
    CONTRADICTION_SEVERITY_EXCESSIVE_REASON,
    EVENT_VELOCITY_TOO_HIGH_REASON,
    FRESH_REASON,
    OFFICIAL_SOURCE_LAG_EXCESSIVE_REASON,
    PROBABILITY_MOVEMENT_EXCESSIVE_REASON,
    RESOLUTION_HORIZON_TOO_SHORT_REASON,
    SOURCE_FAMILY_RELIABILITY_LOW_REASON,
    STALE_TOLERATED_REASON,
    ResearchPacketSourceFreshnessExceptionGateV2Config,
    ResearchPacketSourceFreshnessExceptionGateV2Observation,
    build_research_packet_source_freshness_exception_gate_v2_report,
    research_packet_source_freshness_exception_gate_v2_payload,
)


GENERATED_AT = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)


def d(value: str) -> Decimal:
    return Decimal(value)


def config() -> ResearchPacketSourceFreshnessExceptionGateV2Config:
    return ResearchPacketSourceFreshnessExceptionGateV2Config(
        stale_source_age_seconds=d("3600.000000"),
        max_event_velocity_for_exception=d("0.600000"),
        max_official_source_lag_seconds=d("600.000000"),
        max_contradiction_severity_for_exception=d("0.200000"),
        max_probability_movement_for_exception=d("0.050000"),
        minimum_resolution_horizon_seconds=d("86400.000000"),
        minimum_source_family_reliability=d("0.800000"),
    )


def observation(
    packet_id: str,
    *,
    source_age_seconds: int,
    event_velocity: Decimal = d("0.200000"),
    official_source_lag_seconds: Decimal = d("120.000000"),
    contradiction_severity: Decimal = d("0.050000"),
    probability_movement: Decimal = d("0.010000"),
    resolution_horizon_seconds: Decimal = d("172800.000000"),
    source_family_reliability: Decimal = d("0.950000"),
    source_family: str = "official_report",
) -> ResearchPacketSourceFreshnessExceptionGateV2Observation:
    return ResearchPacketSourceFreshnessExceptionGateV2Observation(
        packet_id=packet_id,
        market_id=f"market_{packet_id}",
        source_family=source_family,
        source_observed_at=GENERATED_AT - timedelta(seconds=source_age_seconds),
        event_velocity=event_velocity,
        official_source_lag_seconds=official_source_lag_seconds,
        contradiction_severity=contradiction_severity,
        probability_movement=probability_movement,
        resolution_horizon_seconds=resolution_horizon_seconds,
        source_family_reliability=source_family_reliability,
    )


def walk_values(value: object) -> tuple[object, ...]:
    values: list[object] = []
    if isinstance(value, dict):
        for item in value.values():
            values.extend(walk_values(item))
    elif isinstance(value, list):
        for item in value:
            values.extend(walk_values(item))
    else:
        values.append(value)
    return tuple(values)


def build_mixed_report():
    return build_research_packet_source_freshness_exception_gate_v2_report(
        (
            observation("fresh", source_age_seconds=1200),
            observation("tolerated", source_age_seconds=7200),
            observation(
                "blocked",
                source_age_seconds=7200,
                event_velocity=d("0.900000"),
                official_source_lag_seconds=d("900.000000"),
                contradiction_severity=d("0.500000"),
                probability_movement=d("0.100000"),
                resolution_horizon_seconds=d("3600.000000"),
                source_family_reliability=d("0.500000"),
            ),
        ),
        generated_at=GENERATED_AT,
        config=config(),
    )


def test_gate_classifies_fresh_tolerated_and_blocked_stale_evidence() -> None:
    report = build_mixed_report()

    assert report.gate_status == "blocked"
    assert report.observation_count == d("3.000000")
    assert report.fresh_source_count == d("1.000000")
    assert report.stale_source_count == d("2.000000")
    assert report.tolerated_stale_source_count == d("1.000000")
    assert report.blocked_stale_source_count == d("1.000000")
    assert report.exception_ratio == d("0.333333")
    assert report.tolerated_stale_source_ratio == d("0.500000")
    assert report.max_source_age_seconds == d("7200.000000")

    rows_by_packet = {row.packet_id: row for row in report.rows}
    assert rows_by_packet["fresh"].source_freshness_status == "fresh"
    assert rows_by_packet["fresh"].reason_codes == (FRESH_REASON,)
    assert rows_by_packet["tolerated"].source_freshness_status == "stale_tolerated"
    assert rows_by_packet["tolerated"].stale_source_tolerated is True
    assert rows_by_packet["tolerated"].reason_codes == (STALE_TOLERATED_REASON,)
    assert rows_by_packet["blocked"].source_freshness_status == "stale_blocked"
    assert rows_by_packet["blocked"].reason_codes == (
        EVENT_VELOCITY_TOO_HIGH_REASON,
        OFFICIAL_SOURCE_LAG_EXCESSIVE_REASON,
        CONTRADICTION_SEVERITY_EXCESSIVE_REASON,
        PROBABILITY_MOVEMENT_EXCESSIVE_REASON,
        RESOLUTION_HORIZON_TOO_SHORT_REASON,
        SOURCE_FAMILY_RELIABILITY_LOW_REASON,
    )
    assert report.reason_codes == (
        EVENT_VELOCITY_TOO_HIGH_REASON,
        OFFICIAL_SOURCE_LAG_EXCESSIVE_REASON,
        CONTRADICTION_SEVERITY_EXCESSIVE_REASON,
        PROBABILITY_MOVEMENT_EXCESSIVE_REASON,
        RESOLUTION_HORIZON_TOO_SHORT_REASON,
        SOURCE_FAMILY_RELIABILITY_LOW_REASON,
        STALE_TOLERATED_REASON,
        FRESH_REASON,
    )


def test_empty_report_is_report_only_and_tamper_evident() -> None:
    report = build_research_packet_source_freshness_exception_gate_v2_report(
        (),
        generated_at=GENERATED_AT,
        config=config(),
    )

    assert report.gate_status == "empty"
    assert report.observation_count == d("0.000000")
    assert report.max_source_age_seconds == d("0.000000")
    assert len(report.derived_validation_digest) == 64
    assert all(character in "0123456789abcdef" for character in report.derived_validation_digest)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_public_payload_serializes_decimals_as_strings() -> None:
    report = build_mixed_report()
    payload = research_packet_source_freshness_exception_gate_v2_payload(report)

    assert payload["observation_count"] == "3.000000"
    assert payload["exception_ratio"] == "0.333333"
    assert payload["rows"][0]["source_age_seconds"] == "7200.000000"
    assert payload["rows"][0]["event_velocity"] == "0.900000"
    assert payload["reason_code_counts"][0]["count"] == "1.000000"
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert not any(type(value) is Decimal for value in walk_values(payload))
    assert not any(type(value) is float for value in walk_values(payload))

    assert research_packet_source_freshness_exception_gate_v2_payload(payload) == payload


def test_derived_validation_digest_rejects_tampered_report_and_payload() -> None:
    report = build_mixed_report()
    payload = research_packet_source_freshness_exception_gate_v2_payload(report)

    with pytest.raises(ValueError, match="derived_validation_digest must match"):
        replace(report, derived_validation_digest="0" * 64)

    tampered_payload = dict(payload)
    tampered_payload["gate_status"] = "pass"
    with pytest.raises(ValueError, match="derived_validation_digest must match"):
        research_packet_source_freshness_exception_gate_v2_payload(tampered_payload)

    missing_digest = dict(payload)
    missing_digest.pop("derived_validation_digest")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        research_packet_source_freshness_exception_gate_v2_payload(missing_digest)

    object.__setattr__(report.rows[0], "source_family_reliability", d("0.900000"))
    with pytest.raises(ValueError, match="derived_validation_digest must match"):
        research_packet_source_freshness_exception_gate_v2_payload(report)


def test_public_payload_rejects_unsafe_keys_and_values() -> None:
    payload = research_packet_source_freshness_exception_gate_v2_payload(build_mixed_report())
    unsafe_terms = (
        "live",
        "auth",
        "wallet",
        "order",
        "network",
        "database",
        "persist",
        "signing",
        "mutation",
        "buy",
        "sell",
        "trade",
    )

    for term in unsafe_terms:
        unsafe_key_payload = dict(payload)
        unsafe_key_payload[f"{term}_field"] = "redacted"
        with pytest.raises(ValueError, match="unsafe public field"):
            research_packet_source_freshness_exception_gate_v2_payload(unsafe_key_payload)

        unsafe_value_payload = deepcopy(payload)
        unsafe_value_payload["rows"][0]["market_id"] = f"{term} surface"
        with pytest.raises(ValueError, match="unsafe public value"):
            research_packet_source_freshness_exception_gate_v2_payload(unsafe_value_payload)


def test_hard_flags_and_decimal_only_inputs_are_required() -> None:
    with pytest.raises(ValueError, match="paper_only"):
        ResearchPacketSourceFreshnessExceptionGateV2Config(paper_only=False)

    with pytest.raises(ValueError, match="event_velocity must be a Decimal"):
        ResearchPacketSourceFreshnessExceptionGateV2Observation(
            packet_id="bad_decimal",
            market_id="market_bad_decimal",
            source_family="official_report",
            source_observed_at=GENERATED_AT,
            event_velocity=0.1,
            official_source_lag_seconds=d("0.000000"),
            contradiction_severity=d("0.000000"),
            probability_movement=d("0.000000"),
            resolution_horizon_seconds=d("1000.000000"),
            source_family_reliability=d("1.000000"),
        )

    payload = research_packet_source_freshness_exception_gate_v2_payload(build_mixed_report())
    missing_flag_payload = dict(payload)
    missing_flag_payload.pop("readonly")
    with pytest.raises(ValueError, match="readonly"):
        research_packet_source_freshness_exception_gate_v2_payload(missing_flag_payload)


def test_public_dataclasses_are_frozen_and_reject_subclassing() -> None:
    report = build_mixed_report()
    with pytest.raises(FrozenInstanceError):
        report.gate_status = "pass"

    with pytest.raises(TypeError, match="does not support subclassing"):
        class CustomConfig(ResearchPacketSourceFreshnessExceptionGateV2Config):
            pass


def test_future_source_observed_at_is_rejected() -> None:
    future_observation = observation("future", source_age_seconds=-1)
    with pytest.raises(ValueError, match="source_observed_at must not be in the future"):
        build_research_packet_source_freshness_exception_gate_v2_report(
            (future_observation,),
            generated_at=GENERATED_AT,
            config=config(),
        )
