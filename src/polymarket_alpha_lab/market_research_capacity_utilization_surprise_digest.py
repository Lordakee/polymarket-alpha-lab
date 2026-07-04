from __future__ import annotations

from dataclasses import dataclass, field, fields, is_dataclass
from datetime import UTC, datetime
from decimal import ROUND_DOWN, ROUND_HALF_EVEN, Decimal
from typing import Any


DEFAULT_CAPACITY_UTILIZATION_SURPRISE_DIGEST_CONFIG_VERSION = (
    "capacity-utilization-surprise-v1"
)
RATIO_QUANT = Decimal("0.000001")
ZERO = Decimal("0")
ONE = Decimal("1")

_SURPRISE_DIRECTIONS = ("negative", "inline", "positive")
_DIGEST_STATUSES = ("blocked", "pass", "watch")
_REASON_CODES = (
    "capacity_utilization_surprise_digest_empty",
    "capacity_utilization_surprise_negative_present",
    "capacity_utilization_surprise_no_surprises",
    "capacity_utilization_surprise_positive_present",
    "capacity_utilization_surprise_probability_edge_present",
)
_WATCH_NEXT_STEP = "review_capacity_utilization_surprise_markets"
_EMPTY_NEXT_STEP = "collect_capacity_utilization_surprise_inputs"
_PASS_NEXT_STEP = "continue_capacity_utilization_surprise_monitoring"


@dataclass(frozen=True)
class CapacityUtilizationSurpriseDigestConfig:
    config_version: str = DEFAULT_CAPACITY_UTILIZATION_SURPRISE_DIGEST_CONFIG_VERSION
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        _require_hard_flags("CapacityUtilizationSurpriseDigestConfig", self)


@dataclass(frozen=True)
class CapacityUtilizationSurpriseInput:
    market_id: str
    release_at: datetime
    actual_utilization_rate: Decimal
    consensus_utilization_rate: Decimal
    previous_utilization_rate: Decimal
    market_probability: Decimal
    threshold_probability: Decimal
    source_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "market_id", _normalize_market_id(self.market_id))
        object.__setattr__(self, "release_at", _as_utc("release_at", self.release_at))
        for field_name in (
            "actual_utilization_rate",
            "consensus_utilization_rate",
            "previous_utilization_rate",
            "market_probability",
            "threshold_probability",
            "source_count",
        ):
            _require_decimal(field_name, getattr(self, field_name))
        for field_name in (
            "actual_utilization_rate",
            "consensus_utilization_rate",
            "previous_utilization_rate",
        ):
            _require_positive_rate(field_name, getattr(self, field_name))
        for field_name in ("market_probability", "threshold_probability"):
            _require_probability(field_name, getattr(self, field_name))
        _require_integral_decimal("source_count", self.source_count)
        _require_nonnegative_decimal("source_count", self.source_count)
        _require_hard_flags("CapacityUtilizationSurpriseInput", self)


@dataclass(frozen=True)
class CapacityUtilizationSurpriseRow:
    market_id: str
    release_at: datetime
    actual_utilization_rate: Decimal
    consensus_utilization_rate: Decimal
    previous_utilization_rate: Decimal
    market_probability: Decimal
    threshold_probability: Decimal
    source_count: Decimal
    surprise_direction: str
    surprise_rate_points: Decimal
    surprise_ratio: Decimal
    market_probability_edge: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "market_id", _normalize_market_id(self.market_id))
        object.__setattr__(self, "release_at", _as_utc("release_at", self.release_at))
        for field_name in (
            "actual_utilization_rate",
            "consensus_utilization_rate",
            "previous_utilization_rate",
            "market_probability",
            "threshold_probability",
            "source_count",
            "surprise_rate_points",
            "surprise_ratio",
            "market_probability_edge",
        ):
            _require_decimal(field_name, getattr(self, field_name))
        for field_name in (
            "actual_utilization_rate",
            "consensus_utilization_rate",
            "previous_utilization_rate",
        ):
            _require_positive_rate(field_name, getattr(self, field_name))
        for field_name in ("market_probability", "threshold_probability"):
            _require_probability(field_name, getattr(self, field_name))
        _require_surprise_direction("surprise_direction", self.surprise_direction)
        _require_integral_decimal("source_count", self.source_count)
        _require_nonnegative_decimal("source_count", self.source_count)
        _validate_row_consistency(self)
        _require_hard_flags("CapacityUtilizationSurpriseRow", self)


