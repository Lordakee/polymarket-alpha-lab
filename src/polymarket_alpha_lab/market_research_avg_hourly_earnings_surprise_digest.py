from __future__ import annotations

from dataclasses import dataclass, field, fields, is_dataclass
from datetime import UTC, datetime
from decimal import ROUND_DOWN, ROUND_HALF_EVEN, Decimal
from typing import Any


DEFAULT_AVG_HOURLY_EARNINGS_SURPRISE_DIGEST_CONFIG_VERSION = (
    "avg-hourly-earnings-surprise-v1"
)
RATIO_QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000")

_SURPRISE_DIRECTIONS = ("negative", "inline", "positive")
_DIGEST_STATUSES = ("blocked", "pass", "watch")
_DIGEST_EMPTY_REASON = "avg_hourly_earnings_surprise_digest_empty"
_STALE_RELEASE_REASON = "avg_hourly_earnings_surprise_release_stale"
_MISSING_EVIDENCE_REASON = "avg_hourly_earnings_surprise_missing_evidence"
_NEGATIVE_SURPRISE_REASON = "avg_hourly_earnings_surprise_negative_present"
_NO_SURPRISE_REASON = "avg_hourly_earnings_surprise_no_surprises"
_POSITIVE_SURPRISE_REASON = "avg_hourly_earnings_surprise_positive_present"
_PROBABILITY_EDGE_REASON = "avg_hourly_earnings_surprise_probability_edge_present"
_REASON_CODES = (
    _DIGEST_EMPTY_REASON,
    _STALE_RELEASE_REASON,
    _MISSING_EVIDENCE_REASON,
    _NEGATIVE_SURPRISE_REASON,
    _NO_SURPRISE_REASON,
    _POSITIVE_SURPRISE_REASON,
    _PROBABILITY_EDGE_REASON,
)
_WATCH_NEXT_STEP = "review_avg_hourly_earnings_surprise_markets"
_EMPTY_NEXT_STEP = "collect_avg_hourly_earnings_surprise_inputs"
_EVIDENCE_NEXT_STEP = "collect_avg_hourly_earnings_surprise_evidence"
_PASS_NEXT_STEP = "continue_avg_hourly_earnings_surprise_monitoring"

__all__ = (
    "DEFAULT_AVG_HOURLY_EARNINGS_SURPRISE_DIGEST_CONFIG_VERSION",
    "AvgHourlyEarningsSurpriseDigestConfig",
    "AvgHourlyEarningsSurpriseInput",
    "AvgHourlyEarningsSurpriseRow",
    "AvgHourlyEarningsSurpriseDigestReport",
    "build_market_research_avg_hourly_earnings_surprise_digest",
    "market_research_avg_hourly_earnings_surprise_digest_payload",
)


@dataclass(frozen=True)
class AvgHourlyEarningsSurpriseDigestConfig:
    config_version: str = DEFAULT_AVG_HOURLY_EARNINGS_SURPRISE_DIGEST_CONFIG_VERSION
    max_release_age_seconds: Decimal = Decimal("31536000.000000")
    min_source_count: Decimal = Decimal("1.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        if self.config_version != DEFAULT_AVG_HOURLY_EARNINGS_SURPRISE_DIGEST_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        object.__setattr__(
            self,
            "max_release_age_seconds",
            _require_positive_decimal(
                "max_release_age_seconds",
                self.max_release_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "min_source_count",
            _require_nonnegative_decimal("min_source_count", self.min_source_count),
        )
        _require_integral_decimal("min_source_count", self.min_source_count)
        _require_hard_flags("AvgHourlyEarningsSurpriseDigestConfig", self)


@dataclass(frozen=True)
class AvgHourlyEarningsSurpriseInput:
    market_id: str
    release_at: datetime
    actual_avg_hourly_earnings_growth: Decimal
    consensus_avg_hourly_earnings_growth: Decimal
    previous_avg_hourly_earnings_growth: Decimal
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
            "actual_avg_hourly_earnings_growth",
            "consensus_avg_hourly_earnings_growth",
            "previous_avg_hourly_earnings_growth",
            "market_probability",
            "threshold_probability",
            "source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "actual_avg_hourly_earnings_growth",
            "consensus_avg_hourly_earnings_growth",
            "previous_avg_hourly_earnings_growth",
        ):
            _require_growth_rate(field_name, getattr(self, field_name))
        _require_nonzero_decimal(
            "consensus_avg_hourly_earnings_growth",
            self.consensus_avg_hourly_earnings_growth,
        )
        for field_name in ("market_probability", "threshold_probability"):
            _require_probability(field_name, getattr(self, field_name))
        _require_integral_decimal("source_count", self.source_count)
        _require_nonnegative_decimal("source_count", self.source_count)
        _require_hard_flags("AvgHourlyEarningsSurpriseInput", self)


