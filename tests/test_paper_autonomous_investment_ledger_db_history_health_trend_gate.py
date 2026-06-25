from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from importlib import import_module

import pytest

from polymarket_alpha_lab.paper_autonomous_investment_ledger_db_history_health import (
    PaperAutonomousInvestmentLedgerDbHistoryHealthReasonCodeCount,
    PaperAutonomousInvestmentLedgerDbHistoryHealthReport,
)
from polymarket_alpha_lab.paper_autonomous_investment_ledger_db_history_health_trend import (
    PaperAutonomousInvestmentLedgerDbHistoryHealthTrendConfig,
    build_paper_autonomous_investment_ledger_db_history_health_trend_report,
)


GENERATED_AT = datetime(2026, 6, 25, 22, 0, tzinfo=UTC)
SOURCE_AT = datetime(2026, 6, 25, 21, 45, tzinfo=UTC)
SOURCE_HEALTH_PASS_REASON_CODE = (
    "paper_autonomous_investment_ledger_db_history_health_passed"
)
NEXT_STEP_BY_HEALTH_STATUS = {
    "pass": "allow_paper_autonomous_investment_ledger_review",
    "watch": "throttle_paper_autonomous_investment_ledger_review",
    "blocked": "block_paper_autonomous_investment_ledger_review",
}


class DatetimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value).quantize(Decimal("0.000001"))


def _api():
    return import_module(
        "polymarket_alpha_lab."
        "paper_autonomous_investment_ledger_db_history_health_trend_gate",
    )


def _config(**overrides):
    values = {
        "config_version": (
            "paper-autonomous-investment-ledger-db-history-health-trend-gate-v0"
        ),
        "min_source_health_report_count": 3,
        "max_consecutive_latest_watch_count": 0,
        "max_consecutive_latest_blocked_count": 0,
        "max_duplicate_generated_at_count": 0,
        "max_latest_source_age_seconds": 86_400,
        "max_watch_ledger_report_count_delta": 0,
        "max_blocked_ledger_report_count_delta": 0,
        "max_repeated_reason_code_count": 0,
    }
    values.update(overrides)
    return _api().PaperAutonomousInvestmentLedgerDbHistoryHealthTrendGateConfig(
        **values,
    )


def _reason_count(
    reason_code: str,
) -> PaperAutonomousInvestmentLedgerDbHistoryHealthReasonCodeCount:
    return PaperAutonomousInvestmentLedgerDbHistoryHealthReasonCodeCount(
        reason_code,
        1,
    )


def _health_report(
    *,
    generated_at: datetime,
    health_status: str = "pass",
    reason_codes: tuple[str, ...] | None = None,
    ledger_report_count: int = 3,
    pass_ledger_report_count: int = 3,
    watch_ledger_report_count: int = 0,
    blocked_ledger_report_count: int = 0,
    latest_ledger_status: str | None = None,
    latest_source_record_count: int = 1,
    latest_submitted_count: int = 1,
    latest_held_count: int = 0,
    latest_blocked_count: int = 0,
    latest_total_submitted_notional: Decimal = d("10.000000"),
    latest_source_age_seconds: int | None = 300,
    max_source_age_seconds: int | None = 600,
    duplicate_latest_generated_at_count: int = 0,
) -> PaperAutonomousInvestmentLedgerDbHistoryHealthReport:
    if reason_codes is None:
        reason_codes = {
            "pass": (SOURCE_HEALTH_PASS_REASON_CODE,),
            "watch": ("latest_paper_autonomous_investment_ledger_watch",),
            "blocked": ("latest_paper_autonomous_investment_ledger_blocked",),
        }[health_status]
    if latest_ledger_status is None:
        latest_ledger_status = {
            "pass": "pass",
            "watch": "watch",
            "blocked": "blocked",
        }[health_status]
    latest_source_generated_at = None
    if latest_source_age_seconds is not None:
        latest_source_generated_at = generated_at - timedelta(
            seconds=latest_source_age_seconds,
        )
    return PaperAutonomousInvestmentLedgerDbHistoryHealthReport(
        generated_at=generated_at,
        config_version="paper-autonomous-investment-ledger-db-history-health-v0",
        health_status=health_status,
        recommended_next_step=NEXT_STEP_BY_HEALTH_STATUS[health_status],
        ledger_report_count=ledger_report_count,
        pass_ledger_report_count=pass_ledger_report_count,
        watch_ledger_report_count=watch_ledger_report_count,
        blocked_ledger_report_count=blocked_ledger_report_count,
        latest_ledger_status=latest_ledger_status,
        latest_source_record_count=latest_source_record_count,
        latest_submitted_count=latest_submitted_count,
        latest_held_count=latest_held_count,
        latest_blocked_count=latest_blocked_count,
        latest_total_submitted_notional=latest_total_submitted_notional,
        latest_source_generated_at=latest_source_generated_at,
        latest_source_age_seconds=latest_source_age_seconds,
        max_source_age_seconds=max_source_age_seconds,
        duplicate_latest_generated_at_count=duplicate_latest_generated_at_count,
        reason_code_counts=tuple(_reason_count(code) for code in reason_codes),
        reason_codes=reason_codes,
    )


