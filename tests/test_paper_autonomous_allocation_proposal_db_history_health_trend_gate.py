from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from importlib import import_module

import pytest

from polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_health import (
    PaperAutonomousAllocationProposalDbHistoryHealthReasonCodeCount,
    PaperAutonomousAllocationProposalDbHistoryHealthReport,
)
from polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_health_trend import (
    PaperAutonomousAllocationProposalDbHistoryHealthTrendReasonCodeRow,
    PaperAutonomousAllocationProposalDbHistoryHealthTrendReport,
    PaperAutonomousAllocationProposalDbHistoryHealthTrendSnapshotSummary,
    build_paper_autonomous_allocation_proposal_db_history_health_trend_report,
)

GENERATED_AT = datetime(2026, 6, 24, 18, 0, tzinfo=UTC)
SOURCE_AT = datetime(2026, 6, 24, 17, 45, tzinfo=UTC)


def d(value: str) -> Decimal:
    return Decimal(value)


def _api():
    return import_module(
        "polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_health_trend_gate",
    )


def _config(**overrides):
    values = {
        "config_version": (
            "paper-autonomous-allocation-proposal-db-history-health-trend-gate-v0"
        ),
        "min_source_health_report_count": 3,
        "max_consecutive_latest_watch_count": 0,
        "max_consecutive_latest_blocked_count": 0,
        "max_duplicate_generated_at_count": 0,
        "max_latest_source_age_seconds": 86_400,
        "max_trend_report_age_seconds": 86_400,
        "max_watch_report_count_delta": 0,
        "max_blocked_report_count_delta": 0,
        "max_repeated_reason_code_count": 0,
    }
    values.update(overrides)
    return _api().PaperAutonomousAllocationProposalDbHistoryHealthTrendGateConfig(
        **values,
    )


def _source_summaries(
    *,
    source_count: int,
    latest_health_status: str | None,
    latest_source_age_seconds: int | None,
    watch_delta: int | None,
    blocked_delta: int | None,
) -> tuple[PaperAutonomousAllocationProposalDbHistoryHealthTrendSnapshotSummary, ...]:
    summaries = []
    for index in range(source_count):
        is_latest = index + 1 == source_count
        generated_at = SOURCE_AT - timedelta(minutes=source_count - index - 1)
        health_status = "pass" if not is_latest else (latest_health_status or "blocked")
        watch_report_count = (
            watch_delta
            if is_latest and watch_delta is not None and source_count > 1
            else 0
        )
        blocked_report_count = (
            blocked_delta
            if is_latest and blocked_delta is not None and source_count > 1
            else 0
        )
        latest_allocated_count = 2 if is_latest and source_count > 1 else 1
        latest_total_allocated_paper_notional = (
            d("20.000000") if is_latest and source_count > 1 else d("10.000000")
        )
        summaries.append(
            PaperAutonomousAllocationProposalDbHistoryHealthTrendSnapshotSummary(
                index + 1,
                generated_at,
                health_status,
                3 + watch_report_count + blocked_report_count,
                3,
                watch_report_count,
                blocked_report_count,
                latest_allocated_count,
                latest_total_allocated_paper_notional,
                latest_source_age_seconds,
                latest_source_age_seconds,
                ("paper_autonomous_allocation_proposal_db_history_health_passed",),
            ),
        )
    return tuple(summaries)


def _clean_health_report(
    *,
    generated_at: datetime,
) -> PaperAutonomousAllocationProposalDbHistoryHealthReport:
    pass_reason = "paper_autonomous_allocation_proposal_db_history_health_passed"
    return PaperAutonomousAllocationProposalDbHistoryHealthReport(
        generated_at=generated_at,
        config_version="paper-autonomous-allocation-proposal-db-history-health-v0",
        health_status="pass",
        recommended_next_step=(
            "allow_paper_autonomous_allocation_proposal_history_review"
        ),
        history_report_count=3,
        pass_report_count=3,
        watch_report_count=0,
        blocked_report_count=0,
        latest_history_status="pass",
        latest_proposal_status="pass",
        latest_allocated_count=1,
        latest_total_allocated_paper_notional=d("10.000000"),
        max_source_age_seconds=600,
        latest_source_age_seconds=300,
        duplicate_latest_report_generated_at_count=0,
        reason_code_counts=(
            PaperAutonomousAllocationProposalDbHistoryHealthReasonCodeCount(
                pass_reason,
                1,
            ),
        ),
        reason_codes=(pass_reason,),
    )


def _delta(first: int | None, latest: int | None) -> int | None:
    if first is None or latest is None:
        return None
    return latest - first


