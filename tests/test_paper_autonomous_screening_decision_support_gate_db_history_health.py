from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta, timezone
from importlib import import_module
from types import SimpleNamespace

import pytest

from polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate import (
    PaperAutonomousScreeningDecisionSupportGateReport,
    build_paper_autonomous_screening_decision_support_gate_report,
)
from tests.test_paper_autonomous_screening_decision_support_gate import (
    _operator_flow_gate_report,
    _priority_report,
    _risk_report,
)


GENERATED_AT = datetime(2026, 6, 25, 12, 0, tzinfo=UTC)


class DatetimeSubclass(datetime):
    pass


def _api():
    return import_module(
        "polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate_db_history_health",
    )


def _config(**overrides):
    values = {
        "config_version": (
            "paper-autonomous-screening-decision-support-gate-db-history-health-v0"
        ),
        "min_source_report_count": 3,
        "max_watch_source_report_count": 0,
        "max_blocked_source_report_count": 0,
        "max_consecutive_watch_count": 0,
        "max_consecutive_blocked_count": 0,
        "max_latest_age_seconds": 86_400,
    }
    values.update(overrides)
    return _api().PaperAutonomousScreeningDecisionSupportGateDbHistoryHealthConfig(
        **values,
    )


def _gate_report(
    *,
    generated_at: datetime,
    gate_status: str = "pass",
    config_version: str = (
        "paper-autonomous-screening-decision-support-gate-v0"
    ),
    operator_flow_gate_config_version: str = (
        "paper-research-packet-operator-flow-db-history-gate-v0"
    ),
    queue_risk_config_version: str = "action-gated-queue-risk-v0",
) -> PaperAutonomousScreeningDecisionSupportGateReport:
    action_status = {
        "pass": "research_ready",
        "watch": "watch",
        "blocked": "blocked",
    }[gate_status]
    risk_status = gate_status
    risk_reason_codes = {
        "pass": ("queue_risk_passed",),
        "watch": ("source_queue_watch",),
        "blocked": ("source_queue_blocked",),
    }[risk_status]

    priority_report = _priority_report(
        generated_at=generated_at,
        action_status=action_status,
    )
    report = build_paper_autonomous_screening_decision_support_gate_report(
        operator_flow_gate_report=_operator_flow_gate_report(gate_status=gate_status),
        priority_report=priority_report,
        risk_report=_risk_report(
            priority_report,
            status=risk_status,
            reason_codes=risk_reason_codes,
        ),
        generated_at=generated_at,
        config_version=config_version,
    )
    return replace(
        report,
        operator_flow_gate_config_version=operator_flow_gate_config_version,
        queue_risk_config_version=queue_risk_config_version,
    )


def _health_report(
    gate_reports: tuple[PaperAutonomousScreeningDecisionSupportGateReport, ...],
    **config_overrides,
):
    return _api().build_paper_autonomous_screening_decision_support_gate_db_history_health_report(
        gate_reports,
        config=_config(**config_overrides),
        generated_at=GENERATED_AT,
    )


def _corrupt_gate_report(
    report: PaperAutonomousScreeningDecisionSupportGateReport,
    **overrides,
) -> PaperAutonomousScreeningDecisionSupportGateReport:
    corrupted = PaperAutonomousScreeningDecisionSupportGateReport.__new__(
        PaperAutonomousScreeningDecisionSupportGateReport,
    )
    values = dict(report.__dict__)
    values.update(overrides)
    for field_name, value in values.items():
        object.__setattr__(corrupted, field_name, value)
    return corrupted


def _gate_subclass(
    report: PaperAutonomousScreeningDecisionSupportGateReport,
) -> PaperAutonomousScreeningDecisionSupportGateReport:
    class GateReportSubclass(PaperAutonomousScreeningDecisionSupportGateReport):
        pass

    subclass_report = GateReportSubclass.__new__(GateReportSubclass)
    for field_name, value in report.__dict__.items():
        object.__setattr__(subclass_report, field_name, value)
    return subclass_report


