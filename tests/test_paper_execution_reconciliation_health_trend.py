from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from importlib import import_module

import pytest

from polymarket_alpha_lab.paper_execution_reconciliation_health_gate import (
    PaperExecutionReconciliationHealthGateReasonCodeCount,
    PaperExecutionReconciliationHealthGateReport,
)


GENERATED_AT = datetime(2026, 6, 25, 12, 0, tzinfo=UTC)
BASE_AT = datetime(2026, 6, 25, 8, 0, tzinfo=UTC)
HEALTH_GATE_NEXT_STEP_BY_STATUS = {
    "pass": "allow_paper_execution_reconciliation",
    "watch": "watch_paper_execution_reconciliation",
    "blocked": "block_paper_execution_reconciliation",
}
PASS_REASON = "paper_execution_reconciliation_health_gate_passed"
PENDING_REASON = "pending_paper_execution_reconciliation_exposure"
STALE_REASON = "stale_paper_execution_reconciliation_evidence"
MISSING_REASON = "missing_paper_execution_reconciliation_evidence"
DISCREPANCY_REASON = "paper_execution_reconciliation_discrepancies_present"


class DatetimeSubclass(datetime):
    pass


def _api():
    return import_module(
        "polymarket_alpha_lab.paper_execution_reconciliation_health_trend",
    )


def _config(**overrides):
    values = {
        "config_version": "paper-execution-reconciliation-health-trend-v0",
    }
    values.update(overrides)
    return _api().PaperExecutionReconciliationHealthTrendConfig(**values)


def _source_reason_count(
    reason_code: str,
    report_count: int = 1,
) -> PaperExecutionReconciliationHealthGateReasonCodeCount:
    return PaperExecutionReconciliationHealthGateReasonCodeCount(
        reason_code=reason_code,
        report_count=report_count,
    )


def _gate_report(
    *,
    generated_at: datetime,
    gate_status: str = "pass",
    reason_codes: tuple[str, ...] = (PASS_REASON,),
    latest_source_age_seconds: int | None = 60,
) -> PaperExecutionReconciliationHealthGateReport:
    sorted_reason_codes = tuple(sorted(reason_codes))
    latest_reconciliation_generated_at = (
        None
        if latest_source_age_seconds is None
        else generated_at - timedelta(seconds=latest_source_age_seconds)
    )
    return PaperExecutionReconciliationHealthGateReport(
        generated_at=generated_at,
        config_version="paper-execution-reconciliation-health-gate-v0",
        source_config_version="paper-execution-reconciliation-v0",
        gate_status=gate_status,
        recommended_next_step=HEALTH_GATE_NEXT_STEP_BY_STATUS[gate_status],
        reason_code_counts=tuple(
            _source_reason_count(reason_code) for reason_code in sorted_reason_codes
        ),
        source_reconciliation_report_count=3,
        latest_reconciliation_status="reconciled",
        latest_reconciliation_generated_at=latest_reconciliation_generated_at,
        latest_source_age_seconds=latest_source_age_seconds,
        latest_filled_pending_count=0,
        latest_unrealized_pnl=Decimal("0.000000"),
        reason_codes=sorted_reason_codes,
    )