@dataclass(frozen=True)
class AvgHourlyEarningsSurpriseRow:
    market_id: str
    release_at: datetime
    actual_avg_hourly_earnings_growth: Decimal
    consensus_avg_hourly_earnings_growth: Decimal
    previous_avg_hourly_earnings_growth: Decimal
    market_probability: Decimal
    threshold_probability: Decimal
    source_count: Decimal
    release_age_seconds: Decimal
    surprise_direction: str
    surprise_growth_points: Decimal
    surprise_ratio: Decimal
    market_probability_edge: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "market_id", _normalize_market_id(self.market_id))
        object.__setattr__(self, "release_at", _as_utc("release_at", self.release_at))
        for field_name in (
            "actual_avg_hourly_earnings_growth",
            "consensus_avg_hourly_earnings_growth",
            "previous_avg_hourly_earnings_growth",
            "market_probability",
            "threshold_probability",
            "source_count",
            "release_age_seconds",
            "surprise_growth_points",
            "surprise_ratio",
            "market_probability_edge",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "actual_avg_hourly_earnings_growth",
            "consensus_avg_hourly_earnings_growth",
            "previous_avg_hourly_earnings_growth",
        ):
            _require_growth_rate(field_name, getattr(self, field_name))
        _require_nonzero_decimal(
            "consensus_avg_hourly_earnings_growth",
            self.consensus_avg_hourly_earnings_growth,
        )
        for field_name in ("market_probability", "threshold_probability"):
            _require_probability(field_name, getattr(self, field_name))
        _require_integral_decimal("source_count", self.source_count)
        _require_nonnegative_decimal("source_count", self.source_count)
        _require_nonnegative_decimal("release_age_seconds", self.release_age_seconds)
        _require_surprise_direction("surprise_direction", self.surprise_direction)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _validate_row_consistency(self)
        _require_hard_flags("AvgHourlyEarningsSurpriseRow", self)


@dataclass(frozen=True)
class AvgHourlyEarningsSurpriseDigestReport:
    generated_at: datetime
    config_version: str
    digest_status: str
    recommended_next_step: str
    input_count: Decimal
    positive_surprise_count: Decimal
    negative_surprise_count: Decimal
    inline_count: Decimal
    stale_release_count: Decimal
    missing_evidence_count: Decimal
    total_source_count: Decimal
    surprise_rows: tuple[AvgHourlyEarningsSurpriseRow, ...]
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
        if self.config_version != DEFAULT_AVG_HOURLY_EARNINGS_SURPRISE_DIGEST_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        _require_digest_status("digest_status", self.digest_status)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        for field_name in (
            "input_count",
            "positive_surprise_count",
            "negative_surprise_count",
            "inline_count",
            "stale_release_count",
            "missing_evidence_count",
            "total_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_decimal(field_name, getattr(self, field_name)),
            )
            _require_integral_decimal(field_name, getattr(self, field_name))
            _require_nonnegative_decimal(field_name, getattr(self, field_name))
        object.__setattr__(self, "surprise_rows", _normalize_surprise_rows(self.surprise_rows))
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _set_report_derived_fields(self)
        _require_hard_flags("AvgHourlyEarningsSurpriseDigestReport", self)
        _validate_report_consistency(self)


