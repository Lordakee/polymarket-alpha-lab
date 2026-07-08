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
    / "research_team_source_assignment_balance_report.py"
)


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_team_source_assignment_balance_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def generated_at():
    from datetime import UTC, datetime

    return datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


def assignment(**overrides: object):
    module = api()
    values = {
        "team_id": "team_macro",
        "source_class_id": "economic_calendar",
        "assigned_load_units": d("40.000000"),
        "aggregate_capacity_units": d("100.000000"),
        "expertise_score": d("0.900000"),
        "source_reliability": d("0.900000"),
        "freshness_decay": d("0.100000"),
        "catalyst_pressure": d("0.100000"),
    }
    values.update(overrides)
    return module.ResearchTeamSourceClassAssignment(**values)


def report(*assignments: object):
    module = api()
    return module.build_research_team_source_assignment_balance_report(
        assignments,
        config=module.ResearchTeamSourceAssignmentBalanceConfig(),
        generated_at=generated_at(),
    )


def assert_no_float_or_int_values(value: Any) -> None:
    if type(value) in (float, int):
        raise AssertionError(f"unexpected numeric payload value {value!r}")
    if isinstance(value, dict):
        for child in value.values():
            assert_no_float_or_int_values(child)
    if isinstance(value, list):
        for child in value:
            assert_no_float_or_int_values(child)


def test_build_report_balances_assignment_pressure_into_exact_statuses() -> None:
    module = api()
    balanced = assignment()
    watch = assignment(
        team_id="team_policy",
        source_class_id="policy_resolution",
        assigned_load_units=d("85.000000"),
        expertise_score=d("0.650000"),
        source_reliability=d("0.550000"),
        freshness_decay=d("0.500000"),
        catalyst_pressure=d("0.700000"),
    )
    block = assignment(
        team_id="team_weather",
        source_class_id="weather_alerts",
        assigned_load_units=d("120.000000"),
        expertise_score=d("0.300000"),
        source_reliability=d("0.400000"),
        freshness_decay=d("0.800000"),
        catalyst_pressure=d("0.900000"),
    )

    result = report(block, watch, balanced)

    assert is_dataclass(result)
    assert module.ASSIGNMENT_BALANCE_STATUSES == ("pass", "watch", "block")
    assert result.report_status == "block"
    assert result.row_count == d("3.000000")
    assert result.pass_count == d("1.000000")
    assert result.watch_count == d("1.000000")
    assert result.block_count == d("1.000000")
    assert result.total_assigned_load_units == d("245.000000")
    assert result.total_capacity_units == d("300.000000")
    assert result.aggregate_utilization_ratio == d("0.816667")
    assert result.max_assignment_pressure == d("0.925000")
    assert result.min_coverage_strength == d("0.024000")
    assert [row.source_class_id for row in result.rows] == [
        "economic_calendar",
        "policy_resolution",
        "weather_alerts",
    ]
    assert [row.monitoring_status for row in result.rows] == [
        "pass",
        "watch",
        "block",
    ]
    assert result.rows[0].utilization_ratio == d("0.400000")
    assert result.rows[0].coverage_strength == d("0.729000")
    assert result.rows[0].assignment_pressure == d("0.220000")
    assert result.rows[1].assignment_pressure == d("0.632500")
    assert result.rows[2].assignment_pressure == d("0.925000")
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True

    payload = module.research_team_source_assignment_balance_report_payload(result)
    assert payload == result.payload
    assert payload["derived_validation_digest"] == result.derived_validation_digest
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_float_or_int_values(payload)
    assert module.validate_research_team_source_assignment_balance_report_payload(payload)


def test_payload_and_digest_are_deterministic_for_same_inputs() -> None:
    module = api()
    left = report(
        assignment(team_id="team_weather", source_class_id="weather_alerts"),
        assignment(team_id="team_macro", source_class_id="economic_calendar"),
    )
    right = report(
        assignment(team_id="team_macro", source_class_id="economic_calendar"),
        assignment(team_id="team_weather", source_class_id="weather_alerts"),
    )

    assert left.derived_validation_digest == right.derived_validation_digest
    assert left.payload == right.payload
    encoded = json.dumps(left.payload, sort_keys=True)
    assert left.derived_validation_digest in encoded


