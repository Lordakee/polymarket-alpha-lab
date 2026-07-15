from __future__ import annotations

import importlib
import inspect
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal

import pytest


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.specialist_team_assignment_load_balance_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def report_input(
    *,
    team_count: Decimal = d("4"),
    overloaded_team_count: Decimal = d("0"),
    ready_team_count: Decimal = d("4"),
    queued_candidate_count: Decimal = d("0"),
    high_priority_candidate_count: Decimal = d("0"),
    average_review_lag_seconds: Decimal = d("120"),
    manual_review_capacity_ready: bool = True,
    supabase_memory_ready: bool = True,
):
    return api().SpecialistTeamAssignmentLoadBalanceInput(
        team_count=team_count,
        overloaded_team_count=overloaded_team_count,
        ready_team_count=ready_team_count,
        queued_candidate_count=queued_candidate_count,
        high_priority_candidate_count=high_priority_candidate_count,
        average_review_lag_seconds=average_review_lag_seconds,
        manual_review_capacity_ready=manual_review_capacity_ready,
        supabase_memory_ready=supabase_memory_ready,
    )


def build_report(**overrides):
    return api().build_specialist_team_assignment_load_balance_report(
        report_input(**overrides),
    )


def test_load_balance_report_marks_clean_capacity_ready() -> None:
    module = api()

    report = build_report()

    assert module.SPECIALIST_TEAM_ASSIGNMENT_LOAD_BALANCE_BANDS == (
        "ready",
        "attention",
        "blocked",
    )
    assert report.load_balance_ready is True
    assert report.load_balance_band == "ready"
    assert report.ready_ratio == d("1.000000")
    assert report.blocked_reason_codes == ()
    assert report.attention_reason_codes == ()

    payload = report.public_payload
    assert payload["team_count"] == "4.000000"
    assert payload["ready_ratio"] == "1.000000"
    assert payload["load_balance_ready"] is True
    assert payload["digest"] == report.digest
    assert payload == module.specialist_team_assignment_load_balance_report_public_payload(
        report,
    )
    assert report.digest == module.specialist_team_assignment_load_balance_report_digest(
        report,
    )
    assert _float_paths(payload) == ()
    json.dumps(payload, sort_keys=True)


def test_load_balance_report_surfaces_attention_without_blocking() -> None:
    report = build_report(
        team_count=d("4"),
        overloaded_team_count=d("1"),
        ready_team_count=d("3"),
        queued_candidate_count=d("6"),
        high_priority_candidate_count=d("2"),
        average_review_lag_seconds=d("1200"),
    )

    assert report.load_balance_ready is False
    assert report.load_balance_band == "attention"
    assert report.ready_ratio == d("0.750000")
    assert report.blocked_reason_codes == ()
    assert report.attention_reason_codes == (
        "specialist_team_assignment_overloaded_teams_attention",
        "specialist_team_assignment_candidate_queue_attention",
        "specialist_team_assignment_high_priority_queue_attention",
        "specialist_team_assignment_review_lag_attention",
    )


def test_load_balance_report_blocks_when_required_readiness_is_absent() -> None:
    report = build_report(
        team_count=d("2"),
        overloaded_team_count=d("2"),
        ready_team_count=d("0"),
        queued_candidate_count=d("3"),
        high_priority_candidate_count=d("1"),
        average_review_lag_seconds=d("1800"),
        manual_review_capacity_ready=False,
        supabase_memory_ready=False,
    )

    assert report.load_balance_ready is False
    assert report.load_balance_band == "blocked"
    assert report.ready_ratio == d("0.000000")
    assert report.blocked_reason_codes == (
        "specialist_team_assignment_no_ready_teams_blocked",
        "specialist_team_assignment_all_teams_overloaded_blocked",
        "specialist_team_assignment_manual_review_capacity_blocked",
        "specialist_team_assignment_supabase_memory_blocked",
    )
    assert report.attention_reason_codes == (
        "specialist_team_assignment_candidate_queue_attention",
        "specialist_team_assignment_high_priority_queue_attention",
        "specialist_team_assignment_review_lag_attention",
    )

    empty_report = build_report(
        team_count=d("0"),
        overloaded_team_count=d("0"),
        ready_team_count=d("0"),
    )
    assert empty_report.load_balance_band == "blocked"
    assert empty_report.ready_ratio == d("0.000000")
    assert empty_report.blocked_reason_codes == (
        "specialist_team_assignment_no_teams_blocked",
    )


def test_load_balance_contract_is_frozen_decimal_only_and_readonly() -> None:
    module = api()

    assert module.__all__ == (
        "DEFAULT_SPECIALIST_TEAM_ASSIGNMENT_LOAD_BALANCE_CONFIG_VERSION",
        "SPECIALIST_TEAM_ASSIGNMENT_LOAD_BALANCE_BANDS",
        "SpecialistTeamAssignmentLoadBalanceInput",
        "SpecialistTeamAssignmentLoadBalanceReport",
        "build_specialist_team_assignment_load_balance_report",
        "specialist_team_assignment_load_balance_report_digest",
        "specialist_team_assignment_load_balance_report_public_payload",
    )
    for exported_name in module.__all__:
        value = getattr(module, exported_name)
        if isinstance(value, type):
            assert is_dataclass(value)
            assert value.__dataclass_params__.frozen is True

    load_balance_input = report_input()
    report = module.build_specialist_team_assignment_load_balance_report(load_balance_input)
    for value in (load_balance_input, report):
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True
        for field in fields(value):
            item = getattr(value, field.name)
            if field.name in {
                "paper_only",
                "report_only",
                "readonly",
                "manual_review_capacity_ready",
                "supabase_memory_ready",
                "load_balance_ready",
                "load_balance_band",
                "blocked_reason_codes",
                "attention_reason_codes",
                "config_version",
            }:
                continue
            assert type(item) is Decimal

    with pytest.raises(FrozenInstanceError):
        report.load_balance_band = "blocked"  # type: ignore[misc]
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="team_count must be a Decimal"):
        report_input(team_count=4)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="average_review_lag_seconds must be a Decimal"):
        report_input(average_review_lag_seconds=120.0)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="manual_review_capacity_ready must be a bool"):
        report_input(manual_review_capacity_ready=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="ready_team_count must be less than or equal"):
        report_input(team_count=d("2"), ready_team_count=d("3"))
    with pytest.raises(ValueError, match="high_priority_candidate_count"):
        report_input(
            queued_candidate_count=d("1"),
            high_priority_candidate_count=d("2"),
        )
    with pytest.raises(ValueError, match="ready_ratio must match"):
        replace(report, ready_ratio=d("0.500000"))

    module_source = inspect.getsource(module).lower()
    for forbidden in (
        "create_client",
        "insert(",
        "upsert(",
        "delete(",
        "requests.",
        "httpx",
        "live_trading",
        "place_order",
        "cancel_order",
        "wallet",
    ):
        assert forbidden not in module_source


def _float_paths(value: object, path: str = "") -> tuple[str, ...]:
    if type(value) is float:
        return (path or "<root>",)
    if isinstance(value, dict):
        found: list[str] = []
        for key, item in value.items():
            found.extend(_float_paths(item, f"{path}.{key}" if path else str(key)))
        return tuple(found)
    if isinstance(value, list):
        found = []
        for index, item in enumerate(value):
            found.extend(_float_paths(item, f"{path}[{index}]"))
        return tuple(found)
    return ()
