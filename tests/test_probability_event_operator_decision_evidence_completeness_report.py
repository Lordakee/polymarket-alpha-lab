from __future__ import annotations

import importlib
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab."
    "probability_event_operator_decision_evidence_completeness_report"
)
GENERATED_AT = datetime(2026, 7, 11, 12, 0, tzinfo=UTC)
EVIDENCE_FLAGS = (
    "probability_screen_present",
    "team_route_present",
    "source_quality_present",
    "memory_policy_present",
    "cost_gate_present",
    "operator_packet_present",
    "manual_attestation_present",
)


def api() -> Any:
    return importlib.import_module(MODULE_NAME)


def evidence(**overrides: object) -> Any:
    module = api()
    values = {
        "evidence_ref": "event-alpha",
        "observed_at": GENERATED_AT,
        **{name: True for name in EVIDENCE_FLAGS},
    }
    values.update(overrides)
    return module.ProbabilityEventOperatorDecisionEvidence(**values)


def build_report(*items: object, generated_at: datetime = GENERATED_AT) -> Any:
    module = api()
    return module.build_probability_event_operator_decision_evidence_completeness_report(
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


def test_complete_single_evidence_passes_with_readonly_report_payload() -> None:
    module = api()
    report = build_report(evidence())

    assert report.completeness_status == "complete"
    assert report.missing_evidence_sections == ()
    assert report.reason_codes == ("probability_event_operator_decision_evidence_complete",)
    assert report.manual_next_step == "manual_attestation_complete_continue_readonly_review"
    assert report.evidence_count == Decimal("1.000000")
    assert report.complete_evidence_count == Decimal("1.000000")
    assert report.incomplete_evidence_count == Decimal("0.000000")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    payload = module.probability_event_operator_decision_evidence_completeness_report_payload(
        report,
    )
    assert payload["completeness_status"] == "complete"
    assert payload["missing_evidence_sections"] == []
    assert payload["manual_next_step"] == (
        "manual_attestation_complete_continue_readonly_review"
    )
    assert payload["evidence_count"] == "1.000000"
    assert payload["complete_evidence_count"] == "1.000000"
    assert payload["incomplete_evidence_count"] == "0.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_json_numbers(payload)


def test_missing_sections_block_and_deduplicate_across_evidence_rows() -> None:
    report = build_report(
        evidence(
            evidence_ref="event-beta",
            probability_screen_present=False,
            team_route_present=False,
            source_quality_present=False,
        ),
        evidence(
            evidence_ref="event-gamma",
            probability_screen_present=False,
            memory_policy_present=False,
            cost_gate_present=False,
            operator_packet_present=False,
            manual_attestation_present=False,
        ),
    )

    assert report.completeness_status == "incomplete"
    assert report.missing_evidence_sections == (
        "probability_screen",
        "team_route",
        "source_quality",
        "memory_policy",
        "cost_gate",
        "operator_packet",
        "manual_attestation",
    )
    assert report.reason_codes == (
        "cost_gate_missing",
        "manual_attestation_missing",
        "memory_policy_missing",
        "operator_packet_missing",
        "probability_event_operator_decision_evidence_incomplete",
        "probability_screen_missing",
        "source_quality_missing",
        "team_route_missing",
    )
    assert report.manual_next_step == (
        "collect_missing_evidence_sections_before_any_operator_decision"
    )
    assert report.evidence_count == Decimal("2.000000")
    assert report.complete_evidence_count == Decimal("0.000000")
    assert report.incomplete_evidence_count == Decimal("2.000000")


def test_empty_report_blocks_for_manual_evidence_collection() -> None:
    report = build_report()

    assert report.completeness_status == "incomplete"
    assert report.missing_evidence_sections == (
        "probability_screen",
        "team_route",
        "source_quality",
        "memory_policy",
        "cost_gate",
        "operator_packet",
        "manual_attestation",
    )
    assert report.reason_codes == (
        "probability_event_operator_decision_evidence_no_inputs",
    )
    assert report.manual_next_step == "collect_all_required_evidence_sections"
    assert report.evidence_count == Decimal("0.000000")
    assert report.complete_evidence_count == Decimal("0.000000")
    assert report.incomplete_evidence_count == Decimal("0.000000")


def test_dataclasses_are_frozen_decimal_only_and_hard_flags_are_enforced() -> None:
    module = api()
    item = evidence()
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

        class BadReport(module.ProbabilityEventOperatorDecisionEvidenceCompletenessReport):
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
            evidence(observed_at=datetime(2026, 7, 11, 13, 0, tzinfo=UTC)),
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

    payload = module.probability_event_operator_decision_evidence_completeness_report_payload(
        build_report(evidence()),
    )
    assert set(payload) == {
        "generated_at",
        "evidence_count",
        "complete_evidence_count",
        "incomplete_evidence_count",
        "completeness_status",
        "missing_evidence_sections",
        "reason_codes",
        "manual_next_step",
        "paper_only",
        "report_only",
        "readonly",
    }
