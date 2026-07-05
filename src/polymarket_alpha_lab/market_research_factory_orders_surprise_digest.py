"""Read-only Factory Orders surprise digest for Phase 1 research."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


DEFAULT_FACTORY_ORDERS_SURPRISE_DIGEST_CONFIG_VERSION = (
    "factory-orders-surprise-digest-v0"
)
FACTORY_ORDERS_SERIES_IDS = (
    "factory_orders_total",
    "factory_orders_ex_transportation",
    "factory_orders_capital_goods",
)
DIGEST_STATUSES = ("blocked", "clear", "watch")
SURPRISE_DIRECTIONS = ("negative", "neutral", "positive")
ROW_REASON_CODES = (
    "factory_orders_negative_surprise",
    "factory_orders_neutral_surprise",
    "factory_orders_positive_surprise",
    "factory_orders_watch_surprise",
)
REPORT_REASON_CODES = (
    "factory_orders_no_inputs",
    "factory_orders_no_surprises",
    "factory_orders_positive_surprises",
    "factory_orders_negative_surprises",
    "factory_orders_mixed_surprises",
    "factory_orders_watch_surprise",
)

COUNT_QUANTUM = Decimal("0.000001")
VALUE_QUANTUM = Decimal("0.000001")
RATIO_QUANTUM = Decimal("0.000001")
ZERO_COUNT = Decimal("0.000000")
ZERO_VALUE = Decimal("0.000000")
ZERO_RATIO = Decimal("0.000000")
ONE_COUNT = Decimal("1.000000")
ONE_RATIO = Decimal("1.000000")
WATCH_SURPRISE_RATIO = Decimal("0.020000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)


@dataclass(frozen=True)
class FactoryOrdersSurpriseDigestConfig:
    config_version: str = DEFAULT_FACTORY_ORDERS_SURPRISE_DIGEST_CONFIG_VERSION
    watch_surprise_ratio: Decimal = WATCH_SURPRISE_RATIO
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "FactoryOrdersSurpriseDigestConfig does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(self, FactoryOrdersSurpriseDigestConfig, "config")
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "watch_surprise_ratio",
            _normalize_abs_ratio("watch_surprise_ratio", self.watch_surprise_ratio),
        )
        reject_unsafe_surface_fields("factory orders surprise digest config", self)
        require_paper_only_flags("FactoryOrdersSurpriseDigestConfig", self)


@dataclass(frozen=True)
class FactoryOrdersSurpriseInput:
    series_id: str
    period: str
    actual_value: Decimal
    consensus_value: Decimal
    prior_value: Decimal
    source_row_count: Decimal
    released_at: datetime
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError("FactoryOrdersSurpriseInput does not support subclassing")

    def __post_init__(self) -> None:
        _require_exact_type(self, FactoryOrdersSurpriseInput, "input")
        _require_series_id("series_id", self.series_id)
        _require_period("period", self.period)
        for field_name in ("actual_value", "consensus_value", "prior_value"):
            object.__setattr__(
                self,
                field_name,
                _normalize_value(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "source_row_count",
            _normalize_positive_count("source_row_count", self.source_row_count),
        )
        object.__setattr__(self, "released_at", _as_utc("released_at", self.released_at))
        if self.consensus_value == ZERO_VALUE:
            raise ValueError("consensus_value must not be zero")
        reject_unsafe_surface_fields("factory orders surprise input", self)
        require_paper_only_flags("FactoryOrdersSurpriseInput", self)


@dataclass(frozen=True)
class FactoryOrdersSurpriseDigestRow:
    series_id: str
    period: str
    actual_value: Decimal
    consensus_value: Decimal
    prior_value: Decimal
    surprise_value: Decimal
    surprise_ratio: Decimal
    prior_revision_value: Decimal
    surprise_direction: str
    source_row_count: Decimal
    released_at: datetime
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError("FactoryOrdersSurpriseDigestRow does not support subclassing")

    def __post_init__(self) -> None:
        _require_exact_type(self, FactoryOrdersSurpriseDigestRow, "row")
        _require_series_id("series_id", self.series_id)
        _require_period("period", self.period)
        for field_name in (
            "actual_value",
            "consensus_value",
            "prior_value",
            "surprise_value",
            "prior_revision_value",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_value(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "surprise_ratio",
            _normalize_signed_ratio("surprise_ratio", self.surprise_ratio),
        )
        _require_member("surprise_direction", self.surprise_direction, SURPRISE_DIRECTIONS)
        object.__setattr__(
            self,
            "source_row_count",
            _normalize_positive_count("source_row_count", self.source_row_count),
        )
        object.__setattr__(self, "released_at", _as_utc("released_at", self.released_at))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _validate_row(self)
        reject_unsafe_surface_fields("factory orders surprise digest row", self)
        require_paper_only_flags("FactoryOrdersSurpriseDigestRow", self)


@dataclass(frozen=True)
class FactoryOrdersSurpriseReasonCodeCount:
    reason_code: str
    count: Decimal
    series_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "FactoryOrdersSurpriseReasonCodeCount does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            FactoryOrdersSurpriseReasonCodeCount,
            "reason code count",
        )
        _require_member("reason_code", self.reason_code, REPORT_REASON_CODES)
        object.__setattr__(
            self,
            "count",
            _normalize_positive_count("count", self.count),
        )
        object.__setattr__(
            self,
            "series_ratio",
            _normalize_ratio("series_ratio", self.series_ratio),
        )
        reject_unsafe_surface_fields("factory orders surprise reason code count", self)
        require_paper_only_flags("FactoryOrdersSurpriseReasonCodeCount", self)


@dataclass(frozen=True)
class FactoryOrdersSurpriseDigestReport:
    generated_at: datetime
    config_version: str
    source_row_count: Decimal
    series_count: Decimal
    positive_surprise_count: Decimal
    negative_surprise_count: Decimal
    neutral_surprise_count: Decimal
    max_abs_surprise_ratio: Decimal
    digest_status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[FactoryOrdersSurpriseReasonCodeCount, ...]
    rows: tuple[FactoryOrdersSurpriseDigestRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError("FactoryOrdersSurpriseDigestReport does not support subclassing")

    def __post_init__(self) -> None:
        _require_exact_type(self, FactoryOrdersSurpriseDigestReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "source_row_count",
            "series_count",
            "positive_surprise_count",
            "negative_surprise_count",
            "neutral_surprise_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_abs_surprise_ratio",
            _normalize_abs_ratio("max_abs_surprise_ratio", self.max_abs_surprise_ratio),
        )
        _require_member("digest_status", self.digest_status, DIGEST_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODES,
            ),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report(self)
        reject_unsafe_surface_fields("factory orders surprise digest report", self)
        require_paper_only_flags("FactoryOrdersSurpriseDigestReport", self)


def build_market_research_factory_orders_surprise_digest(
    inputs: list[FactoryOrdersSurpriseInput] | tuple[FactoryOrdersSurpriseInput, ...],
    *,
    config: FactoryOrdersSurpriseDigestConfig,
    generated_at: datetime,
) -> FactoryOrdersSurpriseDigestReport:
    if type(config) is not FactoryOrdersSurpriseDigestConfig:
        raise ValueError("config must be a FactoryOrdersSurpriseDigestConfig")
    require_paper_only_flags("config", config)
    rows = tuple(
        sorted(
            (_digest_row(row, config) for row in _normalize_inputs(inputs)),
            key=_row_sort_key,
        ),
    )
    reason_codes = _report_reason_codes(rows, config)
    return FactoryOrdersSurpriseDigestReport(
        generated_at=_as_utc("generated_at", generated_at),
        config_version=config.config_version,
        source_row_count=_sum_rows(rows, "source_row_count"),
        series_count=_count(len(rows)),
        positive_surprise_count=_direction_count(rows, "positive"),
        negative_surprise_count=_direction_count(rows, "negative"),
        neutral_surprise_count=_direction_count(rows, "neutral"),
        max_abs_surprise_ratio=_max_abs_surprise_ratio(rows),
        digest_status=_digest_status(rows, config),
        reason_codes=reason_codes,
        reason_code_counts=_reason_code_counts(reason_codes, rows),
        rows=rows,
    )


def market_research_factory_orders_surprise_digest_payload(
    report: FactoryOrdersSurpriseDigestReport,
) -> dict[str, Any]:
    if type(report) is not FactoryOrdersSurpriseDigestReport:
        raise ValueError("report must be a FactoryOrdersSurpriseDigestReport")
    require_paper_only_flags("report", report)
    reject_unsafe_surface_fields("factory orders surprise digest report", report)
    return json_ready_no_floats(report)


def _normalize_inputs(
    inputs: list[FactoryOrdersSurpriseInput] | tuple[FactoryOrdersSurpriseInput, ...],
) -> tuple[FactoryOrdersSurpriseInput, ...]:
    if type(inputs) not in (list, tuple):
        raise ValueError("inputs must be a list or tuple")
    rows = tuple(inputs)
    seen_keys: set[tuple[str, str]] = set()
    for row in rows:
        if type(row) is not FactoryOrdersSurpriseInput:
            raise ValueError("inputs must contain FactoryOrdersSurpriseInput values")
        require_paper_only_flags("input", row)
        key = (row.series_id, row.period)
        if key in seen_keys:
            raise ValueError("inputs must not contain duplicate series_id period values")
        seen_keys.add(key)
    return rows


def _digest_row(
    row: FactoryOrdersSurpriseInput,
    config: FactoryOrdersSurpriseDigestConfig,
) -> FactoryOrdersSurpriseDigestRow:
    surprise_value = _normalize_value("surprise_value", row.actual_value - row.consensus_value)
    surprise_ratio = _normalize_signed_ratio(
        "surprise_ratio",
        surprise_value / abs(row.consensus_value),
    )
    prior_revision_value = _normalize_value(
        "prior_revision_value",
        row.actual_value - row.prior_value,
    )
    direction = _surprise_direction(surprise_value)
    return FactoryOrdersSurpriseDigestRow(
        series_id=row.series_id,
        period=row.period,
        actual_value=row.actual_value,
        consensus_value=row.consensus_value,
        prior_value=row.prior_value,
        surprise_value=surprise_value,
        surprise_ratio=surprise_ratio,
        prior_revision_value=prior_revision_value,
        surprise_direction=direction,
        source_row_count=row.source_row_count,
        released_at=row.released_at,
        reason_codes=_row_reason_codes(direction, surprise_ratio, config),
    )


def _row_reason_codes(
    direction: str,
    surprise_ratio: Decimal,
    config: FactoryOrdersSurpriseDigestConfig,
) -> tuple[str, ...]:
    codes = [f"factory_orders_{direction}_surprise"]
    if abs(surprise_ratio) >= config.watch_surprise_ratio and direction != "neutral":
        codes.append("factory_orders_watch_surprise")
    return tuple(codes)


def _report_reason_codes(
    rows: tuple[FactoryOrdersSurpriseDigestRow, ...],
    config: FactoryOrdersSurpriseDigestConfig,
) -> tuple[str, ...]:
    if not rows:
        return ("factory_orders_no_inputs",)
    if all(row.surprise_direction == "neutral" for row in rows):
        return ("factory_orders_no_surprises",)
    directions = frozenset(row.surprise_direction for row in rows)
    codes: list[str] = []
    if "positive" in directions and "negative" in directions:
        codes.append("factory_orders_mixed_surprises")
    elif "positive" in directions:
        codes.append("factory_orders_positive_surprises")
    elif "negative" in directions:
        codes.append("factory_orders_negative_surprises")
    if _digest_status(rows, config) == "watch":
        codes.append("factory_orders_watch_surprise")
    return tuple(codes)


def _row_sort_key(row: FactoryOrdersSurpriseDigestRow) -> tuple[Decimal, str, str]:
    return (-abs(row.surprise_ratio), row.series_id, row.period)


def _digest_status(
    rows: tuple[FactoryOrdersSurpriseDigestRow, ...],
    config: FactoryOrdersSurpriseDigestConfig,
) -> str:
    if not rows:
        return "blocked"
    if any(abs(row.surprise_ratio) >= config.watch_surprise_ratio for row in rows):
        return "watch"
    return "clear"


def _surprise_direction(surprise_value: Decimal) -> str:
    if surprise_value > ZERO_VALUE:
        return "positive"
    if surprise_value < ZERO_VALUE:
        return "negative"
    return "neutral"


def _max_abs_surprise_ratio(rows: tuple[FactoryOrdersSurpriseDigestRow, ...]) -> Decimal:
    if not rows:
        return ZERO_RATIO
    return _normalize_abs_ratio(
        "max_abs_surprise_ratio",
        max(abs(row.surprise_ratio) for row in rows),
    )


def _sum_rows(rows: tuple[FactoryOrdersSurpriseDigestRow, ...], field_name: str) -> Decimal:
    return _normalize_nonnegative_count(
        field_name,
        sum((getattr(row, field_name) for row in rows), ZERO_COUNT),
    )


def _direction_count(
    rows: tuple[FactoryOrdersSurpriseDigestRow, ...],
    direction: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.surprise_direction == direction))


def _reason_code_counts(
    reason_codes: tuple[str, ...],
    rows: tuple[FactoryOrdersSurpriseDigestRow, ...],
) -> tuple[FactoryOrdersSurpriseReasonCodeCount, ...]:
    if reason_codes == ("factory_orders_no_inputs",):
        return (
            FactoryOrdersSurpriseReasonCodeCount(
                reason_code="factory_orders_no_inputs",
                count=ONE_COUNT,
                series_ratio=ZERO_RATIO,
            ),
        )
    series_count = _count(len(rows))
    return tuple(
        FactoryOrdersSurpriseReasonCodeCount(
            reason_code=reason_code,
            count=_report_reason_row_count(reason_code, rows),
            series_ratio=_ratio(
                _report_reason_row_count(reason_code, rows),
                series_count,
            ),
        )
        for reason_code in reason_codes
    )


def _report_reason_row_count(
    reason_code: str,
    rows: tuple[FactoryOrdersSurpriseDigestRow, ...],
) -> Decimal:
    if reason_code == "factory_orders_no_surprises":
        return _direction_count(rows, "neutral")
    if reason_code == "factory_orders_positive_surprises":
        return _direction_count(rows, "positive")
    if reason_code == "factory_orders_negative_surprises":
        return _direction_count(rows, "negative")
    if reason_code == "factory_orders_mixed_surprises":
        return _count(
            sum(
                1
                for row in rows
                if row.surprise_direction in ("positive", "negative")
            ),
        )
    if reason_code == "factory_orders_watch_surprise":
        return _count(
            sum(
                1
                for row in rows
                if "factory_orders_watch_surprise" in row.reason_codes
            ),
        )
    raise ValueError(f"reason_code must be one of {REPORT_REASON_CODES}")


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO_COUNT:
        return ZERO_RATIO
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(RATIO_QUANTUM)


def _count(value: int) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return Decimal(value).quantize(COUNT_QUANTUM)


def _validate_row(row: FactoryOrdersSurpriseDigestRow) -> None:
    if row.consensus_value == ZERO_VALUE:
        raise ValueError("consensus_value must not be zero")
    if row.surprise_value != _normalize_value(
        "surprise_value",
        row.actual_value - row.consensus_value,
    ):
        raise ValueError("surprise_value must match actual_value less consensus_value")
    if row.surprise_ratio != _normalize_signed_ratio(
        "surprise_ratio",
        row.surprise_value / abs(row.consensus_value),
    ):
        raise ValueError("surprise_ratio must match surprise_value over consensus_value")
    if row.prior_revision_value != _normalize_value(
        "prior_revision_value",
        row.actual_value - row.prior_value,
    ):
        raise ValueError("prior_revision_value must match actual_value less prior_value")
    if row.surprise_direction != _surprise_direction(row.surprise_value):
        raise ValueError("surprise_direction must match surprise_value")


def _validate_report(report: FactoryOrdersSurpriseDigestReport) -> None:
    if not report.rows and report.reason_codes != ("factory_orders_no_inputs",):
        raise ValueError("reason_codes must use no_inputs for empty rows")
    if report.rows and "factory_orders_no_inputs" in report.reason_codes:
        raise ValueError("reason_codes must not include no_inputs when rows are present")
    if report.digest_status != _digest_status_from_reason_codes(report.reason_codes):
        raise ValueError("digest_status must match reason_codes")
    if report.series_count != _count(len(report.rows)):
        raise ValueError("series_count must match rows")
    if report.source_row_count != _sum_rows(report.rows, "source_row_count"):
        raise ValueError("source_row_count must match rows")
    for field_name, direction in (
        ("positive_surprise_count", "positive"),
        ("negative_surprise_count", "negative"),
        ("neutral_surprise_count", "neutral"),
    ):
        if getattr(report, field_name) != _direction_count(report.rows, direction):
            raise ValueError(f"{field_name} must match rows")
    if report.max_abs_surprise_ratio != _max_abs_surprise_ratio(report.rows):
        raise ValueError("max_abs_surprise_ratio must match rows")
    if report.rows != tuple(sorted(report.rows, key=_row_sort_key)):
        raise ValueError("rows must use deterministic ordering")
    if report.reason_code_counts != _reason_code_counts(
        report.reason_codes,
        report.rows,
    ):
        raise ValueError("reason_code_counts must match reason_codes")


def _digest_status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == ("factory_orders_no_inputs",):
        return "blocked"
    if "factory_orders_watch_surprise" in reason_codes:
        return "watch"
    return "clear"


def _normalize_rows(value: object) -> tuple[FactoryOrdersSurpriseDigestRow, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("rows must be a tuple")
    try:
        rows = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("rows must be a tuple") from exc
    seen_keys: set[tuple[str, str]] = set()
    for row in rows:
        if type(row) is not FactoryOrdersSurpriseDigestRow:
            raise ValueError("rows must contain FactoryOrdersSurpriseDigestRow values")
        require_paper_only_flags("row", row)
        key = (row.series_id, row.period)
        if key in seen_keys:
            raise ValueError("rows must not contain duplicate series_id period values")
        seen_keys.add(key)
    return rows


def _normalize_reason_code_counts(
    value: object,
) -> tuple[FactoryOrdersSurpriseReasonCodeCount, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    reason_code_counts = tuple(value)
    seen_reason_codes: set[str] = set()
    for reason_code_count in reason_code_counts:
        if type(reason_code_count) is not FactoryOrdersSurpriseReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain FactoryOrdersSurpriseReasonCodeCount values",
            )
        require_paper_only_flags("reason code count", reason_code_count)
        if reason_code_count.reason_code in seen_reason_codes:
            raise ValueError("reason_code_counts must be unique")
        seen_reason_codes.add(reason_code_count.reason_code)
    expected_order = tuple(
        reason_code
        for reason_code in REPORT_REASON_CODES
        if reason_code in seen_reason_codes
    )
    if tuple(item.reason_code for item in reason_code_counts) != expected_order:
        raise ValueError("reason_code_counts must use deterministic ordering")
    return reason_code_counts


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError(f"{field_name} must not be empty")
    for reason_code in reason_codes:
        _require_member(field_name, reason_code, allowed)
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError(f"{field_name} must be unique")
    if tuple(code for code in allowed if code in reason_codes) != reason_codes:
        raise ValueError(f"{field_name} must be deterministic")
    return reason_codes


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    integral = value.to_integral_value(rounding=ROUND_HALF_EVEN)
    if integral != value:
        raise ValueError(f"{field_name} must be integral")
    with localcontext(DECIMAL_CONTEXT):
        quantized = integral.quantize(COUNT_QUANTUM)
    if quantized < ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    if quantized == ZERO_COUNT:
        return ZERO_COUNT
    return quantized


def _normalize_positive_count(field_name: str, value: object) -> Decimal:
    quantized = _normalize_nonnegative_count(field_name, value)
    if quantized == ZERO_COUNT:
        raise ValueError(f"{field_name} must be positive")
    return quantized


def _normalize_value(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(VALUE_QUANTUM)


def _normalize_signed_ratio(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(RATIO_QUANTUM)


def _normalize_abs_ratio(field_name: str, value: object) -> Decimal:
    ratio = _normalize_signed_ratio(field_name, value)
    if ratio < ZERO_RATIO:
        raise ValueError(f"{field_name} must be nonnegative")
    return ratio


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    ratio = _normalize_abs_ratio(field_name, value)
    if ratio > ONE_RATIO:
        raise ValueError(f"{field_name} must not exceed one")
    return ratio


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_series_id(field_name: str, value: object) -> None:
    _require_member(field_name, value, FACTORY_ORDERS_SERIES_IDS)


def _require_period(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    parts = value.split("-")
    if len(parts) != 2 or len(parts[0]) != 4 or len(parts[1]) != 2:
        raise ValueError(f"{field_name} must use YYYY-MM")
    year_text, month_text = parts
    if not year_text.isdecimal() or not month_text.isdecimal():
        raise ValueError(f"{field_name} must use YYYY-MM")
    month = int(month_text)
    if month < 1 or month > 12:
        raise ValueError(f"{field_name} must use YYYY-MM")


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed}")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exact {expected_type.__name__}")


__all__ = (
    "DEFAULT_FACTORY_ORDERS_SURPRISE_DIGEST_CONFIG_VERSION",
    "FACTORY_ORDERS_SERIES_IDS",
    "FactoryOrdersSurpriseDigestConfig",
    "FactoryOrdersSurpriseDigestReport",
    "FactoryOrdersSurpriseDigestRow",
    "FactoryOrdersSurpriseInput",
    "FactoryOrdersSurpriseReasonCodeCount",
    "build_market_research_factory_orders_surprise_digest",
    "market_research_factory_orders_surprise_digest_payload",
)
