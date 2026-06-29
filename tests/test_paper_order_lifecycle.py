from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from polymarket_alpha_lab.paper_order_lifecycle import (
    DEFAULT_PAPER_ORDER_LIFECYCLE_CONFIG_VERSION,
    PaperOrderLifecycleConfig,
    PaperOrderLifecycleRecord,
    build_paper_order_lifecycle_record,
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
from polymarket_alpha_lab.paper_broker import (
    build_paper_broker_execution_record,
)


def _broker_record(*, gate_status: str = "pass"):
    gate = _gate_report(generated_at=datetime(2026, 6, 24, tzinfo=UTC), gate_status=gate_status)
    proposal = build_paper_autonomous_proposal_report(
        gate_report=gate,
        generated_at=datetime(2026, 6, 25, tzinfo=UTC),
    )
    risk_gate = build_paper_autonomous_proposal_risk_gate_report(
        proposal_report=proposal,
        generated_at=datetime(2026, 6, 25, tzinfo=UTC),
    )
    return build_paper_broker_execution_record(
        risk_gate_report=risk_gate,
        generated_at=datetime(2026, 6, 25, tzinfo=UTC),
    )


def test_lifecycle_record_fills_paper_submitted_immediately():
    broker = _broker_record(gate_status="pass")
    record = build_paper_order_lifecycle_record(
        broker_record=broker,
        generated_at=datetime(2026, 6, 25, tzinfo=UTC),
    )
    assert isinstance(record, PaperOrderLifecycleRecord)
    assert record.lifecycle_status == "paper_filled"
    assert record.recommended_next_step == "record_paper_outcome"
    assert record.fill_notional > 0
    assert record.is_terminal is True
    assert record.config_version == DEFAULT_PAPER_ORDER_LIFECYCLE_CONFIG_VERSION
    assert record.paper_only is True and record.report_only is True and record.readonly is True


def test_lifecycle_record_blocks_when_broker_blocks():
    broker = _broker_record(gate_status="blocked")
    record = build_paper_order_lifecycle_record(
        broker_record=broker,
        generated_at=datetime(2026, 6, 25, tzinfo=UTC),
    )
    assert record.lifecycle_status == "risk_blocked"
    assert record.recommended_next_step == "archive_proposal"
    assert record.fill_notional == Decimal("0.000000")
    assert record.is_terminal is True


def test_lifecycle_record_pends_when_broker_holds():
    broker = _broker_record(gate_status="watch")
    record = build_paper_order_lifecycle_record(
        broker_record=broker,
        generated_at=datetime(2026, 6, 25, tzinfo=UTC),
    )
    assert record.lifecycle_status == "human_approval_pending"
    assert record.recommended_next_step == "await_human_decision"
    assert record.fill_notional == Decimal("0.000000")
    assert record.is_terminal is False


def test_lifecycle_record_rejects_naive_generated_at():
    broker = _broker_record()
    with pytest.raises(ValueError, match="timezone-aware"):
        build_paper_order_lifecycle_record(
            broker_record=broker,
            generated_at=datetime(2026, 6, 25),
        )


def test_lifecycle_record_rejects_wrong_broker_type():
    with pytest.raises(ValueError, match="exactly PaperBrokerExecutionRecord"):
        build_paper_order_lifecycle_record(
            broker_record="not_a_record",
            generated_at=datetime(2026, 6, 25, tzinfo=UTC),
        )


def test_lifecycle_record_rejects_live_route_status():
    with pytest.raises(ValueError, match="lifecycle_status"):
        PaperOrderLifecycleRecord(
            generated_at=datetime(2026, 6, 25, tzinfo=UTC),
            config_version=DEFAULT_PAPER_ORDER_LIFECYCLE_CONFIG_VERSION,
            lifecycle_status="reviewed",
            recommended_next_step="route_to_live_broker",
            source_execution_status="paper_submitted",
            source_execution_notional=Decimal("0.000000"),
            fill_notional=Decimal("0.000000"),
            is_terminal=False,
            reason_codes=("paper_order_lifecycle_reviewed",),
        )


def test_lifecycle_record_rejects_subclassed_config():
    with pytest.raises(TypeError, match="does not support subclassing"):

        class SubConfig(PaperOrderLifecycleConfig):
            pass
