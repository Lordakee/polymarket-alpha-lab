from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import pytest


GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_packet_live_information_gap_detector_v2",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def packet(
    packet_id: str,
    *,
    event_title: str = "Election certification timing",
    latest_source_at: datetime | None = GENERATED_AT - timedelta(minutes=10),
    latest_official_source_at: datetime | None = GENERATED_AT - timedelta(minutes=8),
    event_velocity_score: str = "0.200000",
    contradiction_count: str = "0",
    market_probability_movement: str = "0.010000",
    resolution_at: datetime = GENERATED_AT + timedelta(days=3),
):
    gap = api()
    return gap.ResearchPacketLiveInformationGapInput(
        packet_id=packet_id,
        event_title=event_title,
        latest_source_at=latest_source_at,
        latest_official_source_at=latest_official_source_at,
        event_velocity_score=d(event_velocity_score),
        contradiction_count=d(contradiction_count),
        market_probability_movement=d(market_probability_movement),
        resolution_at=resolution_at,
    )


def report(*packets):
    gap = api()
    return gap.build_research_packet_live_information_gap_report(
        packets,
        config=gap.ResearchPacketLiveInformationGapConfig(),
        generated_at=GENERATED_AT,
    )


def test_report_flags_fast_moving_stale_missing_conflicting_packets() -> None:
    gap_report = report(
        packet(
            "pkt-clear",
            event_title="State certification calendar",
        ),
        packet(
            "pkt-urgent",
            event_title="Central bank emergency meeting",
            latest_source_at=GENERATED_AT - timedelta(hours=2),
            latest_official_source_at=GENERATED_AT - timedelta(hours=1),
            event_velocity_score="0.900000",
            contradiction_count="2",
            market_probability_movement="0.120000",
            resolution_at=GENERATED_AT + timedelta(hours=2),
        ),
        packet(
            "pkt-missing-official",
            event_title="Court filing deadline",
            latest_official_source_at=None,
            event_velocity_score="0.720000",
            contradiction_count="0",
            market_probability_movement="0.020000",
            resolution_at=GENERATED_AT + timedelta(days=2),
        ),
    )

    assert is_dataclass(gap_report)
    assert gap_report.generated_at == GENERATED_AT
    assert gap_report.config_version == "research-packet-live-information-gap-v2"
    assert gap_report.packet_count == d("3")
    assert gap_report.pass_packet_count == d("1")
    assert gap_report.watch_packet_count == d("0")
    assert gap_report.blocked_packet_count == d("2")
    assert gap_report.missing_source_count == d("0")
    assert gap_report.missing_official_source_count == d("1")
    assert gap_report.stale_source_count == d("1")
    assert gap_report.stale_official_source_count == d("1")
    assert gap_report.contradiction_gap_count == d("1")
    assert gap_report.market_probability_movement_gap_count == d("1")
    assert gap_report.near_resolution_count == d("1")
    assert gap_report.max_information_gap_score == d("1.000000")
    assert gap_report.max_source_age_seconds == d("7200")
    assert gap_report.min_resolution_horizon_seconds == d("7200")
    assert gap_report.report_status == "blocked"
    assert gap_report.reason_codes == (
        "information_gap_blocked",
        "official_source_missing",
        "source_stale",
        "official_source_stale",
        "contradiction_count_elevated",
        "market_probability_moved",
        "resolution_horizon_near",
    )
    assert gap_report.paper_only is True
    assert gap_report.report_only is True
    assert gap_report.readonly is True
    assert len(gap_report.derived_validation_digest) == 64

    assert tuple(row.packet_id for row in gap_report.rows) == (
        "pkt-urgent",
        "pkt-missing-official",
        "pkt-clear",
    )
    urgent = gap_report.rows[0]
    assert urgent.source_age_seconds == d("7200")
    assert urgent.official_source_age_seconds == d("3600")
    assert urgent.resolution_horizon_seconds == d("7200")
    assert urgent.information_gap_score == d("1.000000")
    assert urgent.gap_status == "blocked"
    assert urgent.reason_codes == (
        "source_stale",
        "official_source_stale",
        "event_velocity_high",
        "contradiction_count_elevated",
        "market_probability_moved",
        "resolution_horizon_near",
    )

    missing = gap_report.rows[1]
    assert missing.official_source_age_seconds is None
    assert missing.reason_codes == ("official_source_missing", "event_velocity_high")


