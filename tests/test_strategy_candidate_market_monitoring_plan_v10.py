from __future__ import annotations

import ast
import inspect
import json
from dataclasses import FrozenInstanceError, is_dataclass, replace
from decimal import Decimal

import pytest

from polymarket_alpha_lab import strategy_candidate_market_monitoring_plan_v10 as plan_module
from polymarket_alpha_lab.strategy_candidate_market_monitoring_plan_v10 import (
    StrategyCandidateMarketMonitoringPlanV10Config,
    StrategyCandidateMarketMonitoringPlanV10Input,
    StrategyCandidateMarketMonitoringPlanV10Payload,
    StrategyCandidateMarketMonitoringPlanV10Result,
    build_strategy_candidate_market_monitoring_plan_v10_result,
    plan_strategy_candidate_market_monitoring_v10,
    strategy_candidate_market_monitoring_plan_v10_payload,
)


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> StrategyCandidateMarketMonitoringPlanV10Config:
    values = {
        "config_version": "strategy-candidate-market-monitoring-plan-v10",
        "tier_1_review_minutes": d("240.000000"),
        "tier_2_review_minutes": d("720.000000"),
        "tier_3_review_minutes": d("1440.000000"),
        "watch_review_minutes": d("60.000000"),
        "urgent_review_minutes": d("30.000000"),
        "blocked_review_minutes": d("1440.000000"),
        "near_resolution_minutes": d("180.000000"),
        "minimum_resolution_minutes": d("30.000000"),
        "watch_team_capacity_score": d("0.500000"),
        "minimum_team_capacity_score": d("0.250000"),
        "watch_market_move_bps": d("75.000000"),
    }
    values.update(overrides)
    return StrategyCandidateMarketMonitoringPlanV10Config(**values)


def candidate(**overrides: object) -> StrategyCandidateMarketMonitoringPlanV10Input:
    values = {
        "market_id": "market-alpha",
        "candidate_status": "accepted",
        "watchlist_tier": "tier_1",
        "edge_status": "positive",
        "source_refresh_status": "fresh",
        "time_to_resolution_minutes": d("1440.000000"),
        "team_capacity_score": d("0.800000"),
        "market_move_bps": d("20.000000"),
    }
    values.update(overrides)
    return StrategyCandidateMarketMonitoringPlanV10Input(**values)


def result(
    candidate_row: StrategyCandidateMarketMonitoringPlanV10Input | None = None,
    *,
    cfg: StrategyCandidateMarketMonitoringPlanV10Config | None = None,
) -> StrategyCandidateMarketMonitoringPlanV10Result:
    return build_strategy_candidate_market_monitoring_plan_v10_result(
        candidate_row or candidate(),
        config=cfg or config(),
    )


def test_clear_candidate_returns_readonly_monitoring_plan_payload() -> None:
    plan = result()

    assert is_dataclass(plan)
    assert plan.monitoring_status == "monitor"
    assert plan.monitoring_actions == ("continue_readonly_monitoring",)
    assert plan.next_review_minutes == d("240.000000")
    assert plan.reason_codes == ("candidate_market_monitoring_clear",)
    assert plan.paper_only is True
    assert plan.report_only is True
    assert plan.readonly is True

    assert plan.payload.market_id == "market-alpha"
    assert plan.payload.watchlist_tier == "tier_1"
    assert plan.payload.absolute_market_move_bps == d("20.000000")
    assert type(plan.payload.team_capacity_score) is Decimal

    payload = strategy_candidate_market_monitoring_plan_v10_payload(plan)
    assert payload == plan.payload_json
    assert payload["monitoring_status"] == "monitor"
    assert payload["monitoring_actions"] == ["continue_readonly_monitoring"]
    assert payload["next_review_minutes"] == "240.000000"
    assert payload["payload"]["team_capacity_score"] == "0.800000"
    json.dumps(payload, sort_keys=True)
    assert not _contains_float(payload)


