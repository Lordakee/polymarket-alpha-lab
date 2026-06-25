from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from polymarket_alpha_lab.paper_autonomous_proposal import (
    DEFAULT_PAPER_AUTONOMOUS_PROPOSAL_CONFIG_VERSION,
    PASS_REASON_CODE,
    PaperAutonomousProposalConfig,
    PaperAutonomousProposalReport,
    PaperAutonomousProposalRow,
    build_paper_autonomous_proposal_report,
)
from tests.test_paper_autonomous_screening_decision_support_gate_transition import (
    _gate_report,
)


def test_proposal_report_passes_clean_gate_with_ready_candidates():
    gate_report = _gate_report(generated_at=datetime(2026, 6, 24, tzinfo=UTC), gate_status="pass")
    report = build_paper_autonomous_proposal_report(
        gate_report=gate_report,
        generated_at=datetime(2026, 6, 25, tzinfo=UTC),
    )
    assert isinstance(report, PaperAutonomousProposalReport)
    assert report.proposal_status == "candidate"
    assert report.recommended_next_step == "route_to_paper_proposal_risk_gate"
    assert report.proposal_count == 1
    assert report.proposals[0].market_slug == "__aggregate_queue_ready__"
    assert report.source_gate_status == "pass"
    assert report.config_version == DEFAULT_PAPER_AUTONOMOUS_PROPOSAL_CONFIG_VERSION
    assert report.paper_only is True and report.report_only is True and report.readonly is True


def test_proposal_report_blocks_when_gate_blocks():
    gate_report = _gate_report(generated_at=datetime(2026, 6, 24, tzinfo=UTC), gate_status="blocked")
    report = build_paper_autonomous_proposal_report(
        gate_report=gate_report,
        generated_at=datetime(2026, 6, 25, tzinfo=UTC),
    )
    assert report.proposal_status == "blocked"
    assert report.recommended_next_step == "block_paper_proposal_pending_repair"
    assert report.proposal_count == 0
    assert report.proposals == ()
    assert report.reason_codes == ("paper_autonomous_proposal_gate_blocked",)


def test_proposal_report_watches_when_gate_watches():
    gate_report = _gate_report(generated_at=datetime(2026, 6, 24, tzinfo=UTC), gate_status="watch")
    report = build_paper_autonomous_proposal_report(
        gate_report=gate_report,
        generated_at=datetime(2026, 6, 25, tzinfo=UTC),
    )
    assert report.proposal_status == "watch"
    assert report.recommended_next_step == "hold_paper_proposal_for_fresh_evidence"
    assert report.proposal_count == 0
    assert report.proposals == ()
    assert report.reason_codes == ("paper_autonomous_proposal_gate_watch",)


def test_proposal_report_rejects_naive_generated_at():
    gate_report = _gate_report(generated_at=datetime(2026, 6, 24, tzinfo=UTC), gate_status="pass")
    with pytest.raises(ValueError, match="timezone-aware"):
        build_paper_autonomous_proposal_report(
            gate_report=gate_report,
            generated_at=datetime(2026, 6, 25),
        )


def test_proposal_report_rejects_wrong_gate_report_type():
    with pytest.raises(ValueError, match="exactly PaperAutonomousScreeningDecisionSupportGateReport"):
        build_paper_autonomous_proposal_report(
            gate_report="not_a_report",
            generated_at=datetime(2026, 6, 25, tzinfo=UTC),
        )


def test_proposal_config_rejects_subclassing():
    with pytest.raises(TypeError, match="does not support subclassing"):

        class SubConfig(PaperAutonomousProposalConfig):
            pass