def _decimal_delta(first: Decimal | None, latest: Decimal | None) -> Decimal | None:
    if first is None or latest is None:
        return None
    return latest - first


def _trend_report(
    *,
    source_count: int = 3,
    latest_health_status: str | None = "pass",
    consecutive_watch: int = 0,
    consecutive_blocked: int = 0,
    duplicate_generated_at_count: int = 0,
    latest_source_age_seconds: int | None = 300,
    watch_delta: int | None = 0,
    blocked_delta: int | None = 0,
    repeated_reason_counts: tuple[tuple[str, int], ...] = (),
) -> PaperAutonomousAllocationProposalDbHistoryHealthTrendReport:
    source_summaries = _source_summaries(
        source_count=source_count,
        latest_health_status=latest_health_status,
        latest_source_age_seconds=latest_source_age_seconds,
        watch_delta=watch_delta,
        blocked_delta=blocked_delta,
    )
    first = source_summaries[0] if source_summaries else None
    latest = source_summaries[-1] if source_summaries else None
    status_counts = (
        (
            "pass",
            source_count
            if latest_health_status == "pass"
            else max(source_count - 1, 0),
        ),
        ("watch", 1 if latest_health_status == "watch" else 0),
        ("blocked", 1 if latest_health_status == "blocked" else 0),
    )
    return PaperAutonomousAllocationProposalDbHistoryHealthTrendReport(
        generated_at=SOURCE_AT,
        config_version="paper-autonomous-allocation-proposal-db-history-health-trend-v0",
        source_health_report_count=source_count,
        first_generated_at=first.generated_at if first is not None else None,
        latest_generated_at=latest.generated_at if latest is not None else None,
        latest_health_status=latest_health_status if source_count else None,
        health_status_counts=status_counts,
        consecutive_latest_watch_count=consecutive_watch,
        consecutive_latest_blocked_count=consecutive_blocked,
        duplicate_generated_at_count=duplicate_generated_at_count,
        history_report_count_first=(
            first.history_report_count if first is not None else None
        ),
        history_report_count_latest=(
            latest.history_report_count if latest is not None else None
        ),
        history_report_count_delta=_delta(
            first.history_report_count if first is not None else None,
            latest.history_report_count if latest is not None else None,
        ),
        pass_report_count_first=(
            first.pass_report_count if first is not None else None
        ),
        pass_report_count_latest=(
            latest.pass_report_count if latest is not None else None
        ),
        pass_report_count_delta=_delta(
            first.pass_report_count if first is not None else None,
            latest.pass_report_count if latest is not None else None,
        ),
        watch_report_count_first=(
            first.watch_report_count if first is not None else None
        ),
        watch_report_count_latest=(
            latest.watch_report_count if latest is not None else None
        ),
        watch_report_count_delta=_delta(
            first.watch_report_count if first is not None else None,
            latest.watch_report_count if latest is not None else None,
        ),
        blocked_report_count_first=(
            first.blocked_report_count if first is not None else None
        ),
        blocked_report_count_latest=(
            latest.blocked_report_count if latest is not None else None
        ),
        blocked_report_count_delta=_delta(
            first.blocked_report_count if first is not None else None,
            latest.blocked_report_count if latest is not None else None,
        ),
        latest_allocated_count_first=(
            first.latest_allocated_count if first is not None else None
        ),
        latest_allocated_count_latest=(
            latest.latest_allocated_count if latest is not None else None
        ),
        latest_allocated_count_delta=_delta(
            first.latest_allocated_count if first is not None else None,
            latest.latest_allocated_count if latest is not None else None,
        ),
        latest_total_allocated_paper_notional_first=(
            first.latest_total_allocated_paper_notional
            if first is not None
            else None
        ),
        latest_total_allocated_paper_notional_latest=(
            latest.latest_total_allocated_paper_notional
            if latest is not None
            else None
        ),
        latest_total_allocated_paper_notional_delta=_decimal_delta(
            first.latest_total_allocated_paper_notional
            if first is not None
            else None,
            latest.latest_total_allocated_paper_notional
            if latest is not None
            else None,
        ),
        latest_source_age_seconds_first=(
            first.latest_source_age_seconds if first is not None else None
        ),
        latest_source_age_seconds_latest=(
            latest.latest_source_age_seconds if latest is not None else None
        ),
        latest_source_age_seconds_delta=_delta(
            first.latest_source_age_seconds if first is not None else None,
            latest.latest_source_age_seconds if latest is not None else None,
        ),
        max_source_age_seconds_first=(
            first.max_source_age_seconds if first is not None else None
        ),
        max_source_age_seconds_latest=(
            latest.max_source_age_seconds if latest is not None else None
        ),
        max_source_age_seconds_delta=_delta(
            first.max_source_age_seconds if first is not None else None,
            latest.max_source_age_seconds if latest is not None else None,
        ),
        latest_reason_code_counts=(),
        total_reason_code_counts=repeated_reason_counts,
        repeated_reason_code_counts=repeated_reason_counts,
        reason_code_rows=tuple(
            PaperAutonomousAllocationProposalDbHistoryHealthTrendReasonCodeRow(
                code,
                count,
                0,
                0,
            )
            for code, count in repeated_reason_counts
        ),
        source_summaries=source_summaries,
    )


