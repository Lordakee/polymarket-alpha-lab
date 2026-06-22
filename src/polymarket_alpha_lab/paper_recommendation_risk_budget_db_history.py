"""Read-only history reducer for persisted paper recommendation risk budgets."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal

from polymarket_alpha_lab.paper_recommendation_risk_budget import (
    PaperRecommendationRiskBudgetReport,
)


RISK_BUDGET_STATUSES = ("pass", "watch", "blocked")
HISTORY_STATUSES = (
    "empty_paper_recommendation_risk_budget_db_history",
    "latest_paper_recommendation_risk_budget_passed",
    "latest_paper_recommendation_risk_budget_watch",
    "latest_paper_recommendation_risk_budget_blocked",
)


@dataclass(frozen=True)
class PaperRecommendationRiskBudgetDbHistoryConfig:
    config_version: str

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)


@dataclass(frozen=True)
class PaperRecommendationRiskBudgetDbHistoryReport:
    generated_at: datetime
    config_version: str
    status: str
    report_count: int
    first_report_generated_at: datetime | None
    latest_report_generated_at: datetime | None
    latest_status: str | None
    status_counts: tuple[tuple[str, int], ...]
    duplicate_generated_at_count: int
    latest_total_notional_utilization: Decimal | None
    worst_total_notional_utilization: Decimal | None
    latest_largest_single_recommendation_share: Decimal | None
    worst_largest_single_recommendation_share: Decimal | None
    latest_selected_count: int | None
    latest_blocked_count: int | None
    reason_code_counts: tuple[tuple[str, int], ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_canonical_string("config_version", self.config_version)
        if type(self.status) is not str or self.status not in HISTORY_STATUSES:
            raise ValueError("status must be a known history status")
        _require_nonnegative_int("report_count", self.report_count)
        object.__setattr__(
            self,
            "first_report_generated_at",
            _as_optional_utc(
                "first_report_generated_at",
                self.first_report_generated_at,
            ),
        )
        object.__setattr__(
            self,
            "latest_report_generated_at",
            _as_optional_utc(
                "latest_report_generated_at",
                self.latest_report_generated_at,
            ),
        )
        if self.latest_status is not None:
            _require_risk_budget_status("latest_status", self.latest_status)
        object.__setattr__(
            self,
            "status_counts",
            _normalize_status_counts(self.status_counts),
        )
        _require_nonnegative_int(
            "duplicate_generated_at_count",
            self.duplicate_generated_at_count,
        )
        for field_name in (
            "latest_total_notional_utilization",
            "worst_total_notional_utilization",
            "latest_largest_single_recommendation_share",
            "worst_largest_single_recommendation_share",
        ):
            _require_optional_ratio(field_name, getattr(self, field_name))
        if self.latest_selected_count is not None:
            _require_nonnegative_int("latest_selected_count", self.latest_selected_count)
        if self.latest_blocked_count is not None:
            _require_nonnegative_int("latest_blocked_count", self.latest_blocked_count)
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        _validate_report_consistency(self)
        _require_hard_flags(self)


def build_paper_recommendation_risk_budget_db_history_report(
    reports: object,
    *,
    config: PaperRecommendationRiskBudgetDbHistoryConfig,
    generated_at: datetime,
) -> PaperRecommendationRiskBudgetDbHistoryReport:
    if type(config) is not PaperRecommendationRiskBudgetDbHistoryConfig:
        raise ValueError(
            "config must be a PaperRecommendationRiskBudgetDbHistoryConfig",
        )
    if type(generated_at) is not datetime:
        raise ValueError("generated_at must be a datetime")

    report_items = _normalize_reports(reports)
    chronological_reports = tuple(
        sorted(
            enumerate(report_items),
            key=lambda item: (
                _as_utc("report generated_at", item[1].generated_at),
                item[0],
            ),
        ),
    )
    normalized_reports = tuple(report for _, report in chronological_reports)
    latest = normalized_reports[-1] if normalized_reports else None

    return PaperRecommendationRiskBudgetDbHistoryReport(
        generated_at=generated_at,
        config_version=config.config_version,
        status=_history_status(latest),
        report_count=len(normalized_reports),
        first_report_generated_at=(
            normalized_reports[0].generated_at if normalized_reports else None
        ),
        latest_report_generated_at=latest.generated_at if latest is not None else None,
        latest_status=latest.status if latest is not None else None,
        status_counts=_status_counts(normalized_reports),
        duplicate_generated_at_count=_duplicate_generated_at_count(normalized_reports),
        latest_total_notional_utilization=(
            latest.total_notional_utilization if latest is not None else None
        ),
        worst_total_notional_utilization=_max_optional_decimal(
            tuple(report.total_notional_utilization for report in normalized_reports),
        ),
        latest_largest_single_recommendation_share=(
            latest.largest_single_recommendation_share if latest is not None else None
        ),
        worst_largest_single_recommendation_share=_max_optional_decimal(
            tuple(
                report.largest_single_recommendation_share
                for report in normalized_reports
            ),
        ),
        latest_selected_count=latest.selected_count if latest is not None else None,
        latest_blocked_count=latest.blocked_count if latest is not None else None,
        reason_code_counts=_reason_code_counts(normalized_reports),
    )


def _normalize_reports(
    value: object,
) -> tuple[PaperRecommendationRiskBudgetReport, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reports must be a list or tuple")
    reports = tuple(value)
    normalized = []
    for report in reports:
        if type(report) is not PaperRecommendationRiskBudgetReport:
            raise ValueError(
                "reports must contain PaperRecommendationRiskBudgetReport values",
            )
        _validate_source_report(report)
        normalized.append(report)
    return tuple(normalized)


def _validate_source_report(report: PaperRecommendationRiskBudgetReport) -> None:
    _require_hard_flags(report)
    _as_utc("report generated_at", report.generated_at)
    _require_canonical_string("report config_version", report.config_version)
    _require_risk_budget_status("report status", report.status)
    for field_name in (
        "total_suggested_notional",
        "max_total_utilization",
        "max_single_recommendation_share",
        "min_remaining_notional",
    ):
        _require_nonnegative_decimal(field_name, getattr(report, field_name))
    for field_name in (
        "remaining_total_notional",
        "nav_notional",
    ):
        _require_optional_nonnegative_decimal(field_name, getattr(report, field_name))
    for field_name in (
        "total_notional_utilization",
        "largest_single_recommendation_share",
    ):
        _require_optional_ratio(field_name, getattr(report, field_name))
    for field_name in (
        "selected_count",
        "blocked_count",
        "max_selected_count",
    ):
        _require_nonnegative_int(field_name, getattr(report, field_name))
    _normalize_reason_codes(report.reason_codes)
    _normalize_selected_position_notional_values(
        report.selected_position_notional_values,
    )


def _history_status(report: PaperRecommendationRiskBudgetReport | None) -> str:
    if report is None:
        return "empty_paper_recommendation_risk_budget_db_history"
    if report.status == "pass":
        return "latest_paper_recommendation_risk_budget_passed"
    if report.status == "watch":
        return "latest_paper_recommendation_risk_budget_watch"
    return "latest_paper_recommendation_risk_budget_blocked"


def _status_counts(
    reports: tuple[PaperRecommendationRiskBudgetReport, ...],
) -> tuple[tuple[str, int], ...]:
    counts = {status: 0 for status in RISK_BUDGET_STATUSES}
    for report in reports:
        counts[report.status] += 1
    return tuple((status, counts[status]) for status in RISK_BUDGET_STATUSES)


def _reason_code_counts(
    reports: tuple[PaperRecommendationRiskBudgetReport, ...],
) -> tuple[tuple[str, int], ...]:
    counts: dict[str, int] = {}
    for report in reports:
        for reason_code in report.reason_codes:
            counts[reason_code] = counts.get(reason_code, 0) + 1
    return tuple(sorted(counts.items()))


def _duplicate_generated_at_count(
    reports: tuple[PaperRecommendationRiskBudgetReport, ...],
) -> int:
    counts: dict[datetime, int] = {}
    for report in reports:
        generated_at = report.generated_at
        counts[generated_at] = counts.get(generated_at, 0) + 1
    return sum(count - 1 for count in counts.values() if count > 1)


def _max_optional_decimal(values: tuple[Decimal | None, ...]) -> Decimal | None:
    observed = tuple(value for value in values if value is not None)
    if not observed:
        return None
    return max(observed)


def _normalize_status_counts(value: object) -> tuple[tuple[str, int], ...]:
    if type(value) is not tuple:
        raise ValueError("status_counts must be a tuple")
    rows = []
    for item in value:
        if type(item) is not tuple or len(item) != 2:
            raise ValueError("status_counts must contain status/count pairs")
        status, count = item
        _require_risk_budget_status("status", status)
        _require_nonnegative_int("status_count", count)
        rows.append((status, count))
    if tuple(status for status, _ in rows) != RISK_BUDGET_STATUSES:
        raise ValueError("status_counts must cover risk budget statuses")
    return tuple(rows)


def _normalize_reason_code_counts(
    value: object,
) -> tuple[tuple[str, int], ...]:
    if type(value) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    rows = []
    for item in value:
        if type(item) is not tuple or len(item) != 2:
            raise ValueError("reason_code_counts must contain reason/count pairs")
        reason_code, count = item
        _require_canonical_string("reason_code", reason_code)
        _require_nonnegative_int("reason_code_count", count)
        rows.append((reason_code, count))
    if tuple(sorted(rows)) != tuple(rows):
        raise ValueError("reason_code_counts must be sorted")
    return tuple(rows)


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_codes must be an iterable")
    try:
        reason_codes = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable") from exc
    if not reason_codes:
        raise ValueError("reason_codes must contain at least one value")
    for reason_code in reason_codes:
        _require_canonical_string("reason_code", reason_code)
    return reason_codes


def _normalize_selected_position_notional_values(value: object) -> tuple[Decimal, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("selected_position_notional_values must be an iterable")
    try:
        values = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("selected_position_notional_values must be an iterable") from exc
    for item in values:
        _require_nonnegative_decimal("selected_position_notional", item)
    return values


def _validate_report_consistency(
    report: PaperRecommendationRiskBudgetDbHistoryReport,
) -> None:
    if report.report_count == 0:
        if report.status != "empty_paper_recommendation_risk_budget_db_history":
            raise ValueError("status must match report_count")
        if report.first_report_generated_at is not None:
            raise ValueError("first_report_generated_at must be absent without reports")
        if report.latest_report_generated_at is not None:
            raise ValueError("latest_report_generated_at must be absent without reports")
        if report.latest_status is not None:
            raise ValueError("latest_status must be absent without reports")
        if report.duplicate_generated_at_count != 0:
            raise ValueError("duplicate_generated_at_count must be zero without reports")
        if report.latest_total_notional_utilization is not None:
            raise ValueError(
                "latest_total_notional_utilization must be absent without reports",
            )
        if report.worst_total_notional_utilization is not None:
            raise ValueError(
                "worst_total_notional_utilization must be absent without reports",
            )
        if report.latest_largest_single_recommendation_share is not None:
            raise ValueError(
                "latest_largest_single_recommendation_share must be absent "
                "without reports",
            )
        if report.worst_largest_single_recommendation_share is not None:
            raise ValueError(
                "worst_largest_single_recommendation_share must be absent "
                "without reports",
            )
        if report.latest_selected_count is not None:
            raise ValueError("latest_selected_count must be absent without reports")
        if report.latest_blocked_count is not None:
            raise ValueError("latest_blocked_count must be absent without reports")
        if report.reason_code_counts:
            raise ValueError("reason_code_counts must be empty without reports")
    else:
        if report.status == "empty_paper_recommendation_risk_budget_db_history":
            raise ValueError("status must not be empty with reports")
        if report.first_report_generated_at is None:
            raise ValueError("first_report_generated_at is required with reports")
        if report.latest_report_generated_at is None:
            raise ValueError("latest_report_generated_at is required with reports")
        if report.latest_status is None:
            raise ValueError("latest_status is required with reports")
        if report.latest_selected_count is None:
            raise ValueError("latest_selected_count is required with reports")
        if report.latest_blocked_count is None:
            raise ValueError("latest_blocked_count is required with reports")
        if report.status != _history_status_from_latest_status(report.latest_status):
            raise ValueError("status must match latest_status")
    if sum(count for _, count in report.status_counts) != report.report_count:
        raise ValueError("status_counts must match report_count")


def _history_status_from_latest_status(status: str) -> str:
    if status == "pass":
        return "latest_paper_recommendation_risk_budget_passed"
    if status == "watch":
        return "latest_paper_recommendation_risk_budget_watch"
    return "latest_paper_recommendation_risk_budget_blocked"


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _as_optional_utc(field_name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_risk_budget_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in RISK_BUDGET_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _require_nonnegative_int(field_name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_nonnegative_decimal(field_name: str, value: object) -> None:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < Decimal("0"):
        raise ValueError(f"{field_name} must be nonnegative")


def _require_optional_nonnegative_decimal(field_name: str, value: object) -> None:
    if value is not None:
        _require_nonnegative_decimal(field_name, value)


def _require_optional_ratio(field_name: str, value: object) -> None:
    if value is None:
        return
    _require_nonnegative_decimal(field_name, value)
    if value > Decimal("1"):
        raise ValueError(f"{field_name} must be at most 1")


def _require_hard_flags(value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError("paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError("report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError("readonly must be True")


__all__ = (
    "PaperRecommendationRiskBudgetDbHistoryConfig",
    "PaperRecommendationRiskBudgetDbHistoryReport",
    "build_paper_recommendation_risk_budget_db_history_report",
)
