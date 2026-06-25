"""Pure paper-only health reducer for investment ledger DB report history."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal

from polymarket_alpha_lab.paper_autonomous_investment_ledger import (
    LEDGER_STATUSES,
    PaperAutonomousInvestmentLedgerReasonCodeCount,
    PaperAutonomousInvestmentLedgerReport,
)


DEFAULT_PAPER_AUTONOMOUS_INVESTMENT_LEDGER_DB_HISTORY_HEALTH_CONFIG_VERSION = (
    "paper-autonomous-investment-ledger-db-history-health-v0"
)
HEALTH_STATUSES = ("pass", "watch", "blocked")
NEXT_STEP_BY_STATUS = {
    "pass": "allow_paper_autonomous_investment_ledger_review",
    "watch": "throttle_paper_autonomous_investment_ledger_review",
    "blocked": "block_paper_autonomous_investment_ledger_review",
}
PASS_REASON_CODE = "paper_autonomous_investment_ledger_db_history_health_passed"
BLOCKED_REASON_CODES = frozenset(
    (
        "insufficient_paper_autonomous_investment_ledger_samples",
        "latest_paper_autonomous_investment_ledger_blocked",
        "blocked_paper_autonomous_investment_ledger_count_threshold_exceeded",
        "missing_latest_paper_autonomous_investment_ledger_source_timestamp",
    ),
)
WATCH_REASON_CODES = frozenset(
    (
        "latest_paper_autonomous_investment_ledger_watch",
        "watch_paper_autonomous_investment_ledger_count_threshold_exceeded",
        "stale_paper_autonomous_investment_ledger_source_history",
        "duplicate_latest_paper_autonomous_investment_ledger_source_generated_at_threshold_exceeded",
    ),
)
HEALTH_REASON_CODES = BLOCKED_REASON_CODES | WATCH_REASON_CODES | frozenset(
    (PASS_REASON_CODE,),
)

__all__ = (
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
)


@dataclass(frozen=True)
class PaperAutonomousInvestmentLedgerDbHistoryHealthConfig:
    config_version: str = (
        DEFAULT_PAPER_AUTONOMOUS_INVESTMENT_LEDGER_DB_HISTORY_HEALTH_CONFIG_VERSION
    )
    min_ledger_report_count: int = 3
    max_watch_ledger_report_count: int = 0
    max_blocked_ledger_report_count: int = 0
    max_duplicate_latest_generated_at_count: int = 0
    max_latest_age_seconds: int = 86_400
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not PaperAutonomousInvestmentLedgerDbHistoryHealthConfig:
            raise TypeError(
                "PaperAutonomousInvestmentLedgerDbHistoryHealthConfig "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not PaperAutonomousInvestmentLedgerDbHistoryHealthConfig:
            raise ValueError(
                "config must be exactly "
                "PaperAutonomousInvestmentLedgerDbHistoryHealthConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        _require_positive_int("min_ledger_report_count", self.min_ledger_report_count)
        for field_name in (
            "max_watch_ledger_report_count",
            "max_blocked_ledger_report_count",
            "max_duplicate_latest_generated_at_count",
            "max_latest_age_seconds",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        _validate_hard_flags("config", self)


@dataclass(frozen=True)
class PaperAutonomousInvestmentLedgerDbHistoryHealthReasonCodeCount:
    reason_code: str
    report_count: int
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not PaperAutonomousInvestmentLedgerDbHistoryHealthReasonCodeCount:
            raise TypeError(
                "PaperAutonomousInvestmentLedgerDbHistoryHealthReasonCodeCount "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not PaperAutonomousInvestmentLedgerDbHistoryHealthReasonCodeCount:
            raise ValueError(
                "reason code count must be exactly "
                "PaperAutonomousInvestmentLedgerDbHistoryHealthReasonCodeCount",
            )
        _require_canonical_string("reason_code", self.reason_code)
        _require_positive_int("report_count", self.report_count)
        _validate_hard_flags("reason code count", self)


@dataclass(frozen=True)
class PaperAutonomousInvestmentLedgerDbHistoryHealthReport:
    generated_at: datetime
    config_version: str
    health_status: str
    recommended_next_step: str
    ledger_report_count: int
    pass_ledger_report_count: int
    watch_ledger_report_count: int
    blocked_ledger_report_count: int
    latest_ledger_status: str | None
    latest_source_record_count: int | None
    latest_submitted_count: int | None
    latest_held_count: int | None
    latest_blocked_count: int | None
    latest_total_submitted_notional: Decimal | None
    latest_source_generated_at: datetime | None
    latest_source_age_seconds: int | None
    max_source_age_seconds: int | None
    duplicate_latest_generated_at_count: int
    reason_code_counts: tuple[
        PaperAutonomousInvestmentLedgerDbHistoryHealthReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not PaperAutonomousInvestmentLedgerDbHistoryHealthReport:
            raise TypeError(
                "PaperAutonomousInvestmentLedgerDbHistoryHealthReport "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not PaperAutonomousInvestmentLedgerDbHistoryHealthReport:
            raise ValueError(
                "health report must be exactly "
                "PaperAutonomousInvestmentLedgerDbHistoryHealthReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_health_status("health_status", self.health_status)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        for field_name in (
            "ledger_report_count",
            "pass_ledger_report_count",
            "watch_ledger_report_count",
            "blocked_ledger_report_count",
            "duplicate_latest_generated_at_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        if self.latest_ledger_status is not None:
            _require_ledger_status("latest_ledger_status", self.latest_ledger_status)
        _require_optional_nonnegative_int(
            "latest_source_record_count",
            self.latest_source_record_count,
        )
        _require_optional_nonnegative_int(
            "latest_submitted_count",
            self.latest_submitted_count,
        )
        _require_optional_nonnegative_int(
            "latest_held_count",
            self.latest_held_count,
        )
        _require_optional_nonnegative_int(
            "latest_blocked_count",
            self.latest_blocked_count,
        )
        _require_optional_decimal(
            "latest_total_submitted_notional",
            self.latest_total_submitted_notional,
        )
        object.__setattr__(
            self,
            "latest_source_generated_at",
            _as_optional_utc(
                "latest_source_generated_at",
                self.latest_source_generated_at,
            ),
        )
        _require_optional_nonnegative_int(
            "latest_source_age_seconds",
            self.latest_source_age_seconds,
        )
        _require_optional_nonnegative_int(
            "max_source_age_seconds",
            self.max_source_age_seconds,
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


def build_paper_autonomous_investment_ledger_db_history_health_report(
    ledger_reports: object,
    *,
    config: PaperAutonomousInvestmentLedgerDbHistoryHealthConfig,
    generated_at: datetime,
) -> PaperAutonomousInvestmentLedgerDbHistoryHealthReport:
    if type(config) is not PaperAutonomousInvestmentLedgerDbHistoryHealthConfig:
        raise ValueError(
            "config must be exactly "
            "PaperAutonomousInvestmentLedgerDbHistoryHealthConfig",
        )
    generated_at_utc = _as_utc("generated_at", generated_at)
    _validate_hard_flags("config", config)

    reports = _normalize_ledger_reports(ledger_reports)
    latest_report = _latest_source_report(reports)
    pass_ledger_report_count = _status_count(reports, "pass")
    watch_ledger_report_count = _status_count(reports, "watch")
    blocked_ledger_report_count = _status_count(reports, "blocked")
    missing_latest_timestamp = any(
        report.latest_generated_at is None for report in reports
    )
    duplicate_latest_generated_at_count = _duplicate_latest_generated_at_count(reports)
    latest_source_age_seconds, max_source_age_seconds = _source_age_seconds(
        generated_at_utc,
        reports,
    )
    reason_codes = _health_reason_codes(
        reports=reports,
        latest_report=latest_report,
        watch_ledger_report_count=watch_ledger_report_count,
        blocked_ledger_report_count=blocked_ledger_report_count,
        missing_latest_timestamp=missing_latest_timestamp,
        duplicate_latest_generated_at_count=duplicate_latest_generated_at_count,
        latest_source_age_seconds=latest_source_age_seconds,
        config=config,
    )
    health_status = _health_status(reason_codes)

    return PaperAutonomousInvestmentLedgerDbHistoryHealthReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        health_status=health_status,
        recommended_next_step=NEXT_STEP_BY_STATUS[health_status],
        ledger_report_count=len(reports),
        pass_ledger_report_count=pass_ledger_report_count,
        watch_ledger_report_count=watch_ledger_report_count,
        blocked_ledger_report_count=blocked_ledger_report_count,
        latest_ledger_status=(
            latest_report.ledger_status if latest_report is not None else None
        ),
        latest_source_record_count=(
            latest_report.source_record_count if latest_report is not None else None
        ),
        latest_submitted_count=(
            latest_report.submitted_count if latest_report is not None else None
        ),
        latest_held_count=(
            latest_report.held_count if latest_report is not None else None
        ),
        latest_blocked_count=(
            latest_report.blocked_count if latest_report is not None else None
        ),
        latest_total_submitted_notional=(
            latest_report.total_submitted_notional
            if latest_report is not None
            else None
        ),
        latest_source_generated_at=(
            latest_report.latest_generated_at if latest_report is not None else None
        ),
        latest_source_age_seconds=latest_source_age_seconds,
        max_source_age_seconds=max_source_age_seconds,
        duplicate_latest_generated_at_count=duplicate_latest_generated_at_count,
        reason_code_counts=_reason_code_counts(reports),
        reason_codes=reason_codes,
    )


def _normalize_ledger_reports(
    value: object,
) -> tuple[PaperAutonomousInvestmentLedgerReport, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("ledger_reports must be a list or tuple")
    reports = tuple(value)
    for report in reports:
        if type(report) is not PaperAutonomousInvestmentLedgerReport:
            raise ValueError(
                "ledger_reports must contain "
                "PaperAutonomousInvestmentLedgerReport values",
            )
        _validate_ledger_report(report)
    return reports


def _validate_ledger_report(report: PaperAutonomousInvestmentLedgerReport) -> None:
    _validate_hard_flags("ledger report", report)
    _as_utc("source generated_at", report.generated_at)
    _require_canonical_string("source config_version", report.config_version)
    _require_ledger_status("source ledger_status", report.ledger_status)
    _require_canonical_string(
        "source recommended_next_step",
        report.recommended_next_step,
    )
    for field_name in (
        "source_record_count",
        "submitted_count",
        "held_count",
        "blocked_count",
        "held_zero_notional_count",
        "blocked_zero_notional_count",
    ):
        _require_nonnegative_int(f"source {field_name}", getattr(report, field_name))
    _require_optional_nonnegative_int(
        "source latest_age_seconds",
        report.latest_age_seconds,
    )
    _as_optional_utc("source latest_generated_at", report.latest_generated_at)
    _require_optional_decimal(
        "source total_submitted_notional",
        report.total_submitted_notional,
    )
    _normalize_source_reason_code_counts(report.reason_code_counts)
    _normalize_reason_codes("source reason_codes", report.reason_codes)


def _health_reason_codes(
    *,
    reports: tuple[PaperAutonomousInvestmentLedgerReport, ...],
    latest_report: PaperAutonomousInvestmentLedgerReport | None,
    watch_ledger_report_count: int,
    blocked_ledger_report_count: int,
    missing_latest_timestamp: bool,
    duplicate_latest_generated_at_count: int,
    latest_source_age_seconds: int | None,
    config: PaperAutonomousInvestmentLedgerDbHistoryHealthConfig,
) -> tuple[str, ...]:
    blocked_reasons: list[str] = []
    watch_reasons: list[str] = []

    if len(reports) < config.min_ledger_report_count:
        blocked_reasons.append(
            "insufficient_paper_autonomous_investment_ledger_samples",
        )
    if latest_report is not None and latest_report.ledger_status == "blocked":
        blocked_reasons.append("latest_paper_autonomous_investment_ledger_blocked")
    if blocked_ledger_report_count > config.max_blocked_ledger_report_count:
        blocked_reasons.append(
            "blocked_paper_autonomous_investment_ledger_count_threshold_exceeded",
        )
    if missing_latest_timestamp:
        blocked_reasons.append(
            "missing_latest_paper_autonomous_investment_ledger_source_timestamp",
        )

    if latest_report is not None and latest_report.ledger_status == "watch":
        watch_reasons.append("latest_paper_autonomous_investment_ledger_watch")
    if watch_ledger_report_count > config.max_watch_ledger_report_count:
        watch_reasons.append(
            "watch_paper_autonomous_investment_ledger_count_threshold_exceeded",
        )
    if (
        latest_source_age_seconds is not None
        and latest_source_age_seconds > config.max_latest_age_seconds
    ):
        watch_reasons.append(
            "stale_paper_autonomous_investment_ledger_source_history",
        )
    if (
        duplicate_latest_generated_at_count
        > config.max_duplicate_latest_generated_at_count
    ):
        watch_reasons.append(
            "duplicate_latest_paper_autonomous_investment_ledger_source_generated_at_threshold_exceeded",
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


def _latest_source_report(
    reports: tuple[PaperAutonomousInvestmentLedgerReport, ...],
) -> PaperAutonomousInvestmentLedgerReport | None:
    if not reports:
        return None
    return max(
        enumerate(reports),
        key=lambda item: (*_latest_source_sort_key(item[1]), item[0]),
    )[1]


def _latest_source_sort_key(
    report: PaperAutonomousInvestmentLedgerReport,
) -> tuple[int, datetime, datetime]:
    latest_generated_at = _as_optional_utc(
        "source latest_generated_at",
        report.latest_generated_at,
    )
    report_generated_at = _as_utc("source generated_at", report.generated_at)
    if latest_generated_at is None:
        return (0, report_generated_at, report_generated_at)
    return (1, latest_generated_at, report_generated_at)


def _source_age_seconds(
    generated_at: datetime,
    reports: tuple[PaperAutonomousInvestmentLedgerReport, ...],
) -> tuple[int | None, int | None]:
    if not reports:
        return (None, None)
    latest_generated_values = tuple(
        _as_optional_utc("source latest_generated_at", report.latest_generated_at)
        for report in reports
    )
    if any(value is None for value in latest_generated_values):
        return (None, None)
    ages = tuple(
        _age_seconds(generated_at, latest_generated_at)
        for latest_generated_at in latest_generated_values
        if latest_generated_at is not None
    )
    return (min(ages), max(ages))


def _age_seconds(generated_at: datetime, source_generated_at: datetime) -> int:
    source_generated_at_utc = _as_utc("source latest_generated_at", source_generated_at)
    age_seconds = int((generated_at - source_generated_at_utc).total_seconds())
    if age_seconds < 0:
        raise ValueError("source latest_generated_at must not be future dated")
    return age_seconds


def _duplicate_latest_generated_at_count(
    reports: tuple[PaperAutonomousInvestmentLedgerReport, ...],
) -> int:
    counts: dict[datetime, int] = {}
    for report in reports:
        latest_generated_at = _as_optional_utc(
            "source latest_generated_at",
            report.latest_generated_at,
        )
        if latest_generated_at is None:
            continue
        counts[latest_generated_at] = counts.get(latest_generated_at, 0) + 1
    return sum(count - 1 for count in counts.values() if count > 1)


def _reason_code_counts(
    reports: tuple[PaperAutonomousInvestmentLedgerReport, ...],
) -> tuple[PaperAutonomousInvestmentLedgerDbHistoryHealthReasonCodeCount, ...]:
    counts: dict[str, int] = {}
    for report in reports:
        for reason_code in set(report.reason_codes):
            counts[reason_code] = counts.get(reason_code, 0) + 1
    return tuple(
        PaperAutonomousInvestmentLedgerDbHistoryHealthReasonCodeCount(
            reason_code,
            report_count,
        )
        for reason_code, report_count in sorted(
            counts.items(),
            key=lambda item: (-item[1], item[0]),
        )
    )


def _status_count(
    reports: tuple[PaperAutonomousInvestmentLedgerReport, ...],
    ledger_status: str,
) -> int:
    return sum(1 for report in reports if report.ledger_status == ledger_status)


def _validate_health_report(
    report: PaperAutonomousInvestmentLedgerDbHistoryHealthReport,
) -> None:
    if report.recommended_next_step != NEXT_STEP_BY_STATUS[report.health_status]:
        raise ValueError("recommended_next_step must match health_status")
    if report.ledger_report_count != (
        report.pass_ledger_report_count
        + report.watch_ledger_report_count
        + report.blocked_ledger_report_count
    ):
        raise ValueError("ledger_report_count must equal status counts")
    if report.ledger_report_count == 0:
        _validate_empty_health_report(report)
    else:
        _validate_nonempty_health_report(report)
    _validate_health_reason_codes(report)
    for row in report.reason_code_counts:
        if row.report_count > report.ledger_report_count:
            raise ValueError("reason_code_counts report_count must not exceed source count")


def _validate_empty_health_report(
    report: PaperAutonomousInvestmentLedgerDbHistoryHealthReport,
) -> None:
    if report.health_status != "blocked":
        raise ValueError("health_status must be blocked without ledger reports")
    if report.recommended_next_step != "block_paper_autonomous_investment_ledger_review":
        raise ValueError("recommended_next_step must block without ledger reports")
    if report.reason_codes != (
        "insufficient_paper_autonomous_investment_ledger_samples",
    ):
        raise ValueError(
            "reason_codes must only contain the insufficient samples reason "
            "without ledger reports",
        )
    if report.latest_ledger_status is not None:
        raise ValueError("latest_ledger_status must be absent without ledger reports")
    if report.latest_source_record_count is not None:
        raise ValueError(
            "latest_source_record_count must be absent without ledger reports",
        )
    if report.latest_submitted_count is not None:
        raise ValueError("latest_submitted_count must be absent without ledger reports")
    if report.latest_held_count is not None:
        raise ValueError("latest_held_count must be absent without ledger reports")
    if report.latest_blocked_count is not None:
        raise ValueError("latest_blocked_count must be absent without ledger reports")
    if report.latest_total_submitted_notional is not None:
        raise ValueError(
            "latest_total_submitted_notional must be absent without ledger reports",
        )
    if report.latest_source_generated_at is not None:
        raise ValueError(
            "latest_source_generated_at must be absent without ledger reports",
        )
    if report.latest_source_age_seconds is not None:
        raise ValueError(
            "latest_source_age_seconds must be absent without ledger reports",
        )
    if report.max_source_age_seconds is not None:
        raise ValueError("max_source_age_seconds must be absent without ledger reports")
    if report.duplicate_latest_generated_at_count != 0:
        raise ValueError(
            "duplicate_latest_generated_at_count must be zero without ledger reports",
        )
    if report.reason_code_counts:
        raise ValueError("reason_code_counts must be empty without ledger reports")


def _validate_nonempty_health_report(
    report: PaperAutonomousInvestmentLedgerDbHistoryHealthReport,
) -> None:
    if report.latest_ledger_status is None:
        raise ValueError("latest_ledger_status is required with ledger reports")
    if report.latest_source_record_count is None:
        raise ValueError("latest_source_record_count is required with ledger reports")
    if report.latest_submitted_count is None:
        raise ValueError("latest_submitted_count is required with ledger reports")
    if report.latest_held_count is None:
        raise ValueError("latest_held_count is required with ledger reports")
    if report.latest_blocked_count is None:
        raise ValueError("latest_blocked_count is required with ledger reports")
    if report.latest_source_record_count != (
        report.latest_submitted_count
        + report.latest_held_count
        + report.latest_blocked_count
    ):
        raise ValueError("latest_source_record_count must equal latest status counts")
    if report.latest_total_submitted_notional is None:
        raise ValueError(
            "latest_total_submitted_notional is required with ledger reports",
        )
    missing_latest_reason = (
        "missing_latest_paper_autonomous_investment_ledger_source_timestamp"
        in report.reason_codes
    )
    if missing_latest_reason:
        if report.latest_source_age_seconds is not None:
            raise ValueError("latest_source_age_seconds must be absent without timestamp")
        if report.max_source_age_seconds is not None:
            raise ValueError("max_source_age_seconds must be absent without timestamp")
    else:
        if report.latest_source_generated_at is None:
            raise ValueError(
                "latest_source_generated_at is required with ledger reports",
            )
        if report.latest_source_age_seconds is None:
            raise ValueError("latest_source_age_seconds is required with ledger reports")
        if report.max_source_age_seconds is None:
            raise ValueError("max_source_age_seconds is required with ledger reports")
        if report.latest_source_age_seconds > report.max_source_age_seconds:
            raise ValueError(
                "latest_source_age_seconds must not exceed max_source_age_seconds",
            )
    if report.duplicate_latest_generated_at_count >= max(report.ledger_report_count, 1):
        raise ValueError(
            "duplicate_latest_generated_at_count must be below source count",
        )
    if not report.reason_code_counts:
        raise ValueError("reason_code_counts must summarize ledger reports")


def _validate_health_reason_codes(
    report: PaperAutonomousInvestmentLedgerDbHistoryHealthReport,
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
) -> tuple[PaperAutonomousInvestmentLedgerReasonCodeCount, ...]:
    if type(value) is not tuple:
        raise ValueError("source reason_code_counts must be a tuple")
    rows = tuple(value)
    previous_key: tuple[int, str] | None = None
    seen: set[str] = set()
    for row in rows:
        if type(row) is not PaperAutonomousInvestmentLedgerReasonCodeCount:
            raise ValueError("source reason_code_counts must contain exact reason rows")
        _validate_hard_flags("source reason code count", row)
        if row.reason_code in seen:
            raise ValueError("source reason_code_counts must be unique")
        key = (-row.source_record_count, row.reason_code)
        if previous_key is not None and previous_key > key:
            raise ValueError("source reason_code_counts must be deterministic")
        previous_key = key
        seen.add(row.reason_code)
    return rows


def _normalize_reason_code_counts(
    value: object,
) -> tuple[PaperAutonomousInvestmentLedgerDbHistoryHealthReasonCodeCount, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    rows = tuple(value)
    previous_key: tuple[int, str] | None = None
    seen: set[str] = set()
    for row in rows:
        if type(row) is not PaperAutonomousInvestmentLedgerDbHistoryHealthReasonCodeCount:
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


def _require_ledger_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in LEDGER_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _require_optional_decimal(field_name: str, value: object) -> None:
    if value is None:
        return
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")


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
