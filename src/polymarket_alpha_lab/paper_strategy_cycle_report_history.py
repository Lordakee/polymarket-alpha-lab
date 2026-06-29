"""Pure history reducer for paper strategy cycle reports."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_EVEN
from typing import Any

from polymarket_alpha_lab.strategy_cycle import PaperStrategyCycleReport


__all__ = (
    "DEFAULT_PAPER_STRATEGY_CYCLE_REPORT_HISTORY_CONFIG_VERSION",
    "PaperStrategyCycleReportHistoryBlockedReasonRow",
    "PaperStrategyCycleReportHistoryConfig",
    "PaperStrategyCycleReportHistoryReport",
    "build_paper_strategy_cycle_report_history_report",
)


DEFAULT_PAPER_STRATEGY_CYCLE_REPORT_HISTORY_CONFIG_VERSION = (
    "paper-strategy-cycle-report-history-v0"
)
RATIO_QUANTUM = Decimal("0.000001")
HISTORY_STATUSES = ("pass", "watch", "blocked")
REASON_CODES = (
    "insufficient_strategy_cycle_report_history",
    "latest_snapshot_ready_share_below_minimum",
    "blocked_market_share_above_limit",
)


@dataclass(frozen=True)
class PaperStrategyCycleReportHistoryConfig:
    config_version: str = DEFAULT_PAPER_STRATEGY_CYCLE_REPORT_HISTORY_CONFIG_VERSION
    min_report_count: int = 3
    min_latest_snapshot_ready_share: Decimal = Decimal("0.100000")
    max_blocked_market_share: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        _require_positive_int("min_report_count", self.min_report_count)
        _require_probability_decimal(
            "min_latest_snapshot_ready_share",
            self.min_latest_snapshot_ready_share,
        )
        _require_probability_decimal(
            "max_blocked_market_share",
            self.max_blocked_market_share,
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class PaperStrategyCycleReportHistoryBlockedReasonRow:
    reason_code: str
    blocked_market_count: int
    report_count: int

    def __post_init__(self) -> None:
        _require_canonical_string("reason_code", self.reason_code)
        _require_positive_int("blocked_market_count", self.blocked_market_count)
        _require_positive_int("report_count", self.report_count)


@dataclass(frozen=True)
class PaperStrategyCycleReportHistoryReport:
    generated_at: datetime
    config_version: str
    history_status: str
    report_count: int
    first_report_generated_at: datetime
    latest_report_generated_at: datetime
    total_scan_market_count: int
    total_considered_count: int
    total_snapshot_ready_count: int
    total_cost_aware_report_count: int
    total_blocked_market_count: int
    latest_scan_market_count: int
    latest_considered_count: int
    latest_snapshot_ready_count: int
    latest_cost_aware_report_count: int
    latest_blocked_market_count: int
    overall_snapshot_ready_share: Decimal
    latest_snapshot_ready_share: Decimal
    blocked_market_share: Decimal
    blocked_reason_rows: tuple[PaperStrategyCycleReportHistoryBlockedReasonRow, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "first_report_generated_at",
            _as_utc("first_report_generated_at", self.first_report_generated_at),
        )
        object.__setattr__(
            self,
            "latest_report_generated_at",
            _as_utc("latest_report_generated_at", self.latest_report_generated_at),
        )
        _require_canonical_string("config_version", self.config_version)
        if self.history_status not in HISTORY_STATUSES:
            raise ValueError("history_status must be a known status")
        for field_name in (
            "report_count",
            "total_scan_market_count",
            "total_considered_count",
            "total_snapshot_ready_count",
            "total_cost_aware_report_count",
            "total_blocked_market_count",
            "latest_scan_market_count",
            "latest_considered_count",
            "latest_snapshot_ready_count",
            "latest_cost_aware_report_count",
            "latest_blocked_market_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        if self.report_count <= 0:
            raise ValueError("report_count must be positive")
        for field_name in (
            "overall_snapshot_ready_share",
            "latest_snapshot_ready_share",
            "blocked_market_share",
        ):
            _require_probability_decimal(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "blocked_reason_rows",
            _normalize_blocked_reason_rows(self.blocked_reason_rows),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags("report", self)
        _validate_report_consistency(self)


def build_paper_strategy_cycle_report_history_report(
    reports: list[PaperStrategyCycleReport] | tuple[PaperStrategyCycleReport, ...],
    *,
    config: PaperStrategyCycleReportHistoryConfig,
    generated_at: datetime,
) -> PaperStrategyCycleReportHistoryReport:
    if type(config) is not PaperStrategyCycleReportHistoryConfig:
        raise ValueError("config must be a PaperStrategyCycleReportHistoryConfig")
    if type(generated_at) is not datetime:
        raise ValueError("generated_at must be a datetime")
    _require_hard_flags("config", config)
    source_reports = _normalize_reports(reports)
    latest = source_reports[-1]

    total_scan_market_count = sum(report.scan_market_count for report in source_reports)
    total_considered_count = sum(report.considered_count for report in source_reports)
    total_snapshot_ready_count = sum(
        report.snapshot_ready_count for report in source_reports
    )
    total_cost_aware_report_count = sum(
        report.cost_aware_report_count for report in source_reports
    )
    total_blocked_market_count = sum(
        _blocked_market_count(report) for report in source_reports
    )
    latest_blocked_market_count = _blocked_market_count(latest)
    overall_snapshot_ready_share = _ratio(
        total_snapshot_ready_count,
        total_considered_count,
    )
    latest_snapshot_ready_share = _ratio(
        latest.snapshot_ready_count,
        latest.considered_count,
    )
    blocked_market_share = _ratio(
        total_blocked_market_count,
        total_considered_count,
    )
    history_status, reason_codes = _status_and_reasons(
        len(source_reports),
        latest_snapshot_ready_share,
        blocked_market_share,
        config=config,
    )

    return PaperStrategyCycleReportHistoryReport(
        generated_at=generated_at,
        config_version=config.config_version,
        history_status=history_status,
        report_count=len(source_reports),
        first_report_generated_at=source_reports[0].generated_at,
        latest_report_generated_at=latest.generated_at,
        total_scan_market_count=total_scan_market_count,
        total_considered_count=total_considered_count,
        total_snapshot_ready_count=total_snapshot_ready_count,
        total_cost_aware_report_count=total_cost_aware_report_count,
        total_blocked_market_count=total_blocked_market_count,
        latest_scan_market_count=latest.scan_market_count,
        latest_considered_count=latest.considered_count,
        latest_snapshot_ready_count=latest.snapshot_ready_count,
        latest_cost_aware_report_count=latest.cost_aware_report_count,
        latest_blocked_market_count=latest_blocked_market_count,
        overall_snapshot_ready_share=overall_snapshot_ready_share,
        latest_snapshot_ready_share=latest_snapshot_ready_share,
        blocked_market_share=blocked_market_share,
        blocked_reason_rows=_blocked_reason_rows(source_reports),
        reason_codes=reason_codes,
    )


def _normalize_reports(
    reports: list[PaperStrategyCycleReport] | tuple[PaperStrategyCycleReport, ...],
) -> tuple[PaperStrategyCycleReport, ...]:
    if type(reports) not in (list, tuple):
        raise ValueError("reports must be a list or tuple")
    normalized = tuple(reports)
    if not normalized:
        raise ValueError("reports must contain at least one value")
    for report in normalized:
        if type(report) is not PaperStrategyCycleReport:
            raise ValueError("reports must contain PaperStrategyCycleReport values")
        _require_hard_flags("report", report, readonly_required=False)
    return normalized


def _blocked_market_count(report: PaperStrategyCycleReport) -> int:
    return sum(count for _reason_code, count in report.blocked_counts)


def _blocked_reason_rows(
    reports: tuple[PaperStrategyCycleReport, ...],
) -> tuple[PaperStrategyCycleReportHistoryBlockedReasonRow, ...]:
    blocked_market_counts: dict[str, int] = {}
    report_counts: dict[str, int] = {}
    for report in reports:
        for reason_code, blocked_market_count in report.blocked_counts:
            blocked_market_counts[reason_code] = (
                blocked_market_counts.get(reason_code, 0) + blocked_market_count
            )
            report_counts[reason_code] = report_counts.get(reason_code, 0) + 1
    return tuple(
        PaperStrategyCycleReportHistoryBlockedReasonRow(
            reason_code=reason_code,
            blocked_market_count=blocked_market_counts[reason_code],
            report_count=report_counts[reason_code],
        )
        for reason_code in sorted(blocked_market_counts)
        if blocked_market_counts[reason_code] > 0
    )


def _status_and_reasons(
    report_count: int,
    latest_snapshot_ready_share: Decimal,
    blocked_market_share: Decimal,
    *,
    config: PaperStrategyCycleReportHistoryConfig,
) -> tuple[str, tuple[str, ...]]:
    if report_count < config.min_report_count:
        return "blocked", ("insufficient_strategy_cycle_report_history",)
    if latest_snapshot_ready_share < config.min_latest_snapshot_ready_share:
        return "blocked", ("latest_snapshot_ready_share_below_minimum",)
    if blocked_market_share > config.max_blocked_market_share:
        return "watch", ("blocked_market_share_above_limit",)
    return "pass", ()


def _ratio(numerator: int, denominator: int) -> Decimal:
    if denominator == 0:
        return Decimal("0.000000")
    return (Decimal(numerator) / Decimal(denominator)).quantize(
        RATIO_QUANTUM,
        rounding=ROUND_HALF_EVEN,
    )


def _validate_report_consistency(
    report: PaperStrategyCycleReportHistoryReport,
) -> None:
    if report.first_report_generated_at > report.latest_report_generated_at:
        raise ValueError("first_report_generated_at must be <= latest_report_generated_at")
    if report.latest_considered_count > report.latest_scan_market_count:
        raise ValueError("latest_considered_count must be <= latest_scan_market_count")
    if report.total_considered_count > report.total_scan_market_count:
        raise ValueError("total_considered_count must be <= total_scan_market_count")
    if (
        report.total_snapshot_ready_count + report.total_blocked_market_count
        != report.total_considered_count
    ):
        raise ValueError("total ready and blocked counts must sum to total_considered_count")
    if (
        report.latest_snapshot_ready_count + report.latest_blocked_market_count
        != report.latest_considered_count
    ):
        raise ValueError("latest ready and blocked counts must sum to latest_considered_count")
    if report.total_cost_aware_report_count != report.total_snapshot_ready_count:
        raise ValueError("total_cost_aware_report_count must equal total_snapshot_ready_count")
    if report.latest_cost_aware_report_count != report.latest_snapshot_ready_count:
        raise ValueError(
            "latest_cost_aware_report_count must equal latest_snapshot_ready_count",
        )
    if report.overall_snapshot_ready_share != _ratio(
        report.total_snapshot_ready_count,
        report.total_considered_count,
    ):
        raise ValueError("overall_snapshot_ready_share must match total counts")
    if report.latest_snapshot_ready_share != _ratio(
        report.latest_snapshot_ready_count,
        report.latest_considered_count,
    ):
        raise ValueError("latest_snapshot_ready_share must match latest counts")
    if report.blocked_market_share != _ratio(
        report.total_blocked_market_count,
        report.total_considered_count,
    ):
        raise ValueError("blocked_market_share must match total counts")
    if sum(row.blocked_market_count for row in report.blocked_reason_rows) != (
        report.total_blocked_market_count
    ):
        raise ValueError("blocked_reason_rows must match total_blocked_market_count")
    if any(row.report_count > report.report_count for row in report.blocked_reason_rows):
        raise ValueError("blocked reason report_count must not exceed report_count")
    if report.history_status == "pass" and report.reason_codes:
        raise ValueError("pass history must not have reason_codes")
    if report.history_status != "pass" and len(report.reason_codes) != 1:
        raise ValueError("non-pass history must have one reason_code")
    if report.reason_codes:
        reason_code = report.reason_codes[0]
        if reason_code in (
            "insufficient_strategy_cycle_report_history",
            "latest_snapshot_ready_share_below_minimum",
        ) and report.history_status != "blocked":
            raise ValueError("blocked reason_codes require blocked status")
        if (
            reason_code == "blocked_market_share_above_limit"
            and report.history_status != "watch"
        ):
            raise ValueError("watch reason_codes require watch status")


def _normalize_blocked_reason_rows(
    rows: tuple[PaperStrategyCycleReportHistoryBlockedReasonRow, ...],
) -> tuple[PaperStrategyCycleReportHistoryBlockedReasonRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("blocked_reason_rows must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("blocked_reason_rows must be an iterable") from exc
    for row in normalized:
        if type(row) is not PaperStrategyCycleReportHistoryBlockedReasonRow:
            raise ValueError("blocked_reason_rows must contain blocked reason rows")
    reason_codes = tuple(row.reason_code for row in normalized)
    if reason_codes != tuple(sorted(reason_codes)):
        raise ValueError("blocked_reason_rows must be sorted by reason_code")
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError("blocked_reason_rows reason_code values must be unique")
    return normalized


def _normalize_reason_codes(
    field_name: str,
    reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable of reason codes")
    try:
        normalized = tuple(reason_codes)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable of reason codes") from exc
    for reason_code in normalized:
        _require_canonical_string(field_name, reason_code)
        if reason_code not in REASON_CODES:
            raise ValueError(f"{field_name} must contain known reason codes")
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} must not contain duplicates")
    return normalized


def _as_utc(field_name: str, value: Any) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _require_canonical_string(field_name: str, value: Any) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_nonnegative_int(field_name: str, value: Any) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_positive_int(field_name: str, value: Any) -> None:
    _require_nonnegative_int(field_name, value)
    if value <= 0:
        raise ValueError(f"{field_name} must be positive")


def _require_probability_decimal(field_name: str, value: Any) -> None:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < 0 or value > 1:
        raise ValueError(f"{field_name} must be between zero and one")
    if value != value.quantize(RATIO_QUANTUM):
        raise ValueError(f"{field_name} must have at most six decimal places")


def _require_hard_flags(
    field_name: str,
    value: Any,
    *,
    readonly_required: bool = True,
) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} report_only must be True")
    if readonly_required and getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} readonly must be True")
