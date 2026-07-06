from __future__ import annotations

import ast
import inspect
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from json import dumps

import pytest

import polymarket_alpha_lab.strategy_event_team_capacity_allocator_v10 as allocator_module
from polymarket_alpha_lab.strategy_event_team_capacity_allocator_v10 import (
    EventTeamCapacityAllocatorV10Candidate,
    EventTeamCapacityAllocatorV10Config,
    EventTeamCapacityAllocatorV10Report,
    EventTeamCapacityAllocatorV10Team,
    allocate_event_team_capacity_v10,
    event_team_capacity_allocator_v10_payload,
)


class DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def candidate(**overrides: object) -> EventTeamCapacityAllocatorV10Candidate:
    values = {
        "market_id": "fed-july-rate-cut",
        "category": "macro",
        "priority_score": d("0.900000"),
        "time_to_resolution_minutes": d("30"),
        "team_fit_score": d("0.850000"),
        "estimated_research_minutes": d("80"),
    }
    values.update(overrides)
    return EventTeamCapacityAllocatorV10Candidate(**values)


def team(**overrides: object) -> EventTeamCapacityAllocatorV10Team:
    values = {
        "capacity_minutes": d("150"),
        "trust_score": d("0.800000"),
    }
    values.update(overrides)
    return EventTeamCapacityAllocatorV10Team(**values)


def allocate(
    *items: EventTeamCapacityAllocatorV10Candidate,
    tm: EventTeamCapacityAllocatorV10Team | None = None,
    cfg: EventTeamCapacityAllocatorV10Config | None = None,
) -> EventTeamCapacityAllocatorV10Report:
    return allocate_event_team_capacity_v10(
        items,
        team=tm or team(),
        config=cfg or EventTeamCapacityAllocatorV10Config(),
    )


