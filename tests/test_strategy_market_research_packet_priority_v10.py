from __future__ import annotations

import ast
import inspect
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from json import dumps

import pytest

import polymarket_alpha_lab.strategy_market_research_packet_priority_v10 as priority_module
from polymarket_alpha_lab.strategy_market_research_packet_priority_v10 import (
    MarketResearchPacketPriorityV10Config,
    MarketResearchPacketPriorityV10Input,
    MarketResearchPacketPriorityV10Report,
    market_research_packet_priority_v10_payload,
    prioritize_market_research_packet_v10,
)


class DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def packet(**overrides: object) -> MarketResearchPacketPriorityV10Input:
    values = {
        "market_id": "fed-july-rate-above-four",
        "packet_status": "ready",
        "completeness_score": d("0.920000"),
        "information_edge_score": d("0.880000"),
        "time_to_resolution_minutes": d("240"),
        "team_capacity_score": d("0.800000"),
        "human_review_required": False,
        "source_gap_count": d("0"),
    }
    values.update(overrides)
    return MarketResearchPacketPriorityV10Input(**values)


def prioritize(
    item: MarketResearchPacketPriorityV10Input,
    *,
    cfg: MarketResearchPacketPriorityV10Config | None = None,
) -> MarketResearchPacketPriorityV10Report:
    return prioritize_market_research_packet_v10(
        item,
        config=cfg or MarketResearchPacketPriorityV10Config(),
    )