def test_health_trend_empty_input_conservatively_blocks_with_explicit_reason() -> None:
    trend = _api().build_paper_execution_reconciliation_health_trend_report(
        (),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    assert trend.generated_at == GENERATED_AT
    assert trend.config_version == "paper-execution-reconciliation-health-trend-v0"
    assert trend.source_health_gate_report_count == 0
    assert trend.first_generated_at is None
    assert trend.latest_generated_at is None
    assert trend.latest_gate_status is None
    assert trend.trend_status == "blocked"
    assert trend.recommended_next_step == "block_paper_execution_reconciliation_health_trend"
    assert trend.gate_status_counts == (("pass", 0), ("watch", 0), ("blocked", 0))
    assert trend.pass_gate_report_count == 0
    assert trend.watch_gate_report_count == 0
    assert trend.blocked_gate_report_count == 0
    assert trend.consecutive_latest_watch_count == 0
    assert trend.consecutive_latest_blocked_count == 0
    assert trend.latest_source_age_seconds is None
    assert trend.stale_reason_report_count == 0
    assert trend.missing_reason_report_count == 0
    assert trend.discrepancy_reason_report_count == 0
    assert trend.reason_code_counts == ()
    assert trend.reason_codes == (
        "missing_paper_execution_reconciliation_health_gate_reports",
    )
    assert trend.paper_only is True
    assert trend.report_only is True
    assert trend.readonly is True


def test_health_trend_summarizes_latest_status_counts_streaks_age_and_reasons() -> None:
    first_pass = _gate_report(
        generated_at=BASE_AT,
        gate_status="pass",
        reason_codes=(PASS_REASON,),
        latest_source_age_seconds=300,
    )
    watch = _gate_report(
        generated_at=BASE_AT + timedelta(hours=1),
        gate_status="watch",
        reason_codes=(PENDING_REASON,),
        latest_source_age_seconds=240,
    )
    blocked = _gate_report(
        generated_at=BASE_AT + timedelta(hours=2),
        gate_status="blocked",
        reason_codes=(DISCREPANCY_REASON, STALE_REASON),
        latest_source_age_seconds=120,
    )
    latest_blocked = _gate_report(
        generated_at=BASE_AT + timedelta(hours=3),
        gate_status="blocked",
        reason_codes=(MISSING_REASON, STALE_REASON),
        latest_source_age_seconds=45,
    )

    trend = _api().build_paper_execution_reconciliation_health_trend_report(
        (blocked, latest_blocked, first_pass, watch),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    assert trend.source_health_gate_report_count == 4
    assert trend.first_generated_at == BASE_AT
    assert trend.latest_generated_at == BASE_AT + timedelta(hours=3)
    assert trend.latest_gate_status == "blocked"
    assert trend.trend_status == "blocked"
    assert trend.gate_status_counts == (("pass", 1), ("watch", 1), ("blocked", 2))
    assert trend.pass_gate_report_count == 1
    assert trend.watch_gate_report_count == 1
    assert trend.blocked_gate_report_count == 2
    assert trend.consecutive_latest_watch_count == 0
    assert trend.consecutive_latest_blocked_count == 2
    assert trend.latest_source_age_seconds == 45
    assert trend.stale_reason_report_count == 2
    assert trend.missing_reason_report_count == 1
    assert trend.discrepancy_reason_report_count == 1
    assert trend.reason_code_counts == (
        _api().PaperExecutionReconciliationHealthTrendReasonCodeCount(
            reason_code=STALE_REASON,
            report_count=2,
            latest_count=1,
        ),
        _api().PaperExecutionReconciliationHealthTrendReasonCodeCount(
            reason_code=MISSING_REASON,
            report_count=1,
            latest_count=1,
        ),
        _api().PaperExecutionReconciliationHealthTrendReasonCodeCount(
            reason_code=DISCREPANCY_REASON,
            report_count=1,
            latest_count=0,
        ),
        _api().PaperExecutionReconciliationHealthTrendReasonCodeCount(
            reason_code=PASS_REASON,
            report_count=1,
            latest_count=0,
        ),
        _api().PaperExecutionReconciliationHealthTrendReasonCodeCount(
            reason_code=PENDING_REASON,
            report_count=1,
            latest_count=0,
        ),
    )
    assert trend.reason_codes == (
        "latest_paper_execution_reconciliation_health_gate_blocked",
    )


def test_health_trend_computes_latest_watch_streak() -> None:
    trend = _api().build_paper_execution_reconciliation_health_trend_report(
        (
            _gate_report(generated_at=BASE_AT, gate_status="pass"),
            _gate_report(
                generated_at=BASE_AT + timedelta(hours=1),
                gate_status="watch",
                reason_codes=(PENDING_REASON,),
            ),
            _gate_report(
                generated_at=BASE_AT + timedelta(hours=2),
                gate_status="watch",
                reason_codes=(PENDING_REASON,),
            ),
        ),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    assert trend.latest_gate_status == "watch"
    assert trend.trend_status == "watch"
    assert trend.consecutive_latest_watch_count == 2
    assert trend.consecutive_latest_blocked_count == 0
    assert trend.reason_codes == (
        "latest_paper_execution_reconciliation_health_gate_watch",
    )


def test_health_trend_allows_latest_missing_evidence_without_latest_age() -> None:
    trend = _api().build_paper_execution_reconciliation_health_trend_report(
        (
            PaperExecutionReconciliationHealthGateReport(
                generated_at=BASE_AT,
                config_version="paper-execution-reconciliation-health-gate-v0",
                source_config_version=None,
                gate_status="blocked",
                recommended_next_step="block_paper_execution_reconciliation",
                reason_code_counts=(
                    _source_reason_count(MISSING_REASON),
                ),
                source_reconciliation_report_count=0,
                latest_reconciliation_status=None,
                latest_reconciliation_generated_at=None,
                latest_source_age_seconds=None,
                latest_filled_pending_count=None,
                latest_unrealized_pnl=None,
                reason_codes=(MISSING_REASON,),
            ),
        ),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    assert trend.latest_gate_status == "blocked"
    assert trend.latest_source_age_seconds is None
    assert trend.missing_reason_report_count == 1
    assert trend.reason_codes == (
        "latest_paper_execution_reconciliation_health_gate_blocked",
    )


def test_health_trend_dataclasses_are_frozen_and_validate_types_and_flags() -> None:
    api = _api()
    config = _config()
    reason_count = api.PaperExecutionReconciliationHealthTrendReasonCodeCount(
        reason_code=PASS_REASON,
        report_count=1,
        latest_count=1,
    )
    trend = api.build_paper_execution_reconciliation_health_trend_report(
        (_gate_report(generated_at=BASE_AT),),
        config=config,
        generated_at=GENERATED_AT,
    )

    with pytest.raises(FrozenInstanceError):
        config.config_version = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        reason_count.report_count = 2  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        trend.trend_status = "blocked"  # type: ignore[misc]

    with pytest.raises(ValueError, match="config must be exactly"):
        api.build_paper_execution_reconciliation_health_trend_report(
            (_gate_report(generated_at=BASE_AT),),
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="health_gate_reports must be a tuple"):
        api.build_paper_execution_reconciliation_health_trend_report(
            [_gate_report(generated_at=BASE_AT)],
            config=config,
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        api.build_paper_execution_reconciliation_health_trend_report(
            (_gate_report(generated_at=BASE_AT),),
            config=config,
            generated_at=DatetimeSubclass(2026, 6, 25, 12, 0, tzinfo=UTC),
        )

    unsafe_source = _gate_report(generated_at=BASE_AT)
    object.__setattr__(unsafe_source, "readonly", False)
    with pytest.raises(ValueError, match="source health_gate_reports.0 must be readonly"):
        api.build_paper_execution_reconciliation_health_trend_report(
            (unsafe_source,),
            config=config,
            generated_at=GENERATED_AT,
        )

    with pytest.raises(ValueError, match="config must be paper_only"):
        replace(config, paper_only=False)
    with pytest.raises(ValueError, match="reason code count must be readonly"):
        replace(reason_count, readonly=False)
    with pytest.raises(ValueError, match="gate_status_counts"):
        replace(trend, gate_status_counts=(("watch", 0), ("pass", 1), ("blocked", 0)))


def test_health_trend_public_dataclass_subclasses_cannot_be_constructed() -> None:
    api = _api()

    with pytest.raises(TypeError, match="TrendConfig .*subclassing"):
        class ConfigSubclass(api.PaperExecutionReconciliationHealthTrendConfig):
            pass

    with pytest.raises(TypeError, match="TrendReasonCodeCount .*subclassing"):
        class ReasonCodeCountSubclass(
            api.PaperExecutionReconciliationHealthTrendReasonCodeCount,
        ):
            pass

    with pytest.raises(TypeError, match="TrendReport .*subclassing"):
        class ReportSubclass(api.PaperExecutionReconciliationHealthTrendReport):
            pass