def test_health_config_defaults_are_safe_phase1_defaults() -> None:
    api = _api()
    config = api.PaperAutonomousScreeningDecisionSupportGateDbHistoryHealthConfig()

    assert config.config_version == (
        api.DEFAULT_PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_DB_HISTORY_HEALTH_CONFIG_VERSION
    )
    assert config.min_source_report_count == 3
    assert config.max_watch_source_report_count == 0
    assert config.max_blocked_source_report_count == 0
    assert config.max_consecutive_watch_count == 0
    assert config.max_consecutive_blocked_count == 0
    assert config.max_latest_age_seconds == 86_400
    assert config.paper_only is True
    assert config.report_only is True
    assert config.readonly is True


def test_health_blocks_empty_and_insufficient_gate_history_samples() -> None:
    empty = _health_report(())
    insufficient = _health_report(
        (
            _gate_report(generated_at=GENERATED_AT - timedelta(minutes=2)),
            _gate_report(generated_at=GENERATED_AT - timedelta(minutes=1)),
        ),
    )

    assert empty.source_report_count == 0
    assert empty.health_status == "blocked"
    assert empty.recommended_next_step == (
        "block_paper_autonomous_screening_decision_support_gate_history_review"
    )
    assert empty.latest_gate_status is None
    assert empty.latest_gate_generated_at is None
    assert empty.latest_gate_age_seconds is None
    assert empty.consecutive_latest_watch_count == 0
    assert empty.consecutive_latest_blocked_count == 0
    assert empty.distinct_gate_config_versions == ()
    assert empty.distinct_operator_flow_gate_config_versions == ()
    assert empty.distinct_queue_risk_config_versions == ()
    assert empty.reason_code_counts == ()
    assert empty.reason_codes == (
        "insufficient_paper_autonomous_screening_decision_support_gate_history_samples",
    )

    assert insufficient.source_report_count == 2
    assert insufficient.health_status == "blocked"
    assert insufficient.pass_gate_report_count == 2
    assert insufficient.reason_codes == (
        "insufficient_paper_autonomous_screening_decision_support_gate_history_samples",
    )