def test_market_research_packet_priority_v10_queues_urgent_ready_packet() -> None:
    result = prioritize(packet())

    assert result == MarketResearchPacketPriorityV10Report(
        config_version="market-research-packet-priority-v10",
        market_id="fed-july-rate-above-four",
        packet_status="ready",
        completeness_score=d("0.920000"),
        information_edge_score=d("0.880000"),
        time_to_resolution_minutes=d("240"),
        team_capacity_score=d("0.800000"),
        human_review_required=False,
        source_gap_count=d("0"),
        urgency_score=d("0.666667"),
        readiness_score=d("1.000000"),
        gap_penalty=d("0.000000"),
        review_penalty=d("0.000000"),
        priority_score=d("0.853333"),
        priority_status="urgent",
        queue_recommendation="front_of_queue",
        reason_codes=(
            "capacity_available",
            "completeness_high",
            "information_edge_high",
            "packet_ready",
            "priority_urgent",
            "resolution_window_near",
            "source_gaps_none",
        ),
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True


def test_market_research_packet_priority_v10_routes_review_packet_to_human_queue() -> None:
    result = prioritize(
        packet(
            packet_status="researching",
            completeness_score=d("0.650000"),
            information_edge_score=d("0.700000"),
            time_to_resolution_minutes=d("1200"),
            team_capacity_score=d("0.450000"),
            human_review_required=True,
            source_gap_count=d("2"),
        ),
    )

    assert result.priority_score == d("0.345000")
    assert result.priority_status == "review"
    assert result.queue_recommendation == "human_review_queue"
    assert result.reason_codes == (
        "capacity_constrained",
        "completeness_watch",
        "human_review_required",
        "information_edge_medium",
        "packet_in_progress",
        "priority_review",
        "resolution_window_normal",
        "source_gaps_present",
    )


def test_market_research_packet_priority_v10_blocks_incomplete_or_archived_packet() -> None:
    result = prioritize(
        packet(
            packet_status="archived",
            completeness_score=d("0.300000"),
            information_edge_score=d("0.200000"),
            time_to_resolution_minutes=d("30"),
            team_capacity_score=d("0.900000"),
            source_gap_count=d("4"),
        ),
    )

    assert result.priority_score == d("0.310000")
    assert result.priority_status == "blocked"
    assert result.queue_recommendation == "do_not_queue"
    assert result.reason_codes == (
        "capacity_available",
        "completeness_low",
        "information_edge_low",
        "packet_blocked_status",
        "priority_blocked",
        "resolution_window_immediate",
        "source_gaps_present",
    )


def test_market_research_packet_priority_v10_payload_is_json_ready_readonly_and_decimal_safe() -> None:
    result = prioritize(packet())
    payload = market_research_packet_priority_v10_payload(result)

    dumps(payload, sort_keys=True)
    assert result.payload == payload
    assert payload["config_version"] == "market-research-packet-priority-v10"
    assert payload["market_id"] == "fed-july-rate-above-four"
    assert payload["time_to_resolution_minutes"] == "240"
    assert payload["priority_score"] == "0.853333"
    assert payload["priority_status"] == "urgent"
    assert payload["queue_recommendation"] == "front_of_queue"
    assert payload["reason_codes"] == [
        "capacity_available",
        "completeness_high",
        "information_edge_high",
        "packet_ready",
        "priority_urgent",
        "resolution_window_near",
        "source_gaps_none",
    ]
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    _assert_no_float_or_int(payload)


def test_market_research_packet_priority_v10_validates_decimals_counts_status_and_flags() -> None:
    result = prioritize(packet())

    assert is_dataclass(result)
    assert result.__dataclass_params__.frozen
    with pytest.raises(FrozenInstanceError):
        result.priority_score = d("0.000000")  # type: ignore[misc]
    with pytest.raises(ValueError, match="completeness_score must be a Decimal"):
        packet(completeness_score=1)
    with pytest.raises(ValueError, match="information_edge_score must be a Decimal"):
        packet(information_edge_score=0.8)
    with pytest.raises(ValueError, match="team_capacity_score must be a Decimal"):
        packet(team_capacity_score=DecimalSubclass("0.800000"))
    with pytest.raises(ValueError, match="source_gap_count must be a whole Decimal"):
        packet(source_gap_count=d("1.500000"))
    with pytest.raises(ValueError, match="time_to_resolution_minutes must be nonnegative"):
        packet(time_to_resolution_minutes=d("-1"))
    with pytest.raises(ValueError, match="packet_status must be one of"):
        packet(packet_status="queued")
    with pytest.raises(ValueError, match="human_review_required must be a bool"):
        packet(human_review_required=1)
    with pytest.raises(ValueError, match="paper_only must be True"):
        packet(paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        MarketResearchPacketPriorityV10Config(report_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(result, readonly=False)


def test_market_research_packet_priority_v10_rejects_manual_inconsistent_outputs() -> None:
    valid = prioritize(packet())

    with pytest.raises(ValueError, match="priority_status must match priority_score"):
        replace(valid, priority_status="low")
    with pytest.raises(ValueError, match="queue_recommendation must match"):
        replace(valid, queue_recommendation="do_not_queue")
    with pytest.raises(ValueError, match="report reason_codes must match"):
        replace(valid, reason_codes=("priority_urgent",))
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(valid, readonly=False)


def test_market_research_packet_priority_v10_accepts_only_exact_input_and_config_types() -> None:
    with pytest.raises(
        ValueError,
        match="packet must be a MarketResearchPacketPriorityV10Input",
    ):
        prioritize_market_research_packet_v10(object())  # type: ignore[arg-type]
    with pytest.raises(
        ValueError,
        match="config must be a MarketResearchPacketPriorityV10Config",
    ):
        prioritize_market_research_packet_v10(
            packet(),
            config=object(),  # type: ignore[arg-type]
        )


def test_market_research_packet_priority_v10_public_numeric_annotations_are_decimal() -> None:
    decimal_fields = {
        "MarketResearchPacketPriorityV10Config": {
            "immediate_resolution_minutes",
            "near_resolution_minutes",
            "minimum_ready_completeness",
            "high_completeness_score",
            "high_information_edge_score",
            "medium_information_edge_score",
            "minimum_capacity_score",
            "high_priority_threshold",
            "review_priority_threshold",
            "completeness_weight",
            "information_edge_weight",
            "urgency_weight",
            "capacity_weight",
            "source_gap_penalty_weight",
            "human_review_penalty_weight",
        },
        "MarketResearchPacketPriorityV10Input": {
            "completeness_score",
            "information_edge_score",
            "time_to_resolution_minutes",
            "team_capacity_score",
            "source_gap_count",
        },
        "MarketResearchPacketPriorityV10Report": {
            "completeness_score",
            "information_edge_score",
            "time_to_resolution_minutes",
            "team_capacity_score",
            "source_gap_count",
            "urgency_score",
            "readiness_score",
            "gap_penalty",
            "review_penalty",
            "priority_score",
        },
    }

    for class_name, field_names in decimal_fields.items():
        annotations = getattr(priority_module, class_name).__annotations__
        for field_name in field_names:
            assert annotations[field_name] == "Decimal"


def test_market_research_packet_priority_v10_has_no_live_trading_persistence_or_network_surface() -> None:
    source = inspect.getsource(priority_module)
    tree = ast.parse(source)
    forbidden_import_roots = {
        "boto3",
        "http",
        "pathlib",
        "psycopg",
        "requests",
        "socket",
        "sqlite3",
        "urllib",
        "web3",
    }
    forbidden_calls = {
        "connect",
        "commit",
        "cursor",
        "execute",
        "open",
        "request",
        "send",
        "urlopen",
        "write",
    }

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in forbidden_import_roots
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".")[0] not in forbidden_import_roots
        if isinstance(node, ast.Call):
            function = node.func
            if isinstance(function, ast.Name):
                assert function.id not in forbidden_calls
            if isinstance(function, ast.Attribute):
                assert function.attr not in forbidden_calls
    lowered = source.lower()
    for token in (
        "auth",
        "database",
        "live trading",
        "order placement",
        "private_key",
        "signing",
        "wallet",
    ):
        assert token not in lowered


def _assert_no_float_or_int(value: object) -> None:
    if type(value) in (float, int):
        raise AssertionError(f"unexpected concrete numeric payload value: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_float_or_int(item)
    if isinstance(value, list):
        for item in value:
            _assert_no_float_or_int(item)
