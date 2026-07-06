from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

import pytest

import polymarket_alpha_lab.research_packet_source_latency_escalation_plan_v2 as module
from polymarket_alpha_lab.research_packet_source_latency_escalation_plan_v2 import (
    ResearchPacketSourceLatencyEscalationPlanV2Config,
    ResearchPacketSourceLatencyEscalationPlanV2Report,
    ResearchPacketSourceLatencyEscalationPlanV2Row,
    ResearchPacketSourceLatencyEscalationPlanV2Source,
    build_research_packet_source_latency_escalation_plan_v2,
    research_packet_source_latency_escalation_plan_v2_payload,
)


NOW = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)
UNSAFE_TERMS = (
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


def d(value: str) -> Decimal:
    return Decimal(value)


def source(
    source_id: str,
    *,
    age_seconds: int,
    base_priority_score: Decimal = d("0.100000"),
    source_confidence_score: Decimal = d("1.000000"),
    missed_recheck_count: Decimal = d("0.000000"),
) -> ResearchPacketSourceLatencyEscalationPlanV2Source:
    return ResearchPacketSourceLatencyEscalationPlanV2Source(
        packet_id=f"packet-{source_id}",
        source_id=source_id,
        source_family="official",
        observed_at=NOW - timedelta(seconds=age_seconds),
        base_priority_score=base_priority_score,
        source_confidence_score=source_confidence_score,
        missed_recheck_count=missed_recheck_count,
    )


def report(
    rows: tuple[ResearchPacketSourceLatencyEscalationPlanV2Source, ...] | None = None,
) -> ResearchPacketSourceLatencyEscalationPlanV2Report:
    if rows is None:
        rows = (
            source("calm", age_seconds=300),
            source(
                "stale",
                age_seconds=2_000,
                base_priority_score=d("0.300000"),
                source_confidence_score=d("0.900000"),
                missed_recheck_count=d("1.000000"),
            ),
            source(
                "critical",
                age_seconds=4_000,
                base_priority_score=d("0.250000"),
                source_confidence_score=d("0.400000"),
                missed_recheck_count=d("3.000000"),
            ),
        )
    return build_research_packet_source_latency_escalation_plan_v2(
        rows,
        generated_at=NOW,
        config=ResearchPacketSourceLatencyEscalationPlanV2Config(),
    )


def assert_no_float_or_decimal_payload_values(value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            assert type(key) is str
            assert_no_float_or_decimal_payload_values(item)
        return
    if isinstance(value, list):
        for item in value:
            assert_no_float_or_decimal_payload_values(item)
        return
    assert not isinstance(value, (Decimal, float, datetime))


def test_escalation_priority_orders_critical_sources_first() -> None:
    built = report()

    assert [row.source_id for row in built.rows] == ["critical", "stale", "calm"]
    assert [row.escalation_tier for row in built.rows] == [
        "critical",
        "escalate",
        "normal",
    ]
    assert built.rows[0].escalation_priority_score == d("1.000000")
    assert built.rows[0].escalation_priority_score > built.rows[1].escalation_priority_score
    assert built.rows[1].escalation_priority_score > built.rows[2].escalation_priority_score
    assert built.critical_count == d("1.000000")
    assert built.escalate_count == d("1.000000")


def test_stale_source_penalties_increase_with_source_age() -> None:
    built = report(
        (
            source("recent", age_seconds=300),
            source("warn", age_seconds=700),
            source("stale", age_seconds=2_000),
            source("critical", age_seconds=4_000),
        ),
    )
    rows_by_source = {row.source_id: row for row in built.rows}

    assert rows_by_source["recent"].stale_penalty_score == d("0.000000")
    assert rows_by_source["warn"].stale_penalty_score == d("0.150000")
    assert rows_by_source["stale"].stale_penalty_score == d("0.350000")
    assert rows_by_source["critical"].stale_penalty_score == d("0.600000")
    assert "source_latency_warn" in rows_by_source["warn"].reason_codes
    assert "source_latency_stale" in rows_by_source["stale"].reason_codes
    assert "source_latency_critical" in rows_by_source["critical"].reason_codes


def test_payload_serializes_decimals_as_strings_and_validates_round_trip() -> None:
    built = report()

    payload = research_packet_source_latency_escalation_plan_v2_payload(built)

    assert payload["config_version"] == "research-packet-source-latency-escalation-plan-v2"
    assert payload["row_count"] == "3.000000"
    assert payload["watch_count"] == "0.000000"
    assert payload["escalate_count"] == "1.000000"
    assert payload["critical_count"] == "1.000000"
    assert payload["max_escalation_priority_score"] == "1.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert isinstance(payload["rows"], list)
    assert payload["rows"][0]["source_age_seconds"] == "4000.000000"
    assert payload["rows"][0]["escalation_priority_score"] == "1.000000"
    assert len(payload["derived_validation_digest"]) == 64
    assert_no_float_or_decimal_payload_values(payload)
    assert research_packet_source_latency_escalation_plan_v2_payload(payload) == payload


def test_dataclasses_are_frozen_and_public_numeric_values_are_decimal_only() -> None:
    built = report()
    config = ResearchPacketSourceLatencyEscalationPlanV2Config()
    sample_source = source("sample", age_seconds=60)

    for instance in (config, sample_source, built, *built.rows):
        assert is_dataclass(instance)
        for field in fields(instance):
            value = getattr(instance, field.name)
            if isinstance(value, Decimal):
                assert type(value) is Decimal
            assert not isinstance(value, float)

    with pytest.raises(FrozenInstanceError):
        built.rows[0].source_id = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        config.config_version = "changed"  # type: ignore[misc]


def test_hard_phase_flags_are_required_on_all_public_records() -> None:
    built = report()

    assert built.paper_only is True
    assert built.report_only is True
    assert built.readonly is True
    assert built.rows[0].paper_only is True
    assert built.rows[0].report_only is True
    assert built.rows[0].readonly is True

    with pytest.raises(ValueError, match="paper_only must be True"):
        ResearchPacketSourceLatencyEscalationPlanV2Config(paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        source("bad-report-flag", age_seconds=60, missed_recheck_count=d("0.000000")).__class__(
            packet_id="packet-bad-report-flag",
            source_id="bad-report-flag",
            source_family="official",
            observed_at=NOW,
            base_priority_score=d("0.100000"),
            source_confidence_score=d("1.000000"),
            missed_recheck_count=d("0.000000"),
            report_only=False,
        )
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(built.rows[0], readonly=False)
    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(built, paper_only=False)


def test_derived_validation_digest_rejects_dataclass_and_payload_tampering() -> None:
    built = report()
    payload = research_packet_source_latency_escalation_plan_v2_payload(built)

    with pytest.raises(ValueError, match="derived_validation_digest must match"):
        replace(built.rows[0], escalation_priority_score=d("0.123456"))
    with pytest.raises(ValueError, match="derived_validation_digest must match"):
        replace(built, row_count=d("4.000000"))

    missing_digest = dict(payload)
    missing_digest.pop("derived_validation_digest")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        research_packet_source_latency_escalation_plan_v2_payload(missing_digest)

    tampered_payload = dict(payload)
    tampered_payload["row_count"] = "4.000000"
    with pytest.raises(ValueError, match="derived_validation_digest must match"):
        research_packet_source_latency_escalation_plan_v2_payload(tampered_payload)


def test_unsafe_public_payload_keys_and_values_are_rejected() -> None:
    payload = research_packet_source_latency_escalation_plan_v2_payload(report())

    for unsafe_term in UNSAFE_TERMS:
        unsafe_key_payload = dict(payload)
        unsafe_key_payload[f"{unsafe_term}_surface"] = "redacted"
        with pytest.raises(ValueError, match="unsafe"):
            research_packet_source_latency_escalation_plan_v2_payload(unsafe_key_payload)

        unsafe_value_payload = dict(payload)
        unsafe_value_payload["source_family_summary"] = f"{unsafe_term} surface"
        with pytest.raises(ValueError, match="unsafe"):
            research_packet_source_latency_escalation_plan_v2_payload(unsafe_value_payload)

    with pytest.raises(ValueError, match="unsafe"):
        source("wallet source", age_seconds=60)


def test_no_unsafe_surface_terms_are_exported_or_public_dataclass_fields() -> None:
    for public_name in module.__all__:
        lowered_name = public_name.lower()
        assert not any(term in lowered_name for term in UNSAFE_TERMS)
        public_value: Any = getattr(module, public_name)
        if isinstance(public_value, type) and is_dataclass(public_value):
            for field in fields(public_value):
                lowered_field = field.name.lower()
                assert not any(term in lowered_field for term in UNSAFE_TERMS)
