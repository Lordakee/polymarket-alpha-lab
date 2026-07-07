from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import importlib
import json
from pathlib import Path
from typing import Any

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "team_research_round_robin_scheduler.py"
)
GENERATED_AT = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.team_research_round_robin_scheduler",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values: dict[str, object] = {
        "config_version": "team-research-round-robin-scheduler-test",
        "queue_priority_weight": d("0.550000"),
        "sla_priority_weight": d("0.450000"),
        "sla_watch_window_seconds": d("86400.000000"),
        "watch_queue_pressure_score": d("0.500000"),
        "high_queue_pressure_score": d("0.850000"),
        "watch_sla_risk_score": d("0.500000"),
        "high_sla_risk_score": d("0.850000"),
        "watch_priority_floor": d("0.500000"),
        "watch_team_load_ratio": d("0.750000"),
        "min_specialist_coverage_score": d("0.600000"),
        "strong_specialist_coverage_score": d("0.800000"),
    }
    values.update(overrides)
    return module.TeamResearchRoundRobinSchedulerConfig(**values)


def task(
    work_item_id: str,
    *,
    domain_id: str = "rates_domain",
    queued_seconds_ago: int = 3600,
    due_seconds_from_now: int = 86400,
    queue_pressure_score: str = "0.100000",
):
    module = api()
    return module.TeamResearchRoundRobinTaskInput(
        work_item_id=work_item_id,
        domain_id=domain_id,
        queued_at=GENERATED_AT - timedelta(seconds=queued_seconds_ago),
        due_at=GENERATED_AT + timedelta(seconds=due_seconds_from_now),
        queue_pressure_score=d(queue_pressure_score),
    )


def coverage(
    team_id: str,
    *,
    domain_id: str = "rates_domain",
    specialist_coverage_score: str = "0.900000",
    specialist_coverage_count: str = "2",
    active_work_count: str = "0",
    max_work_count: str = "4",
    rotation_rank: str = "1",
):
    module = api()
    return module.TeamResearchRoundRobinTeamCoverageInput(
        team_id=team_id,
        domain_id=domain_id,
        specialist_coverage_score=d(specialist_coverage_score),
        specialist_coverage_count=d(specialist_coverage_count),
        active_work_count=d(active_work_count),
        max_work_count=d(max_work_count),
        rotation_rank=d(rotation_rank),
    )


def build_report(
    *items: object,
    team_coverages: tuple[object, ...] | None = None,
    generated_at=GENERATED_AT,
):
    module = api()
    if not items:
        items = (task("task_alpha"), task("task_beta"))
    return module.build_team_research_round_robin_scheduler(
        items,
        team_coverages=team_coverages
        if team_coverages is not None
        else (
            coverage("team_a", rotation_rank="1"),
            coverage("team_b", rotation_rank="2"),
        ),
        config=config(),
        generated_at=generated_at,
    )


