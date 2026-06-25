from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from polymarket_alpha_lab.paper_execution_reconciliation import (
    PaperExecutionReconciliationReport,
)
from polymarket_alpha_lab.paper_execution_reconciliation_db_history import (
    DEFAULT_PAPER_EXECUTION_RECONCILIATION_DB_HISTORY_CONFIG_VERSION,
    PaperExecutionReconciliationDbHistoryConfig,
    PaperExecutionReconciliationDbHistoryReport,
    build_paper_execution_reconciliation_db_history_report,
)


NOW = datetime(2026, 6, 25, 12, 0, tzinfo=UTC)
T1 = datetime(2026, 6, 25, 9, 0, tzinfo=UTC)
T2 = datetime(2026, 6, 25, 10, 0, tzinfo=UTC)
T3 = datetime(2026, 6, 25, 11, 0, tzinfo=UTC)


def d(value: str) -> Decimal:
    return Decimal(value)


def _report(
    *,
    generated_at: datetime,
    reconciliation_status: str = "reconciled",
    total_positions: int = 1,
    filled_pending_count: int = 0,
    total_pnl: Decimal | None = None,
    realized_pnl: Decimal = d("0.000000"),
    unrealized_pnl: Decimal = d("0.000000"),
    reason_codes: tuple[str, ...] = (
        "paper_execution_reconciliation_has_settled",
    ),
) -> PaperExecutionReconciliationReport:
    return PaperExecutionReconciliationReport(
        generated_at=generated_at,
        config_version="paper-execution-reconciliation-v0",
        reconciliation_status=reconciliation_status,
        total_positions=total_positions,
        filled_pending_count=filled_pending_count,
        settled_win_count=0,
        settled_loss_count=0,
        expired_count=0,
        cancelled_count=0,
        total_fill_notional=d("1.000000") if total_positions else d("0.000000"),
        total_cost_basis=d("1.000000") if total_positions else d("0.000000"),
        total_outcome_value=None,
        total_pnl=total_pnl,
        realized_pnl=realized_pnl,
        unrealized_pnl=unrealized_pnl,
        position_rows=(),
        reason_codes=tuple(sorted(reason_codes)),
        paper_only=True,
        report_only=True,
        readonly=True,
    )


def test_config_defaults_are_paper_only_readonly_defaults() -> None:
    config = PaperExecutionReconciliationDbHistoryConfig()

    assert (
        config.config_version
        == DEFAULT_PAPER_EXECUTION_RECONCILIATION_DB_HISTORY_CONFIG_VERSION
    )
    assert config.min_report_count == 1
    assert config.max_pending_streak == 0
    assert config.max_discrepancy_streak == 0
    assert config.max_duplicate_generated_at_count == 0
    assert config.paper_only is True
    assert config.report_only is True
    assert config.readonly is True

    with pytest.raises(FrozenInstanceError):
        config.min_report_count = 2  # type: ignore[misc]


def test_history_summarizes_reconciliation_reports_chronologically() -> None:
    reports = (
        _report(
            generated_at=T3,
            reconciliation_status="has_discrepancies",
            total_positions=0,
            total_pnl=d("-3.500000"),
            realized_pnl=d("-2.500000"),
            unrealized_pnl=d("-1.000000"),
            reason_codes=("manual_review_required",),
        ),
        _report(
            generated_at=T1,
            reconciliation_status="reconciled",
            total_positions=2,
            total_pnl=d("1.500000"),
            realized_pnl=d("1.000000"),
            unrealized_pnl=d("0.500000"),
            reason_codes=("paper_execution_reconciliation_has_settled",),
        ),
        _report(
            generated_at=T2,
            reconciliation_status="has_pending",
            total_positions=1,
            filled_pending_count=1,
            total_pnl=d("0.250000"),
            realized_pnl=d("0.000000"),
            unrealized_pnl=d("0.250000"),
            reason_codes=("paper_execution_reconciliation_has_pending",),
        ),
        _report(
            generated_at=T2,
            reconciliation_status="has_pending",
            total_positions=1,
            filled_pending_count=1,
            total_pnl=None,
            realized_pnl=d("-0.500000"),
            unrealized_pnl=d("0.000000"),
            reason_codes=("paper_execution_reconciliation_has_pending",),
        ),
    )

    history = build_paper_execution_reconciliation_db_history_report(
        reports,
        config=PaperExecutionReconciliationDbHistoryConfig(
            max_discrepancy_streak=1,
            max_duplicate_generated_at_count=0,
        ),
        generated_at=NOW,
    )

    assert type(history) is PaperExecutionReconciliationDbHistoryReport
    assert history.paper_only is True
    assert history.report_only is True
    assert history.readonly is True
    assert history.history_status == "watch"
    assert history.report_count == 4
    assert history.first_report_generated_at == T1
    assert history.latest_report_generated_at == T3
    assert history.latest_reconciliation_status == "has_discrepancies"
    assert history.pending_streak_count == 0
    assert history.discrepancy_streak_count == 1
    assert history.latest_total_pnl == d("-3.500000")
    assert history.total_pnl_sum == d("-1.750000")
    assert history.latest_realized_pnl == d("-2.500000")
    assert history.realized_pnl_sum == d("-2.000000")
    assert history.latest_unrealized_pnl == d("-1.000000")
    assert history.unrealized_pnl_sum == d("-0.250000")
    assert history.no_position_report_count == 1
    assert history.duplicate_generated_at_count == 1
    assert [
        (row.reconciliation_status, row.report_count)
        for row in history.reconciliation_status_rows
    ] == [
        ("reconciled", 1),
        ("has_pending", 2),
        ("has_discrepancies", 1),
    ]
    assert [
        (row.reason_code, row.report_count) for row in history.reason_code_rows
    ] == [
        ("paper_execution_reconciliation_has_pending", 2),
        ("manual_review_required", 1),
        ("paper_execution_reconciliation_has_settled", 1),
    ]
    assert history.latest_reason_codes == ("manual_review_required",)
    assert history.reason_codes == ("duplicate_generated_at_threshold_exceeded",)


def test_history_blocks_insufficient_reports_and_records_omitted_fields_concern() -> None:
    history = build_paper_execution_reconciliation_db_history_report(
        (),
        config=PaperExecutionReconciliationDbHistoryConfig(min_report_count=2),
        generated_at=NOW,
    )

    assert history.history_status == "blocked"
    assert history.report_count == 0
    assert history.latest_reconciliation_status is None
    assert history.total_pnl_sum is None
    assert history.no_position_report_count == 0
    assert history.reason_codes == (
        "insufficient_paper_execution_reconciliation_history",
    )
    assert history.concerns == (
        "current PaperExecutionReconciliationReport has no explicit no_position_count field; "
        "history uses total_positions == 0",
    )


def test_history_rejects_float_financial_values() -> None:
    report = _report(generated_at=T1)
    object.__setattr__(report, "realized_pnl", 1.25)

    with pytest.raises(ValueError, match="realized_pnl"):
        build_paper_execution_reconciliation_db_history_report(
            (report,),
            config=PaperExecutionReconciliationDbHistoryConfig(),
            generated_at=NOW,
        )


def test_history_rejects_unsafe_nested_report_flags() -> None:
    report = _report(generated_at=T1)
    object.__setattr__(report, "readonly", False)

    with pytest.raises(ValueError, match="readonly"):
        build_paper_execution_reconciliation_db_history_report(
            (report,),
            config=PaperExecutionReconciliationDbHistoryConfig(),
            generated_at=NOW,
        )
