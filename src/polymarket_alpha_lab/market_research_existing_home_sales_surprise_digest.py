"""Pure Phase 1 existing home sales surprise digest reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
import re
from typing import Any


DEFAULT_EXISTING_HOME_SALES_SURPRISE_DIGEST_CONFIG_VERSION = (
    "market-research-existing-home-sales-surprise-digest-v0"
)

SURPRISE_DIRECTIONS = ("positive", "negative", "inline")
SURPRISE_STATUSES = ("pass", "watch", "blocked")
INPUT_REASON_CODES = (
    "existing_home_sales_positive_surprise",
    "existing_home_sales_negative_surprise",
    "existing_home_sales_inline",
)
ROW_REASON_CODES = (
    "existing_home_sales_segment_large_positive_surprise",
    "existing_home_sales_segment_large_negative_surprise",
    "existing_home_sales_segment_positive_surprise",
    "existing_home_sales_segment_negative_surprise",
    "existing_home_sales_segment_inline",
)
REPORT_REASON_CODES = (
    "existing_home_sales_large_surprise_present",
    "existing_home_sales_positive_surprises_present",
    "existing_home_sales_negative_surprises_present",
    "existing_home_sales_mixed_surprises_present",
    "existing_home_sales_surprise_digest_clear",
    "existing_home_sales_surprise_digest_empty",
)

COUNT_QUANTUM = Decimal("0.000001")
INTEGER_QUANTUM = Decimal("1")
VALUE_QUANTUM = Decimal("0.000001")
RATIO_QUANTUM = Decimal("0.000001")
ZERO_COUNT = Decimal("0.000000")
ONE_COUNT = Decimal("1.000000")
ZERO_RATIO = Decimal("0.000000")
WATCH_ABS_SURPRISE_RATIO = Decimal("0.050000")
BLOCKED_ABS_SURPRISE_RATIO = Decimal("0.100000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
STATUS_WEIGHT = {
    "blocked": Decimal("2"),
    "watch": Decimal("1"),
    "pass": Decimal("0"),
}
_CANONICAL_RE = re.compile(r"^[a-z0-9][a-z0-9_.-]*$")


__all__ = (
    "DEFAULT_EXISTING_HOME_SALES_SURPRISE_DIGEST_CONFIG_VERSION",
    "ExistingHomeSalesSurpriseDigestConfig",
    "ExistingHomeSalesSurpriseObservation",
    "ExistingHomeSalesSurpriseDigestRow",
    "ExistingHomeSalesSurpriseReasonCodeCount",
    "ExistingHomeSalesSurpriseDigestReport",
    "build_market_research_existing_home_sales_surprise_digest",
    "market_research_existing_home_sales_surprise_digest_payload",
)


@dataclass(frozen=True)
class ExistingHomeSalesSurpriseDigestConfig:
    config_version: str = DEFAULT_EXISTING_HOME_SALES_SURPRISE_DIGEST_CONFIG_VERSION
    watch_abs_surprise_ratio: Decimal = WATCH_ABS_SURPRISE_RATIO
    blocked_abs_surprise_ratio: Decimal = BLOCKED_ABS_SURPRISE_RATIO
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ExistingHomeSalesSurpriseDigestConfig:
            raise TypeError(
                "ExistingHomeSalesSurpriseDigestConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ExistingHomeSalesSurpriseDigestConfig:
            raise ValueError(
                "config must be exactly ExistingHomeSalesSurpriseDigestConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        if self.config_version != DEFAULT_EXISTING_HOME_SALES_SURPRISE_DIGEST_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        object.__setattr__(
            self,
            "watch_abs_surprise_ratio",
            _normalize_positive_ratio(
                "watch_abs_surprise_ratio",
                self.watch_abs_surprise_ratio,
            ),
        )
        object.__setattr__(
            self,
            "blocked_abs_surprise_ratio",
            _normalize_positive_ratio(
                "blocked_abs_surprise_ratio",
                self.blocked_abs_surprise_ratio,
            ),
        )
        if self.blocked_abs_surprise_ratio < self.watch_abs_surprise_ratio:
            raise ValueError("blocked_abs_surprise_ratio must be at least watch threshold")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ExistingHomeSalesSurpriseObservation:
    source_id: str
    region_id: str
    market_slug: str
    observed_sales: Decimal
    expected_sales: Decimal
    surprise_ratio: Decimal
    source_row_count: Decimal
    data_timestamp: datetime
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ExistingHomeSalesSurpriseObservation:
            raise TypeError(
                "ExistingHomeSalesSurpriseObservation does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ExistingHomeSalesSurpriseObservation:
            raise ValueError(
                "observation must be exactly ExistingHomeSalesSurpriseObservation",
            )
        for field_name in ("source_id", "region_id", "market_slug"):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "observed_sales",
            _normalize_nonnegative_value("observed_sales", self.observed_sales),
        )
        object.__setattr__(
            self,
            "expected_sales",
            _normalize_positive_value("expected_sales", self.expected_sales),
        )
        object.__setattr__(
            self,
            "surprise_ratio",
            _normalize_signed_ratio("surprise_ratio", self.surprise_ratio),
        )
        object.__setattr__(
            self,
            "source_row_count",
            _normalize_nonnegative_count("source_row_count", self.source_row_count),
        )
        object.__setattr__(
            self,
            "data_timestamp",
            _as_utc("data_timestamp", self.data_timestamp),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                INPUT_REASON_CODES,
            ),
        )
        _validate_observation(self)
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class ExistingHomeSalesSurpriseDigestRow:
    source_id: str
    region_id: str
    market_slug: str
    observed_sales: Decimal
    expected_sales: Decimal
    surprise_ratio: Decimal
    abs_surprise_ratio: Decimal
    source_row_count: Decimal
    data_timestamp: datetime
    surprise_direction: str
    surprise_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ExistingHomeSalesSurpriseDigestRow:
            raise TypeError(
                "ExistingHomeSalesSurpriseDigestRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ExistingHomeSalesSurpriseDigestRow:
            raise ValueError("row must be exactly ExistingHomeSalesSurpriseDigestRow")
        for field_name in ("source_id", "region_id", "market_slug"):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "observed_sales",
            _normalize_nonnegative_value("observed_sales", self.observed_sales),
        )
        object.__setattr__(
            self,
            "expected_sales",
            _normalize_positive_value("expected_sales", self.expected_sales),
        )
        object.__setattr__(
            self,
            "surprise_ratio",
            _normalize_signed_ratio("surprise_ratio", self.surprise_ratio),
        )
        object.__setattr__(
            self,
            "abs_surprise_ratio",
            _normalize_ratio("abs_surprise_ratio", self.abs_surprise_ratio),
        )
        object.__setattr__(
            self,
            "source_row_count",
            _normalize_nonnegative_count("source_row_count", self.source_row_count),
        )
        object.__setattr__(
            self,
            "data_timestamp",
            _as_utc("data_timestamp", self.data_timestamp),
        )
        _require_member("surprise_direction", self.surprise_direction, SURPRISE_DIRECTIONS)
        _require_member("surprise_status", self.surprise_status, SURPRISE_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ExistingHomeSalesSurpriseReasonCodeCount:
    reason_code: str
    count: Decimal
    observation_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ExistingHomeSalesSurpriseReasonCodeCount:
            raise TypeError(
                "ExistingHomeSalesSurpriseReasonCodeCount does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ExistingHomeSalesSurpriseReasonCodeCount:
            raise ValueError(
                "reason code count must be exactly ExistingHomeSalesSurpriseReasonCodeCount",
            )
        _require_member("reason_code", self.reason_code, REPORT_REASON_CODES)
        object.__setattr__(
            self,
            "count",
            _normalize_nonnegative_count("count", self.count),
        )
        object.__setattr__(
            self,
            "observation_ratio",
            _normalize_ratio("observation_ratio", self.observation_ratio),
        )
        _require_hard_flags("reason code count", self)


@dataclass(frozen=True)
class ExistingHomeSalesSurpriseDigestReport:
    generated_at: datetime
    config_version: str
    source_row_count: Decimal
    observation_count: Decimal
    positive_surprise_count: Decimal
    negative_surprise_count: Decimal
    inline_count: Decimal
    max_abs_surprise_ratio: Decimal
    average_surprise_ratio: Decimal
    blocked_observation_ratio: Decimal
    digest_status: str
    recommended_next_step: str
    reason_codes: tuple[str, ...]
    surprise_rows: tuple[ExistingHomeSalesSurpriseDigestRow, ...]
    reason_code_counts: tuple[ExistingHomeSalesSurpriseReasonCodeCount, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ExistingHomeSalesSurpriseDigestReport:
            raise TypeError(
                "ExistingHomeSalesSurpriseDigestReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ExistingHomeSalesSurpriseDigestReport:
            raise ValueError("report must be exactly ExistingHomeSalesSurpriseDigestReport")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if self.config_version != DEFAULT_EXISTING_HOME_SALES_SURPRISE_DIGEST_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "source_row_count",
            "observation_count",
            "positive_surprise_count",
            "negative_surprise_count",
            "inline_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_abs_surprise_ratio",
            _normalize_ratio("max_abs_surprise_ratio", self.max_abs_surprise_ratio),
        )
        object.__setattr__(
            self,
            "average_surprise_ratio",
            _normalize_signed_ratio("average_surprise_ratio", self.average_surprise_ratio),
        )
        object.__setattr__(
            self,
            "blocked_observation_ratio",
            _normalize_ratio(
                "blocked_observation_ratio",
                self.blocked_observation_ratio,
            ),
        )
        _require_member("digest_status", self.digest_status, SURPRISE_STATUSES)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, REPORT_REASON_CODES),
        )
        object.__setattr__(
            self,
            "surprise_rows",
            _normalize_rows(self.surprise_rows),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        _validate_report(self)
        _require_hard_flags("report", self)


def build_market_research_existing_home_sales_surprise_digest(
    observations: Iterable[ExistingHomeSalesSurpriseObservation],
    *,
    config: ExistingHomeSalesSurpriseDigestConfig | None = None,
    generated_at: datetime | None = None,
) -> ExistingHomeSalesSurpriseDigestReport:
    cfg = config or ExistingHomeSalesSurpriseDigestConfig()
    if type(cfg) is not ExistingHomeSalesSurpriseDigestConfig:
        raise ValueError("config must be exactly ExistingHomeSalesSurpriseDigestConfig")
    _require_hard_flags("config", cfg)
    generated = _as_utc("generated_at", generated_at or datetime.now(UTC))
    normalized_observations = _normalize_observations(observations)
    rows = [_build_row(observation, cfg) for observation in normalized_observations]

    ordered_rows = tuple(sorted(rows, key=_row_sort_key))
    observation_count = _count_decimal(len(ordered_rows))
    source_row_count = _sum_counts(row.source_row_count for row in ordered_rows)
    positive_count = _count_decimal(
        sum(1 for row in ordered_rows if row.surprise_direction == "positive"),
    )
    negative_count = _count_decimal(
        sum(1 for row in ordered_rows if row.surprise_direction == "negative"),
    )
    inline_count = _count_decimal(
        sum(1 for row in ordered_rows if row.surprise_direction == "inline"),
    )
    blocked_count = _count_decimal(
        sum(1 for row in ordered_rows if row.surprise_status == "blocked"),
    )
    max_abs_surprise_ratio = (
        max((row.abs_surprise_ratio for row in ordered_rows), default=ZERO_RATIO)
        .quantize(RATIO_QUANTUM)
    )
    average_surprise_ratio = _average_ratio(
        tuple(row.surprise_ratio for row in ordered_rows),
    )
    digest_status = _digest_status(ordered_rows)
    reason_codes = _report_reason_codes(ordered_rows)

    return ExistingHomeSalesSurpriseDigestReport(
        generated_at=generated,
        config_version=cfg.config_version,
        source_row_count=source_row_count,
        observation_count=observation_count,
        positive_surprise_count=positive_count,
        negative_surprise_count=negative_count,
        inline_count=inline_count,
        max_abs_surprise_ratio=max_abs_surprise_ratio,
        average_surprise_ratio=average_surprise_ratio,
        blocked_observation_ratio=_ratio(blocked_count, observation_count),
        digest_status=digest_status,
        recommended_next_step=_recommended_next_step(digest_status),
        reason_codes=reason_codes,
        surprise_rows=ordered_rows,
        reason_code_counts=_reason_code_counts(reason_codes, observation_count),
    )


def market_research_existing_home_sales_surprise_digest_payload(
    report: ExistingHomeSalesSurpriseDigestReport,
) -> dict[str, Any]:
    if type(report) is not ExistingHomeSalesSurpriseDigestReport:
        raise ValueError("report must be exactly ExistingHomeSalesSurpriseDigestReport")
    return _json_ready(asdict(report))


def _build_row(
    observation: ExistingHomeSalesSurpriseObservation,
    config: ExistingHomeSalesSurpriseDigestConfig,
) -> ExistingHomeSalesSurpriseDigestRow:
    abs_surprise_ratio = abs(observation.surprise_ratio).quantize(RATIO_QUANTUM)
    direction = _direction(observation.surprise_ratio, config.watch_abs_surprise_ratio)
    status = _row_status(abs_surprise_ratio, config)
    reason_codes = _row_reason_codes(direction, status)
    return ExistingHomeSalesSurpriseDigestRow(
        source_id=observation.source_id,
        region_id=observation.region_id,
        market_slug=observation.market_slug,
        observed_sales=observation.observed_sales,
        expected_sales=observation.expected_sales,
        surprise_ratio=observation.surprise_ratio,
        abs_surprise_ratio=abs_surprise_ratio,
        source_row_count=observation.source_row_count,
        data_timestamp=observation.data_timestamp,
        surprise_direction=direction,
        surprise_status=status,
        reason_codes=reason_codes,
    )


def _row_status(
    abs_surprise_ratio: Decimal,
    config: ExistingHomeSalesSurpriseDigestConfig,
) -> str:
    if abs_surprise_ratio >= config.blocked_abs_surprise_ratio:
        return "blocked"
    if abs_surprise_ratio >= config.watch_abs_surprise_ratio:
        return "watch"
    return "pass"


def _direction(surprise_ratio: Decimal, watch_abs_surprise_ratio: Decimal) -> str:
    if abs(surprise_ratio) < watch_abs_surprise_ratio:
        return "inline"
    if surprise_ratio > ZERO_RATIO:
        return "positive"
    return "negative"


def _row_reason_codes(direction: str, status: str) -> tuple[str, ...]:
    if status == "blocked" and direction == "positive":
        return ("existing_home_sales_segment_large_positive_surprise",)
    if status == "blocked" and direction == "negative":
        return ("existing_home_sales_segment_large_negative_surprise",)
    if status == "watch" and direction == "positive":
        return ("existing_home_sales_segment_positive_surprise",)
    if status == "watch" and direction == "negative":
        return ("existing_home_sales_segment_negative_surprise",)
    return ("existing_home_sales_segment_inline",)


def _digest_status(rows: tuple[ExistingHomeSalesSurpriseDigestRow, ...]) -> str:
    if not rows:
        return "blocked"
    if any(row.surprise_status == "blocked" for row in rows):
        return "blocked"
    if any(row.surprise_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ExistingHomeSalesSurpriseDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("existing_home_sales_surprise_digest_empty",)
    has_large = any(row.surprise_status == "blocked" for row in rows)
    has_positive = any(row.surprise_direction == "positive" for row in rows)
    has_negative = any(row.surprise_direction == "negative" for row in rows)
    reasons: list[str] = []
    if has_large:
        reasons.append("existing_home_sales_large_surprise_present")
    if has_positive and has_negative:
        reasons.append("existing_home_sales_mixed_surprises_present")
    elif has_positive:
        reasons.append("existing_home_sales_positive_surprises_present")
    elif has_negative:
        reasons.append("existing_home_sales_negative_surprises_present")
    if not reasons:
        reasons.append("existing_home_sales_surprise_digest_clear")
    return tuple(reason for reason in REPORT_REASON_CODES if reason in reasons)


def _reason_code_counts(
    reason_codes: tuple[str, ...],
    observation_count: Decimal,
) -> tuple[ExistingHomeSalesSurpriseReasonCodeCount, ...]:
    if reason_codes == ("existing_home_sales_surprise_digest_empty",):
        return (
            ExistingHomeSalesSurpriseReasonCodeCount(
                reason_code="existing_home_sales_surprise_digest_empty",
                count=ONE_COUNT,
                observation_ratio=ZERO_RATIO,
            ),
        )
    return tuple(
        ExistingHomeSalesSurpriseReasonCodeCount(
            reason_code=reason_code,
            count=ONE_COUNT,
            observation_ratio=_ratio(ONE_COUNT, observation_count),
        )
        for reason_code in reason_codes
    )


def _recommended_next_step(status: str) -> str:
    if status == "pass":
        return "allow_report_only_market_research_existing_home_sales_surprise_digest"
    if status == "watch":
        return "monitor_report_only_market_research_existing_home_sales_surprise_digest"
    return "block_report_only_market_research_existing_home_sales_surprise_digest"


def _row_sort_key(row: ExistingHomeSalesSurpriseDigestRow) -> tuple[Decimal, Decimal, datetime, str, str, str]:
    return (
        -STATUS_WEIGHT[row.surprise_status],
        -row.abs_surprise_ratio,
        _reverse_datetime(row.data_timestamp),
        row.region_id,
        row.source_id,
        row.market_slug,
    )


def _reverse_datetime(value: datetime) -> datetime:
    return datetime.max.replace(tzinfo=UTC) - (value - datetime.min.replace(tzinfo=UTC))


def _average_ratio(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO_RATIO
    with localcontext(DECIMAL_CONTEXT):
        return (sum(values, ZERO_RATIO) / Decimal(len(values))).quantize(RATIO_QUANTUM)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO_COUNT:
        return ZERO_RATIO
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(RATIO_QUANTUM)


def _sum_counts(values: Any) -> Decimal:
    total = ZERO_COUNT
    for value in values:
        total += value
    return total.quantize(COUNT_QUANTUM)


def _count_decimal(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _validate_observation(row: ExistingHomeSalesSurpriseObservation) -> None:
    expected_ratio = _calculate_surprise_ratio(row.observed_sales, row.expected_sales)
    if row.surprise_ratio != expected_ratio:
        raise ValueError("surprise_ratio must match observed and expected")
    if row.reason_codes not in _allowed_input_reason_codes(row.surprise_ratio):
        raise ValueError("reason_codes must match surprise direction")


def _input_direction(surprise_ratio: Decimal) -> str:
    if surprise_ratio > ZERO_RATIO:
        return "positive"
    if surprise_ratio < ZERO_RATIO:
        return "negative"
    return "inline"


def _allowed_input_reason_codes(surprise_ratio: Decimal) -> tuple[tuple[str, ...], ...]:
    direction = _input_direction(surprise_ratio)
    direction_reason = {
        "positive": "existing_home_sales_positive_surprise",
        "negative": "existing_home_sales_negative_surprise",
        "inline": "existing_home_sales_inline",
    }[direction]
    if abs(surprise_ratio) < WATCH_ABS_SURPRISE_RATIO and direction != "inline":
        return (
            ("existing_home_sales_inline",),
            (direction_reason,),
        )
    return ((direction_reason,),)


def _validate_row(row: ExistingHomeSalesSurpriseDigestRow) -> None:
    if row.abs_surprise_ratio != abs(row.surprise_ratio).quantize(RATIO_QUANTUM):
        raise ValueError("abs_surprise_ratio must match surprise_ratio")
    if row.surprise_direction == "positive" and row.surprise_ratio <= ZERO_RATIO:
        raise ValueError("surprise_direction must match surprise_ratio")
    if row.surprise_direction == "negative" and row.surprise_ratio >= ZERO_RATIO:
        raise ValueError("surprise_direction must match surprise_ratio")
    if row.surprise_direction == "inline" and row.surprise_status != "pass":
        raise ValueError("surprise_status must match surprise_direction")
    if row.surprise_direction != "inline" and row.surprise_status == "pass":
        raise ValueError("surprise_status must match surprise_direction")
    expected_reason_codes = _row_reason_codes(row.surprise_direction, row.surprise_status)
    if row.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match surprise direction and status")


def _validate_report(report: ExistingHomeSalesSurpriseDigestReport) -> None:
    if report.observation_count != _count_decimal(len(report.surprise_rows)):
        raise ValueError("observation_count must match surprise_rows")
    if report.positive_surprise_count != _count_decimal(
        sum(1 for row in report.surprise_rows if row.surprise_direction == "positive"),
    ):
        raise ValueError("positive_surprise_count must match surprise_rows")
    if report.negative_surprise_count != _count_decimal(
        sum(1 for row in report.surprise_rows if row.surprise_direction == "negative"),
    ):
        raise ValueError("negative_surprise_count must match surprise_rows")
    if report.inline_count != _count_decimal(
        sum(1 for row in report.surprise_rows if row.surprise_direction == "inline"),
    ):
        raise ValueError("inline_count must match surprise_rows")
    if report.source_row_count != _sum_counts(
        row.source_row_count for row in report.surprise_rows
    ):
        raise ValueError("source_row_count must match surprise_rows")
    if report.max_abs_surprise_ratio != max(
        (row.abs_surprise_ratio for row in report.surprise_rows),
        default=ZERO_RATIO,
    ).quantize(RATIO_QUANTUM):
        raise ValueError("max_abs_surprise_ratio must match surprise_rows")
    if report.average_surprise_ratio != _average_ratio(
        tuple(row.surprise_ratio for row in report.surprise_rows),
    ):
        raise ValueError("average_surprise_ratio must match surprise_rows")
    if report.blocked_observation_ratio != _ratio(
        _count_decimal(
            sum(1 for row in report.surprise_rows if row.surprise_status == "blocked"),
        ),
        report.observation_count,
    ):
        raise ValueError("blocked_observation_ratio must match surprise_rows")
    if report.digest_status != _digest_status(report.surprise_rows):
        raise ValueError("digest_status must match surprise_rows")
    if report.recommended_next_step != _recommended_next_step(report.digest_status):
        raise ValueError("recommended_next_step must match digest_status")
    if report.reason_codes != _report_reason_codes(report.surprise_rows):
        raise ValueError("reason_codes must match surprise_rows")
    if report.reason_code_counts != _reason_code_counts(
        report.reason_codes,
        report.observation_count,
    ):
        raise ValueError("reason_code_counts must match reason_codes")


def _calculate_surprise_ratio(observed_sales: Decimal, expected_sales: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return ((observed_sales - expected_sales) / expected_sales).quantize(RATIO_QUANTUM)


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _normalize_nonnegative_value(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_decimal(field_name, value).quantize(VALUE_QUANTUM)
    if normalized < Decimal("0.000000"):
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_positive_value(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_decimal(field_name, value).quantize(VALUE_QUANTUM)
    if normalized <= Decimal("0.000000"):
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_ratio(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_decimal(field_name, value).quantize(RATIO_QUANTUM)
    if normalized < ZERO_RATIO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_positive_ratio(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_ratio(field_name, value)
    if normalized <= ZERO_RATIO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_signed_ratio(field_name: str, value: Decimal) -> Decimal:
    return _require_decimal(field_name, value).quantize(RATIO_QUANTUM)


def _normalize_nonnegative_count(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_decimal(field_name, value).quantize(COUNT_QUANTUM)
    if normalized < ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != normalized.quantize(INTEGER_QUANTUM):
        raise ValueError(f"{field_name} must be an integer Decimal")
    return normalized


def _require_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    try:
        return +value
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be finite") from exc


def _require_canonical_string(field_name: str, value: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be non-empty canonical text")
    if not _CANONICAL_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be canonical lowercase text")


def _require_member(field_name: str, value: str, allowed: tuple[str, ...]) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed}")


def _normalize_reason_codes(
    field_name: str,
    values: tuple[str, ...],
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    seen: set[str] = set()
    for value in values:
        if type(value) is not str:
            raise ValueError(f"{field_name} must contain strings")
        if value not in allowed:
            raise ValueError(f"{field_name} contains unsupported reason code")
        if value in seen:
            raise ValueError(f"{field_name} must not contain duplicate reason codes")
        seen.add(value)
    normalized = tuple(values)
    if normalized != tuple(value for value in allowed if value in seen):
        raise ValueError(f"{field_name} must be sorted deterministically")
    return normalized


def _normalize_observations(
    observations: Iterable[ExistingHomeSalesSurpriseObservation],
) -> tuple[ExistingHomeSalesSurpriseObservation, ...]:
    if isinstance(observations, (str, bytes)):
        raise ValueError("observations must contain ExistingHomeSalesSurpriseObservation rows")
    try:
        normalized = tuple(observations)
    except TypeError as exc:
        raise ValueError(
            "observations must contain ExistingHomeSalesSurpriseObservation rows",
        ) from exc
    seen: set[str] = set()
    for observation in normalized:
        if type(observation) is not ExistingHomeSalesSurpriseObservation:
            raise ValueError(
                "observations must contain ExistingHomeSalesSurpriseObservation rows",
            )
        if observation.source_id in seen:
            raise ValueError("inputs must not contain duplicate source_id values")
        seen.add(observation.source_id)
    return normalized


def _normalize_rows(
    rows: tuple[ExistingHomeSalesSurpriseDigestRow, ...],
) -> tuple[ExistingHomeSalesSurpriseDigestRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("surprise_rows must be a tuple")
    seen: set[str] = set()
    normalized: list[ExistingHomeSalesSurpriseDigestRow] = []
    for row in rows:
        if type(row) is not ExistingHomeSalesSurpriseDigestRow:
            raise ValueError("surprise_rows must contain digest rows")
        if row.source_id in seen:
            raise ValueError("surprise_rows must not contain duplicate source_id values")
        seen.add(row.source_id)
        normalized.append(row)
    normalized_rows = tuple(normalized)
    if normalized_rows != tuple(sorted(normalized_rows, key=_row_sort_key)):
        raise ValueError("surprise_rows must be sorted deterministically")
    return normalized_rows


def _normalize_reason_code_counts(
    values: tuple[ExistingHomeSalesSurpriseReasonCodeCount, ...],
) -> tuple[ExistingHomeSalesSurpriseReasonCodeCount, ...]:
    if type(values) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for value in values:
        if type(value) is not ExistingHomeSalesSurpriseReasonCodeCount:
            raise ValueError("reason_code_counts must contain reason code count rows")
    if values != tuple(
        sorted(values, key=lambda value: REPORT_REASON_CODES.index(value.reason_code)),
    ):
        raise ValueError("reason_code_counts must be sorted deterministically")
    return values


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        flag = getattr(value, field_name)
        if type(flag) is not bool:
            raise ValueError(f"{label} {field_name} must be a bool")
        if flag is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _json_ready(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _json_ready(child) for key, child in value.items()}
    if isinstance(value, tuple):
        return [_json_ready(child) for child in value]
    if isinstance(value, list):
        return [_json_ready(child) for child in value]
    if type(value) is Decimal:
        with localcontext(DECIMAL_CONTEXT):
            return format(value.quantize(VALUE_QUANTUM), "f")
    if type(value) is datetime:
        return value.astimezone(UTC).isoformat()
    if isinstance(value, bool) or value is None or isinstance(value, str):
        return value
    if type(value) in {float, int}:
        raise ValueError("payload contains a non-Decimal numeric value")
    return value