@dataclass(frozen=True)
class CapacityUtilizationSurpriseDigestReport:
    generated_at: datetime
    config_version: str
    digest_status: str
    recommended_next_step: str
    input_count: Decimal
    positive_surprise_count: Decimal
    negative_surprise_count: Decimal
    inline_count: Decimal
    total_source_count: Decimal
    surprise_rows: tuple[CapacityUtilizationSurpriseRow, ...]
    reason_codes: tuple[str, ...]
    positive_surprise_ratio: Decimal | None = field(init=False)
    negative_surprise_ratio: Decimal | None = field(init=False)
    market_probability_edge_ratio: Decimal | None = field(init=False)
    largest_abs_surprise_market_id: str | None = field(init=False)
    largest_abs_surprise_ratio: Decimal | None = field(init=False)
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_digest_status("digest_status", self.digest_status)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        for field_name in (
            "input_count",
            "positive_surprise_count",
            "negative_surprise_count",
            "inline_count",
            "total_source_count",
        ):
            _require_integral_decimal(field_name, getattr(self, field_name))
            _require_nonnegative_decimal(field_name, getattr(self, field_name))
        object.__setattr__(self, "surprise_rows", _normalize_surprise_rows(self.surprise_rows))
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _set_report_derived_fields(self)
        _require_hard_flags("CapacityUtilizationSurpriseDigestReport", self)
        _validate_report_consistency(self)


def build_market_research_capacity_utilization_surprise_digest(
    inputs: list[CapacityUtilizationSurpriseInput]
    | tuple[CapacityUtilizationSurpriseInput, ...],
    *,
    config: CapacityUtilizationSurpriseDigestConfig,
    generated_at: datetime,
) -> CapacityUtilizationSurpriseDigestReport:
    if type(config) is not CapacityUtilizationSurpriseDigestConfig:
        raise ValueError("config must be a CapacityUtilizationSurpriseDigestConfig")
    _require_hard_flags("CapacityUtilizationSurpriseDigestConfig", config)
    normalized_inputs = _normalize_inputs(inputs)
    rows = tuple(_surprise_row(item) for item in sorted(normalized_inputs, key=_input_sort_key))
    reason_codes = _reason_codes(rows)
    return CapacityUtilizationSurpriseDigestReport(
        generated_at=_as_utc("generated_at", generated_at),
        config_version=config.config_version,
        digest_status=_digest_status(reason_codes),
        recommended_next_step=_recommended_next_step(reason_codes),
        input_count=Decimal(len(rows)),
        positive_surprise_count=Decimal(
            sum(1 for row in rows if row.surprise_direction == "positive"),
        ),
        negative_surprise_count=Decimal(
            sum(1 for row in rows if row.surprise_direction == "negative"),
        ),
        inline_count=Decimal(sum(1 for row in rows if row.surprise_direction == "inline")),
        total_source_count=sum((row.source_count for row in rows), ZERO),
        surprise_rows=rows,
        reason_codes=reason_codes,
    )


def market_research_capacity_utilization_surprise_digest_payload(
    report: CapacityUtilizationSurpriseDigestReport,
) -> dict[str, Any]:
    if type(report) is not CapacityUtilizationSurpriseDigestReport:
        raise ValueError("report must be exactly CapacityUtilizationSurpriseDigestReport")
    return _payload_value(report)


def _normalize_inputs(
    inputs: list[CapacityUtilizationSurpriseInput]
    | tuple[CapacityUtilizationSurpriseInput, ...],
) -> tuple[CapacityUtilizationSurpriseInput, ...]:
    if type(inputs) not in (list, tuple):
        raise ValueError("inputs must be a list or tuple")
    normalized = tuple(inputs)
    for item in normalized:
        if type(item) is not CapacityUtilizationSurpriseInput:
            raise ValueError("inputs must contain CapacityUtilizationSurpriseInput values")
        _require_hard_flags("CapacityUtilizationSurpriseInput", item)
    return normalized


