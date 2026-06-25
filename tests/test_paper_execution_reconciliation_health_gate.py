from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from importlib import import_module
from types import SimpleNamespace

import pytest

from polymarket_alpha_lab.paper_execution_reconciliation import (
    PaperExecutionReconciliationPositionRow,
    PaperExecutionReconciliationReport,
)
from polymarket_alpha_lab.paper_execution_reconciliation_db_history import (
    PaperExecutionReconciliationDbHistoryConfig,
    PaperExecutionReconciliationDbHistoryReport,
    build_paper_execution_reconciliation_db_history_report,
)


GENERATED_AT = datetime(2026, 6, 25, 12, 0, tzinfo=UTC)
LATEST_AT = datetime(2026, 6, 25, 11, 55, tzinfo=UTC)


def d(value: str) -> Decimal:
    return Decimal(value)


def _api():
    return import_module(
        "polymarket_alpha_lab.paper_execution_reconciliation_health_gate",
    )


def _config(**overrides):
    values = {
        "config_version": "paper-execution-reconciliation-health-gate-v0",
        "min_source_reconciliation_report_count": 3,
        "max_latest_source_age_seconds": 86_400,
        "max_unrealized_loss": None,
    }
    values.update(overrides)
    return _api().PaperExecutionReconciliationHealthGateConfig(**values)


def _position(
    *,
    status: str = "settled_win",
    fill_notional: Decimal = d("10.000000"),
    cost_basis: Decimal = d("8.000000"),
    outcome_value: Decimal | None = d("12.000000"),
    pnl: Decimal | None = d("4.000000"),
) -> PaperExecutionReconciliationPositionRow:
    return PaperExecutionReconciliationPositionRow(
        condition_id="condition-1",
        market_slug="paper-market",
        question="Paper market",
        scoring_side="YES",
        position_status=status,
        fill_notional=fill_notional,
        cost_basis=cost_basis,
        outcome_value=outcome_value,
        pnl=pnl,
    )


def _report(
    *,
    generated_at: datetime = LATEST_AT,
    reconciliation_status: str = "reconciled",
    filled_pending_count: int = 0,
    total_positions: int = 1,
    unrealized_pnl: Decimal = d("0.000000"),
    total_pnl: Decimal | None = d("4.000000"),
    reason_codes: tuple[str, ...] = ("paper_execution_reconciliation_clean",),
) -> PaperExecutionReconciliationReport:
    position_rows = (
        ()
        if total_positions == 0
        else (
            _position(
                status="filled_pending" if filled_pending_count else "settled_win",
                outcome_value=None if filled_pending_count else d("12.000000"),
                pnl=None if filled_pending_count else d("4.000000"),
            ),
        )
    )
    return PaperExecutionReconciliationReport(
        generated_at=generated_at,
        config_version="paper-execution-reconciliation-v0",
        reconciliation_status=reconciliation_status,
        total_positions=total_positions,
        filled_pending_count=filled_pending_count,
        settled_win_count=0 if filled_pending_count else total_positions,
        settled_loss_count=0,
        expired_count=0,
        cancelled_count=0,
        total_fill_notional=d("10.000000") if total_positions else d("0.000000"),
        total_cost_basis=d("8.000000") if total_positions else d("0.000000"),
        total_outcome_value=(
            None
            if filled_pending_count or total_positions == 0
            else d("12.000000")
        ),
        total_pnl=total_pnl,
        realized_pnl=d("4.000000") if total_positions and not filled_pending_count else d("0.000000"),
        unrealized_pnl=unrealized_pnl,
        position_rows=position_rows,
        reason_codes=tuple(sorted(reason_codes)),
        paper_only=True,
        report_only=True,
        readonly=True,
    )


def _clean_history() -> tuple[PaperExecutionReconciliationReport, ...]:
    return (
        _report(generated_at=LATEST_AT - timedelta(minutes=2)),
        _report(generated_at=LATEST_AT - timedelta(minutes=1)),
        _report(generated_at=LATEST_AT),
    )


