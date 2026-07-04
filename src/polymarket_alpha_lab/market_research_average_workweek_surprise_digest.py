from __future__ import annotations

from dataclasses import dataclass, field, fields, is_dataclass
from datetime import UTC, datetime
from decimal import ROUND_DOWN, ROUND_HALF_EVEN, Decimal
from typing import Any


DEFAULT_AVERAGE_WORKWEEK_SURPRISE_DIGEST_CONFIG_VERSION = (
    "average-workweek-surprise-v1"
)
RATIO_QUANT = Decimal("0.000001")
ZERO = Decimal("0")
ONE = Decimal("1")
MICROSECONDS_PER_SECOND = Decimal("1000000")

_SURPRISE_DIRECTIONS = ("negative", "inline", "positive")
_DIGEST_STATUSES = ("blocked", "pass", "watch")
_REASON_CODES = (
    "average_workweek_surprise_digest_empty",
    "average_workweek_surprise_negative_present",
    "average_workweek_surprise_no_surprises",
    "average_workweek_surprise_positive_present",
    "average_workweek_surprise_probability_edge_present",
    "average_workweek_surprise_stale_evidence_present",
    "average_workweek_surprise_missing_evidence_present",
)
_WATCH_NEXT_STEP = "review_average_workweek_surprise_markets"
_EMPTY_NEXT_STEP = "collect_average_workweek_surprise_inputs"
_PASS_NEXT_STEP = "continue_average_workweek_surprise_monitoring"
_EVIDENCE_NEXT_STEP = "repair_average_workweek_surprise_evidence"
_UNSAFE_TEXT_FRAGMENTS = (
    "api_key",
    "apikey",
    "auth",
    "bearer",
    "credential",
    "private" + "_key",
    "secret",
    "token",
    "wal" "let",
)

__all__ = (
    "AverageWorkweekSurpriseDigestConfig",
    "AverageWorkweekSurpriseInput",
    "AverageWorkweekSurpriseRow",
    "AverageWorkweekSurpriseDigestReport",
    "build_market_research_average_workweek_surprise_digest",
    "market_research_average_workweek_surprise_digest_payload",
)


@dataclass(frozen=True)
class AverageWorkweekSurpriseDigestConfig:
    config_version: str = DEFAULT_AVERAGE_WORKWEEK_SURPRISE_DIGEST_CONFIG_VERSION
    max_evidence_age_seconds: Decimal = Decimal("7200.000000")
    min_source_count: Decimal = Decimal("1.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "max_evidence_age_seconds",
            _require_positive_decimal(
                "max_evidence_age_seconds",
                self.max_evidence_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "min_source_count",
            _require_integral_count_decimal("min_source_count", self.min_source_count),
        )
        _require_hard_flags("AverageWorkweekSurpriseDigestConfig", self)


@dataclass(frozen=True)
class AverageWorkweekSurpriseInput:
    market_id: str
    release_at: datetime
    actual_hours: Decimal
    consensus_hours: Decimal
    previous_hours: Decimal
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
            "actual_hours",
            "consensus_hours",
            "previous_hours",
            "market_probability",
            "threshold_probability",
            "source_count",
        ):
            _require_decimal(field_name, getattr(self, field_name))
        for field_name in ("actual_hours", "consensus_hours", "previous_hours"):
            _require_positive_hours(field_name, getattr(self, field_name))
        for field_name in ("market_probability", "threshold_probability"):
            _require_probability(field_name, getattr(self, field_name))
        _require_integral_decimal("source_count", self.source_count)
        _require_nonnegative_decimal("source_count", self.source_count)
        _require_hard_flags("AverageWorkweekSurpriseInput", self)


