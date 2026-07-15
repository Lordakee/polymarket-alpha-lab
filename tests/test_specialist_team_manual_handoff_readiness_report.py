from decimal import Decimal

import pytest

from polymarket_alpha_lab.specialist_team_manual_handoff_readiness_report import (
    SpecialistTeamManualHandoffReadinessInput,
    SpecialistTeamManualHandoffReadinessReport,
    build_specialist_team_manual_handoff_readiness_report,
    specialist_team_manual_handoff_readiness_report_payload,
)


def _input(
    *,
    primary_team_id: str = "research-team-alpha",
    operator_owner_present: bool = True,
    research_packet_present: bool = True,
    source_gaps_count: Decimal = Decimal("0.000000"),
    memory_policy_status: str = "pass",
    handoff_note_present: bool = True,
) -> SpecialistTeamManualHandoffReadinessInput:
    return SpecialistTeamManualHandoffReadinessInput(
        primary_team_id=primary_team_id,
        operator_owner_present=operator_owner_present,
        research_packet_present=research_packet_present,
        source_gaps_count=source_gaps_count,
        memory_policy_status=memory_policy_status,
        handoff_note_present=handoff_note_present,
    )


def test_ready_report_when_all_manual_handoff_inputs_are_present() -> None:
    report = build_specialist_team_manual_handoff_readiness_report(_input())

    assert report.handoff_status == "ready"
    assert report.reason_codes == ("manual_handoff_ready",)
    assert report.manual_next_step == "operator_manual_review"
    assert report.primary_team_id == "research-team-alpha"
    assert report.source_gaps_count == Decimal("0.000000")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


@pytest.mark.parametrize(
    ("override", "reason_code", "next_step"),
    (
        (
            {"operator_owner_present": False},
            "operator_owner_missing",
            "assign_operator_owner_before_manual_handoff",
        ),
        (
            {"research_packet_present": False},
            "research_packet_missing",
            "attach_research_packet_before_manual_handoff",
        ),
        (
            {"source_gaps_count": Decimal("2.000000")},
            "source_gaps_open",
            "close_source_gaps_before_manual_handoff",
        ),
        (
            {"memory_policy_status": "watch"},
            "memory_policy_watch",
            "resolve_memory_policy_watch_before_manual_handoff",
        ),
        (
            {"memory_policy_status": "block"},
            "memory_policy_block",
            "resolve_memory_policy_block_before_manual_handoff",
        ),
        (
            {"handoff_note_present": False},
            "handoff_note_missing",
            "add_handoff_note_before_manual_handoff",
        ),
    ),
)
def test_not_ready_report_explains_each_missing_manual_handoff_requirement(
    override: dict[str, object],
    reason_code: str,
    next_step: str,
) -> None:
    report = build_specialist_team_manual_handoff_readiness_report(_input(**override))

    assert report.handoff_status == "not_ready"
    assert reason_code in report.reason_codes
    assert report.manual_next_step == next_step


def test_multiple_gaps_keep_deterministic_reason_priority_and_first_next_step() -> None:
    report = build_specialist_team_manual_handoff_readiness_report(
        _input(
            operator_owner_present=False,
            research_packet_present=False,
            source_gaps_count=Decimal("3.000000"),
            memory_policy_status="watch",
            handoff_note_present=False,
        ),
    )

    assert report.handoff_status == "not_ready"
    assert report.reason_codes == (
        "operator_owner_missing",
        "research_packet_missing",
        "source_gaps_open",
        "memory_policy_watch",
        "handoff_note_missing",
    )
    assert report.manual_next_step == "assign_operator_owner_before_manual_handoff"


def test_payload_is_json_ready_and_contains_only_readonly_report_fields() -> None:
    report = build_specialist_team_manual_handoff_readiness_report(
        _input(source_gaps_count=Decimal("1.000000")),
    )

    payload = specialist_team_manual_handoff_readiness_report_payload(report)

    assert payload == {
        "primary_team_id": "research-team-alpha",
        "operator_owner_present": True,
        "research_packet_present": True,
        "source_gaps_count": "1.000000",
        "memory_policy_status": "pass",
        "handoff_note_present": True,
        "handoff_status": "not_ready",
        "reason_codes": ["source_gaps_open"],
        "manual_next_step": "close_source_gaps_before_manual_handoff",
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    blocked_fragments = ("live", "auth", "wallet", "order")
    assert all(fragment not in repr(payload).lower() for fragment in blocked_fragments)


def test_payload_rejects_unsafe_dict_and_float_numbers() -> None:
    report = build_specialist_team_manual_handoff_readiness_report(_input())
    payload = specialist_team_manual_handoff_readiness_report_payload(report)

    unsafe_payload = dict(payload)
    unsafe_payload["wallet_action"] = "none"
    with pytest.raises(ValueError, match="unsafe"):
        specialist_team_manual_handoff_readiness_report_payload(unsafe_payload)

    numeric_payload = dict(payload)
    numeric_payload["source_gaps_count"] = 1.0
    with pytest.raises(ValueError, match="Decimal|numeric"):
        specialist_team_manual_handoff_readiness_report_payload(numeric_payload)


def test_rejects_non_decimal_source_gap_counts_and_false_hard_flags() -> None:
    with pytest.raises(ValueError, match="source_gaps_count.*Decimal"):
        _input(source_gaps_count=1)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="paper_only"):
        SpecialistTeamManualHandoffReadinessInput(
            primary_team_id="research-team-alpha",
            operator_owner_present=True,
            research_packet_present=True,
            source_gaps_count=Decimal("0.000000"),
            memory_policy_status="pass",
            handoff_note_present=True,
            paper_only=False,
        )

    with pytest.raises(ValueError, match="readonly"):
        SpecialistTeamManualHandoffReadinessReport(
            primary_team_id="research-team-alpha",
            operator_owner_present=True,
            research_packet_present=True,
            source_gaps_count=Decimal("0.000000"),
            memory_policy_status="pass",
            handoff_note_present=True,
            handoff_status="ready",
            reason_codes=("manual_handoff_ready",),
            manual_next_step="operator_manual_review",
            readonly=False,
        )


@pytest.mark.parametrize(
    ("field_name", "value"),
    (
        ("primary_team_id", ""),
        ("memory_policy_status", "ready"),
    ),
)
def test_rejects_invalid_public_inputs(field_name: str, value: object) -> None:
    kwargs = {
        "primary_team_id": "research-team-alpha",
        "operator_owner_present": True,
        "research_packet_present": True,
        "source_gaps_count": Decimal("0.000000"),
        "memory_policy_status": "pass",
        "handoff_note_present": True,
    }
    kwargs[field_name] = value

    with pytest.raises(ValueError, match=field_name):
        SpecialistTeamManualHandoffReadinessInput(**kwargs)