def test_health_gate_passes_fresh_clean_reconciliation_evidence() -> None:
    report = _api().build_paper_execution_reconciliation_health_gate_report(
        _clean_history(),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    assert report.gate_status == "pass"
    assert report.recommended_next_step == "allow_paper_execution_reconciliation"
    assert report.reason_codes == ("paper_execution_reconciliation_health_gate_passed",)
    assert report.reason_code_counts == (
        _api().PaperExecutionReconciliationHealthGateReasonCodeCount(
            reason_code="paper_execution_reconciliation_health_gate_passed",
            report_count=1,
        ),
    )
    assert report.source_reconciliation_report_count == 3
    assert report.latest_reconciliation_status == "reconciled"
    assert report.latest_reconciliation_generated_at == LATEST_AT
    assert report.latest_source_age_seconds == 300
    assert report.latest_filled_pending_count == 0
    assert report.latest_unrealized_pnl == d("0.000000")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_health_gate_accepts_supplied_history_like_evidence_report_tuple() -> None:
    source_reports = _clean_history()
    history_report = SimpleNamespace(
        reconciliation_reports=source_reports,
        paper_only=True,
        report_only=True,
        readonly=True,
    )

    report = _api().build_paper_execution_reconciliation_health_gate_report(
        history_report,
        config=_config(),
        generated_at=GENERATED_AT,
    )

    assert report.gate_status == "pass"
    assert report.source_reconciliation_report_count == len(source_reports)
    assert report.latest_reconciliation_generated_at == LATEST_AT


def test_health_gate_accepts_db_history_report_when_available() -> None:
    history = build_paper_execution_reconciliation_db_history_report(
        _clean_history(),
        config=PaperExecutionReconciliationDbHistoryConfig(),
        generated_at=GENERATED_AT,
    )
    assert type(history) is PaperExecutionReconciliationDbHistoryReport

    report = _api().build_paper_execution_reconciliation_health_gate_report(
        history,
        config=_config(),
        generated_at=GENERATED_AT,
    )

    assert report.gate_status == "pass"
    assert report.source_config_version == history.config_version
    assert report.source_reconciliation_report_count == history.report_count
    assert report.latest_reconciliation_status == "reconciled"
    assert report.latest_reconciliation_generated_at == LATEST_AT
    assert report.latest_source_age_seconds == 300
    assert report.latest_filled_pending_count is None
    assert report.latest_unrealized_pnl == d("0.000000")


@pytest.mark.parametrize(
    ("source_reports", "expected_reason"),
    (
        (
            (_report(generated_at=LATEST_AT),),
            "insufficient_paper_execution_reconciliation_source_history",
        ),
        (
            (
                _report(generated_at=LATEST_AT - timedelta(minutes=2)),
                _report(generated_at=LATEST_AT - timedelta(minutes=1)),
                _report(generated_at=LATEST_AT, reconciliation_status="has_discrepancies"),
            ),
            "paper_execution_reconciliation_discrepancies_present",
        ),
        (
            (
                _report(generated_at=GENERATED_AT - timedelta(days=3, minutes=2)),
                _report(generated_at=GENERATED_AT - timedelta(days=3, minutes=1)),
                _report(generated_at=GENERATED_AT - timedelta(days=3)),
            ),
            "stale_paper_execution_reconciliation_evidence",
        ),
    ),
)
def test_health_gate_blocks_on_unhealthy_or_insufficient_evidence(
    source_reports: tuple[PaperExecutionReconciliationReport, ...],
    expected_reason: str,
) -> None:
    report = _api().build_paper_execution_reconciliation_health_gate_report(
        source_reports,
        config=_config(),
        generated_at=GENERATED_AT,
    )

    assert report.gate_status == "blocked"
    assert report.recommended_next_step == "block_paper_execution_reconciliation"
    assert expected_reason in report.reason_codes


def test_health_gate_watches_on_pending_exposure_without_blocking_clean_sources() -> None:
    report = _api().build_paper_execution_reconciliation_health_gate_report(
        (
            _report(generated_at=LATEST_AT - timedelta(minutes=2)),
            _report(generated_at=LATEST_AT - timedelta(minutes=1)),
            _report(
                generated_at=LATEST_AT,
                reconciliation_status="has_pending",
                filled_pending_count=1,
                unrealized_pnl=d("2.000000"),
                total_pnl=None,
                reason_codes=("paper_execution_reconciliation_has_pending",),
            ),
        ),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    assert report.gate_status == "watch"
    assert report.recommended_next_step == "watch_paper_execution_reconciliation"
    assert report.reason_codes == (
        "pending_paper_execution_reconciliation_exposure",
    )
    assert report.latest_filled_pending_count == 1
    assert report.latest_unrealized_pnl == d("2.000000")


def test_health_gate_blocks_when_configured_unrealized_loss_threshold_is_exceeded() -> None:
    report = _api().build_paper_execution_reconciliation_health_gate_report(
        (
            _report(generated_at=LATEST_AT - timedelta(minutes=2)),
            _report(generated_at=LATEST_AT - timedelta(minutes=1)),
            _report(
                generated_at=LATEST_AT,
                reconciliation_status="has_pending",
                filled_pending_count=1,
                unrealized_pnl=d("-5.000001"),
                total_pnl=None,
                reason_codes=("paper_execution_reconciliation_has_pending",),
            ),
        ),
        config=_config(max_unrealized_loss=d("5.000000")),
        generated_at=GENERATED_AT,
    )

    assert report.gate_status == "blocked"
    assert report.reason_codes == (
        "paper_execution_reconciliation_unrealized_loss_threshold_exceeded",
        "pending_paper_execution_reconciliation_exposure",
    )
    assert report.reason_code_counts == (
        _api().PaperExecutionReconciliationHealthGateReasonCodeCount(
            reason_code="paper_execution_reconciliation_unrealized_loss_threshold_exceeded",
            report_count=1,
        ),
        _api().PaperExecutionReconciliationHealthGateReasonCodeCount(
            reason_code="pending_paper_execution_reconciliation_exposure",
            report_count=1,
        ),
    )


def test_health_gate_reason_codes_and_counts_are_deterministic() -> None:
    report = _api().build_paper_execution_reconciliation_health_gate_report(
        (_report(generated_at=LATEST_AT, reconciliation_status="has_discrepancies"),),
        config=_config(max_latest_source_age_seconds=1),
        generated_at=GENERATED_AT,
    )

    assert report.gate_status == "blocked"
    assert report.reason_codes == tuple(sorted(report.reason_codes))
    assert report.reason_codes == tuple(
        row.reason_code for row in report.reason_code_counts
    )
    assert tuple(row.report_count for row in report.reason_code_counts) == (1, 1, 1)


def test_health_gate_dataclasses_are_frozen_and_validate_exact_types_and_flags() -> None:
    api = _api()
    config = _config()
    report = api.build_paper_execution_reconciliation_health_gate_report(
        _clean_history(),
        config=config,
        generated_at=GENERATED_AT,
    )

    with pytest.raises(FrozenInstanceError):
        config.config_version = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.gate_status = "blocked"  # type: ignore[misc]
    with pytest.raises(ValueError, match="config must be exactly"):
        api.build_paper_execution_reconciliation_health_gate_report(
            _clean_history(),
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="config must be paper_only"):
        replace(config, paper_only=False)
    with pytest.raises(ValueError, match="gate report must be readonly"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="max_unrealized_loss must be a Decimal"):
        _config(max_unrealized_loss=5)


def test_health_gate_rejects_non_report_sources_and_false_source_flags() -> None:
    api = _api()

    with pytest.raises(ValueError, match="source reports must be a tuple"):
        api.build_paper_execution_reconciliation_health_gate_report(
            [_report()],
            config=_config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="source reports entries must be"):
        api.build_paper_execution_reconciliation_health_gate_report(
            (object(),),
            config=_config(),
            generated_at=GENERATED_AT,
        )

    unsafe_report = _report()
    object.__setattr__(unsafe_report, "readonly", False)
    with pytest.raises(ValueError, match="source reports.0 must be readonly"):
        api.build_paper_execution_reconciliation_health_gate_report(
            (unsafe_report,),
            config=_config(),
            generated_at=GENERATED_AT,
        )


def test_health_gate_rejects_naive_generated_at_and_future_source_evidence() -> None:
    api = _api()

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        api.build_paper_execution_reconciliation_health_gate_report(
            _clean_history(),
            config=_config(),
            generated_at=datetime(2026, 6, 25, 12, 0),
        )

    with pytest.raises(ValueError, match="source reports must not be newer"):
        api.build_paper_execution_reconciliation_health_gate_report(
            (_report(generated_at=GENERATED_AT + timedelta(seconds=1)),),
            config=_config(min_source_reconciliation_report_count=1),
            generated_at=GENERATED_AT,
        )
