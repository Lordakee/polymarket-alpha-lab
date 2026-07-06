from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import pytest


GENERATED_AT = datetime(2026, 7, 6, 16, 0, tzinfo=UTC)


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_packet_event_velocity_change_detector_v2",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def packet(
    packet_id: str,
    *,
    event_title: str = "Election certification timing",
    previous_probability: str = "0.420000",
    current_probability: str = "0.440000",
    previous_source_arrivals_24h: str = "2",
    current_source_arrivals_24h: str = "3",
    last_market_update_at: datetime | None = GENERATED_AT - timedelta(minutes=12),
    latest_official_source_update_at: datetime | None = GENERATED_AT
    - timedelta(minutes=18),
    previous_contradiction_count: str = "0",
    current_contradiction_count: str = "0",
    previous_resolution_horizon_seconds: str = "172800",
    current_resolution_horizon_seconds: str = "165600",
    previous_liquidity: str = "12000.000000",
    current_liquidity: str = "12300.000000",
):
    velocity = api()
    return velocity.ResearchPacketEventVelocityChangeInput(
        packet_id=packet_id,
        event_title=event_title,
        previous_probability=d(previous_probability),
        current_probability=d(current_probability),
        previous_source_arrivals_24h=d(previous_source_arrivals_24h),
        current_source_arrivals_24h=d(current_source_arrivals_24h),
        last_market_update_at=last_market_update_at,
        latest_official_source_update_at=latest_official_source_update_at,
        previous_contradiction_count=d(previous_contradiction_count),
        current_contradiction_count=d(current_contradiction_count),
        previous_resolution_horizon_seconds=d(previous_resolution_horizon_seconds),
        current_resolution_horizon_seconds=d(current_resolution_horizon_seconds),
        previous_liquidity=d(previous_liquidity),
        current_liquidity=d(current_liquidity),
    )


def report(*packets):
    velocity = api()
    return velocity.build_research_packet_event_velocity_change_report(
        packets,
        config=velocity.ResearchPacketEventVelocityChangeConfig(),
        generated_at=GENERATED_AT,
    )


def test_detects_event_velocity_changes_and_sorts_highest_pressure_first() -> None:
    velocity_report = report(
        packet("pkt-clear", event_title="State certification calendar"),
        packet(
            "pkt-urgent",
            event_title="Central bank emergency meeting",
            previous_probability="0.390000",
            current_probability="0.510000",
            previous_source_arrivals_24h="2",
            current_source_arrivals_24h="7",
            last_market_update_at=GENERATED_AT - timedelta(minutes=5),
            latest_official_source_update_at=GENERATED_AT - timedelta(hours=1),
            previous_contradiction_count="0",
            current_contradiction_count="2",
            previous_resolution_horizon_seconds="28800",
            current_resolution_horizon_seconds="7200",
            previous_liquidity="10000.000000",
            current_liquidity="12600.000000",
        ),
        packet(
            "pkt-liquidity",
            event_title="Court filing deadline",
            previous_probability="0.600000",
            current_probability="0.630000",
            previous_source_arrivals_24h="1",
            current_source_arrivals_24h="4",
            previous_liquidity="5000.000000",
            current_liquidity="6500.000000",
        ),
    )

    assert is_dataclass(velocity_report)
    assert velocity_report.generated_at == GENERATED_AT
    assert velocity_report.config_version == "research-packet-event-velocity-change-v2"
    assert velocity_report.packet_count == d("3")
    assert velocity_report.pass_packet_count == d("1")
    assert velocity_report.watch_packet_count == d("1")
    assert velocity_report.blocked_packet_count == d("1")
    assert velocity_report.probability_movement_count == d("1")
    assert velocity_report.source_arrival_rate_increase_count == d("2")
    assert velocity_report.official_source_update_lag_count == d("1")
    assert velocity_report.contradiction_delta_count == d("1")
    assert velocity_report.resolution_horizon_compression_count == d("1")
    assert velocity_report.near_resolution_horizon_count == d("1")
    assert velocity_report.liquidity_movement_count == d("2")
    assert velocity_report.max_event_velocity_change_score == d("0.950000")
    assert velocity_report.max_official_source_update_lag_seconds == d("3300")
    assert velocity_report.min_current_resolution_horizon_seconds == d("7200")
    assert velocity_report.report_status == "blocked"
    assert velocity_report.reason_codes == (
        "event_velocity_change_blocked",
        "probability_movement_material",
        "source_arrival_rate_increased",
        "official_source_update_lagged",
        "contradiction_delta_elevated",
        "resolution_horizon_compressed",
        "resolution_horizon_near",
        "liquidity_movement_material",
    )
    assert velocity_report.paper_only is True
    assert velocity_report.report_only is True
    assert velocity_report.readonly is True
    assert len(velocity_report.derived_validation_digest) == 64

    assert tuple(row.packet_id for row in velocity_report.rows) == (
        "pkt-urgent",
        "pkt-liquidity",
        "pkt-clear",
    )
    urgent = velocity_report.rows[0]
    assert urgent.probability_move == d("0.120000")
    assert urgent.absolute_probability_move == d("0.120000")
    assert urgent.source_arrival_delta_24h == d("5")
    assert urgent.official_source_update_lag_seconds == d("3300")
    assert urgent.contradiction_delta == d("2")
    assert urgent.resolution_horizon_compression_seconds == d("21600")
    assert urgent.liquidity_move == d("2600.000000")
    assert urgent.absolute_liquidity_move == d("2600.000000")
    assert urgent.event_velocity_change_score == d("0.950000")
    assert urgent.velocity_change_status == "blocked"
    assert urgent.reason_codes == (
        "probability_movement_material",
        "source_arrival_rate_increased",
        "official_source_update_lagged",
        "contradiction_delta_elevated",
        "resolution_horizon_compressed",
        "resolution_horizon_near",
        "liquidity_movement_material",
    )


