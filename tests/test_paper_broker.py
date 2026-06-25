from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from polymarket_alpha_lab.paper_broker import (
    DEFAULT_PAPER_BROKER_CONFIG_VERSION,
    PaperBrokerConfig,
    PaperBrokerExecutionRecord,
    build_paper_broker_execution_record,
)
from tests.test_paper_autonomous_screening_decision_support_gate_transition import (
    _gate_report,
)
from polymarket_alpha_lab.paper_autonomous_proposal import (
    build_paper_autonomous_proposal_report,
)
from polymarket_alpha_lab.paper_autonomous_proposal_risk_gate import (
    build_paper_autonomous_proposal_risk_gate_report,
)


def _risk_gate_report(*, gate_status: str = "pass"):
    gate = _gate_report(generated_at=datetime(2026, 6, 24, tzinfo=UTC), gate_status=gate_status)
    proposal = build_paper_autonomous_proposal_report(
        gate_report=gate,
        generated_at=datetime(2026, 6, 25, tzinfo=UTC),
    )
    return build_paper_autonomous_proposal_risk_gate_report(
        proposal_report=proposal,
        generated_at=datetime(2026, 6, 25, tzinfo=UTC),
    )


def test_paper_broker_submits_clean_passing_proposals():
    risk_gate = _risk_gate_report(gate_status="pass")
    record = build_paper_broker_execution_record(
        risk_gate_report=risk_gate,
        generated_at=datetime(2026, 6, 25, tzinfo=UTC),
    )
    assert isinstance(record, PaperBrokerExecutionRecord)
    assert record.execution_status == "paper_submitted"
    assert record.recommended_next_step == "route_to_paper_order_lifecycle"
    assert record.execution_notional > 0
    assert record.config_version == DEFAULT_PAPER_BROKER_CONFIG_VERSION
    assert record.paper_only is True and record.report_only is True and record.readonly is True


def test_paper_broker_blocks_when_risk_gate_blocks():
    risk_gate = _risk_gate_report(gate_status="blocked")
    record = build_paper_broker_execution_record(
        risk_gate_report=risk_gate,
        generated_at=datetime(2026, 6, 25, tzinfo=UTC),
    )
    assert record.execution_status == "paper_blocked"
    assert record.recommended_next_step == "block_paper_execution_pending_repair"
    assert record.execution_notional == Decimal("0.000000")


def test_paper_broker_holds_when_risk_gate_watches():
    risk_gate = _risk_gate_report(gate_status="watch")
    record = build_paper_broker_execution_record(
        risk_gate_report=risk_gate,
        generated_at=datetime(2026, 6, 25, tzinfo=UTC),
    )
    assert record.execution_status == "paper_held"
    assert record.recommended_next_step == "hold_for_broker_review"
    assert record.execution_notional == Decimal("0.000000")


def test_paper_broker_rejects_naive_generated_at():
    risk_gate = _risk_gate_report()
    with pytest.raises(ValueError, match="timezone-aware"):
        build_paper_broker_execution_record(
            risk_gate_report=risk_gate,
            generated_at=datetime(2026, 6, 25),
        )


def test_paper_broker_rejects_wrong_risk_gate_type():
    with pytest.raises(ValueError, match="exactly PaperAutonomousProposalRiskGateReport"):
        build_paper_broker_execution_record(
            risk_gate_report="not_a_report",
            generated_at=datetime(2026, 6, 25, tzinfo=UTC),
        )


def test_paper_broker_rejects_subclassed_config():
    with pytest.raises(TypeError, match="does not support subclassing"):

        class SubConfig(PaperBrokerConfig):
            pass
