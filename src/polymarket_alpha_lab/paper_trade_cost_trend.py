"""Paper-only trend summaries over paper-trade cost audit reports.

Pure aggregation over already-built ``PaperTradeCostAuditReport`` values. This
module is local/report-only: it does not read files, fetch markets, construct
API clients, authenticate, access wallets, place orders, rank investments,
recommend trades, or provide financial advice.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, ROUND_HALF_EVEN
from typing import Any

from polymarket_alpha_lab.paper_trade_cost_audit import PaperTradeCostAuditReport


RATIO_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0")
ONE = Decimal("1")
COST_TREND_STATUSES = (
    "empty_cost_audit_history",
    "latest_cost_observed",
    "latest_negative_cost_adjusted_edges",
)


@dataclass(frozen=True)
class PaperTradeCostTrendConfig:
    config_version: str

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)


@dataclass(frozen=True)
class PaperTradeCostTrendStatusRow:
    status: str
    status_count: int
    status_ratio: Decimal | None

    def __post_init__(self) -> None:
        if self.status not in COST_TREND_STATUSES:
            raise ValueError("status must be a known cost trend status")
        _require_nonnegative_int("status_count", self.status_count)
        _require_optional_probability_decimal("status_ratio", self.status_ratio)


@dataclass(frozen=True)
class PaperTradeCostTrendReport:
    generated_at: datetime
    config_version: str
    cost_audit_report_count: int
    first_report_generated_at: datetime | None
    latest_report_generated_at: datetime | None
    latest_trade_count: int
    latest_fill_rate: Decimal | None
    latest_mean_theoretical_edge: Decimal | None
    latest_mean_cost_adjusted_edge: Decimal | None
    latest_mean_edge_cost_drag: Decimal | None
    latest_total_edge_cost_drag: Decimal | None
    latest_partial_fill_count: int
    latest_negative_cost_adjusted_edge_count: int
    worst_observed_mean_edge_cost_drag: Decimal | None
    worst_observed_negative_cost_adjusted_edge_count: int
    consecutive_negative_cost_adjusted_edge_count: int
    status: str
    status_rows: tuple[PaperTradeCostTrendStatusRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self.generated_at) is not datetime:
            raise ValueError("generated_at must be a datetime")
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "cost_audit_report_count",
            "latest_trade_count",
            "latest_partial_fill_count",
            "latest_negative_cost_adjusted_edge_count",
            "worst_observed_negative_cost_adjusted_edge_count",
            "consecutive_negative_cost_adjusted_edge_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        for field_name in (
            "first_report_generated_at",
            "latest_report_generated_at",
        ):
            _require_optional_datetime(field_name, getattr(self, field_name))
        for field_name in (
            "latest_fill_rate",
            "latest_mean_theoretical_edge",
            "latest_mean_cost_adjusted_edge",
            "latest_mean_edge_cost_drag",
            "latest_total_edge_cost_drag",
            "worst_observed_mean_edge_cost_drag",
        ):
            _require_optional_decimal(field_name, getattr(self, field_name))
        if self.status not in COST_TREND_STATUSES:
            raise ValueError("status must be a known cost trend status")
        object.__setattr__(self, "status_rows", _normalize_status_rows(self.status_rows))
        _validate_report_consistency(self)
        if self.paper_only is not True:
            raise ValueError("paper_only must be True")
        if self.report_only is not True:
            raise ValueError("report_only must be True")
        if self.readonly is not True:
            raise ValueError("readonly must be True")

    @property
    def report_count(self) -> int:
        return self.cost_audit_report_count

    @property
    def worst_mean_edge_cost_drag(self) -> Decimal | None:
        return self.worst_observed_mean_edge_cost_drag


def build_paper_trade_cost_trend_report(
    reports: list[PaperTradeCostAuditReport]
    | tuple[PaperTradeCostAuditReport, ...],
    *,
    config: PaperTradeCostTrendConfig,
    generated_at: datetime,
) -> PaperTradeCostTrendReport:
    """Aggregate local paper-trade cost audit reports into a trend snapshot."""

    if type(config) is not PaperTradeCostTrendConfig:
        raise ValueError("config must be a PaperTradeCostTrendConfig")
    if type(generated_at) is not datetime:
        raise ValueError("generated_at must be a datetime")

    cost_audits = _normalize_cost_audit_reports(reports)
    for report in cost_audits[:-1]:
        if report.generated_at > generated_at:
            raise ValueError("source report generated_at must not be after generated_at")
    report_count = len(cost_audits)
    status_counts = _status_counts(cost_audits)
    if not cost_audits:
        return PaperTradeCostTrendReport(
            generated_at=generated_at,
            config_version=config.config_version,
            cost_audit_report_count=0,
            first_report_generated_at=None,
            latest_report_generated_at=None,
            latest_trade_count=0,
            latest_fill_rate=None,
            latest_mean_theoretical_edge=None,
            latest_mean_cost_adjusted_edge=None,
            latest_mean_edge_cost_drag=None,
            latest_total_edge_cost_drag=None,
            latest_partial_fill_count=0,
            latest_negative_cost_adjusted_edge_count=0,
            worst_observed_mean_edge_cost_drag=None,
            worst_observed_negative_cost_adjusted_edge_count=0,
            consecutive_negative_cost_adjusted_edge_count=0,
            status="empty_cost_audit_history",
            status_rows=_build_status_rows(status_counts, report_count),
        )

    latest = cost_audits[-1]
    return PaperTradeCostTrendReport(
        generated_at=generated_at,
        config_version=config.config_version,
        cost_audit_report_count=report_count,
        first_report_generated_at=cost_audits[0].generated_at,
        latest_report_generated_at=latest.generated_at,
        latest_trade_count=latest.trade_count,
        latest_fill_rate=latest.fill_rate,
        latest_mean_theoretical_edge=latest.mean_theoretical_edge,
        latest_mean_cost_adjusted_edge=latest.mean_cost_adjusted_edge,
        latest_mean_edge_cost_drag=latest.mean_edge_cost_drag,
        latest_total_edge_cost_drag=latest.total_edge_cost_drag,
        latest_partial_fill_count=latest.partial_fill_count,
        latest_negative_cost_adjusted_edge_count=(
            latest.negative_cost_adjusted_edge_count
        ),
        worst_observed_mean_edge_cost_drag=_worst_observed_mean_edge_cost_drag(
            cost_audits,
        ),
        worst_observed_negative_cost_adjusted_edge_count=max(
            report.negative_cost_adjusted_edge_count for report in cost_audits
        ),
        consecutive_negative_cost_adjusted_edge_count=(
            _consecutive_negative_cost_adjusted_edge_count(cost_audits)
        ),
        status=_report_status(latest),
        status_rows=_build_status_rows(status_counts, report_count),
    )


def _normalize_cost_audit_reports(
    reports: list[PaperTradeCostAuditReport]
    | tuple[PaperTradeCostAuditReport, ...],
) -> tuple[PaperTradeCostAuditReport, ...]:
    if type(reports) not in (list, tuple):
        raise ValueError("reports must be a list or tuple of cost audit reports")
    normalized = tuple(reports)
    for report in normalized:
        if type(report) is not PaperTradeCostAuditReport:
            raise ValueError(
                "reports must contain only PaperTradeCostAuditReport values",
            )
        if report.paper_only is not True:
            raise ValueError("reports must contain paper_only cost audit reports")
        if report.report_only is not True:
            raise ValueError("reports must contain report_only cost audit reports")
        if report.readonly is not True:
            raise ValueError("reports must contain readonly cost audit reports")
        if report.negative_cost_adjusted_edge_count > report.trade_count:
            raise ValueError(
                "negative_cost_adjusted_edge_count must not exceed trade_count",
            )
    return normalized


def _status_counts(
    reports: tuple[PaperTradeCostAuditReport, ...],
) -> dict[str, int]:
    counts = {status: 0 for status in COST_TREND_STATUSES}
    for report in reports:
        counts[_report_status(report)] += 1
    return counts


def _build_status_rows(
    status_counts: dict[str, int],
    total: int,
) -> tuple[PaperTradeCostTrendStatusRow, ...]:
    return tuple(
        PaperTradeCostTrendStatusRow(
            status=status,
            status_count=status_counts[status],
            status_ratio=_ratio(status_counts[status], total),
        )
        for status in COST_TREND_STATUSES
    )


def _report_status(report: PaperTradeCostAuditReport) -> str:
    if report.negative_cost_adjusted_edge_count > 0:
        return "latest_negative_cost_adjusted_edges"
    return "latest_cost_observed"


def _worst_observed_mean_edge_cost_drag(
    reports: tuple[PaperTradeCostAuditReport, ...],
) -> Decimal | None:
    values = tuple(
        report.mean_edge_cost_drag
        for report in reports
        if report.mean_edge_cost_drag is not None
    )
    return max(values) if values else None


def _consecutive_negative_cost_adjusted_edge_count(
    reports: tuple[PaperTradeCostAuditReport, ...],
) -> int:
    count = 0
    for report in reversed(reports):
        if report.negative_cost_adjusted_edge_count == 0:
            break
        count += 1
    return count


def _ratio(numerator: int, denominator: int) -> Decimal | None:
    if denominator == 0:
        return None
    return (Decimal(numerator) / Decimal(denominator)).quantize(
        RATIO_QUANTUM,
        rounding=ROUND_HALF_EVEN,
    )


def _validate_report_consistency(report: PaperTradeCostTrendReport) -> None:
    if report.status_rows != _build_status_rows(
        _counts_from_status_rows(report.status_rows),
        report.cost_audit_report_count,
    ):
        raise ValueError("status_rows ratios must match cost audit report count")
    if (
        sum(row.status_count for row in report.status_rows)
        != report.cost_audit_report_count
    ):
        raise ValueError("status_rows counts must sum to cost audit report count")

    if report.cost_audit_report_count == 0:
        _require_none("first_report_generated_at", report.first_report_generated_at)
        _require_none("latest_report_generated_at", report.latest_report_generated_at)
        _require_zero("latest_trade_count", report.latest_trade_count)
        _require_none("latest_fill_rate", report.latest_fill_rate)
        _require_none("latest_mean_theoretical_edge", report.latest_mean_theoretical_edge)
        _require_none("latest_mean_cost_adjusted_edge", report.latest_mean_cost_adjusted_edge)
        _require_none("latest_mean_edge_cost_drag", report.latest_mean_edge_cost_drag)
        _require_none("latest_total_edge_cost_drag", report.latest_total_edge_cost_drag)
        _require_zero("latest_partial_fill_count", report.latest_partial_fill_count)
        _require_zero(
            "latest_negative_cost_adjusted_edge_count",
            report.latest_negative_cost_adjusted_edge_count,
        )
        _require_none(
            "worst_observed_mean_edge_cost_drag",
            report.worst_observed_mean_edge_cost_drag,
        )
        _require_zero(
            "worst_observed_negative_cost_adjusted_edge_count",
            report.worst_observed_negative_cost_adjusted_edge_count,
        )
        _require_zero(
            "consecutive_negative_cost_adjusted_edge_count",
            report.consecutive_negative_cost_adjusted_edge_count,
        )
        if report.status != "empty_cost_audit_history":
            raise ValueError("status must match cost trend observations")
        return

    if report.first_report_generated_at is None:
        raise ValueError("first_report_generated_at is required when reports exist")
    if report.latest_report_generated_at is None:
        raise ValueError("latest_report_generated_at is required when reports exist")
    if report.latest_report_generated_at > report.generated_at:
        raise ValueError("latest_report_generated_at must not be after generated_at")
    if report.first_report_generated_at > report.generated_at:
        raise ValueError("first_report_generated_at must not be after generated_at")
    if report.status == "empty_cost_audit_history":
        raise ValueError("status must match cost trend observations")
    status_counts = _counts_from_status_rows(report.status_rows)
    if status_counts[report.status] < 1:
        raise ValueError("status_rows must include the latest status")
    if report.latest_negative_cost_adjusted_edge_count > report.latest_trade_count:
        raise ValueError(
            "latest_negative_cost_adjusted_edge_count must not exceed trades",
        )
    if (
        report.worst_observed_negative_cost_adjusted_edge_count
        < report.latest_negative_cost_adjusted_edge_count
    ):
        raise ValueError(
            "worst_observed_negative_cost_adjusted_edge_count cannot be below latest",
        )
    if report.latest_mean_edge_cost_drag is not None:
        if report.worst_observed_mean_edge_cost_drag is None:
            raise ValueError("worst_observed_mean_edge_cost_drag is required")
        if report.worst_observed_mean_edge_cost_drag < report.latest_mean_edge_cost_drag:
            raise ValueError(
                "worst_observed_mean_edge_cost_drag cannot be below latest",
            )
    if report.status == "latest_negative_cost_adjusted_edges":
        if report.latest_negative_cost_adjusted_edge_count == 0:
            raise ValueError("status must match latest negative cost-adjusted edges")
        if report.consecutive_negative_cost_adjusted_edge_count < 1:
            raise ValueError("negative latest report requires a streak")
        if (
            report.consecutive_negative_cost_adjusted_edge_count
            > status_counts["latest_negative_cost_adjusted_edges"]
        ):
            raise ValueError(
                "negative cost-adjusted edge streak must not exceed status rows",
            )
    else:
        if report.latest_negative_cost_adjusted_edge_count != 0:
            raise ValueError("status must match latest negative cost-adjusted edges")
        if report.consecutive_negative_cost_adjusted_edge_count != 0:
            raise ValueError("observed latest report must reset the streak")


def _normalize_status_rows(
    rows: tuple[PaperTradeCostTrendStatusRow, ...],
) -> tuple[PaperTradeCostTrendStatusRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("status_rows must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("status_rows must be an iterable") from exc
    for row in normalized:
        if type(row) is not PaperTradeCostTrendStatusRow:
            raise ValueError("status_rows must contain PaperTradeCostTrendStatusRow values")
    if tuple(row.status for row in normalized) != COST_TREND_STATUSES:
        raise ValueError("status_rows must cover cost trend statuses")
    return normalized


def _counts_from_status_rows(
    rows: tuple[PaperTradeCostTrendStatusRow, ...],
) -> dict[str, int]:
    return {row.status: row.status_count for row in rows}


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


def _require_optional_datetime(field_name: str, value: Any) -> None:
    if value is None:
        return
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime or None")


def _require_optional_decimal(field_name: str, value: Any) -> None:
    if value is None:
        return
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal or None")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")


def _require_optional_probability_decimal(
    field_name: str,
    value: Decimal | None,
) -> None:
    if value is None:
        return
    _require_optional_decimal(field_name, value)
    if value < ZERO or value > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    if (
        value != value.quantize(RATIO_QUANTUM, rounding=ROUND_HALF_EVEN)
        or value.as_tuple().exponent != RATIO_QUANTUM.as_tuple().exponent
    ):
        raise ValueError(f"{field_name} must align to {RATIO_QUANTUM}")


def _require_none(field_name: str, value: Any) -> None:
    if value is not None:
        raise ValueError(f"{field_name} must be None when there are no reports")


def _require_zero(field_name: str, value: int) -> None:
    if value != 0:
        raise ValueError(f"{field_name} must be zero when there are no reports")


__all__ = (
    "PaperTradeCostTrendConfig",
    "PaperTradeCostTrendReport",
    "PaperTradeCostTrendStatusRow",
    "build_paper_trade_cost_trend_report",
)
