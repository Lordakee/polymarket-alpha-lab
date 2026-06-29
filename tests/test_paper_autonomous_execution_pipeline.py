from __future__ import annotations

from dataclasses import FrozenInstanceError, fields
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from polymarket_alpha_lab.paper_autonomous_execution_pipeline import (
    DEFAULT_PAPER_AUTONOMOUS_EXECUTION_PIPELINE_CONFIG_VERSION,
    PaperAutonomousExecutionPipelineReport,
    build_paper_autonomous_execution_pipeline_report,
)
from polymarket_alpha_lab.paper_autonomous_proposal import (
    PaperAutonomousProposalConfig,
)
from polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate import (
    PaperAutonomousScreeningDecisionSupportGateReport,
)
from tests.test_paper_autonomous_screening_decision_support_gate_transition import (
    _gate_report,
)


GENERATED_AT = datetime(2026, 6, 25, 12, 0, tzinfo=UTC)


def test_execution_pipeline_pass_flow_summarizes_all_paper_stages() -> None:
    gate_report = _gate_report(
        generated_at=datetime(2026, 6, 24, tzinfo=UTC),
        gate_status="pass",
    )

    report = build_paper_autonomous_execution_pipeline_report(
        gate_report=gate_report,
        generated_at=GENERATED_AT,
    )

    assert type(report) is PaperAutonomousExecutionPipelineReport
    assert report.generated_at == GENERATED_AT
    assert report.config_version == DEFAULT_PAPER_AUTONOMOUS_EXECUTION_PIPELINE_CONFIG_VERSION
    assert report.source_gate_status == "pass"
    assert report.proposal_status == "candidate"
    assert report.proposal_count == 1
    assert report.risk_gate_status == "pass"
    assert report.broker_execution_status == "paper_submitted"
    assert report.broker_execution_notional == Decimal("10.000000")
    assert report.lifecycle_status == "paper_filled"
    assert report.lifecycle_fill_notional == Decimal("10.000000")
    assert report.lifecycle_is_terminal is True
    assert report.reconciliation_status == "has_pending"
    assert report.reconciliation_total_positions == 1
    assert report.reconciliation_filled_pending_count == 1
    assert report.reconciliation_settled_win_count == 0
    assert report.reconciliation_settled_loss_count == 0
    assert report.reconciliation_expired_count == 0
    assert report.reconciliation_cancelled_count == 0
    assert report.reason_codes == (
        "paper_autonomous_proposal_candidate_passed",
        "paper_autonomous_proposal_risk_gate_passed",
        "paper_autonomous_screening_decision_support_gate_passed",
        "paper_broker_execution_submitted",
        "paper_execution_reconciliation_has_pending",
        "paper_order_lifecycle_filled",
    )
    assert report.recommended_next_step == "track_paper_execution_reconciliation"
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_execution_pipeline_watch_flow_holds_without_notional_or_fills() -> None:
    gate_report = _gate_report(
        generated_at=datetime(2026, 6, 24, tzinfo=UTC),
        gate_status="watch",
    )

    report = build_paper_autonomous_execution_pipeline_report(
        gate_report=gate_report,
        generated_at=GENERATED_AT,
    )

    assert report.source_gate_status == "watch"
    assert report.proposal_status == "watch"
    assert report.proposal_count == 0
    assert report.risk_gate_status == "watch"
    assert report.broker_execution_status == "paper_held"
    assert report.broker_execution_notional == Decimal("0.000000")
    assert report.lifecycle_status == "human_approval_pending"
    assert report.lifecycle_fill_notional == Decimal("0.000000")
    assert report.lifecycle_is_terminal is False
    assert report.reconciliation_status == "has_pending"
    assert report.reconciliation_total_positions == 1
    assert report.reconciliation_filled_pending_count == 1
    assert report.reconciliation_cancelled_count == 0
    assert report.reason_codes == tuple(sorted(report.reason_codes))
    assert "paper_autonomous_proposal_gate_watch" in report.reason_codes
    assert "source_proposal_watch" in report.reason_codes
    assert "paper_broker_gate_held" in report.reason_codes
    assert "paper_order_lifecycle_awaiting_approval" in report.reason_codes
    assert report.recommended_next_step == "hold_paper_autonomous_execution_pipeline"


def test_execution_pipeline_blocked_flow_blocks_without_notional_or_fills() -> None:
    gate_report = _gate_report(
        generated_at=datetime(2026, 6, 24, tzinfo=UTC),
        gate_status="blocked",
    )

    report = build_paper_autonomous_execution_pipeline_report(
        gate_report=gate_report,
        generated_at=GENERATED_AT,
    )

    assert report.source_gate_status == "blocked"
    assert report.proposal_status == "blocked"
    assert report.proposal_count == 0
    assert report.risk_gate_status == "blocked"
    assert report.broker_execution_status == "paper_blocked"
    assert report.broker_execution_notional == Decimal("0.000000")
    assert report.lifecycle_status == "risk_blocked"
    assert report.lifecycle_fill_notional == Decimal("0.000000")
    assert report.lifecycle_is_terminal is True
    assert report.reconciliation_status == "reconciled"
    assert report.reconciliation_total_positions == 1
    assert report.reconciliation_filled_pending_count == 0
    assert report.reconciliation_cancelled_count == 1
    assert "paper_autonomous_proposal_gate_blocked" in report.reason_codes
    assert "source_proposal_blocked" in report.reason_codes
    assert "paper_broker_gate_blocked" in report.reason_codes
    assert "paper_order_lifecycle_blocked" in report.reason_codes
    assert report.recommended_next_step == "repair_paper_autonomous_execution_pipeline"