def _trend_report(*health_reports: PaperAutonomousInvestmentLedgerDbHistoryHealthReport):
    return build_paper_autonomous_investment_ledger_db_history_health_trend_report(
        health_reports,
        config=PaperAutonomousInvestmentLedgerDbHistoryHealthTrendConfig(),
        generated_at=SOURCE_AT,
    )


def _clean_trend_report():
    return _trend_report(
        _health_report(generated_at=SOURCE_AT - timedelta(minutes=2)),
        _health_report(generated_at=SOURCE_AT - timedelta(minutes=1)),
        _health_report(generated_at=SOURCE_AT),
    )


def test_health_trend_gate_config_defaults_are_safe_phase1_defaults() -> None:
    api = _api()

    config = api.PaperAutonomousInvestmentLedgerDbHistoryHealthTrendGateConfig()

    assert config.config_version == (
        api.DEFAULT_PAPER_AUTONOMOUS_INVESTMENT_LEDGER_DB_HISTORY_HEALTH_TREND_GATE_CONFIG_VERSION
    )
    assert config.config_version == (
        "paper-autonomous-investment-ledger-db-history-health-trend-gate-v0"
    )
    assert config.min_source_health_report_count == 3
    assert config.max_consecutive_latest_watch_count == 0
    assert config.max_consecutive_latest_blocked_count == 0
    assert config.max_duplicate_generated_at_count == 0
    assert config.max_latest_source_age_seconds == 86_400
    assert config.max_watch_ledger_report_count_delta == 0
    assert config.max_blocked_ledger_report_count_delta == 0
    assert config.max_repeated_reason_code_count == 0
    assert config.paper_only is True
    assert config.report_only is True
    assert config.readonly is True


def test_health_trend_gate_public_all_exports_constants_dataclasses_and_builder() -> None:
    api = _api()

    assert set(api.__all__) == {
        "DEFAULT_PAPER_AUTONOMOUS_INVESTMENT_LEDGER_DB_HISTORY_HEALTH_TREND_GATE_CONFIG_VERSION",
        "PaperAutonomousInvestmentLedgerDbHistoryHealthTrendGateConfig",
        "PaperAutonomousInvestmentLedgerDbHistoryHealthTrendGateReasonCodeCount",
        "PaperAutonomousInvestmentLedgerDbHistoryHealthTrendGateReport",
        "build_paper_autonomous_investment_ledger_db_history_health_trend_gate_report",
    }


