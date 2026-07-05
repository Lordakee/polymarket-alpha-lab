from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from decimal import ROUND_DOWN, ROUND_HALF_EVEN, Decimal
from typing import Any


DEFAULT_EMPLOYMENT_COST_INDEX_SURPRISE_DIGEST_CONFIG_VERSION = (
    "employment-cost-index-surprise-v1"
)
RATIO_QUANT = Decimal("0.000001")
ZERO = Decimal("0")
ONE = Decimal("1")

_SURPRISE_DIRECTIONS = ("negative", "inline", "positive")
_DIGEST_STATUSES = ("blocked", "pass", "watch")
_REASON_CODES = (
    "employment_cost_index_surprise_digest_empty",
    "employment_cost_index_surprise_negative_present",
    "employment_cost_index_surprise_no_surprises",
    "employment_cost_index_surprise_positive_present",
    "employment_cost_index_surprise_probability_edge_present",
)
_WATCH_NEXT_STEP = "review_employment_cost_index_surprise_markets"
_EMPTY_NEXT_STEP = "collect_employment_cost_index_surprise_inputs"
_PASS_NEXT_STEP = "continue_employment_cost_index_surprise_monitoring"

__all__ = (
    "DEFAULT_EMPLOYMENT_COST_INDEX_SURPRISE_DIGEST_CONFIG_VERSION",
    "EmploymentCostIndexSurpriseDigestConfig",
    "EmploymentCostIndexSurpriseInput",
    "EmploymentCostIndexSurpriseRow",
    "EmploymentCostIndexSurpriseDigestReport",
    "build_market_research_employment_cost_index_surprise_digest",
    "market_research_employment_cost_index_surprise_digest_payload",
)