def test_trend_report_helper_builds_valid_source_report():
    report = _trend_report()
    assert report.source_health_report_count == 3
    assert report.latest_health_status == "pass"
    assert report.latest_source_age_seconds_latest == 300


def test_health_trend_gate_config_defaults_are_safe_phase1_defaults() -> None:
    api = _api()

    config = api.PaperAutonomousAllocationProposalDbHistoryHealthTrendGateConfig()

    assert config.config_version == (
        api.DEFAULT_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_HEALTH_TREND_GATE_CONFIG_VERSION
    )
    assert config.config_version == (
        "paper-autonomous-allocation-proposal-db-history-health-trend-gate-v0"
    )
    assert config.min_source_health_report_count == 3
    assert config.max_consecutive_latest_watch_count == 0
    assert config.max_consecutive_latest_blocked_count == 0
    assert config.max_duplicate_generated_at_count == 0
    assert config.max_latest_source_age_seconds == 86_400
    assert config.max_trend_report_age_seconds == 86_400
    assert config.max_watch_report_count_delta == 0
    assert config.max_blocked_report_count_delta == 0
    assert config.max_repeated_reason_code_count == 0
    assert config.paper_only is True
    assert config.report_only is True
    assert config.readonly is True


def test_health_trend_gate_passes_clean_source_trend():
    report = _api().build_paper_autonomous_allocation_proposal_db_history_health_trend_gate_report(
        _trend_report(),
        config=_config(),
        generated_at=GENERATED_AT,
    )
    assert report.gate_status == "pass"
    assert report.recommended_next_step == (
        "allow_paper_autonomous_allocation_proposal_db_history_health_trend_review"
    )
    assert report.reason_codes == (
        "paper_autonomous_allocation_proposal_db_history_health_trend_gate_passed",
    )
    assert report.source_health_report_count == 3
    assert report.trend_report_age_seconds == 900
    assert report.latest_health_status == "pass"
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_health_trend_gate_passes_real_clean_all_pass_repeated_pass_reasons():
    trend = build_paper_autonomous_allocation_proposal_db_history_health_trend_report(
        (
            _clean_health_report(generated_at=SOURCE_AT - timedelta(minutes=2)),
            _clean_health_report(generated_at=SOURCE_AT - timedelta(minutes=1)),
            _clean_health_report(generated_at=SOURCE_AT),
        ),
        config=import_module(
            "polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_health_trend",
        ).PaperAutonomousAllocationProposalDbHistoryHealthTrendConfig(),
        generated_at=GENERATED_AT,
    )

    assert trend.repeated_reason_code_counts == (
        ("paper_autonomous_allocation_proposal_db_history_health_passed", 3),
    )

    report = _api().build_paper_autonomous_allocation_proposal_db_history_health_trend_gate_report(
        trend,
        config=_config(),
        generated_at=GENERATED_AT,
    )

    assert report.gate_status == "pass"
    assert report.reason_codes == (
        "paper_autonomous_allocation_proposal_db_history_health_trend_gate_passed",
    )