def test_validation_requires_decimal_inputs_public_codes_flags_and_frozen_outputs() -> None:
    module = api()
    result = report(assignment())

    with pytest.raises(FrozenInstanceError):
        result.report_status = "watch"  # type: ignore[misc]

    with pytest.raises(ValueError, match="assigned_load_units must be a Decimal"):
        assignment(assigned_load_units=1)

    with pytest.raises(ValueError, match="source_reliability must be a Decimal"):
        assignment(source_reliability=_DecimalSubclass("0.900000"))

    with pytest.raises(ValueError, match="aggregate_capacity_units must be greater than zero"):
        assignment(aggregate_capacity_units=d("0.000000"))

    with pytest.raises(ValueError, match="expertise_score must be between 0 and 1"):
        assignment(expertise_score=d("1.000001"))

    with pytest.raises(ValueError, match="source_class_id must be a public code"):
        assignment(source_class_id="https://example.invalid/raw-source")

    with pytest.raises(ValueError, match="team_id must be a public code"):
        assignment(team_id="Team Macro")

    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(assignment(), paper_only=False)

    with pytest.raises(ValueError, match="readonly must be True"):
        replace(result, readonly=False)

    with pytest.raises(ValueError, match="monitoring_status must be supported"):
        module.ResearchTeamSourceAssignmentBalanceRow(
            team_id="team_macro",
            source_class_id="economic_calendar",
            assigned_load_units=d("40.000000"),
            aggregate_capacity_units=d("100.000000"),
            utilization_ratio=d("0.400000"),
            expertise_score=d("0.900000"),
            source_reliability=d("0.900000"),
            freshness_decay=d("0.100000"),
            catalyst_pressure=d("0.100000"),
            coverage_strength=d("0.729000"),
            assignment_pressure=d("0.220000"),
            monitoring_status="clear",
            reason_codes=("assignment_balance_pass",),
        )


def test_public_numeric_dataclass_fields_are_decimal_only() -> None:
    module = api()
    decimal_fields = {
        "assigned_load_units",
        "aggregate_capacity_units",
        "expertise_score",
        "source_reliability",
        "freshness_decay",
        "catalyst_pressure",
        "watch_utilization_ratio",
        "block_utilization_ratio",
        "watch_assignment_pressure",
        "block_assignment_pressure",
        "watch_coverage_strength",
        "block_coverage_strength",
        "low_source_reliability",
        "high_freshness_decay",
        "high_catalyst_pressure",
        "utilization_ratio",
        "coverage_strength",
        "assignment_pressure",
        "row_count",
        "team_count",
        "source_class_count",
        "pass_count",
        "watch_count",
        "block_count",
        "total_assigned_load_units",
        "total_capacity_units",
        "aggregate_utilization_ratio",
        "max_assignment_pressure",
        "min_coverage_strength",
        "count",
    }

    for cls in (
        module.ResearchTeamSourceAssignmentBalanceConfig,
        module.ResearchTeamSourceClassAssignment,
        module.ResearchTeamSourceAssignmentBalanceRow,
        module.ResearchTeamSourceAssignmentBalanceReasonCodeCount,
        module.ResearchTeamSourceAssignmentBalanceReport,
    ):
        hints = get_type_hints(cls)
        for item in fields(cls):
            if item.name in decimal_fields:
                assert hints[item.name] is Decimal


def test_payload_validation_rejects_tampering_and_unsafe_numeric_values() -> None:
    module = api()
    payload = report(assignment()).payload

    tampered = dict(payload)
    tampered["report_status"] = "watch"
    with pytest.raises(ValueError, match="derived_validation_digest must match"):
        module.validate_research_team_source_assignment_balance_report_payload(tampered)

    with pytest.raises(ValueError, match="payload must be readonly"):
        module.validate_research_team_source_assignment_balance_report_payload(
            {"paper_only": True, "report_only": True, "readonly": False},
        )

    with pytest.raises(ValueError, match="JSON value must not be a float"):
        module.validate_research_team_source_assignment_balance_report_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "row_count": 1.0,
            },
        )

    with pytest.raises(ValueError, match="JSON numeric value must use Decimal strings"):
        module.validate_research_team_source_assignment_balance_report_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "row_count": 1,
            },
        )


def test_module_scope_is_report_only_without_raw_or_execution_surfaces() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "source_url",
        "source_name",
        "source_text",
        "raw_source",
        "auth",
        "wallet",
        "order",
        "trade",
        "database",
        "network",
        "requests",
        "urllib",
        "socket",
        "sqlite",
        "open(",
        "recommend",
        "sizing",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in {"float", "open"}
