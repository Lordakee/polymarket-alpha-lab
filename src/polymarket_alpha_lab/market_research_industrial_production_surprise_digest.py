from __future__ import annotations

from dataclasses import dataclass, field, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, ROUND_DOWN, ROUND_HALF_EVEN, Decimal, localcontext
from typing import Any


DEFAULT_INDUSTRIAL_PRODUCTION_SURPRISE_DIGEST_CONFIG_VERSION = (
    "industrial-production-surprise-v1"
)
RATIO_QUANT = Decimal("0.000001")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
ZERO = Decimal("0")
ONE = Decimal("1")

_SURPRISE_DIRECTIONS = ("negative", "inline", "positive")
_DIGEST_STATUSES = ("blocked", "pass", "watch")
_REASON_CODES = (
    "industrial_production_surprise_digest_empty",
    "industrial_production_surprise_negative_present",
    "industrial_production_surprise_no_surprises",
    "industrial_production_surprise_positive_present",
    "industrial_production_surprise_probability_edge_present",
)
_WATCH_NEXT_STEP = "review_industrial_production_surprise_markets"
_EMPTY_NEXT_STEP = "collect_industrial_production_surprise_inputs"
_PASS_NEXT_STEP = "continue_industrial_production_surprise_monitoring"

__all__ = (
    "DEFAULT_INDUSTRIAL_PRODUCTION_SURPRISE_DIGEST_CONFIG_VERSION",
    "IndustrialProductionSurpriseDigestConfig",
    "IndustrialProductionSurpriseInput",
    "IndustrialProductionSurpriseReasonCodeCount",
    "IndustrialProductionSurpriseRow",
    "IndustrialProductionSurpriseDigestReport",
    "build_market_research_industrial_production_surprise_digest",
    "market_research_industrial_production_surprise_digest_payload",
)


@dataclass(frozen=True)
class IndustrialProductionSurpriseDigestConfig:
    config_version: str = DEFAULT_INDUSTRIAL_PRODUCTION_SURPRISE_DIGEST_CONFIG_VERSION
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type("config", self, IndustrialProductionSurpriseDigestConfig)
        _require_canonical_string("config_version", self.config_version)
        if self.config_version != DEFAULT_INDUSTRIAL_PRODUCTION_SURPRISE_DIGEST_CONFIG_VERSION:
            raise ValueError("config_version must be the supported version")
        _require_hard_flags("IndustrialProductionSurpriseDigestConfig", self)


@dataclass(frozen=True)
class IndustrialProductionSurpriseInput:
    market_id: str
    release_at: datetime
    actual_index_level: Decimal
    consensus_index_level: Decimal
    previous_index_level: Decimal
    market_probability: Decimal
    threshold_probability: Decimal
    source_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type("input", self, IndustrialProductionSurpriseInput)
        object.__setattr__(self, "market_id", _normalize_market_id(self.market_id))
        object.__setattr__(self, "release_at", _as_utc("release_at", self.release_at))
        for field_name in ("actual_index_level", "consensus_index_level", "previous_index_level"):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("market_probability", "threshold_probability"):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "source_count",
            _normalize_nonnegative_count_decimal("source_count", self.source_count),
        )
        _require_hard_flags("IndustrialProductionSurpriseInput", self)


@dataclass(frozen=True)
class IndustrialProductionSurpriseRow:
    market_id: str
    release_at: datetime
    actual_index_level: Decimal
    consensus_index_level: Decimal
    previous_index_level: Decimal
    market_probability: Decimal
    threshold_probability: Decimal
    source_count: Decimal
    surprise_direction: str
    surprise_index_points: Decimal
    surprise_ratio: Decimal
    market_probability_edge: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type("row", self, IndustrialProductionSurpriseRow)
        object.__setattr__(self, "market_id", _normalize_market_id(self.market_id))
        object.__setattr__(self, "release_at", _as_utc("release_at", self.release_at))
        for field_name in ("actual_index_level", "consensus_index_level", "previous_index_level"):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("market_probability", "threshold_probability"):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "source_count",
            _normalize_nonnegative_count_decimal("source_count", self.source_count),
        )
        _require_surprise_direction("surprise_direction", self.surprise_direction)
        for field_name in (
            "surprise_index_points",
            "surprise_ratio",
            "market_probability_edge",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_decimal(field_name, getattr(self, field_name)),
            )
        _validate_row_consistency(self)
        _require_hard_flags("IndustrialProductionSurpriseRow", self)


