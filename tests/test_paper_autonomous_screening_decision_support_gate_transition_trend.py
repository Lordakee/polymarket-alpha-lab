from __future__ import annotations

from datetime import UTC, datetime

from polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate_transition import (
    build_paper_autonomous_screening_decision_support_gate_transition_report,
)
from polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate_transition_trend import (
    DEFAULT_PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_TRANSITION_TREND_CONFIG_VERSION,
    PaperAutonomousScreeningDecisionSupportGateTransitionTrendReport,
    build_paper_autonomous_screening_decision_support_gate_transition_trend_report,
)
from tests.test_paper_autonomous_screening_decision_support_gate_transition import (
    _gate_report,
)


def test_transition_trend_report_summarizes_latest_transition_changes():
    r1 = _gate_report(generated_at=datetime(2026, 6, 20, tzinfo=UTC), gate_status="pass")
    r2 = _gate_report(generated_at=datetime(2026, 6, 21, tzinfo=UTC), gate_status="watch")
    transition_report = build_paper_autonomous_screening_decision_support_gate_transition_report([r1, r2], generated_at=datetime(2026, 6, 22, tzinfo=UTC))
    trend_report = build_paper_autonomous_screening_decision_support_gate_transition_trend_report([transition_report], generated_at=datetime(2026, 6, 23, tzinfo=UTC))
    assert isinstance(trend_report, PaperAutonomousScreeningDecisionSupportGateTransitionTrendReport)
    assert trend_report.transition_report_count == 1
    assert trend_report.latest_from_gate_status == "pass"
    assert trend_report.latest_to_gate_status == "watch"
    assert trend_report.latest_transition_count == 1
    assert trend_report.config_version == DEFAULT_PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_TRANSITION_TREND_CONFIG_VERSION
    assert trend_report.paper_only is True and trend_report.report_only is True and trend_report.readonly is True


def test_transition_trend_report_supports_empty_input():
    report = build_paper_autonomous_screening_decision_support_gate_transition_trend_report([], generated_at=datetime(2026, 6, 23, tzinfo=UTC))
    assert report.transition_report_count == 0
    assert report.latest_from_gate_status is None
    assert report.latest_to_gate_status is None
    assert report.latest_transition_count == 0
    assert report.latest_instability_ratio is None
