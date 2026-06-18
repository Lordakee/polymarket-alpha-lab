"""Paper-only cost sensitivity reducer."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal

from polymarket_alpha_lab.cost_aware_event_strategy import (
    PaperCostAwareEventSideResult,
    PaperCostAwareEventStrategyReport,
)


ZERO = Decimal("0")
SIDES = ("yes", "no")
ROW_STATUSES = ("pass", "watch", "blocked")
REPORT_STATUSES = ROW_STATUSES


@dataclass(frozen=True)
class PaperCostSensitivityConfig:
    config_version: str
    min_stressed_net_edge: Decimal
    cost_shock_per_share_values: tuple[Decimal, ...]

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        _require_nonnegative_decimal(
            "min_stressed_net_edge",
            self.min_stressed_net_edge,
        )
        object.__setattr__(
            self,
            "cost_shock_per_share_values",
            _normalize_cost_shocks(self.cost_shock_per_share_values),
        )


@dataclass(frozen=True)
class PaperCostSensitivityRow:
    market_slug: str
    selected_side: str
    base_net_edge_per_share: Decimal | None
    cost_shock_per_share: Decimal
    stressed_net_edge_per_share: Decimal | None
    status: str
    reason_codes: tuple[str, ...]

    def __post_init__(self) -> None:
        _require_canonical_string("market_slug", self.market_slug)
        _require_selected_side("selected_side", self.selected_side)
        _require_optional_finite_decimal(
            "base_net_edge_per_share",
            self.base_net_edge_per_share,
        )
        _require_nonnegative_decimal(
            "cost_shock_per_share",
            self.cost_shock_per_share,
        )
        _require_optional_finite_decimal(
            "stressed_net_edge_per_share",
            self.stressed_net_edge_per_share,
        )
        _require_row_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_string_tuple("reason_codes", self.reason_codes),
        )


@dataclass(frozen=True)
class PaperCostSensitivityReport:
    generated_at: datetime
    config_version: str
    source_report_count: int
    row_count: int
    pass_count: int
    watch_count: int
    blocked_count: int
    status: str
    rows: tuple[PaperCostSensitivityRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc(self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "source_report_count",
            "row_count",
            "pass_count",
            "watch_count",
            "blocked_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        _require_report_status("status", self.status)
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report_consistency(self)
        if self.paper_only is not True:
            raise ValueError("paper_only must be True")
        if self.report_only is not True:
            raise ValueError("report_only must be True")
        if self.readonly is not True:
            raise ValueError("readonly must be True")


def build_paper_cost_sensitivity_report(
    source_reports: object,
    *,
    config: PaperCostSensitivityConfig,
    generated_at: datetime,
) -> PaperCostSensitivityReport:
    if type(config) is not PaperCostSensitivityConfig:
        raise ValueError("config must be a PaperCostSensitivityConfig")
    if type(generated_at) is not datetime:
        raise ValueError("generated_at must be a datetime")

    reports = _normalize_source_reports(source_reports)
    rows = _build_rows(reports, config=config)
    pass_count = _row_status_count(rows, "pass")
    watch_count = _row_status_count(rows, "watch")
    blocked_count = _row_status_count(rows, "blocked")

    return PaperCostSensitivityReport(
        generated_at=generated_at,
        config_version=config.config_version,
        source_report_count=len(reports),
        row_count=len(rows),
        pass_count=pass_count,
        watch_count=watch_count,
        blocked_count=blocked_count,
        status=_overall_status(
            watch_count=watch_count,
            blocked_count=blocked_count,
        ),
        rows=rows,
    )


def _normalize_source_reports(source_reports: object) -> tuple[PaperCostAwareEventStrategyReport, ...]:
    if isinstance(source_reports, (str, bytes)):
        raise ValueError("source reports must be an iterable")
    try:
        reports = tuple(source_reports)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("source reports must be an iterable") from exc
    for report in reports:
        if type(report) is not PaperCostAwareEventStrategyReport:
            raise ValueError(
                "source reports must contain PaperCostAwareEventStrategyReport values",
            )
        if report.paper_only is not True:
            raise ValueError("source reports must contain paper_only reports")
        if report.report_only is not True:
            raise ValueError("source reports must contain report_only reports")
    return reports


def _build_rows(
    reports: tuple[PaperCostAwareEventStrategyReport, ...],
    *,
    config: PaperCostSensitivityConfig,
) -> tuple[PaperCostSensitivityRow, ...]:
    rows = tuple(
        row
        for report in reports
        for shock in config.cost_shock_per_share_values
        for row in (_row_for_report(report, shock, config.min_stressed_net_edge),)
    )
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                row.market_slug,
                row.selected_side,
                row.cost_shock_per_share,
            ),
        ),
    )


def _row_for_report(
    report: PaperCostAwareEventStrategyReport,
    shock: Decimal,
    min_stressed_net_edge: Decimal,
) -> PaperCostSensitivityRow:
    if report.selected_side not in SIDES:
        return PaperCostSensitivityRow(
            market_slug=report.market_slug,
            selected_side=report.selected_side,
            base_net_edge_per_share=None,
            cost_shock_per_share=shock,
            stressed_net_edge_per_share=None,
            status="blocked",
            reason_codes=("missing_selected_side",),
        )

    side_result = _selected_result(report)
    base_net_edge = side_result.net_edge_per_share
    if base_net_edge is None:
        return PaperCostSensitivityRow(
            market_slug=report.market_slug,
            selected_side=report.selected_side,
            base_net_edge_per_share=None,
            cost_shock_per_share=shock,
            stressed_net_edge_per_share=None,
            status="blocked",
            reason_codes=("missing_base_net_edge",),
        )

    stressed_net_edge = base_net_edge - shock
    if stressed_net_edge >= min_stressed_net_edge:
        return PaperCostSensitivityRow(
            market_slug=report.market_slug,
            selected_side=report.selected_side,
            base_net_edge_per_share=base_net_edge,
            cost_shock_per_share=shock,
            stressed_net_edge_per_share=stressed_net_edge,
            status="pass",
            reason_codes=("stressed_net_edge_ready",),
        )
    return PaperCostSensitivityRow(
        market_slug=report.market_slug,
        selected_side=report.selected_side,
        base_net_edge_per_share=base_net_edge,
        cost_shock_per_share=shock,
        stressed_net_edge_per_share=stressed_net_edge,
        status="watch",
        reason_codes=("stressed_net_edge_below_minimum",),
    )


def _selected_result(
    report: PaperCostAwareEventStrategyReport,
) -> PaperCostAwareEventSideResult:
    if report.selected_side == "yes":
        return report.yes_result
    return report.no_result


def _row_status_count(
    rows: tuple[PaperCostSensitivityRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _overall_status(*, watch_count: int, blocked_count: int) -> str:
    if blocked_count > 0:
        return "blocked"
    if watch_count > 0:
        return "watch"
    return "pass"


def _validate_report_consistency(report: PaperCostSensitivityReport) -> None:
    if report.row_count != len(report.rows):
        raise ValueError("row_count must match rows")
    if report.pass_count != _row_status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _row_status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.blocked_count != _row_status_count(report.rows, "blocked"):
        raise ValueError("blocked_count must match rows")
    if report.pass_count + report.watch_count + report.blocked_count != report.row_count:
        raise ValueError("row status counts must sum to row_count")
    if report.status != _overall_status(
        watch_count=report.watch_count,
        blocked_count=report.blocked_count,
    ):
        raise ValueError("status must match row statuses")


def _normalize_cost_shocks(value: object) -> tuple[Decimal, ...]:
    if type(value) is not tuple:
        raise ValueError("cost_shock_per_share_values must be a tuple")
    if not value:
        raise ValueError("cost_shock_per_share_values must not be empty")
    for shock in value:
        _require_nonnegative_decimal("cost_shock_per_share_values", shock)
    normalized = tuple(sorted(value))
    if len(set(normalized)) != len(normalized):
        raise ValueError("cost_shock_per_share_values must be unique")
    return normalized


def _normalize_rows(value: object) -> tuple[PaperCostSensitivityRow, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        rows = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for row in rows:
        if type(row) is not PaperCostSensitivityRow:
            raise ValueError("rows must contain PaperCostSensitivityRow values")
    row_keys = tuple(
        (row.market_slug, row.selected_side, row.cost_shock_per_share)
        for row in rows
    )
    if row_keys != tuple(sorted(row_keys)):
        raise ValueError("rows must be sorted by market_slug, selected_side, and shock")
    return rows


def _normalize_string_tuple(field_name: str, value: object) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable of strings")
    try:
        items = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable of strings") from exc
    if not items:
        raise ValueError(f"{field_name} must contain at least one value")
    for item in items:
        _require_canonical_string(field_name, item)
    return items


def _as_utc(value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError("datetime value is required")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_nonnegative_int(field_name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_finite_decimal(field_name: str, value: object) -> None:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")


def _require_optional_finite_decimal(field_name: str, value: object) -> None:
    if value is not None:
        _require_finite_decimal(field_name, value)


def _require_nonnegative_decimal(field_name: str, value: object) -> None:
    _require_finite_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_selected_side(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be yes, no, or none")
    if value not in ("yes", "no", "none"):
        raise ValueError(f"{field_name} must be yes, no, or none")


def _require_row_status(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a known cost sensitivity row status")
    if value not in ROW_STATUSES:
        raise ValueError(f"{field_name} must be a known cost sensitivity row status")


def _require_report_status(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a known cost sensitivity status")
    if value not in REPORT_STATUSES:
        raise ValueError(f"{field_name} must be a known cost sensitivity status")


__all__ = (
    "PaperCostSensitivityConfig",
    "PaperCostSensitivityReport",
    "PaperCostSensitivityRow",
    "build_paper_cost_sensitivity_report",
)
