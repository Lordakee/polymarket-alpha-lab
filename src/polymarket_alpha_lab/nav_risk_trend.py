from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from polymarket_alpha_lab.nav_risk_metrics import PaperNavRiskMetricsReport


RATIO_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0")
NAV_RISK_TREND_STATUSES = (
    "empty_nav_risk_history",
    "latest_nav_risk_observed",
    "latest_nav_has_unexecutable_positions",
)


@dataclass(frozen=True)
class PaperNavRiskTrendConfig:
    config_version: str

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)


@dataclass(frozen=True)
class PaperNavRiskTrendStatusRow:
    status: str
    report_count: int
    report_ratio: Decimal | None

    def __post_init__(self) -> None:
        if self.status not in NAV_RISK_TREND_STATUSES:
            raise ValueError("status must be a known nav risk trend status")
        _require_nonnegative_int("report_count", self.report_count)
        _require_optional_ratio_decimal("report_ratio", self.report_ratio)


@dataclass(frozen=True)
class PaperNavRiskTrendReport:
    generated_at: datetime
    config_version: str
    nav_risk_report_count: int
    first_report_generated_at: datetime | None
    latest_report_generated_at: datetime | None
    latest_exit_nav: Decimal | None
    latest_cumulative_return: Decimal | None
    latest_max_drawdown: Decimal | None
    latest_max_drawdown_pct: Decimal | None
    latest_nav_return_volatility: Decimal | None
    latest_open_position_count: int
    latest_fully_executable_count: int
    latest_partially_executable_count: int
    latest_no_exit_depth_count: int
    latest_largest_market_exposure_value: Decimal | None
    latest_largest_market_exposure_share: Decimal | None
    worst_observed_max_drawdown_pct: Decimal | None
    consecutive_unexecutable_open_position_count: int
    status: str
    status_rows: tuple[PaperNavRiskTrendStatusRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if not isinstance(self.generated_at, datetime):
            raise ValueError("generated_at must be a datetime")
        _require_canonical_string("config_version", self.config_version)
        _require_nonnegative_int(
            "nav_risk_report_count",
            self.nav_risk_report_count,
        )
        _require_optional_datetime(
            "first_report_generated_at",
            self.first_report_generated_at,
        )
        _require_optional_datetime(
            "latest_report_generated_at",
            self.latest_report_generated_at,
        )
        for field_name in (
            "latest_exit_nav",
            "latest_max_drawdown",
            "latest_max_drawdown_pct",
            "latest_nav_return_volatility",
            "latest_largest_market_exposure_value",
            "latest_largest_market_exposure_share",
            "worst_observed_max_drawdown_pct",
        ):
            _require_optional_nonnegative_decimal(field_name, getattr(self, field_name))
        _require_optional_decimal(
            "latest_cumulative_return",
            self.latest_cumulative_return,
        )
        for field_name in (
            "latest_open_position_count",
            "latest_fully_executable_count",
            "latest_partially_executable_count",
            "latest_no_exit_depth_count",
            "consecutive_unexecutable_open_position_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        if self.status not in NAV_RISK_TREND_STATUSES:
            raise ValueError("status must be a known nav risk trend status")
        object.__setattr__(self, "status_rows", _normalize_status_rows(self.status_rows))
        if self.paper_only is not True:
            raise ValueError("paper_only must be True")
        if self.report_only is not True:
            raise ValueError("report_only must be True")
        if self.readonly is not True:
            raise ValueError("readonly must be True")
        _validate_report_consistency(self)


def build_paper_nav_risk_trend_report(
    reports: list[PaperNavRiskMetricsReport] | tuple[PaperNavRiskMetricsReport, ...],
    *,
    config: PaperNavRiskTrendConfig,
    generated_at: datetime,
) -> PaperNavRiskTrendReport:
    if type(config) is not PaperNavRiskTrendConfig:
        raise ValueError("config must be a PaperNavRiskTrendConfig")
    if not isinstance(generated_at, datetime):
        raise ValueError("generated_at must be a datetime")

    normalized_reports = _normalize_reports(reports)
    report_count = len(normalized_reports)
    status_counts = _status_counts(normalized_reports)
    latest = normalized_reports[-1] if normalized_reports else None

    if latest is None:
        return PaperNavRiskTrendReport(
            generated_at=generated_at,
            config_version=config.config_version,
            nav_risk_report_count=0,
            first_report_generated_at=None,
            latest_report_generated_at=None,
            latest_exit_nav=None,
            latest_cumulative_return=None,
            latest_max_drawdown=None,
            latest_max_drawdown_pct=None,
            latest_nav_return_volatility=None,
            latest_open_position_count=0,
            latest_fully_executable_count=0,
            latest_partially_executable_count=0,
            latest_no_exit_depth_count=0,
            latest_largest_market_exposure_value=None,
            latest_largest_market_exposure_share=None,
            worst_observed_max_drawdown_pct=None,
            consecutive_unexecutable_open_position_count=0,
            status="empty_nav_risk_history",
            status_rows=_build_status_rows(status_counts, report_count),
        )

    return PaperNavRiskTrendReport(
        generated_at=generated_at,
        config_version=config.config_version,
        nav_risk_report_count=report_count,
        first_report_generated_at=normalized_reports[0].generated_at,
        latest_report_generated_at=latest.generated_at,
        latest_exit_nav=latest.latest_exit_nav,
        latest_cumulative_return=latest.cumulative_return,
        latest_max_drawdown=latest.max_drawdown,
        latest_max_drawdown_pct=latest.max_drawdown_pct,
        latest_nav_return_volatility=latest.nav_return_volatility,
        latest_open_position_count=latest.open_position_count,
        latest_fully_executable_count=latest.fully_executable_count,
        latest_partially_executable_count=latest.partially_executable_count,
        latest_no_exit_depth_count=latest.no_exit_depth_count,
        latest_largest_market_exposure_value=latest.largest_market_exposure_value,
        latest_largest_market_exposure_share=latest.largest_market_exposure_share,
        worst_observed_max_drawdown_pct=_worst_observed_max_drawdown_pct(
            normalized_reports,
        ),
        consecutive_unexecutable_open_position_count=(
            _consecutive_unexecutable_open_position_count(normalized_reports)
        ),
        status=_report_status(latest),
        status_rows=_build_status_rows(status_counts, report_count),
    )


def _normalize_reports(
    reports: list[PaperNavRiskMetricsReport] | tuple[PaperNavRiskMetricsReport, ...],
) -> tuple[PaperNavRiskMetricsReport, ...]:
    if type(reports) not in (list, tuple):
        raise ValueError("reports must be a list or tuple")

    normalized = tuple(reports)
    for report in normalized:
        if type(report) is not PaperNavRiskMetricsReport:
            raise ValueError(
                "reports must contain only PaperNavRiskMetricsReport values",
            )
        if getattr(report, "paper_only", True) is not True:
            raise ValueError("source report paper_only must be True")
        if getattr(report, "report_only", True) is not True:
            raise ValueError("source report report_only must be True")
    return normalized


def _status_counts(
    reports: tuple[PaperNavRiskMetricsReport, ...],
) -> dict[str, int]:
    counts = {status: 0 for status in NAV_RISK_TREND_STATUSES}
    if not reports:
        return counts
    for report in reports:
        counts[_report_status(report)] += 1
    return counts


def _build_status_rows(
    status_counts: dict[str, int],
    total: int,
) -> tuple[PaperNavRiskTrendStatusRow, ...]:
    return tuple(
        PaperNavRiskTrendStatusRow(
            status=status,
            report_count=status_counts[status],
            report_ratio=_ratio(status_counts[status], total),
        )
        for status in NAV_RISK_TREND_STATUSES
    )


def _report_status(report: PaperNavRiskMetricsReport) -> str:
    if _unexecutable_open_position_count(report) > 0:
        return "latest_nav_has_unexecutable_positions"
    return "latest_nav_risk_observed"


def _unexecutable_open_position_count(report: PaperNavRiskMetricsReport) -> int:
    implied_unexecutable_count = (
        report.open_position_count
        - report.fully_executable_count
        - report.partially_executable_count
    )
    return max(report.no_exit_depth_count, implied_unexecutable_count, 0)


def _consecutive_unexecutable_open_position_count(
    reports: tuple[PaperNavRiskMetricsReport, ...],
) -> int:
    count = 0
    for report in reversed(reports):
        if _unexecutable_open_position_count(report) == 0:
            break
        count += 1
    return count


def _worst_observed_max_drawdown_pct(
    reports: tuple[PaperNavRiskMetricsReport, ...],
) -> Decimal | None:
    values = tuple(
        report.max_drawdown_pct for report in reports if report.max_drawdown_pct is not None
    )
    return max(values) if values else None


def _ratio(numerator: int, denominator: int) -> Decimal | None:
    if denominator == 0:
        return None
    return (Decimal(numerator) / Decimal(denominator)).quantize(RATIO_QUANTUM)


def _validate_report_consistency(report: PaperNavRiskTrendReport) -> None:
    if sum(row.report_count for row in report.status_rows) != report.nav_risk_report_count:
        raise ValueError("status_rows counts must sum to nav_risk_report_count")
    if report.status_rows != _build_status_rows(
        _counts_from_status_rows(report.status_rows),
        report.nav_risk_report_count,
    ):
        raise ValueError("status_rows ratios must match nav_risk_report_count")

    timestamps_absent = (
        report.first_report_generated_at is None
        and report.latest_report_generated_at is None
    )
    timestamps_present = (
        report.first_report_generated_at is not None
        and report.latest_report_generated_at is not None
    )
    if report.nav_risk_report_count == 0:
        if not timestamps_absent:
            raise ValueError("empty trend report must not have report timestamps")
        _require_empty_latest_fields(report)
        if report.status != "empty_nav_risk_history":
            raise ValueError("status must match nav risk trend observations")
    else:
        if not timestamps_present:
            raise ValueError("non-empty trend report must have report timestamps")
        latest_unexecutable_count = _latest_unexecutable_open_position_count(report)
        if latest_unexecutable_count == 0:
            expected_status = "latest_nav_risk_observed"
        else:
            expected_status = "latest_nav_has_unexecutable_positions"
        if report.status != expected_status:
            raise ValueError("status must match nav risk trend observations")
        if latest_unexecutable_count == 0:
            if report.consecutive_unexecutable_open_position_count != 0:
                raise ValueError("observed latest report must reset the streak")
        elif report.consecutive_unexecutable_open_position_count < 1:
            raise ValueError("unexecutable latest report requires a streak")


def _latest_unexecutable_open_position_count(report: PaperNavRiskTrendReport) -> int:
    implied_unexecutable_count = (
        report.latest_open_position_count
        - report.latest_fully_executable_count
        - report.latest_partially_executable_count
    )
    return max(report.latest_no_exit_depth_count, implied_unexecutable_count, 0)


def _require_empty_latest_fields(report: PaperNavRiskTrendReport) -> None:
    for field_name in (
        "latest_exit_nav",
        "latest_cumulative_return",
        "latest_max_drawdown",
        "latest_max_drawdown_pct",
        "latest_nav_return_volatility",
        "latest_largest_market_exposure_value",
        "latest_largest_market_exposure_share",
        "worst_observed_max_drawdown_pct",
    ):
        if getattr(report, field_name) is not None:
            raise ValueError(f"{field_name} must be absent without reports")
    for field_name in (
        "latest_open_position_count",
        "latest_fully_executable_count",
        "latest_partially_executable_count",
        "latest_no_exit_depth_count",
        "consecutive_unexecutable_open_position_count",
    ):
        if getattr(report, field_name) != 0:
            raise ValueError(f"{field_name} must be zero without reports")


def _normalize_status_rows(
    rows: tuple[PaperNavRiskTrendStatusRow, ...],
) -> tuple[PaperNavRiskTrendStatusRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("status_rows must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("status_rows must be an iterable") from exc
    if tuple(row.status for row in normalized) != NAV_RISK_TREND_STATUSES:
        raise ValueError("status_rows must cover nav risk trend statuses")
    for row in normalized:
        if type(row) is not PaperNavRiskTrendStatusRow:
            raise ValueError("status_rows must contain PaperNavRiskTrendStatusRow values")
    return normalized


def _counts_from_status_rows(
    rows: tuple[PaperNavRiskTrendStatusRow, ...],
) -> dict[str, int]:
    return {row.status: row.report_count for row in rows}


def _require_canonical_string(field_name: str, value: str) -> None:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_nonnegative_int(field_name: str, value: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_optional_datetime(field_name: str, value: datetime | None) -> None:
    if value is None:
        return
    if not isinstance(value, datetime):
        raise ValueError(f"{field_name} must be a datetime or None")


def _require_decimal(field_name: str, value: Decimal) -> None:
    if not isinstance(value, Decimal):
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")


def _require_optional_decimal(field_name: str, value: Decimal | None) -> None:
    if value is not None:
        _require_decimal(field_name, value)


def _require_optional_nonnegative_decimal(
    field_name: str,
    value: Decimal | None,
) -> None:
    if value is None:
        return
    _require_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_optional_ratio_decimal(
    field_name: str,
    value: Decimal | None,
) -> None:
    if value is None:
        return
    _require_optional_nonnegative_decimal(field_name, value)
    if value > Decimal("1"):
        raise ValueError(f"{field_name} must be at most one")
    if value != value.quantize(RATIO_QUANTUM):
        raise ValueError(f"{field_name} must use ratio quantum")


__all__ = (
    "PaperNavRiskTrendConfig",
    "PaperNavRiskTrendStatusRow",
    "PaperNavRiskTrendReport",
    "build_paper_nav_risk_trend_report",
)
