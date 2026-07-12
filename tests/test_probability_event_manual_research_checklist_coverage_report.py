from __future__ import annotations

import importlib
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab."
    "probability_event_manual_research_checklist_coverage_report"
)
GENERATED_AT = datetime(2026, 7, 11, 12, 0, tzinfo=UTC)
CHECKLIST_FLAGS = (
    "probability_screen_present",
    "source_anchor_present",
    "independent_sources_present",
    "resolution_rules_present",
    "team_route_present",
    "memory_policy_present",
    "cost_gate_present",
    "manual_operator_packet_present",
)
REQUIRED_ITEMS = (
    "probability_screen",
    "source_anchor",
    "independent_sources",
    "resolution_rules",
    "team_route",
    "memory_policy",
    "cost_gate",
    "manual_operator_packet",
)


def api() -> Any:
    return importlib.import_module(MODULE_NAME)


def checklist(**overrides: object) -> Any:
    module = api()
    values = {
        "checklist_ref": "event-alpha",
        "observed_at": GENERATED_AT,
        **{name: True for name in CHECKLIST_FLAGS},
    }
    values.update(overrides)
    return module.ProbabilityEventManualResearchChecklistCoverage(**values)


def build_report(*items: object, generated_at: datetime = GENERATED_AT) -> Any:
    module = api()
    return module.build_probability_event_manual_research_checklist_coverage_report(
        items,
        generated_at=generated_at,
    )


def assert_no_json_numbers(value: Any) -> None:
    if isinstance(value, dict):
        for nested in value.values():
            assert_no_json_numbers(nested)
        return
    if isinstance(value, (list, tuple)):
        for nested in value:
            assert_no_json_numbers(nested)
        return
    assert isinstance(value, bool) or not isinstance(value, (int, float, Decimal))


def test_complete_checklist_passes_with_readonly_payload() -> None:
    module = api()
    report = build_report(checklist())

    assert report.coverage_status == "covered"
    assert report.missing_checklist_items == ()
    assert report.reason_codes == (
        "probability_event_manual_research_checklist_covered",
    )
    assert report.manual_next_step == "manual_research_checklist_complete_continue_readonly_review"
    assert report.checklist_count == Decimal("1.000000")
    assert report.covered_checklist_count == Decimal("1.000000")
    assert report.incomplete_checklist_count == Decimal("0.000000")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    payload = module.probability_event_manual_research_checklist_coverage_report_payload(
        report,
    )
    assert payload["coverage_status"] == "covered"
    assert payload["missing_checklist_items"] == []
    assert payload["manual_next_step"] == (
        "manual_research_checklist_complete_continue_readonly_review"
    )
    assert payload["checklist_count"] == "1.000000"
    assert payload["covered_checklist_count"] == "1.000000"
    assert payload["incomplete_checklist_count"] == "0.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_json_numbers(payload)


def test_missing_checklist_items_are_deduplicated_across_rows() -> None:
    report = build_report(
        checklist(
            checklist_ref="event-beta",
            probability_screen_present=False,
            source_anchor_present=False,
            independent_sources_present=False,
        ),
        checklist(
            checklist_ref="event-gamma",
            probability_screen_present=False,
            resolution_rules_present=False,
            team_route_present=False,
            memory_policy_present=False,
            cost_gate_present=False,
            manual_operator_packet_present=False,
        ),
    )

    assert report.coverage_status == "missing"
    assert report.missing_checklist_items == REQUIRED_ITEMS
    assert report.reason_codes == (
        "cost_gate_missing",
        "independent_sources_missing",
        "manual_operator_packet_missing",
        "memory_policy_missing",
        "probability_event_manual_research_checklist_missing",
        "probability_screen_missing",
        "resolution_rules_missing",
        "source_anchor_missing",
        "team_route_missing",
    )
    assert report.manual_next_step == (
        "collect_missing_manual_research_checklist_items_before_any_operator_decision"
    )
    assert report.checklist_count == Decimal("2.000000")
    assert report.covered_checklist_count == Decimal("0.000000")
    assert report.incomplete_checklist_count == Decimal("2.000000")


def test_empty_report_requires_all_manual_research_checklist_items() -> None:
    report = build_report()

    assert report.coverage_status == "missing"
    assert report.missing_checklist_items == REQUIRED_ITEMS
    assert report.reason_codes == (
        "probability_event_manual_research_checklist_no_inputs",
    )
    assert report.manual_next_step == "collect_all_manual_research_checklist_items"
    assert report.checklist_count == Decimal("0.000000")
    assert report.covered_checklist_count == Decimal("0.000000")
    assert report.incomplete_checklist_count == Decimal("0.000000")


def test_dataclasses_are_frozen_decimal_only_and_hard_flags_are_enforced() -> None:
    module = api()
    item = checklist()
    report = build_report(item)

    records = (item, report)
    for record in records:
        assert is_dataclass(record)
        assert record.__dataclass_params__.frozen is True
        assert record.paper_only is True
        assert record.report_only is True
        assert record.readonly is True
        for field in fields(record):
            value = getattr(record, field.name)
            if isinstance(value, Decimal):
                assert type(value) is Decimal, field.name
        with pytest.raises(FrozenInstanceError):
            record.paper_only = False  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadReport(module.ProbabilityEventManualResearchChecklistCoverageReport):
            pass

    with pytest.raises(ValueError, match="paper_only"):
        replace(item, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(report, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="generated_at must be exactly datetime"):
        build_report(item, generated_at="2026-07-11T12:00:00Z")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="observed_at must not be after generated_at"):
        build_report(
            checklist(observed_at=datetime(2026, 7, 11, 13, 0, tzinfo=UTC)),
        )


def test_module_exposes_no_execution_or_persistence_surfaces() -> None:
    module = api()
    forbidden_fragments = (
        "auth",
        "database",
        "dsn",
        "execute",
        "execution",
        "live",
        "order",
        "persist",
        "private",
        "sign",
        "submit",
        "token",
        "trade",
        "trading",
        "wallet",
    )

    public_names = [name for name in dir(module) if not name.startswith("_")]
    offenders = [
        name
        for name in public_names
        if any(fragment in name.lower() for fragment in forbidden_fragments)
    ]
    assert offenders == []

    payload = module.probability_event_manual_research_checklist_coverage_report_payload(
        build_report(checklist()),
    )
    assert set(payload) == {
        "generated_at",
        "checklist_count",
        "covered_checklist_count",
        "incomplete_checklist_count",
        "coverage_status",
        "missing_checklist_items",
        "reason_codes",
        "manual_next_step",
        "paper_only",
        "report_only",
        "readonly",
    }