def build_market_research_avg_hourly_earnings_surprise_digest(
    inputs: list[AvgHourlyEarningsSurpriseInput] | tuple[AvgHourlyEarningsSurpriseInput, ...],
    *,
    config: AvgHourlyEarningsSurpriseDigestConfig,
    generated_at: datetime,
) -> AvgHourlyEarningsSurpriseDigestReport:
    if type(config) is not AvgHourlyEarningsSurpriseDigestConfig:
        raise ValueError("config must be an AvgHourlyEarningsSurpriseDigestConfig")
    _require_hard_flags("AvgHourlyEarningsSurpriseDigestConfig", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(inputs)
    rows = tuple(
        sorted(
            (
                _surprise_row(item, config=config, generated_at=generated_at_utc)
                for item in normalized_inputs
            ),
            key=_row_sort_key,
        ),
    )
    reason_codes = _reason_codes(rows)
    return AvgHourlyEarningsSurpriseDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        digest_status=_digest_status(reason_codes),
        recommended_next_step=_recommended_next_step(reason_codes),
        input_count=_count_decimal(len(rows)),
        positive_surprise_count=_count_decimal(
            sum(1 for row in rows if row.surprise_direction == "positive"),
        ),
        negative_surprise_count=_count_decimal(
            sum(1 for row in rows if row.surprise_direction == "negative"),
        ),
        inline_count=_count_decimal(
            sum(1 for row in rows if row.surprise_direction == "inline"),
        ),
        stale_release_count=_reason_count(rows, _STALE_RELEASE_REASON),
        missing_evidence_count=_reason_count(rows, _MISSING_EVIDENCE_REASON),
        total_source_count=_sum_decimal(row.source_count for row in rows),
        surprise_rows=rows,
        reason_codes=reason_codes,
    )


def market_research_avg_hourly_earnings_surprise_digest_payload(
    report: AvgHourlyEarningsSurpriseDigestReport,
) -> dict[str, Any]:
    if type(report) is not AvgHourlyEarningsSurpriseDigestReport:
        raise ValueError("report must be an AvgHourlyEarningsSurpriseDigestReport")
    _require_hard_flags("AvgHourlyEarningsSurpriseDigestReport", report)
    return _payload(report)


def _normalize_inputs(
    inputs: list[AvgHourlyEarningsSurpriseInput] | tuple[AvgHourlyEarningsSurpriseInput, ...],
) -> tuple[AvgHourlyEarningsSurpriseInput, ...]:
    if type(inputs) not in (list, tuple):
        raise ValueError("inputs must be a list or tuple")
    normalized = tuple(inputs)
    for item in normalized:
        if type(item) is not AvgHourlyEarningsSurpriseInput:
            raise ValueError("inputs must contain AvgHourlyEarningsSurpriseInput values")
        _require_hard_flags("AvgHourlyEarningsSurpriseInput", item)
    return normalized


def _surprise_row(
    item: AvgHourlyEarningsSurpriseInput,
    *,
    config: AvgHourlyEarningsSurpriseDigestConfig,
    generated_at: datetime,
) -> AvgHourlyEarningsSurpriseRow:
    surprise_growth_points = _quantize(
        item.actual_avg_hourly_earnings_growth
        - item.consensus_avg_hourly_earnings_growth,
    )
    surprise_ratio = _ratio(
        surprise_growth_points,
        item.consensus_avg_hourly_earnings_growth,
    )
    market_probability_edge = _quantize(item.market_probability - item.threshold_probability)
    release_age_seconds = max(_age_seconds(generated_at, item.release_at), ZERO)
    surprise_direction = _surprise_direction(surprise_growth_points)
    return AvgHourlyEarningsSurpriseRow(
        market_id=item.market_id,
        release_at=item.release_at,
        actual_avg_hourly_earnings_growth=item.actual_avg_hourly_earnings_growth,
        consensus_avg_hourly_earnings_growth=item.consensus_avg_hourly_earnings_growth,
        previous_avg_hourly_earnings_growth=item.previous_avg_hourly_earnings_growth,
        market_probability=item.market_probability,
        threshold_probability=item.threshold_probability,
        source_count=item.source_count,
        release_age_seconds=release_age_seconds,
        surprise_direction=surprise_direction,
        surprise_growth_points=surprise_growth_points,
        surprise_ratio=surprise_ratio,
        market_probability_edge=market_probability_edge,
        reason_codes=_row_reason_codes(
            config=config,
            release_age_seconds=release_age_seconds,
            source_count=item.source_count,
            surprise_direction=surprise_direction,
            market_probability_edge=market_probability_edge,
        ),
    )