def test_payload_is_json_ready_decimal_string_and_digest_checked() -> None:
    gap = api()
    gap_report = report(
        packet(
            "pkt-urgent",
            latest_source_at=GENERATED_AT - timedelta(hours=2),
            latest_official_source_at=GENERATED_AT - timedelta(hours=1),
            event_velocity_score="0.900000",
            contradiction_count="2",
            market_probability_movement="0.120000",
            resolution_at=GENERATED_AT + timedelta(hours=2),
        ),
    )

    payload = gap.research_packet_live_information_gap_report_payload(gap_report)

    assert payload["packet_count"] == "1"
    assert payload["blocked_packet_count"] == "1"
    assert payload["max_information_gap_score"] == "1.000000"
    assert payload["rows"][0]["event_velocity_score"] == "0.900000"
    assert payload["rows"][0]["source_age_seconds"] == "7200"
    assert payload["rows"][0]["paper_only"] is True
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["derived_validation_digest"] == gap_report.derived_validation_digest

    tampered = dict(payload)
    tampered["packet_count"] = "2"
    with pytest.raises(ValueError, match="derived_validation_digest mismatch"):
        gap.research_packet_live_information_gap_report_payload(tampered)

    tampered_row_payload = dict(payload)
    tampered_row_payload["rows"] = [dict(payload["rows"][0])]
    tampered_row_payload["rows"][0]["event_velocity_score"] = "0.100000"
    with pytest.raises(ValueError, match="derived_validation_digest mismatch"):
        gap.research_packet_live_information_gap_report_payload(tampered_row_payload)

    with pytest.raises(ValueError, match="derived_validation_digest mismatch"):
        replace(gap_report, packet_count=d("2"))

    with pytest.raises(ValueError, match="derived_validation_digest mismatch"):
        replace(gap_report.rows[0], event_velocity_score=d("0.100000"))


def test_inputs_validate_decimal_datetime_flags_duplicates_and_mutation() -> None:
    gap = api()

    with pytest.raises(ValueError, match="event_velocity_score must be a Decimal"):
        gap.ResearchPacketLiveInformationGapInput(
            packet_id="pkt-float",
            event_title="Calendar update",
            latest_source_at=GENERATED_AT,
            latest_official_source_at=GENERATED_AT,
            event_velocity_score=0.5,
            contradiction_count=d("0"),
            market_probability_movement=d("0.010000"),
            resolution_at=GENERATED_AT + timedelta(days=1),
        )

    with pytest.raises(ValueError, match="latest_source_at must be timezone-aware"):
        packet("pkt-naive", latest_source_at=datetime(2026, 7, 6, 11, 0))

    normalized = report(
        packet(
            "pkt-offset",
            latest_source_at=datetime(
                2026,
                7,
                6,
                9,
                0,
                tzinfo=timezone(timedelta(hours=-2)),
            ),
        ),
    )
    assert normalized.rows[0].latest_source_at == GENERATED_AT - timedelta(hours=1)

    with pytest.raises(ValueError, match="timestamps must not be after generated_at"):
        report(packet("pkt-future", latest_source_at=GENERATED_AT + timedelta(seconds=1)))

    with pytest.raises(ValueError, match="resolution_at must not be before generated_at"):
        report(packet("pkt-expired", resolution_at=GENERATED_AT - timedelta(seconds=1)))

    with pytest.raises(ValueError, match="inputs must not contain duplicate packet_id"):
        report(packet("pkt-dupe"), packet("pkt-dupe"))

    item = packet("pkt-frozen")
    with pytest.raises(FrozenInstanceError):
        item.packet_id = "pkt-edited"  # type: ignore[misc]

    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(item, paper_only=False)

    with pytest.raises(ValueError, match="paper_only must be True"):
        gap.ResearchPacketLiveInformationGapConfig(paper_only=False)


def test_public_payload_rejects_unsafe_keys_and_values() -> None:
    gap = api()

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

    with pytest.raises(ValueError, match="unsafe public key"):
        gap.research_packet_live_information_gap_report_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "wallet_reference": "redacted",
            },
        )


def test_module_has_no_network_persistence_or_float_surface() -> None:
    source = Path(
        "src/polymarket_alpha_lab/research_packet_live_information_gap_detector_v2.py",
    ).read_text(encoding="utf-8")
    tree = ast.parse(source)

    forbidden_import_roots = {
        "requests",
        "httpx",
        "urllib",
        "socket",
        "sqlite3",
        "sqlalchemy",
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
