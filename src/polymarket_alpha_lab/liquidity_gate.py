"""Paper-only liquidity gate over cost-aware strategy reports.

This module is a pure reducer: it only summarizes already-built
``PaperCostAwareEventStrategyReport`` values and is side-effect free.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from polymarket_alpha_lab.cost_aware_event_strategy import (
    PaperCostAwareEventSideResult,
    PaperCostAwareEventStrategyReport,
)


ZERO = Decimal("0")
LIQUIDITY_GATE_STATUSES = ("pass", "watch", "blocked")
SELECTED_SIDES = ("yes", "no", "none")
STATUS_SEVERITY = {"blocked": 0, "watch": 1, "pass": 2}
ROW_REASON_CODES = (
    "liquidity_ready",
    "wide_spread",
    "missing_selected_side",
    "missing_selected_ask_size",
    "insufficient_selected_ask_size",
)
REPORT_REASON_CODES = (
    "empty_input",
    "insufficient_depth_ready_count",
    "too_many_missing_depth",
    "row_level_liquidity_block",
    "liquidity_gate_watch",
    "liquidity_gate_passed",
)


@dataclass(frozen=True)
class PaperLiquidityGateConfig:
    config_version: str
    max_spread: Decimal = Decimal("0.0500")
    min_ask_size: Decimal = Decimal("1.0000")
    min_depth_ready_count: int = 1
    max_missing_depth_count: int = 0

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        _require_nonnegative_decimal("max_spread", self.max_spread)
        _require_positive_decimal("min_ask_size", self.min_ask_size)
        _require_positive_int("min_depth_ready_count", self.min_depth_ready_count)
        _require_nonnegative_int("max_missing_depth_count", self.max_missing_depth_count)


@dataclass(frozen=True)
class PaperLiquidityGateRow:
    market_slug: str
    selected_side: str
    spread: Decimal
    selected_ask_size: Decimal | None
    status: str
    reason_codes: tuple[str, ...]

    def __post_init__(self) -> None:
        _require_canonical_string("market_slug", self.market_slug)
        _require_canonical_string("selected_side", self.selected_side)
        if self.selected_side not in SELECTED_SIDES:
            raise ValueError("selected_side must be yes, no, or none")
        _require_nonnegative_decimal("spread", self.spread)
        _require_optional_nonnegative_decimal(
            "selected_ask_size",
            self.selected_ask_size,
        )
        if self.status not in LIQUIDITY_GATE_STATUSES:
            raise ValueError("status must be pass, watch, or blocked")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_string_tuple("reason_codes", self.reason_codes),
        )


@dataclass(frozen=True)
class PaperLiquidityGateReport:
    generated_at: datetime
    config_version: str
    status: str
    reason_codes: tuple[str, ...]
    market_count: int
    pass_count: int
    watch_count: int
    blocked_count: int
    depth_ready_count: int
    missing_depth_count: int
    rows: tuple[PaperLiquidityGateRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc(self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_canonical_string("status", self.status)
        if self.status not in LIQUIDITY_GATE_STATUSES:
            raise ValueError("status must be pass, watch, or blocked")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_string_tuple("reason_codes", self.reason_codes),
        )
        for field_name in (
            "market_count",
            "pass_count",
            "watch_count",
            "blocked_count",
            "depth_ready_count",
            "missing_depth_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report_consistency(self)
        if self.paper_only is not True:
            raise ValueError("paper_only must be True")
        if self.report_only is not True:
            raise ValueError("report_only must be True")
        if self.readonly is not True:
            raise ValueError("readonly must be True")


def build_paper_liquidity_gate_report(
    reports: Iterable[PaperCostAwareEventStrategyReport],
    *,
    config: PaperLiquidityGateConfig,
    generated_at: datetime,
) -> PaperLiquidityGateReport:
    """Reduce cost-aware strategy reports into a paper liquidity gate report."""

    if type(config) is not PaperLiquidityGateConfig:
        raise ValueError("config must be a PaperLiquidityGateConfig")

    cost_aware_reports = _normalize_cost_aware_reports(reports)
    rows = tuple(
        sorted(
            (_row_from_report(report, config) for report in cost_aware_reports),
            key=_row_sort_key,
        ),
    )
    pass_count = sum(1 for row in rows if row.status == "pass")
    watch_count = sum(1 for row in rows if row.status == "watch")
    blocked_count = sum(1 for row in rows if row.status == "blocked")
    depth_ready_count = sum(1 for row in rows if _row_has_ready_depth(row, config))
    missing_depth_count = sum(1 for row in rows if row.selected_ask_size is None)
    reason_codes = _report_reason_codes(
        market_count=len(rows),
        depth_ready_count=depth_ready_count,
        missing_depth_count=missing_depth_count,
        blocked_count=blocked_count,
        watch_count=watch_count,
        config=config,
    )
    status = "blocked" if _has_blocking_reason(reason_codes) else (
        "watch" if watch_count > 0 else "pass"
    )

    return PaperLiquidityGateReport(
        generated_at=generated_at,
        config_version=config.config_version,
        status=status,
        reason_codes=reason_codes,
        market_count=len(rows),
        pass_count=pass_count,
        watch_count=watch_count,
        blocked_count=blocked_count,
        depth_ready_count=depth_ready_count,
        missing_depth_count=missing_depth_count,
        rows=rows,
    )


def _row_from_report(
    report: PaperCostAwareEventStrategyReport,
    config: PaperLiquidityGateConfig,
) -> PaperLiquidityGateRow:
    selected_result = _selected_side_result(report)
    selected_ask_size = (
        None if selected_result is None else selected_result.ask_size
    )
    status, reason_codes = _row_status(
        selected_side=report.selected_side,
        spread=report.spread,
        selected_ask_size=selected_ask_size,
        config=config,
    )
    return PaperLiquidityGateRow(
        market_slug=report.market_slug,
        selected_side=report.selected_side,
        spread=report.spread,
        selected_ask_size=selected_ask_size,
        status=status,
        reason_codes=reason_codes,
    )


def _selected_side_result(
    report: PaperCostAwareEventStrategyReport,
) -> PaperCostAwareEventSideResult | None:
    if report.selected_side == "yes":
        return report.yes_result
    if report.selected_side == "no":
        return report.no_result
    return None


def _row_status(
    *,
    selected_side: str,
    spread: Decimal,
    selected_ask_size: Decimal | None,
    config: PaperLiquidityGateConfig,
) -> tuple[str, tuple[str, ...]]:
    if selected_side == "none":
        return "blocked", ("missing_selected_side",)
    if selected_ask_size is None:
        return "blocked", ("missing_selected_ask_size",)
    if selected_ask_size < config.min_ask_size:
        return "blocked", ("insufficient_selected_ask_size",)
    if spread > config.max_spread:
        return "watch", ("wide_spread",)
    return "pass", ("liquidity_ready",)


def _report_reason_codes(
    *,
    market_count: int,
    depth_ready_count: int,
    missing_depth_count: int,
    blocked_count: int,
    watch_count: int,
    config: PaperLiquidityGateConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if market_count == 0:
        reason_codes.append("empty_input")
    if depth_ready_count < config.min_depth_ready_count:
        reason_codes.append("insufficient_depth_ready_count")
    if missing_depth_count > config.max_missing_depth_count:
        reason_codes.append("too_many_missing_depth")
    if not reason_codes and blocked_count > 0:
        reason_codes.append("row_level_liquidity_block")
    if reason_codes:
        return tuple(reason_codes)
    if watch_count > 0:
        return ("liquidity_gate_watch",)
    return ("liquidity_gate_passed",)


def _has_blocking_reason(reason_codes: tuple[str, ...]) -> bool:
    return any(
        reason_code
        in {
            "empty_input",
            "insufficient_depth_ready_count",
            "row_level_liquidity_block",
            "too_many_missing_depth",
        }
        for reason_code in reason_codes
    )


def _row_has_ready_depth(
    row: PaperLiquidityGateRow,
    config: PaperLiquidityGateConfig,
) -> bool:
    return row.selected_ask_size is not None and row.selected_ask_size >= config.min_ask_size


def _row_sort_key(row: PaperLiquidityGateRow) -> tuple[int, str]:
    return STATUS_SEVERITY[row.status], row.market_slug


def _normalize_cost_aware_reports(
    reports: Iterable[PaperCostAwareEventStrategyReport],
) -> tuple[PaperCostAwareEventStrategyReport, ...]:
    if isinstance(reports, (str, bytes)):
        raise ValueError("reports must be an iterable of cost-aware reports")
    try:
        normalized = tuple(reports)
    except TypeError as exc:
        raise ValueError("reports must be an iterable of cost-aware reports") from exc
    for report in normalized:
        if type(report) is not PaperCostAwareEventStrategyReport:
            raise ValueError(
                "reports must contain only PaperCostAwareEventStrategyReport values",
            )
        if report.paper_only is not True:
            raise ValueError("reports must contain paper_only cost-aware reports")
        if report.report_only is not True:
            raise ValueError("reports must contain report_only cost-aware reports")
    return normalized


def _validate_report_consistency(report: PaperLiquidityGateReport) -> None:
    if report.market_count != len(report.rows):
        raise ValueError("market_count must match rows")
    if report.pass_count != sum(1 for row in report.rows if row.status == "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != sum(1 for row in report.rows if row.status == "watch"):
        raise ValueError("watch_count must match rows")
    if report.blocked_count != sum(1 for row in report.rows if row.status == "blocked"):
        raise ValueError("blocked_count must match rows")
    if report.depth_ready_count != sum(
        1 for row in report.rows if _row_counts_as_depth_ready(row)
    ):
        raise ValueError("depth_ready_count must match rows")
    if report.missing_depth_count != sum(
        1 for row in report.rows if row.selected_ask_size is None
    ):
        raise ValueError("missing_depth_count must match rows")
    for row in report.rows:
        _validate_row_semantics(row)
    if report.blocked_count > 0 and report.status == "pass":
        raise ValueError("status must not pass with blocked rows")
    _validate_report_reason_codes(report)


def _validate_row_semantics(row: PaperLiquidityGateRow) -> None:
    for reason_code in row.reason_codes:
        if reason_code not in ROW_REASON_CODES:
            raise ValueError("rows reason_codes must match liquidity gate semantics")
    if row.status in ("pass", "watch") and row.selected_side == "none":
        raise ValueError("rows selected_side must match row status")
    if row.status in ("pass", "watch") and row.selected_ask_size is None:
        raise ValueError("rows selected_ask_size must match row status")
    if row.status == "pass":
        if row.reason_codes != ("liquidity_ready",):
            raise ValueError("rows reason_codes must match row status")
    elif row.status == "watch":
        if row.reason_codes != ("wide_spread",):
            raise ValueError("rows reason_codes must match row status")
    elif row.selected_side == "none":
        if row.reason_codes != ("missing_selected_side",):
            raise ValueError("rows reason_codes must match selected_side")
    elif row.selected_ask_size is None:
        if row.reason_codes != ("missing_selected_ask_size",):
            raise ValueError("rows reason_codes must match selected_ask_size")
    elif row.reason_codes != ("insufficient_selected_ask_size",):
        raise ValueError("rows reason_codes must match row status")


def _row_counts_as_depth_ready(row: PaperLiquidityGateRow) -> bool:
    return row.status in ("pass", "watch")


def _validate_report_reason_codes(report: PaperLiquidityGateReport) -> None:
    for reason_code in report.reason_codes:
        if reason_code not in REPORT_REASON_CODES:
            raise ValueError("reason_codes must match liquidity gate semantics")
    if len(set(report.reason_codes)) != len(report.reason_codes):
        raise ValueError("reason_codes must match liquidity gate semantics")

    if report.market_count == 0:
        if report.reason_codes != ("empty_input", "insufficient_depth_ready_count"):
            raise ValueError("reason_codes must match empty input")
        expected_status = "blocked"
    elif "empty_input" in report.reason_codes:
        raise ValueError("reason_codes must match market_count")
    elif _has_blocking_reason(report.reason_codes):
        _validate_blocking_report_reason_codes(report)
        expected_status = "blocked"
    elif report.depth_ready_count == 0:
        raise ValueError("reason_codes must include insufficient_depth_ready_count")
    elif report.blocked_count > 0:
        raise ValueError("reason_codes must include row_level_liquidity_block")
    elif report.watch_count > 0:
        if report.reason_codes != ("liquidity_gate_watch",):
            raise ValueError("reason_codes must match watch rows")
        expected_status = "watch"
    else:
        if report.reason_codes != ("liquidity_gate_passed",):
            raise ValueError("reason_codes must match passing rows")
        expected_status = "pass"

    if report.status != expected_status:
        raise ValueError("status must match reason_codes")


def _validate_blocking_report_reason_codes(report: PaperLiquidityGateReport) -> None:
    if "row_level_liquidity_block" in report.reason_codes:
        if report.reason_codes != ("row_level_liquidity_block",):
            raise ValueError("reason_codes must match liquidity gate semantics")
        if report.blocked_count == 0:
            raise ValueError("reason_codes must match blocked rows")
        if report.depth_ready_count == 0:
            raise ValueError("reason_codes must include insufficient_depth_ready_count")
        return

    expected_reason_codes: list[str] = []
    if "insufficient_depth_ready_count" in report.reason_codes:
        expected_reason_codes.append("insufficient_depth_ready_count")
    elif report.depth_ready_count == 0:
        raise ValueError("reason_codes must include insufficient_depth_ready_count")

    if "too_many_missing_depth" in report.reason_codes:
        if report.missing_depth_count == 0:
            raise ValueError("reason_codes must match missing_depth_count")
        expected_reason_codes.append("too_many_missing_depth")

    if report.reason_codes != tuple(expected_reason_codes):
        raise ValueError("reason_codes must match liquidity gate semantics")


def _normalize_rows(
    rows: tuple[PaperLiquidityGateRow, ...],
) -> tuple[PaperLiquidityGateRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for row in normalized:
        if type(row) is not PaperLiquidityGateRow:
            raise ValueError("rows must contain PaperLiquidityGateRow values")
    if normalized != tuple(sorted(normalized, key=_row_sort_key)):
        raise ValueError("rows must be ordered by status severity then market_slug")
    return normalized


def _as_utc(value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError("generated_at must be a datetime")
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


def _require_decimal(field_name: str, value: Any) -> None:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")


def _require_nonnegative_decimal(field_name: str, value: Any) -> None:
    _require_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_positive_decimal(field_name: str, value: Any) -> None:
    _require_decimal(field_name, value)
    if value <= ZERO:
        raise ValueError(f"{field_name} must be positive")


def _require_optional_nonnegative_decimal(field_name: str, value: Any) -> None:
    if value is None:
        return
    _require_nonnegative_decimal(field_name, value)


def _normalize_string_tuple(field_name: str, value: tuple[str, ...]) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable of strings")
    try:
        normalized = tuple(value)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable of strings") from exc
    if not normalized:
        raise ValueError(f"{field_name} must contain at least one value")
    for item in normalized:
        _require_canonical_string(field_name, item)
    return normalized


__all__ = (
    "PaperLiquidityGateConfig",
    "PaperLiquidityGateReport",
    "PaperLiquidityGateRow",
    "build_paper_liquidity_gate_report",
)