def _surprise_row(item: CapacityUtilizationSurpriseInput) -> CapacityUtilizationSurpriseRow:
    surprise_rate_points = item.actual_utilization_rate - item.consensus_utilization_rate
    return CapacityUtilizationSurpriseRow(
        market_id=item.market_id,
        release_at=item.release_at,
        actual_utilization_rate=item.actual_utilization_rate,
        consensus_utilization_rate=item.consensus_utilization_rate,
        previous_utilization_rate=item.previous_utilization_rate,
        market_probability=item.market_probability,
        threshold_probability=item.threshold_probability,
        source_count=item.source_count,
        surprise_direction=_surprise_direction(surprise_rate_points),
        surprise_rate_points=surprise_rate_points,
        surprise_ratio=_ratio(surprise_rate_points, item.consensus_utilization_rate),
        market_probability_edge=item.market_probability - item.threshold_probability,
    )


def _input_sort_key(item: CapacityUtilizationSurpriseInput) -> tuple[datetime, str]:
    return (item.release_at, item.market_id)


def _reason_codes(rows: tuple[CapacityUtilizationSurpriseRow, ...]) -> tuple[str, ...]:
    if not rows:
        return ("capacity_utilization_surprise_digest_empty",)
    codes: list[str] = []
    if any(row.surprise_direction == "negative" for row in rows):
        codes.append("capacity_utilization_surprise_negative_present")
    if any(row.surprise_direction == "positive" for row in rows):
        codes.append("capacity_utilization_surprise_positive_present")
    if any(row.market_probability_edge > ZERO for row in rows):
        codes.append("capacity_utilization_surprise_probability_edge_present")
    if not codes:
        codes.append("capacity_utilization_surprise_no_surprises")
    return tuple(codes)


def _digest_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == ("capacity_utilization_surprise_digest_empty",):
        return "blocked"
    if reason_codes == ("capacity_utilization_surprise_no_surprises",):
        return "pass"
    return "watch"


def _recommended_next_step(reason_codes: tuple[str, ...]) -> str:
    status = _digest_status(reason_codes)
    if status == "blocked":
        return _EMPTY_NEXT_STEP
    if status == "pass":
        return _PASS_NEXT_STEP
    return _WATCH_NEXT_STEP


def _set_report_derived_fields(report: CapacityUtilizationSurpriseDigestReport) -> None:
    object.__setattr__(
        report,
        "positive_surprise_ratio",
        _optional_ratio(report.positive_surprise_count, report.input_count),
    )
    object.__setattr__(
        report,
        "negative_surprise_ratio",
        _optional_ratio(report.negative_surprise_count, report.input_count),
    )
    probability_edge_count = Decimal(
        sum(1 for row in report.surprise_rows if row.market_probability_edge > ZERO),
    )
    object.__setattr__(
        report,
        "market_probability_edge_ratio",
        _optional_ratio(probability_edge_count, report.input_count),
    )
    largest_row = _largest_abs_surprise_row(report.surprise_rows)
    object.__setattr__(
        report,
        "largest_abs_surprise_market_id",
        None if largest_row is None else largest_row.market_id,
    )
    object.__setattr__(
        report,
        "largest_abs_surprise_ratio",
        None
        if largest_row is None
        else abs(
            _rounded_ratio(
                largest_row.surprise_rate_points,
                largest_row.consensus_utilization_rate,
            ),
        ),
    )


def _largest_abs_surprise_row(
    rows: tuple[CapacityUtilizationSurpriseRow, ...],
) -> CapacityUtilizationSurpriseRow | None:
    if not rows:
        return None
    return max(rows, key=lambda row: (abs(row.surprise_ratio), row.release_at, row.market_id))


def _surprise_direction(value: Decimal) -> str:
    if value > ZERO:
        return "positive"
    if value < ZERO:
        return "negative"
    return "inline"


def _ratio(value: Decimal, total: Decimal) -> Decimal:
    return (value / total).quantize(RATIO_QUANT, rounding=ROUND_DOWN)


def _rounded_ratio(value: Decimal, total: Decimal) -> Decimal:
    return (value / total).quantize(RATIO_QUANT, rounding=ROUND_HALF_EVEN)


def _optional_ratio(value: Decimal, total: Decimal) -> Decimal | None:
    if total == ZERO:
        return None
    return _ratio(value, total)


def _validate_row_consistency(row: CapacityUtilizationSurpriseRow) -> None:
    surprise_rate_points = row.actual_utilization_rate - row.consensus_utilization_rate
    if row.surprise_rate_points != surprise_rate_points:
        raise ValueError(
            "surprise_rate_points must match actual_utilization_rate and "
            "consensus_utilization_rate",
        )
    if row.surprise_direction != _surprise_direction(surprise_rate_points):
        raise ValueError("surprise_direction must match surprise_rate_points")
    if row.surprise_ratio != _ratio(surprise_rate_points, row.consensus_utilization_rate):
        raise ValueError(
            "surprise_ratio must match surprise_rate_points and consensus_utilization_rate",
        )
    if row.market_probability_edge != row.market_probability - row.threshold_probability:
        raise ValueError(
            "market_probability_edge must match market_probability and threshold_probability",
        )


