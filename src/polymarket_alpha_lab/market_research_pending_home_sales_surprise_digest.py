"""Pure Phase 1 pending home sales surprise digest reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
import re
from typing import Any


DEFAULT_PENDING_HOME_SALES_SURPRISE_DIGEST_CONFIG_VERSION = (
    "market-research-pending-home-sales-surprise-digest-v0"
)

SURPRISE_DIRECTIONS = ("positive", "negative", "inline")
SURPRISE_STATUSES = ("pass", "watch", "blocked")
INPUT_REASON_CODES = (
    "pending_home_sales_positive_surprise",
    "pending_home_sales_negative_surprise",
    "pending_home_sales_inline",
)
ROW_REASON_CODES = (
    "pending_home_sales_segment_large_positive_surprise",
    "pending_home_sales_segment_large_negative_surprise",
    "pending_home_sales_segment_positive_surprise",
    "pending_home_sales_segment_negative_surprise",
    "pending_home_sales_segment_inline",
)
REPORT_REASON_CODES = (
    "pending_home_sales_large_surprise_present",
    "pending_home_sales_positive_surprises_present",
    "pending_home_sales_negative_surprises_present",
    "pending_home_sales_mixed_surprises_present",
    "pending_home_sales_surprise_digest_clear",
    "pending_home_sales_surprise_digest_empty",
)

VALUE_QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
WATCH_ABS_SURPRISE_RATIO = Decimal("0.050000")
BLOCKED_ABS_SURPRISE_RATIO = Decimal("0.100000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
STATUS_WEIGHT = {
    "blocked": Decimal("2.000000"),
    "watch": Decimal("1.000000"),
    "pass": Decimal("0.000000"),
}
_CANONICAL_RE = re.compile(r"^[a-z0-9][a-z0-9_.-]*$")


__all__ = (
    "DEFAULT_PENDING_HOME_SALES_SURPRISE_DIGEST_CONFIG_VERSION",
    "PendingHomeSalesSurpriseDigestConfig",
    "PendingHomeSalesSurpriseObservation",
    "PendingHomeSalesSurpriseDigestRow",
    "PendingHomeSalesSurpriseReasonCodeCount",
    "PendingHomeSalesSurpriseDigestReport",
    "build_market_research_pending_home_sales_surprise_digest",
    "market_research_pending_home_sales_surprise_digest_payload",
)


@dataclass(frozen=True)
class PendingHomeSalesSurpriseDigestConfig:
    config_version: str = DEFAULT_PENDING_HOME_SALES_SURPRISE_DIGEST_CONFIG_VERSION
    watch_abs_surprise_ratio: Decimal = WATCH_ABS_SURPRISE_RATIO
    blocked_abs_surprise_ratio: Decimal = BLOCKED_ABS_SURPRISE_RATIO
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not PendingHomeSalesSurpriseDigestConfig:
            raise TypeError(
                "PendingHomeSalesSurpriseDigestConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not PendingHomeSalesSurpriseDigestConfig:
            raise ValueError(
                "config must be exactly PendingHomeSalesSurpriseDigestConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        if self.config_version != DEFAULT_PENDING_HOME_SALES_SURPRISE_DIGEST_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        object.__setattr__(
            self,
            "watch_abs_surprise_ratio",
            _require_positive_ratio(
                "watch_abs_surprise_ratio",
                self.watch_abs_surprise_ratio,
            ),
        )
        object.__setattr__(
            self,
            "blocked_abs_surprise_ratio",
            _require_positive_ratio(
                "blocked_abs_surprise_ratio",
                self.blocked_abs_surprise_ratio,
            ),
        )
        if self.blocked_abs_surprise_ratio < self.watch_abs_surprise_ratio:
            raise ValueError("blocked_abs_surprise_ratio must be at least watch threshold")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class PendingHomeSalesSurpriseObservation:
    source_id: str
    region_id: str
    market_slug: str
    observed_index: Decimal
    expected_index: Decimal
    prior_index: Decimal
    surprise_ratio: Decimal
    source_row_count: Decimal
    data_timestamp: datetime
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not PendingHomeSalesSurpriseObservation:
            raise TypeError(
                "PendingHomeSalesSurpriseObservation does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not PendingHomeSalesSurpriseObservation:
            raise ValueError(
                "observation must be exactly PendingHomeSalesSurpriseObservation",
            )
        for field_name in ("source_id", "region_id", "market_slug"):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "observed_index",
            _require_nonnegative_decimal("observed_index", self.observed_index),
        )
        object.__setattr__(
            self,
            "expected_index",
            _require_positive_decimal("expected_index", self.expected_index),
        )
        object.__setattr__(
            self,
            "prior_index",
            _require_nonnegative_decimal("prior_index", self.prior_index),
        )
        object.__setattr__(
            self,
            "surprise_ratio",
            _require_signed_ratio("surprise_ratio", self.surprise_ratio),
        )
        object.__setattr__(
            self,
            "source_row_count",
            _require_nonnegative_decimal("source_row_count", self.source_row_count),
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
class PendingHomeSalesSurpriseDigestRow:
    source_id: str
    region_id: str
    market_slug: str
    observed_index: Decimal
    expected_index: Decimal
    prior_index: Decimal
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
        if cls is not PendingHomeSalesSurpriseDigestRow:
            raise TypeError(
                "PendingHomeSalesSurpriseDigestRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not PendingHomeSalesSurpriseDigestRow:
            raise ValueError("row must be exactly PendingHomeSalesSurpriseDigestRow")
        for field_name in ("source_id", "region_id", "market_slug"):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "observed_index",
            _require_nonnegative_decimal("observed_index", self.observed_index),
        )
        object.__setattr__(
            self,
            "expected_index",
            _require_positive_decimal("expected_index", self.expected_index),
        )
        object.__setattr__(
            self,
            "prior_index",
            _require_nonnegative_decimal("prior_index", self.prior_index),
        )
        object.__setattr__(
            self,
            "surprise_ratio",
            _require_signed_ratio("surprise_ratio", self.surprise_ratio),
        )
        object.__setattr__(
            self,
            "abs_surprise_ratio",
            _require_ratio("abs_surprise_ratio", self.abs_surprise_ratio),
        )
        object.__setattr__(
            self,
            "source_row_count",
            _require_nonnegative_decimal("source_row_count", self.source_row_count),
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
class PendingHomeSalesSurpriseReasonCodeCount:
    reason_code: str
    count: Decimal
    observation_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not PendingHomeSalesSurpriseReasonCodeCount:
            raise TypeError(
                "PendingHomeSalesSurpriseReasonCodeCount does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not PendingHomeSalesSurpriseReasonCodeCount:
            raise ValueError(
                "reason code count must be exactly PendingHomeSalesSurpriseReasonCodeCount",
            )
        _require_member("reason_code", self.reason_code, REPORT_REASON_CODES)
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "observation_ratio",
            _require_ratio("observation_ratio", self.observation_ratio),
        )
        _require_hard_flags("reason code count", self)


@dataclass(frozen=True)
class PendingHomeSalesSurpriseDigestReport:
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
    surprise_rows: tuple[PendingHomeSalesSurpriseDigestRow, ...]
    reason_code_counts: tuple[PendingHomeSalesSurpriseReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not PendingHomeSalesSurpriseDigestReport:
            raise TypeError(
                "PendingHomeSalesSurpriseDigestReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not PendingHomeSalesSurpriseDigestReport:
            raise ValueError("report must be exactly PendingHomeSalesSurpriseDigestReport")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if self.config_version != DEFAULT_PENDING_HOME_SALES_SURPRISE_DIGEST_CONFIG_VERSION:
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
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_abs_surprise_ratio",
            "average_surprise_ratio",
            "blocked_observation_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_signed_ratio(field_name, getattr(self, field_name)),
            )
        _require_member("digest_status", self.digest_status, SURPRISE_STATUSES)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
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
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, REPORT_REASON_CODES),
        )
        _validate_report(self)
        _require_hard_flags("report", self)


def build_market_research_pending_home_sales_surprise_digest(
    inputs: Iterable[PendingHomeSalesSurpriseObservation],
    *,
    config: PendingHomeSalesSurpriseDigestConfig,
    generated_at: datetime,
) -> PendingHomeSalesSurpriseDigestReport:
    if type(config) is not PendingHomeSalesSurpriseDigestConfig:
        raise ValueError("config must be exactly PendingHomeSalesSurpriseDigestConfig")
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(inputs)
    rows = tuple(_row_for_observation(item, config=config) for item in normalized_inputs)
    sorted_rows = tuple(sorted(rows, key=_row_sort_key))
    reason_codes = _report_reason_codes(sorted_rows)
    digest_status = _digest_status(sorted_rows)
    observation_count = _count_decimal(len(sorted_rows))
    blocked_count = _count_decimal(
        sum(1 for row in sorted_rows if row.surprise_status == "blocked"),
    )

    return PendingHomeSalesSurpriseDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        source_row_count=_sum_decimal(row.source_row_count for row in sorted_rows),
        observation_count=observation_count,
        positive_surprise_count=_count_decimal(
            sum(1 for row in sorted_rows if row.surprise_direction == "positive"),
        ),
        negative_surprise_count=_count_decimal(
            sum(1 for row in sorted_rows if row.surprise_direction == "negative"),
        ),
        inline_count=_count_decimal(
            sum(1 for row in sorted_rows if row.surprise_direction == "inline"),
        ),
        max_abs_surprise_ratio=max(
            (row.abs_surprise_ratio for row in sorted_rows),
            default=ZERO,
        ),
        average_surprise_ratio=_ratio(
            _sum_decimal(row.surprise_ratio for row in sorted_rows),
            observation_count,
        ),
        blocked_observation_ratio=_ratio(blocked_count, observation_count),
        digest_status=digest_status,
        recommended_next_step=_recommended_next_step(digest_status),
        surprise_rows=sorted_rows,
        reason_code_counts=_reason_code_counts(reason_codes, observation_count),
        reason_codes=reason_codes,
    )


def market_research_pending_home_sales_surprise_digest_payload(
    report: PendingHomeSalesSurpriseDigestReport,
) -> dict[str, Any]:
    if type(report) is not PendingHomeSalesSurpriseDigestReport:
        raise ValueError("report must be exactly PendingHomeSalesSurpriseDigestReport")
    return _json_ready(asdict(report))


def _row_for_observation(
    observation: PendingHomeSalesSurpriseObservation,
    *,
    config: PendingHomeSalesSurpriseDigestConfig,
) -> PendingHomeSalesSurpriseDigestRow:
    direction = _surprise_direction(observation.surprise_ratio)
    status = _surprise_status(
        abs(observation.surprise_ratio),
        config=config,
    )
    return PendingHomeSalesSurpriseDigestRow(
        source_id=observation.source_id,
        region_id=observation.region_id,
        market_slug=observation.market_slug,
        observed_index=observation.observed_index,
        expected_index=observation.expected_index,
        prior_index=observation.prior_index,
        surprise_ratio=observation.surprise_ratio,
        abs_surprise_ratio=abs(observation.surprise_ratio),
        source_row_count=observation.source_row_count,
        data_timestamp=observation.data_timestamp,
        surprise_direction=direction,
        surprise_status=status,
        reason_codes=_row_reason_codes(direction=direction, status=status),
    )


def _row_reason_codes(*, direction: str, status: str) -> tuple[str, ...]:
    if direction == "inline":
        return ("pending_home_sales_segment_inline",)
    if status == "blocked" and direction == "positive":
        return ("pending_home_sales_segment_large_positive_surprise",)
    if status == "blocked":
        return ("pending_home_sales_segment_large_negative_surprise",)
    if direction == "positive":
        return ("pending_home_sales_segment_positive_surprise",)
    return ("pending_home_sales_segment_negative_surprise",)


def _report_reason_codes(
    rows: tuple[PendingHomeSalesSurpriseDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("pending_home_sales_surprise_digest_empty",)
    has_large = any(row.surprise_status == "blocked" for row in rows)
    has_positive = any(row.surprise_direction == "positive" for row in rows)
    has_negative = any(row.surprise_direction == "negative" for row in rows)
    reasons: list[str] = []
    if has_large:
        reasons.append("pending_home_sales_large_surprise_present")
    if has_positive and not has_negative:
        reasons.append("pending_home_sales_positive_surprises_present")
    if has_negative and not has_positive:
        reasons.append("pending_home_sales_negative_surprises_present")
    if has_positive and has_negative:
        reasons.append("pending_home_sales_mixed_surprises_present")
    if not reasons:
        reasons.append("pending_home_sales_surprise_digest_clear")
    return tuple(reason for reason in REPORT_REASON_CODES if reason in reasons)


def _reason_code_counts(
    reason_codes: tuple[str, ...],
    observation_count: Decimal,
) -> tuple[PendingHomeSalesSurpriseReasonCodeCount, ...]:
    if reason_codes == ("pending_home_sales_surprise_digest_empty",):
        return (
            PendingHomeSalesSurpriseReasonCodeCount(
                reason_code="pending_home_sales_surprise_digest_empty",
                count=ONE,
                observation_ratio=ZERO,
            ),
        )
    return tuple(
        PendingHomeSalesSurpriseReasonCodeCount(
            reason_code=reason_code,
            count=ONE,
            observation_ratio=_ratio(ONE, observation_count),
        )
        for reason_code in reason_codes
    )


def _digest_status(rows: tuple[PendingHomeSalesSurpriseDigestRow, ...]) -> str:
    if not rows:
        return "blocked"
    if any(row.surprise_status == "blocked" for row in rows):
        return "blocked"
    if any(row.surprise_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _recommended_next_step(status: str) -> str:
    if status == "pass":
        return "allow_report_only_market_research_pending_home_sales_surprise_digest"
    if status == "watch":
        return "monitor_report_only_market_research_pending_home_sales_surprise_digest"
    return "block_report_only_market_research_pending_home_sales_surprise_digest"


def _surprise_direction(surprise_ratio: Decimal) -> str:
    if abs(surprise_ratio) < WATCH_ABS_SURPRISE_RATIO:
        return "inline"
    if surprise_ratio > ZERO:
        return "positive"
    return "negative"


def _surprise_status(
    abs_surprise_ratio: Decimal,
    *,
    config: PendingHomeSalesSurpriseDigestConfig,
) -> str:
    if abs_surprise_ratio >= config.blocked_abs_surprise_ratio:
        return "blocked"
    if abs_surprise_ratio >= config.watch_abs_surprise_ratio:
        return "watch"
    return "pass"


def _validate_observation(observation: PendingHomeSalesSurpriseObservation) -> None:
    expected_surprise = _ratio(
        observation.observed_index - observation.expected_index,
        observation.expected_index,
    )
    if observation.surprise_ratio != expected_surprise:
        raise ValueError("surprise_ratio must match observed and expected")
    direction_reason = {
        "positive": ("pending_home_sales_positive_surprise",),
        "negative": ("pending_home_sales_negative_surprise",),
        "inline": ("pending_home_sales_inline",),
    }[_surprise_direction(observation.surprise_ratio)]
    if observation.reason_codes != direction_reason:
        raise ValueError("reason_codes must match surprise direction")


def _validate_row(row: PendingHomeSalesSurpriseDigestRow) -> None:
    if row.abs_surprise_ratio != abs(row.surprise_ratio):
        raise ValueError("abs_surprise_ratio must match surprise_ratio")
    if row.surprise_direction != _surprise_direction(row.surprise_ratio):
        raise ValueError("surprise_direction must match surprise_ratio")
    if row.reason_codes != _row_reason_codes(
        direction=row.surprise_direction,
        status=row.surprise_status,
    ):
        raise ValueError("reason_codes must match surprise direction and status")


def _validate_report(report: PendingHomeSalesSurpriseDigestReport) -> None:
    if report.source_row_count != _sum_decimal(
        row.source_row_count for row in report.surprise_rows
    ):
        raise ValueError("source_row_count must match rows")
    if report.observation_count != _count_decimal(len(report.surprise_rows)):
        raise ValueError("observation_count must match rows")
    if report.positive_surprise_count != _count_decimal(
        sum(1 for row in report.surprise_rows if row.surprise_direction == "positive"),
    ):
        raise ValueError("positive_surprise_count must match rows")
    if report.negative_surprise_count != _count_decimal(
        sum(1 for row in report.surprise_rows if row.surprise_direction == "negative"),
    ):
        raise ValueError("negative_surprise_count must match rows")
    if report.inline_count != _count_decimal(
        sum(1 for row in report.surprise_rows if row.surprise_direction == "inline"),
    ):
        raise ValueError("inline_count must match rows")
    if report.max_abs_surprise_ratio != max(
        (row.abs_surprise_ratio for row in report.surprise_rows),
        default=ZERO,
    ):
        raise ValueError("max_abs_surprise_ratio must match rows")
    if report.average_surprise_ratio != _ratio(
        _sum_decimal(row.surprise_ratio for row in report.surprise_rows),
        report.observation_count,
    ):
        raise ValueError("average_surprise_ratio must match rows")
    if report.blocked_observation_ratio != _ratio(
        _count_decimal(
            sum(1 for row in report.surprise_rows if row.surprise_status == "blocked"),
        ),
        report.observation_count,
    ):
        raise ValueError("blocked_observation_ratio must match rows")
    if report.digest_status != _digest_status(report.surprise_rows):
        raise ValueError("digest_status must match rows")
    if report.recommended_next_step != _recommended_next_step(report.digest_status):
        raise ValueError("recommended_next_step must match digest_status")
    if report.reason_codes != _report_reason_codes(report.surprise_rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(
        report.reason_codes,
        report.observation_count,
    ):
        raise ValueError("reason_code_counts must match reason_codes")


def _normalize_inputs(
    inputs: Iterable[PendingHomeSalesSurpriseObservation],
) -> tuple[PendingHomeSalesSurpriseObservation, ...]:
    if isinstance(inputs, (str, bytes)):
        raise ValueError("inputs must contain pending home sales observations")
    try:
        normalized = tuple(inputs)
    except TypeError as exc:
        raise ValueError("inputs must contain pending home sales observations") from exc
    seen: set[str] = set()
    for item in normalized:
        if type(item) is not PendingHomeSalesSurpriseObservation:
            raise ValueError(
                "inputs must contain PendingHomeSalesSurpriseObservation",
            )
        if item.source_id in seen:
            raise ValueError("inputs must not contain duplicate source_id values")
        seen.add(item.source_id)
    return normalized


def _normalize_rows(value: object) -> tuple[PendingHomeSalesSurpriseDigestRow, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("surprise_rows must contain pending home sales digest rows")
    try:
        rows = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("surprise_rows must contain pending home sales digest rows") from exc
    for row in rows:
        if type(row) is not PendingHomeSalesSurpriseDigestRow:
            raise ValueError(
                "surprise_rows must contain PendingHomeSalesSurpriseDigestRow",
            )
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("surprise_rows must be sorted deterministically")
    if len({row.source_id for row in rows}) != len(rows):
        raise ValueError("surprise_rows must not contain duplicate source_id values")
    return rows


def _normalize_reason_code_counts(
    value: object,
) -> tuple[PendingHomeSalesSurpriseReasonCodeCount, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_code_counts must contain reason code counts")
    try:
        counts = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("reason_code_counts must contain reason code counts") from exc
    for item in counts:
        if type(item) is not PendingHomeSalesSurpriseReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain PendingHomeSalesSurpriseReasonCodeCount",
            )
    if counts != tuple(
        sorted(counts, key=lambda item: REPORT_REASON_CODES.index(item.reason_code))
    ):
        raise ValueError("reason_code_counts must be sorted deterministically")
    return counts


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must contain reason code strings")
    try:
        normalized = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError(f"{field_name} must contain reason code strings") from exc
    for reason_code in normalized:
        _require_member("reason_code", reason_code, allowed)
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} must be unique")
    if normalized != tuple(
        sorted(normalized, key=lambda reason_code: allowed.index(reason_code))
    ):
        raise ValueError(f"{field_name} must be sorted deterministically")
    return normalized


def _row_sort_key(row: PendingHomeSalesSurpriseDigestRow) -> tuple[Decimal, Decimal, str, str]:
    return (
        -STATUS_WEIGHT[row.surprise_status],
        -row.abs_surprise_ratio,
        row.market_slug,
        row.source_id,
    )


def _json_ready(value: object) -> Any:
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    return value


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _sum_decimal(values: Iterable[Decimal]) -> Decimal:
    total = ZERO
    for value in values:
        if type(value) is not Decimal:
            raise ValueError("values must be Decimals")
        if not value.is_finite():
            raise ValueError("values must be finite")
        total += value
    return _quantize(total)


def _count_decimal(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(VALUE_QUANT)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    _require_canonical_string(field_name, value)
    if value not in allowed:
        raise ValueError(f"{field_name} must be supported")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value or _CANONICAL_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_ratio(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return decimal_value


def _require_positive_ratio(field_name: str, value: object) -> Decimal:
    decimal_value = _require_ratio(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_signed_ratio(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < Decimal("-1.000000") or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between negative one and one")
    return decimal_value


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} readonly must be True")