def test_watch_candidate_accelerates_review_for_refresh_edge_move_and_timing() -> None:
    plan = result(
        candidate(
            edge_status="weakening",
            source_refresh_status="stale",
            time_to_resolution_minutes=d("120.000000"),
            team_capacity_score=d("0.400000"),
            market_move_bps=d("-80.000000"),
        ),
    )

    assert plan.monitoring_status == "watch"
    assert plan.monitoring_actions == (
        "refresh_sources_before_review",
        "review_edge_decay",
        "review_market_move",
        "increase_cadence_near_resolution",
        "rebalance_team_capacity",
    )
    assert plan.next_review_minutes == d("30.000000")
    assert plan.reason_codes == (
        "candidate_source_refresh_stale_watch",
        "candidate_edge_status_weakening_watch",
        "candidate_market_move_watch",
        "candidate_near_resolution_watch",
        "candidate_team_capacity_watch",
    )
    assert plan.payload.market_move_bps == d("-80.000000")
    assert plan.payload.absolute_market_move_bps == d("80.000000")


def test_blocked_candidate_reports_reasons_and_review_hold() -> None:
    plan = result(
        candidate(
            candidate_status="blocked",
            watchlist_tier="none",
            edge_status="negative",
            source_refresh_status="blocked",
            time_to_resolution_minutes=d("10.000000"),
            team_capacity_score=d("0.100000"),
            market_move_bps=d("5.000000"),
        ),
    )

    assert plan.monitoring_status == "blocked"
    assert plan.monitoring_actions == (
        "hold_readonly_monitoring_until_candidate_reopens",
        "remove_from_active_readonly_watchlist",
        "defer_until_edge_recovers",
        "repair_source_refresh_before_review",
        "archive_resolution_too_close",
        "defer_until_capacity_recovers",
    )
    assert plan.next_review_minutes == d("1440.000000")
    assert plan.reason_codes == (
        "candidate_status_blocked_blocked",
        "candidate_not_watchlisted_blocked",
        "candidate_edge_negative_blocked",
        "candidate_source_refresh_blocked",
        "candidate_resolution_window_too_short_blocked",
        "candidate_team_capacity_below_floor_blocked",
    )


def test_direct_function_accepts_required_input_surface() -> None:
    plan = plan_strategy_candidate_market_monitoring_v10(
        market_id="market-direct",
        candidate_status="researching",
        watchlist_tier="tier_2",
        edge_status="flat",
        source_refresh_status="fresh",
        time_to_resolution_minutes=d("960.000000"),
        team_capacity_score=d("0.700000"),
        market_move_bps=d("40.000000"),
    )

    assert plan.monitoring_status == "watch"
    assert plan.monitoring_actions == (
        "review_edge_decay",
        "complete_candidate_research_check",
    )
    assert plan.next_review_minutes == d("60.000000")
    assert plan.payload.market_id == "market-direct"


def test_dataclasses_are_frozen_and_numeric_fields_are_decimal_only() -> None:
    cfg = config()
    candidate_row = candidate()
    plan = result(candidate_row, cfg=cfg)

    for dataclass_type in (
        StrategyCandidateMarketMonitoringPlanV10Config,
        StrategyCandidateMarketMonitoringPlanV10Input,
        StrategyCandidateMarketMonitoringPlanV10Payload,
        StrategyCandidateMarketMonitoringPlanV10Result,
    ):
        assert is_dataclass(dataclass_type)

    with pytest.raises(FrozenInstanceError):
        plan.monitoring_status = "blocked"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        plan.payload.team_capacity_score = d("0.000000")  # type: ignore[misc]

    decimal_fields_by_object = (
        (
            cfg,
            (
                "tier_1_review_minutes",
                "tier_2_review_minutes",
                "tier_3_review_minutes",
                "watch_review_minutes",
                "urgent_review_minutes",
                "blocked_review_minutes",
                "near_resolution_minutes",
                "minimum_resolution_minutes",
                "watch_team_capacity_score",
                "minimum_team_capacity_score",
                "watch_market_move_bps",
            ),
        ),
        (
            candidate_row,
            (
                "time_to_resolution_minutes",
                "team_capacity_score",
                "market_move_bps",
            ),
        ),
        (
            plan.payload,
            (
                "time_to_resolution_minutes",
                "team_capacity_score",
                "market_move_bps",
                "absolute_market_move_bps",
            ),
        ),
        (plan, ("next_review_minutes",)),
    )
    for item, field_names in decimal_fields_by_object:
        for field_name in field_names:
            assert type(getattr(item, field_name)) is Decimal
        for field_name, value in item.__dict__.items():
            assert type(value) not in (int, float), field_name