def test_execution_pipeline_uses_source_gate_generated_at_when_not_supplied() -> None:
    generated_at = datetime(2026, 6, 24, tzinfo=UTC)
    gate_report = _gate_report(generated_at=generated_at, gate_status="pass")

    report = build_paper_autonomous_execution_pipeline_report(gate_report=gate_report)

    assert report.generated_at == generated_at


def test_execution_pipeline_rejects_naive_generated_at() -> None:
    gate_report = _gate_report(
        generated_at=datetime(2026, 6, 24, tzinfo=UTC),
        gate_status="pass",
    )

    with pytest.raises(ValueError, match="timezone-aware"):
        build_paper_autonomous_execution_pipeline_report(
            gate_report=gate_report,
            generated_at=datetime(2026, 6, 25),
        )


def test_execution_pipeline_rejects_wrong_gate_report_type() -> None:
    with pytest.raises(
        ValueError,
        match="gate_report must be exactly PaperAutonomousScreeningDecisionSupportGateReport",
    ):
        build_paper_autonomous_execution_pipeline_report(
            gate_report="not_a_report",
            generated_at=GENERATED_AT,
        )


def test_execution_pipeline_rejects_subclassed_gate_report() -> None:
    gate_report = _gate_report(
        generated_at=datetime(2026, 6, 24, tzinfo=UTC),
        gate_status="pass",
    )

    class SubclassedGateReport(PaperAutonomousScreeningDecisionSupportGateReport):
        pass

    subclassed = SubclassedGateReport(
        **{
            field.name: getattr(gate_report, field.name)
            for field in fields(PaperAutonomousScreeningDecisionSupportGateReport)
        },
    )

    with pytest.raises(
        ValueError,
        match="gate_report must be exactly PaperAutonomousScreeningDecisionSupportGateReport",
    ):
        build_paper_autonomous_execution_pipeline_report(
            gate_report=subclassed,
            generated_at=GENERATED_AT,
        )


def test_execution_pipeline_rejects_wrong_config_type() -> None:
    gate_report = _gate_report(
        generated_at=datetime(2026, 6, 24, tzinfo=UTC),
        gate_status="pass",
    )

    with pytest.raises(
        ValueError,
        match="proposal_config must be exactly PaperAutonomousProposalConfig",
    ):
        build_paper_autonomous_execution_pipeline_report(
            gate_report=gate_report,
            proposal_config="not_a_config",
            generated_at=GENERATED_AT,
        )


def test_execution_pipeline_rejects_false_hard_flags_on_source_gate() -> None:
    gate_report = _gate_report(
        generated_at=datetime(2026, 6, 24, tzinfo=UTC),
        gate_status="pass",
    )
    object.__setattr__(gate_report, "paper_only", False)

    with pytest.raises(ValueError, match="paper_only must be True for gate report"):
        build_paper_autonomous_execution_pipeline_report(
            gate_report=gate_report,
            generated_at=GENERATED_AT,
        )


def test_execution_pipeline_report_is_frozen() -> None:
    gate_report = _gate_report(
        generated_at=datetime(2026, 6, 24, tzinfo=UTC),
        gate_status="pass",
    )
    report = build_paper_autonomous_execution_pipeline_report(
        gate_report=gate_report,
        generated_at=GENERATED_AT,
    )

    with pytest.raises(FrozenInstanceError):
        report.source_gate_status = "blocked"  # type: ignore[misc]


def test_execution_pipeline_reason_codes_are_deterministic() -> None:
    gate_report = _gate_report(
        generated_at=datetime(2026, 6, 24, tzinfo=UTC),
        gate_status="pass",
    )

    first = build_paper_autonomous_execution_pipeline_report(
        gate_report=gate_report,
        generated_at=GENERATED_AT,
    )
    second = build_paper_autonomous_execution_pipeline_report(
        gate_report=gate_report,
        generated_at=GENERATED_AT,
    )

    assert first.reason_codes == second.reason_codes
    assert first.reason_codes == tuple(sorted(first.reason_codes))
    assert len(first.reason_codes) == len(set(first.reason_codes))
    assert all(type(reason_code) is str for reason_code in first.reason_codes)


def test_execution_pipeline_accepts_custom_proposal_config() -> None:
    gate_report = _gate_report(
        generated_at=datetime(2026, 6, 24, tzinfo=UTC),
        gate_status="pass",
    )
    proposal_config = PaperAutonomousProposalConfig(
        min_queue_ready_notional=Decimal("20.000000"),
    )

    report = build_paper_autonomous_execution_pipeline_report(
        gate_report=gate_report,
        proposal_config=proposal_config,
        generated_at=GENERATED_AT,
    )

    assert report.proposal_status == "watch"
    assert report.risk_gate_status == "watch"
    assert report.broker_execution_status == "paper_held"
    assert report.reason_codes == tuple(sorted(report.reason_codes))
