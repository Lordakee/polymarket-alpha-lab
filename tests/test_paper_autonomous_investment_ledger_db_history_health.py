from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from importlib import import_module

import pytest

from polymarket_alpha_lab.paper_autonomous_investment_ledger import (
    PaperAutonomousInvestmentLedgerReport,
    build_paper_autonomous_investment_ledger_report,
)
from polymarket_alpha_lab.paper_broker import PaperBrokerExecutionRecord


GENERATED_AT = datetime(2026, 6, 25, 18, 0, tzinfo=UTC)
SOURCE_GENERATED_AT = datetime(2026, 6, 25, 17, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


class DatetimeSubclass(datetime):
    pass


def _api():
    return import_module(
        "polymarket_alpha_lab.paper_autonomous_investment_ledger_db_history_health",
    )


def d(value: str) -> Decimal:
    return Decimal(value).quantize(Decimal("0.000001"))


def _config(**overrides):
    values = {
        "config_version": (
            "paper-autonomous-investment-ledger-db-history-health-v0"
        ),
        "min_ledger_report_count": 3,
        "max_watch_ledger_report_count": 0,
        "max_blocked_ledger_report_count": 0,
        "max_duplicate_latest_generated_at_count": 0,
        "max_latest_age_seconds": 86_400,
    }
    values.update(overrides)
    return _api().PaperAutonomousInvestmentLedgerDbHistoryHealthConfig(**values)


def _source_record(
    *,
    generated_at: datetime = SOURCE_GENERATED_AT,
    execution_status: str = "paper_submitted",
    execution_notional: Decimal = d("10.000000"),
    reason_codes: tuple[str, ...] = ("paper_broker_execution_submitted",),
) -> PaperBrokerExecutionRecord:
    return PaperBrokerExecutionRecord(
        generated_at=generated_at,
        config_version="paper-broker-v0",
        execution_status=execution_status,
        recommended_next_step={
            "paper_submitted": "route_to_paper_order_lifecycle",
            "paper_held": "hold_for_broker_review",
            "paper_blocked": "block_paper_execution_pending_repair",
        }[execution_status],
        source_gate_status={
            "paper_submitted": "pass",
            "paper_held": "watch",
            "paper_blocked": "blocked",
        }[execution_status],
        source_proposal_count=1,
        source_proposal_total_notional=d("10.000000"),
        execution_notional=execution_notional,
        reason_codes=reason_codes,
    )


def _ledger_report(
    *,
    latest_generated_at: datetime = SOURCE_GENERATED_AT,
    ledger_status: str = "pass",
    total_submitted_notional: Decimal = d("10.000000"),
) -> PaperAutonomousInvestmentLedgerReport:
    execution_status = {
        "pass": "paper_submitted",
        "watch": "paper_held",
        "blocked": "paper_blocked",
    }[ledger_status]
    execution_notional = (
        total_submitted_notional if execution_status == "paper_submitted" else ZERO
    )
    reason_codes = {
        "paper_submitted": ("paper_broker_execution_submitted",),
        "paper_held": ("paper_broker_gate_held",),
        "paper_blocked": ("paper_broker_gate_blocked",),
    }[execution_status]
    return build_paper_autonomous_investment_ledger_report(
        broker_execution_records=(
            _source_record(
                generated_at=latest_generated_at,
                execution_status=execution_status,
                execution_notional=execution_notional,
                reason_codes=reason_codes,
            ),
        ),
        generated_at=latest_generated_at + timedelta(seconds=60),
    )


def _health_report(
    ledger_reports: tuple[PaperAutonomousInvestmentLedgerReport, ...],
    **config_overrides,
):
    return _api().build_paper_autonomous_investment_ledger_db_history_health_report(
        ledger_reports,
        config=_config(**config_overrides),
        generated_at=GENERATED_AT,
    )


def _corrupt_ledger_report(
    report: PaperAutonomousInvestmentLedgerReport,
    **overrides,
) -> PaperAutonomousInvestmentLedgerReport:
    corrupted = PaperAutonomousInvestmentLedgerReport.__new__(
        PaperAutonomousInvestmentLedgerReport,
    )
    values = dict(report.__dict__)
    values.update(overrides)
    for field_name, value in values.items():
        object.__setattr__(corrupted, field_name, value)
    return corrupted


def test_health_config_defaults_are_safe_paper_report_readonly_defaults() -> None:
    api = _api()

    config = api.PaperAutonomousInvestmentLedgerDbHistoryHealthConfig()

    assert config.config_version == (
        api.DEFAULT_PAPER_AUTONOMOUS_INVESTMENT_LEDGER_DB_HISTORY_HEALTH_CONFIG_VERSION
    )
    assert config.config_version == (
        "paper-autonomous-investment-ledger-db-history-health-v0"
    )
    assert config.min_ledger_report_count == 3
    assert config.max_watch_ledger_report_count == 0
    assert config.max_blocked_ledger_report_count == 0
    assert config.max_duplicate_latest_generated_at_count == 0
    assert config.max_latest_age_seconds == 86_400
    assert config.paper_only is True
    assert config.report_only is True
    assert config.readonly is True


def test_health_public_all_exports_constants_dataclasses_and_builder() -> None:
    api = _api()

    assert set(api.__all__) == {
        "DEFAULT_PAPER_AUTONOMOUS_INVESTMENT_LEDGER_DB_HISTORY_HEALTH_CONFIG_VERSION",
        "HEALTH_STATUSES",
        "NEXT_STEP_BY_STATUS",
        "PASS_REASON_CODE",
        "BLOCKED_REASON_CODES",
        "WATCH_REASON_CODES",
        "HEALTH_REASON_CODES",
        "PaperAutonomousInvestmentLedgerDbHistoryHealthConfig",
        "PaperAutonomousInvestmentLedgerDbHistoryHealthReasonCodeCount",
        "PaperAutonomousInvestmentLedgerDbHistoryHealthReport",
        "build_paper_autonomous_investment_ledger_db_history_health_report",
    }
    assert api.HEALTH_STATUSES == ("pass", "watch", "blocked")
    assert api.NEXT_STEP_BY_STATUS == {
        "pass": "allow_paper_autonomous_investment_ledger_review",
        "watch": "throttle_paper_autonomous_investment_ledger_review",
        "blocked": "block_paper_autonomous_investment_ledger_review",
    }


def test_health_blocks_empty_and_insufficient_ledger_report_samples() -> None:
    empty = _health_report(())
    insufficient = _health_report(
        (
            _ledger_report(
                latest_generated_at=GENERATED_AT - timedelta(seconds=1_200),
            ),
            _ledger_report(
                latest_generated_at=GENERATED_AT - timedelta(seconds=600),
            ),
        ),
    )

    assert empty.ledger_report_count == 0
    assert empty.health_status == "blocked"
    assert empty.recommended_next_step == (
        "block_paper_autonomous_investment_ledger_review"
    )
    assert empty.latest_ledger_status is None
    assert empty.latest_source_record_count is None
    assert empty.latest_submitted_count is None
    assert empty.latest_held_count is None
    assert empty.latest_blocked_count is None
    assert empty.latest_total_submitted_notional is None
    assert empty.latest_source_generated_at is None
    assert empty.latest_source_age_seconds is None
    assert empty.max_source_age_seconds is None
    assert empty.duplicate_latest_generated_at_count == 0
    assert empty.reason_code_counts == ()
    assert empty.reason_codes == (
        "insufficient_paper_autonomous_investment_ledger_samples",
    )

    assert insufficient.ledger_report_count == 2
    assert insufficient.health_status == "blocked"
    assert insufficient.pass_ledger_report_count == 2
    assert insufficient.reason_codes == (
        "insufficient_paper_autonomous_investment_ledger_samples",
    )


def test_health_passes_clean_recent_pass_history_and_preserves_latest_decimal() -> None:
    report = _health_report(
        (
            _ledger_report(
                latest_generated_at=GENERATED_AT - timedelta(seconds=1_800),
                total_submitted_notional=d("10.000000"),
            ),
            _ledger_report(
                latest_generated_at=GENERATED_AT - timedelta(seconds=1_200),
                total_submitted_notional=d("15.500000"),
            ),
            _ledger_report(
                latest_generated_at=GENERATED_AT - timedelta(seconds=600),
                total_submitted_notional=d("42.250000"),
            ),
        ),
    )

    assert report.health_status == "pass"
    assert report.recommended_next_step == (
        "allow_paper_autonomous_investment_ledger_review"
    )
    assert report.ledger_report_count == 3
    assert report.pass_ledger_report_count == 3
    assert report.watch_ledger_report_count == 0
    assert report.blocked_ledger_report_count == 0
    assert report.latest_ledger_status == "pass"
    assert report.latest_source_record_count == 1
    assert report.latest_submitted_count == 1
    assert report.latest_held_count == 0
    assert report.latest_blocked_count == 0
    assert report.latest_total_submitted_notional == d("42.250000")
    assert type(report.latest_total_submitted_notional) is Decimal
    assert report.latest_source_generated_at == GENERATED_AT - timedelta(seconds=600)
    assert report.latest_source_age_seconds == 600
    assert report.max_source_age_seconds == 1_800
    assert report.duplicate_latest_generated_at_count == 0
    assert report.reason_code_counts == (
        _api().PaperAutonomousInvestmentLedgerDbHistoryHealthReasonCodeCount(
            "paper_autonomous_investment_ledger_passed",
            3,
        ),
    )
    assert report.reason_codes == (
        "paper_autonomous_investment_ledger_db_history_health_passed",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_health_blocks_when_latest_ledger_report_is_blocked() -> None:
    report = _health_report(
        (
            _ledger_report(latest_generated_at=GENERATED_AT - timedelta(hours=3)),
            _ledger_report(latest_generated_at=GENERATED_AT - timedelta(hours=2)),
            _ledger_report(
                latest_generated_at=GENERATED_AT - timedelta(hours=1),
                ledger_status="blocked",
            ),
        ),
        max_blocked_ledger_report_count=2,
    )

    assert report.health_status == "blocked"
    assert report.latest_ledger_status == "blocked"
    assert report.reason_codes == (
        "latest_paper_autonomous_investment_ledger_blocked",
    )


def test_health_blocks_excess_blocked_ledger_report_count() -> None:
    report = _health_report(
        (
            _ledger_report(
                latest_generated_at=GENERATED_AT - timedelta(hours=3),
                ledger_status="blocked",
            ),
            _ledger_report(latest_generated_at=GENERATED_AT - timedelta(hours=2)),
            _ledger_report(latest_generated_at=GENERATED_AT - timedelta(hours=1)),
        ),
    )

    assert report.health_status == "blocked"
    assert report.blocked_ledger_report_count == 1
    assert report.latest_ledger_status == "pass"
    assert report.reason_codes == (
        "blocked_paper_autonomous_investment_ledger_count_threshold_exceeded",
    )


def test_health_blocks_missing_latest_source_timestamp() -> None:
    source = _corrupt_ledger_report(
        _ledger_report(),
        latest_generated_at=None,
    )

    report = _health_report((source,), min_ledger_report_count=1)

    assert report.health_status == "blocked"
    assert report.latest_source_generated_at is None
    assert report.latest_source_age_seconds is None
    assert report.max_source_age_seconds is None
    assert report.reason_codes == (
        "missing_latest_paper_autonomous_investment_ledger_source_timestamp",
    )


def test_health_watches_when_latest_ledger_report_is_watch() -> None:
    report = _health_report(
        (
            _ledger_report(latest_generated_at=GENERATED_AT - timedelta(hours=3)),
            _ledger_report(latest_generated_at=GENERATED_AT - timedelta(hours=2)),
            _ledger_report(
                latest_generated_at=GENERATED_AT - timedelta(hours=1),
                ledger_status="watch",
            ),
        ),
        max_watch_ledger_report_count=2,
    )

    assert report.health_status == "watch"
    assert report.recommended_next_step == (
        "throttle_paper_autonomous_investment_ledger_review"
    )
    assert report.latest_ledger_status == "watch"
    assert report.reason_codes == (
        "latest_paper_autonomous_investment_ledger_watch",
    )


def test_health_watches_excess_watch_ledger_report_count() -> None:
    report = _health_report(
        (
            _ledger_report(
                latest_generated_at=GENERATED_AT - timedelta(hours=3),
                ledger_status="watch",
            ),
            _ledger_report(latest_generated_at=GENERATED_AT - timedelta(hours=2)),
            _ledger_report(latest_generated_at=GENERATED_AT - timedelta(hours=1)),
        ),
    )

    assert report.health_status == "watch"
    assert report.watch_ledger_report_count == 1
    assert report.latest_ledger_status == "pass"
    assert report.reason_codes == (
        "watch_paper_autonomous_investment_ledger_count_threshold_exceeded",
    )


def test_health_watches_stale_latest_source_age() -> None:
    report = _health_report(
        (
            _ledger_report(
                latest_generated_at=GENERATED_AT - timedelta(seconds=86_403),
            ),
            _ledger_report(
                latest_generated_at=GENERATED_AT - timedelta(seconds=86_402),
            ),
            _ledger_report(
                latest_generated_at=GENERATED_AT - timedelta(seconds=86_401),
            ),
        ),
    )

    assert report.health_status == "watch"
    assert report.latest_source_age_seconds == 86_401
    assert report.max_source_age_seconds == 86_403
    assert report.reason_codes == (
        "stale_paper_autonomous_investment_ledger_source_history",
    )


def test_health_watches_duplicate_latest_source_generated_at_values() -> None:
    report = _health_report(
        (
            _ledger_report(
                latest_generated_at=GENERATED_AT - timedelta(seconds=900),
            ),
            _ledger_report(
                latest_generated_at=GENERATED_AT - timedelta(seconds=900),
            ),
            _ledger_report(
                latest_generated_at=GENERATED_AT - timedelta(seconds=600),
            ),
        ),
    )

    assert report.health_status == "watch"
    assert report.duplicate_latest_generated_at_count == 1
    assert report.reason_codes == (
        "duplicate_latest_paper_autonomous_investment_ledger_source_generated_at_threshold_exceeded",
    )


def test_health_dataclasses_are_frozen_and_validate_hard_flags() -> None:
    api = _api()
    config = _config()
    reason_count = api.PaperAutonomousInvestmentLedgerDbHistoryHealthReasonCodeCount(
        "paper_autonomous_investment_ledger_passed",
        1,
    )
    report = _health_report(
        (
            _ledger_report(latest_generated_at=GENERATED_AT - timedelta(hours=3)),
            _ledger_report(latest_generated_at=GENERATED_AT - timedelta(hours=2)),
            _ledger_report(latest_generated_at=GENERATED_AT - timedelta(hours=1)),
        ),
    )

    with pytest.raises(FrozenInstanceError):
        config.config_version = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        reason_count.report_count = 2  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.health_status = "blocked"  # type: ignore[misc]

    with pytest.raises(ValueError, match="config .*paper_only"):
        replace(config, paper_only=False)
    with pytest.raises(ValueError, match="reason code count .*report_only"):
        replace(reason_count, report_only=False)
    with pytest.raises(ValueError, match="health report .*readonly"):
        replace(report, readonly=False)


def test_health_public_dataclass_subclasses_are_rejected() -> None:
    api = _api()

    with pytest.raises(TypeError, match="HealthConfig .*subclassing"):
        class ConfigSubclass(api.PaperAutonomousInvestmentLedgerDbHistoryHealthConfig):
            def __post_init__(self) -> None:
                pass

    with pytest.raises(TypeError, match="HealthReasonCodeCount .*subclassing"):
        class ReasonCodeCountSubclass(
            api.PaperAutonomousInvestmentLedgerDbHistoryHealthReasonCodeCount,
        ):
            def __post_init__(self) -> None:
                pass

    with pytest.raises(TypeError, match="HealthReport .*subclassing"):
        class ReportSubclass(api.PaperAutonomousInvestmentLedgerDbHistoryHealthReport):
            def __post_init__(self) -> None:
                pass


@pytest.mark.parametrize(
    ("overrides", "message"),
    (
        ({"config_version": ""}, "config_version"),
        ({"min_ledger_report_count": True}, "min_ledger_report_count"),
        ({"min_ledger_report_count": 0}, "min_ledger_report_count"),
        ({"max_watch_ledger_report_count": True}, "max_watch_ledger_report_count"),
        ({"max_blocked_ledger_report_count": -1}, "max_blocked_ledger_report_count"),
        (
            {"max_duplicate_latest_generated_at_count": -1},
            "max_duplicate_latest_generated_at_count",
        ),
        ({"max_latest_age_seconds": 1.5}, "max_latest_age_seconds"),
    ),
)
def test_health_config_rejects_invalid_thresholds(
    overrides: dict[str, object],
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        _config(**overrides)


def test_health_rejects_wrong_types_naive_datetimes_and_corrupt_flags() -> None:
    api = _api()
    source = _ledger_report()

    with pytest.raises(ValueError, match="ledger_reports"):
        api.build_paper_autonomous_investment_ledger_db_history_health_report(
            object(),
            config=_config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="ledger_reports"):
        api.build_paper_autonomous_investment_ledger_db_history_health_report(
            (object(),),
            config=_config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="config must be"):
        api.build_paper_autonomous_investment_ledger_db_history_health_report(
            (source,),
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        api.build_paper_autonomous_investment_ledger_db_history_health_report(
            (source,),
            config=_config(min_ledger_report_count=1),
            generated_at=DatetimeSubclass(2026, 6, 25, 18, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        api.build_paper_autonomous_investment_ledger_db_history_health_report(
            (source,),
            config=_config(min_ledger_report_count=1),
            generated_at=datetime(2026, 6, 25, 18, 0),
        )
    with pytest.raises(ValueError, match="ledger report .*paper_only"):
        api.build_paper_autonomous_investment_ledger_db_history_health_report(
            (_corrupt_ledger_report(source, paper_only=False),),
            config=_config(min_ledger_report_count=1),
            generated_at=GENERATED_AT,
        )

    report = _health_report((source,), min_ledger_report_count=1)
    with pytest.raises(ValueError, match="ledger_report_count"):
        replace(report, ledger_report_count=2)
    with pytest.raises(ValueError, match="recommended_next_step"):
        replace(report, recommended_next_step="manual_review")
    with pytest.raises(ValueError, match="reason_code_counts"):
        replace(report, reason_code_counts=(object(),))
    with pytest.raises(ValueError, match="latest_total_submitted_notional"):
        replace(report, latest_total_submitted_notional=42.0)
    with pytest.raises(ValueError, match="reason_codes"):
        replace(
            report,
            reason_codes=(
                "paper_autonomous_investment_ledger_db_history_health_passed",
                "stale_paper_autonomous_investment_ledger_source_history",
            ),
        )


def test_health_normalizes_aware_datetimes_to_utc() -> None:
    offset = timezone(timedelta(hours=-4))
    report = _api().build_paper_autonomous_investment_ledger_db_history_health_report(
        (
            _ledger_report(
                latest_generated_at=datetime(2026, 6, 25, 12, 0, tzinfo=offset),
            ),
            _ledger_report(
                latest_generated_at=datetime(2026, 6, 25, 12, 10, tzinfo=offset),
            ),
            _ledger_report(
                latest_generated_at=datetime(2026, 6, 25, 12, 30, tzinfo=offset),
            ),
        ),
        config=_config(),
        generated_at=datetime(2026, 6, 25, 14, 0, tzinfo=offset),
    )

    assert report.generated_at == GENERATED_AT
    assert report.latest_source_generated_at == datetime(2026, 6, 25, 16, 30, tzinfo=UTC)
    assert report.latest_source_age_seconds == 5_400
    assert report.max_source_age_seconds == 7_200
