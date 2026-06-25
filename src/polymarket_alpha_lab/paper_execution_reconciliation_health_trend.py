"""Pure trend reducer over paper execution reconciliation health gate reports."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from polymarket_alpha_lab.paper_execution_reconciliation_health_gate import (
    PaperExecutionReconciliationHealthGateReport,
)


DEFAULT_PAPER_EXECUTION_RECONCILIATION_HEALTH_TREND_CONFIG_VERSION = (
    "paper-execution-reconciliation-health-trend-v0"
)
HEALTH_STATUSES = ("pass", "watch", "blocked")
TREND_NEXT_STEP_BY_STATUS = {
    "pass": "allow_paper_execution_reconciliation_health_trend",
    "watch": "watch_paper_execution_reconciliation_health_trend",
    "blocked": "block_paper_execution_reconciliation_health_trend",
}
EMPTY_INPUT_REASON_CODE = "missing_paper_execution_reconciliation_health_gate_reports"
LATEST_BLOCKED_REASON_CODE = "latest_paper_execution_reconciliation_health_gate_blocked"
LATEST_WATCH_REASON_CODE = "latest_paper_execution_reconciliation_health_gate_watch"
STALE_GATE_REASON_CODE = "stale_paper_execution_reconciliation_evidence"
MISSING_GATE_REASON_CODE = "missing_paper_execution_reconciliation_evidence"
DISCREPANCY_GATE_REASON_CODE = "paper_execution_reconciliation_discrepancies_present"

__all__ = (
    "DEFAULT_PAPER_EXECUTION_RECONCILIATION_HEALTH_TREND_CONFIG_VERSION",
    "PaperExecutionReconciliationHealthTrendConfig",
    "PaperExecutionReconciliationHealthTrendReasonCodeCount",
    "PaperExecutionReconciliationHealthTrendReport",
    "build_paper_execution_reconciliation_health_trend_report",
)


@dataclass(frozen=True)
class PaperExecutionReconciliationHealthTrendConfig:
    config_version: str = (
        DEFAULT_PAPER_EXECUTION_RECONCILIATION_HEALTH_TREND_CONFIG_VERSION
    )
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "PaperExecutionReconciliationHealthTrendConfig does not support subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not PaperExecutionReconciliationHealthTrendConfig:
            raise ValueError(
                "config must be exactly PaperExecutionReconciliationHealthTrendConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        _validate_hard_flags("config", self)


@dataclass(frozen=True)
class PaperExecutionReconciliationHealthTrendReasonCodeCount:
    reason_code: str
    report_count: int
    latest_count: int
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "PaperExecutionReconciliationHealthTrendReasonCodeCount "
            "does not support subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not PaperExecutionReconciliationHealthTrendReasonCodeCount:
            raise ValueError(
                "reason code count must be exactly "
                "PaperExecutionReconciliationHealthTrendReasonCodeCount",
            )
        _require_canonical_string("reason_code", self.reason_code)
        _require_positive_int("report_count", self.report_count)
        _require_nonnegative_int("latest_count", self.latest_count)
        if self.latest_count > self.report_count:
            raise ValueError("latest_count must not exceed report_count")
        _validate_hard_flags("reason code count", self)


@dataclass(frozen=True)
class PaperExecutionReconciliationHealthTrendReport:
    generated_at: datetime
    config_version: str
    source_health_gate_report_count: int
    first_generated_at: datetime | None
    latest_generated_at: datetime | None
    latest_gate_status: str | None
    trend_status: str
    recommended_next_step: str
    gate_status_counts: tuple[tuple[str, int], ...]
    pass_gate_report_count: int
    watch_gate_report_count: int
    blocked_gate_report_count: int
    consecutive_latest_watch_count: int
    consecutive_latest_blocked_count: int
    latest_source_age_seconds: int | None
    stale_reason_report_count: int
    missing_reason_report_count: int
    discrepancy_reason_report_count: int
    reason_code_counts: tuple[
        PaperExecutionReconciliationHealthTrendReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "PaperExecutionReconciliationHealthTrendReport does not support subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not PaperExecutionReconciliationHealthTrendReport:
            raise ValueError(
                "trend report must be exactly "
                "PaperExecutionReconciliationHealthTrendReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "first_generated_at",
            _as_optional_utc("first_generated_at", self.first_generated_at),
        )
        object.__setattr__(
            self,
            "latest_generated_at",
            _as_optional_utc("latest_generated_at", self.latest_generated_at),
        )
        _require_canonical_string("config_version", self.config_version)
        _require_nonnegative_int(
            "source_health_gate_report_count",
            self.source_health_gate_report_count,
        )
        if self.latest_gate_status is not None:
            _require_health_status("latest_gate_status", self.latest_gate_status)
        _require_health_status("trend_status", self.trend_status)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        object.__setattr__(
            self,
            "gate_status_counts",
            _normalize_status_counts(self.gate_status_counts),
        )
        for field_name in (
            "pass_gate_report_count",
            "watch_gate_report_count",
            "blocked_gate_report_count",
            "consecutive_latest_watch_count",
            "consecutive_latest_blocked_count",
            "stale_reason_report_count",
            "missing_reason_report_count",
            "discrepancy_reason_report_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        _require_optional_nonnegative_int(
            "latest_source_age_seconds",
            self.latest_source_age_seconds,
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_trend_report(self)
        _validate_hard_flags("trend report", self)


def build_paper_execution_reconciliation_health_trend_report(
    health_gate_reports: object,
    *,
    config: PaperExecutionReconciliationHealthTrendConfig,
    generated_at: datetime,
) -> PaperExecutionReconciliationHealthTrendReport:
    if type(config) is not PaperExecutionReconciliationHealthTrendConfig:
        raise ValueError(
            "config must be exactly PaperExecutionReconciliationHealthTrendConfig",
        )
    _validate_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    reports = _normalize_health_gate_reports(health_gate_reports)
    ordered_reports = _ordered_reports(reports)
    latest = ordered_reports[-1] if ordered_reports else None
    status_counts = _status_counts(ordered_reports)
    reason_codes = _trend_reason_codes(latest)
    reason_count_rows = _reason_code_counts(ordered_reports, latest)
    status_count_map = dict(status_counts)

    return PaperExecutionReconciliationHealthTrendReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        source_health_gate_report_count=len(ordered_reports),
        first_generated_at=ordered_reports[0].generated_at if ordered_reports else None,
        latest_generated_at=latest.generated_at if latest is not None else None,
        latest_gate_status=latest.gate_status if latest is not None else None,
        trend_status=_trend_status(latest),
        recommended_next_step=TREND_NEXT_STEP_BY_STATUS[_trend_status(latest)],
        gate_status_counts=status_counts,
        pass_gate_report_count=status_count_map["pass"],
        watch_gate_report_count=status_count_map["watch"],
        blocked_gate_report_count=status_count_map["blocked"],
        consecutive_latest_watch_count=_latest_status_streak(
            ordered_reports,
            "watch",
        ),
        consecutive_latest_blocked_count=_latest_status_streak(
            ordered_reports,
            "blocked",
        ),
        latest_source_age_seconds=(
            latest.latest_source_age_seconds if latest is not None else None
        ),
        stale_reason_report_count=_reason_report_count(
            ordered_reports,
            STALE_GATE_REASON_CODE,
        ),
        missing_reason_report_count=_reason_report_count(
            ordered_reports,
            MISSING_GATE_REASON_CODE,
        ),
        discrepancy_reason_report_count=_reason_report_count(
            ordered_reports,
            DISCREPANCY_GATE_REASON_CODE,
        ),
        reason_code_counts=reason_count_rows,
        reason_codes=reason_codes,
    )


def _normalize_health_gate_reports(
    value: object,
) -> tuple[PaperExecutionReconciliationHealthGateReport, ...]:
    if type(value) is not tuple:
        raise ValueError("health_gate_reports must be a tuple")
    reports = tuple(value)
    for index, report in enumerate(reports):
        if type(report) is not PaperExecutionReconciliationHealthGateReport:
            raise ValueError(
                "health_gate_reports must contain "
                "PaperExecutionReconciliationHealthGateReport values",
            )
        _validate_hard_flags(f"source health_gate_reports.{index}", report)
    return reports


def _status_counts(
    reports: tuple[PaperExecutionReconciliationHealthGateReport, ...],
) -> tuple[tuple[str, int], ...]:
    counts = {status: 0 for status in HEALTH_STATUSES}
    for report in reports:
        counts[report.gate_status] += 1
    return tuple((status, counts[status]) for status in HEALTH_STATUSES)


def _latest_status_streak(
    reports: tuple[PaperExecutionReconciliationHealthGateReport, ...],
    status: str,
) -> int:
    count = 0
    for report in reversed(reports):
        if report.gate_status != status:
            break
        count += 1
    return count


def _trend_status(
    latest: PaperExecutionReconciliationHealthGateReport | None,
) -> str:
    if latest is None:
        return "blocked"
    return latest.gate_status


def _trend_reason_codes(
    latest: PaperExecutionReconciliationHealthGateReport | None,
) -> tuple[str, ...]:
    if latest is None:
        return (EMPTY_INPUT_REASON_CODE,)
    if latest.gate_status == "blocked":
        return (LATEST_BLOCKED_REASON_CODE,)
    if latest.gate_status == "watch":
        return (LATEST_WATCH_REASON_CODE,)
    return ()


def _reason_report_count(
    reports: tuple[PaperExecutionReconciliationHealthGateReport, ...],
    reason_code: str,
) -> int:
    return sum(1 for report in reports if reason_code in report.reason_codes)


def _reason_code_counts(
    reports: tuple[PaperExecutionReconciliationHealthGateReport, ...],
    latest: PaperExecutionReconciliationHealthGateReport | None,
) -> tuple[PaperExecutionReconciliationHealthTrendReasonCodeCount, ...]:
    counts: dict[str, int] = {}
    for report in reports:
        for reason_code in set(report.reason_codes):
            counts[reason_code] = counts.get(reason_code, 0) + 1
    latest_counts = {}
    if latest is not None:
        for reason_code in latest.reason_codes:
            latest_counts[reason_code] = latest_counts.get(reason_code, 0) + 1
    return tuple(
        PaperExecutionReconciliationHealthTrendReasonCodeCount(
            reason_code=reason_code,
            report_count=report_count,
            latest_count=latest_counts.get(reason_code, 0),
        )
        for _, reason_code, report_count in sorted(
            (-report_count, reason_code, report_count)
            for reason_code, report_count in counts.items()
        )
    )


def _ordered_reports(
    reports: tuple[PaperExecutionReconciliationHealthGateReport, ...],
) -> tuple[PaperExecutionReconciliationHealthGateReport, ...]:
    return tuple(
        report
        for _, _, report in sorted(
            (report.generated_at, input_position, report)
            for input_position, report in enumerate(reports)
        )
    )


def _validate_trend_report(report: PaperExecutionReconciliationHealthTrendReport) -> None:
    if report.recommended_next_step != TREND_NEXT_STEP_BY_STATUS[report.trend_status]:
        raise ValueError("recommended_next_step must match trend_status")
    status_count_map = dict(report.gate_status_counts)
    if report.source_health_gate_report_count != sum(status_count_map.values()):
        raise ValueError("gate_status_counts must match source_health_gate_report_count")
    if report.pass_gate_report_count != status_count_map["pass"]:
        raise ValueError("pass_gate_report_count must match gate_status_counts")
    if report.watch_gate_report_count != status_count_map["watch"]:
        raise ValueError("watch_gate_report_count must match gate_status_counts")
    if report.blocked_gate_report_count != status_count_map["blocked"]:
        raise ValueError("blocked_gate_report_count must match gate_status_counts")
    if report.source_health_gate_report_count == 0:
        _validate_empty_trend_report(report)
    else:
        _validate_nonempty_trend_report(report)


def _validate_empty_trend_report(
    report: PaperExecutionReconciliationHealthTrendReport,
) -> None:
    if report.first_generated_at is not None:
        raise ValueError("first_generated_at must be absent without source reports")
    if report.latest_generated_at is not None:
        raise ValueError("latest_generated_at must be absent without source reports")
    if report.latest_gate_status is not None:
        raise ValueError("latest_gate_status must be absent without source reports")
    if report.trend_status != "blocked":
        raise ValueError("empty trend reports must be blocked")
    if report.latest_source_age_seconds is not None:
        raise ValueError("latest_source_age_seconds must be absent without source reports")
    if report.gate_status_counts != (("pass", 0), ("watch", 0), ("blocked", 0)):
        raise ValueError("gate_status_counts must be zeroed without source reports")
    if report.consecutive_latest_watch_count != 0:
        raise ValueError(
            "consecutive_latest_watch_count must be zero without source reports",
        )
    if report.consecutive_latest_blocked_count != 0:
        raise ValueError(
            "consecutive_latest_blocked_count must be zero without source reports",
        )
    if report.stale_reason_report_count != 0:
        raise ValueError("stale_reason_report_count must be zero without source reports")
    if report.missing_reason_report_count != 0:
        raise ValueError("missing_reason_report_count must be zero without source reports")
    if report.discrepancy_reason_report_count != 0:
        raise ValueError(
            "discrepancy_reason_report_count must be zero without source reports",
        )
    if report.reason_code_counts:
        raise ValueError("reason_code_counts must be empty without source reports")
    if report.reason_codes != (EMPTY_INPUT_REASON_CODE,):
        raise ValueError("empty trend reports require an explicit missing reason")


def _validate_nonempty_trend_report(
    report: PaperExecutionReconciliationHealthTrendReport,
) -> None:
    if report.first_generated_at is None:
        raise ValueError("first_generated_at is required with source reports")
    if report.latest_generated_at is None:
        raise ValueError("latest_generated_at is required with source reports")
    if report.latest_gate_status is None:
        raise ValueError("latest_gate_status is required with source reports")
    if report.latest_gate_status != report.trend_status:
        raise ValueError("trend_status must match latest_gate_status")
    expected_reason_codes = _trend_reason_codes_from_status(report.latest_gate_status)
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match latest_gate_status")
    if report.latest_gate_status == "watch":
        if report.consecutive_latest_watch_count < 1:
            raise ValueError("watch trend reports require a latest watch streak")
        if report.consecutive_latest_blocked_count != 0:
            raise ValueError("watch trend reports must not have a latest blocked streak")
    if report.latest_gate_status == "blocked":
        if report.consecutive_latest_blocked_count < 1:
            raise ValueError("blocked trend reports require a latest blocked streak")
        if report.consecutive_latest_watch_count != 0:
            raise ValueError("blocked trend reports must not have a latest watch streak")
    if report.latest_gate_status == "pass":
        if report.consecutive_latest_watch_count != 0:
            raise ValueError("pass trend reports must not have a latest watch streak")
        if report.consecutive_latest_blocked_count != 0:
            raise ValueError("pass trend reports must not have a latest blocked streak")


def _trend_reason_codes_from_status(status: str) -> tuple[str, ...]:
    if status == "blocked":
        return (LATEST_BLOCKED_REASON_CODE,)
    if status == "watch":
        return (LATEST_WATCH_REASON_CODE,)
    return ()


def _normalize_status_counts(value: object) -> tuple[tuple[str, int], ...]:
    if type(value) is not tuple:
        raise ValueError("gate_status_counts must be a tuple")
    rows: list[tuple[str, int]] = []
    seen: set[str] = set()
    for item in value:
        if type(item) is not tuple or len(item) != 2:
            raise ValueError("gate_status_counts must contain (status, count) tuples")
        status, count = item
        _require_health_status("gate_status_counts status", status)
        _require_nonnegative_int("gate_status_counts count", count)
        if status in seen:
            raise ValueError("gate_status_counts must be unique")
        seen.add(status)
        rows.append((status, count))
    if tuple(status for status, _ in rows) != HEALTH_STATUSES:
        raise ValueError("gate_status_counts must follow pass/watch/blocked order")
    return tuple(rows)


def _normalize_reason_code_counts(
    value: object,
) -> tuple[PaperExecutionReconciliationHealthTrendReasonCodeCount, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    rows = tuple(value)
    seen: set[str] = set()
    previous_order: tuple[int, str] | None = None
    for row in rows:
        if type(row) is not PaperExecutionReconciliationHealthTrendReasonCodeCount:
            raise ValueError("reason_code_counts must contain exact reason rows")
        if row.reason_code in seen:
            raise ValueError("reason_code_counts must be unique")
        order = (-row.report_count, row.reason_code)
        if previous_order is not None and previous_order > order:
            raise ValueError("reason_code_counts must be deterministic")
        previous_order = order
        seen.add(row.reason_code)
    return rows


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    reason_codes = tuple(value)
    seen: set[str] = set()
    previous_reason_code: str | None = None
    for reason_code in reason_codes:
        _require_canonical_string(field_name, reason_code)
        if reason_code in seen:
            raise ValueError(f"{field_name} must be unique")
        if previous_reason_code is not None and previous_reason_code > reason_code:
            raise ValueError(f"{field_name} must be sorted")
        previous_reason_code = reason_code
        seen.add(reason_code)
    return reason_codes


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


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_nonnegative_int(field_name: str, value: object) -> None:
    if isinstance(value, bool) or type(value) is not int or value < 0:
        raise ValueError(f"{field_name} must be a nonnegative int")


def _require_positive_int(field_name: str, value: object) -> None:
    if isinstance(value, bool) or type(value) is not int or value < 1:
        raise ValueError(f"{field_name} must be a positive int")


def _require_optional_nonnegative_int(field_name: str, value: object) -> None:
    if value is None:
        return
    _require_nonnegative_int(field_name, value)


def _validate_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{label} must be paper_only")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{label} must be report_only")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{label} must be readonly")
