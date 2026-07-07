from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)
OBSERVED_AT = datetime(2026, 7, 6, 11, 0, tzinfo=UTC)
RESOLUTION_DEADLINE_AT = datetime(2026, 7, 7, 0, 0, tzinfo=UTC)
MODULE_NAME = "polymarket_alpha_lab.research_packet_urgent_source_collection_plan_v2"


class DerivedDatetime(datetime):
    pass


class DerivedDecimal(Decimal):
    pass


class NoneOffsetTimezone(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


def module() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def cfg(**overrides: object) -> Any:
    report_module = module()
    values = {
        "config_version": "research-packet-urgent-source-collection-plan-v2-test",
        "high_event_velocity_score": d("0.700000"),
        "high_market_probability_move_24h": d("0.080000"),
        "required_official_source_count": d("2.000000"),
        "max_source_age_seconds": d("3600.000000"),
        "urgent_resolution_horizon_seconds": d("86400.000000"),
        "high_contradiction_severity_score": d("0.500000"),
        "high_specialist_uncertainty_score": d("0.400000"),
        "collect_now_urgency_score": d("0.700000"),
        "collect_soon_urgency_score": d("0.400000"),
    }
    values.update(overrides)
    return report_module.ResearchPacketUrgentSourceCollectionPlanV2Config(**values)


def packet(**overrides: object) -> Any:
    report_module = module()
    values = {
        "event_slug": "btc-resolution-packet",
        "condition_id": "condition-alpha",
        "packet_id": "packet-alpha",
        "observed_at": OBSERVED_AT,
        "resolution_deadline_at": RESOLUTION_DEADLINE_AT,
        "event_velocity_score": d("0.100000"),
        "market_probability_move_24h": d("0.010000"),
        "official_source_count": d("2.000000"),
        "contradiction_severity_score": d("0.100000"),
        "newest_source_age_seconds": d("900.000000"),
        "source_freshness_exception_count": d("0.000000"),
        "specialist_uncertainty_score": d("0.100000"),
        "source_config_version": "research-packet-source-config-v1",
    }
    values.update(overrides)
    return report_module.ResearchPacketUrgentSourceCollectionPlanV2Packet(**values)


def build_report(*items: Any, generated_at: datetime = GENERATED_AT) -> Any:
    report_module = module()
    return report_module.build_research_packet_urgent_source_collection_plan_v2(
        items,
        config=cfg(),
        generated_at=generated_at,
    )


def test_builds_readonly_urgent_source_collection_plan_with_decimal_payload() -> None:
    report_module = module()
    report = build_report(
        packet(
            event_slug="urgent-event",
            condition_id="condition-urgent",
            packet_id="packet-urgent",
            event_velocity_score=d("0.900000"),
            market_probability_move_24h=d("0.200000"),
            official_source_count=d("0.000000"),
            contradiction_severity_score=d("0.800000"),
            newest_source_age_seconds=d("7200.000000"),
            source_freshness_exception_count=d("1.000000"),
            specialist_uncertainty_score=d("0.700000"),
        ),
        packet(
            event_slug="soon-event",
            condition_id="condition-soon",
            packet_id="packet-soon",
            observed_at=datetime(2026, 7, 6, 10, 0, tzinfo=UTC),
            resolution_deadline_at=datetime(2026, 7, 9, 12, 0, tzinfo=UTC),
            event_velocity_score=d("0.700000"),
            market_probability_move_24h=d("0.080000"),
            contradiction_severity_score=d("0.200000"),
            newest_source_age_seconds=d("1800.000000"),
            specialist_uncertainty_score=d("0.400000"),
        ),
        packet(
            event_slug="watch-event",
            condition_id="condition-watch",
            packet_id="packet-watch",
            observed_at=datetime(2026, 7, 6, 9, 0, tzinfo=UTC),
            resolution_deadline_at=datetime(2026, 7, 10, 12, 0, tzinfo=UTC),
            newest_source_age_seconds=d("5000.000000"),
        ),
        packet(
            event_slug="routine-event",
            condition_id="condition-routine",
            packet_id="packet-routine",
            observed_at=datetime(2026, 7, 6, 9, 30, tzinfo=UTC),
            resolution_deadline_at=datetime(2026, 7, 12, 12, 0, tzinfo=UTC),
        ),
    )

    assert report.generated_at == GENERATED_AT
    assert report.config_version == "research-packet-urgent-source-collection-plan-v2-test"
    assert report.input_count == d("4.000000")
    assert report.row_count == d("4.000000")
    assert report.collect_now_count == d("1.000000")
    assert report.collect_within_1h_count == d("1.000000")
    assert report.collect_within_6h_count == d("1.000000")
    assert report.monitor_next_cycle_count == d("1.000000")
    assert report.official_source_gap_count == d("1.000000")
    assert report.contradiction_severity_count == d("1.000000")
    assert report.source_freshness_exception_count == d("2.000000")
    assert report.urgent_resolution_horizon_count == d("1.000000")
    assert report.specialist_uncertainty_count == d("2.000000")
    assert report.max_urgency_score == d("0.890000")
    assert report.reason_codes == (
        "high_event_velocity",
        "market_probability_moved",
        "official_source_gap",
        "contradiction_severity_high",
        "source_freshness_exception",
        "resolution_horizon_urgent",
        "specialist_uncertainty_high",
    )
    assert len(report.derived_validation_digest) == 64
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple((row.collection_window, row.event_slug) for row in report.rows) == (
        ("collect_now", "urgent-event"),
        ("collect_within_1h", "soon-event"),
        ("collect_within_6h", "watch-event"),
        ("monitor_next_cycle", "routine-event"),
    )

    urgent, soon, watch, routine = report.rows
    assert urgent.urgency_score == d("0.890000")
    assert urgent.official_source_gap == d("2.000000")
    assert urgent.resolution_horizon_seconds == d("43200.000000")
    assert urgent.reason_codes == (
        "high_event_velocity",
        "market_probability_moved",
        "official_source_gap",
        "contradiction_severity_high",
        "source_freshness_exception",
        "resolution_horizon_urgent",
        "specialist_uncertainty_high",
    )
    assert soon.urgency_score == d("0.470000")
    assert watch.urgency_score == d("0.153571")
    assert routine.urgency_score == d("0.097321")
    assert routine.reason_codes == ("source_collection_monitor",)

    payload = report_module.research_packet_urgent_source_collection_plan_v2_payload(report)
    assert payload["generated_at"] == "2026-07-06T12:00:00+00:00"
    assert payload["input_count"] == "4.000000"
    assert payload["max_urgency_score"] == "0.890000"
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert payload["rows"][0]["urgency_score"] == "0.890000"
    assert payload["rows"][2]["resolution_horizon_seconds"] == "345600.000000"
    assert report_module.validate_research_packet_urgent_source_collection_plan_v2_payload(payload)
    assert_no_public_numeric(payload)
    json.dumps(payload, allow_nan=False, sort_keys=True)


def test_empty_and_routine_inputs_are_deterministic_readonly_reports() -> None:
    empty = build_report()
    assert empty.input_count == d("0.000000")
    assert empty.row_count == d("0.000000")
    assert empty.collect_now_count == d("0.000000")
    assert empty.monitor_next_cycle_count == d("0.000000")
    assert empty.average_urgency_score == d("0.000000")
    assert empty.max_urgency_score == d("0.000000")
    assert empty.reason_codes == ("source_collection_plan_empty",)
    assert empty.rows == ()
    assert len(empty.derived_validation_digest) == 64

    routine = build_report(
        packet(event_slug="event-beta", condition_id="condition-beta", packet_id="packet-beta"),
        packet(event_slug="event-alpha", condition_id="condition-alpha", packet_id="packet-alpha"),
    )

    assert routine.input_count == d("2.000000")
    assert routine.collect_now_count == d("0.000000")
    assert routine.monitor_next_cycle_count == d("2.000000")
    assert routine.reason_codes == ("source_collection_plan_monitor",)
    assert tuple(row.event_slug for row in routine.rows) == ("event-alpha", "event-beta")


def test_aware_datetimes_normalize_to_utc_and_deadline_floor_is_urgent() -> None:
    eastern = timezone(timedelta(hours=-4))
    report = build_report(
        packet(
            event_slug="timezone-event",
            observed_at=datetime(2026, 7, 6, 7, 0, tzinfo=eastern),
            resolution_deadline_at=datetime(2026, 7, 6, 7, 30, tzinfo=eastern),
            official_source_count=d("1.000000"),
        ),
    )

    row = report.rows[0]
    assert row.observed_at == datetime(2026, 7, 6, 11, 0, tzinfo=UTC)
    assert row.resolution_deadline_at == datetime(2026, 7, 6, 11, 30, tzinfo=UTC)
    assert row.packet_age_seconds == d("3600.000000")
    assert row.resolution_horizon_seconds == d("0.000000")
    assert row.collection_window == "collect_within_1h"
    assert "resolution_horizon_urgent" in row.reason_codes

    payload = module().research_packet_urgent_source_collection_plan_v2_payload(report)
    assert payload["rows"][0]["observed_at"] == "2026-07-06T11:00:00+00:00"
    assert payload["rows"][0]["resolution_deadline_at"] == "2026-07-06T11:30:00+00:00"
    assert payload["rows"][0]["packet_age_seconds"] == "3600.000000"
    assert_no_public_numeric(payload)


def test_dataclasses_are_frozen_decimal_only_and_reject_subclassing() -> None:
    report_module = module()

    assert report_module.__all__ == (
        "DEFAULT_RESEARCH_PACKET_URGENT_SOURCE_COLLECTION_PLAN_V2_CONFIG_VERSION",
        "ResearchPacketUrgentSourceCollectionPlanV2Config",
        "ResearchPacketUrgentSourceCollectionPlanV2Packet",
        "ResearchPacketUrgentSourceCollectionPlanV2Row",
        "ResearchPacketUrgentSourceCollectionPlanV2Report",
        "build_research_packet_urgent_source_collection_plan_v2",
        "research_packet_urgent_source_collection_plan_v2_payload",
        "validate_research_packet_urgent_source_collection_plan_v2_payload",
    )
    for exported_name in report_module.__all__:
        value = getattr(report_module, exported_name)
        if isinstance(value, type):
            assert is_dataclass(value)

    report = build_report(packet())
    for item in (cfg(), packet(), report, *report.rows):
        for field in fields(item):
            value = getattr(item, field.name)
            assert type(value) is not float
            if (
                field.name.endswith("_count")
                or field.name.endswith("_score")
                or field.name.endswith("_seconds")
                or field.name.endswith("_24h")
                or field.name == "official_source_gap"
            ):
                assert type(value) is Decimal

    with pytest.raises(FrozenInstanceError):
        report.rows[0].collection_window = "collect_now"  # type: ignore[misc]
    with pytest.raises(ValueError, match="event_velocity_score must be a Decimal"):
        packet(event_velocity_score=1)
    with pytest.raises(ValueError, match="high_event_velocity_score must be a Decimal"):
        cfg(high_event_velocity_score=DerivedDecimal("0.700000"))
    with pytest.raises(TypeError, match="subclassing"):

        class UnsafeConfig(report_module.ResearchPacketUrgentSourceCollectionPlanV2Config):
            pass

    with pytest.raises(TypeError, match="subclassing"):

        class UnsafePacket(report_module.ResearchPacketUrgentSourceCollectionPlanV2Packet):
            pass

    with pytest.raises(TypeError, match="subclassing"):

        class UnsafeRow(report_module.ResearchPacketUrgentSourceCollectionPlanV2Row):
            pass

    with pytest.raises(TypeError, match="subclassing"):

        class UnsafeReport(report_module.ResearchPacketUrgentSourceCollectionPlanV2Report):
            pass


def test_validation_rejects_dates_decimals_sequences_and_false_hard_flags() -> None:
    report_module = module()

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        report_module.build_research_packet_urgent_source_collection_plan_v2(
            (),
            config=cfg(),
            generated_at=datetime(2026, 7, 6, 12, 0),
        )
    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        report_module.build_research_packet_urgent_source_collection_plan_v2(
            (),
            config=cfg(),
            generated_at=DerivedDatetime(2026, 7, 6, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        packet(observed_at=datetime(2026, 7, 6, 11, 0))
    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        packet(observed_at=datetime(2026, 7, 6, 11, 0, tzinfo=NoneOffsetTimezone()))
    with pytest.raises(ValueError, match="resolution_deadline_at"):
        packet(resolution_deadline_at=datetime(2026, 7, 6, 10, 59, tzinfo=UTC))
    with pytest.raises(ValueError, match="generated_at"):
        build_report(packet(observed_at=datetime(2026, 7, 6, 13, 0, tzinfo=UTC)))
    with pytest.raises(ValueError, match="reason_codes"):
        replace(build_report(packet()).rows[0], reason_codes=("dup", "dup"))
    with pytest.raises(ValueError, match="collect_now_urgency_score"):
        cfg(collect_now_urgency_score=d("0.300000"), collect_soon_urgency_score=d("0.400000"))
    with pytest.raises(ValueError, match="paper_only must be True"):
        packet(paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        cfg(report_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        cfg(readonly=False)
    shifted = build_report(
        packet(),
        generated_at=datetime(2026, 7, 6, 5, 0, tzinfo=timezone(timedelta(hours=-7))),
    )
    assert shifted.generated_at == GENERATED_AT
    assert shifted.generated_at.tzinfo is UTC
    with pytest.raises(ValueError, match="packets"):
        report_module.build_research_packet_urgent_source_collection_plan_v2(
            "bad",
            config=cfg(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="config"):
        report_module.build_research_packet_urgent_source_collection_plan_v2(
            (packet(),),
            config=object(),
            generated_at=GENERATED_AT,
        )


def test_report_consistency_and_digest_are_tamper_evident() -> None:
    report_module = module()
    report = build_report(packet())

    with pytest.raises(ValueError, match="row_count"):
        replace(report, row_count=d("2.000000"))
    with pytest.raises(ValueError, match="collect_now_count"):
        replace(report, collect_now_count=d("1.000000"))
    with pytest.raises(ValueError, match="rows"):
        replace(report, rows=(report.rows[0], report.rows[0]))
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)

    payload = report_module.research_packet_urgent_source_collection_plan_v2_payload(report)
    tampered_payload = dict(payload)
    tampered_payload["input_count"] = "2.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        report_module.validate_research_packet_urgent_source_collection_plan_v2_payload(
            tampered_payload,
        )

    object.__setattr__(report.rows[0], "event_slug", "changed-event")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        report_module.research_packet_urgent_source_collection_plan_v2_payload(report)


def test_unsafe_public_keys_values_and_public_numbers_are_rejected() -> None:
    report_module = module()
    unsafe_terms = (
        "".join(("li", "ve")),
        "".join(("au", "th")),
        "".join(("wall", "et")),
        "".join(("or", "der")),
        "".join(("net", "work")),
        "".join(("data", "base")),
        "".join(("per", "sist")),
        "".join(("sign", "ing")),
        "".join(("muta", "tion")),
        "".join(("b", "uy")),
        "".join(("s", "ell")),
        "".join(("tr", "ade")),
    )

    for unsafe_term in unsafe_terms:
        with pytest.raises(ValueError, match="unsafe public surface"):
            packet(event_slug=f"event-{unsafe_term}")

    report = build_report(packet())
    payload = report_module.research_packet_urgent_source_collection_plan_v2_payload(report)

    unsafe_key_payload = dict(payload)
    unsafe_key_payload["".join(("wall", "et"))] = "forbidden"
    with pytest.raises(ValueError, match="unsafe public surface"):
        report_module.validate_research_packet_urgent_source_collection_plan_v2_payload(
            unsafe_key_payload,
        )

    unsafe_value_payload = dict(payload)
    unsafe_value_payload["note"] = "".join(("sign", "ing"))
    with pytest.raises(ValueError, match="unsafe public surface"):
        report_module.validate_research_packet_urgent_source_collection_plan_v2_payload(
            unsafe_value_payload,
        )

    numeric_payload = dict(payload)
    numeric_payload["input_count"] = 1
    with pytest.raises(ValueError, match="public payload"):
        report_module.validate_research_packet_urgent_source_collection_plan_v2_payload(
            numeric_payload,
        )


def test_module_omits_runtime_financial_action_and_storage_surfaces() -> None:
    source = Path(
        "src/polymarket_alpha_lab/research_packet_urgent_source_collection_plan_v2.py",
    ).read_text(encoding="utf-8")
    lowered = source.lower()

    for forbidden in (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "sqlite",
        "psycopg",
        "sqlalchemy",
        "aiohttp",
        "".join(("li", "ve")),
        "".join(("au", "th")),
        "".join(("wall", "et")),
        "".join(("or", "der")),
        "".join(("net", "work")),
        "".join(("data", "base")),
        "".join(("per", "sist")),
        "".join(("sign", "ing")),
        "".join(("muta", "tion")),
        "".join(("b", "uy")),
        "".join(("s", "ell")),
        "".join(("tr", "ade")),
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id != "float"


def assert_no_public_numeric(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError("payload must not contain floats")
    if type(value) is int:
        raise AssertionError("payload numeric values must be Decimal strings")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_public_numeric(item)
    if isinstance(value, list):
        for item in value:
            assert_no_public_numeric(item)
