from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from importlib import import_module

import pytest

from polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history import (
    PaperAutonomousAllocationProposalDbHistoryReasonCodeRow,
    PaperAutonomousAllocationProposalDbHistoryReport,
    PaperAutonomousAllocationProposalDbHistoryStatusRow,
)


GENERATED_AT = datetime(2026, 6, 24, 18, 0, tzinfo=UTC)
LATEST_AT = datetime(2026, 6, 24, 17, 30, tzinfo=UTC)
PROPOSAL_STATUSES = ("pass", "watch", "blocked")


def _api():
    return import_module(
        "polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_gate",
    )


def _config(**overrides):
    values = {
        "config_version": "paper-autonomous-allocation-proposal-db-history-gate-v0",
        "min_history_report_count": 3,
        "max_latest_age_seconds": 86_400,
        "max_consecutive_latest_watch_count": 0,
        "max_consecutive_latest_blocked_count": 0,
        "max_duplicate_generated_at_count": 0,
    }
    values.update(overrides)
    return _api().PaperAutonomousAllocationProposalDbHistoryGateConfig(**values)


def _source_reason(history_status: str, latest_proposal_status: str) -> str:
    if history_status == "blocked":
        return "blocked_allocation_proposal_report_threshold_exceeded"
    if history_status == "watch":
        return "watch_allocation_proposal_report_threshold_exceeded"
    if latest_proposal_status == "blocked":
        return "blocked_allocation_proposal_report_threshold_exceeded"
    if latest_proposal_status == "watch":
        return "watch_allocation_proposal_report_threshold_exceeded"
    return "paper_autonomous_allocation_proposal_db_history_passed"


def _history_report(
    *,
    generated_at: datetime = GENERATED_AT,
    history_status: str = "pass",
    report_count: int = 3,
    latest_report_generated_at: datetime | None = LATEST_AT,
    latest_proposal_status: str | None = "pass",
    duplicate_generated_at_count: int = 0,
    consecutive_latest_pass_count: int = 3,
    consecutive_latest_watch_count: int = 0,
    consecutive_latest_blocked_count: int = 0,
    reason_codes: tuple[str, ...] | None = None,
) -> PaperAutonomousAllocationProposalDbHistoryReport:
    if report_count == 0:
        return PaperAutonomousAllocationProposalDbHistoryReport(
            generated_at=generated_at,
            config_version="paper-autonomous-allocation-proposal-db-history-v0",
            history_status=history_status,
            report_count=0,
            first_report_generated_at=None,
            latest_report_generated_at=None,
            latest_proposal_status=None,
            latest_screening_gate_status=None,
            latest_queue_risk_status=None,
            latest_allocation_input_count=None,
            latest_allocation_row_count=None,
            latest_allocated_count=None,
            latest_total_allocated_paper_notional=None,
            proposal_status_rows=tuple(
                PaperAutonomousAllocationProposalDbHistoryStatusRow(status, 0)
                for status in PROPOSAL_STATUSES
            ),
            duplicate_generated_at_count=0,
            consecutive_latest_pass_count=0,
            consecutive_latest_watch_count=0,
            consecutive_latest_blocked_count=0,
            latest_reason_codes=(),
            reason_code_rows=(),
            reason_codes=(
                reason_codes
                if reason_codes is not None
                else ("insufficient_paper_autonomous_allocation_proposal_history",)
            ),
        )

    if latest_proposal_status is None:
        raise AssertionError("test helper requires latest_proposal_status")
    status_counts = {
        "pass": report_count,
        "watch": 0,
        "blocked": 0,
    }
    if latest_proposal_status == "watch":
        status_counts = {
            "pass": report_count - consecutive_latest_watch_count,
            "watch": consecutive_latest_watch_count,
            "blocked": 0,
        }
    elif latest_proposal_status == "blocked":
        status_counts = {
            "pass": report_count - consecutive_latest_blocked_count,
            "watch": 0,
            "blocked": consecutive_latest_blocked_count,
        }

    source_reason = _source_reason(history_status, latest_proposal_status)
    normalized_reason_codes = (
        reason_codes if reason_codes is not None else (source_reason,)
    )
    latest_reason_codes = (
        ("paper_autonomous_allocation_proposal_passed",)
        if latest_proposal_status == "pass"
        else (f"allocation_proposal_{latest_proposal_status}",)
    )

    return PaperAutonomousAllocationProposalDbHistoryReport(
        generated_at=generated_at,
        config_version="paper-autonomous-allocation-proposal-db-history-v0",
        history_status=history_status,
        report_count=report_count,
        first_report_generated_at=latest_report_generated_at - timedelta(hours=2),
        latest_report_generated_at=latest_report_generated_at,
        latest_proposal_status=latest_proposal_status,
        latest_screening_gate_status="pass",
        latest_queue_risk_status="pass",
        latest_allocation_input_count=2,
        latest_allocation_row_count=2,
        latest_allocated_count=1,
        latest_total_allocated_paper_notional=Decimal("25.000000"),
        proposal_status_rows=tuple(
            PaperAutonomousAllocationProposalDbHistoryStatusRow(
                status,
                status_counts[status],
            )
            for status in PROPOSAL_STATUSES
        ),
        duplicate_generated_at_count=duplicate_generated_at_count,
        consecutive_latest_pass_count=consecutive_latest_pass_count,
        consecutive_latest_watch_count=consecutive_latest_watch_count,
        consecutive_latest_blocked_count=consecutive_latest_blocked_count,
        latest_reason_codes=latest_reason_codes,
        reason_code_rows=tuple(
            PaperAutonomousAllocationProposalDbHistoryReasonCodeRow(
                reason_code,
                report_count,
            )
            for reason_code in normalized_reason_codes
        ),
        reason_codes=normalized_reason_codes,
    )