def test_health_trend_gate_blocks_missing_source_timestamp_without_stale_reason() -> None:
    report = _api().build_paper_autonomous_allocation_proposal_db_history_health_trend_gate_report(
        _trend_report(
            latest_health_status="blocked",
            latest_source_age_seconds=None,
        ),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    assert report.source_health_report_count == 3
    assert report.latest_source_age_seconds is None
    assert report.gate_status == "blocked"
    assert (
        "latest_allocation_proposal_db_history_health_trend_blocked"
        in report.reason_codes
    )
    assert "stale_allocation_proposal_db_history_health_trend" not in report.reason_codes
    assert (
        "missing_latest_allocation_proposal_db_history_health_trend_timestamp"
        not in report.reason_codes
    )


def test_health_trend_gate_watches_stale_trend_report_age() -> None:
    report = _api().build_paper_autonomous_allocation_proposal_db_history_health_trend_gate_report(
        _trend_report(),
        config=_config(max_trend_report_age_seconds=899),
        generated_at=GENERATED_AT,
    )

    assert report.gate_status == "watch"
    assert report.trend_report_age_seconds == 900
    assert "stale_allocation_proposal_db_history_health_trend" in report.reason_codes
    assert (
        "paper_autonomous_allocation_proposal_db_history_health_trend_gate_passed"
        not in report.reason_codes
    )


def test_health_trend_gate_rejects_future_dated_trend_report() -> None:
    with pytest.raises(ValueError, match="trend_report_age_seconds"):
        _api().build_paper_autonomous_allocation_proposal_db_history_health_trend_gate_report(
            _trend_report(),
            config=_config(),
            generated_at=SOURCE_AT - timedelta(seconds=1),
        )


@pytest.mark.parametrize(
    ("trend", "expected_reason"),
    (
        (
            _trend_report(source_count=1),
            "insufficient_allocation_proposal_db_history_health_trend_samples",
        ),
        (
            _trend_report(latest_health_status="blocked", consecutive_blocked=1),
            "latest_allocation_proposal_db_history_health_trend_blocked",
        ),
        (
            _trend_report(latest_health_status=None, source_count=0),
            "missing_latest_allocation_proposal_db_history_health_trend_timestamp",
        ),
    ),
)
def test_health_trend_gate_blocks_for_blocking_trend_inputs(trend, expected_reason):
    report = _api().build_paper_autonomous_allocation_proposal_db_history_health_trend_gate_report(
        trend,
        config=_config(),
        generated_at=GENERATED_AT,
    )
    assert report.gate_status == "blocked"
    assert report.recommended_next_step == (
        "block_paper_autonomous_allocation_proposal_db_history_health_trend_review"
    )
    assert expected_reason in report.reason_codes


@pytest.mark.parametrize(
    ("trend", "expected_reason"),
    (
        (
            _trend_report(latest_health_status="watch", consecutive_watch=1),
            "latest_allocation_proposal_db_history_health_trend_watch",
        ),
        (
            _trend_report(duplicate_generated_at_count=1),
            "duplicate_allocation_proposal_db_history_health_trend_timestamp_threshold_exceeded",
        ),
        (
            _trend_report(watch_delta=1),
            "worsening_allocation_proposal_db_history_health_trend_watch_count",
        ),
        (
            _trend_report(blocked_delta=1),
            "worsening_allocation_proposal_db_history_health_trend_blocked_count",
        ),
        (
            _trend_report(
                repeated_reason_counts=(
                    ("stale_allocation_proposal_db_history", 2),
                ),
            ),
            "repeated_allocation_proposal_db_history_health_trend_reason_threshold_exceeded",
        ),
        (
            _trend_report(latest_source_age_seconds=86_401),
            "stale_allocation_proposal_db_history_health_trend",
        ),
    ),
)
def test_health_trend_gate_watches_for_watch_trend_inputs(trend, expected_reason):
    report = _api().build_paper_autonomous_allocation_proposal_db_history_health_trend_gate_report(
        trend,
        config=_config(),
        generated_at=GENERATED_AT,
    )
    assert report.gate_status == "watch"
    assert report.recommended_next_step == (
        "throttle_paper_autonomous_allocation_proposal_db_history_health_trend_review"
    )
    assert expected_reason in report.reason_codes


def test_health_trend_gate_reason_code_counts_are_deterministic_and_positive():
    trend = _trend_report(
        latest_health_status="blocked",
        consecutive_blocked=2,
        duplicate_generated_at_count=1,
        blocked_delta=1,
        repeated_reason_counts=(
            ("latest_allocation_proposal_db_history_blocked", 2),
        ),
    )
    report = _api().build_paper_autonomous_allocation_proposal_db_history_health_trend_gate_report(
        trend,
        config=_config(
            min_source_health_report_count=4,
            max_consecutive_latest_blocked_count=1,
        ),
        generated_at=GENERATED_AT,
    )
    assert report.gate_status == "blocked"
    assert report.reason_codes == tuple(row.reason_code for row in report.reason_code_counts)
    assert all(row.report_count == 1 for row in report.reason_code_counts)
    assert (
        "paper_autonomous_allocation_proposal_db_history_health_trend_gate_passed"
        not in report.reason_codes
    )


def test_health_trend_gate_dataclasses_are_frozen_and_validate_hard_flags():
    api = _api()
    config = _config()
    report = api.build_paper_autonomous_allocation_proposal_db_history_health_trend_gate_report(
        _trend_report(),
        config=config,
        generated_at=GENERATED_AT,
    )
    with pytest.raises(FrozenInstanceError):
        config.config_version = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.gate_status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="config .*paper_only"):
        replace(config, paper_only=False)
    with pytest.raises(ValueError, match="gate report .*readonly"):
        replace(report, readonly=False)