def _input_sort_key(item: AvgHourlyEarningsSurpriseInput) -> tuple[datetime, str]:
    return (item.release_at, item.market_id)


def _row_sort_key(row: AvgHourlyEarningsSurpriseRow) -> tuple[datetime, str]:
    return (row.release_at, row.market_id)


def _row_reason_codes(
    *,
    config: AvgHourlyEarningsSurpriseDigestConfig,
    release_age_seconds: Decimal,
    source_count: Decimal,
    surprise_direction: str,
    market_probability_edge: Decimal,
) -> tuple[str, ...]:
    codes: list[str] = []
    if release_age_seconds > config.max_release_age_seconds:
        codes.append(_STALE_RELEASE_REASON)
    if source_count < config.min_source_count:
        codes.append(_MISSING_EVIDENCE_REASON)
    if surprise_direction == "negative":
        codes.append(_NEGATIVE_SURPRISE_REASON)
    elif surprise_direction == "positive":
        codes.append(_POSITIVE_SURPRISE_REASON)
    if market_probability_edge > ZERO:
        codes.append(_PROBABILITY_EDGE_REASON)
    if not codes:
        codes.append(_NO_SURPRISE_REASON)
    return _normalize_reason_codes(tuple(codes))


def _reason_codes(rows: tuple[AvgHourlyEarningsSurpriseRow, ...]) -> tuple[str, ...]:
    if not rows:
        return (_DIGEST_EMPTY_REASON,)
    report_codes = {
        reason_code
        for row in rows
        for reason_code in row.reason_codes
        if reason_code != _NO_SURPRISE_REASON
    }
    if not report_codes:
        return (_NO_SURPRISE_REASON,)
    return tuple(reason_code for reason_code in _REASON_CODES if reason_code in report_codes)


def _digest_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == (_DIGEST_EMPTY_REASON,):
        return "blocked"
    if _MISSING_EVIDENCE_REASON in reason_codes:
        return "blocked"
    if reason_codes == (_NO_SURPRISE_REASON,):
        return "pass"
    return "watch"


def _recommended_next_step(reason_codes: tuple[str, ...]) -> str:
    status = _digest_status(reason_codes)
    if reason_codes == (_DIGEST_EMPTY_REASON,):
        return _EMPTY_NEXT_STEP
    if _MISSING_EVIDENCE_REASON in reason_codes:
        return _EVIDENCE_NEXT_STEP
    if status == "pass":
        return _PASS_NEXT_STEP
    return _WATCH_NEXT_STEP


def _set_report_derived_fields(report: AvgHourlyEarningsSurpriseDigestReport) -> None:
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
    probability_edge_count = _count_decimal(
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
                largest_row.consensus_avg_hourly_earnings_growth,
            ),
        ),
    )


def _largest_abs_surprise_row(
    rows: tuple[AvgHourlyEarningsSurpriseRow, ...],
) -> AvgHourlyEarningsSurpriseRow | None:
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
    _require_nonzero_decimal("ratio denominator", total)
    return (value / total).quantize(RATIO_QUANT, rounding=ROUND_DOWN)


def _rounded_ratio(value: Decimal, total: Decimal) -> Decimal:
    _require_nonzero_decimal("ratio denominator", total)
    return (value / total).quantize(RATIO_QUANT, rounding=ROUND_HALF_EVEN)


def _optional_ratio(value: Decimal, total: Decimal) -> Decimal | None:
    if total == ZERO:
        return None
    return _ratio(value, total)