def assert_no_float_values(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError(f"unexpected float value {value!r}")
    if type(value) is dict:
        for item in value.values():
            assert_no_float_values(item)
    if type(value) in (list, tuple):
        for item in value:
            assert_no_float_values(item)


def assert_public_numeric_values_are_decimal(value: object) -> None:
    if type(value) is bool or value is None:
        return
    if type(value) is Decimal:
        return
    if type(value) in (int, float):
        raise AssertionError(f"public numeric value must be Decimal, got {value!r}")
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            assert_public_numeric_values_are_decimal(getattr(value, field.name))
        return
    if type(value) is dict:
        for item in value.values():
            assert_public_numeric_values_are_decimal(item)
        return
    if type(value) in (list, tuple):
        for item in value:
            assert_public_numeric_values_are_decimal(item)


def test_balanced_dispatch_round_robins_equal_domain_work() -> None:
    report = build_report(
        task("task_a"),
        task("task_b"),
        task("task_c"),
        task("task_d"),
    )

    assert report.report_status == "pass"
    assert report.work_item_count == d("4")
    assert report.assigned_count == d("4")
    assert report.pass_count == d("4")
    assert report.watch_count == d("0")
    assert report.block_count == d("0")
    assert report.team_count == d("2")
    assert report.domain_count == d("1")
    assert report.reason_codes == ("team_research_round_robin_pass",)

    assert tuple(row.assigned_team_id for row in report.rows) == (
        "team_a",
        "team_b",
        "team_a",
        "team_b",
    )
    assert tuple(row.assignment_status for row in report.rows) == (
        "pass",
        "pass",
        "pass",
        "pass",
    )
    assert tuple(row.rank for row in report.rows) == (d("1"), d("2"), d("3"), d("4"))
    assert report.rows[0].queue_age_seconds == d("3600.000000")
    assert report.rows[0].sla_seconds_remaining == d("86400.000000")
    assert report.rows[0].sla_risk_score == d("0.000000")
    assert report.rows[0].task_priority_score == d("0.055000")
    assert report.rows[0].reason_codes == (
        "task_assignment_pass",
        "queue_pressure_low",
        "sla_low",
        "specialist_coverage_strong",
        "round_robin_balanced",
    )


def test_pressure_dispatch_prefers_lower_load_and_watch_status() -> None:
    report = build_report(
        task(
            "task_pressure",
            queued_seconds_ago=7200,
            due_seconds_from_now=3600,
            queue_pressure_score="0.900000",
        ),
        team_coverages=(
            coverage("team_loaded", active_work_count="3", max_work_count="4", rotation_rank="1"),
            coverage("team_open", active_work_count="0", max_work_count="4", rotation_rank="2"),
        ),
    )

    row = report.rows[0]
    assert report.report_status == "watch"
    assert report.watch_count == d("1")
    assert row.work_item_id == "task_pressure"
    assert row.assigned_team_id == "team_open"
    assert row.assignment_status == "watch"
    assert row.queue_pressure_score == d("0.900000")
    assert row.sla_seconds_remaining == d("3600.000000")
    assert row.sla_risk_score == d("0.958333")
    assert row.task_priority_score == d("0.926250")
    assert row.team_load_ratio == d("0.000000")
    assert row.team_remaining_capacity_count == d("3")
    assert row.reason_codes == (
        "task_assignment_watch",
        "queue_pressure_high",
        "sla_high",
        "specialist_coverage_strong",
        "round_robin_balanced",
        "team_load_watch",
    )


def test_missing_expert_coverage_blocks_without_assignment() -> None:
    report = build_report(
        task("task_gap", domain_id="labor_domain", queue_pressure_score="0.700000"),
        team_coverages=(
            coverage(
                "team_rates",
                domain_id="rates_domain",
                specialist_coverage_score="0.950000",
                rotation_rank="1",
            ),
        ),
    )

    row = report.rows[0]
    assert report.report_status == "block"
    assert report.assigned_count == d("0")
    assert report.block_count == d("1")
    assert row.assigned_team_id is None
    assert row.assignment_status == "block"
    assert row.specialist_coverage_score == d("0.000000")
    assert row.specialist_coverage_count == d("0")
    assert row.team_remaining_capacity_count == d("0")
    assert "domain_gap" in row.reason_codes


def test_rejects_non_decimal_subclasses_bad_iterables_and_datetime_types() -> None:
    module = api()
    with pytest.raises(ValueError, match="exactly Decimal"):
        module.TeamResearchRoundRobinTaskInput(
            work_item_id="task_type",
            domain_id="rates_domain",
            queued_at=GENERATED_AT,
            due_at=GENERATED_AT + timedelta(days=1),
            queue_pressure_score=1,
        )
    with pytest.raises(ValueError, match="exactly Decimal"):
        module.TeamResearchRoundRobinTeamCoverageInput(
            team_id="team_type",
            domain_id="rates_domain",
            specialist_coverage_score=d("0.900000"),
            specialist_coverage_count=d("2"),
            active_work_count=_DecimalSubclass("1"),
            max_work_count=d("4"),
            rotation_rank=d("1"),
        )
    with pytest.raises(ValueError, match="timezone-aware"):
        module.TeamResearchRoundRobinTaskInput(
            work_item_id="task_time",
            domain_id="rates_domain",
            queued_at=datetime(2026, 7, 7, 12, 0),
            due_at=GENERATED_AT + timedelta(days=1),
            queue_pressure_score=d("0.100000"),
        )
    with pytest.raises(ValueError, match="work_items must be an iterable"):
        module.build_team_research_round_robin_scheduler(
            "task_type",
            team_coverages=(coverage("team_a"),),
            config=config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="config must be"):
        module.build_team_research_round_robin_scheduler(
            (task("task_type"),),
            team_coverages=(coverage("team_a"),),
            config=object(),
            generated_at=GENERATED_AT,
        )


def test_rejects_leaky_public_payload_and_keeps_report_sanitized() -> None:
    module = api()
    with pytest.raises(ValueError, match="unsafe public payload"):
        module.TeamResearchRoundRobinTaskInput(
            work_item_id="market-raw-123",
            domain_id="rates_domain",
            queued_at=GENERATED_AT,
            due_at=GENERATED_AT + timedelta(days=1),
            queue_pressure_score=d("0.100000"),
        )
    with pytest.raises(ValueError, match="unsafe public payload"):
        coverage("team_wallet_ops")

    report = build_report(task("task_safe"))
    payload_json = json.dumps(report.payload, sort_keys=True).lower()
    forbidden = (
        "candidate",
        "market",
        "slug",
        "question",
        "source",
        "url",
        "dsn",
        "table",
        "token",
        "wallet",
        "auth",
        "order",
        "trade",
        "position",
        "buy",
        "sell",
        "recommend",
    )
    assert not any(fragment in payload_json for fragment in forbidden)
    assert_no_float_values(report.payload)


def test_dataclasses_are_frozen_decimal_only_and_hard_flagged() -> None:
    module = api()
    cfg = config()
    item = task("task_flags")
    team = coverage("team_flags")
    report = build_report(item, team_coverages=(team,))
    row = report.rows[0]

    numeric_fields = {
        "queue_priority_weight",
        "sla_priority_weight",
        "sla_watch_window_seconds",
        "watch_queue_pressure_score",
        "high_queue_pressure_score",
        "watch_sla_risk_score",
        "high_sla_risk_score",
        "watch_priority_floor",
        "watch_team_load_ratio",
        "min_specialist_coverage_score",
        "strong_specialist_coverage_score",
        "queue_pressure_score",
        "specialist_coverage_score",
        "specialist_coverage_count",
        "active_work_count",
        "max_work_count",
        "rotation_rank",
        "rank",
        "queue_age_seconds",
        "sla_seconds_remaining",
        "sla_risk_score",
        "task_priority_score",
        "team_load_ratio",
        "team_remaining_capacity_count",
        "work_item_count",
        "assigned_count",
        "pass_count",
        "watch_count",
        "block_count",
        "team_count",
        "domain_count",
    }

    for obj in (cfg, item, team, row, report):
        assert is_dataclass(obj)
        assert obj.paper_only is True
        assert obj.report_only is True
        assert obj.readonly is True
        with pytest.raises(FrozenInstanceError):
            obj.readonly = False  # type: ignore[misc]
        for field in fields(obj):
            if field.name in numeric_fields:
                assert type(getattr(obj, field.name)) is Decimal
        assert_public_numeric_values_are_decimal(obj)

    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(cfg, paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        replace(item, report_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(team, readonly=False)
    with pytest.raises(TypeError):
        type("UnsafeSubclass", (module.TeamResearchRoundRobinSchedulerConfig,), {})


def test_output_is_deterministic_for_input_order_and_digest() -> None:
    slow = task("task_slow", queue_pressure_score="0.100000")
    fast = task(
        "task_fast",
        due_seconds_from_now=3600,
        queue_pressure_score="0.900000",
    )
    teams = (
        coverage("team_b", rotation_rank="2"),
        coverage("team_a", rotation_rank="1"),
    )

    first = build_report(slow, fast, team_coverages=teams)
    second = build_report(fast, slow, team_coverages=tuple(reversed(teams)))

    assert first.rows == second.rows
    assert first.payload == second.payload
    assert first.derived_validation_digest == second.derived_validation_digest
    assert tuple(row.work_item_id for row in first.rows) == ("task_fast", "task_slow")
    assert len(first.derived_validation_digest) == 64


def test_module_has_no_float_literals_and_only_public_status_values() -> None:
    tree = ast.parse(MODULE_PATH.read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, float):
            raise AssertionError(f"float literal found: {node.value!r}")

    report = build_report(task("task_public"))
    statuses = {report.report_status, *(row.assignment_status for row in report.rows)}
    assert statuses <= {"pass", "watch", "block"}
    assert report.payload["paper_only"] is True
    assert report.payload["report_only"] is True
    assert report.payload["readonly"] is True