@dataclass(frozen=True)
class IndustrialProductionSurpriseReasonCodeCount:
    reason_code: str
    count: Decimal
    input_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type("reason_code_count", self, IndustrialProductionSurpriseReasonCodeCount)
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _normalize_nonnegative_count_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "input_ratio",
            _normalize_probability_decimal("input_ratio", self.input_ratio),
        )
        _require_hard_flags("IndustrialProductionSurpriseReasonCodeCount", self)


@dataclass(frozen=True)
class IndustrialProductionSurpriseDigestReport:
    generated_at: datetime
    config_version: str
    digest_status: str
    recommended_next_step: str
    input_count: Decimal
    positive_surprise_count: Decimal
    negative_surprise_count: Decimal
    inline_count: Decimal
    total_source_count: Decimal
    surprise_rows: tuple[IndustrialProductionSurpriseRow, ...]
    reason_code_counts: tuple[IndustrialProductionSurpriseReasonCodeCount, ...]
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
        _require_exact_type("report", self, IndustrialProductionSurpriseDigestReport)
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if self.config_version != DEFAULT_INDUSTRIAL_PRODUCTION_SURPRISE_DIGEST_CONFIG_VERSION:
            raise ValueError("config_version must be the supported version")
        _require_digest_status("digest_status", self.digest_status)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        for field_name in (
            "input_count",
            "positive_surprise_count",
            "negative_surprise_count",
            "inline_count",
            "total_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "surprise_rows",
            _normalize_surprise_rows(self.surprise_rows),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _set_report_derived_fields(self)
        _require_hard_flags("IndustrialProductionSurpriseDigestReport", self)
        _validate_report_consistency(self)


def build_market_research_industrial_production_surprise_digest(
    inputs: list[IndustrialProductionSurpriseInput]
    | tuple[IndustrialProductionSurpriseInput, ...],
    *,
    config: IndustrialProductionSurpriseDigestConfig,
    generated_at: datetime,
) -> IndustrialProductionSurpriseDigestReport:
    if type(config) is not IndustrialProductionSurpriseDigestConfig:
        raise ValueError("config must be an IndustrialProductionSurpriseDigestConfig")
    _require_hard_flags("IndustrialProductionSurpriseDigestConfig", config)
    normalized_inputs = _normalize_inputs(inputs)
    rows = tuple(_surprise_row(item) for item in sorted(normalized_inputs, key=_input_sort_key))
    reason_codes = _reason_codes(rows)
    reason_code_counts = _reason_code_counts(rows)
    return IndustrialProductionSurpriseDigestReport(
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
        reason_code_counts=reason_code_counts,
        reason_codes=reason_codes,
    )


def market_research_industrial_production_surprise_digest_payload(
    report: IndustrialProductionSurpriseDigestReport,
) -> dict[str, Any]:
    if type(report) is not IndustrialProductionSurpriseDigestReport:
        raise ValueError("report must be an IndustrialProductionSurpriseDigestReport")
    _require_hard_flags("IndustrialProductionSurpriseDigestReport", report)
    payload = _payload_value(report)
    if type(payload) is not dict:
        raise ValueError("payload must be a dictionary")
    return payload


def _normalize_inputs(
    inputs: list[IndustrialProductionSurpriseInput]
    | tuple[IndustrialProductionSurpriseInput, ...],
) -> tuple[IndustrialProductionSurpriseInput, ...]:
    if type(inputs) not in (list, tuple):
        raise ValueError("inputs must be a list or tuple")
    normalized = tuple(inputs)
    for item in normalized:
        if type(item) is not IndustrialProductionSurpriseInput:
            raise ValueError("inputs must contain IndustrialProductionSurpriseInput values")
        _require_hard_flags("IndustrialProductionSurpriseInput", item)
    return normalized


def _surprise_row(item: IndustrialProductionSurpriseInput) -> IndustrialProductionSurpriseRow:
    surprise_index_points = item.actual_index_level - item.consensus_index_level
    return IndustrialProductionSurpriseRow(
        market_id=item.market_id,
        release_at=item.release_at,
        actual_index_level=item.actual_index_level,
        consensus_index_level=item.consensus_index_level,
        previous_index_level=item.previous_index_level,
        market_probability=item.market_probability,
        threshold_probability=item.threshold_probability,
        source_count=item.source_count,
        surprise_direction=_surprise_direction(surprise_index_points),
        surprise_index_points=surprise_index_points,
        surprise_ratio=_ratio(surprise_index_points, item.consensus_index_level),
        market_probability_edge=item.market_probability - item.threshold_probability,
    )


def _input_sort_key(item: IndustrialProductionSurpriseInput) -> tuple[datetime, str]:
    return (item.release_at, item.market_id)


def _reason_codes(rows: tuple[IndustrialProductionSurpriseRow, ...]) -> tuple[str, ...]:
    if not rows:
        return ("industrial_production_surprise_digest_empty",)
    codes: list[str] = []
    if any(row.surprise_direction == "negative" for row in rows):
        codes.append("industrial_production_surprise_negative_present")
    if any(row.surprise_direction == "positive" for row in rows):
        codes.append("industrial_production_surprise_positive_present")
    if any(row.market_probability_edge > ZERO for row in rows):
        codes.append("industrial_production_surprise_probability_edge_present")
    if not codes:
        codes.append("industrial_production_surprise_no_surprises")
    return tuple(codes)


def _reason_code_counts(
    rows: tuple[IndustrialProductionSurpriseRow, ...],
) -> tuple[IndustrialProductionSurpriseReasonCodeCount, ...]:
    reason_codes = _reason_codes(rows)
    if not rows:
        return (
            IndustrialProductionSurpriseReasonCodeCount(
                reason_code="industrial_production_surprise_digest_empty",
                count=ONE,
                input_ratio=ZERO,
            ),
        )
    input_count = Decimal(len(rows))
    return tuple(
        IndustrialProductionSurpriseReasonCodeCount(
            reason_code=reason_code,
            count=_reason_count(rows, reason_code),
            input_ratio=_ratio(_reason_count(rows, reason_code), input_count),
        )
        for reason_code in reason_codes
    )


def _reason_count(
    rows: tuple[IndustrialProductionSurpriseRow, ...],
    reason_code: str,
) -> Decimal:
    if reason_code == "industrial_production_surprise_negative_present":
        return Decimal(sum(1 for row in rows if row.surprise_direction == "negative"))
    if reason_code == "industrial_production_surprise_positive_present":
        return Decimal(sum(1 for row in rows if row.surprise_direction == "positive"))
    if reason_code == "industrial_production_surprise_probability_edge_present":
        return Decimal(sum(1 for row in rows if row.market_probability_edge > ZERO))
    if reason_code == "industrial_production_surprise_no_surprises":
        return Decimal(sum(1 for row in rows if row.surprise_direction == "inline"))
    if reason_code == "industrial_production_surprise_digest_empty":
        return ONE if not rows else ZERO
    raise ValueError("reason_code contains an unknown reason code")


def _digest_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == ("industrial_production_surprise_digest_empty",):
        return "blocked"
    if reason_codes == ("industrial_production_surprise_no_surprises",):
        return "pass"
    return "watch"


def _recommended_next_step(reason_codes: tuple[str, ...]) -> str:
    status = _digest_status(reason_codes)
    if status == "blocked":
        return _EMPTY_NEXT_STEP
    if status == "pass":
        return _PASS_NEXT_STEP
    return _WATCH_NEXT_STEP


def _set_report_derived_fields(report: IndustrialProductionSurpriseDigestReport) -> None:
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
        else abs(_ratio(largest_row.surprise_index_points, largest_row.previous_index_level)),
    )


