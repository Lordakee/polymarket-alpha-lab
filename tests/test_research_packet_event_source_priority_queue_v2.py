from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pytest


GENERATED_AT = datetime(2026, 7, 6, 17, 0, tzinfo=UTC)


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_packet_event_source_priority_queue_v2",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def packet(
    packet_id: str,
    *,
    event_slug: str = "state-certification-calendar",
    event_velocity_per_hour: str = "1.000000",
    official_source_count: str = "2",
    independent_source_family_count: str = "4",
    contradiction_severity_score: str = "0.000000",
    probability_movement_24h: str = "0.005000",
    resolution_horizon_minutes: str = "4320.000000",
    specialist_uncertainty_score: str = "0.100000",
):
    queue = api()
    return queue.ResearchPacketEventSourcePriorityQueueV2Input(
        packet_id=packet_id,
        event_slug=event_slug,
        event_velocity_per_hour=d(event_velocity_per_hour),
        official_source_count=d(official_source_count),
        independent_source_family_count=d(independent_source_family_count),
        contradiction_severity_score=d(contradiction_severity_score),
        probability_movement_24h=d(probability_movement_24h),
        resolution_horizon_minutes=d(resolution_horizon_minutes),
        specialist_uncertainty_score=d(specialist_uncertainty_score),
    )


def report(*packets):
    queue = api()
    return queue.build_research_packet_event_source_priority_queue_v2_report(
        packets,
        config=queue.ResearchPacketEventSourcePriorityQueueV2Config(),
        generated_at=GENERATED_AT,
    )


def test_prioritizes_source_collection_pressure_with_decimal_rows() -> None:
    priority_report = report(
        packet("pkt-low", event_slug="routine-calendar-check"),
        packet(
            "pkt-high",
            event_slug="central-bank-emergency-meeting",
            event_velocity_per_hour="12.000000",
            official_source_count="0",
            independent_source_family_count="0",
            contradiction_severity_score="0.900000",
            probability_movement_24h="0.120000",
            resolution_horizon_minutes="30.000000",
            specialist_uncertainty_score="0.800000",
        ),
        packet(
            "pkt-medium",
            event_slug="court-filing-deadline",
            event_velocity_per_hour="4.000000",
            official_source_count="1",
            independent_source_family_count="2",
            contradiction_severity_score="0.300000",
            probability_movement_24h="0.030000",
            resolution_horizon_minutes="360.000000",
            specialist_uncertainty_score="0.350000",
        ),
    )

    assert is_dataclass(priority_report)
    assert priority_report.generated_at == GENERATED_AT
    assert priority_report.config_version == (
        "research-packet-event-source-priority-queue-v2"
    )
    assert priority_report.packet_count == d("3")
    assert priority_report.high_priority_packet_count == d("1")
    assert priority_report.medium_priority_packet_count == d("1")
    assert priority_report.low_priority_packet_count == d("1")
    assert priority_report.official_source_gap_count == d("2")
    assert priority_report.source_family_gap_count == d("2")
    assert priority_report.contradiction_severity_count == d("1")
    assert priority_report.probability_movement_count == d("1")
    assert priority_report.near_resolution_horizon_count == d("2")
    assert priority_report.specialist_uncertainty_count == d("1")
    assert priority_report.max_priority_score == d("0.969000")
    assert priority_report.report_status == "high_priority"
    assert priority_report.reason_codes == (
        "source_priority_high_present",
        "event_velocity_high",
        "official_source_gap_present",
        "source_family_gap_present",
        "contradiction_severity_high",
        "probability_movement_high",
        "resolution_horizon_near",
        "specialist_uncertainty_high",
    )
    assert priority_report.paper_only is True
    assert priority_report.report_only is True
    assert priority_report.readonly is True
    assert len(priority_report.derived_validation_digest) == 64

    assert tuple(row.packet_id for row in priority_report.rows) == (
        "pkt-high",
        "pkt-medium",
        "pkt-low",
    )
    high = priority_report.rows[0]
    assert high.row_rank == d("1")
    assert high.official_source_gap == d("2")
    assert high.source_family_gap == d("4")
    assert high.event_velocity_pressure == d("1.000000")
    assert high.official_source_gap_pressure == d("1.000000")
    assert high.source_family_independence_pressure == d("1.000000")
    assert high.contradiction_pressure == d("0.900000")
    assert high.probability_movement_pressure == d("1.000000")
    assert high.resolution_horizon_pressure == d("1.000000")
    assert high.specialist_uncertainty_pressure == d("0.800000")
    assert high.priority_score == d("0.969000")
    assert high.priority_tier == "high"
    assert high.reason_codes == (
        "source_priority_high",
        "event_velocity_high",
        "official_source_gap_present",
        "source_family_gap_present",
        "contradiction_severity_high",
        "probability_movement_high",
        "resolution_horizon_near",
        "specialist_uncertainty_high",
    )


