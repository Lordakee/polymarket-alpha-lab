from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, get_type_hints

import pytest


MODULE_PATH = Path(
    "src/polymarket_alpha_lab/research_team_domain_assignment_balance_report.py",
)
GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_team_domain_assignment_balance_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def assignment(**overrides: object):
    module = api()
    values = {
        "team_id": "team_macro",
        "research_lane": "macro",
        "assigned_researchers": d("2.000000"),
        "active_review_load": d("2.000000"),
        "review_capacity": d("10.000000"),
        "fresh_memory_items": d("8.000000"),
        "stale_memory_items": d("1.000000"),
        "covered_topic_count": d("10.000000"),
        "required_topic_count": d("10.000000"),
        "escalation_pressure": d("0.100000"),
    }
    values.update(overrides)
    return module.ResearchTeamDomainAssignment(**values)


def build_report(*rows: object):
    module = api()
    return module.build_research_team_domain_assignment_balance_report(
        rows,
        generated_at=GENERATED_AT,
        config=module.ResearchTeamDomainAssignmentBalanceConfig(),
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


def lane_inputs() -> tuple[object, ...]:
    return (
        assignment(team_id="team_politics", research_lane="politics"),
        assignment(team_id="team_macro_core", research_lane="macro"),
        assignment(
            team_id="team_macro_alt",
            research_lane="macro",
            assigned_researchers=d("1.000000"),
            active_review_load=d("1.000000"),
            review_capacity=d("5.000000"),
            fresh_memory_items=d("4.000000"),
            stale_memory_items=d("0.000000"),
            covered_topic_count=d("5.000000"),
            required_topic_count=d("5.000000"),
            escalation_pressure=d("0.000000"),
        ),
        assignment(team_id="team_crypto", research_lane="crypto"),
        assignment(team_id="team_equity", research_lane="equity_index"),
        assignment(team_id="team_metals", research_lane="precious_metals"),
        assignment(team_id="team_soccer", research_lane="soccer"),
        assignment(team_id="team_basketball", research_lane="basketball"),
        assignment(
            team_id="team_baseball",
            research_lane="baseball",
            active_review_load=d("8.000000"),
            fresh_memory_items=d("4.000000"),
            stale_memory_items=d("6.000000"),
            covered_topic_count=d("8.000000"),
            required_topic_count=d("10.000000"),
            escalation_pressure=d("0.600000"),
        ),
        assignment(
            team_id="team_tennis",
            research_lane="tennis",
            active_review_load=d("11.000000"),
            fresh_memory_items=d("1.000000"),
            stale_memory_items=d("9.000000"),
            covered_topic_count=d("5.000000"),
            required_topic_count=d("10.000000"),
            escalation_pressure=d("0.900000"),
        ),
    )


def test_domain_assignment_balance_aggregates_all_public_research_lanes() -> None:
    module = api()

    result = build_report(*reversed(lane_inputs()))

    assert is_dataclass(result)
    assert module.DOMAIN_ASSIGNMENT_BALANCE_STATUSES == ("pass", "watch", "block")
    assert module.RESEARCH_TEAM_DOMAIN_ASSIGNMENT_RESEARCH_LANES == (
        "politics",
        "macro",
        "crypto",
        "equity_index",
        "precious_metals",
        "soccer",
        "basketball",
        "baseball",
        "tennis",
    )
    assert result.report_status == "block"
    assert result.row_count == d("9.000000")
    assert result.team_count == d("10.000000")
    assert result.research_lane_count == d("9.000000")
    assert result.pass_count == d("7.000000")
    assert result.watch_count == d("1.000000")
    assert result.block_count == d("1.000000")
    assert result.total_assigned_researchers == d("19.000000")
    assert result.total_active_review_load == d("34.000000")
    assert result.total_review_capacity == d("95.000000")
    assert result.aggregate_review_load_ratio == d("0.357895")
    assert result.max_stale_memory_ratio == d("0.900000")
    assert result.max_coverage_gap_ratio == d("0.500000")
    assert result.max_escalation_pressure == d("0.900000")
    assert result.max_assignment_pressure == d("0.860000")
    assert tuple(row.research_lane for row in result.rows) == (
        "politics",
        "macro",
        "crypto",
        "equity_index",
        "precious_metals",
        "soccer",
        "basketball",
        "baseball",
        "tennis",
    )
    assert tuple(row.balance_status for row in result.rows) == (
        "pass",
        "pass",
        "pass",
        "pass",
        "pass",
        "pass",
        "pass",
        "watch",
        "block",
    )

    macro = result.rows[1]
    assert macro.team_count == d("2.000000")
    assert macro.active_review_load == d("3.000000")
    assert macro.review_capacity == d("15.000000")
    assert macro.stale_memory_ratio == d("0.076923")
    assert macro.assignment_pressure == d("0.115385")

    baseball = result.rows[7]
    assert baseball.review_load_ratio == d("0.800000")
    assert baseball.stale_memory_ratio == d("0.600000")
    assert baseball.coverage_gap_ratio == d("0.200000")
    assert baseball.assignment_pressure == d("0.600000")
    assert baseball.reason_codes == (
        "domain_assignment_balance_watch",
        "review_load_watch",
        "stale_memory_watch",
        "coverage_gap_watch",
        "escalation_pressure_watch",
    )

    tennis = result.rows[8]
    assert tennis.review_load_ratio == d("1.100000")
    assert tennis.coverage_gap_count == d("5.000000")
    assert tennis.assignment_pressure == d("0.860000")
    assert tennis.reason_codes == (
        "domain_assignment_balance_block",
        "review_load_block",
        "stale_memory_block",
        "coverage_gap_block",
        "escalation_pressure_block",
        "assignment_pressure_block",
    )
    assert result.reason_codes[0] == "domain_assignment_balance_report_block"
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True


def test_payload_digest_and_validation_are_deterministic_and_decimal_safe() -> None:
    module = api()
    first = build_report(*lane_inputs())
    second = build_report(*reversed(lane_inputs()))

    assert first.derived_validation_digest == second.derived_validation_digest
    assert first.payload == second.payload
    assert len(first.derived_validation_digest) == 64

    payload = module.research_team_domain_assignment_balance_report_payload(first)
    assert payload == first.payload
    assert payload["derived_validation_digest"] == first.derived_validation_digest
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_float_or_int_values(payload)
    assert module.validate_research_team_domain_assignment_balance_report_payload(payload)

    tampered = dict(payload)
    tampered["report_status"] = "watch"
    with pytest.raises(ValueError, match="derived_validation_digest must match"):
        module.validate_research_team_domain_assignment_balance_report_payload(tampered)


def test_validation_requires_public_aggregate_labels_exact_decimals_and_hard_flags() -> None:
    module = api()
    result = build_report(assignment())

    with pytest.raises(FrozenInstanceError):
        result.report_status = "watch"  # type: ignore[misc]

    with pytest.raises(ValueError, match="active_review_load must be a Decimal"):
        assignment(active_review_load=1)

    with pytest.raises(ValueError, match="escalation_pressure must be a Decimal"):
        assignment(escalation_pressure=_DecimalSubclass("0.100000"))

    with pytest.raises(ValueError, match="review_capacity must be greater than zero"):
        assignment(review_capacity=d("0.000000"))

    with pytest.raises(ValueError, match="escalation_pressure must be between 0 and 1"):
        assignment(escalation_pressure=d("1.000001"))

    with pytest.raises(ValueError, match="research_lane must be supported"):
        assignment(research_lane="weather")

    with pytest.raises(ValueError, match="team_id must be a public code"):
        assignment(team_id="team macro")

    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(assignment(), paper_only=False)

    with pytest.raises(ValueError, match="readonly must be True"):
        replace(result, readonly=False)

    with pytest.raises(ValueError, match="balance_status must be supported"):
        module.ResearchTeamDomainAssignmentBalanceRow(
            research_lane="macro",
            team_count=d("1.000000"),
            assigned_researchers=d("2.000000"),
            active_review_load=d("2.000000"),
            review_capacity=d("10.000000"),
            review_load_ratio=d("0.200000"),
            fresh_memory_items=d("8.000000"),
            stale_memory_items=d("1.000000"),
            stale_memory_ratio=d("0.111111"),
            covered_topic_count=d("10.000000"),
            required_topic_count=d("10.000000"),
            coverage_gap_count=d("0.000000"),
            coverage_gap_ratio=d("0.000000"),
            escalation_pressure=d("0.100000"),
            assignment_pressure=d("0.102222"),
            balance_status="review",
            reason_codes=("domain_assignment_balance_pass",),
        )


def test_public_numeric_dataclass_fields_are_decimal_only() -> None:
    module = api()
    decimal_fields = {
        "assigned_researchers",
        "active_review_load",
        "review_capacity",
        "fresh_memory_items",
        "stale_memory_items",
        "covered_topic_count",
        "required_topic_count",
        "escalation_pressure",
        "watch_review_load_ratio",
        "block_review_load_ratio",
        "watch_stale_memory_ratio",
        "block_stale_memory_ratio",
        "watch_coverage_gap_ratio",
        "block_coverage_gap_ratio",
        "watch_escalation_pressure",
        "block_escalation_pressure",
        "review_load_weight",
        "stale_memory_weight",
        "coverage_gap_weight",
        "escalation_pressure_weight",
        "team_count",
        "review_load_ratio",
        "stale_memory_ratio",
        "coverage_gap_count",
        "coverage_gap_ratio",
        "assignment_pressure",
        "row_count",
        "research_lane_count",
        "pass_count",
        "watch_count",
        "block_count",
        "total_assigned_researchers",
        "total_active_review_load",
        "total_review_capacity",
        "aggregate_review_load_ratio",
        "max_stale_memory_ratio",
        "max_coverage_gap_ratio",
        "max_escalation_pressure",
        "max_assignment_pressure",
        "count",
    }

    for cls in (
        module.ResearchTeamDomainAssignmentBalanceConfig,
        module.ResearchTeamDomainAssignment,
        module.ResearchTeamDomainAssignmentBalanceRow,
        module.ResearchTeamDomainAssignmentBalanceReasonCodeCount,
        module.ResearchTeamDomainAssignmentBalanceReport,
    ):
        hints = get_type_hints(cls)
        for item in fields(cls):
            if item.name in decimal_fields:
                assert hints[item.name] is Decimal


def test_module_scope_is_report_only_without_sensitive_or_action_surfaces() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "market_slug",
        "market_question",
        "event_id",
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