def test_health_passes_clean_recent_gate_history_and_summarizes_versions() -> None:
    report = _health_report(
        (
            _gate_report(
                generated_at=GENERATED_AT - timedelta(seconds=1_800),
                config_version="gate-v0",
                operator_flow_gate_config_version="operator-v0",
                queue_risk_config_version="queue-risk-v0",
            ),
            _gate_report(
                generated_at=GENERATED_AT - timedelta(seconds=1_200),
                config_version="gate-v1",
                operator_flow_gate_config_version="operator-v0",
                queue_risk_config_version="queue-risk-v1",
            ),
            _gate_report(
                generated_at=GENERATED_AT - timedelta(seconds=600),
                config_version="gate-v1",
                operator_flow_gate_config_version="operator-v1",
                queue_risk_config_version="queue-risk-v1",
            ),
        ),
    )

    assert report.health_status == "pass"
    assert report.recommended_next_step == (
        "allow_paper_autonomous_screening_decision_support_gate_history_review"
    )
    assert report.source_report_count == 3
    assert report.pass_gate_report_count == 3
    assert report.watch_gate_report_count == 0
    assert report.blocked_gate_report_count == 0
    assert report.latest_gate_status == "pass"
    assert report.latest_gate_generated_at == GENERATED_AT - timedelta(seconds=600)
    assert report.latest_gate_age_seconds == 600
    assert report.consecutive_latest_watch_count == 0
    assert report.consecutive_latest_blocked_count == 0
    assert report.distinct_gate_config_versions == ("gate-v0", "gate-v1")
    assert report.distinct_operator_flow_gate_config_versions == (
        "operator-v0",
        "operator-v1",
    )
    assert report.distinct_queue_risk_config_versions == (
        "queue-risk-v0",
        "queue-risk-v1",
    )
    assert report.reason_code_counts == (
        _api().PaperAutonomousScreeningDecisionSupportGateDbHistoryHealthReasonCodeCount(
            "paper_autonomous_screening_decision_support_gate_passed",
            3,
        ),
    )
    assert report.reason_codes == (
        "paper_autonomous_screening_decision_support_gate_db_history_health_passed",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_health_blocks_latest_blocked_even_when_count_threshold_allows_it() -> None:
    report = _health_report(
        (
            _gate_report(generated_at=GENERATED_AT - timedelta(hours=3)),
            _gate_report(generated_at=GENERATED_AT - timedelta(hours=2)),
            _gate_report(
                generated_at=GENERATED_AT - timedelta(hours=1),
                gate_status="blocked",
            ),
        ),
        max_blocked_source_report_count=2,
        max_consecutive_blocked_count=2,
    )

    assert report.health_status == "blocked"
    assert report.latest_gate_status == "blocked"
    assert report.blocked_gate_report_count == 1
    assert report.consecutive_latest_blocked_count == 1
    assert report.consecutive_latest_watch_count == 0
    assert report.reason_codes == (
        "latest_paper_autonomous_screening_decision_support_gate_blocked",
    )


def test_health_watches_latest_watch_and_consecutive_watch_streak() -> None:
    report = _health_report(
        (
            _gate_report(generated_at=GENERATED_AT - timedelta(hours=4)),
            _gate_report(
                generated_at=GENERATED_AT - timedelta(hours=3),
                gate_status="watch",
            ),
            _gate_report(
                generated_at=GENERATED_AT - timedelta(hours=2),
                gate_status="watch",
            ),
            _gate_report(
                generated_at=GENERATED_AT - timedelta(hours=1),
                gate_status="watch",
            ),
        ),
        max_watch_source_report_count=4,
    )

    assert report.health_status == "watch"
    assert report.latest_gate_status == "watch"
    assert report.watch_gate_report_count == 3
    assert report.consecutive_latest_watch_count == 3
    assert report.consecutive_latest_blocked_count == 0
    assert report.reason_codes == (
        "consecutive_paper_autonomous_screening_decision_support_gate_watch_threshold_exceeded",
        "latest_paper_autonomous_screening_decision_support_gate_watch",
    )


def test_health_blocks_excess_blocked_count_and_consecutive_blocked_streak() -> None:
    report = _health_report(
        (
            _gate_report(generated_at=GENERATED_AT - timedelta(hours=4)),
            _gate_report(
                generated_at=GENERATED_AT - timedelta(hours=3),
                gate_status="blocked",
            ),
            _gate_report(
                generated_at=GENERATED_AT - timedelta(hours=2),
                gate_status="blocked",
            ),
            _gate_report(
                generated_at=GENERATED_AT - timedelta(hours=1),
                gate_status="blocked",
            ),
        ),
        max_blocked_source_report_count=1,
        max_consecutive_blocked_count=2,
    )

    assert report.health_status == "blocked"
    assert report.blocked_gate_report_count == 3
    assert report.consecutive_latest_blocked_count == 3
    assert report.reason_codes == (
        "blocked_paper_autonomous_screening_decision_support_gate_count_threshold_exceeded",
        "consecutive_paper_autonomous_screening_decision_support_gate_blocked_threshold_exceeded",
        "latest_paper_autonomous_screening_decision_support_gate_blocked",
    )


def test_health_watches_stale_latest_gate_history() -> None:
    report = _health_report(
        (
            _gate_report(generated_at=GENERATED_AT - timedelta(seconds=86_403)),
            _gate_report(generated_at=GENERATED_AT - timedelta(seconds=86_402)),
            _gate_report(generated_at=GENERATED_AT - timedelta(seconds=86_401)),
        ),
    )

    assert report.health_status == "watch"
    assert report.latest_gate_age_seconds == 86_401
    assert report.reason_codes == (
        "stale_paper_autonomous_screening_decision_support_gate_history",
    )


def test_health_reason_code_counts_are_source_presence_counts_and_deterministic() -> None:
    report = _health_report(
        (
            _gate_report(
                generated_at=GENERATED_AT - timedelta(seconds=1_800),
                gate_status="watch",
            ),
            _gate_report(
                generated_at=GENERATED_AT - timedelta(seconds=1_200),
                gate_status="blocked",
            ),
            _gate_report(
                generated_at=GENERATED_AT - timedelta(seconds=600),
                gate_status="blocked",
            ),
        ),
        max_blocked_source_report_count=3,
        max_watch_source_report_count=3,
        max_consecutive_blocked_count=3,
    )

    assert report.reason_code_counts == (
        _api().PaperAutonomousScreeningDecisionSupportGateDbHistoryHealthReasonCodeCount(
            "operator_flow_db_history_gate_blocked",
            2,
        ),
        _api().PaperAutonomousScreeningDecisionSupportGateDbHistoryHealthReasonCodeCount(
            "queue_risk_blocked",
            2,
        ),
        _api().PaperAutonomousScreeningDecisionSupportGateDbHistoryHealthReasonCodeCount(
            "operator_flow_db_history_gate_watch",
            1,
        ),
        _api().PaperAutonomousScreeningDecisionSupportGateDbHistoryHealthReasonCodeCount(
            "queue_risk_watch",
            1,
        ),
    )


def test_health_dataclasses_are_frozen_and_validate_hard_flags() -> None:
    api = _api()
    config = _config()
    reason_count = (
        api.PaperAutonomousScreeningDecisionSupportGateDbHistoryHealthReasonCodeCount(
            "paper_autonomous_screening_decision_support_gate_passed",
            1,
        )
    )
    report = _health_report(
        (
            _gate_report(generated_at=GENERATED_AT - timedelta(hours=3)),
            _gate_report(generated_at=GENERATED_AT - timedelta(hours=2)),
            _gate_report(generated_at=GENERATED_AT - timedelta(hours=1)),
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


def test_health_public_dataclass_subclasses_cannot_be_constructed() -> None:
    api = _api()

    with pytest.raises(TypeError, match="HealthConfig .*subclassing"):
        class ConfigSubclass(
            api.PaperAutonomousScreeningDecisionSupportGateDbHistoryHealthConfig,
        ):
            def __post_init__(self) -> None:
                pass

    with pytest.raises(TypeError, match="HealthReasonCodeCount .*subclassing"):
        class ReasonCodeCountSubclass(
            api.PaperAutonomousScreeningDecisionSupportGateDbHistoryHealthReasonCodeCount,
        ):
            def __post_init__(self) -> None:
                pass

    with pytest.raises(TypeError, match="HealthReport .*subclassing"):
        class ReportSubclass(
            api.PaperAutonomousScreeningDecisionSupportGateDbHistoryHealthReport,
        ):
            def __post_init__(self) -> None:
                pass


@pytest.mark.parametrize(
    ("overrides", "message"),
    (
        ({"config_version": ""}, "config_version"),
        ({"min_source_report_count": 0}, "min_source_report_count"),
        ({"max_watch_source_report_count": True}, "max_watch_source_report_count"),
        ({"max_blocked_source_report_count": -1}, "max_blocked_source_report_count"),
        ({"max_consecutive_watch_count": -1}, "max_consecutive_watch_count"),
        ({"max_consecutive_blocked_count": True}, "max_consecutive_blocked_count"),
        ({"max_latest_age_seconds": 1.5}, "max_latest_age_seconds"),
    ),
)
def test_health_config_rejects_invalid_thresholds(
    overrides: dict[str, object],
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        _config(**overrides)


def test_health_rejects_lists_duck_types_subclasses_and_false_hard_flags() -> None:
    api = _api()
    source = _gate_report(generated_at=GENERATED_AT - timedelta(minutes=5))

    with pytest.raises(ValueError, match="gate_reports must be a tuple"):
        api.build_paper_autonomous_screening_decision_support_gate_db_history_health_report(
            [source],
            config=_config(min_source_report_count=1),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="gate_reports"):
        api.build_paper_autonomous_screening_decision_support_gate_db_history_health_report(
            (SimpleNamespace(**source.__dict__),),
            config=_config(min_source_report_count=1),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="gate_reports"):
        api.build_paper_autonomous_screening_decision_support_gate_db_history_health_report(
            (_gate_subclass(source),),
            config=_config(min_source_report_count=1),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="paper_only"):
        api.build_paper_autonomous_screening_decision_support_gate_db_history_health_report(
            (_corrupt_gate_report(source, paper_only=False),),
            config=_config(min_source_report_count=1),
            generated_at=GENERATED_AT,
        )


def test_health_rejects_wrong_config_generated_at_and_corrupt_source_datetimes() -> None:
    api = _api()
    source = _gate_report(generated_at=GENERATED_AT - timedelta(minutes=5))

    with pytest.raises(ValueError, match="config must be"):
        api.build_paper_autonomous_screening_decision_support_gate_db_history_health_report(
            (source,),
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        api.build_paper_autonomous_screening_decision_support_gate_db_history_health_report(
            (source,),
            config=_config(min_source_report_count=1),
            generated_at=DatetimeSubclass(2026, 6, 25, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        api.build_paper_autonomous_screening_decision_support_gate_db_history_health_report(
            (source,),
            config=_config(min_source_report_count=1),
            generated_at=datetime(2026, 6, 25, 12, 0),
        )
    with pytest.raises(ValueError, match="source generated_at must be timezone-aware"):
        api.build_paper_autonomous_screening_decision_support_gate_db_history_health_report(
            (_corrupt_gate_report(source, generated_at=datetime(2026, 6, 25, 11, 55)),),
            config=_config(min_source_report_count=1),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="future dated"):
        api.build_paper_autonomous_screening_decision_support_gate_db_history_health_report(
            (_gate_report(generated_at=GENERATED_AT + timedelta(seconds=1)),),
            config=_config(min_source_report_count=1),
            generated_at=GENERATED_AT,
        )


def test_health_report_rejects_inconsistent_direct_construction() -> None:
    report = _health_report(
        (
            _gate_report(generated_at=GENERATED_AT - timedelta(hours=3)),
            _gate_report(generated_at=GENERATED_AT - timedelta(hours=2)),
            _gate_report(generated_at=GENERATED_AT - timedelta(hours=1)),
        ),
    )

    with pytest.raises(ValueError, match="source_report_count"):
        replace(report, source_report_count=4)
    with pytest.raises(ValueError, match="recommended_next_step"):
        replace(report, recommended_next_step="manual_review")
    with pytest.raises(ValueError, match="reason_code_counts"):
        replace(report, reason_code_counts=(object(),))
    with pytest.raises(ValueError, match="reason_codes"):
        replace(
            report,
            reason_codes=(
                "paper_autonomous_screening_decision_support_gate_db_history_health_passed",
                "stale_paper_autonomous_screening_decision_support_gate_history",
            ),
        )
    with pytest.raises(ValueError, match="latest_gate_age_seconds"):
        replace(report, latest_gate_age_seconds=None)
    with pytest.raises(ValueError, match="distinct_gate_config_versions"):
        replace(report, distinct_gate_config_versions=("gate-v1", "gate-v0"))


def test_health_normalizes_aware_datetimes_to_utc() -> None:
    offset = timezone(timedelta(hours=-4))
    report = _api().build_paper_autonomous_screening_decision_support_gate_db_history_health_report(
        (
            _gate_report(
                generated_at=datetime(2026, 6, 25, 6, 0, tzinfo=offset),
            ),
            _gate_report(
                generated_at=datetime(2026, 6, 25, 6, 10, tzinfo=offset),
            ),
            _gate_report(
                generated_at=datetime(2026, 6, 25, 6, 30, tzinfo=offset),
            ),
        ),
        config=_config(),
        generated_at=datetime(2026, 6, 25, 8, 0, tzinfo=offset),
    )

    assert report.generated_at == GENERATED_AT
    assert report.latest_gate_generated_at == datetime(2026, 6, 25, 10, 30, tzinfo=UTC)
    assert report.latest_gate_age_seconds == 5_400