def test_payload_serializes_decimals_as_strings_and_rejects_tampering() -> None:
    queue = api()
    priority_report = report(
        packet(
            "pkt-high",
            event_velocity_per_hour="12.000000",
            official_source_count="0",
            independent_source_family_count="0",
            contradiction_severity_score="0.900000",
            probability_movement_24h="0.120000",
            resolution_horizon_minutes="30.000000",
            specialist_uncertainty_score="0.800000",
        ),
    )

    payload = queue.research_packet_event_source_priority_queue_v2_report_payload(
        priority_report,
    )

    assert payload["packet_count"] == "1"
    assert payload["high_priority_packet_count"] == "1"
    assert payload["max_priority_score"] == "0.969000"
    assert payload["rows"][0]["official_source_gap"] == "2"
    assert payload["rows"][0]["priority_score"] == "0.969000"
    assert payload["rows"][0]["paper_only"] is True
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["derived_validation_digest"] == (
        priority_report.derived_validation_digest
    )
    assert not any(type(value) in (float, int) for value in _walk_payload_values(payload))

    tampered = dict(payload)
    tampered["packet_count"] = "2"
    with pytest.raises(ValueError, match="derived_validation_digest mismatch"):
        queue.research_packet_event_source_priority_queue_v2_report_payload(tampered)

    tampered_row_payload = dict(payload)
    tampered_row_payload["rows"] = [dict(payload["rows"][0])]
    tampered_row_payload["rows"][0]["priority_score"] = "0.100000"
    with pytest.raises(ValueError, match="derived_validation_digest mismatch"):
        queue.research_packet_event_source_priority_queue_v2_report_payload(
            tampered_row_payload,
        )

    with pytest.raises(ValueError, match="derived_validation_digest mismatch"):
        replace(priority_report, derived_validation_digest="0" * 64)


def test_inputs_are_decimal_only_frozen_unique_and_hard_flagged() -> None:
    queue = api()

    with pytest.raises(ValueError, match="event_velocity_per_hour must be a Decimal"):
        queue.ResearchPacketEventSourcePriorityQueueV2Input(
            packet_id="pkt-int",
            event_slug="calendar-check",
            event_velocity_per_hour=1,
            official_source_count=d("2"),
            independent_source_family_count=d("4"),
            contradiction_severity_score=d("0.000000"),
            probability_movement_24h=d("0.005000"),
            resolution_horizon_minutes=d("4320.000000"),
            specialist_uncertainty_score=d("0.100000"),
        )

    with pytest.raises(ValueError, match="resolution_horizon_minutes must be >= 0"):
        packet("pkt-negative", resolution_horizon_minutes="-1.000000")

    with pytest.raises(ValueError, match="inputs must not contain duplicate packet_id"):
        report(packet("pkt-dupe"), packet("pkt-dupe"))

    item = packet("pkt-frozen")
    with pytest.raises(FrozenInstanceError):
        item.packet_id = "pkt-edited"  # type: ignore[misc]

    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(item, paper_only=False)

    with pytest.raises(ValueError, match="paper_only must be True"):
        queue.ResearchPacketEventSourcePriorityQueueV2Config(paper_only=False)

    with pytest.raises(ValueError, match="weights must sum to 1.000000"):
        queue.ResearchPacketEventSourcePriorityQueueV2Config(
            event_velocity_weight=d("0.100000"),
        )


def test_public_payload_rejects_unsafe_keys_and_values() -> None:
    queue = api()

    for unsafe_value in (
        "live refresh",
        "auth token",
        "wallet check",
        "order book",
        "network call",
        "database row",
        "persist this",
        "signing request",
        "mutation path",
        "buy signal",
        "sell signal",
        "trade action",
    ):
        with pytest.raises(ValueError, match="unsafe public value"):
            packet("pkt-unsafe", event_slug=unsafe_value)

    payload = queue.research_packet_event_source_priority_queue_v2_report_payload(
        report(packet("pkt-clear")),
    )
    for unsafe_key in (
        "live_mode",
        "auth_token",
        "wallet_address",
        "order_id",
        "network_client",
        "database_url",
        "persist_path",
        "signing_key",
        "mutation_name",
        "buy_flag",
        "sell_flag",
        "trade_id",
    ):
        unsafe_payload = dict(payload)
        unsafe_payload[unsafe_key] = "redacted"
        with pytest.raises(ValueError, match="unsafe public key"):
            queue.research_packet_event_source_priority_queue_v2_report_payload(
                unsafe_payload,
            )

    unsafe_payload = dict(payload)
    unsafe_payload["review_note"] = "auth token"
    with pytest.raises(ValueError, match="unsafe public value"):
        queue.research_packet_event_source_priority_queue_v2_report_payload(
            unsafe_payload,
        )


def test_module_has_no_external_side_effect_or_float_surface() -> None:
    source = Path(
        "src/polymarket_alpha_lab/research_packet_event_source_priority_queue_v2.py",
    ).read_text(encoding="utf-8")
    tree = ast.parse(source)

    forbidden_import_roots = {
        "requests",
        "httpx",
        "urllib",
        "socket",
        "sqlite3",
        "sqlalchemy",
        "psycopg",
        "web3",
        "eth_account",
    }
    forbidden_calls = {
        "connect",
        "execute",
        "open",
        "post",
        "put",
        "request",
        "send",
        "sign",
    }

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in forbidden_import_roots
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".")[0] not in forbidden_import_roots
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in forbidden_calls
            assert node.func.id != "float"


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