def _validate_report_consistency(report: CapacityUtilizationSurpriseDigestReport) -> None:
    if report.input_count != Decimal(len(report.surprise_rows)):
        raise ValueError("input_count must match surprise_rows")
    if report.positive_surprise_count != Decimal(
        sum(1 for row in report.surprise_rows if row.surprise_direction == "positive"),
    ):
        raise ValueError("positive_surprise_count must match surprise_rows")
    if report.negative_surprise_count != Decimal(
        sum(1 for row in report.surprise_rows if row.surprise_direction == "negative"),
    ):
        raise ValueError("negative_surprise_count must match surprise_rows")
    if report.inline_count != Decimal(
        sum(1 for row in report.surprise_rows if row.surprise_direction == "inline"),
    ):
        raise ValueError("inline_count must match surprise_rows")
    if report.total_source_count != sum((row.source_count for row in report.surprise_rows), ZERO):
        raise ValueError("total_source_count must match surprise_rows")
    if report.reason_codes != _reason_codes(report.surprise_rows):
        raise ValueError("reason_codes must match surprise_rows")
    if report.digest_status != _digest_status(report.reason_codes):
        raise ValueError("digest_status must match reason_codes")
    if report.recommended_next_step != _recommended_next_step(report.reason_codes):
        raise ValueError("recommended_next_step must match reason_codes")


def _normalize_surprise_rows(
    rows: tuple[CapacityUtilizationSurpriseRow, ...],
) -> tuple[CapacityUtilizationSurpriseRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("surprise_rows must be a list or tuple")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not CapacityUtilizationSurpriseRow:
            raise ValueError("surprise_rows must contain CapacityUtilizationSurpriseRow values")
        _require_hard_flags("CapacityUtilizationSurpriseRow", row)
    if tuple(sorted(normalized, key=lambda row: (row.release_at, row.market_id))) != normalized:
        raise ValueError("surprise_rows must be sorted by release_at and market_id")
    return normalized


def _normalize_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    if type(reason_codes) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    normalized = tuple(reason_codes)
    if not normalized:
        raise ValueError("reason_codes must not be empty")
    for reason_code in normalized:
        _require_reason_code("reason_codes", reason_code)
    if tuple(code for code in _REASON_CODES if code in set(normalized)) != normalized:
        raise ValueError("reason_codes must use canonical sequence")
    if len(set(normalized)) != len(normalized):
        raise ValueError("reason_codes must be unique")
    return normalized


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _payload_value(value: object) -> Any:
    if type(value) is Decimal:
        return _decimal_string(value)
    if type(value) is datetime:
        return value.astimezone(UTC).isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _payload_value(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    return value


def _decimal_string(value: Decimal) -> str:
    _require_decimal("value", value)
    return format(value.quantize(RATIO_QUANT, rounding=ROUND_HALF_EVEN), "f")


def _normalize_market_id(value: object) -> str:
    _require_canonical_string("market_id", value)
    return value


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a non-empty canonical string")


def _require_decimal(field_name: str, value: object) -> None:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")


def _require_positive_rate(field_name: str, value: Decimal) -> None:
    if value <= ZERO or value > ONE:
        raise ValueError(f"{field_name} must be positive and no more than 1")


def _require_nonnegative_decimal(field_name: str, value: Decimal) -> None:
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_integral_decimal(field_name: str, value: Decimal) -> None:
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be an integral Decimal")


def _require_probability(field_name: str, value: Decimal) -> None:
    if value < ZERO or value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")


def _require_surprise_direction(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if value not in _SURPRISE_DIRECTIONS:
        raise ValueError(f"{field_name} must be negative, inline, or positive")


def _require_digest_status(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if value not in _DIGEST_STATUSES:
        raise ValueError(f"{field_name} must be blocked, pass, or watch")


def _require_reason_code(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if value not in _REASON_CODES:
        raise ValueError(f"{field_name} contains an unknown reason code")


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} must be paper_only")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} must be report_only")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} must be readonly")