@dataclass(frozen=True)
class AverageWorkweekSurpriseRow:
    market_id: str
    release_at: datetime
    actual_hours: Decimal
    consensus_hours: Decimal
    previous_hours: Decimal
    market_probability: Decimal
    threshold_probability: Decimal
    source_count: Decimal
    surprise_direction: str
    surprise_hours: Decimal
    surprise_ratio: Decimal
    market_probability_edge: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "market_id", _normalize_market_id(self.market_id))
        object.__setattr__(self, "release_at", _as_utc("release_at", self.release_at))
        for field_name in (
            "actual_hours",
            "consensus_hours",
            "previous_hours",
            "market_probability",
            "threshold_probability",
            "source_count",
            "surprise_hours",
            "surprise_ratio",
            "market_probability_edge",
        ):
            _require_decimal(field_name, getattr(self, field_name))
        for field_name in ("actual_hours", "consensus_hours", "previous_hours"):
            _require_positive_hours(field_name, getattr(self, field_name))
        for field_name in ("market_probability", "threshold_probability"):
            _require_probability(field_name, getattr(self, field_name))
        _require_surprise_direction("surprise_direction", self.surprise_direction)
        _require_integral_decimal("source_count", self.source_count)
        _require_nonnegative_decimal("source_count", self.source_count)
        _require_hard_flags("AverageWorkweekSurpriseRow", self)


@dataclass(frozen=True)
class AverageWorkweekSurpriseDigestReport:
    generated_at: datetime
    config_version: str
    digest_status: str
    recommended_next_step: str
    input_count: Decimal
    positive_surprise_count: Decimal
    negative_surprise_count: Decimal
    inline_count: Decimal
    total_source_count: Decimal
    stale_evidence_count: Decimal
    missing_evidence_count: Decimal
    max_evidence_age_seconds: Decimal
    surprise_rows: tuple[AverageWorkweekSurpriseRow, ...]
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
            "stale_evidence_count",
            "missing_evidence_count",
        ):
            _require_integral_decimal(field_name, getattr(self, field_name))
            _require_nonnegative_decimal(field_name, getattr(self, field_name))
        _require_decimal("max_evidence_age_seconds", self.max_evidence_age_seconds)
        _require_nonnegative_decimal(
            "max_evidence_age_seconds",
            self.max_evidence_age_seconds,
        )
        object.__setattr__(self, "surprise_rows", _normalize_surprise_rows(self.surprise_rows))
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _set_report_derived_fields(self)
        _require_hard_flags("AverageWorkweekSurpriseDigestReport", self)
        _validate_report_consistency(self)


def build_market_research_average_workweek_surprise_digest(
    inputs: list[AverageWorkweekSurpriseInput]
    | tuple[AverageWorkweekSurpriseInput, ...],
    *,
    config: AverageWorkweekSurpriseDigestConfig,
    generated_at: datetime,
) -> AverageWorkweekSurpriseDigestReport:
    if type(config) is not AverageWorkweekSurpriseDigestConfig:
        raise ValueError("config must be an AverageWorkweekSurpriseDigestConfig")
    generated_at_utc = _as_utc("generated_at", generated_at)
    _require_hard_flags("AverageWorkweekSurpriseDigestConfig", config)
    normalized_inputs = _normalize_inputs(inputs)
    rows = tuple(_surprise_row(item) for item in sorted(normalized_inputs, key=_input_sort_key))
    stale_evidence_count = _stale_evidence_count(
        rows,
        generated_at=generated_at_utc,
        max_evidence_age_seconds=config.max_evidence_age_seconds,
    )
    missing_evidence_count = _missing_evidence_count(
        rows,
        min_source_count=config.min_source_count,
    )
    max_evidence_age_seconds = _max_evidence_age_seconds(generated_at_utc, rows)
    reason_codes = _reason_codes(
        rows,
        stale_evidence_count=stale_evidence_count,
        missing_evidence_count=missing_evidence_count,
    )
    return AverageWorkweekSurpriseDigestReport(
        generated_at=generated_at_utc,
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
        stale_evidence_count=stale_evidence_count,
        missing_evidence_count=missing_evidence_count,
        max_evidence_age_seconds=max_evidence_age_seconds,
        surprise_rows=rows,
        reason_codes=reason_codes,
    )


def market_research_average_workweek_surprise_digest_payload(
    report: AverageWorkweekSurpriseDigestReport,
) -> dict[str, Any]:
    if type(report) is not AverageWorkweekSurpriseDigestReport:
        raise ValueError("report must be an AverageWorkweekSurpriseDigestReport")
    _validate_tree(report)
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    return payload


