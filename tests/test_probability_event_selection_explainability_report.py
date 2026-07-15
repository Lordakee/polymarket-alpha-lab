from __future__ import annotations

import importlib
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest


GENERATED_AT = datetime(2026, 6, 22, 15, 0, tzinfo=UTC)


def d(value: str) -> Decimal:
    return Decimal(value)


def _module():
    return importlib.import_module(
        "polymarket_alpha_lab.probability_event_selection_explainability_report",
    )


def _component_status(
    *,
    component_name: str = "screen",
    status: str = "pass",
    reason_codes: tuple[str, ...] = ("screen_passed",),
    summary: str = "screen passed public criteria",
    severity_score: Decimal = d("0.000000"),
):
    module = _module()
    return module.ProbabilityEventSelectionComponentStatus(
        component_name=component_name,
        status=status,
        reason_codes=reason_codes,
        summary=summary,
        severity_score=severity_score,
    )


def _build(statuses, *, generated_at=GENERATED_AT, config=None):
    module = _module()
    return module.build_probability_event_selection_explainability_report(
        screen_status=statuses["screen_status"],
        team_route_status=statuses["team_route_status"],
        memory_policy=statuses["memory_policy"],
        source_quality_status=statuses["source_quality_status"],
        cost_gate_status=statuses["cost_gate_status"],
        operator_packet_status=statuses["operator_packet_status"],
        config=config or module.ProbabilityEventSelectionExplainabilityConfig(
            config_version="probability-event-selection-explainability-v0",
        ),
        generated_at=generated_at,
    )


def _ready_statuses():
    return {
        "screen_status": _component_status(
            component_name="screen",
            status="pass",
            reason_codes=("screen_passed",),
            summary="screen passed public criteria",
        ),
        "team_route_status": _component_status(
            component_name="team_route",
            status="pass",
            reason_codes=("team_route_available",),
            summary="team route available for review",
        ),
        "memory_policy": _component_status(
            component_name="memory_policy",
            status="pass",
            reason_codes=("memory_policy_satisfied",),
            summary="memory policy satisfied",
        ),
        "source_quality_status": _component_status(
            component_name="source_quality",
            status="pass",
            reason_codes=("source_quality_sufficient",),
            summary="source quality sufficient",
        ),
        "cost_gate_status": _component_status(
            component_name="cost_gate",
            status="pass",
            reason_codes=("cost_gate_passed",),
            summary="cost gate passed paper threshold",
        ),
        "operator_packet_status": _component_status(
            component_name="operator_packet",
            status="pass",
            reason_codes=("operator_packet_ready",),
            summary="operator packet ready for review",
        ),
    }


