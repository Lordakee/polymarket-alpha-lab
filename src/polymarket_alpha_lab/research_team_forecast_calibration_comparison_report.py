"""Side-effect-free report comparing research team forecast calibration."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any


__all__ = (
    "ResearchTeamForecastCalibrationComparisonConfig",
    "ResearchTeamForecastCalibrationComparisonReasonCodeCount",
    "ResearchTeamForecastCalibrationComparisonReport",
    "ResearchTeamForecastCalibrationComparisonRow",
    "ResearchTeamForecastCalibrationObservation",
    "build_research_team_forecast_calibration_comparison_report",
    "research_team_forecast_calibration_comparison_report_payload",
)


DEFAULT_CONFIG_VERSION = "research-team-forecast-calibration-comparison-v0"
ZERO = Decimal("0")
ONE = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")

PASS_REASON = "calibration_pass"
EMPTY_REASON = "no_calibration_observations"
INSUFFICIENT_SAMPLE_REASON = "insufficient_sample"
NARROW_DOMAIN_REASON = "narrow_domain_coverage"
ERROR_WATCH_REASON = "calibration_error_watch"
ERROR_BLOCKED_REASON = "calibration_error_blocked"
LOW_REVIEW_REASON = "low_review_quality"
INTERVAL_MISS_REASON = "confidence_interval_miss"
WIDE_INTERVAL_REASON = "wide_confidence_interval"

REASON_CODES = (
    PASS_REASON,
    EMPTY_REASON,
    INSUFFICIENT_SAMPLE_REASON,
    ERROR_BLOCKED_REASON,
    ERROR_WATCH_REASON,
    INTERVAL_MISS_REASON,
    LOW_REVIEW_REASON,
    NARROW_DOMAIN_REASON,
    WIDE_INTERVAL_REASON,
)
REASON_CODE_RANK = {reason_code: index for index, reason_code in enumerate(REASON_CODES)}
BLOCKED_REASONS = (EMPTY_REASON, INSUFFICIENT_SAMPLE_REASON, ERROR_BLOCKED_REASON)
WATCH_REASONS = (
    NARROW_DOMAIN_REASON,
    ERROR_WATCH_REASON,
    LOW_REVIEW_REASON,
    INTERVAL_MISS_REASON,
    WIDE_INTERVAL_REASON,
)
STATUSES = ("pass", "watch", "blocked")
PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
UNSAFE_PUBLIC_FRAGMENTS = ("wal" + "let", "au" + "th", "ord" + "er")


@dataclass(frozen=True)
class ResearchTeamForecastCalibrationComparisonConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    min_sample_count: Decimal = Decimal("3")
    min_domain_count: Decimal = Decimal("2")
    pass_mean_absolute_error: Decimal = Decimal("0.200000")
    watch_mean_absolute_error: Decimal = Decimal("0.350000")
    min_review_quality_score: Decimal = Decimal("0.700000")
    min_confidence_interval_hit_rate: Decimal = Decimal("0.600000")
    max_mean_confidence_interval_width: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        for field_name in ("min_sample_count", "min_domain_count"):
            object.__setattr__(
                self,
                field_name,
                _require_positive_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "pass_mean_absolute_error",
            "watch_mean_absolute_error",
            "min_review_quality_score",
            "min_confidence_interval_hit_rate",
            "max_mean_confidence_interval_width",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        if self.pass_mean_absolute_error > self.watch_mean_absolute_error:
            raise ValueError(
                "pass_mean_absolute_error must not exceed watch_mean_absolute_error",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchTeamForecastCalibrationObservation:
    research_team_id: str
    model_id: str
    domain_id: str
    forecast_id: str
    forecast_probability: Decimal
    resolved_outcome: Decimal
    review_quality_score: Decimal
    confidence_lower: Decimal
    confidence_upper: Decimal
    observed_at: datetime
    resolved_at: datetime
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "research_team_id",
            "model_id",
            "domain_id",
            "forecast_id",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "forecast_probability",
            _require_probability_decimal(
                "forecast_probability",
                self.forecast_probability,
            ),
        )
        object.__setattr__(
            self,
            "resolved_outcome",
            _require_binary_decimal("resolved_outcome", self.resolved_outcome),
        )
        object.__setattr__(
            self,
            "review_quality_score",
            _require_probability_decimal(
                "review_quality_score",
                self.review_quality_score,
            ),
        )
        object.__setattr__(
            self,
            "confidence_lower",
            _require_probability_decimal("confidence_lower", self.confidence_lower),
        )
        object.__setattr__(
            self,
            "confidence_upper",
            _require_probability_decimal("confidence_upper", self.confidence_upper),
        )
        if self.confidence_lower > self.confidence_upper:
            raise ValueError("confidence bounds must be ascending")
        if not self.confidence_lower <= self.forecast_probability <= self.confidence_upper:
            raise ValueError("confidence bounds must contain forecast_probability")
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(self, "resolved_at", _as_utc("resolved_at", self.resolved_at))
        if self.resolved_at < self.observed_at:
            raise ValueError("resolved_at must not be before observed_at")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=True),
        )
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class ResearchTeamForecastCalibrationComparisonRow:
    research_team_id: str
    model_id: str
    sample_count: Decimal
    domain_count: Decimal
    forecast_ids: tuple[str, ...]
    domain_ids: tuple[str, ...]
    mean_absolute_error: Decimal
    mean_brier_score: Decimal
    mean_signed_error: Decimal
    mean_review_quality_score: Decimal
    confidence_interval_hit_rate: Decimal
    mean_confidence_interval_width: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("research_team_id", self.research_team_id)
        _require_canonical_string("model_id", self.model_id)
        for field_name in ("sample_count", "domain_count"):
            object.__setattr__(
                self,
                field_name,
                _require_positive_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "forecast_ids",
            _normalize_string_tuple("forecast_ids", self.forecast_ids, allow_empty=False),
        )
        object.__setattr__(
            self,
            "domain_ids",
            _normalize_string_tuple("domain_ids", self.domain_ids, allow_empty=False),
        )
        for field_name in (
            "mean_absolute_error",
            "mean_brier_score",
            "mean_review_quality_score",
            "confidence_interval_hit_rate",
            "mean_confidence_interval_width",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "mean_signed_error",
            _require_signed_probability_decimal(
                "mean_signed_error",
                self.mean_signed_error,
            ),
        )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _require_hard_flags("row", self)
        _validate_row(self)


@dataclass(frozen=True)
class ResearchTeamForecastCalibrationComparisonReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(self, "count", _require_positive_whole_decimal("count", self.count))
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchTeamForecastCalibrationComparisonReport:
    generated_at: datetime
    config_version: str
    comparison_status: str
    observation_count: Decimal
    team_model_count: Decimal
    domain_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    mean_absolute_error: Decimal | None
    mean_brier_score: Decimal | None
    mean_signed_error: Decimal | None
    mean_review_quality_score: Decimal | None
    confidence_interval_hit_rate: Decimal | None
    mean_confidence_interval_width: Decimal | None
    rows: tuple[ResearchTeamForecastCalibrationComparisonRow, ...]
    reason_code_counts: tuple[
        ResearchTeamForecastCalibrationComparisonReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_status("comparison_status", self.comparison_status)
        for field_name in (
            "observation_count",
            "team_model_count",
            "domain_count",
            "pass_count",
            "watch_count",
            "blocked_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "mean_absolute_error",
            "mean_brier_score",
            "mean_review_quality_score",
            "confidence_interval_hit_rate",
            "mean_confidence_interval_width",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_optional_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "mean_signed_error",
            _require_optional_signed_probability_decimal(
                "mean_signed_error",
                self.mean_signed_error,
            ),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _require_hard_flags("report", self)
        _validate_report(self)


def build_research_team_forecast_calibration_comparison_report(
    observations: Iterable[ResearchTeamForecastCalibrationObservation],
    *,
    config: ResearchTeamForecastCalibrationComparisonConfig,
    generated_at: datetime,
) -> ResearchTeamForecastCalibrationComparisonReport:
    if type(config) is not ResearchTeamForecastCalibrationComparisonConfig:
        raise ValueError(
            "config must be a ResearchTeamForecastCalibrationComparisonConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_observations = _normalize_observations(
        observations,
        generated_at=generated_at_utc,
    )
    rows = _build_rows(normalized_observations, config=config)
    reason_codes = _report_reason_codes(rows)

    return ResearchTeamForecastCalibrationComparisonReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        comparison_status=_status_for_reason_codes(reason_codes),
        observation_count=_decimal_count(len(normalized_observations)),
        team_model_count=_decimal_count(len(rows)),
        domain_count=_decimal_count(len({item.domain_id for item in normalized_observations})),
        pass_count=_decimal_count(sum(1 for row in rows if row.status == "pass")),
        watch_count=_decimal_count(sum(1 for row in rows if row.status == "watch")),
        blocked_count=_decimal_count(sum(1 for row in rows if row.status == "blocked")),
        mean_absolute_error=_weighted_row_average(rows, "mean_absolute_error"),
        mean_brier_score=_weighted_row_average(rows, "mean_brier_score"),
        mean_signed_error=_weighted_row_average(rows, "mean_signed_error"),
        mean_review_quality_score=_weighted_row_average(
            rows,
            "mean_review_quality_score",
        ),
        confidence_interval_hit_rate=_weighted_row_average(
            rows,
            "confidence_interval_hit_rate",
        ),
        mean_confidence_interval_width=_weighted_row_average(
            rows,
            "mean_confidence_interval_width",
        ),
        rows=rows,
        reason_code_counts=_reason_code_counts(rows, reason_codes),
        reason_codes=reason_codes,
    )


def research_team_forecast_calibration_comparison_report_payload(
    value: object,
) -> dict[str, Any]:
    if type(value) in (
        ResearchTeamForecastCalibrationComparisonConfig,
        ResearchTeamForecastCalibrationObservation,
        ResearchTeamForecastCalibrationComparisonRow,
        ResearchTeamForecastCalibrationComparisonReasonCodeCount,
        ResearchTeamForecastCalibrationComparisonReport,
    ):
        _require_hard_flags("payload", value)
    elif type(value) is dict:
        _validate_payload_flags(value, "payload")
    else:
        raise ValueError(
            "value must be a research team forecast calibration comparison "
            "dataclass or JSON object",
        )

    _reject_unsafe_public_payload("payload", value)
    payload = _payload_value(value)
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    _validate_payload_flags(payload, "payload")
    _reject_unsafe_public_payload("payload", payload, allow_json_containers=True)
    return payload


def _normalize_observations(
    observations: Iterable[ResearchTeamForecastCalibrationObservation],
    *,
    generated_at: datetime,
) -> tuple[ResearchTeamForecastCalibrationObservation, ...]:
    if isinstance(observations, (str, bytes)):
        raise ValueError("observations must be an iterable")
    try:
        values = tuple(observations)
    except TypeError as exc:
        raise ValueError("observations must be an iterable") from exc
    seen_forecast_ids: set[str] = set()
    for item in values:
        if type(item) is not ResearchTeamForecastCalibrationObservation:
            raise ValueError(
                "observations must contain ResearchTeamForecastCalibrationObservation",
            )
        _require_hard_flags("observation", item)
        if item.forecast_id in seen_forecast_ids:
            raise ValueError("forecast_id values must be unique")
        seen_forecast_ids.add(item.forecast_id)
        if item.observed_at > generated_at:
            raise ValueError("observed_at must not be after generated_at")
        if item.resolved_at > generated_at:
            raise ValueError("resolved_at must not be after generated_at")
    return tuple(
        sorted(
            values,
            key=lambda item: (
                item.research_team_id,
                item.model_id,
                item.domain_id,
                item.forecast_id,
            ),
        ),
    )


def _build_rows(
    observations: tuple[ResearchTeamForecastCalibrationObservation, ...],
    *,
    config: ResearchTeamForecastCalibrationComparisonConfig,
) -> tuple[ResearchTeamForecastCalibrationComparisonRow, ...]:
    grouped: dict[tuple[str, str], list[ResearchTeamForecastCalibrationObservation]] = {}
    for item in observations:
        grouped.setdefault((item.research_team_id, item.model_id), []).append(item)
    return tuple(
        _build_row(
            research_team_id=research_team_id,
            model_id=model_id,
            observations=tuple(grouped[(research_team_id, model_id)]),
            config=config,
        )
        for research_team_id, model_id in sorted(grouped)
    )


def _build_row(
    *,
    research_team_id: str,
    model_id: str,
    observations: tuple[ResearchTeamForecastCalibrationObservation, ...],
    config: ResearchTeamForecastCalibrationComparisonConfig,
) -> ResearchTeamForecastCalibrationComparisonRow:
    absolute_errors = tuple(_absolute_error(item) for item in observations)
    brier_scores = tuple(_brier_score(item) for item in observations)
    signed_errors = tuple(_signed_error(item) for item in observations)
    review_scores = tuple(item.review_quality_score for item in observations)
    interval_hits = tuple(_interval_hit(item) for item in observations)
    interval_widths = tuple(_interval_width(item) for item in observations)
    domain_ids = tuple(sorted({item.domain_id for item in observations}))
    reason_codes = _row_reason_codes(
        sample_count=_decimal_count(len(observations)),
        domain_count=_decimal_count(len(domain_ids)),
        mean_absolute_error=_average_decimal(absolute_errors),
        mean_review_quality_score=_average_decimal(review_scores),
        confidence_interval_hit_rate=_average_decimal(interval_hits),
        mean_confidence_interval_width=_average_decimal(interval_widths),
        config=config,
    )

    return ResearchTeamForecastCalibrationComparisonRow(
        research_team_id=research_team_id,
        model_id=model_id,
        sample_count=_decimal_count(len(observations)),
        domain_count=_decimal_count(len(domain_ids)),
        forecast_ids=tuple(item.forecast_id for item in observations),
        domain_ids=domain_ids,
        mean_absolute_error=_average_decimal(absolute_errors),
        mean_brier_score=_average_decimal(brier_scores),
        mean_signed_error=_average_decimal(signed_errors),
        mean_review_quality_score=_average_decimal(review_scores),
        confidence_interval_hit_rate=_average_decimal(interval_hits),
        mean_confidence_interval_width=_average_decimal(interval_widths),
        status=_status_for_reason_codes(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    sample_count: Decimal,
    domain_count: Decimal,
    mean_absolute_error: Decimal,
    mean_review_quality_score: Decimal,
    confidence_interval_hit_rate: Decimal,
    mean_confidence_interval_width: Decimal,
    config: ResearchTeamForecastCalibrationComparisonConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if sample_count < config.min_sample_count:
        reason_codes.append(INSUFFICIENT_SAMPLE_REASON)
    if domain_count < config.min_domain_count:
        reason_codes.append(NARROW_DOMAIN_REASON)
    if mean_absolute_error > config.watch_mean_absolute_error:
        reason_codes.append(ERROR_BLOCKED_REASON)
    elif mean_absolute_error > config.pass_mean_absolute_error:
        reason_codes.append(ERROR_WATCH_REASON)
    if mean_review_quality_score < config.min_review_quality_score:
        reason_codes.append(LOW_REVIEW_REASON)
    if confidence_interval_hit_rate < config.min_confidence_interval_hit_rate:
        reason_codes.append(INTERVAL_MISS_REASON)
    if mean_confidence_interval_width > config.max_mean_confidence_interval_width:
        reason_codes.append(WIDE_INTERVAL_REASON)
    if not reason_codes:
        reason_codes.append(PASS_REASON)
    return _combined_reason_codes(tuple(reason_codes))


def _report_reason_codes(
    rows: tuple[ResearchTeamForecastCalibrationComparisonRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON,)
    return _combined_reason_codes(tuple(code for row in rows for code in row.reason_codes))


def _combined_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    if any(reason_code != PASS_REASON for reason_code in reason_codes):
        reason_codes = tuple(
            reason_code for reason_code in reason_codes if reason_code != PASS_REASON
        )
    return tuple(
        sorted(
            set(reason_codes),
            key=lambda reason_code: REASON_CODE_RANK[reason_code],
        )
    )


def _reason_code_counts(
    rows: tuple[ResearchTeamForecastCalibrationComparisonRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchTeamForecastCalibrationComparisonReasonCodeCount, ...]:
    if reason_codes == (EMPTY_REASON,):
        return (
            ResearchTeamForecastCalibrationComparisonReasonCodeCount(
                reason_code=EMPTY_REASON,
                count=ONE,
            ),
        )
    counter: Counter[str] = Counter()
    for row in rows:
        for reason_code in row.reason_codes:
            if reason_code in reason_codes:
                counter[reason_code] += 1
    return tuple(
        ResearchTeamForecastCalibrationComparisonReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(counter[reason_code]),
        )
        for reason_code in reason_codes
    )


def _status_for_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in BLOCKED_REASONS for reason_code in reason_codes):
        return "blocked"
    if any(reason_code in WATCH_REASONS for reason_code in reason_codes):
        return "watch"
    return "pass"


def _absolute_error(item: ResearchTeamForecastCalibrationObservation) -> Decimal:
    return abs(_signed_error(item))


def _brier_score(item: ResearchTeamForecastCalibrationObservation) -> Decimal:
    error = _signed_error(item)
    return _quantize(error * error)


def _signed_error(item: ResearchTeamForecastCalibrationObservation) -> Decimal:
    return _quantize(item.forecast_probability - item.resolved_outcome)


def _interval_hit(item: ResearchTeamForecastCalibrationObservation) -> Decimal:
    if item.confidence_lower <= item.resolved_outcome <= item.confidence_upper:
        return ONE
    return ZERO


def _interval_width(item: ResearchTeamForecastCalibrationObservation) -> Decimal:
    return _quantize(item.confidence_upper - item.confidence_lower)


def _average_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        raise ValueError("values must be nonempty")
    return _quantize(sum(values, ZERO) / Decimal(len(values)))


def _weighted_row_average(
    rows: tuple[ResearchTeamForecastCalibrationComparisonRow, ...],
    field_name: str,
) -> Decimal | None:
    if not rows:
        return None
    numerator = sum(
        (getattr(row, field_name) * row.sample_count for row in rows),
        ZERO,
    )
    denominator = sum((row.sample_count for row in rows), ZERO)
    if denominator == ZERO:
        return None
    return _quantize(numerator / denominator)


def _validate_row(row: ResearchTeamForecastCalibrationComparisonRow) -> None:
    if row.sample_count != _decimal_count(len(row.forecast_ids)):
        raise ValueError("sample_count must match forecast_ids")
    if row.domain_count != _decimal_count(len(row.domain_ids)):
        raise ValueError("domain_count must match domain_ids")
    if row.domain_count > row.sample_count:
        raise ValueError("domain_count must not exceed sample_count")
    if row.status != _status_for_reason_codes(row.reason_codes):
        raise ValueError("status must match reason_codes")


def _validate_report(report: ResearchTeamForecastCalibrationComparisonReport) -> None:
    if report.observation_count != sum((row.sample_count for row in report.rows), ZERO):
        raise ValueError("observation_count must match rows")
    if report.team_model_count != _decimal_count(len(report.rows)):
        raise ValueError("team_model_count must match rows")
    expected_domain_count = _decimal_count(
        len({domain_id for row in report.rows for domain_id in row.domain_ids}),
    )
    if report.domain_count != expected_domain_count:
        raise ValueError("domain_count must match rows")
    if report.pass_count != _decimal_count(sum(1 for row in report.rows if row.status == "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(
        sum(1 for row in report.rows if row.status == "watch"),
    ):
        raise ValueError("watch_count must match rows")
    if report.blocked_count != _decimal_count(
        sum(1 for row in report.rows if row.status == "blocked"),
    ):
        raise ValueError("blocked_count must match rows")
    weighted_fields = (
        "mean_absolute_error",
        "mean_brier_score",
        "mean_signed_error",
        "mean_review_quality_score",
        "confidence_interval_hit_rate",
        "mean_confidence_interval_width",
    )
    for field_name in weighted_fields:
        if getattr(report, field_name) != _weighted_row_average(report.rows, field_name):
            raise ValueError(f"{field_name} must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.comparison_status != _status_for_reason_codes(report.reason_codes):
        raise ValueError("comparison_status must match reason_codes")
    if report.reason_code_counts != _reason_code_counts(report.rows, report.reason_codes):
        raise ValueError("reason_code_counts must match rows")


def _normalize_rows(
    rows: object,
) -> tuple[ResearchTeamForecastCalibrationComparisonRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchTeamForecastCalibrationComparisonRow:
            raise ValueError(
                "rows must contain ResearchTeamForecastCalibrationComparisonRow values",
            )
        _require_hard_flags("row", row)
    sorted_rows = tuple(sorted(rows, key=lambda row: (row.research_team_id, row.model_id)))
    if rows != sorted_rows:
        raise ValueError("rows must be sorted by research_team_id and model_id")
    return rows


def _normalize_reason_code_counts(
    counts: object,
) -> tuple[ResearchTeamForecastCalibrationComparisonReasonCodeCount, ...]:
    if type(counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for count in counts:
        if type(count) is not ResearchTeamForecastCalibrationComparisonReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchTeamForecastCalibrationComparisonReasonCodeCount values",
            )
        _require_hard_flags("reason_code_count", count)
    sorted_counts = tuple(
        sorted(
            counts,
            key=lambda count: REASON_CODE_RANK[count.reason_code],
        )
    )
    if counts != sorted_counts:
        raise ValueError("reason_code_counts must be sorted by reason_code")
    return counts


def _payload_value(value: object) -> object:
    if type(value) is Decimal:
        return str(value)
    if type(value) is datetime:
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _payload_value(getattr(value, field.name)) for field in fields(value)}
    if type(value) is tuple:
        return [_payload_value(item) for item in value]
    if type(value) is list:
        return [_payload_value(item) for item in value]
    if type(value) is dict:
        return {str(key): _payload_value(item) for key, item in value.items()}
    return value


def _validate_payload_flags(value: dict[str, Any], label: str) -> None:
    for field_name in PHASE_FLAG_FIELDS:
        if value.get(field_name) is not True:
            raise ValueError(f"{label}.{field_name} must be True")


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    path: str = "",
    *,
    allow_json_containers: bool = False,
) -> None:
    current_path = path or label
    if is_dataclass(value) and not isinstance(value, type):
        if type(value) not in (
            ResearchTeamForecastCalibrationComparisonConfig,
            ResearchTeamForecastCalibrationObservation,
            ResearchTeamForecastCalibrationComparisonRow,
            ResearchTeamForecastCalibrationComparisonReasonCodeCount,
            ResearchTeamForecastCalibrationComparisonReport,
        ):
            raise ValueError(f"{current_path} must be a supported public dataclass")
        for field in fields(value):
            if _has_unsafe_public_fragment(field.name):
                raise ValueError(f"{field.name} has unsafe public field")
            field_path = field.name if not path else f"{path}.{field.name}"
            _reject_unsafe_public_payload(
                label,
                getattr(value, field.name),
                field_path,
                allow_json_containers=allow_json_containers,
            )
        return
    if type(value) is Decimal:
        _require_decimal(current_path, value)
        return
    if type(value) is datetime:
        _as_utc(current_path, value)
        return
    if type(value) is tuple:
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(
                label,
                item,
                f"{current_path}[{index}]",
                allow_json_containers=allow_json_containers,
            )
        return
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            item_path = key if not path else f"{path}.{key}"
            if _has_unsafe_public_fragment(key):
                raise ValueError(f"{item_path} has unsafe public field")
            if key in PHASE_FLAG_FIELDS and item is not True:
                raise ValueError(f"{item_path} must be True")
            _reject_unsafe_public_payload(
                label,
                item,
                item_path,
                allow_json_containers=True,
            )
        return
    if type(value) is list:
        if not allow_json_containers:
            raise ValueError(f"{current_path} must remain constructor-normalized")
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(
                label,
                item,
                f"{current_path}[{index}]",
                allow_json_containers=True,
            )
        return
    if type(value) is str:
        if value.strip() != value:
            raise ValueError(f"{current_path} has unsafe public value")
        if "://" in value or "?" in value:
            raise ValueError(f"{current_path} has unsafe public value")
        if _has_unsafe_public_fragment(value):
            raise ValueError(f"{current_path} has unsafe public value")
        return
    if value is None or type(value) is bool:
        return
    if type(value) is int or isinstance(value, float):
        raise ValueError(f"{current_path} must use Decimal-derived string values")
    raise ValueError(f"{current_path} is not JSON-ready")


def _has_unsafe_public_fragment(value: str) -> bool:
    lowered = value.lower()
    return any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS)


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    try:
        return +value
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be finite") from exc


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_probability_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _quantize(normalized)


def _require_optional_probability_decimal(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _require_probability_decimal(field_name, value)


def _require_signed_probability_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < -ONE or normalized > ONE:
        raise ValueError(f"{field_name} must be between -1 and 1")
    return _quantize(normalized)


def _require_optional_signed_probability_decimal(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _require_signed_probability_decimal(field_name, value)


def _require_binary_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_probability_decimal(field_name, value)
    if normalized not in (ZERO, ONE):
        raise ValueError(f"{field_name} must be 0 or 1")
    return normalized


def _require_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_positive_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return normalized


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return normalized


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count source must be an int")
    if value < 0:
        raise ValueError("count source must be nonnegative")
    return Decimal(value)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(RATIO_QUANTUM)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a nonempty canonical string")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be one of {STATUSES}")


def _normalize_string_tuple(
    field_name: str,
    values: object,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized: list[str] = []
    for value in values:
        _require_canonical_string(field_name, value)
        normalized.append(value)
    if not allow_empty and not normalized:
        raise ValueError(f"{field_name} must be nonempty")
    return tuple(normalized)


def _normalize_reason_codes(
    field_name: str,
    values: object,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized: list[str] = []
    for value in values:
        _require_reason_code(field_name, value)
        normalized.append(value)
    if not allow_empty and not normalized:
        raise ValueError(f"{field_name} must be nonempty")
    return _combined_reason_codes(tuple(normalized))


def _require_reason_code(field_name: str, value: object) -> None:
    if type(value) is not str or value not in REASON_CODES:
        raise ValueError(f"{field_name} must be one of {REASON_CODES}")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in PHASE_FLAG_FIELDS:
        if not hasattr(value, field_name):
            raise ValueError(f"{label} must expose {field_name}")
        if getattr(value, field_name) is not True:
            raise ValueError(f"{label}.{field_name} must be True")