def _normalize_inputs(
    inputs: list[AverageWorkweekSurpriseInput]
    | tuple[AverageWorkweekSurpriseInput, ...],
) -> tuple[AverageWorkweekSurpriseInput, ...]:
    if type(inputs) not in (list, tuple):
        raise ValueError("inputs must be a list or tuple")
    normalized = tuple(inputs)
    seen: set[tuple[str, datetime]] = set()
    for item in normalized:
        if type(item) is not AverageWorkweekSurpriseInput:
            raise ValueError("inputs must contain AverageWorkweekSurpriseInput values")
        _require_hard_flags("AverageWorkweekSurpriseInput", item)
        key = (item.market_id, item.release_at)
        if key in seen:
            raise ValueError("market_id/release_at values must be unique")
        seen.add(key)
    return normalized


def _surprise_row(item: AverageWorkweekSurpriseInput) -> AverageWorkweekSurpriseRow:
    surprise_hours = item.actual_hours - item.consensus_hours
    return AverageWorkweekSurpriseRow(
        market_id=item.market_id,
        release_at=item.release_at,
        actual_hours=item.actual_hours,
        consensus_hours=item.consensus_hours,
        previous_hours=item.previous_hours,
        market_probability=item.market_probability,
        threshold_probability=item.threshold_probability,
        source_count=item.source_count,
        surprise_direction=_surprise_direction(surprise_hours),
        surprise_hours=surprise_hours,
        surprise_ratio=_ratio(surprise_hours, item.consensus_hours),
        market_probability_edge=item.market_probability - item.threshold_probability,
    )


def _input_sort_key(item: AverageWorkweekSurpriseInput) -> tuple[datetime, str]:
    return (item.release_at, item.market_id)


def _reason_codes(
    rows: tuple[AverageWorkweekSurpriseRow, ...],
    *,
    stale_evidence_count: Decimal,
    missing_evidence_count: Decimal,
) -> tuple[str, ...]:
    if not rows:
        return ("average_workweek_surprise_digest_empty",)
    codes: list[str] = []
    if any(row.surprise_direction == "negative" for row in rows):
        codes.append("average_workweek_surprise_negative_present")
    if any(row.surprise_direction == "positive" for row in rows):
        codes.append("average_workweek_surprise_positive_present")
    if any(row.market_probability_edge > ZERO for row in rows):
        codes.append("average_workweek_surprise_probability_edge_present")
    if stale_evidence_count > ZERO:
        codes.append("average_workweek_surprise_stale_evidence_present")
    if missing_evidence_count > ZERO:
        codes.append("average_workweek_surprise_missing_evidence_present")
    if not codes:
        codes.append("average_workweek_surprise_no_surprises")
    return tuple(codes)


def _digest_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == ("average_workweek_surprise_digest_empty",):
        return "blocked"
    if "average_workweek_surprise_missing_evidence_present" in reason_codes:
        return "blocked"
    if reason_codes == ("average_workweek_surprise_no_surprises",):
        return "pass"
    return "watch"


def _recommended_next_step(reason_codes: tuple[str, ...]) -> str:
    status = _digest_status(reason_codes)
    if "average_workweek_surprise_missing_evidence_present" in reason_codes:
        return _EVIDENCE_NEXT_STEP
    if status == "blocked":
        return _EMPTY_NEXT_STEP
    if status == "pass":
        return _PASS_NEXT_STEP
    return _WATCH_NEXT_STEP


def _set_report_derived_fields(report: AverageWorkweekSurpriseDigestReport) -> None:
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
        else abs(_rounded_ratio(largest_row.surprise_hours, largest_row.consensus_hours)),
    )


def _largest_abs_surprise_row(
    rows: tuple[AverageWorkweekSurpriseRow, ...],
) -> AverageWorkweekSurpriseRow | None:
    if not rows:
        return None
    return max(rows, key=lambda row: (abs(row.surprise_ratio), row.release_at, row.market_id))


def _stale_evidence_count(
    rows: tuple[AverageWorkweekSurpriseRow, ...],
    *,
    generated_at: datetime,
    max_evidence_age_seconds: Decimal,
) -> Decimal:
    return _count_decimal(
        sum(
            1
            for row in rows
            if _evidence_age_seconds(generated_at, row.release_at) > max_evidence_age_seconds
        ),
    )