def test_event_team_capacity_allocator_v10_assigns_top_events_until_capacity_is_used() -> None:
    result = allocate(
        candidate(
            market_id="fed-july-rate-cut",
            category="macro",
            priority_score=d("0.900000"),
            time_to_resolution_minutes=d("30"),
            team_fit_score=d("0.850000"),
            estimated_research_minutes=d("80"),
        ),
        candidate(
            market_id="eth-etf-approval",
            category="crypto",
            priority_score=d("0.820000"),
            time_to_resolution_minutes=d("240"),
            team_fit_score=d("0.800000"),
            estimated_research_minutes=d("70"),
        ),
        candidate(
            market_id="nba-finals-game-7",
            category="sports",
            priority_score=d("0.700000"),
            time_to_resolution_minutes=d("120"),
            team_fit_score=d("0.400000"),
            estimated_research_minutes=d("60"),
        ),
    )

    assert result == EventTeamCapacityAllocatorV10Report(
        config_version="event-team-capacity-allocator-v10",
        allocation_status="partial",
        candidate_count=d("3"),
        assigned_count=d("2"),
        unassigned_count=d("1"),
        capacity_minutes=d("150"),
        allocated_minutes=d("150"),
        remaining_capacity_minutes=d("0"),
        trust_score=d("0.800000"),
        assigned_rows=result.assigned_rows,
        unassigned_market_ids=("nba-finals-game-7",),
        capacity_warnings=("capacity_fully_used", "capacity_constrained"),
        reason_codes=(
            "events_assigned",
            "events_unassigned",
            "capacity_fully_used",
            "capacity_constrained",
            "trust_score_sufficient",
        ),
    )
    assert tuple(row.market_id for row in result.assigned_rows) == (
        "fed-july-rate-cut",
        "eth-etf-approval",
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True

    macro, crypto = result.assigned_rows
    assert macro.category == "macro"
    assert macro.urgency_score == d("1.000000")
    assert macro.allocation_score == d("0.897500")
    assert macro.assigned_minutes == d("80")
    assert macro.remaining_capacity_minutes == d("70")
    assert macro.reason_codes == (
        "event_assigned",
        "priority_high",
        "resolution_window_immediate",
        "team_fit_strong",
        "trust_score_sufficient",
    )

    assert crypto.category == "crypto"
    assert crypto.urgency_score == d("0.666667")
    assert crypto.allocation_score == d("0.782333")
    assert crypto.assigned_minutes == d("70")
    assert crypto.remaining_capacity_minutes == d("0")
    assert crypto.reason_codes == (
        "event_assigned",
        "priority_high",
        "resolution_window_near",
        "team_fit_strong",
        "trust_score_sufficient",
    )


def test_event_team_capacity_allocator_v10_blocks_when_team_trust_is_too_low() -> None:
    result = allocate(
        candidate(market_id="fed-july-rate-cut"),
        candidate(market_id="eth-etf-approval", category="crypto"),
        tm=team(capacity_minutes=d("500"), trust_score=d("0.300000")),
    )

    assert result.allocation_status == "blocked"
    assert result.assigned_rows == ()
    assert result.unassigned_market_ids == ("fed-july-rate-cut", "eth-etf-approval")
    assert result.capacity_warnings == ("trust_score_below_minimum",)
    assert result.reason_codes == (
        "events_unassigned",
        "trust_score_below_minimum",
    )


def test_event_team_capacity_allocator_v10_empty_input_returns_readonly_report() -> None:
    result = allocate(tm=team(capacity_minutes=d("90"), trust_score=d("0.900000")))

    assert result.allocation_status == "empty"
    assert result.candidate_count == d("0")
    assert result.assigned_count == d("0")
    assert result.unassigned_count == d("0")
    assert result.allocated_minutes == d("0")
    assert result.remaining_capacity_minutes == d("90")
    assert result.assigned_rows == ()
    assert result.unassigned_market_ids == ()
    assert result.capacity_warnings == ()
    assert result.reason_codes == ("no_candidate_events", "trust_score_sufficient")
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True


def test_event_team_capacity_allocator_v10_payload_is_json_ready_decimal_only() -> None:
    result = allocate(candidate())
    payload = event_team_capacity_allocator_v10_payload(result)

    dumps(payload, sort_keys=True)
    assert result.payload == payload
    assert payload["config_version"] == "event-team-capacity-allocator-v10"
    assert payload["allocation_status"] == "assigned"
    assert payload["candidate_count"] == "1"
    assert payload["capacity_minutes"] == "150"
    assert payload["trust_score"] == "0.800000"
    assert payload["assigned_rows"][0]["market_id"] == "fed-july-rate-cut"
    assert payload["assigned_rows"][0]["allocation_score"] == "0.897500"
    assert payload["unassigned_market_ids"] == []
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    _assert_no_float_or_int(payload)


def test_event_team_capacity_allocator_v10_dataclasses_are_frozen_and_flag_locked() -> None:
    cfg = EventTeamCapacityAllocatorV10Config()
    item = candidate()
    tm = team()
    report = allocate(item, tm=tm, cfg=cfg)
    row = report.assigned_rows[0]

    for value in (cfg, item, tm, row, report):
        assert is_dataclass(value)
        assert value.__dataclass_params__.frozen
        with pytest.raises(FrozenInstanceError):
            value.paper_only = False  # type: ignore[misc]
        for field in fields(value):
            if field.name in {"paper_only", "report_only", "readonly"}:
                assert getattr(value, field.name) is True

    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(cfg, paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        replace(item, report_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(row, readonly=False)


def test_event_team_capacity_allocator_v10_validates_decimal_inputs_ranges_and_exact_types() -> None:
    with pytest.raises(ValueError, match="priority_score must be a Decimal"):
        candidate(priority_score=1)
    with pytest.raises(ValueError, match="team_fit_score must be a Decimal"):
        candidate(team_fit_score=0.8)
    with pytest.raises(ValueError, match="trust_score must be a Decimal"):
        team(trust_score=DecimalSubclass("0.800000"))
    with pytest.raises(ValueError, match="estimated_research_minutes must be a whole Decimal"):
        candidate(estimated_research_minutes=d("10.500000"))
    with pytest.raises(ValueError, match="time_to_resolution_minutes must be nonnegative"):
        candidate(time_to_resolution_minutes=d("-1"))
    with pytest.raises(ValueError, match="team_fit_score must be between"):
        candidate(team_fit_score=d("1.000001"))
    with pytest.raises(ValueError, match="capacity_minutes must be nonnegative"):
        team(capacity_minutes=d("-1"))
    with pytest.raises(ValueError, match="team must be an EventTeamCapacityAllocatorV10Team"):
        allocate_event_team_capacity_v10((candidate(),), team=object())  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="candidates must contain"):
        allocate_event_team_capacity_v10((object(),), team=team())  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="config must be an EventTeamCapacityAllocatorV10Config"):
        allocate_event_team_capacity_v10(
            (candidate(),),
            team=team(),
            config=object(),  # type: ignore[arg-type]
        )


def test_event_team_capacity_allocator_v10_rejects_inconsistent_manual_reports() -> None:
    valid = allocate(candidate())

    with pytest.raises(ValueError, match="assigned_count must equal assigned_rows count"):
        replace(valid, assigned_count=d("2"))
    with pytest.raises(ValueError, match="allocated_minutes must equal assigned row sum"):
        replace(valid, allocated_minutes=d("1"))
    with pytest.raises(ValueError, match="unassigned_count must equal unassigned ids count"):
        replace(valid, unassigned_count=d("1"))
    with pytest.raises(ValueError, match="allocation_status must match assignment state"):
        replace(valid, allocation_status="blocked")
    with pytest.raises(ValueError, match="report reason_codes must match"):
        replace(valid, reason_codes=("events_unassigned",))


def test_event_team_capacity_allocator_v10_public_numeric_annotations_are_decimal() -> None:
    decimal_fields = {
        "EventTeamCapacityAllocatorV10Config": {
            "immediate_resolution_minutes",
            "near_resolution_minutes",
            "minimum_assignment_score",
            "minimum_trust_score",
            "capacity_warning_threshold",
            "high_priority_score",
            "strong_team_fit_score",
            "priority_weight",
            "urgency_weight",
            "team_fit_weight",
            "trust_weight",
        },
        "EventTeamCapacityAllocatorV10Candidate": {
            "priority_score",
            "time_to_resolution_minutes",
            "team_fit_score",
            "estimated_research_minutes",
        },
        "EventTeamCapacityAllocatorV10Team": {
            "capacity_minutes",
            "trust_score",
        },
        "EventTeamCapacityAllocatorV10AssignedRow": {
            "priority_score",
            "time_to_resolution_minutes",
            "team_fit_score",
            "estimated_research_minutes",
            "urgency_score",
            "allocation_score",
            "assigned_minutes",
            "remaining_capacity_minutes",
        },
        "EventTeamCapacityAllocatorV10Report": {
            "candidate_count",
            "assigned_count",
            "unassigned_count",
            "capacity_minutes",
            "allocated_minutes",
            "remaining_capacity_minutes",
            "trust_score",
        },
    }

    for class_name, field_names in decimal_fields.items():
        annotations = getattr(allocator_module, class_name).__annotations__
        for field_name in field_names:
            assert annotations[field_name] == "Decimal"


def test_event_team_capacity_allocator_v10_has_no_live_trading_persistence_or_network_surface() -> None:
    source = inspect.getsource(allocator_module)
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
        "api_key",
        "auth",
        "database",
        "live_trading",
        "private_key",
        "signing",
        "submit_order",
        "wallet",
    ):
        assert token not in lowered

    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert not isinstance(node.value, float)


def _assert_no_float_or_int(value: object) -> None:
    if type(value) in (float, int):
        raise AssertionError(f"unexpected concrete numeric payload value: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_float_or_int(item)
    if isinstance(value, list):
        for item in value:
            _assert_no_float_or_int(item)
