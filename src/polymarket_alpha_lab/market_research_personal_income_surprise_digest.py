"""Pure Phase 1 personal income surprise digest reducer."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Iterable


DEFAULT_PERSONAL_INCOME_SURPRISE_DIGEST_CONFIG_VERSION = (
    "market-research-personal-income-surprise-digest-v0"
)
DEFAULT_PERSONAL_INCOME_SURPRISE_DIGEST_MAX_ROWS = Decimal("25.000000")
DEFAULT_PERSONAL_INCOME_SURPRISE_DIGEST_MIN_ABS_SURPRISE_RATIO = Decimal("0.010000")

NO_REASON_CODE = "no_reason"
_DECIMAL_PLACES = Decimal("0.000001")
_COUNT_PLACES = Decimal("1")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
_LOW_LIQUIDITY_THRESHOLD = Decimal("1000.000000")
_LARGE_ABS_SURPRISE_RATIO = Decimal("0.100000")
_SURPRISE_DIRECTION_ORDER = {
    "positive": 0,
    "negative": 1,
    "neutral": 2,
}
REPORT_REASON_CODES = (
    "personal_income_surprise_positive_present",
    "personal_income_surprise_negative_present",
    "personal_income_surprise_neutral_present",
    "personal_income_surprise_large_present",
    "personal_income_surprise_low_liquidity_present",
    "personal_income_surprise_digest_clear",
    "personal_income_surprise_digest_empty",
)

__all__ = (
    "DEFAULT_PERSONAL_INCOME_SURPRISE_DIGEST_CONFIG_VERSION",
    "DEFAULT_PERSONAL_INCOME_SURPRISE_DIGEST_MAX_ROWS",
    "DEFAULT_PERSONAL_INCOME_SURPRISE_DIGEST_MIN_ABS_SURPRISE_RATIO",
    "REPORT_REASON_CODES",
    "MarketResearchPersonalIncomeSurpriseDigestConfig",
    "MarketResearchPersonalIncomeSurpriseDigestInputRow",
    "MarketResearchPersonalIncomeSurpriseDigestRow",
    "MarketResearchPersonalIncomeSurpriseReasonCodeCount",
    "MarketResearchPersonalIncomeSurpriseDigestReport",
    "build_market_research_personal_income_surprise_digest",
    "build_market_research_personal_income_surprise_digest_report",
    "market_research_personal_income_surprise_digest_payload",
)


@dataclass(frozen=True)
class MarketResearchPersonalIncomeSurpriseDigestConfig:
    config_version: str = DEFAULT_PERSONAL_INCOME_SURPRISE_DIGEST_CONFIG_VERSION
    max_rows: Decimal = DEFAULT_PERSONAL_INCOME_SURPRISE_DIGEST_MAX_ROWS
    min_abs_surprise_ratio: Decimal = (
        DEFAULT_PERSONAL_INCOME_SURPRISE_DIGEST_MIN_ABS_SURPRISE_RATIO
    )
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchPersonalIncomeSurpriseDigestConfig,
            "config",
        )
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_PERSONAL_INCOME_SURPRISE_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        object.__setattr__(
            self,
            "max_rows",
            _require_positive_count("max_rows", self.max_rows),
        )
        object.__setattr__(
            self,
            "min_abs_surprise_ratio",
            _quantize_decimal(
                "min_abs_surprise_ratio",
                self.min_abs_surprise_ratio,
            ),
        )
        if self.min_abs_surprise_ratio < ZERO:
            raise ValueError("min_abs_surprise_ratio must be nonnegative")
        _validate_hard_flags("config", self)


@dataclass(frozen=True)
class MarketResearchPersonalIncomeSurpriseDigestInputRow:
    market_slug: str
    question: str
    category: str
    event_date: datetime
    actual_value: Decimal
    consensus_value: Decimal
    prior_value: Decimal
    probability: Decimal
    liquidity: Decimal
    reason_codes: tuple[str, ...] = (NO_REASON_CODE,)
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchPersonalIncomeSurpriseDigestInputRow,
            "input row",
        )
        _require_canonical_string("market_slug", self.market_slug)
        _require_canonical_string("question", self.question)
        _require_canonical_string("category", self.category)
        object.__setattr__(self, "event_date", _as_utc("event_date", self.event_date))
        object.__setattr__(
            self,
            "actual_value",
            _quantize_decimal("actual_value", self.actual_value),
        )
        object.__setattr__(
            self,
            "consensus_value",
            _quantize_decimal("consensus_value", self.consensus_value),
        )
        if self.consensus_value == ZERO:
            raise ValueError("consensus_value cannot be zero")
        object.__setattr__(
            self,
            "prior_value",
            _quantize_decimal("prior_value", self.prior_value),
        )
        object.__setattr__(
            self,
            "probability",
            _quantize_decimal("probability", self.probability),
        )
        if not ZERO <= self.probability <= ONE:
            raise ValueError("probability must be between 0 and 1")
        object.__setattr__(
            self,
            "liquidity",
            _quantize_decimal("liquidity", self.liquidity),
        )
        if self.liquidity < ZERO:
            raise ValueError("liquidity must be nonnegative")
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _validate_hard_flags("input row", self)


@dataclass(frozen=True)
class MarketResearchPersonalIncomeSurpriseDigestRow:
    digest_rank: Decimal
    market_slug: str
    question: str
    category: str
    event_date: datetime
    surprise_direction: str
    reason_codes: tuple[str, ...]
    actual_value: Decimal
    consensus_value: Decimal
    prior_value: Decimal
    surprise: Decimal
    surprise_ratio: Decimal
    probability: Decimal
    liquidity: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchPersonalIncomeSurpriseDigestRow,
            "digest row",
        )
        object.__setattr__(self, "digest_rank", _quantize_count("digest_rank", self.digest_rank))
        if self.digest_rank <= ZERO:
            raise ValueError("digest_rank must be positive")
        _require_canonical_string("market_slug", self.market_slug)
        _require_canonical_string("question", self.question)
        _require_canonical_string("category", self.category)
        object.__setattr__(self, "event_date", _as_utc("event_date", self.event_date))
        _require_surprise_direction("surprise_direction", self.surprise_direction)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        for field_name in (
            "actual_value",
            "consensus_value",
            "prior_value",
            "surprise",
            "surprise_ratio",
            "probability",
            "liquidity",
        ):
            object.__setattr__(
                self,
                field_name,
                _quantize_decimal(field_name, getattr(self, field_name)),
            )
        _validate_digest_row(self)
        _validate_hard_flags("digest row", self)


@dataclass(frozen=True)
class MarketResearchPersonalIncomeSurpriseReasonCodeCount:
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchPersonalIncomeSurpriseReasonCodeCount,
            "reason code count",
        )
        _require_member("reason_code", self.reason_code, REPORT_REASON_CODES)
        object.__setattr__(self, "count", _quantize_count("count", self.count))
        if self.count < ZERO:
            raise ValueError("count must be nonnegative")
        object.__setattr__(self, "row_ratio", _quantize_decimal("row_ratio", self.row_ratio))
        if not ZERO <= self.row_ratio <= ONE:
            raise ValueError("row_ratio must be between 0 and 1")
        _validate_hard_flags("reason code count", self)


@dataclass(frozen=True)
class MarketResearchPersonalIncomeSurpriseDigestReport:
    generated_at: datetime
    config_version: str
    input_row_count: Decimal
    digest_row_count: Decimal
    included_count: Decimal
    skipped_count: Decimal
    positive_surprise_count: Decimal
    negative_surprise_count: Decimal
    neutral_surprise_count: Decimal
    reason_code_counts: tuple[MarketResearchPersonalIncomeSurpriseReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    digest_rows: tuple[MarketResearchPersonalIncomeSurpriseDigestRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchPersonalIncomeSurpriseDigestReport,
            "digest report",
        )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_PERSONAL_INCOME_SURPRISE_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "input_row_count",
            "digest_row_count",
            "included_count",
            "skipped_count",
            "positive_surprise_count",
            "negative_surprise_count",
            "neutral_surprise_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _quantize_count(field_name, getattr(self, field_name)),
            )
            if getattr(self, field_name) < Decimal("0"):
                raise ValueError(f"{field_name} must be nonnegative")
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_report_reason_codes(self.reason_codes),
        )
        object.__setattr__(self, "digest_rows", _normalize_digest_rows(self.digest_rows))
        _validate_report_consistency(self)
        _validate_hard_flags("digest report", self)


def build_market_research_personal_income_surprise_digest_report(
    rows: Iterable[MarketResearchPersonalIncomeSurpriseDigestInputRow],
    *,
    config: MarketResearchPersonalIncomeSurpriseDigestConfig,
    generated_at: datetime,
) -> MarketResearchPersonalIncomeSurpriseDigestReport:
    """Build a readonly digest from already-supplied personal income release rows."""

    if type(config) is not MarketResearchPersonalIncomeSurpriseDigestConfig:
        raise ValueError(
            "config must be a MarketResearchPersonalIncomeSurpriseDigestConfig"
        )
    if type(generated_at) is not datetime:
        raise ValueError("generated_at must be a datetime")
    generated_at_utc = _as_utc("generated_at", generated_at)
    _validate_hard_flags("config", config)

    input_rows = _normalize_input_rows(rows)
    candidates = tuple(
        sorted(
            (
                candidate
                for candidate in (
                    _digest_candidate(
                        row,
                        min_abs_surprise_ratio=config.min_abs_surprise_ratio,
                    )
                    for row in input_rows
                )
                if candidate[5]
            ),
            key=_candidate_sort_key,
        )
    )
    selected = candidates[: _max_rows_as_int(config.max_rows)]
    digest_rows = tuple(
        MarketResearchPersonalIncomeSurpriseDigestRow(
            digest_rank=Decimal(index),
            market_slug=row.market_slug,
            question=row.question,
            category=row.category,
            event_date=row.event_date,
            surprise_direction=direction,
            reason_codes=reason_codes,
            actual_value=row.actual_value,
            consensus_value=row.consensus_value,
            prior_value=row.prior_value,
            surprise=surprise,
            surprise_ratio=surprise_ratio,
            probability=row.probability,
            liquidity=row.liquidity,
        )
        for index, (
            row,
            direction,
            reason_codes,
            surprise,
            surprise_ratio,
        _selected,
        ) in enumerate(selected, start=1)
    )
    reason_codes = _report_reason_codes(digest_rows)

    return MarketResearchPersonalIncomeSurpriseDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        input_row_count=_count_decimal(len(input_rows)),
        digest_row_count=_count_decimal(len(digest_rows)),
        included_count=_direction_count(digest_rows, "positive")
        + _direction_count(digest_rows, "negative"),
        skipped_count=_direction_count(digest_rows, "neutral"),
        positive_surprise_count=_direction_count(digest_rows, "positive"),
        negative_surprise_count=_direction_count(digest_rows, "negative"),
        neutral_surprise_count=_direction_count(digest_rows, "neutral"),
        reason_code_counts=_reason_code_counts(reason_codes, digest_rows),
        reason_codes=reason_codes,
        digest_rows=digest_rows,
    )


def build_market_research_personal_income_surprise_digest(
    rows: Iterable[MarketResearchPersonalIncomeSurpriseDigestInputRow],
    *,
    config: MarketResearchPersonalIncomeSurpriseDigestConfig,
    generated_at: datetime,
) -> MarketResearchPersonalIncomeSurpriseDigestReport:
    """Alias for callers that name the reducer by the digest artifact."""

    return build_market_research_personal_income_surprise_digest_report(
        rows,
        config=config,
        generated_at=generated_at,
    )


def market_research_personal_income_surprise_digest_payload(
    report: MarketResearchPersonalIncomeSurpriseDigestReport,
) -> dict[str, Any]:
    """Serialize the report-only digest without exposing live objects."""

    if type(report) is not MarketResearchPersonalIncomeSurpriseDigestReport:
        raise ValueError(
            "report must be exactly MarketResearchPersonalIncomeSurpriseDigestReport",
        )
    return _payload_value(report)


def _digest_candidate(
    row: MarketResearchPersonalIncomeSurpriseDigestInputRow,
    *,
    min_abs_surprise_ratio: Decimal,
) -> tuple[
    MarketResearchPersonalIncomeSurpriseDigestInputRow,
    str,
    tuple[str, ...],
    Decimal,
    Decimal,
    bool,
]:
    surprise = _quantize_decimal("surprise", row.actual_value - row.consensus_value)
    surprise_ratio = _quantize_decimal(
        "surprise_ratio",
        surprise / row.consensus_value.copy_abs(),
    )
    abs_surprise_ratio = surprise_ratio.copy_abs()
    if abs_surprise_ratio < min_abs_surprise_ratio:
        direction = "neutral"
        selected = False
    elif abs_surprise_ratio < _LARGE_ABS_SURPRISE_RATIO:
        direction = "neutral"
        selected = True
    elif surprise > ZERO:
        direction = "positive"
        selected = True
    else:
        direction = "negative"
        selected = True

    reason_codes = row.reason_codes + _derived_reason_codes(
        abs_surprise_ratio=abs_surprise_ratio,
        liquidity=row.liquidity,
    )
    return (
        row,
        direction,
        _normalize_reason_codes(reason_codes),
        surprise,
        surprise_ratio,
        selected,
    )


def _candidate_sort_key(
    candidate: tuple[
        MarketResearchPersonalIncomeSurpriseDigestInputRow,
        str,
        tuple[str, ...],
        Decimal,
        Decimal,
        bool,
    ],
) -> tuple[int, Decimal, Decimal, datetime, str]:
    row, direction, _reason_codes, _surprise, surprise_ratio, _included = candidate
    return (
        1 if direction == "neutral" else 0,
        -row.liquidity,
        -surprise_ratio.copy_abs(),
        row.event_date,
        row.market_slug,
    )


def _derived_reason_codes(
    *,
    abs_surprise_ratio: Decimal,
    liquidity: Decimal,
) -> tuple[str, ...]:
    surprise_reason = (
        "large_surprise"
        if abs_surprise_ratio >= _LARGE_ABS_SURPRISE_RATIO
        else "small_surprise"
    )
    liquidity_reason = (
        "low_liquidity"
        if liquidity < _LOW_LIQUIDITY_THRESHOLD
        else "high_liquidity"
    )
    return (surprise_reason, liquidity_reason)


def _direction_count(
    rows: tuple[MarketResearchPersonalIncomeSurpriseDigestRow, ...],
    direction: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.surprise_direction == direction))


def _report_reason_codes(
    rows: tuple[MarketResearchPersonalIncomeSurpriseDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("personal_income_surprise_digest_empty",)
    reason_codes: list[str] = []
    if _direction_count(rows, "positive") > ZERO:
        reason_codes.append("personal_income_surprise_positive_present")
    if _direction_count(rows, "negative") > ZERO:
        reason_codes.append("personal_income_surprise_negative_present")
    if _direction_count(rows, "neutral") > ZERO:
        reason_codes.append("personal_income_surprise_neutral_present")
    if _row_reason_count(rows, "large_surprise") > ZERO:
        reason_codes.append("personal_income_surprise_large_present")
    if _row_reason_count(rows, "low_liquidity") > ZERO:
        reason_codes.append("personal_income_surprise_low_liquidity_present")
    if not reason_codes:
        reason_codes.append("personal_income_surprise_digest_clear")
    return tuple(reason_code for reason_code in REPORT_REASON_CODES if reason_code in reason_codes)


def _reason_code_counts(
    reason_codes: tuple[str, ...],
    rows: tuple[MarketResearchPersonalIncomeSurpriseDigestRow, ...],
) -> tuple[MarketResearchPersonalIncomeSurpriseReasonCodeCount, ...]:
    row_count = _count_decimal(len(rows))
    if reason_codes == ("personal_income_surprise_digest_empty",):
        return (
            MarketResearchPersonalIncomeSurpriseReasonCodeCount(
                reason_code="personal_income_surprise_digest_empty",
                count=ONE,
                row_ratio=ZERO,
            ),
        )
    return tuple(
        MarketResearchPersonalIncomeSurpriseReasonCodeCount(
            reason_code=reason_code,
            count=_report_reason_row_count(reason_code, rows),
            row_ratio=_ratio(_report_reason_row_count(reason_code, rows), row_count),
        )
        for reason_code in reason_codes
    )


def _report_reason_row_count(
    reason_code: str,
    rows: tuple[MarketResearchPersonalIncomeSurpriseDigestRow, ...],
) -> Decimal:
    if reason_code == "personal_income_surprise_positive_present":
        return _direction_count(rows, "positive")
    if reason_code == "personal_income_surprise_negative_present":
        return _direction_count(rows, "negative")
    if reason_code == "personal_income_surprise_neutral_present":
        return _direction_count(rows, "neutral")
    if reason_code == "personal_income_surprise_large_present":
        return _row_reason_count(rows, "large_surprise")
    if reason_code == "personal_income_surprise_low_liquidity_present":
        return _row_reason_count(rows, "low_liquidity")
    if reason_code == "personal_income_surprise_digest_clear":
        return _count_decimal(len(rows))
    if reason_code == "personal_income_surprise_digest_empty":
        return ONE
    raise ValueError("reason_code must be supported")


def _row_reason_count(
    rows: tuple[MarketResearchPersonalIncomeSurpriseDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if reason_code in row.reason_codes))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return _quantize_decimal("ratio", numerator / denominator)


def _count_decimal(value: int) -> Decimal:
    return _quantize_decimal("count", Decimal(value))


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _quantize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value.quantize(_DECIMAL_PLACES, rounding=ROUND_HALF_UP)


def _quantize_count(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    quantized = value.quantize(_COUNT_PLACES, rounding=ROUND_HALF_UP)
    if value != quantized:
        raise ValueError(f"{field_name} must be an integer Decimal")
    return quantized.quantize(_DECIMAL_PLACES, rounding=ROUND_HALF_UP)


def _require_positive_count(field_name: str, value: object) -> Decimal:
    decimal_value = _quantize_count(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_surprise_direction(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value not in _SURPRISE_DIRECTION_ORDER:
        raise ValueError(f"{field_name} must be positive, negative, or neutral")


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    _require_canonical_string(field_name, value)
    if value not in allowed:
        raise ValueError(f"{field_name} must be supported")


def _normalize_reason_codes(value: tuple[str, ...]) -> tuple[str, ...]:
    if not isinstance(value, tuple):
        raise ValueError("reason_codes must be a tuple")
    normalized: list[str] = []
    seen: set[str] = set()
    for reason_code in value:
        _require_reason_code(reason_code)
        if reason_code not in seen:
            normalized.append(reason_code)
            seen.add(reason_code)
    if not normalized:
        return (NO_REASON_CODE,)
    return tuple(sorted(normalized))


def _normalize_report_reason_codes(value: tuple[str, ...]) -> tuple[str, ...]:
    if not isinstance(value, tuple):
        raise ValueError("reason_codes must be a tuple")
    for reason_code in value:
        _require_member("reason_code", reason_code, REPORT_REASON_CODES)
    if len(set(value)) != len(value):
        raise ValueError("reason_codes must be unique")
    return tuple(sorted(value, key=lambda reason_code: REPORT_REASON_CODES.index(reason_code)))


def _normalize_reason_code_counts(
    values: tuple[MarketResearchPersonalIncomeSurpriseReasonCodeCount, ...],
) -> tuple[MarketResearchPersonalIncomeSurpriseReasonCodeCount, ...]:
    if not isinstance(values, tuple):
        raise ValueError("reason_code_counts must be a tuple")
    seen: set[str] = set()
    for value in values:
        if type(value) is not MarketResearchPersonalIncomeSurpriseReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "MarketResearchPersonalIncomeSurpriseReasonCodeCount",
            )
        _validate_hard_flags("reason code count", value)
        if value.reason_code in seen:
            raise ValueError("reason_code_counts must be unique")
        seen.add(value.reason_code)
    return tuple(sorted(values, key=lambda value: REPORT_REASON_CODES.index(value.reason_code)))


def _require_reason_code(value: object) -> None:
    if type(value) is not str:
        raise ValueError("reason_codes must contain strings")
    if not value or value.strip() != value or " " in value:
        raise ValueError("reason_codes must contain canonical strings")


def _normalize_input_rows(
    rows: Iterable[MarketResearchPersonalIncomeSurpriseDigestInputRow],
) -> tuple[MarketResearchPersonalIncomeSurpriseDigestInputRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable of input rows")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable of input rows") from exc
    for row in normalized:
        if type(row) is not MarketResearchPersonalIncomeSurpriseDigestInputRow:
            raise ValueError(
                "rows must contain MarketResearchPersonalIncomeSurpriseDigestInputRow"
            )
        _validate_hard_flags("input row", row)
    return normalized


def _normalize_digest_rows(
    rows: tuple[MarketResearchPersonalIncomeSurpriseDigestRow, ...],
) -> tuple[MarketResearchPersonalIncomeSurpriseDigestRow, ...]:
    if not isinstance(rows, tuple):
        raise ValueError("digest_rows must be a tuple")
    for row in rows:
        if type(row) is not MarketResearchPersonalIncomeSurpriseDigestRow:
            raise ValueError(
                "digest_rows must contain MarketResearchPersonalIncomeSurpriseDigestRow"
            )
        _validate_hard_flags("digest row", row)
    ranks = tuple(row.digest_rank for row in rows)
    expected_ranks = tuple(Decimal(index) for index in range(1, len(rows) + 1))
    if ranks != expected_ranks:
        raise ValueError("digest_rows must use deterministic ordering")
    if tuple(sorted(rows, key=_digest_row_sort_key)) != rows:
        raise ValueError("digest_rows must use deterministic ordering")
    return rows


def _digest_row_sort_key(
    row: MarketResearchPersonalIncomeSurpriseDigestRow,
) -> tuple[int, Decimal, Decimal, datetime, str]:
    return (
        1 if row.surprise_direction == "neutral" else 0,
        -row.liquidity,
        -row.surprise_ratio.copy_abs(),
        row.event_date,
        row.market_slug,
    )


def _validate_report_consistency(
    report: MarketResearchPersonalIncomeSurpriseDigestReport,
) -> None:
    if report.digest_row_count != Decimal(len(report.digest_rows)):
        raise ValueError("digest_row_count must match digest_rows")
    included_count = report.positive_surprise_count + report.negative_surprise_count
    if report.included_count != included_count:
        raise ValueError("included_count must match surprise direction counts")
    if report.skipped_count != report.neutral_surprise_count:
        raise ValueError("skipped_count must match neutral_surprise_count")
    if report.digest_row_count != report.included_count + report.skipped_count:
        raise ValueError("digest_row_count must match included plus skipped")
    if report.positive_surprise_count != _direction_count(report.digest_rows, "positive"):
        raise ValueError("positive_surprise_count must match digest_rows")
    if report.negative_surprise_count != _direction_count(report.digest_rows, "negative"):
        raise ValueError("negative_surprise_count must match digest_rows")
    if report.neutral_surprise_count != _direction_count(report.digest_rows, "neutral"):
        raise ValueError("neutral_surprise_count must match digest_rows")
    if report.input_row_count < report.digest_row_count:
        raise ValueError("input_row_count must be at least digest_row_count")
    if report.reason_codes != _report_reason_codes(report.digest_rows):
        raise ValueError("reason_codes must match digest_rows")
    if report.reason_code_counts != _reason_code_counts(
        report.reason_codes,
        report.digest_rows,
    ):
        raise ValueError("reason_code_counts must match reason_codes")


def _validate_digest_row(row: MarketResearchPersonalIncomeSurpriseDigestRow) -> None:
    if row.consensus_value == ZERO:
        raise ValueError("consensus_value cannot be zero")
    if not ZERO <= row.probability <= ONE:
        raise ValueError("probability must be between 0 and 1")
    if row.liquidity < ZERO:
        raise ValueError("liquidity must be nonnegative")
    if row.surprise != _quantize_decimal("surprise", row.actual_value - row.consensus_value):
        raise ValueError("surprise must match actual_value and consensus_value")
    expected_ratio = _quantize_decimal(
        "surprise_ratio",
        row.surprise / row.consensus_value.copy_abs(),
    )
    if row.surprise_ratio != expected_ratio:
        raise ValueError("surprise_ratio must match surprise and consensus_value")
    if row.surprise_direction != _surprise_direction(row.surprise, row.surprise_ratio):
        raise ValueError("surprise_direction must match surprise_ratio")
    for reason_code in _derived_reason_codes(
        abs_surprise_ratio=row.surprise_ratio.copy_abs(),
        liquidity=row.liquidity,
    ):
        if reason_code not in row.reason_codes:
            raise ValueError("reason_codes must include derived reason codes")


def _surprise_direction(surprise: Decimal, surprise_ratio: Decimal) -> str:
    if surprise_ratio.copy_abs() < _LARGE_ABS_SURPRISE_RATIO:
        return "neutral"
    if surprise > ZERO:
        return "positive"
    return "negative"


def _max_rows_as_int(value: Decimal) -> int:
    return int(_require_positive_count("max_rows", value))


def _require_exact_type(value: object, expected_type: type[object], field_name: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be exactly {expected_type.__name__}")


def _validate_hard_flags(field_name: str, value: object) -> None:
    for flag in ("paper_only", "report_only", "readonly"):
        if getattr(value, flag) is not True:
            raise ValueError(f"{field_name} {flag} must be True")


def _payload_value(value: object) -> Any:
    if type(value) is Decimal:
        return format(value.quantize(_DECIMAL_PLACES, rounding=ROUND_HALF_UP), "f")
    if type(value) is datetime:
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _payload_value(getattr(value, field.name))
            for field in fields(value)
        }
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    return value