def _gate_report(
    history_report: PaperAutonomousAllocationProposalDbHistoryReport,
    **config_overrides,
):
    return _api().build_paper_autonomous_allocation_proposal_db_history_gate_report(
        history_report,
        config=_config(**config_overrides),
        generated_at=GENERATED_AT,
    )


def _history_subclass(
    report: PaperAutonomousAllocationProposalDbHistoryReport,
) -> PaperAutonomousAllocationProposalDbHistoryReport:
    class HistoryReportSubclass(PaperAutonomousAllocationProposalDbHistoryReport):
        pass

    subclass_report = HistoryReportSubclass.__new__(HistoryReportSubclass)
    for field_name, value in report.__dict__.items():
        object.__setattr__(subclass_report, field_name, value)
    return subclass_report


def test_allocation_proposal_db_history_gate_passes_clean_recent_history():
    api = _api()
    source = _history_report()

    report = api.build_paper_autonomous_allocation_proposal_db_history_gate_report(
        source,
        config=_config(),
        generated_at=GENERATED_AT,
    )

    assert type(report) is api.PaperAutonomousAllocationProposalDbHistoryGateReport
    assert report.generated_at == GENERATED_AT
    assert report.config_version == (
        "paper-autonomous-allocation-proposal-db-history-gate-v0"
    )
    assert report.gate_status == "pass"
    assert report.recommended_next_step == (
        "allow_paper_autonomous_allocation_proposal_history_review"
    )
    assert report.source_report_count == 3
    assert report.source_history_status == "pass"
    assert report.latest_proposal_status == "pass"
    assert report.latest_screening_gate_status == "pass"
    assert report.latest_queue_risk_status == "pass"
    assert report.latest_allocation_input_count == 2
    assert report.latest_allocation_row_count == 2
    assert report.latest_allocated_count == 1
    assert report.latest_total_allocated_paper_notional == Decimal("25.000000")
    assert report.latest_source_generated_at == LATEST_AT
    assert report.latest_source_age_seconds == 1_800
    assert report.reason_code_counts == (
        api.PaperAutonomousAllocationProposalDbHistoryGateReasonCodeCount(
            "paper_autonomous_allocation_proposal_db_history_gate_passed",
            1,
        ),
    )
    assert report.reason_codes == (
        "paper_autonomous_allocation_proposal_db_history_gate_passed",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


@pytest.mark.parametrize(
    ("source", "expected_reason"),
    (
        (
            _history_report(history_status="blocked", reason_codes=("z_source_blocked",)),
            "source_allocation_proposal_db_history_blocked",
        ),
        (
            _history_report(report_count=2, consecutive_latest_pass_count=2),
            "insufficient_allocation_proposal_db_history",
        ),
        (
            _history_report(
                latest_proposal_status="blocked",
                consecutive_latest_pass_count=0,
                consecutive_latest_blocked_count=1,
                reason_codes=("z_latest_blocked",),
            ),
            "latest_allocation_proposal_blocked",
        ),
    ),
)
def test_allocation_proposal_db_history_gate_blocks_for_blocked_inputs(
    source: PaperAutonomousAllocationProposalDbHistoryReport,
    expected_reason: str,
):
    report = _gate_report(source)

    assert report.gate_status == "blocked"
    assert report.recommended_next_step == (
        "block_paper_autonomous_allocation_proposal_history_review"
    )
    assert expected_reason in report.reason_codes
    assert (
        "paper_autonomous_allocation_proposal_db_history_gate_passed"
        not in report.reason_codes
    )


@pytest.mark.parametrize(
    ("source", "expected_reason"),
    (
        (
            _history_report(history_status="watch", reason_codes=("z_source_watch",)),
            "source_allocation_proposal_db_history_watch",
        ),
        (
            _history_report(
                latest_proposal_status="watch",
                consecutive_latest_pass_count=0,
                consecutive_latest_watch_count=1,
                reason_codes=("z_latest_watch",),
            ),
            "latest_allocation_proposal_watch",
        ),
        (
            _history_report(duplicate_generated_at_count=1),
            "duplicate_allocation_proposal_generated_at_threshold_exceeded",
        ),
    ),
)
def test_allocation_proposal_db_history_gate_watches_for_watch_inputs(
    source: PaperAutonomousAllocationProposalDbHistoryReport,
    expected_reason: str,
):
    report = _gate_report(source)

    assert report.gate_status == "watch"
    assert report.recommended_next_step == (
        "throttle_paper_autonomous_allocation_proposal_history_review"
    )
    assert expected_reason in report.reason_codes
    assert (
        "paper_autonomous_allocation_proposal_db_history_gate_passed"
        not in report.reason_codes
    )


def test_allocation_proposal_db_history_gate_watches_stale_latest_timestamp():
    source = _history_report(
        latest_report_generated_at=GENERATED_AT - timedelta(seconds=86_401),
    )

    report = _gate_report(source)

    assert report.gate_status == "watch"
    assert report.latest_source_age_seconds == 86_401
    assert report.reason_codes == ("stale_allocation_proposal_db_history",)


def test_allocation_proposal_db_history_gate_enforces_consecutive_thresholds():
    watch_source = _history_report(
        latest_proposal_status="watch",
        consecutive_latest_pass_count=0,
        consecutive_latest_watch_count=2,
        reason_codes=("z_latest_watch",),
    )
    blocked_source = _history_report(
        latest_proposal_status="blocked",
        consecutive_latest_pass_count=0,
        consecutive_latest_blocked_count=2,
        reason_codes=("z_latest_blocked",),
    )

    watch_report = _gate_report(
        watch_source,
        max_consecutive_latest_watch_count=1,
    )
    blocked_report = _gate_report(
        blocked_source,
        max_consecutive_latest_blocked_count=1,
    )

    assert watch_report.gate_status == "watch"
    assert "latest_allocation_proposal_watch" in watch_report.reason_codes
    assert (
        "consecutive_allocation_proposal_watch_threshold_exceeded"
        in watch_report.reason_codes
    )
    assert blocked_report.gate_status == "blocked"
    assert "latest_allocation_proposal_blocked" in blocked_report.reason_codes
    assert (
        "consecutive_allocation_proposal_blocked_threshold_exceeded"
        in blocked_report.reason_codes
    )


def test_allocation_proposal_db_history_gate_missing_latest_timestamp_blocks():
    source = _history_report(report_count=0)

    report = _gate_report(source, min_history_report_count=0)

    assert report.gate_status == "blocked"
    assert report.latest_source_generated_at is None
    assert report.latest_source_age_seconds is None
    assert "missing_latest_allocation_proposal_history_timestamp" in report.reason_codes


def test_allocation_proposal_db_history_gate_reason_code_counts_are_deterministic_and_positive():
    source = _history_report(
        history_status="blocked",
        latest_proposal_status="blocked",
        duplicate_generated_at_count=1,
        consecutive_latest_pass_count=0,
        consecutive_latest_blocked_count=2,
        reason_codes=("z_latest_blocked",),
    )

    report = _gate_report(
        source,
        min_history_report_count=4,
        max_consecutive_latest_blocked_count=1,
    )

    assert report.gate_status == "blocked"
    assert report.reason_code_counts == (
        _api().PaperAutonomousAllocationProposalDbHistoryGateReasonCodeCount(
            "consecutive_allocation_proposal_blocked_threshold_exceeded",
            1,
        ),
        _api().PaperAutonomousAllocationProposalDbHistoryGateReasonCodeCount(
            "duplicate_allocation_proposal_generated_at_threshold_exceeded",
            1,
        ),
        _api().PaperAutonomousAllocationProposalDbHistoryGateReasonCodeCount(
            "insufficient_allocation_proposal_db_history",
            1,
        ),
        _api().PaperAutonomousAllocationProposalDbHistoryGateReasonCodeCount(
            "latest_allocation_proposal_blocked",
            1,
        ),
        _api().PaperAutonomousAllocationProposalDbHistoryGateReasonCodeCount(
            "source_allocation_proposal_db_history_blocked",
            1,
        ),
    )
    assert report.reason_codes == tuple(row.reason_code for row in report.reason_code_counts)
    assert all(row.report_count == 1 for row in report.reason_code_counts)
    assert (
        "paper_autonomous_allocation_proposal_db_history_gate_passed"
        not in report.reason_codes
    )


def test_allocation_proposal_db_history_gate_dataclasses_are_frozen_and_validate_hard_flags():
    api = _api()
    source = _history_report()
    config = _config()
    reason_count = api.PaperAutonomousAllocationProposalDbHistoryGateReasonCodeCount(
        "paper_autonomous_allocation_proposal_db_history_gate_passed",
        1,
    )
    report = _gate_report(source)

    with pytest.raises(FrozenInstanceError):
        config.config_version = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        reason_count.report_count = 2  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.gate_status = "watch"  # type: ignore[misc]

    with pytest.raises(ValueError, match="config .*paper_only"):
        replace(config, paper_only=False)
    with pytest.raises(ValueError, match="reason code count .*report_only"):
        replace(reason_count, report_only=False)
    with pytest.raises(ValueError, match="gate report .*readonly"):
        replace(report, readonly=False)


@pytest.mark.parametrize(
    ("overrides", "message"),
    (
        ({"config_version": ""}, "config_version"),
        ({"min_history_report_count": -1}, "min_history_report_count"),
        ({"max_latest_age_seconds": -1}, "max_latest_age_seconds"),
        (
            {"max_consecutive_latest_watch_count": -1},
            "max_consecutive_latest_watch_count",
        ),
        (
            {"max_consecutive_latest_blocked_count": -1},
            "max_consecutive_latest_blocked_count",
        ),
        ({"max_duplicate_generated_at_count": -1}, "max_duplicate_generated_at_count"),
    ),
)
def test_allocation_proposal_db_history_gate_config_rejects_invalid_thresholds(
    overrides: dict[str, object],
    message: str,
):
    with pytest.raises(ValueError, match=message):
        _config(**overrides)


def test_allocation_proposal_db_history_gate_rejects_wrong_types_subclasses_and_corruption():
    api = _api()
    source = _history_report()

    class ConfigSubclass(api.PaperAutonomousAllocationProposalDbHistoryGateConfig):
        pass

    class DatetimeSubclass(datetime):
        pass

    with pytest.raises(ValueError, match="history_report must be"):
        api.build_paper_autonomous_allocation_proposal_db_history_gate_report(
            object(),
            config=_config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="history_report must be"):
        api.build_paper_autonomous_allocation_proposal_db_history_gate_report(
            _history_subclass(source),
            config=_config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="config must be"):
        api.build_paper_autonomous_allocation_proposal_db_history_gate_report(
            source,
            config=ConfigSubclass(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        api.build_paper_autonomous_allocation_proposal_db_history_gate_report(
            source,
            config=_config(),
            generated_at=DatetimeSubclass(2026, 6, 24, 18, 0, tzinfo=UTC),
        )

    with pytest.raises(ValueError, match="gate_status"):
        replace(_gate_report(source), gate_status="paused")
    with pytest.raises(ValueError, match="recommended_next_step"):
        replace(_gate_report(source), recommended_next_step="manual_review")
    with pytest.raises(ValueError, match="reason_code_counts"):
        replace(_gate_report(source), reason_code_counts=(object(),))
    with pytest.raises(ValueError, match="reason_code_counts"):
        replace(
            _gate_report(source),
            reason_code_counts=(
                api.PaperAutonomousAllocationProposalDbHistoryGateReasonCodeCount(
                    "paper_autonomous_allocation_proposal_db_history_gate_passed",
                    1,
                ),
                api.PaperAutonomousAllocationProposalDbHistoryGateReasonCodeCount(
                    "paper_autonomous_allocation_proposal_db_history_gate_passed",
                    1,
                ),
            ),
        )


def test_allocation_proposal_db_history_gate_normalizes_aware_datetimes():
    offset = timezone(timedelta(hours=-4))
    source = _history_report(
        latest_report_generated_at=datetime(2026, 6, 24, 13, 30, tzinfo=offset),
    )

    report = _api().build_paper_autonomous_allocation_proposal_db_history_gate_report(
        source,
        config=_config(),
        generated_at=datetime(2026, 6, 24, 14, 0, tzinfo=offset),
    )

    assert report.generated_at == GENERATED_AT
    assert report.latest_source_generated_at == LATEST_AT
    assert report.latest_source_age_seconds == 1_800
