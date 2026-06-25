"""Tests for paper execution reconciliation module."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from polymarket_alpha_lab.paper_execution_reconciliation import (
    PaperExecutionReconciliationConfig,
    PaperExecutionReconciliationPositionRow,
    PaperExecutionReconciliationReport,
    build_paper_execution_reconciliation_report,
)
from polymarket_alpha_lab.paper_order_lifecycle import (
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


def _lifecycle_record(*, gate_status: str = "pass") -> PaperOrderLifecycleRecord:
    gate = _gate_report(generated_at=datetime(2026, 6, 24, tzinfo=UTC), gate_status=gate_status)
    proposal = build_paper_autonomous_proposal_report(
        gate_report=gate,
        generated_at=datetime(2026, 6, 25, tzinfo=UTC),
    )
    risk_gate = build_paper_autonomous_proposal_risk_gate_report(
        proposal_report=proposal,
        generated_at=datetime(2026, 6, 25, tzinfo=UTC),
    )
    broker = build_paper_broker_execution_record(
        risk_gate_report=risk_gate,
        generated_at=datetime(2026, 6, 25, tzinfo=UTC),
    )
    return build_paper_order_lifecycle_record(
        broker_record=broker,
        generated_at=datetime(2026, 6, 25, tzinfo=UTC),
    )


def test_reconciliation_empty_records() -> None:
    report = build_paper_execution_reconciliation_report(
        lifecycle_records=(),
        generated_at=datetime(2026, 6, 25, tzinfo=UTC),
    )
    assert isinstance(report, PaperExecutionReconciliationReport)
    assert report.total_positions == 0
    assert report.reconciliation_status == "reconciled"
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_reconciliation_with_filled_record() -> None:
    record = _lifecycle_record(gate_status="pass")
    report = build_paper_execution_reconciliation_report(
        lifecycle_records=(record,),
        generated_at=datetime(2026, 6, 25, tzinfo=UTC),
    )
    assert report.total_positions == 1
    assert report.filled_pending_count == 1
    assert report.reconciliation_status == "has_pending"
    assert report.total_fill_notional > ZERO


def test_reconciliation_with_blocked_record() -> None:
    record = _lifecycle_record(gate_status="blocked")
    report = build_paper_execution_reconciliation_report(
        lifecycle_records=(record,),
        generated_at=datetime(2026, 6, 25, tzinfo=UTC),
    )
    assert report.total_positions == 1
    assert report.cancelled_count == 1
    assert report.reconciliation_status == "reconciled"


def test_reconciliation_with_mixed_records() -> None:
    filled = _lifecycle_record(gate_status="pass")
    blocked = _lifecycle_record(gate_status="blocked")
    report = build_paper_execution_reconciliation_report(
        lifecycle_records=(filled, blocked),
        generated_at=datetime(2026, 6, 25, tzinfo=UTC),
    )
    assert report.total_positions == 2
    assert report.filled_pending_count == 1
    assert report.cancelled_count == 1


def test_reconciliation_rejects_naive_generated_at() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        build_paper_execution_reconciliation_report(
            lifecycle_records=(),
            generated_at=datetime(2026, 6, 25),
        )


def test_reconciliation_config_defaults() -> None:
    config = PaperExecutionReconciliationConfig()
    assert config.paper_only is True
    assert config.report_only is True
    assert config.readonly is True


def test_reconciliation_config_rejects_subclass() -> None:
    with pytest.raises(TypeError, match="does not support subclassing"):
        class BadConfig(PaperExecutionReconciliationConfig):
            pass


ZERO = Decimal("0.000000")
