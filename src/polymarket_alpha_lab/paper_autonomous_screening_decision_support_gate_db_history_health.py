"""Pure paper-only health reducer for autonomous screening gate history."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate import (
    GATE_STATUSES,
    PaperAutonomousScreeningDecisionSupportGateReasonCodeCount,
    PaperAutonomousScreeningDecisionSupportGateReport,
)


DEFAULT_PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_DB_HISTORY_HEALTH_CONFIG_VERSION = (
    "paper-autonomous-screening-decision-support-gate-db-history-health-v0"
)

HEALTH_STATUSES = ("pass", "watch", "blocked")
NEXT_STEP_BY_STATUS = {
    "pass": "allow_paper_autonomous_screening_decision_support_gate_history_review",
    "watch": "throttle_paper_autonomous_screening_decision_support_gate_history_review",
    "blocked": "block_paper_autonomous_screening_decision_support_gate_history_review",
}
PASS_REASON_CODE = (
    "paper_autonomous_screening_decision_support_gate_db_history_health_passed"
)
BLOCKED_REASON_CODES = frozenset(
    (
        "insufficient_paper_autonomous_screening_decision_support_gate_history_samples",
        "latest_paper_autonomous_screening_decision_support_gate_blocked",
        "blocked_paper_autonomous_screening_decision_support_gate_count_threshold_exceeded",
        "consecutive_paper_autonomous_screening_decision_support_gate_blocked_threshold_exceeded",
    ),
)
WATCH_REASON_CODES = frozenset(
    (
        "latest_paper_autonomous_screening_decision_support_gate_watch",
        "watch_paper_autonomous_screening_decision_support_gate_count_threshold_exceeded",
        "consecutive_paper_autonomous_screening_decision_support_gate_watch_threshold_exceeded",
        "stale_paper_autonomous_screening_decision_support_gate_history",
    ),
)
HEALTH_REASON_CODES = BLOCKED_REASON_CODES | WATCH_REASON_CODES | frozenset(
    (PASS_REASON_CODE,),
)

__all__ = (
    "DEFAULT_PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_DB_HISTORY_HEALTH_CONFIG_VERSION",
    "PaperAutonomousScreeningDecisionSupportGateDbHistoryHealthConfig",
    "PaperAutonomousScreeningDecisionSupportGateDbHistoryHealthReasonCodeCount",
    "PaperAutonomousScreeningDecisionSupportGateDbHistoryHealthReport",
    "build_paper_autonomous_screening_decision_support_gate_db_history_health_report",
)


@dataclass(frozen=True)
class PaperAutonomousScreeningDecisionSupportGateDbHistoryHealthConfig:
    config_version: str = (
        DEFAULT_PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_DB_HISTORY_HEALTH_CONFIG_VERSION
    )
    min_source_report_count: int = 3
    max_watch_source_report_count: int = 0
    max_blocked_source_report_count: int = 0
    max_consecutive_watch_count: int = 0
    max_consecutive_blocked_count: int = 0
    max_latest_age_seconds: int = 86_400
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not PaperAutonomousScreeningDecisionSupportGateDbHistoryHealthConfig:
            raise TypeError(
                "PaperAutonomousScreeningDecisionSupportGateDbHistoryHealthConfig "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not PaperAutonomousScreeningDecisionSupportGateDbHistoryHealthConfig:
            raise ValueError(
                "config must be exactly "
                "PaperAutonomousScreeningDecisionSupportGateDbHistoryHealthConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        _require_positive_int("min_source_report_count", self.min_source_report_count)
        for field_name in (
            "max_watch_source_report_count",
            "max_blocked_source_report_count",
            "max_consecutive_watch_count",
            "max_consecutive_blocked_count",
            "max_latest_age_seconds",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        _validate_hard_flags("config", self)


@dataclass(frozen=True)
class PaperAutonomousScreeningDecisionSupportGateDbHistoryHealthReasonCodeCount:
    reason_code: str
    report_count: int
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs) -> None:
        super().__init_subclass__(**kwargs)
        if (
            cls
            is not PaperAutonomousScreeningDecisionSupportGateDbHistoryHealthReasonCodeCount
        ):
            raise TypeError(
                "PaperAutonomousScreeningDecisionSupportGateDbHistoryHealthReasonCodeCount "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if (
            type(self)
            is not PaperAutonomousScreeningDecisionSupportGateDbHistoryHealthReasonCodeCount
        ):
            raise ValueError(
                "reason code count must be exactly "
                "PaperAutonomousScreeningDecisionSupportGateDbHistoryHealthReasonCodeCount",
            )
        _require_canonical_string("reason_code", self.reason_code)
        _require_positive_int("report_count", self.report_count)
        _validate_hard_flags("reason code count", self)


@dataclass(frozen=True)
class PaperAutonomousScreeningDecisionSupportGateDbHistoryHealthReport:
    generated_at: datetime
    config_version: str
    health_status: str
    recommended_next_step: str
    source_report_count: int
    pass_gate_report_count: int
    watch_gate_report_count: int
    blocked_gate_report_count: int
    latest_gate_status: str | None
    latest_gate_generated_at: datetime | None
    latest_gate_age_seconds: int | None
    consecutive_latest_watch_count: int
    consecutive_latest_blocked_count: int
    distinct_gate_config_versions: tuple[str, ...]
    distinct_operator_flow_gate_config_versions: tuple[str, ...]
    distinct_queue_risk_config_versions: tuple[str, ...]
    reason_code_counts: tuple[
        PaperAutonomousScreeningDecisionSupportGateDbHistoryHealthReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not PaperAutonomousScreeningDecisionSupportGateDbHistoryHealthReport:
            raise TypeError(
                "PaperAutonomousScreeningDecisionSupportGateDbHistoryHealthReport "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not PaperAutonomousScreeningDecisionSupportGateDbHistoryHealthReport:
            raise ValueError(
                "health report must be exactly "
                "PaperAutonomousScreeningDecisionSupportGateDbHistoryHealthReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "latest_gate_generated_at",
            _as_optional_utc("latest_gate_generated_at", self.latest_gate_generated_at),
        )
        _require_canonical_string("config_version", self.config_version)
        _require_health_status("health_status", self.health_status)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        for field_name in (
            "source_report_count",
            "pass_gate_report_count",
            "watch_gate_report_count",
            "blocked_gate_report_count",
            "consecutive_latest_watch_count",
            "consecutive_latest_blocked_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        _require_optional_nonnegative_int(
            "latest_gate_age_seconds",
            self.latest_gate_age_seconds,
        )
        if self.latest_gate_status is not None:
            _require_gate_status("latest_gate_status", self.latest_gate_status)
        object.__setattr__(
            self,
            "distinct_gate_config_versions",
            _normalize_string_tuple(
                "distinct_gate_config_versions",
                self.distinct_gate_config_versions,
            ),
        )
        object.__setattr__(
            self,
            "distinct_operator_flow_gate_config_versions",
            _normalize_string_tuple(
                "distinct_operator_flow_gate_config_versions",
                self.distinct_operator_flow_gate_config_versions,
            ),
        )
        object.__setattr__(
            self,
            "distinct_queue_risk_config_versions",
            _normalize_string_tuple(
                "distinct_queue_risk_config_versions",
                self.distinct_queue_risk_config_versions,
            ),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                allowed=HEALTH_REASON_CODES,
            ),
        )
        _validate_health_report(self)
        _validate_hard_flags("health report", self)


def build_paper_autonomous_screening_decision_support_gate_db_history_health_report(
    gate_reports: object,
    *,
    config: PaperAutonomousScreeningDecisionSupportGateDbHistoryHealthConfig,
    generated_at: datetime,
) -> PaperAutonomousScreeningDecisionSupportGateDbHistoryHealthReport:
    if type(config) is not PaperAutonomousScreeningDecisionSupportGateDbHistoryHealthConfig:
        raise ValueError(
            "config must be a "
            "PaperAutonomousScreeningDecisionSupportGateDbHistoryHealthConfig",
        )
    generated_at_utc = _as_utc("generated_at", generated_at)
    _validate_hard_flags("config", config)

    reports = _normalize_gate_reports(gate_reports)
    ordered_reports = _ordered_gate_reports(reports)
    latest_report = ordered_reports[-1] if ordered_reports else None
    pass_report_count = _status_count(reports, "pass")
    watch_report_count = _status_count(reports, "watch")
    blocked_report_count = _status_count(reports, "blocked")
    consecutive_watch_count = _consecutive_latest_status_count(
        ordered_reports,
        "watch",
    )
    consecutive_blocked_count = _consecutive_latest_status_count(
        ordered_reports,
        "blocked",
    )
    latest_gate_age_seconds = (
        _age_seconds(generated_at_utc, latest_report.generated_at)
        if latest_report is not None
        else None
    )
    reason_codes = _health_reason_codes(
        reports=reports,
        latest_report=latest_report,
        watch_report_count=watch_report_count,
        blocked_report_count=blocked_report_count,
        consecutive_watch_count=consecutive_watch_count,
        consecutive_blocked_count=consecutive_blocked_count,
        latest_gate_age_seconds=latest_gate_age_seconds,
        config=config,
    )
    health_status = _health_status(reason_codes)

    return PaperAutonomousScreeningDecisionSupportGateDbHistoryHealthReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        health_status=health_status,
        recommended_next_step=NEXT_STEP_BY_STATUS[health_status],
        source_report_count=len(reports),
        pass_gate_report_count=pass_report_count,
        watch_gate_report_count=watch_report_count,
        blocked_gate_report_count=blocked_report_count,
        latest_gate_status=latest_report.gate_status if latest_report is not None else None,
        latest_gate_generated_at=(
            latest_report.generated_at if latest_report is not None else None
        ),
        latest_gate_age_seconds=latest_gate_age_seconds,
        consecutive_latest_watch_count=consecutive_watch_count,
        consecutive_latest_blocked_count=consecutive_blocked_count,
        distinct_gate_config_versions=_distinct_values(
            report.config_version for report in reports
        ),
        distinct_operator_flow_gate_config_versions=_distinct_values(
            report.operator_flow_gate_config_version for report in reports
        ),
        distinct_queue_risk_config_versions=_distinct_values(
            report.queue_risk_config_version for report in reports
        ),
        reason_code_counts=_reason_code_counts(reports),
        reason_codes=reason_codes,
    )


def _normalize_gate_reports(
    value: object,
) -> tuple[PaperAutonomousScreeningDecisionSupportGateReport, ...]:
    if type(value) is not tuple:
        raise ValueError("gate_reports must be a tuple")
    reports = value
    for report in reports:
        if type(report) is not PaperAutonomousScreeningDecisionSupportGateReport:
            raise ValueError(
                "gate_reports must contain exact "
                "PaperAutonomousScreeningDecisionSupportGateReport values",
            )
        _validate_source_report(report)
    return reports


def _validate_source_report(
    report: PaperAutonomousScreeningDecisionSupportGateReport,
) -> None:
    _validate_hard_flags("gate report", report)
    _as_utc("source generated_at", report.generated_at)
    _require_canonical_string("source config_version", report.config_version)
    _require_gate_status("source gate_status", report.gate_status)
    _require_canonical_string(
        "source recommended_next_step",
        report.recommended_next_step,
    )
    _require_canonical_string(
        "source operator_flow_gate_config_version",
        report.operator_flow_gate_config_version,
    )
    _as_utc("source operator_flow_gate_generated_at", report.operator_flow_gate_generated_at)
    _require_gate_status("source operator_flow_gate_status", report.operator_flow_gate_status)
    _require_canonical_string(
        "source operator_flow_recommended_next_step",
        report.operator_flow_recommended_next_step,
    )
    _as_utc("source queue_priority_generated_at", report.queue_priority_generated_at)
    _as_utc("source queue_risk_generated_at", report.queue_risk_generated_at)
    _require_canonical_string(
        "source queue_risk_config_version",
        report.queue_risk_config_version,
    )
    _require_gate_status("source queue_risk_status", report.queue_risk_status)
    _require_canonical_string(
        "source queue_risk_recommended_next_step",
        report.queue_risk_recommended_next_step,
    )
    _normalize_source_reason_code_counts(report.reason_code_counts)
    _normalize_reason_codes("source reason_codes", report.reason_codes)


def _health_reason_codes(
    *,
    reports: tuple[PaperAutonomousScreeningDecisionSupportGateReport, ...],
    latest_report: PaperAutonomousScreeningDecisionSupportGateReport | None,
    watch_report_count: int,
    blocked_report_count: int,
    consecutive_watch_count: int,
    consecutive_blocked_count: int,
    latest_gate_age_seconds: int | None,
    config: PaperAutonomousScreeningDecisionSupportGateDbHistoryHealthConfig,
) -> tuple[str, ...]:
    blocked_reasons: list[str] = []
    watch_reasons: list[str] = []

    if len(reports) < config.min_source_report_count:
        blocked_reasons.append(
            "insufficient_paper_autonomous_screening_decision_support_gate_history_samples",
        )
    if latest_report is not None and latest_report.gate_status == "blocked":
        blocked_reasons.append(
            "latest_paper_autonomous_screening_decision_support_gate_blocked",
        )
    if blocked_report_count > config.max_blocked_source_report_count:
        blocked_reasons.append(
            "blocked_paper_autonomous_screening_decision_support_gate_count_threshold_exceeded",
        )
    if consecutive_blocked_count > config.max_consecutive_blocked_count:
        blocked_reasons.append(
            "consecutive_paper_autonomous_screening_decision_support_gate_blocked_threshold_exceeded",
        )

    if latest_report is not None and latest_report.gate_status == "watch":
        watch_reasons.append(
            "latest_paper_autonomous_screening_decision_support_gate_watch",
        )
    if watch_report_count > config.max_watch_source_report_count:
        watch_reasons.append(
            "watch_paper_autonomous_screening_decision_support_gate_count_threshold_exceeded",
        )
    if consecutive_watch_count > config.max_consecutive_watch_count:
        watch_reasons.append(
            "consecutive_paper_autonomous_screening_decision_support_gate_watch_threshold_exceeded",
        )
    if (
        latest_gate_age_seconds is not None
        and latest_gate_age_seconds > config.max_latest_age_seconds
    ):
        watch_reasons.append(
            "stale_paper_autonomous_screening_decision_support_gate_history",
        )

    reason_codes = blocked_reasons + watch_reasons
    if not reason_codes:
        reason_codes.append(PASS_REASON_CODE)
    return tuple(sorted(set(reason_codes)))


def _health_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in BLOCKED_REASON_CODES for reason_code in reason_codes):
        return "blocked"
    if any(reason_code in WATCH_REASON_CODES for reason_code in reason_codes):
        return "watch"
    return "pass"


def _ordered_gate_reports(
    reports: tuple[PaperAutonomousScreeningDecisionSupportGateReport, ...],
) -> tuple[PaperAutonomousScreeningDecisionSupportGateReport, ...]:
    return tuple(
        report
        for _, report in sorted(
            enumerate(reports),
            key=lambda item: (_as_utc("source generated_at", item[1].generated_at), item[0]),
        )
    )


def _status_count(
    reports: tuple[PaperAutonomousScreeningDecisionSupportGateReport, ...],
    gate_status: str,
) -> int:
    return sum(1 for report in reports if report.gate_status == gate_status)


def _consecutive_latest_status_count(
    reports: tuple[PaperAutonomousScreeningDecisionSupportGateReport, ...],
    gate_status: str,
) -> int:
    count = 0
    for report in reversed(reports):
        if report.gate_status != gate_status:
            break
        count += 1
    return count


def _age_seconds(generated_at: datetime, source_generated_at: datetime) -> int:
    source_generated_at_utc = _as_utc("source generated_at", source_generated_at)
    age_seconds = int((generated_at - source_generated_at_utc).total_seconds())
    if age_seconds < 0:
        raise ValueError("source generated_at must not be future dated")
    return age_seconds


def _distinct_values(values: object) -> tuple[str, ...]:
    distinct = tuple(sorted(set(values)))
    for value in distinct:
        _require_canonical_string("source config version", value)
    return distinct


def _reason_code_counts(
    reports: tuple[PaperAutonomousScreeningDecisionSupportGateReport, ...],
) -> tuple[PaperAutonomousScreeningDecisionSupportGateDbHistoryHealthReasonCodeCount, ...]:
    counts: dict[str, int] = {}
    for report in reports:
        for reason_code in set(report.reason_codes):
            counts[reason_code] = counts.get(reason_code, 0) + 1
    return tuple(
        PaperAutonomousScreeningDecisionSupportGateDbHistoryHealthReasonCodeCount(
            reason_code,
            report_count,
        )
        for reason_code, report_count in sorted(
            counts.items(),
            key=lambda item: (-item[1], item[0]),
        )
    )


def _validate_health_report(
    report: PaperAutonomousScreeningDecisionSupportGateDbHistoryHealthReport,
) -> None:
    if report.recommended_next_step != NEXT_STEP_BY_STATUS[report.health_status]:
        raise ValueError("recommended_next_step must match health_status")
    if report.source_report_count != (
        report.pass_gate_report_count
        + report.watch_gate_report_count
        + report.blocked_gate_report_count
    ):
        raise ValueError("source_report_count must equal gate status counts")
    if report.source_report_count == 0:
        _validate_empty_health_report(report)
    else:
        _validate_nonempty_health_report(report)
    _validate_health_reason_codes(report)
    for row in report.reason_code_counts:
        if row.report_count > report.source_report_count:
            raise ValueError("reason_code_counts report_count must not exceed source count")


def _validate_empty_health_report(
    report: PaperAutonomousScreeningDecisionSupportGateDbHistoryHealthReport,
) -> None:
    if report.health_status != "blocked":
        raise ValueError("health_status must be blocked without source reports")
    if report.recommended_next_step != (
        "block_paper_autonomous_screening_decision_support_gate_history_review"
    ):
        raise ValueError("recommended_next_step must block without source reports")
    if report.reason_codes != (
        "insufficient_paper_autonomous_screening_decision_support_gate_history_samples",
    ):
        raise ValueError(
            "reason_codes must only contain the insufficient samples reason "
            "without source reports",
        )
    if report.latest_gate_status is not None:
        raise ValueError("latest_gate_status must be absent without source reports")
    if report.latest_gate_generated_at is not None:
        raise ValueError("latest_gate_generated_at must be absent without source reports")
    if report.latest_gate_age_seconds is not None:
        raise ValueError("latest_gate_age_seconds must be absent without source reports")
    if report.consecutive_latest_watch_count != 0:
        raise ValueError(
            "consecutive_latest_watch_count must be zero without source reports",
        )
    if report.consecutive_latest_blocked_count != 0:
        raise ValueError(
            "consecutive_latest_blocked_count must be zero without source reports",
        )
    if report.distinct_gate_config_versions:
        raise ValueError(
            "distinct_gate_config_versions must be empty without source reports",
        )
    if report.distinct_operator_flow_gate_config_versions:
        raise ValueError(
            "distinct_operator_flow_gate_config_versions must be empty without source reports",
        )
    if report.distinct_queue_risk_config_versions:
        raise ValueError(
            "distinct_queue_risk_config_versions must be empty without source reports",
        )
    if report.reason_code_counts:
        raise ValueError("reason_code_counts must be empty without source reports")


def _validate_nonempty_health_report(
    report: PaperAutonomousScreeningDecisionSupportGateDbHistoryHealthReport,
) -> None:
    if report.latest_gate_status is None:
        raise ValueError("latest_gate_status is required with source reports")
    if report.latest_gate_generated_at is None:
        raise ValueError("latest_gate_generated_at is required with source reports")
    if report.latest_gate_age_seconds is None:
        raise ValueError("latest_gate_age_seconds is required with source reports")
    if not report.distinct_gate_config_versions:
        raise ValueError("distinct_gate_config_versions are required with source reports")
    if not report.distinct_operator_flow_gate_config_versions:
        raise ValueError(
            "distinct_operator_flow_gate_config_versions are required with source reports",
        )
    if not report.distinct_queue_risk_config_versions:
        raise ValueError(
            "distinct_queue_risk_config_versions are required with source reports",
        )
    if not report.reason_code_counts:
        raise ValueError("reason_code_counts must summarize source reports")
    if report.latest_gate_status == "watch":
        if report.consecutive_latest_watch_count < 1:
            raise ValueError(
                "consecutive_latest_watch_count is required for latest watch status",
            )
        if report.consecutive_latest_blocked_count != 0:
            raise ValueError(
                "consecutive_latest_blocked_count must be zero for latest watch status",
            )
    elif report.latest_gate_status == "blocked":
        if report.consecutive_latest_blocked_count < 1:
            raise ValueError(
                "consecutive_latest_blocked_count is required for latest blocked status",
            )
        if report.consecutive_latest_watch_count != 0:
            raise ValueError(
                "consecutive_latest_watch_count must be zero for latest blocked status",
            )
    else:
        if report.consecutive_latest_watch_count != 0:
            raise ValueError(
                "consecutive_latest_watch_count must be zero for latest pass status",
            )
        if report.consecutive_latest_blocked_count != 0:
            raise ValueError(
                "consecutive_latest_blocked_count must be zero for latest pass status",
            )
    if report.consecutive_latest_watch_count > report.watch_gate_report_count:
        raise ValueError(
            "consecutive_latest_watch_count must not exceed watch gate count",
        )
    if report.consecutive_latest_blocked_count > report.blocked_gate_report_count:
        raise ValueError(
            "consecutive_latest_blocked_count must not exceed blocked gate count",
        )


def _validate_health_reason_codes(
    report: PaperAutonomousScreeningDecisionSupportGateDbHistoryHealthReport,
) -> None:
    has_pass_reason = PASS_REASON_CODE in report.reason_codes
    has_other_reason = any(
        reason_code in BLOCKED_REASON_CODES or reason_code in WATCH_REASON_CODES
        for reason_code in report.reason_codes
    )
    if has_pass_reason and has_other_reason:
        raise ValueError("reason_codes pass reason must not be mixed with other reasons")
    if report.health_status != _health_status(report.reason_codes):
        raise ValueError("health_status must match reason_codes")
    if report.health_status == "pass" and report.reason_codes != (PASS_REASON_CODE,):
        raise ValueError("reason_codes must contain the pass reason for pass health")
    if report.health_status != "pass" and has_pass_reason:
        raise ValueError("reason_codes must not contain pass reason unless health passes")


def _normalize_source_reason_code_counts(
    value: object,
) -> tuple[PaperAutonomousScreeningDecisionSupportGateReasonCodeCount, ...]:
    if type(value) is not tuple:
        raise ValueError("source reason_code_counts must be a tuple")
    rows = tuple(value)
    if not rows:
        raise ValueError("source reason_code_counts are required")
    previous_key: tuple[int, str] | None = None
    seen: set[str] = set()
    for row in rows:
        if type(row) is not PaperAutonomousScreeningDecisionSupportGateReasonCodeCount:
            raise ValueError("source reason_code_counts must contain exact reason rows")
        _validate_hard_flags("source reason code count", row)
        if row.reason_code in seen:
            raise ValueError("source reason_code_counts must be unique")
        key = (-row.report_count, row.reason_code)
        if previous_key is not None and previous_key > key:
            raise ValueError("source reason_code_counts must be deterministic")
        previous_key = key
        seen.add(row.reason_code)
    return rows


def _normalize_reason_code_counts(
    value: object,
) -> tuple[PaperAutonomousScreeningDecisionSupportGateDbHistoryHealthReasonCodeCount, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    rows = tuple(value)
    previous_key: tuple[int, str] | None = None
    seen: set[str] = set()
    for row in rows:
        if (
            type(row)
            is not PaperAutonomousScreeningDecisionSupportGateDbHistoryHealthReasonCodeCount
        ):
            raise ValueError("reason_code_counts must contain exact reason code counts")
        if row.reason_code in seen:
            raise ValueError("reason_code_counts must be unique")
        key = (-row.report_count, row.reason_code)
        if previous_key is not None and previous_key > key:
            raise ValueError("reason_code_counts must be deterministic")
        previous_key = key
        seen.add(row.reason_code)
    return rows


def _normalize_reason_codes(
    field_name: str,
    value: object,
    *,
    allowed: frozenset[str] | None = None,
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    codes = tuple(value)
    if not codes:
        raise ValueError(f"{field_name} is required")
    previous: str | None = None
    seen: set[str] = set()
    for code in codes:
        _require_canonical_string(field_name, code)
        if allowed is not None and code not in allowed:
            raise ValueError(f"{field_name} contains an unknown reason code")
        if code in seen:
            raise ValueError(f"{field_name} must be unique")
        if previous is not None and previous > code:
            raise ValueError(f"{field_name} must be sorted")
        previous = code
        seen.add(code)
    return codes


def _normalize_string_tuple(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    values = tuple(value)
    previous: str | None = None
    seen: set[str] = set()
    for item in values:
        _require_canonical_string(field_name, item)
        if item in seen:
            raise ValueError(f"{field_name} must be unique")
        if previous is not None and previous > item:
            raise ValueError(f"{field_name} must be sorted")
        previous = item
        seen.add(item)
    return values


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _as_optional_utc(field_name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _require_health_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in HEALTH_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _require_gate_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in GATE_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical string")


def _require_nonnegative_int(field_name: str, value: object) -> None:
    if isinstance(value, bool) or type(value) is not int or value < 0:
        raise ValueError(f"{field_name} must be a nonnegative int")


def _require_optional_nonnegative_int(field_name: str, value: object) -> None:
    if value is None:
        return
    _require_nonnegative_int(field_name, value)


def _require_positive_int(field_name: str, value: object) -> None:
    if isinstance(value, bool) or type(value) is not int or value < 1:
        raise ValueError(f"{field_name} must be a positive int")


def _validate_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{label} must be paper_only")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{label} must be report_only")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{label} must be readonly")