def _validate_row_consistency(row: AvgHourlyEarningsSurpriseRow) -> None:
    if _NO_SURPRISE_REASON in row.reason_codes and row.reason_codes != (_NO_SURPRISE_REASON,):
        raise ValueError("no-surprise rows must only carry the no-surprises reason code")
    if row.surprise_direction == "negative" and _NEGATIVE_SURPRISE_REASON not in row.reason_codes:
        raise ValueError("negative rows must carry the negative surprise reason code")
    if row.surprise_direction == "positive" and _POSITIVE_SURPRISE_REASON not in row.reason_codes:
        raise ValueError("positive rows must carry the positive surprise reason code")
    if row.market_probability_edge > ZERO and _PROBABILITY_EDGE_REASON not in row.reason_codes:
        raise ValueError("probability edge rows must carry the probability edge reason code")
    if (
        row.surprise_direction == "inline"
        and row.market_probability_edge <= ZERO
        and not any(
            reason_code in (_STALE_RELEASE_REASON, _MISSING_EVIDENCE_REASON)
            for reason_code in row.reason_codes
        )
        and row.reason_codes != (_NO_SURPRISE_REASON,)
    ):
        raise ValueError("inline rows without evidence gaps must carry no-surprises")


def _validate_report_consistency(report: AvgHourlyEarningsSurpriseDigestReport) -> None:
    if report.input_count != _count_decimal(len(report.surprise_rows)):
        raise ValueError("input_count must match surprise_rows")
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
    if report.stale_release_count != _reason_count(report.surprise_rows, _STALE_RELEASE_REASON):
        raise ValueError("stale_release_count must match surprise_rows")
    if report.missing_evidence_count != _reason_count(
        report.surprise_rows,
        _MISSING_EVIDENCE_REASON,
    ):
        raise ValueError("missing_evidence_count must match surprise_rows")
    if report.total_source_count != _sum_decimal(
        row.source_count for row in report.surprise_rows
    ):
        raise ValueError("total_source_count must match surprise_rows")
    if report.reason_codes != _reason_codes(report.surprise_rows):
        raise ValueError("reason_codes must match surprise_rows")
    if report.digest_status != _digest_status(report.reason_codes):
        raise ValueError("digest_status must match reason_codes")
    if report.recommended_next_step != _recommended_next_step(report.reason_codes):
        raise ValueError("recommended_next_step must match reason_codes")


def _normalize_surprise_rows(
    rows: tuple[AvgHourlyEarningsSurpriseRow, ...],
) -> tuple[AvgHourlyEarningsSurpriseRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("surprise_rows must be a list or tuple")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not AvgHourlyEarningsSurpriseRow:
            raise ValueError("surprise_rows must contain AvgHourlyEarningsSurpriseRow values")
        _require_hard_flags("AvgHourlyEarningsSurpriseRow", row)
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


def _reason_count(rows: tuple[AvgHourlyEarningsSurpriseRow, ...], reason_code: str) -> Decimal:
    return _count_decimal(sum(1 for row in rows if reason_code in row.reason_codes))


def _count_decimal(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _sum_decimal(values: Any) -> Decimal:
    total = ZERO
    for value in values:
        total += value
    return _quantize(total)


def _age_seconds(generated_at: datetime, release_at: datetime) -> Decimal:
    delta = generated_at - release_at
    microseconds = (
        Decimal(delta.days) * Decimal("86400000000")
        + Decimal(delta.seconds) * Decimal("1000000")
        + Decimal(delta.microseconds)
    )
    return _quantize(microseconds / MICROSECONDS_PER_SECOND)


def _payload(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return {item.name: _payload(getattr(value, item.name)) for item in fields(value)}
    if type(value) is tuple:
        return [_payload(item) for item in value]
    if type(value) is list:
        return [_payload(item) for item in value]
    if type(value) is datetime:
        return value.isoformat()
    if type(value) is Decimal:
        return f"{value.quantize(RATIO_QUANT):f}"
    return value


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


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(RATIO_QUANT)


def _require_growth_rate(field_name: str, value: Decimal) -> None:
    if value < -ONE or value > ONE:
        raise ValueError(f"{field_name} must be between -1 and 1")


def _require_nonzero_decimal(field_name: str, value: Decimal) -> None:
    if value == ZERO:
        raise ValueError(f"{field_name} must be nonzero")


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_nonnegative_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    normalized = _quantize(value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


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