def test_all_passed_inputs_return_ready_safe_explanation():
    report = _build(_ready_statuses())

    module = _module()
    assert isinstance(report, module.ProbabilityEventSelectionExplainabilityReport)
    assert report.generated_at == GENERATED_AT
    assert report.config_version == "probability-event-selection-explainability-v0"
    assert report.selection_status == "ready"
    assert report.status == "ready"
    assert report.component_count == 6
    assert report.pass_count == 6
    assert report.watch_count == 0
    assert report.blocked_count == 0
    assert report.blocked_reason_codes == ()
    assert report.watch_reason_codes == ()
    assert report.reason_codes == ("selection_ready",)
    assert report.selection_explanation == (
        "Selection ready for paper review: screen passed public criteria; "
        "team route available for review; memory policy satisfied; "
        "source quality sufficient; cost gate passed paper threshold; "
        "operator packet ready for review."
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_blocked_components_win_and_reason_codes_are_deduplicated_in_component_order():
    statuses = _ready_statuses()
    statuses["source_quality_status"] = _component_status(
        component_name="source_quality",
        status="blocked",
        reason_codes=("source_quality_missing", "shared_attention"),
        summary="source quality missing independent support",
        severity_score=d("0.900000"),
    )
    statuses["cost_gate_status"] = _component_status(
        component_name="cost_gate",
        status="blocked",
        reason_codes=("shared_attention", "cost_gate_failed"),
        summary="cost gate failed paper threshold",
        severity_score=d("0.800000"),
    )
    statuses["operator_packet_status"] = _component_status(
        component_name="operator_packet",
        status="watch",
        reason_codes=("operator_packet_partial",),
        summary="operator packet needs manual review",
        severity_score=d("0.300000"),
    )

    report = _build(statuses)

    assert report.selection_status == "blocked"
    assert report.pass_count == 3
    assert report.watch_count == 1
    assert report.blocked_count == 2
    assert report.blocked_reason_codes == (
        "source_quality_missing",
        "shared_attention",
        "cost_gate_failed",
    )
    assert report.watch_reason_codes == ("operator_packet_partial",)
    assert report.reason_codes == (
        "blocked_selection_components_present",
        "watch_selection_components_present",
    )
    assert report.selection_explanation == (
        "Selection blocked for paper review: source quality missing independent "
        "support; cost gate failed paper threshold. Watch items: operator packet "
        "needs manual review."
    )


def test_watch_components_explain_attention_without_blocking():
    statuses = _ready_statuses()
    statuses["memory_policy"] = _component_status(
        component_name="memory_policy",
        status="watch",
        reason_codes=("memory_recheck_due",),
        summary="memory policy needs recheck",
        severity_score=d("0.200000"),
    )
    statuses["team_route_status"] = _component_status(
        component_name="team_route",
        status="watch",
        reason_codes=("team_route_capacity_watch",),
        summary="team route has limited capacity",
        severity_score=d("0.100000"),
    )

    report = _build(statuses)

    assert report.selection_status == "watch"
    assert report.blocked_reason_codes == ()
    assert report.watch_reason_codes == (
        "team_route_capacity_watch",
        "memory_recheck_due",
    )
    assert report.reason_codes == ("watch_selection_components_present",)
    assert report.selection_explanation == (
        "Selection needs watch review: team route has limited capacity; "
        "memory policy needs recheck."
    )


def test_empty_or_invalid_public_surface_is_rejected_and_output_never_exposes_execution_terms():
    module = _module()
    forbidden_terms = module.FORBIDDEN_PUBLIC_TERMS

    with pytest.raises(ValueError, match="component_name"):
        _component_status(component_name="wallet")
    with pytest.raises(ValueError, match="summary"):
        _component_status(summary="wallet balance is unavailable")
    with pytest.raises(ValueError, match="reason_codes"):
        _component_status(reason_codes=("account_missing",))

    statuses = _ready_statuses()
    statuses["operator_packet_status"] = _component_status(
        component_name="operator_packet",
        status="blocked",
        reason_codes=("operator_packet_missing",),
        summary="operator packet missing public review fields",
    )
    report = _build(statuses)
    public_text = " ".join(
        (
            report.selection_explanation,
            " ".join(report.blocked_reason_codes),
            " ".join(report.watch_reason_codes),
            " ".join(report.reason_codes),
        ),
    ).lower()
    assert not any(term in public_text for term in forbidden_terms)


def test_report_validates_flags_counts_order_decimal_inputs_datetime_and_is_frozen():
    statuses = _ready_statuses()
    module = _module()

    report = _build(
        statuses,
        generated_at=datetime(2026, 6, 22, 11, 0, tzinfo=timezone(timedelta(hours=-4))),
    )

    assert report.generated_at == GENERATED_AT
    with pytest.raises(FrozenInstanceError):
        report.selection_status = "blocked"
    with pytest.raises(FrozenInstanceError):
        report.component_statuses[0].status = "blocked"
    with pytest.raises(ValueError, match="blocked_count"):
        replace(report, blocked_count=1)
    with pytest.raises(ValueError, match="paper_only"):
        module.ProbabilityEventSelectionExplainabilityConfig(
            config_version="probability-event-selection-explainability-v0",
            paper_only=False,
        )
    with pytest.raises(ValueError, match="report_only"):
        replace(report, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report.component_statuses[0], readonly=False)
    with pytest.raises(ValueError, match="severity_score"):
        _component_status(severity_score=0.1)
    with pytest.raises(ValueError, match="generated_at"):
        _build(statuses, generated_at="2026-06-22T15:00:00Z")

    out_of_order = tuple(reversed(report.component_statuses))
    with pytest.raises(ValueError, match="component_statuses"):
        replace(report, component_statuses=out_of_order)
