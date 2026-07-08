from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from pathlib import Path
from typing import Any, get_type_hints

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "research_team_review_capacity_forecast_report.py"
)


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_team_review_capacity_forecast_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def fixed_time():
    from datetime import datetime, timezone

    return datetime(2026, 7, 8, 12, 0, tzinfo=timezone.utc)


def capacity_input(**overrides: object):
    module = api()
    values = {
        "team_id": "macro_review",
        "queue_id": "election_calendar",
        "market_group": "public_events",
        "pending_task_count": d("8.000000"),
        "available_review_slot_count": d("12.000000"),
        "due_soon_task_count": d("1.000000"),
        "overdue_task_count": d("0.000000"),
        "sla_pressure_score": d("0.300000"),
        "hours_until_nearest_event": d("72.000000"),
        "event_importance_score": d("0.200000"),
        "expertise_fit_score": d("0.900000"),
    }
    values.update(overrides)
    return module.ResearchTeamReviewCapacityForecastInput(**values)


def build_report(*rows: object, **overrides: object):
    module = api()
    generated_at = overrides.pop("generated_at", fixed_time())
    return module.build_research_team_review_capacity_forecast_report(
        rows,
        generated_at=generated_at,
        **overrides,
    )


def assert_no_float_values(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError(f"unexpected float value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_values(item)
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_no_float_values(item)


def test_block_capacity_forecast_identifies_sla_event_and_expertise_bottleneck() -> None:
    report = build_report(
        capacity_input(
            team_id="macro_review",
            queue_id="election_calendar",
            pending_task_count=d("18.000000"),
            available_review_slot_count=d("10.000000"),
            due_soon_task_count=d("7.000000"),
            overdue_task_count=d("3.000000"),
            sla_pressure_score=d("0.910000"),
            hours_until_nearest_event=d("3.000000"),
            event_importance_score=d("0.900000"),
            expertise_fit_score=d("0.350000"),
        ),
        capacity_input(
            team_id="policy_review",
            queue_id="regulatory_updates",
            market_group="public_policy",
        ),
    )

    assert is_dataclass(report)
    assert report.capacity_status == "block"
    assert report.team_queue_count == d("2.000000")
    assert report.pass_queue_count == d("1.000000")
    assert report.watch_queue_count == d("0.000000")
    assert report.block_queue_count == d("1.000000")
    assert report.bottleneck_queue_count == d("1.000000")
    assert report.total_pending_task_count == d("26.000000")
    assert report.total_available_review_slot_count == d("22.000000")
    assert report.weighted_capacity_utilization == d("1.181818")
    assert report.max_sla_pressure_score == d("0.910000")
    assert report.min_expertise_fit_score == d("0.350000")
    assert report.max_event_timing_pressure == d("0.900000")
    assert report.reason_codes == (
        "capacity_block_present",
        "capacity_over_committed",
        "sla_pressure_block",
        "event_timing_block",
        "expertise_fit_block",
        "overdue_tasks_present",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    blocked_row = report.rows[0]
    assert blocked_row.team_id == "macro_review"
    assert blocked_row.capacity_utilization == d("1.800000")
    assert blocked_row.event_timing_pressure == d("0.900000")
    assert blocked_row.expertise_gap_score == d("0.650000")
    assert blocked_row.capacity_status == "block"
    assert blocked_row.reason_codes == (
        "capacity_over_committed",
        "sla_pressure_block",
        "event_timing_block",
        "expertise_fit_block",
        "overdue_tasks_present",
    )


def test_watch_status_uses_capacity_sla_event_timing_and_expertise_fit() -> None:
    report = build_report(
        capacity_input(
            pending_task_count=d("9.000000"),
            available_review_slot_count=d("10.000000"),
            due_soon_task_count=d("3.000000"),
            sla_pressure_score=d("0.650000"),
            hours_until_nearest_event=d("4.000000"),
            event_importance_score=d("0.700000"),
            expertise_fit_score=d("0.650000"),
        ),
    )

    row = report.rows[0]

    assert report.capacity_status == "watch"
    assert report.pass_queue_count == d("0.000000")
    assert report.watch_queue_count == d("1.000000")
    assert report.block_queue_count == d("0.000000")
    assert row.capacity_status == "watch"
    assert row.capacity_utilization == d("0.900000")
    assert row.event_timing_pressure == d("0.700000")
    assert row.expertise_gap_score == d("0.350000")
    assert row.reason_codes == (
        "capacity_near_limit",
        "sla_pressure_watch",
        "event_timing_watch",
        "expertise_fit_watch",
        "due_soon_tasks_present",
    )


def test_pass_status_reports_clear_capacity_without_bottlenecks() -> None:
    report = build_report(capacity_input())

    row = report.rows[0]

    assert report.capacity_status == "pass"
    assert row.capacity_status == "pass"
    assert row.capacity_utilization == d("0.666667")
    assert row.event_timing_pressure == d("0.000000")
    assert row.expertise_gap_score == d("0.100000")
    assert row.reason_codes == ("review_capacity_clear",)
    assert report.reason_codes == ("review_capacity_clear",)


def test_payload_uses_decimal_strings_public_lists_no_floats_and_stable_digest() -> None:
    module = api()
    first = build_report(
        capacity_input(
            team_id="macro_review",
            queue_id="election_calendar",
            pending_task_count=d("18.000000"),
            available_review_slot_count=d("10.000000"),
            sla_pressure_score=d("0.910000"),
            hours_until_nearest_event=d("3.000000"),
            event_importance_score=d("0.900000"),
            expertise_fit_score=d("0.350000"),
        ),
        capacity_input(team_id="policy_review", queue_id="regulatory_updates"),
    )
    second = build_report(
        capacity_input(team_id="policy_review", queue_id="regulatory_updates"),
        capacity_input(
            team_id="macro_review",
            queue_id="election_calendar",
            pending_task_count=d("18.000000"),
            available_review_slot_count=d("10.000000"),
            sla_pressure_score=d("0.910000"),
            hours_until_nearest_event=d("3.000000"),
            event_importance_score=d("0.900000"),
            expertise_fit_score=d("0.350000"),
        ),
    )

    payload = module.research_team_review_capacity_forecast_report_payload(first)
    encoded = json.dumps(payload, sort_keys=True)

    assert first.payload == payload
    assert first.payload_digest == second.payload_digest
    assert payload["payload_digest"] == first.payload_digest
    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["weighted_capacity_utilization"] == "1.181818"
    assert payload["rows"][0]["pending_task_count"] == "18.000000"
    assert payload["rows"][0]["reason_codes"] == [
        "capacity_over_committed",
        "sla_pressure_block",
        "event_timing_block",
        "expertise_fit_block",
    ]
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert '"1.181818"' in encoded
    assert_no_float_values(payload)


def test_public_numeric_dataclass_fields_are_decimal_only() -> None:
    module = api()
    numeric_fields = {
        "watch_capacity_utilization",
        "block_capacity_utilization",
        "watch_sla_pressure_score",
        "block_sla_pressure_score",
        "event_watch_window_hours",
        "event_block_window_hours",
        "watch_event_timing_pressure",
        "block_event_timing_pressure",
        "watch_expertise_fit_score",
        "block_expertise_fit_score",
        "pending_task_count",
        "available_review_slot_count",
        "due_soon_task_count",
        "overdue_task_count",
        "sla_pressure_score",
        "hours_until_nearest_event",
        "event_importance_score",
        "expertise_fit_score",
        "capacity_utilization",
        "event_timing_pressure",
        "expertise_gap_score",
        "count",
        "queue_ratio",
        "team_queue_count",
        "pass_queue_count",
        "watch_queue_count",
        "block_queue_count",
        "bottleneck_queue_count",
        "total_pending_task_count",
        "total_available_review_slot_count",
        "weighted_capacity_utilization",
        "max_sla_pressure_score",
        "min_expertise_fit_score",
        "max_event_timing_pressure",
    }

    for cls in (
        module.ResearchTeamReviewCapacityForecastConfig,
        module.ResearchTeamReviewCapacityForecastInput,
        module.ResearchTeamReviewCapacityForecastRow,
        module.ResearchTeamReviewCapacityForecastReasonCodeCount,
        module.ResearchTeamReviewCapacityForecastReport,
    ):
        hints = get_type_hints(cls)
        for item in fields(cls):
            if item.name in numeric_fields:
                assert hints[item.name] is Decimal


def test_validation_rejects_bad_types_ranges_precision_duplicates_and_flags() -> None:
    module = api()

    with pytest.raises(ValueError, match="team_id"):
        capacity_input(team_id=_StringSubclass("macro_review"))

    with pytest.raises(ValueError, match="pending_task_count must be a Decimal"):
        capacity_input(pending_task_count=8)

    with pytest.raises(ValueError, match="sla_pressure_score must be a Decimal"):
        capacity_input(sla_pressure_score=_DecimalSubclass("0.500000"))

    with pytest.raises(ValueError, match="available_review_slot_count must be positive"):
        capacity_input(available_review_slot_count=d("0.000000"))

    with pytest.raises(ValueError, match="pending_task_count must be nonnegative"):
        capacity_input(pending_task_count=d("-0.000001"))

    with pytest.raises(ValueError, match="sla_pressure_score must be between 0 and 1"):
        capacity_input(sla_pressure_score=d("1.000001"))

    with pytest.raises(ValueError, match="event_importance_score must be finite"):
        capacity_input(event_importance_score=Decimal("NaN"))

    with pytest.raises(ValueError, match="required decimal precision"):
        capacity_input(expertise_fit_score=d("0.3333333"))

    with pytest.raises(ValueError, match="reason_codes must be unique"):
        module.ResearchTeamReviewCapacityForecastRow(
            team_id="macro_review",
            queue_id="election_calendar",
            market_group="public_events",
            pending_task_count=d("9.000000"),
            available_review_slot_count=d("10.000000"),
            due_soon_task_count=d("3.000000"),
            overdue_task_count=d("0.000000"),
            sla_pressure_score=d("0.650000"),
            hours_until_nearest_event=d("4.000000"),
            event_importance_score=d("0.700000"),
            expertise_fit_score=d("0.650000"),
            capacity_utilization=d("0.900000"),
            event_timing_pressure=d("0.700000"),
            expertise_gap_score=d("0.350000"),
            capacity_status="watch",
            reason_codes=("capacity_near_limit", "capacity_near_limit"),
        )

    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(capacity_input(), paper_only=False)

    with pytest.raises(ValueError, match="readonly must be True"):
        replace(build_report(capacity_input()), readonly=False)

    with pytest.raises(FrozenInstanceError):
        report = build_report(capacity_input())
        report.capacity_status = "watch"  # type: ignore[misc]


def test_public_strings_reject_secret_like_values_before_payload_leakage() -> None:
    with pytest.raises(ValueError, match="must not contain sensitive material"):
        capacity_input(team_id="postgresql://user:secret@db.example.local/team")


def test_public_status_values_are_exactly_pass_watch_block() -> None:
    module = api()

    assert module.PUBLIC_STATUSES == ("pass", "watch", "block")

    with pytest.raises(ValueError, match="capacity_status must be one of pass, watch, block"):
        module.ResearchTeamReviewCapacityForecastRow(
            team_id="macro_review",
            queue_id="election_calendar",
            market_group="public_events",
            pending_task_count=d("9.000000"),
            available_review_slot_count=d("10.000000"),
            due_soon_task_count=d("3.000000"),
            overdue_task_count=d("0.000000"),
            sla_pressure_score=d("0.650000"),
            hours_until_nearest_event=d("4.000000"),
            event_importance_score=d("0.700000"),
            expertise_fit_score=d("0.650000"),
            capacity_utilization=d("0.900000"),
            event_timing_pressure=d("0.700000"),
            expertise_gap_score=d("0.350000"),
            capacity_status="review",
            reason_codes=("capacity_near_limit",),
        )


def test_module_scope_is_report_only_public_safe_with_no_execution_surface() -> None:
    source_text = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source_text.lower()
    for forbidden in (
        "auth",
        "wallet",
        "account",
        "order",
        "trade",
        "broker",
        "signing",
        "submit",
        "cancel",
        "replace",
        "database",
        "network",
        "durable",
        "store",
        "open(",
        "requests",
        "http",
        "socket",
        "postgres",
        "psycopg",
        "sqlite",
        "sqlalchemy",
        "supabase",
        "execute(",
        "position sizing",
        "recommend",
        "recommendation",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source_text)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id != "float"