def test_health_trend_gate_passes_clean_source_trend() -> None:
    report = _api().build_paper_autonomous_investment_ledger_db_history_health_trend_gate_report(
        _clean_trend_report(),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    assert report.generated_at == GENERATED_AT
    assert report.source_generated_at == SOURCE_AT
    assert report.gate_status == "pass"
    assert report.recommended_next_step == (
        "allow_paper_autonomous_investment_ledger_db_history_health_trend_review"
    )
    assert report.reason_codes == (
        "paper_autonomous_investment_ledger_db_history_health_trend_gate_passed",
    )
    assert report.source_health_report_count == 3
    assert report.latest_health_status == "pass"
    assert report.latest_health_generated_at == SOURCE_AT
    assert report.latest_source_age_seconds == 300
    assert report.watch_ledger_report_count_delta == 0
    assert report.blocked_ledger_report_count_delta == 0
    assert report.latest_submitted_count_delta == 0
    assert report.latest_total_submitted_notional_delta == d("0.000000")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_health_trend_gate_passes_clean_all_pass_repeated_pass_reasons() -> None:
    trend = _clean_trend_report()

    assert trend.repeated_reason_code_counts == (
        (SOURCE_HEALTH_PASS_REASON_CODE, 3),
    )

    report = _api().build_paper_autonomous_investment_ledger_db_history_health_trend_gate_report(
        trend,
        config=_config(),
        generated_at=GENERATED_AT,
    )

    assert report.gate_status == "pass"
    assert report.reason_codes == (
        "paper_autonomous_investment_ledger_db_history_health_trend_gate_passed",
    )


@pytest.mark.parametrize(
    ("trend", "expected_reason"),
    (
        (
            _trend_report(_health_report(generated_at=SOURCE_AT)),
            "insufficient_paper_autonomous_investment_ledger_db_history_health_trend_samples",
        ),
        (
            _trend_report(
                _health_report(generated_at=SOURCE_AT - timedelta(minutes=2)),
                _health_report(generated_at=SOURCE_AT - timedelta(minutes=1)),
                _health_report(generated_at=SOURCE_AT, health_status="blocked"),
            ),
            "latest_paper_autonomous_investment_ledger_db_history_health_trend_blocked",
        ),
        (
            _trend_report(),
            "missing_latest_paper_autonomous_investment_ledger_db_history_health_trend_timestamp",
        ),
        (
            _trend_report(
                _health_report(generated_at=SOURCE_AT - timedelta(minutes=2)),
                _health_report(
                    generated_at=SOURCE_AT - timedelta(minutes=1),
                    health_status="blocked",
                ),
                _health_report(generated_at=SOURCE_AT, health_status="blocked"),
            ),
            "consecutive_paper_autonomous_investment_ledger_db_history_health_trend_blocked_threshold_exceeded",
        ),
    ),
)
def test_health_trend_gate_blocks_for_blocking_trend_inputs(trend, expected_reason):
    report = _api().build_paper_autonomous_investment_ledger_db_history_health_trend_gate_report(
        trend,
        config=_config(),
        generated_at=GENERATED_AT,
    )

    assert report.gate_status == "blocked"
    assert report.recommended_next_step == (
        "block_paper_autonomous_investment_ledger_db_history_health_trend_review"
    )
    assert expected_reason in report.reason_codes
    assert (
        "paper_autonomous_investment_ledger_db_history_health_trend_gate_passed"
        not in report.reason_codes
    )


@pytest.mark.parametrize(
    ("trend", "expected_reason"),
    (
        (
            _trend_report(
                _health_report(generated_at=SOURCE_AT - timedelta(minutes=2)),
                _health_report(generated_at=SOURCE_AT - timedelta(minutes=1)),
                _health_report(generated_at=SOURCE_AT, health_status="watch"),
            ),
            "latest_paper_autonomous_investment_ledger_db_history_health_trend_watch",
        ),
        (
            _trend_report(
                _health_report(generated_at=SOURCE_AT - timedelta(minutes=2)),
                _health_report(
                    generated_at=SOURCE_AT - timedelta(minutes=1),
                    health_status="watch",
                ),
                _health_report(generated_at=SOURCE_AT, health_status="watch"),
            ),
            "consecutive_paper_autonomous_investment_ledger_db_history_health_trend_watch_threshold_exceeded",
        ),
        (
            _trend_report(
                _health_report(generated_at=SOURCE_AT - timedelta(minutes=1)),
                _health_report(generated_at=SOURCE_AT),
                _health_report(generated_at=SOURCE_AT),
            ),
            "duplicate_paper_autonomous_investment_ledger_db_history_health_trend_timestamp_threshold_exceeded",
        ),
        (
            _trend_report(
                _health_report(generated_at=SOURCE_AT - timedelta(minutes=2)),
                _health_report(generated_at=SOURCE_AT - timedelta(minutes=1)),
                _health_report(
                    generated_at=SOURCE_AT,
                    health_status="watch",
                    reason_codes=(
                        "watch_paper_autonomous_investment_ledger_count_threshold_exceeded",
                    ),
                    ledger_report_count=4,
                    watch_ledger_report_count=1,
                ),
            ),
            "worsening_paper_autonomous_investment_ledger_db_history_health_trend_watch_count",
        ),
        (
            _trend_report(
                _health_report(generated_at=SOURCE_AT - timedelta(minutes=2)),
                _health_report(generated_at=SOURCE_AT - timedelta(minutes=1)),
                _health_report(
                    generated_at=SOURCE_AT,
                    health_status="watch",
                    reason_codes=(
                        "watch_paper_autonomous_investment_ledger_count_threshold_exceeded",
                    ),
                    ledger_report_count=4,
                    blocked_ledger_report_count=1,
                ),
            ),
            "worsening_paper_autonomous_investment_ledger_db_history_health_trend_blocked_count",
        ),
        (
            _trend_report(
                _health_report(
                    generated_at=SOURCE_AT - timedelta(minutes=2),
                    health_status="watch",
                    reason_codes=(
                        "stale_paper_autonomous_investment_ledger_source_history",
                    ),
                ),
                _health_report(
                    generated_at=SOURCE_AT - timedelta(minutes=1),
                    health_status="watch",
                    reason_codes=(
                        "stale_paper_autonomous_investment_ledger_source_history",
                    ),
                ),
                _health_report(generated_at=SOURCE_AT),
            ),
            "repeated_paper_autonomous_investment_ledger_db_history_health_trend_reason_threshold_exceeded",
        ),
        (
            _trend_report(
                _health_report(generated_at=SOURCE_AT - timedelta(minutes=2)),
                _health_report(generated_at=SOURCE_AT - timedelta(minutes=1)),
                _health_report(
                    generated_at=SOURCE_AT,
                    health_status="watch",
                    reason_codes=(
                        "stale_paper_autonomous_investment_ledger_source_history",
                    ),
                    latest_source_age_seconds=86_401,
                    max_source_age_seconds=86_401,
                ),
            ),
            "stale_paper_autonomous_investment_ledger_db_history_health_trend",
        ),
    ),
)
def test_health_trend_gate_watches_for_watch_trend_inputs(trend, expected_reason):
    report = _api().build_paper_autonomous_investment_ledger_db_history_health_trend_gate_report(
        trend,
        config=_config(),
        generated_at=GENERATED_AT,
    )

    assert report.gate_status == "watch"
    assert report.recommended_next_step == (
        "throttle_paper_autonomous_investment_ledger_db_history_health_trend_review"
    )
    assert expected_reason in report.reason_codes
    assert (
        "paper_autonomous_investment_ledger_db_history_health_trend_gate_passed"
        not in report.reason_codes
    )


def test_health_trend_gate_reason_code_counts_are_deterministic_and_positive() -> None:
    trend = _trend_report(
        _health_report(generated_at=SOURCE_AT - timedelta(minutes=2)),
        _health_report(generated_at=SOURCE_AT - timedelta(minutes=1)),
        _health_report(
            generated_at=SOURCE_AT,
            health_status="blocked",
            duplicate_latest_generated_at_count=1,
        ),
    )

    report = _api().build_paper_autonomous_investment_ledger_db_history_health_trend_gate_report(
        trend,
        config=_config(
            min_source_health_report_count=4,
            max_consecutive_latest_blocked_count=0,
        ),
        generated_at=GENERATED_AT,
    )

    assert report.gate_status == "blocked"
    assert report.reason_codes == tuple(row.reason_code for row in report.reason_code_counts)
    assert all(row.report_count == 1 for row in report.reason_code_counts)
    assert report.reason_codes == tuple(sorted(report.reason_codes))
    assert (
        "paper_autonomous_investment_ledger_db_history_health_trend_gate_passed"
        not in report.reason_codes
    )


def test_health_trend_gate_dataclasses_are_frozen_and_validate_hard_flags() -> None:
    api = _api()
    config = _config()
    reason_count = api.PaperAutonomousInvestmentLedgerDbHistoryHealthTrendGateReasonCodeCount(
        "paper_autonomous_investment_ledger_db_history_health_trend_gate_passed",
        1,
    )
    report = api.build_paper_autonomous_investment_ledger_db_history_health_trend_gate_report(
        _clean_trend_report(),
        config=config,
        generated_at=GENERATED_AT,
    )

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


def test_health_trend_gate_public_dataclass_subclasses_cannot_be_constructed() -> None:
    api = _api()

    with pytest.raises(TypeError, match="TrendGateConfig .*subclassing"):
        class ConfigSubclass(
            api.PaperAutonomousInvestmentLedgerDbHistoryHealthTrendGateConfig,
        ):
            pass

    with pytest.raises(TypeError, match="TrendGateReasonCodeCount .*subclassing"):
        class ReasonCodeCountSubclass(
            api.PaperAutonomousInvestmentLedgerDbHistoryHealthTrendGateReasonCodeCount,
        ):
            pass

    with pytest.raises(TypeError, match="TrendGateReport .*subclassing"):
        class ReportSubclass(
            api.PaperAutonomousInvestmentLedgerDbHistoryHealthTrendGateReport,
        ):
            pass


def test_health_trend_gate_rejects_wrong_types_naive_datetimes_and_corruption() -> None:
    api = _api()
    trend = _clean_trend_report()

    with pytest.raises(ValueError, match="trend_report"):
        api.build_paper_autonomous_investment_ledger_db_history_health_trend_gate_report(
            object(),
            config=_config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="config must be"):
        api.build_paper_autonomous_investment_ledger_db_history_health_trend_gate_report(
            trend,
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        api.build_paper_autonomous_investment_ledger_db_history_health_trend_gate_report(
            trend,
            config=_config(),
            generated_at=DatetimeSubclass(2026, 6, 25, 22, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        api.build_paper_autonomous_investment_ledger_db_history_health_trend_gate_report(
            trend,
            config=_config(),
            generated_at=datetime(2026, 6, 25, 22, 0),
        )

    report = api.build_paper_autonomous_investment_ledger_db_history_health_trend_gate_report(
        trend,
        config=_config(),
        generated_at=GENERATED_AT,
    )
    with pytest.raises(ValueError, match="recommended_next_step"):
        replace(report, recommended_next_step="manual_review")
    with pytest.raises(ValueError, match="reason_code_counts"):
        replace(report, reason_code_counts=(object(),))
    with pytest.raises(ValueError, match="reason_code_counts must match reason_codes"):
        replace(report, reason_codes=("some_other_reason",))
    with pytest.raises(ValueError, match="latest_total_submitted_notional_delta"):
        replace(report, latest_total_submitted_notional_delta=0.0)