def test_validation_rejects_bad_inputs_flags_and_inconsistent_objects() -> None:
    with pytest.raises(ValueError, match="market_id"):
        candidate(market_id=" market-alpha")
    with pytest.raises(ValueError, match="candidate_status"):
        candidate(candidate_status="pending")
    with pytest.raises(ValueError, match="watchlist_tier"):
        candidate(watchlist_tier="tier_4")
    with pytest.raises(ValueError, match="edge_status"):
        candidate(edge_status="unknown")
    with pytest.raises(ValueError, match="source_refresh_status"):
        candidate(source_refresh_status="unknown")
    with pytest.raises(ValueError, match="time_to_resolution_minutes"):
        candidate(time_to_resolution_minutes=d("-0.000001"))
    with pytest.raises(ValueError, match="team_capacity_score"):
        candidate(team_capacity_score=d("1.000001"))
    with pytest.raises(ValueError, match="market_move_bps"):
        candidate(market_move_bps=_DecimalSubclass("1.000000"))
    with pytest.raises(ValueError, match="paper_only"):
        candidate(paper_only=False)
    with pytest.raises(ValueError, match="review cadence"):
        config(urgent_review_minutes=d("120.000000"))
    with pytest.raises(ValueError, match="candidate must be"):
        build_strategy_candidate_market_monitoring_plan_v10_result(
            object(),  # type: ignore[arg-type]
            config=config(),
        )
    with pytest.raises(ValueError, match="readonly"):
        replace(result(), readonly=False)
    with pytest.raises(ValueError, match="monitoring_status"):
        replace(result(), monitoring_status="blocked")


def test_payload_rejects_flag_downgrades_and_unsafe_public_text() -> None:
    with pytest.raises(ValueError, match="readonly"):
        strategy_candidate_market_monitoring_plan_v10_payload(
            {
                "monitoring_status": "monitor",
                "paper_only": True,
                "report_only": True,
                "readonly": False,
            },
        )

    with pytest.raises(ValueError, match="unsafe"):
        candidate(market_id="market-" + "wal" "let")

    with pytest.raises(ValueError, match="unsafe"):
        strategy_candidate_market_monitoring_plan_v10_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "summary": "contains " + "sign" + "al surface",
            },
        )


def test_module_surface_stays_report_only_without_external_side_effects() -> None:
    source = inspect.getsource(plan_module)
    tree = ast.parse(source)
    imported_modules: set[str] = set()
    call_names: set[str] = set()
    float_literals: list[float] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
        elif isinstance(node, ast.Call):
            function = node.func
            if isinstance(function, ast.Name):
                call_names.add(function.id)
            elif isinstance(function, ast.Attribute):
                call_names.add(function.attr)
        elif isinstance(node, ast.Constant) and isinstance(node.value, float):
            float_literals.append(node.value)

    forbidden_imports = {
        "os",
        "pathlib",
        "subprocess",
        "requests",
        "httpx",
        "urllib",
        "sqlite3",
        "psycopg",
    }
    forbidden_calls = {
        "connect",
        "cursor",
        "execute",
        "executemany",
        "commit",
        "rollback",
        "open",
        "urlopen",
        "submit_" + "order",
        "cancel_" + "order",
        "sign_" + "order",
        "place_" + "order",
    }
    forbidden_fragments = (
        "li" "ve",
        "trad" "ing",
        "au" "th",
        "wal" "let",
        "or" "der",
        "sign",
        "private" "_" "key",
        "bro" "ker",
        "database",
        "persist",
        "network",
    )

    assert imported_modules.isdisjoint(forbidden_imports)
    assert call_names.isdisjoint(forbidden_calls)
    assert float_literals == []
    assert all(fragment not in source.lower() for fragment in forbidden_fragments)


def _contains_float(value: object) -> bool:
    if isinstance(value, float):
        return True
    if isinstance(value, dict):
        return any(_contains_float(item) for item in value.values())
    if isinstance(value, list):
        return any(_contains_float(item) for item in value)
    return False