def _largest_abs_surprise_row(
    rows: tuple[IndustrialProductionSurpriseRow, ...],
) -> IndustrialProductionSurpriseRow | None:
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
    with localcontext(DECIMAL_CONTEXT):
        return (value / total).quantize(RATIO_QUANT, rounding=ROUND_DOWN)


def _optional_ratio(value: Decimal, total: Decimal) -> Decimal | None:
    if total == ZERO:
        return None
    return _ratio(value, total)


def _validate_row_consistency(row: IndustrialProductionSurpriseRow) -> None:
    expected_surprise_index_points = _normalize_decimal(
        "surprise_index_points",
        row.actual_index_level - row.consensus_index_level,
    )
    if row.surprise_index_points != expected_surprise_index_points:
        raise ValueError(
            "surprise_index_points must match actual_index_level and "
            "consensus_index_level",
        )
    expected_surprise_ratio = _ratio(
        expected_surprise_index_points,
        row.consensus_index_level,
    )
    if row.surprise_ratio != expected_surprise_ratio:
        raise ValueError("surprise_ratio must match surprise_index_points")
    expected_market_probability_edge = _normalize_decimal(
        "market_probability_edge",
        row.market_probability - row.threshold_probability,
    )
    if row.market_probability_edge != expected_market_probability_edge:
        raise ValueError(
            "market_probability_edge must match market_probability and "
            "threshold_probability",
        )
    if row.surprise_direction != _surprise_direction(expected_surprise_index_points):
        raise ValueError("surprise_direction must match surprise_index_points")