def test_payload_serializes_decimals_as_strings_and_rejects_tampering() -> None:
    velocity = api()
    velocity_report = report(
        packet(
            "pkt-urgent",
            previous_probability="0.390000",
            current_probability="0.510000",
            previous_source_arrivals_24h="2",
            current_source_arrivals_24h="7",
            last_market_update_at=GENERATED_AT - timedelta(minutes=5),
            latest_official_source_update_at=GENERATED_AT - timedelta(hours=1),
            previous_contradiction_count="0",
            current_contradiction_count="2",
            previous_resolution_horizon_seconds="28800",
            current_resolution_horizon_seconds="7200",
            previous_liquidity="10000.000000",
            current_liquidity="12600.000000",
        ),
    )

    payload = velocity.research_packet_event_velocity_change_report_payload(
        velocity_report,
    )

    assert payload["packet_count"] == "1"
    assert payload["blocked_packet_count"] == "1"
    assert payload["max_event_velocity_change_score"] == "0.950000"
    assert payload["rows"][0]["probability_move"] == "0.120000"
    assert payload["rows"][0]["current_liquidity"] == "12600.000000"
    assert payload["rows"][0]["paper_only"] is True
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["derived_validation_digest"] == velocity_report.derived_validation_digest
    assert not any(
        isinstance(value, float)
        or (isinstance(value, int) and not isinstance(value, bool))
        for value in _walk_payload_values(payload)
    )

    tampered = dict(payload)
    tampered["packet_count"] = "2"
    with pytest.raises(ValueError, match="derived_validation_digest mismatch"):
        velocity.research_packet_event_velocity_change_report_payload(tampered)

    tampered_row_payload = dict(payload)
    tampered_row_payload["rows"] = [dict(payload["rows"][0])]
    tampered_row_payload["rows"][0]["probability_move"] = "0.010000"
    with pytest.raises(ValueError, match="derived_validation_digest mismatch"):
        velocity.research_packet_event_velocity_change_report_payload(
            tampered_row_payload,
        )

    with pytest.raises(ValueError, match="derived_validation_digest mismatch"):
        replace(velocity_report, packet_count=d("2"))

    with pytest.raises(ValueError, match="derived_validation_digest mismatch"):
        replace(velocity_report.rows[0], probability_move=d("0.010000"))


def test_inputs_are_decimal_only_timezone_aware_frozen_and_hard_flagged() -> None:
    velocity = api()

    with pytest.raises(ValueError, match="previous_probability must be a Decimal"):
        velocity.ResearchPacketEventVelocityChangeInput(
            packet_id="pkt-float",
            event_title="Calendar update",
            previous_probability=0.42,
            current_probability=d("0.440000"),
            previous_source_arrivals_24h=d("2"),
            current_source_arrivals_24h=d("3"),
            last_market_update_at=GENERATED_AT,
            latest_official_source_update_at=GENERATED_AT,
            previous_contradiction_count=d("0"),
            current_contradiction_count=d("0"),
            previous_resolution_horizon_seconds=d("172800"),
            current_resolution_horizon_seconds=d("165600"),
            previous_liquidity=d("12000.000000"),
            current_liquidity=d("12300.000000"),
        )

    with pytest.raises(ValueError, match="last_market_update_at must be timezone-aware"):
        packet("pkt-naive", last_market_update_at=datetime(2026, 7, 6, 15, 0))

    normalized = report(
        packet(
            "pkt-offset",
            last_market_update_at=datetime(
                2026,
                7,
                6,
                9,
                0,
                tzinfo=timezone(timedelta(hours=-6)),
            ),
        ),
    )
    assert normalized.rows[0].last_market_update_at == GENERATED_AT - timedelta(hours=1)

    with pytest.raises(ValueError, match="timestamps must not be after generated_at"):
        report(
            packet(
                "pkt-future",
                latest_official_source_update_at=GENERATED_AT + timedelta(seconds=1),
            ),
        )

    with pytest.raises(ValueError, match="current_resolution_horizon_seconds"):
        packet(
            "pkt-expired",
            previous_resolution_horizon_seconds="3600",
            current_resolution_horizon_seconds="-1",
        )

    with pytest.raises(ValueError, match="inputs must not contain duplicate packet_id"):
        report(packet("pkt-dupe"), packet("pkt-dupe"))

    item = packet("pkt-frozen")
    with pytest.raises(FrozenInstanceError):
        item.packet_id = "pkt-edited"  # type: ignore[misc]

    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(item, paper_only=False)

    with pytest.raises(ValueError, match="paper_only must be True"):
        velocity.ResearchPacketEventVelocityChangeConfig(paper_only=False)


def test_public_payload_rejects_unsafe_keys_and_values() -> None:
    velocity = api()

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
            packet("pkt-unsafe", event_title=unsafe_value)

    payload = velocity.research_packet_event_velocity_change_report_payload(
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
            velocity.research_packet_event_velocity_change_report_payload(
                unsafe_payload,
            )


def test_module_has_no_external_side_effect_or_float_surface() -> None:
    source = Path(
        "src/polymarket_alpha_lab/research_packet_event_velocity_change_detector_v2.py",
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
