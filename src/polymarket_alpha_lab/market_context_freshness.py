"""Pure paper-only market context freshness reports.

This module reduces caller-supplied PaperCostAwareEventStrategyReport values
into a deterministic freshness report. It performs no file IO, network access,
privileged secret handling, custody handling, placement actions, execution, or
trade instructions.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from polymarket_alpha_lab.cost_aware_event_strategy import (
    PaperCostAwareEventStrategyReport,
)


__all__ = (
    "PaperMarketContextFreshnessConfig",
    "PaperMarketContextFreshnessReport",
    "PaperMarketContextFreshnessRow",
    "build_paper_market_context_freshness_report",
)


ROW_STATUSES = ("pass", "watch", "blocked")
REPORT_STATUSES = ("pass", "watch", "blocked")
SEVERITY_WEIGHT = {"blocked": 0, "watch": 1, "pass": 2}


@dataclass(frozen=True)
class PaperMarketContextFreshnessConfig:
    config_version: str
    max_report_age_seconds: int
    min_context_count: int

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        _require_positive_int(
            "max_report_age_seconds",
            self.max_report_age_seconds,
        )
        _require_positive_int("min_context_count", self.min_context_count)


@dataclass(frozen=True)
class PaperMarketContextFreshnessRow:
    market_slug: str
    report_generated_at: datetime
    report_age_seconds: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("market_slug", self.market_slug)
        object.__setattr__(
            self,
            "report_generated_at",
            _as_utc(self.report_generated_at, field_name="report_generated_at"),
        )
        _require_nonnegative_decimal("report_age_seconds", self.report_age_seconds)
        if type(self.status) is not str or self.status not in ROW_STATUSES:
            raise ValueError("status must be a known market context freshness status")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        if self.paper_only is not True:
            raise ValueError("paper_only must be True")
        if self.report_only is not True:
            raise ValueError("report_only must be True")
        if self.readonly is not True:
            raise ValueError("readonly must be True")


@dataclass(frozen=True)
class PaperMarketContextFreshnessReport:
    generated_at: datetime
    config_version: str
    max_report_age_seconds: int
    min_context_count: int
    context_count: int
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[PaperMarketContextFreshnessRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "generated_at",
            _as_utc(self.generated_at, field_name="generated_at"),
        )
        _require_canonical_string("config_version", self.config_version)
        _require_positive_int(
            "max_report_age_seconds",
            self.max_report_age_seconds,
        )
        _require_positive_int("min_context_count", self.min_context_count)
        _require_nonnegative_int("context_count", self.context_count)
        if type(self.status) is not str or self.status not in REPORT_STATUSES:
            raise ValueError("status must be a known market context freshness status")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(self, "rows", _clone_rows(self.rows))
        _validate_report_consistency(self)
        if self.paper_only is not True:
            raise ValueError("paper_only must be True")
        if self.report_only is not True:
            raise ValueError("report_only must be True")
        if self.readonly is not True:
            raise ValueError("readonly must be True")


def build_paper_market_context_freshness_report(
    reports: tuple[PaperCostAwareEventStrategyReport, ...]
    | list[PaperCostAwareEventStrategyReport],
    *,
    config: PaperMarketContextFreshnessConfig,
    generated_at: datetime,
) -> PaperMarketContextFreshnessReport:
    if type(config) is not PaperMarketContextFreshnessConfig:
        raise ValueError("config must be a PaperMarketContextFreshnessConfig")
    generated_at_utc = _as_utc(generated_at, field_name="generated_at")
    source_reports = _normalize_reports(reports)
    rows = tuple(
        sorted(
            (
                _row_from_report(
                    source_report,
                    generated_at=generated_at_utc,
                    max_report_age_seconds=config.max_report_age_seconds,
                )
                for source_report in source_reports
            ),
            key=lambda row: (SEVERITY_WEIGHT[row.status], row.market_slug),
        ),
    )
    status = _report_status(
        rows,
        context_count=len(source_reports),
        min_context_count=config.min_context_count,
    )
    return PaperMarketContextFreshnessReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        max_report_age_seconds=config.max_report_age_seconds,
        min_context_count=config.min_context_count,
        context_count=len(source_reports),
        status=status,
        reason_codes=_report_reason_codes(
            rows,
            status=status,
            context_count=len(source_reports),
            min_context_count=config.min_context_count,
        ),
        rows=rows,
    )


def _row_from_report(
    report: PaperCostAwareEventStrategyReport,
    *,
    generated_at: datetime,
    max_report_age_seconds: int,
) -> PaperMarketContextFreshnessRow:
    report_generated_at = _as_utc(
        report.generated_at,
        field_name="report_generated_at",
    )
    if report_generated_at > generated_at:
        raise ValueError("report_generated_at must not be in the future")
    delta = generated_at - report_generated_at
    age_seconds = (
        Decimal(delta.days * 86_400)
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / Decimal("1000000"))
    )
    status = _row_status(
        age_seconds,
        max_report_age_seconds=max_report_age_seconds,
    )
    return PaperMarketContextFreshnessRow(
        market_slug=report.market_slug,
        report_generated_at=report_generated_at,
        report_age_seconds=age_seconds,
        status=status,
        reason_codes=(_row_reason_code(status),),
    )


def _row_status(
    report_age_seconds: Decimal,
    *,
    max_report_age_seconds: int,
) -> str:
    max_age = Decimal(max_report_age_seconds)
    if report_age_seconds <= max_age:
        return "pass"
    if report_age_seconds <= max_age * Decimal(2):
        return "watch"
    return "blocked"


def _row_reason_code(status: str) -> str:
    if status == "pass":
        return "fresh_market_context"
    if status == "watch":
        return "stale_market_context"
    return "expired_market_context"


def _report_status(
    rows: tuple[PaperMarketContextFreshnessRow, ...],
    *,
    context_count: int,
    min_context_count: int,
) -> str:
    if context_count < min_context_count:
        return "blocked"
    if any(row.status == "blocked" for row in rows):
        return "blocked"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[PaperMarketContextFreshnessRow, ...],
    *,
    status: str,
    context_count: int,
    min_context_count: int,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if context_count == 0:
        reason_codes.append("no_market_context")
    if context_count < min_context_count:
        reason_codes.append("insufficient_market_context")
    if status == "blocked" and not reason_codes:
        reason_codes.append("blocked_market_context")
    elif status == "watch":
        reason_codes.append("stale_market_context")
    elif status == "pass":
        reason_codes.append("market_context_fresh")
    return tuple(reason_codes)


def _normalize_reports(
    reports: tuple[PaperCostAwareEventStrategyReport, ...]
    | list[PaperCostAwareEventStrategyReport],
) -> tuple[PaperCostAwareEventStrategyReport, ...]:
    if isinstance(reports, (str, bytes)) or type(reports) not in (list, tuple):
        raise ValueError("reports must be a list or tuple")
    items = tuple(reports)
    for item in items:
        if type(item) is not PaperCostAwareEventStrategyReport:
            raise ValueError(
                "reports must contain PaperCostAwareEventStrategyReport values",
            )
        if item.paper_only is not True:
            raise ValueError("reports must contain paper_only PaperCostAwareEventStrategyReport values")
        if item.report_only is not True:
            raise ValueError("reports must contain report_only PaperCostAwareEventStrategyReport values")
    return items


def _clone_rows(
    rows: tuple[PaperMarketContextFreshnessRow, ...],
) -> tuple[PaperMarketContextFreshnessRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        items = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for item in items:
        if type(item) is not PaperMarketContextFreshnessRow:
            raise ValueError(
                "rows must contain PaperMarketContextFreshnessRow values",
            )
    return tuple(
        PaperMarketContextFreshnessRow(
            market_slug=row.market_slug,
            report_generated_at=row.report_generated_at,
            report_age_seconds=row.report_age_seconds,
            status=row.status,
            reason_codes=row.reason_codes,
            paper_only=row.paper_only,
            report_only=row.report_only,
            readonly=row.readonly,
        )
        for row in items
    )


def _validate_report_consistency(report: PaperMarketContextFreshnessReport) -> None:
    if report.context_count != len(report.rows):
        raise ValueError("context_count must match rows")
    for row in report.rows:
        expected_status = _row_status(
            row.report_age_seconds,
            max_report_age_seconds=report.max_report_age_seconds,
        )
        if row.status != expected_status:
            raise ValueError("row status must match report age")
        expected_reason_codes = (_row_reason_code(expected_status),)
        if row.reason_codes != expected_reason_codes:
            raise ValueError("row reason_codes must match row status")
    expected_status = _report_status(
        report.rows,
        context_count=report.context_count,
        min_context_count=report.min_context_count,
    )
    if report.status != expected_status:
        raise ValueError("status must match market context freshness state")
    expected_reason_codes = _report_reason_codes(
        report.rows,
        status=report.status,
        context_count=report.context_count,
        min_context_count=report.min_context_count,
    )
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match market context freshness state")
    row_keys = tuple((SEVERITY_WEIGHT[row.status], row.market_slug) for row in report.rows)
    if row_keys != tuple(sorted(row_keys)):
        raise ValueError("rows must use deterministic severity and market sorting")


def _as_utc(value: datetime, *, field_name: str) -> datetime:
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
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value <= 0:
        raise ValueError(f"{field_name} must be positive")


def _require_nonnegative_decimal(field_name: str, value: Any) -> None:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < Decimal(0):
        raise ValueError(f"{field_name} must be nonnegative")


def _normalize_reason_codes(
    field_name: str,
    values: tuple[str, ...],
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable of strings")
    try:
        items = tuple(values)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable of strings") from exc
    if not items:
        raise ValueError(f"{field_name} must contain at least one value")
    for item in items:
        _require_canonical_string(field_name, item)
    return items