def _missing_evidence_count(
    rows: tuple[AverageWorkweekSurpriseRow, ...],
    *,
    min_source_count: Decimal,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.source_count < min_source_count))


def _max_evidence_age_seconds(
    generated_at: datetime,
    rows: tuple[AverageWorkweekSurpriseRow, ...],
) -> Decimal:
    if not rows:
        return _quantize(ZERO)
    return max(_evidence_age_seconds(generated_at, row.release_at) for row in rows)


def _evidence_age_seconds(generated_at: datetime, release_at: datetime) -> Decimal:
    delta = generated_at - release_at
    micros = (
        Decimal(delta.days) * Decimal("86400000000")
        + Decimal(delta.seconds) * MICROSECONDS_PER_SECOND
        + Decimal(delta.microseconds)
    )
    return _quantize(max(ZERO, micros / MICROSECONDS_PER_SECOND))


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


def _count_decimal(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(RATIO_QUANT, rounding=ROUND_HALF_EVEN)


def _validate_report_consistency(report: AverageWorkweekSurpriseDigestReport) -> None:
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
    if report.stale_evidence_count > report.input_count:
        raise ValueError("stale_evidence_count must not exceed input_count")
    if report.missing_evidence_count > report.input_count:
        raise ValueError("missing_evidence_count must not exceed input_count")
    if report.max_evidence_age_seconds != _max_evidence_age_seconds(
        report.generated_at,
        report.surprise_rows,
    ):
        raise ValueError("max_evidence_age_seconds must match surprise_rows")
    if report.reason_codes != _reason_codes(
        report.surprise_rows,
        stale_evidence_count=report.stale_evidence_count,
        missing_evidence_count=report.missing_evidence_count,
    ):
        raise ValueError("reason_codes must match surprise_rows")
    if report.digest_status != _digest_status(report.reason_codes):
        raise ValueError("digest_status must match reason_codes")
    if report.recommended_next_step != _recommended_next_step(report.reason_codes):
        raise ValueError("recommended_next_step must match reason_codes")


def _normalize_surprise_rows(
    rows: tuple[AverageWorkweekSurpriseRow, ...],
) -> tuple[AverageWorkweekSurpriseRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("surprise_rows must be a list or tuple")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not AverageWorkweekSurpriseRow:
            raise ValueError("surprise_rows must contain AverageWorkweekSurpriseRow values")
        _require_hard_flags("AverageWorkweekSurpriseRow", row)
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


def _normalize_market_id(value: object) -> str:
    _require_public_string("market_id", value)
    return value


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a non-empty canonical string")


def _require_public_string(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    lowered = value.lower()
    if any(fragment in lowered for fragment in _UNSAFE_TEXT_FRAGMENTS):
        raise ValueError(f"{field_name} must be public")


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _require_positive_hours(field_name: str, value: Decimal) -> None:
    if value <= ZERO:
        raise ValueError(f"{field_name} must be positive")


def _require_nonnegative_decimal(field_name: str, value: Decimal) -> Decimal:
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return value


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return _quantize(decimal_value)


def _require_integral_decimal(field_name: str, value: Decimal) -> None:
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be an integral Decimal")


def _require_integral_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    _require_integral_decimal(field_name, decimal_value)
    _require_nonnegative_decimal(field_name, decimal_value)
    return _quantize(decimal_value)


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


def _validate_tree(value: object) -> None:
    if is_dataclass(value):
        _require_hard_flags(value.__class__.__name__, value)
        for field_value in fields(value):
            _validate_tree(getattr(value, field_value.name))
    elif type(value) is tuple:
        for item in value:
            _validate_tree(item)


def _json_ready(value: object) -> Any:
    if is_dataclass(value):
        return {field_value.name: _json_ready(getattr(value, field_value.name)) for field_value in fields(value)}
    if type(value) is tuple:
        return [_json_ready(item) for item in value]
    if type(value) is Decimal:
        return format(_quantize(value), "f")
    if type(value) is datetime:
        return value.isoformat()
    return value
