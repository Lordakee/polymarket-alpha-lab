from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from polymarket_alpha_lab.paper_autonomous_proposal_risk_gate import (
    DEFAULT_PAPER_AUTONOMOUS_PROPOSAL_RISK_GATE_CONFIG_VERSION,
    PASS_REASON_CODE,
    PaperAutonomousProposalRiskGateConfig,
    PaperAutonomousProposalRiskGateReport,
    build_paper_autonomous_proposal_risk_gate_report,
)
from tests.test_paper_autonomous_screening_decision_support_gate_transition import (
    _gate_report,
)
from polymarket_alpha_lab.paper_autonomous_proposal import (
    build_paper_autonomous_proposal_report,
)


def _proposal_report(*, gate_status: str = "pass") -> PaperAutonomousProposalReport:
    gate = _gate_report(generated_at=datetime(2026, 6, 24, tzinfo=UTC), gate_status=gate_status)
    return build_paper_autonomous_proposal_report(
        gate_report=gate,
        generated_at=datetime(2026, 6, 25, tzinfo=UTC),
    )


def test_risk_gate_passes_clean_candidate_proposals():
    proposal_report = _proposal_report(gate_status="pass")
    report = build_paper_autonomous_proposal_risk_gate_report(
        proposal_report=proposal_report,
        generated_at=datetime(2026, 6, 25, tzinfo=UTC),
    )
    assert isinstance(report, PaperAutonomousProposalRiskGateReport)
    assert report.gate_status == "pass"
    assert report.recommended_next_step == "allow_paper_proposal_to_paper_broker"
    assert report.source_proposal_status == "candidate"
    assert report.reason_codes == (PASS_REASON_CODE,)
    assert report.config_version == DEFAULT_PAPER_AUTONOMOUS_PROPOSAL_RISK_GATE_CONFIG_VERSION
    assert report.paper_only is True and report.report_only is True and report.readonly is True


def test_risk_gate_blocks_when_source_proposal_blocks():
    proposal_report = _proposal_report(gate_status="blocked")
    report = build_paper_autonomous_proposal_risk_gate_report(
        proposal_report=proposal_report,
        generated_at=datetime(2026, 6, 25, tzinfo=UTC),
    )
    assert report.gate_status == "blocked"
    assert report.recommended_next_step == "block_paper_proposal_pending_risk_repair"
    assert "source_proposal_blocked" in report.blocked_reason_codes


def test_risk_gate_watches_when_source_proposal_watches():
    proposal_report = _proposal_report(gate_status="watch")
    report = build_paper_autonomous_proposal_risk_gate_report(
        proposal_report=proposal_report,
        generated_at=datetime(2026, 6, 25, tzinfo=UTC),
    )
    assert report.gate_status == "watch"
    assert report.recommended_next_step == "hold_paper_proposal_for_risk_review"
    assert "source_proposal_watch" in report.watch_reason_codes


def test_risk_gate_rejects_naive_generated_at():
    proposal_report = _proposal_report()
    with pytest.raises(ValueError, match="timezone-aware"):
        build_paper_autonomous_proposal_risk_gate_report(
            proposal_report=proposal_report,
            generated_at=datetime(2026, 6, 25),
        )


def test_risk_gate_rejects_wrong_proposal_report_type():
    with pytest.raises(ValueError, match="exactly PaperAutonomousProposalReport"):
        build_paper_autonomous_proposal_risk_gate_report(
            proposal_report="not_a_report",
            generated_at=datetime(2026, 6, 25, tzinfo=UTC),
        )


def test_risk_gate_rejects_subclassed_config():
    with pytest.raises(TypeError, match="does not support subclassing"):

        class SubConfig(PaperAutonomousProposalRiskGateConfig):
            pass