def _validate_report_consistency(report: IndustrialProductionSurpriseDigestReport) -> None:
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
    if report.reason_code_counts != _reason_code_counts(report.surprise_rows):
        raise ValueError("reason_code_counts must match surprise_rows")
    if report.reason_codes != tuple(item.reason_code for item in report.reason_code_counts):
        raise ValueError("reason_codes must match reason_code_counts")
    if report.reason_codes != _reason_codes(report.surprise_rows):
        raise ValueError("reason_codes must match surprise_rows")
    if report.digest_status != _digest_status(report.reason_codes):
        raise ValueError("digest_status must match reason_codes")
    if report.recommended_next_step != _recommended_next_step(report.reason_codes):
        raise ValueError("recommended_next_step must match reason_codes")


def _normalize_surprise_rows(
    rows: tuple[IndustrialProductionSurpriseRow, ...],
) -> tuple[IndustrialProductionSurpriseRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("surprise_rows must be a list or tuple")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not IndustrialProductionSurpriseRow:
            raise ValueError("surprise_rows must contain IndustrialProductionSurpriseRow values")
        _require_hard_flags("IndustrialProductionSurpriseRow", row)
    if tuple(sorted(normalized, key=lambda row: (row.release_at, row.market_id))) != normalized:
        raise ValueError("surprise_rows must be sorted by release_at and market_id")
    return normalized


def _normalize_reason_code_counts(
    reason_code_counts: tuple[IndustrialProductionSurpriseReasonCodeCount, ...],
) -> tuple[IndustrialProductionSurpriseReasonCodeCount, ...]:
    if type(reason_code_counts) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    normalized = tuple(reason_code_counts)
    seen_reason_codes: set[str] = set()
    for item in normalized:
        if type(item) is not IndustrialProductionSurpriseReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain IndustrialProductionSurpriseReasonCodeCount values",
            )
        _require_hard_flags("IndustrialProductionSurpriseReasonCodeCount", item)
        if item.reason_code in seen_reason_codes:
            raise ValueError("reason_code_counts must be unique")
        seen_reason_codes.add(item.reason_code)
    if tuple(sorted(normalized, key=lambda item: _REASON_CODES.index(item.reason_code))) != normalized:
        raise ValueError("reason_code_counts must use canonical sequence")
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


def _payload_value(value: object) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return {item.name: _payload_value(getattr(value, item.name)) for item in fields(value)}
    if type(value) is Decimal:
        return f"{_quantize_decimal(value):f}"
    if type(value) is datetime:
        return value.astimezone(UTC).isoformat()
    if type(value) in (list, tuple):
        return [_payload_value(item) for item in value]
    if value is None or type(value) in (str, bool):
        return value
    raise ValueError("payload contains an unsupported value")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _normalize_market_id(value: object) -> str:
    _require_canonical_string("market_id", value)
    return value


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a non-empty canonical string")


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    return _quantize_decimal(_require_decimal(field_name, value))


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    _require_positive_decimal(field_name, decimal_value)
    return _quantize_decimal(decimal_value)


def _normalize_probability_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    _require_probability(field_name, decimal_value)
    return _quantize_decimal(decimal_value)


def _normalize_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    _require_integral_decimal(field_name, decimal_value)
    _require_nonnegative_decimal(field_name, decimal_value)
    return _quantize_decimal(decimal_value)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _quantize_decimal(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(RATIO_QUANT)


def _require_positive_decimal(field_name: str, value: Decimal) -> None:
    if value <= ZERO:
        raise ValueError(f"{field_name} must be positive")


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


def _require_exact_type(field_name: str, value: object, expected_type: type[object]) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be exactly {expected_type.__name__}")
