"""Paper-only fee schedule reducer.

Pure supplied-input normalization for category/token fee assumptions.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, localcontext


QUANTUM = Decimal("0.000001")
ZERO = Decimal("0")
ONE = Decimal("1")
DECIMAL_CONTEXT = Context(prec=64)
FEE_SCHEDULE_STATUSES = ("pass", "watch", "blocked")
SAFE_FLAGS = ("paper_only", "readonly", "report_only")


@dataclass(frozen=True)
class PaperFeeScheduleRow:
    category: str
    taker_fee_rate: Decimal
    maker_fee_rate: Decimal
    maker_rebate_share: Decimal
    reason_codes: tuple[str, ...]
    flags: tuple[str, ...] = SAFE_FLAGS

    def __post_init__(self) -> None:
        _require_canonical_string("category", self.category)
        object.__setattr__(
            self,
            "taker_fee_rate",
            _normalize_rate("taker_fee_rate", self.taker_fee_rate),
        )
        object.__setattr__(
            self,
            "maker_fee_rate",
            _normalize_rate("maker_fee_rate", self.maker_fee_rate),
        )
        object.__setattr__(
            self,
            "maker_rebate_share",
            _normalize_rate("maker_rebate_share", self.maker_rebate_share),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        object.__setattr__(self, "flags", _normalize_safe_flags(self.flags))


@dataclass(frozen=True)
class PaperFeeScheduleReport:
    generated_at: datetime
    config_version: str
    row_count: int
    max_taker_fee_rate: Decimal
    average_taker_fee_rate: Decimal
    zero_taker_fee_count: int
    fee_schedule_status: str
    reason_codes: tuple[str, ...]
    rows: tuple[PaperFeeScheduleRow, ...]
    flags: tuple[str, ...] = SAFE_FLAGS

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc(self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_nonnegative_int("row_count", self.row_count)
        object.__setattr__(
            self,
            "max_taker_fee_rate",
            _normalize_rate("max_taker_fee_rate", self.max_taker_fee_rate),
        )
        object.__setattr__(
            self,
            "average_taker_fee_rate",
            _normalize_rate("average_taker_fee_rate", self.average_taker_fee_rate),
        )
        _require_nonnegative_int("zero_taker_fee_count", self.zero_taker_fee_count)
        if self.fee_schedule_status not in FEE_SCHEDULE_STATUSES:
            raise ValueError("fee_schedule_status must be pass, watch, or blocked")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(self, "flags", _normalize_safe_flags(self.flags))
        _validate_report_consistency(self)


def build_paper_fee_schedule_report(
    *,
    generated_at: datetime,
    config_version: str,
    rows: Iterable[PaperFeeScheduleRow],
    required_categories: Iterable[str] = (),
) -> PaperFeeScheduleReport:
    if type(generated_at) is not datetime:
        raise ValueError("generated_at must be a datetime")
    _require_canonical_string("config_version", config_version)

    normalized_rows = _normalize_rows(rows)
    _require_unique_categories(normalized_rows)
    sorted_rows = tuple(sorted(normalized_rows, key=lambda row: row.category))
    required = _normalize_categories("required_categories", required_categories)
    missing_required = tuple(
        category
        for category in required
        if category not in {row.category for row in sorted_rows}
    )
    return PaperFeeScheduleReport(
        generated_at=_as_utc(generated_at),
        config_version=config_version,
        row_count=len(sorted_rows),
        max_taker_fee_rate=_max_taker_fee_rate(sorted_rows),
        average_taker_fee_rate=_average_taker_fee_rate(sorted_rows),
        zero_taker_fee_count=_zero_taker_fee_count(sorted_rows),
        fee_schedule_status=_fee_schedule_status(
            rows=sorted_rows,
            missing_required=missing_required,
        ),
        reason_codes=_report_reason_codes(
            rows=sorted_rows,
            missing_required=missing_required,
        ),
        rows=sorted_rows,
    )


def _max_taker_fee_rate(rows: tuple[PaperFeeScheduleRow, ...]) -> Decimal:
    if not rows:
        return _quantize(ZERO)
    return max(row.taker_fee_rate for row in rows)


def _average_taker_fee_rate(rows: tuple[PaperFeeScheduleRow, ...]) -> Decimal:
    if not rows:
        return _quantize(ZERO)
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(
            sum((row.taker_fee_rate for row in rows), ZERO) / Decimal(len(rows)),
        )


def _zero_taker_fee_count(rows: tuple[PaperFeeScheduleRow, ...]) -> int:
    return sum(1 for row in rows if row.taker_fee_rate == _quantize(ZERO))


def _fee_schedule_status(
    *,
    rows: tuple[PaperFeeScheduleRow, ...],
    missing_required: tuple[str, ...],
) -> str:
    if missing_required:
        return "blocked"
    if not rows:
        return "watch"
    return "pass"


def _report_reason_codes(
    *,
    rows: tuple[PaperFeeScheduleRow, ...],
    missing_required: tuple[str, ...],
) -> tuple[str, ...]:
    if missing_required:
        return _normalize_reason_codes(
            (
                "missing_required_fee_categories",
                *(f"missing_required_category:{category}" for category in missing_required),
            ),
        )
    if not rows:
        return ("fee_schedule_empty",)
    return ("fee_schedule_complete",)


def _normalize_rows(
    rows: Iterable[PaperFeeScheduleRow],
) -> tuple[PaperFeeScheduleRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable of PaperFeeScheduleRow values")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable of PaperFeeScheduleRow values") from exc
    for row in normalized:
        if type(row) is not PaperFeeScheduleRow:
            raise ValueError("rows must contain only PaperFeeScheduleRow values")
        _normalize_safe_flags(row.flags)
    return normalized


def _normalize_categories(
    field_name: str,
    values: Iterable[str],
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable of strings")
    try:
        normalized = tuple(values)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable of strings") from exc
    for value in normalized:
        _require_canonical_string(field_name, value)
    return tuple(sorted(set(normalized)))


def _require_unique_categories(rows: tuple[PaperFeeScheduleRow, ...]) -> None:
    seen: set[str] = set()
    for row in rows:
        if row.category in seen:
            raise ValueError("rows must not contain duplicate category values")
        seen.add(row.category)


def _validate_report_consistency(report: PaperFeeScheduleReport) -> None:
    _require_unique_categories(report.rows)
    if report.row_count != len(report.rows):
        raise ValueError("row_count must equal rows length")
    if report.rows != tuple(sorted(report.rows, key=lambda row: row.category)):
        raise ValueError("rows must be sorted by category")
    if report.max_taker_fee_rate != _max_taker_fee_rate(report.rows):
        raise ValueError("max_taker_fee_rate must equal rows")
    if report.average_taker_fee_rate != _average_taker_fee_rate(report.rows):
        raise ValueError("average_taker_fee_rate must equal rows")
    if report.zero_taker_fee_count != _zero_taker_fee_count(report.rows):
        raise ValueError("zero_taker_fee_count must equal rows")
    if report.row_count == 0:
        _require_report_status_and_reason(
            report,
            status="watch",
            reason_code="fee_schedule_empty",
        )
    elif any(
        reason_code.startswith("missing_required_category:")
        for reason_code in report.reason_codes
    ):
        _require_report_status_and_reason(
            report,
            status="blocked",
            reason_code="missing_required_fee_categories",
        )
    elif report.fee_schedule_status != "pass":
        raise ValueError("fee_schedule_status must be pass for complete schedules")
    if report.fee_schedule_status == "pass" and report.reason_codes != (
        "fee_schedule_complete",
    ):
        raise ValueError("pass reports require fee_schedule_complete")


def _require_report_status_and_reason(
    report: PaperFeeScheduleReport,
    *,
    status: str,
    reason_code: str,
) -> None:
    if report.fee_schedule_status != status:
        raise ValueError(f"fee_schedule_status must be {status}")
    if reason_code not in report.reason_codes:
        raise ValueError(f"reason_codes must include {reason_code}")


def _normalize_rate(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized > ONE:
        raise ValueError(f"{field_name} must be at most one")
    return normalized


def _normalize_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _normalize_reason_codes(reason_codes: Iterable[str]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)):
        raise ValueError("reason_codes must be an iterable of strings")
    try:
        normalized = tuple(reason_codes)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable of strings") from exc
    for reason_code in normalized:
        _require_canonical_string("reason_codes", reason_code)
    return tuple(sorted(set(normalized)))


def _normalize_safe_flags(flags: Iterable[str]) -> tuple[str, ...]:
    if isinstance(flags, (str, bytes)):
        raise ValueError("flags must be an iterable of strings")
    try:
        normalized = tuple(flags)
    except TypeError as exc:
        raise ValueError("flags must be an iterable of strings") from exc
    if normalized != SAFE_FLAGS:
        raise ValueError("flags must be exactly paper_only, readonly, report_only")
    return normalized


def _require_canonical_string(field_name: str, value: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_nonnegative_int(field_name: str, value: int) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


def _as_utc(value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError("generated_at must be a datetime")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


__all__ = (
    "PaperFeeScheduleRow",
    "PaperFeeScheduleReport",
    "build_paper_fee_schedule_report",
)
