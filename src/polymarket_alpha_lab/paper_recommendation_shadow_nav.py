"""Pure paper-only shadow NAV impact report for recommendation allocations."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal


__all__ = (
    "PaperRecommendationShadowNavAllocationRow",
    "PaperRecommendationShadowNavConfig",
    "PaperRecommendationShadowNavReport",
    "build_paper_recommendation_shadow_nav_report",
)


ZERO = Decimal("0")
ONE = Decimal("1")
NOTIONAL_QUANTUM = Decimal("0.000001")
RATIO_QUANTUM = Decimal("0.000001")
VALID_SIDES = ("yes", "no")
STATUSES = ("pass", "watch", "blocked")
PASS_REASON_CODE = "shadow_nav_impact_passed"
BLOCKING_REASON_CODES = (
    "nav_at_risk_limit_exceeded",
    "expected_drawdown_limit_exceeded",
)
WATCH_REASON_CODES = (
    "near_nav_at_risk_limit",
    "near_expected_drawdown_limit",
)
WATCH_THRESHOLD = Decimal("0.95")


@dataclass(frozen=True)
class PaperRecommendationShadowNavAllocationRow:
    market_slug: str
    side: str
    allocated_paper_notional: Decimal
    max_loss_notional: Decimal
    expected_value_notional: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("market_slug", self.market_slug)
        if type(self.side) is not str or self.side not in VALID_SIDES:
            raise ValueError("side must be yes or no")
        _require_notional("allocated_paper_notional", self.allocated_paper_notional)
        _require_notional("max_loss_notional", self.max_loss_notional)
        _require_net_notional(
            "expected_value_notional",
            self.expected_value_notional,
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_row_reason_codes(self.reason_codes),
        )
        _validate_hard_flags("allocation row", self)


@dataclass(frozen=True)
class PaperRecommendationShadowNavConfig:
    nav_notional: Decimal
    max_nav_at_risk_ratio: Decimal
    max_expected_drawdown_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_notional("nav_notional", self.nav_notional)
        if self.nav_notional <= ZERO:
            raise ValueError("nav_notional must be positive")
        _require_ratio("max_nav_at_risk_ratio", self.max_nav_at_risk_ratio)
        _require_ratio(
            "max_expected_drawdown_ratio",
            self.max_expected_drawdown_ratio,
        )
        _validate_hard_flags("config", self)


@dataclass(frozen=True)
class PaperRecommendationShadowNavReport:
    generated_at: datetime
    status: str
    reason_codes: tuple[str, ...]
    total_allocated_notional: Decimal
    total_max_loss_notional: Decimal
    total_expected_value_notional: Decimal
    nav_at_risk_ratio: Decimal
    expected_drawdown_ratio: Decimal
    row_count: int
    nav_notional: Decimal
    max_nav_at_risk_ratio: Decimal
    max_expected_drawdown_ratio: Decimal
    allocation_rows: tuple[PaperRecommendationShadowNavAllocationRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc(self.generated_at))
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_report_reason_codes(self.reason_codes),
        )
        _require_notional("total_allocated_notional", self.total_allocated_notional)
        _require_notional("total_max_loss_notional", self.total_max_loss_notional)
        _require_net_notional(
            "total_expected_value_notional",
            self.total_expected_value_notional,
        )
        _require_nonnegative_ratio_value("nav_at_risk_ratio", self.nav_at_risk_ratio)
        _require_nonnegative_ratio_value(
            "expected_drawdown_ratio",
            self.expected_drawdown_ratio,
        )
        _require_nonnegative_int("row_count", self.row_count)
        _require_notional("nav_notional", self.nav_notional)
        if self.nav_notional <= ZERO:
            raise ValueError("nav_notional must be positive")
        _require_ratio("max_nav_at_risk_ratio", self.max_nav_at_risk_ratio)
        _require_ratio(
            "max_expected_drawdown_ratio",
            self.max_expected_drawdown_ratio,
        )
        object.__setattr__(
            self,
            "allocation_rows",
            _normalize_allocation_rows(self.allocation_rows),
        )
        _validate_report_consistency(self)
        _validate_hard_flags("report", self)


def build_paper_recommendation_shadow_nav_report(
    allocation_rows: object,
    *,
    config: PaperRecommendationShadowNavConfig,
    generated_at: datetime,
) -> PaperRecommendationShadowNavReport:
    if type(config) is not PaperRecommendationShadowNavConfig:
        raise ValueError("config must be a PaperRecommendationShadowNavConfig")
    _validate_hard_flags("config", config)
    generated_at = _as_utc(generated_at)
    rows = _normalize_allocation_rows(allocation_rows)
    total_allocated_notional = _sum_notional(
        row.allocated_paper_notional for row in rows
    )
    total_max_loss_notional = _sum_notional(row.max_loss_notional for row in rows)
    total_expected_value_notional = _sum_net_notional(
        row.expected_value_notional for row in rows
    )
    nav_at_risk_ratio = _ratio(total_max_loss_notional, config.nav_notional)
    expected_drawdown_ratio = _ratio(
        _expected_drawdown_notional(total_expected_value_notional),
        config.nav_notional,
    )
    reason_codes = _reason_codes(
        nav_at_risk_ratio=nav_at_risk_ratio,
        expected_drawdown_ratio=expected_drawdown_ratio,
        max_nav_at_risk_ratio=config.max_nav_at_risk_ratio,
        max_expected_drawdown_ratio=config.max_expected_drawdown_ratio,
    )
    return PaperRecommendationShadowNavReport(
        generated_at=generated_at,
        status=_status_from_reason_codes(reason_codes),
        reason_codes=reason_codes,
        total_allocated_notional=total_allocated_notional,
        total_max_loss_notional=total_max_loss_notional,
        total_expected_value_notional=total_expected_value_notional,
        nav_at_risk_ratio=nav_at_risk_ratio,
        expected_drawdown_ratio=expected_drawdown_ratio,
        row_count=len(rows),
        nav_notional=config.nav_notional,
        max_nav_at_risk_ratio=config.max_nav_at_risk_ratio,
        max_expected_drawdown_ratio=config.max_expected_drawdown_ratio,
        allocation_rows=rows,
    )


def _normalize_allocation_rows(
    allocation_rows: object,
) -> tuple[PaperRecommendationShadowNavAllocationRow, ...]:
    if isinstance(allocation_rows, (str, bytes)):
        raise ValueError("allocation rows must be an iterable")
    try:
        rows = tuple(allocation_rows)
    except TypeError as exc:
        raise ValueError("allocation rows must be an iterable") from exc
    return tuple(_normalize_allocation_row(row) for row in rows)


def _normalize_allocation_row(
    row: object,
) -> PaperRecommendationShadowNavAllocationRow:
    _validate_hard_flags("allocation rows", row)
    if type(row) is PaperRecommendationShadowNavAllocationRow:
        return row
    return PaperRecommendationShadowNavAllocationRow(
        market_slug=_row_attr(row, "market_slug"),
        side=_row_attr(row, "side"),
        allocated_paper_notional=_row_attr(row, "allocated_paper_notional"),
        max_loss_notional=_row_attr(row, "max_loss_notional"),
        expected_value_notional=_row_attr(row, "expected_value_notional"),
        reason_codes=_row_attr(row, "reason_codes"),
    )


def _row_attr(row: object, field_name: str) -> object:
    if not hasattr(row, field_name):
        raise ValueError(f"{field_name} is required")
    return getattr(row, field_name)


def _validate_report_consistency(report: PaperRecommendationShadowNavReport) -> None:
    if report.row_count != len(report.allocation_rows):
        raise ValueError("row_count must match allocation rows")
    total_allocated_notional = _sum_notional(
        row.allocated_paper_notional for row in report.allocation_rows
    )
    if report.total_allocated_notional != total_allocated_notional:
        raise ValueError("total_allocated_notional must match allocation rows")
    total_max_loss_notional = _sum_notional(
        row.max_loss_notional for row in report.allocation_rows
    )
    if report.total_max_loss_notional != total_max_loss_notional:
        raise ValueError("total_max_loss_notional must match allocation rows")
    total_expected_value_notional = _sum_net_notional(
        row.expected_value_notional for row in report.allocation_rows
    )
    if report.total_expected_value_notional != total_expected_value_notional:
        raise ValueError("total_expected_value_notional must match allocation rows")
    expected_nav_at_risk_ratio = _ratio(
        report.total_max_loss_notional,
        report.nav_notional,
    )
    if report.nav_at_risk_ratio != expected_nav_at_risk_ratio:
        raise ValueError("nav_at_risk_ratio must match total_max_loss_notional")
    expected_expected_drawdown_ratio = _ratio(
        _expected_drawdown_notional(report.total_expected_value_notional),
        report.nav_notional,
    )
    if report.expected_drawdown_ratio != expected_expected_drawdown_ratio:
        raise ValueError(
            "expected_drawdown_ratio must match total_expected_value_notional",
        )
    expected_reason_codes = _reason_codes(
        nav_at_risk_ratio=report.nav_at_risk_ratio,
        expected_drawdown_ratio=report.expected_drawdown_ratio,
        max_nav_at_risk_ratio=report.max_nav_at_risk_ratio,
        max_expected_drawdown_ratio=report.max_expected_drawdown_ratio,
    )
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match shadow NAV metrics")
    if report.status != _status_from_reason_codes(report.reason_codes):
        raise ValueError("status must match reason_codes")


def _reason_codes(
    *,
    nav_at_risk_ratio: Decimal,
    expected_drawdown_ratio: Decimal,
    max_nav_at_risk_ratio: Decimal,
    max_expected_drawdown_ratio: Decimal,
) -> tuple[str, ...]:
    blocking_reason_codes = (
        ("nav_at_risk_limit_exceeded",)
        if nav_at_risk_ratio > max_nav_at_risk_ratio
        else ()
    ) + (
        ("expected_drawdown_limit_exceeded",)
        if expected_drawdown_ratio > max_expected_drawdown_ratio
        else ()
    )
    if blocking_reason_codes:
        return blocking_reason_codes
    watch_reason_codes = (
        ("near_nav_at_risk_limit",)
        if nav_at_risk_ratio >= _quantize_ratio(max_nav_at_risk_ratio * WATCH_THRESHOLD)
        else ()
    ) + (
        ("near_expected_drawdown_limit",)
        if expected_drawdown_ratio
        >= _quantize_ratio(max_expected_drawdown_ratio * WATCH_THRESHOLD)
        else ()
    )
    if watch_reason_codes:
        return watch_reason_codes
    return (PASS_REASON_CODE,)


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in BLOCKING_REASON_CODES for reason_code in reason_codes):
        return "blocked"
    if any(reason_code in WATCH_REASON_CODES for reason_code in reason_codes):
        return "watch"
    return "pass"


def _sum_notional(values: object) -> Decimal:
    return _quantize_notional(sum(values, ZERO))


def _sum_net_notional(values: object) -> Decimal:
    return _quantize_net_notional(sum(values, ZERO))


def _expected_drawdown_notional(expected_value_notional: Decimal) -> Decimal:
    if expected_value_notional >= ZERO:
        return _quantize_notional(ZERO)
    return _quantize_notional(-expected_value_notional)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= ZERO:
        raise ValueError("nav_notional must be positive")
    return _quantize_ratio(numerator / denominator)


def _as_utc(value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError("generated_at must be a datetime")
    if value.tzinfo is None:
        return datetime(
            value.year,
            value.month,
            value.day,
            value.hour,
            value.minute,
            value.second,
            value.microsecond,
            tzinfo=UTC,
            fold=value.fold,
        )
    return value.astimezone(UTC)


def _validate_hard_flags(field_name: str, value: object) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if hasattr(value, flag_name) and getattr(value, flag_name) is not True:
            raise ValueError(f"{field_name} must be {flag_name}")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _require_decimal(field_name: str, value: object) -> None:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")


def _require_finite_decimal(field_name: str, value: object) -> None:
    _require_decimal(field_name, value)
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")


def _require_nonnegative_decimal(field_name: str, value: object) -> None:
    _require_finite_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_net_notional(field_name: str, value: object) -> None:
    _require_finite_decimal(field_name, value)
    if value != _quantize_net_notional(value):
        raise ValueError(f"{field_name} must be quantized to 0.000001")


def _require_notional(field_name: str, value: object) -> None:
    _require_nonnegative_decimal(field_name, value)
    if value != _quantize_notional(value):
        raise ValueError(f"{field_name} must be quantized to 0.000001")


def _require_ratio(field_name: str, value: object) -> None:
    _require_nonnegative_decimal(field_name, value)
    if value > ONE:
        raise ValueError(f"{field_name} must be at most 1")
    if value != _quantize_ratio(value):
        raise ValueError(f"{field_name} must be quantized to 0.000001")


def _require_nonnegative_ratio_value(field_name: str, value: object) -> None:
    _require_nonnegative_decimal(field_name, value)
    if value != _quantize_ratio(value):
        raise ValueError(f"{field_name} must be quantized to 0.000001")


def _require_nonnegative_int(field_name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


def _normalize_row_reason_codes(value: object) -> tuple[str, ...]:
    reason_codes = _normalize_reason_code_values(value)
    if not reason_codes:
        raise ValueError("reason_codes must contain at least one value")
    return reason_codes


def _normalize_report_reason_codes(value: object) -> tuple[str, ...]:
    reason_codes = _normalize_reason_code_values(value)
    if not reason_codes:
        raise ValueError("reason_codes must contain at least one value")
    allowed_reason_codes = set(BLOCKING_REASON_CODES) | set(WATCH_REASON_CODES) | {
        PASS_REASON_CODE,
    }
    for reason_code in reason_codes:
        if reason_code not in allowed_reason_codes:
            raise ValueError("reason_codes must match shadow NAV metrics")
    return reason_codes


def _normalize_reason_code_values(value: object) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_codes must be an iterable of strings")
    try:
        reason_codes = tuple(value)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable of strings") from exc
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError("reason_codes must not contain duplicates")
    for reason_code in reason_codes:
        _require_canonical_string("reason_codes", reason_code)
    return reason_codes


def _quantize_notional(value: Decimal) -> Decimal:
    _require_nonnegative_decimal("notional", value)
    return value.quantize(NOTIONAL_QUANTUM)


def _quantize_net_notional(value: Decimal) -> Decimal:
    _require_finite_decimal("notional", value)
    return value.quantize(NOTIONAL_QUANTUM)


def _quantize_ratio(value: Decimal) -> Decimal:
    _require_nonnegative_decimal("ratio", value)
    return value.quantize(RATIO_QUANTUM)