@dataclass(frozen=True)
class EmploymentCostIndexSurpriseDigestConfig:
    config_version: str = DEFAULT_EMPLOYMENT_COST_INDEX_SURPRISE_DIGEST_CONFIG_VERSION
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not EmploymentCostIndexSurpriseDigestConfig:
            raise TypeError(
                "EmploymentCostIndexSurpriseDigestConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not EmploymentCostIndexSurpriseDigestConfig:
            raise ValueError(
                "config must be exactly EmploymentCostIndexSurpriseDigestConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_EMPLOYMENT_COST_INDEX_SURPRISE_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_hard_flags("EmploymentCostIndexSurpriseDigestConfig", self)


@dataclass(frozen=True)
class EmploymentCostIndexSurpriseInput:
    market_id: str
    release_at: datetime
    actual_employment_cost_index_growth: Decimal
    consensus_employment_cost_index_growth: Decimal
    previous_employment_cost_index_growth: Decimal
    market_probability: Decimal
    threshold_probability: Decimal
    source_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not EmploymentCostIndexSurpriseInput:
            raise TypeError(
                "EmploymentCostIndexSurpriseInput does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not EmploymentCostIndexSurpriseInput:
            raise ValueError("input must be exactly EmploymentCostIndexSurpriseInput")
        object.__setattr__(self, "market_id", _normalize_market_id(self.market_id))
        object.__setattr__(self, "release_at", _as_utc("release_at", self.release_at))
        for field_name in (
            "actual_employment_cost_index_growth",
            "consensus_employment_cost_index_growth",
            "previous_employment_cost_index_growth",
            "market_probability",
            "threshold_probability",
            "source_count",
        ):
            _require_decimal(field_name, getattr(self, field_name))
        for field_name in (
            "actual_employment_cost_index_growth",
            "consensus_employment_cost_index_growth",
            "previous_employment_cost_index_growth",
        ):
            _require_growth_rate(field_name, getattr(self, field_name))
        for field_name in ("market_probability", "threshold_probability"):
            _require_probability(field_name, getattr(self, field_name))
        _require_integral_decimal("source_count", self.source_count)
        _require_nonnegative_decimal("source_count", self.source_count)
        _require_hard_flags("EmploymentCostIndexSurpriseInput", self)


@dataclass(frozen=True)
class EmploymentCostIndexSurpriseRow:
    market_id: str
    release_at: datetime
    actual_employment_cost_index_growth: Decimal
    consensus_employment_cost_index_growth: Decimal
    previous_employment_cost_index_growth: Decimal
    market_probability: Decimal
    threshold_probability: Decimal
    source_count: Decimal
    surprise_direction: str
    surprise_growth_points: Decimal
    surprise_ratio: Decimal
    market_probability_edge: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not EmploymentCostIndexSurpriseRow:
            raise TypeError(
                "EmploymentCostIndexSurpriseRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not EmploymentCostIndexSurpriseRow:
            raise ValueError("row must be exactly EmploymentCostIndexSurpriseRow")
        object.__setattr__(self, "market_id", _normalize_market_id(self.market_id))
        object.__setattr__(self, "release_at", _as_utc("release_at", self.release_at))
        for field_name in (
            "actual_employment_cost_index_growth",
            "consensus_employment_cost_index_growth",
            "previous_employment_cost_index_growth",
            "market_probability",
            "threshold_probability",
            "source_count",
            "surprise_growth_points",
            "surprise_ratio",
            "market_probability_edge",
        ):
            _require_decimal(field_name, getattr(self, field_name))
        for field_name in (
            "actual_employment_cost_index_growth",
            "consensus_employment_cost_index_growth",
            "previous_employment_cost_index_growth",
        ):
            _require_growth_rate(field_name, getattr(self, field_name))
        for field_name in ("market_probability", "threshold_probability"):
            _require_probability(field_name, getattr(self, field_name))
        _require_surprise_direction("surprise_direction", self.surprise_direction)
        _require_integral_decimal("source_count", self.source_count)
        _require_nonnegative_decimal("source_count", self.source_count)
        _require_hard_flags("EmploymentCostIndexSurpriseRow", self)


@dataclass(frozen=True)
class EmploymentCostIndexSurpriseDigestReport:
    generated_at: datetime
    config_version: str
    digest_status: str
    recommended_next_step: str
    input_count: Decimal
    positive_surprise_count: Decimal
    negative_surprise_count: Decimal
    inline_count: Decimal
    total_source_count: Decimal
    surprise_rows: tuple[EmploymentCostIndexSurpriseRow, ...]
    reason_codes: tuple[str, ...]
    positive_surprise_ratio: Decimal | None = field(init=False)
    negative_surprise_ratio: Decimal | None = field(init=False)
    market_probability_edge_ratio: Decimal | None = field(init=False)
    largest_abs_surprise_market_id: str | None = field(init=False)
    largest_abs_surprise_ratio: Decimal | None = field(init=False)
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not EmploymentCostIndexSurpriseDigestReport:
            raise TypeError(
                "EmploymentCostIndexSurpriseDigestReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not EmploymentCostIndexSurpriseDigestReport:
            raise ValueError(
                "report must be exactly EmploymentCostIndexSurpriseDigestReport",
            )
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
            _require_decimal(field_name, getattr(self, field_name))
            _require_integral_decimal(field_name, getattr(self, field_name))
            _require_nonnegative_decimal(field_name, getattr(self, field_name))
        object.__setattr__(self, "surprise_rows", _normalize_surprise_rows(self.surprise_rows))
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _set_report_derived_fields(self)
        _require_hard_flags("EmploymentCostIndexSurpriseDigestReport", self)
        _validate_report_consistency(self)


def build_market_research_employment_cost_index_surprise_digest(
    inputs: list[EmploymentCostIndexSurpriseInput]
    | tuple[EmploymentCostIndexSurpriseInput, ...],
    *,
    config: EmploymentCostIndexSurpriseDigestConfig,
    generated_at: datetime,
) -> EmploymentCostIndexSurpriseDigestReport:
    if type(config) is not EmploymentCostIndexSurpriseDigestConfig:
        raise ValueError("config must be an EmploymentCostIndexSurpriseDigestConfig")
    _require_hard_flags("EmploymentCostIndexSurpriseDigestConfig", config)
    normalized_inputs = _normalize_inputs(inputs)
    rows = tuple(_surprise_row(item) for item in sorted(normalized_inputs, key=_input_sort_key))
    reason_codes = _reason_codes(rows)
    return EmploymentCostIndexSurpriseDigestReport(
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


def market_research_employment_cost_index_surprise_digest_payload(
    report: EmploymentCostIndexSurpriseDigestReport,
) -> dict[str, Any]:
    if type(report) is not EmploymentCostIndexSurpriseDigestReport:
        raise ValueError("report must be an EmploymentCostIndexSurpriseDigestReport")
    _require_hard_flags("EmploymentCostIndexSurpriseDigestReport", report)
    return _payload_value(asdict(report))


def _normalize_inputs(
    inputs: list[EmploymentCostIndexSurpriseInput]
    | tuple[EmploymentCostIndexSurpriseInput, ...],
) -> tuple[EmploymentCostIndexSurpriseInput, ...]:
    if type(inputs) not in (list, tuple):
        raise ValueError("inputs must be a list or tuple")
    normalized = tuple(inputs)
    for item in normalized:
        if type(item) is not EmploymentCostIndexSurpriseInput:
            raise ValueError("inputs must contain EmploymentCostIndexSurpriseInput values")
        _require_hard_flags("EmploymentCostIndexSurpriseInput", item)
    return normalized


def _surprise_row(item: EmploymentCostIndexSurpriseInput) -> EmploymentCostIndexSurpriseRow:
    surprise_growth_points = (
        item.actual_employment_cost_index_growth
        - item.consensus_employment_cost_index_growth
    )
    return EmploymentCostIndexSurpriseRow(
        market_id=item.market_id,
        release_at=item.release_at,
        actual_employment_cost_index_growth=item.actual_employment_cost_index_growth,
        consensus_employment_cost_index_growth=item.consensus_employment_cost_index_growth,
        previous_employment_cost_index_growth=item.previous_employment_cost_index_growth,
        market_probability=item.market_probability,
        threshold_probability=item.threshold_probability,
        source_count=item.source_count,
        surprise_direction=_surprise_direction(surprise_growth_points),
        surprise_growth_points=surprise_growth_points,
        surprise_ratio=_ratio(
            surprise_growth_points,
            item.consensus_employment_cost_index_growth,
        ),
        market_probability_edge=item.market_probability - item.threshold_probability,
    )


def _input_sort_key(item: EmploymentCostIndexSurpriseInput) -> tuple[datetime, str]:
    return (item.release_at, item.market_id)


def _row_sort_key(row: EmploymentCostIndexSurpriseRow) -> tuple[datetime, str]:
    return (row.release_at, row.market_id)


def _reason_codes(rows: tuple[EmploymentCostIndexSurpriseRow, ...]) -> tuple[str, ...]:
    if not rows:
        return ("employment_cost_index_surprise_digest_empty",)
    codes: list[str] = []
    if any(row.surprise_direction == "negative" for row in rows):
        codes.append("employment_cost_index_surprise_negative_present")
    if any(row.surprise_direction == "positive" for row in rows):
        codes.append("employment_cost_index_surprise_positive_present")
    if any(row.market_probability_edge > ZERO for row in rows):
        codes.append("employment_cost_index_surprise_probability_edge_present")
    if not codes:
        codes.append("employment_cost_index_surprise_no_surprises")
    return tuple(codes)


def _digest_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == ("employment_cost_index_surprise_digest_empty",):
        return "blocked"
    if reason_codes == ("employment_cost_index_surprise_no_surprises",):
        return "pass"
    return "watch"


def _recommended_next_step(reason_codes: tuple[str, ...]) -> str:
    status = _digest_status(reason_codes)
    if status == "blocked":
        return _EMPTY_NEXT_STEP
    if status == "pass":
        return _PASS_NEXT_STEP
    return _WATCH_NEXT_STEP


def _set_report_derived_fields(report: EmploymentCostIndexSurpriseDigestReport) -> None:
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
                largest_row.surprise_growth_points,
                largest_row.consensus_employment_cost_index_growth,
            ),
        ),
    )


def _largest_abs_surprise_row(
    rows: tuple[EmploymentCostIndexSurpriseRow, ...],
) -> EmploymentCostIndexSurpriseRow | None:
    if not rows:
        return None
    return sorted(rows, key=lambda row: (-abs(row.surprise_ratio), row.release_at, row.market_id))[0]


def _surprise_direction(value: Decimal) -> str:
    if value > ZERO:
        return "positive"
    if value < ZERO:
        return "negative"
    return "inline"


def _ratio(value: Decimal, total: Decimal) -> Decimal:
    if total == ZERO:
        raise ValueError("ratio total must not be zero")
    return (value / total).quantize(RATIO_QUANT, rounding=ROUND_DOWN)


def _rounded_ratio(value: Decimal, total: Decimal) -> Decimal:
    if total == ZERO:
        raise ValueError("ratio total must not be zero")
    return (value / total).quantize(RATIO_QUANT, rounding=ROUND_HALF_EVEN)


def _optional_ratio(value: Decimal, total: Decimal) -> Decimal | None:
    if total == ZERO:
        return None
    return _ratio(value, total)


def _validate_report_consistency(report: EmploymentCostIndexSurpriseDigestReport) -> None:
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
    rows: tuple[EmploymentCostIndexSurpriseRow, ...],
) -> tuple[EmploymentCostIndexSurpriseRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("surprise_rows must be a list or tuple")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not EmploymentCostIndexSurpriseRow:
            raise ValueError("surprise_rows must contain EmploymentCostIndexSurpriseRow values")
        _require_hard_flags("EmploymentCostIndexSurpriseRow", row)
    if tuple(sorted(normalized, key=_row_sort_key)) != normalized:
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


def _payload_value(value: object) -> Any:
    if type(value) is dict:
        return {str(key): _payload_value(item) for key, item in value.items()}
    if type(value) in (list, tuple):
        return [_payload_value(item) for item in value]
    if type(value) is Decimal:
        return _decimal_payload_string(value)
    if type(value) is datetime:
        return value.isoformat()
    return value


def _decimal_payload_string(value: Decimal) -> str:
    return format(value.quantize(RATIO_QUANT, rounding=ROUND_HALF_EVEN), "f")


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


def _require_decimal(field_name: str, value: object) -> None:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")


def _require_growth_rate(field_name: str, value: Decimal) -> None:
    if value < -ONE or value > ONE:
        raise ValueError(f"{field_name} must be between -1 and 1")


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
