from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate import (
    PaperAutonomousScreeningDecisionSupportGateReport,
    build_paper_autonomous_screening_decision_support_gate_report,
)
from polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate_transition import (
    DEFAULT_PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_TRANSITION_CONFIG_VERSION,
    PaperAutonomousScreeningDecisionSupportGateTransitionReport,
    build_paper_autonomous_screening_decision_support_gate_transition_report,
)
from tests.test_paper_autonomous_screening_decision_support_gate import (
    _priority_report,
    _risk_report,
    _operator_flow_gate_report,
)


def _gate_report(*, generated_at: datetime, gate_status: str) -> PaperAutonomousScreeningDecisionSupportGateReport:
    priority_report = _priority_report(generated_at=generated_at, action_status="research_ready" if gate_status == "pass" else "watch" if gate_status == "watch" else "blocked")
    risk_status = "pass" if gate_status == "pass" else "watch" if gate_status == "watch" else "blocked"
    risk_reason_codes = ("queue_risk_passed",) if risk_status == "pass" else ("source_queue_watch",) if risk_status == "watch" else ("source_queue_blocked",)
    risk_report = _risk_report(priority_report, status=risk_status, reason_codes=risk_reason_codes)
    operator_flow_gate_report = _operator_flow_gate_report(gate_status="pass" if gate_status == "pass" else "watch" if gate_status == "watch" else "blocked")
    return build_paper_autonomous_screening_decision_support_gate_report(
        operator_flow_gate_report=operator_flow_gate_report,
        priority_report=priority_report,
        risk_report=risk_report,
        generated_at=generated_at,
    )


def test_transition_report_reports_deterministic_status_transitions():
    t1 = datetime(2026, 6, 21, tzinfo=UTC)
    t2 = datetime(2026, 6, 22, tzinfo=UTC)
    r1 = _gate_report(generated_at=t1, gate_status="pass")
    r2 = _gate_report(generated_at=t2, gate_status="watch")
    report = build_paper_autonomous_screening_decision_support_gate_transition_report(
        [r1, r2],
        generated_at=datetime(2026, 6, 23, tzinfo=UTC),
    )
    assert isinstance(report, PaperAutonomousScreeningDecisionSupportGateTransitionReport)
    assert report.gate_report_count == 2
    assert report.transition_count == 1
    assert report.latest_from_gate_status == "pass"
    assert report.latest_to_gate_status == "watch"
    row = next(r for r in report.status_transition_rows if r.from_gate_status == "pass" and r.to_gate_status == "watch")
    assert row.transition_count == 1
    assert report.config_version == DEFAULT_PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_TRANSITION_CONFIG_VERSION


def test_transition_report_supports_empty_input():
    report = build_paper_autonomous_screening_decision_support_gate_transition_report(
        [],
        generated_at=datetime(2026, 6, 23, tzinfo=UTC),
    )
    assert report.gate_report_count == 0
    assert report.transition_count == 0
    assert report.latest_from_gate_status is None
    assert report.latest_to_gate_status is None
    assert report.status_transition_rows is None
    assert report.reason_change_rows is None
    assert report.paper_only is True and report.report_only is True and report.readonly is True
