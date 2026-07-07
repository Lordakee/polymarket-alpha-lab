"""Pure report for domain-level probability calibration benchmarks."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, localcontext
from typing import Any

from polymarket_alpha_lab.team_paper_guard import require_paper_only_flags


DEFAULT_RESEARCH_DOMAIN_CALIBRATION_BENCHMARK_CONFIG_VERSION = (
    "research-domain-calibration-benchmark-report-v0"
)
DEFAULT_DOMAIN_IDS = (
    "basketball",
    "btc",
    "football",
    "gold",
    "politics",
    "stock_index",
)

STATUSES = ("pass", "watch", "block")
PASS_REASON = "research_domain_calibration_benchmark_pass"
NO_SAMPLES_REASON = "research_domain_calibration_benchmark_no_resolved_samples"
LOW_SAMPLE_BLOCK_REASON = "research_domain_calibration_benchmark_sample_size_block"
LOW_SAMPLE_WATCH_REASON = "research_domain_calibration_benchmark_sample_size_watch"
HIGH_ERROR_BLOCK_REASON = "research_domain_calibration_benchmark_historical_error_block"
HIGH_ERROR_WATCH_REASON = "research_domain_calibration_benchmark_historical_error_watch"
LOW_REVIEW_BLOCK_REASON = "research_domain_calibration_benchmark_postmortem_quality_block"
LOW_REVIEW_WATCH_REASON = "research_domain_calibration_benchmark_postmortem_quality_watch"
OUTSIDE_CI_REASON = (
    "research_domain_calibration_benchmark_forecast_outside_confidence_interval"
)

REASON_CODE_RANK = {
    NO_SAMPLES_REASON: 0,
    LOW_SAMPLE_BLOCK_REASON: 1,
    HIGH_ERROR_BLOCK_REASON: 2,
    LOW_REVIEW_BLOCK_REASON: 3,
    LOW_SAMPLE_WATCH_REASON: 4,
    HIGH_ERROR_WATCH_REASON: 5,
    LOW_REVIEW_WATCH_REASON: 6,
    OUTSIDE_CI_REASON: 7,
    PASS_REASON: 8,
}

ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
RATIO_QUANTUM = Decimal("0.000001")
DECIMAL_CONTEXT = Context(prec=64)

__all__ = (
    "DEFAULT_RESEARCH_DOMAIN_CALIBRATION_BENCHMARK_CONFIG_VERSION",
    "ResearchDomainCalibrationBenchmarkConfig",
    "ResearchDomainCalibrationBenchmarkReasonCodeCount",
    "ResearchDomainCalibrationBenchmarkReport",
    "ResearchDomainCalibrationBenchmarkRow",
    "ResearchDomainCalibrationBenchmarkSource",
    "build_research_domain_calibration_benchmark_report",
    "research_domain_calibration_benchmark_report_payload",
)


@dataclass(frozen=True)
class ResearchDomainCalibrationBenchmarkConfig:
    config_version: str = DEFAULT_RESEARCH_DOMAIN_CALIBRATION_BENCHMARK_CONFIG_VERSION
    domain_ids: tuple[str, ...] = DEFAULT_DOMAIN_IDS
    pass_min_sample_size: Decimal = Decimal("50")
    watch_min_sample_size: Decimal = Decimal("20")
    pass_max_historical_error: Decimal = Decimal("0.050000")
    watch_max_historical_error: Decimal = Decimal("0.120000")
    pass_min_postmortem_quality: Decimal = Decimal("0.850000")
    watch_min_postmortem_quality: Decimal = Decimal("0.600000")
    confidence_interval_z_score: Decimal = Decimal("1.960000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchDomainCalibrationBenchmarkConfig does not support subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not ResearchDomainCalibrationBenchmarkConfig:
            raise ValueError(
                "config must be exactly ResearchDomainCalibrationBenchmarkConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "domain_ids",
            _normalize_domain_ids("domain_ids", self.domain_ids),
        )
        for field_name in ("pass_min_sample_size", "watch_min_sample_size"):
            object.__setattr__(
                self,
                field_name,
                _require_positive_whole_decimal(field_name, getattr(self, field_name)),
            )
        if self.pass_min_sample_size <= self.watch_min_sample_size:
            raise ValueError(
                "pass_min_sample_size must be greater than watch_min_sample_size",
            )
        for field_name in (
            "pass_max_historical_error",
            "watch_max_historical_error",
            "pass_min_postmortem_quality",
            "watch_min_postmortem_quality",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        if self.pass_max_historical_error >= self.watch_max_historical_error:
            raise ValueError(
                "pass_max_historical_error must be less than watch_max_historical_error",
            )
        if self.pass_min_postmortem_quality <= self.watch_min_postmortem_quality:
            raise ValueError(
                "pass_min_postmortem_quality must be greater than "
                "watch_min_postmortem_quality",
            )
        object.__setattr__(
            self,
            "confidence_interval_z_score",
            _require_positive_decimal(
                "confidence_interval_z_score",
                self.confidence_interval_z_score,
            ),
        )
        require_paper_only_flags("research domain calibration benchmark config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchDomainCalibrationBenchmarkSource:
    domain_id: str
    forecast_id: str
    forecast_probability: Decimal
    resolved_outcome: Decimal
    postmortem_quality_score: Decimal
    resolved_at: datetime
    reviewed_at: datetime
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchDomainCalibrationBenchmarkSource does not support subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not ResearchDomainCalibrationBenchmarkSource:
            raise ValueError(
                "source must be exactly ResearchDomainCalibrationBenchmarkSource",
            )
        _require_canonical_string("domain_id", self.domain_id)
        _require_canonical_string("forecast_id", self.forecast_id)
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
            "postmortem_quality_score",
            _require_probability_decimal(
                "postmortem_quality_score",
                self.postmortem_quality_score,
            ),
        )
        object.__setattr__(
            self,
            "resolved_at",
            _as_utc("resolved_at", self.resolved_at),
        )
        object.__setattr__(
            self,
            "reviewed_at",
            _as_utc("reviewed_at", self.reviewed_at),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=True),
        )
        require_paper_only_flags("research domain calibration benchmark source", self)
        _reject_unsafe_public_payload("source", self)


@dataclass(frozen=True)
class ResearchDomainCalibrationBenchmarkRow:
    domain_id: str
    sample_size: Decimal
    average_forecast_probability: Decimal
    observed_probability: Decimal
    historical_error: Decimal
    mean_brier_score: Decimal
    postmortem_quality_score: Decimal
    confidence_interval_lower: Decimal
    confidence_interval_upper: Decimal
    confidence_interval_width: Decimal
    status: str
    forecast_ids: tuple[str, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchDomainCalibrationBenchmarkRow does not support subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not ResearchDomainCalibrationBenchmarkRow:
            raise ValueError("row must be exactly ResearchDomainCalibrationBenchmarkRow")
        _require_canonical_string("domain_id", self.domain_id)
        object.__setattr__(
            self,
            "sample_size",
            _require_nonnegative_whole_decimal("sample_size", self.sample_size),
        )
        for field_name in (
            "average_forecast_probability",
            "observed_probability",
            "historical_error",
            "mean_brier_score",
            "postmortem_quality_score",
            "confidence_interval_lower",
            "confidence_interval_upper",
            "confidence_interval_width",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "forecast_ids",
            _normalize_string_tuple("forecast_ids", self.forecast_ids, allow_empty=True),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _validate_row(self)
        require_paper_only_flags("research domain calibration benchmark row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchDomainCalibrationBenchmarkReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchDomainCalibrationBenchmarkReasonCodeCount "
            "does not support subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not ResearchDomainCalibrationBenchmarkReasonCodeCount:
            raise ValueError(
                "reason count must be exactly "
                "ResearchDomainCalibrationBenchmarkReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_positive_whole_decimal("count", self.count),
        )
        require_paper_only_flags("research domain calibration benchmark reason count", self)
        _reject_unsafe_public_payload("reason count", self)


@dataclass(frozen=True)
class ResearchDomainCalibrationBenchmarkReport:
    generated_at: datetime
    config_version: str
    domain_count: Decimal
    source_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    status: str
    rows: tuple[ResearchDomainCalibrationBenchmarkRow, ...]
    reason_code_counts: tuple[ResearchDomainCalibrationBenchmarkReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchDomainCalibrationBenchmarkReport does not support subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not ResearchDomainCalibrationBenchmarkReport:
            raise ValueError(
                "report must be exactly ResearchDomainCalibrationBenchmarkReport",
            )
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "domain_count",
            "source_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
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
        _validate_report(self)
        require_paper_only_flags("research domain calibration benchmark report", self)
        _reject_unsafe_public_payload("report", self)


def build_research_domain_calibration_benchmark_report(
    source_rows: Iterable[ResearchDomainCalibrationBenchmarkSource],
    *,
    config: ResearchDomainCalibrationBenchmarkConfig,
    generated_at: datetime,
) -> ResearchDomainCalibrationBenchmarkReport:
    if type(config) is not ResearchDomainCalibrationBenchmarkConfig:
        raise ValueError("config must be a ResearchDomainCalibrationBenchmarkConfig")
    require_paper_only_flags("research domain calibration benchmark config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    sources = _normalize_sources(source_rows, config=config, generated_at=generated_at_utc)
    rows = _build_rows(sources, config=config)
    reason_codes = _report_reason_codes(rows)

    return ResearchDomainCalibrationBenchmarkReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        domain_count=_decimal_count(len(rows)),
        source_count=_decimal_count(len(sources)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        status=_report_status(rows),
        rows=rows,
        reason_code_counts=_reason_code_counts(rows, reason_codes),
        reason_codes=reason_codes,
    )


def research_domain_calibration_benchmark_report_payload(value: object) -> dict[str, Any]:
    if isinstance(
        value,
        (
            ResearchDomainCalibrationBenchmarkConfig,
            ResearchDomainCalibrationBenchmarkSource,
            ResearchDomainCalibrationBenchmarkRow,
            ResearchDomainCalibrationBenchmarkReasonCodeCount,
            ResearchDomainCalibrationBenchmarkReport,
        ),
    ):
        require_paper_only_flags("research domain calibration benchmark payload", value)
    elif type(value) is not dict:
        raise ValueError(
            "value must be a research domain calibration benchmark dataclass "
            "or JSON object",
        )
    _reject_unsafe_public_payload("payload", value)
    payload = _payload_value(value)
    if type(payload) is not dict:
        raise ValueError(
            "research domain calibration benchmark payload must be a JSON object",
        )
    _reject_unsafe_public_payload("payload", payload)
    return payload


def _normalize_sources(
    source_rows: Iterable[ResearchDomainCalibrationBenchmarkSource],
    *,
    config: ResearchDomainCalibrationBenchmarkConfig,
    generated_at: datetime,
) -> tuple[ResearchDomainCalibrationBenchmarkSource, ...]:
    if isinstance(source_rows, (str, bytes)):
        raise ValueError("source_rows must be an iterable")
    try:
        values = tuple(source_rows)
    except TypeError as exc:
        raise ValueError("source_rows must be an iterable") from exc

    seen_forecast_ids: set[str] = set()
    sources: list[ResearchDomainCalibrationBenchmarkSource] = []
    configured_domain_ids = set(config.domain_ids)
    for value in values:
        if type(value) is not ResearchDomainCalibrationBenchmarkSource:
            raise ValueError(
                "source_rows must contain ResearchDomainCalibrationBenchmarkSource values",
            )
        require_paper_only_flags("research domain calibration benchmark source", value)
        if value.domain_id not in configured_domain_ids:
            raise ValueError("domain_id must be configured")
        if value.forecast_id in seen_forecast_ids:
            raise ValueError("forecast_id values must be unique")
        seen_forecast_ids.add(value.forecast_id)
        if value.resolved_at > generated_at:
            raise ValueError("resolved_at must not be after generated_at")
        if value.reviewed_at > generated_at:
            raise ValueError("reviewed_at must not be after generated_at")
        sources.append(value)

    return tuple(sorted(sources, key=lambda row: (row.domain_id, row.forecast_id)))


def _build_rows(
    sources: tuple[ResearchDomainCalibrationBenchmarkSource, ...],
    *,
    config: ResearchDomainCalibrationBenchmarkConfig,
) -> tuple[ResearchDomainCalibrationBenchmarkRow, ...]:
    grouped: dict[str, list[ResearchDomainCalibrationBenchmarkSource]] = {
        domain_id: [] for domain_id in config.domain_ids
    }
    for source in sources:
        grouped[source.domain_id].append(source)
    return tuple(
        _build_row(domain_id=domain_id, sources=tuple(grouped[domain_id]), config=config)
        for domain_id in config.domain_ids
    )


def _build_row(
    *,
    domain_id: str,
    sources: tuple[ResearchDomainCalibrationBenchmarkSource, ...],
    config: ResearchDomainCalibrationBenchmarkConfig,
) -> ResearchDomainCalibrationBenchmarkRow:
    if not sources:
        return ResearchDomainCalibrationBenchmarkRow(
            domain_id=domain_id,
            sample_size=ZERO,
            average_forecast_probability=ZERO,
            observed_probability=ZERO,
            historical_error=ZERO,
            mean_brier_score=ZERO,
            postmortem_quality_score=ZERO,
            confidence_interval_lower=ZERO,
            confidence_interval_upper=ZERO,
            confidence_interval_width=ZERO,
            status="block",
            forecast_ids=(),
            reason_codes=(NO_SAMPLES_REASON,),
        )

    sample_size = _decimal_count(len(sources))
    average_forecast_probability = _average_decimal(
        tuple(source.forecast_probability for source in sources),
    )
    observed_probability = _average_decimal(tuple(source.resolved_outcome for source in sources))
    historical_error = _abs_probability(
        average_forecast_probability - observed_probability,
    )
    mean_brier_score = _average_decimal(
        tuple(
            _square(source.forecast_probability - source.resolved_outcome)
            for source in sources
        ),
    )
    postmortem_quality_score = _average_decimal(
        tuple(source.postmortem_quality_score for source in sources),
    )
    lower, upper = _confidence_interval(
        observed_probability=observed_probability,
        sample_size=sample_size,
        z_score=config.confidence_interval_z_score,
    )
    reason_codes = _row_reason_codes(
        average_forecast_probability=average_forecast_probability,
        confidence_interval_lower=lower,
        confidence_interval_upper=upper,
        historical_error=historical_error,
        postmortem_quality_score=postmortem_quality_score,
        sample_size=sample_size,
        config=config,
    )

    return ResearchDomainCalibrationBenchmarkRow(
        domain_id=domain_id,
        sample_size=sample_size,
        average_forecast_probability=average_forecast_probability,
        observed_probability=observed_probability,
        historical_error=historical_error,
        mean_brier_score=mean_brier_score,
        postmortem_quality_score=postmortem_quality_score,
        confidence_interval_lower=lower,
        confidence_interval_upper=upper,
        confidence_interval_width=_abs_probability(upper - lower),
        status=_status_for_reason_codes(reason_codes),
        forecast_ids=tuple(source.forecast_id for source in sources),
        reason_codes=reason_codes,
    )


def _confidence_interval(
    *,
    observed_probability: Decimal,
    sample_size: Decimal,
    z_score: Decimal,
) -> tuple[Decimal, Decimal]:
    if sample_size <= ZERO:
        return ZERO, ZERO
    variance = observed_probability * (ONE - observed_probability)
    with localcontext(DECIMAL_CONTEXT):
        standard_error = (variance / sample_size).sqrt()
        margin = z_score * standard_error
    lower = _clamp_probability(observed_probability - margin)
    upper = _clamp_probability(observed_probability + margin)
    return lower, upper


def _row_reason_codes(
    *,
    average_forecast_probability: Decimal,
    confidence_interval_lower: Decimal,
    confidence_interval_upper: Decimal,
    historical_error: Decimal,
    postmortem_quality_score: Decimal,
    sample_size: Decimal,
    config: ResearchDomainCalibrationBenchmarkConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if sample_size < config.watch_min_sample_size:
        reason_codes.append(LOW_SAMPLE_BLOCK_REASON)
    elif sample_size < config.pass_min_sample_size:
        reason_codes.append(LOW_SAMPLE_WATCH_REASON)

    if historical_error > config.watch_max_historical_error:
        reason_codes.append(HIGH_ERROR_BLOCK_REASON)
    elif historical_error > config.pass_max_historical_error:
        reason_codes.append(HIGH_ERROR_WATCH_REASON)

    if postmortem_quality_score < config.watch_min_postmortem_quality:
        reason_codes.append(LOW_REVIEW_BLOCK_REASON)
    elif postmortem_quality_score < config.pass_min_postmortem_quality:
        reason_codes.append(LOW_REVIEW_WATCH_REASON)

    if (
        average_forecast_probability < confidence_interval_lower
        or average_forecast_probability > confidence_interval_upper
    ):
        reason_codes.append(OUTSIDE_CI_REASON)

    if not reason_codes:
        reason_codes.append(PASS_REASON)
    return _ranked_reason_codes(tuple(reason_codes))


def _report_reason_codes(
    rows: tuple[ResearchDomainCalibrationBenchmarkRow, ...],
) -> tuple[str, ...]:
    reason_codes = tuple(reason_code for row in rows for reason_code in row.reason_codes)
    if all(reason_code == PASS_REASON for reason_code in reason_codes):
        return (PASS_REASON,)
    return _ranked_reason_codes(
        tuple(reason_code for reason_code in reason_codes if reason_code != PASS_REASON),
    )


def _reason_code_counts(
    rows: tuple[ResearchDomainCalibrationBenchmarkRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchDomainCalibrationBenchmarkReasonCodeCount, ...]:
    counter: Counter[str] = Counter()
    for row in rows:
        counter.update(row.reason_codes)
    if reason_codes == (PASS_REASON,):
        counter = Counter({PASS_REASON: len(rows)})
    return tuple(
        ResearchDomainCalibrationBenchmarkReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(counter[reason_code]),
        )
        for reason_code in reason_codes
    )


def _status_for_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(
        reason_code
        in {
            NO_SAMPLES_REASON,
            LOW_SAMPLE_BLOCK_REASON,
            HIGH_ERROR_BLOCK_REASON,
            LOW_REVIEW_BLOCK_REASON,
        }
        for reason_code in reason_codes
    ):
        return "block"
    if reason_codes == (PASS_REASON,):
        return "pass"
    return "watch"


def _report_status(rows: tuple[ResearchDomainCalibrationBenchmarkRow, ...]) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _status_count(
    rows: tuple[ResearchDomainCalibrationBenchmarkRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.status == status))


def _validate_row(row: ResearchDomainCalibrationBenchmarkRow) -> None:
    if row.sample_size != _decimal_count(len(row.forecast_ids)):
        raise ValueError("sample_size must match forecast_ids")
    if row.confidence_interval_lower > row.confidence_interval_upper:
        raise ValueError("confidence interval lower bound must not exceed upper bound")
    if row.confidence_interval_width != _abs_probability(
        row.confidence_interval_upper - row.confidence_interval_lower,
    ):
        raise ValueError("confidence_interval_width must match bounds")
    if row.status != _status_for_reason_codes(row.reason_codes):
        raise ValueError("status must match reason_codes")
    if row.sample_size == ZERO:
        zero_fields = (
            "average_forecast_probability",
            "observed_probability",
            "historical_error",
            "mean_brier_score",
            "postmortem_quality_score",
            "confidence_interval_lower",
            "confidence_interval_upper",
            "confidence_interval_width",
        )
        if any(getattr(row, field_name) != ZERO for field_name in zero_fields):
            raise ValueError("empty domain benchmark rows must use zero metrics")
        if row.reason_codes != (NO_SAMPLES_REASON,):
            raise ValueError("empty domain benchmark rows must use no sample reason")


def _validate_report(report: ResearchDomainCalibrationBenchmarkReport) -> None:
    if report.domain_count != _decimal_count(len(report.rows)):
        raise ValueError("domain_count must match rows")
    if report.source_count != sum((row.sample_size for row in report.rows), ZERO):
        raise ValueError("source_count must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, "block"):
        raise ValueError("block_count must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows, report.reason_codes):
        raise ValueError("reason_code_counts must match rows")


def _normalize_rows(
    rows: object,
) -> tuple[ResearchDomainCalibrationBenchmarkRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchDomainCalibrationBenchmarkRow:
            raise ValueError(
                "rows must contain ResearchDomainCalibrationBenchmarkRow values",
            )
        require_paper_only_flags("research domain calibration benchmark row", row)
    sorted_rows = tuple(sorted(rows, key=lambda row: row.domain_id))
    if rows != sorted_rows:
        raise ValueError("rows must be sorted by domain_id")
    return rows


def _normalize_reason_code_counts(
    counts: object,
) -> tuple[ResearchDomainCalibrationBenchmarkReasonCodeCount, ...]:
    if type(counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for count in counts:
        if type(count) is not ResearchDomainCalibrationBenchmarkReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchDomainCalibrationBenchmarkReasonCodeCount values",
            )
        require_paper_only_flags(
            "research domain calibration benchmark reason count",
            count,
        )
    ranked_counts = tuple(
        sorted(counts, key=lambda count: REASON_CODE_RANK[count.reason_code]),
    )
    if counts != ranked_counts:
        raise ValueError("reason_code_counts must be sorted by reason_code rank")
    return counts


def _payload_value(value: object) -> object:
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("payload Decimal values must be exactly Decimal")
        return str(value)
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("payload datetime values must be exactly datetime")
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _payload_value(getattr(value, field.name))
            for field in fields(value)
        }
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    if isinstance(value, list):
        return [_payload_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _payload_value(item) for key, item in value.items()}
    return value


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    path: str = "",
) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, _dataclass_public_dict(value), path)
        return
    if type(value) is str:
        lowered = value.lower()
        unsafe_fragments = (
            "://",
            "api_key",
            "authorization",
            "bearer",
            "email",
            "password",
            "private",
            "secret",
            "token",
        )
        if any(fragment in lowered for fragment in unsafe_fragments):
            raise ValueError(f"{path or label} has unsafe public value")
        return
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError(f"{path or label} must be exactly Decimal")
        if not value.is_finite():
            raise ValueError(f"{path or label} must be finite")
        return
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError(f"{path or label} must be exactly datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(f"{path or label} must be timezone-aware")
        return
    if value is None or type(value) is bool:
        return
    if type(value) in (int, float):
        raise ValueError(f"{path or label} must use Decimal numeric values")
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            item_path = key if not path else f"{path}.{key}"
            if key in {"paper_only", "report_only", "readonly"} and item is not True:
                raise ValueError(f"{item_path} must be True")
            _reject_unsafe_public_payload(label, key, item_path)
            _reject_unsafe_public_payload(label, item, item_path)
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            item_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_unsafe_public_payload(label, item, item_path)
        return
    raise ValueError(f"{path or label} is not JSON serializable")


def _dataclass_public_dict(value: object) -> dict[str, object]:
    return {field.name: getattr(value, field.name) for field in fields(value)}


def _normalize_domain_ids(field_name: str, values: object) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized = _normalize_string_tuple(field_name, values, allow_empty=False)
    sorted_unique = tuple(sorted(set(normalized)))
    if normalized != sorted_unique:
        raise ValueError(f"{field_name} must be unique and sorted")
    return normalized


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
    return _ranked_reason_codes(tuple(normalized))


def _ranked_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    unknown = tuple(reason_code for reason_code in reason_codes if reason_code not in REASON_CODE_RANK)
    if unknown:
        raise ValueError("reason_codes must be known benchmark reason codes")
    return tuple(sorted(set(reason_codes), key=lambda reason: REASON_CODE_RANK[reason]))


def _require_reason_code(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if value not in REASON_CODE_RANK:
        raise ValueError(f"{field_name} must be a known benchmark reason code")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a nonempty canonical string")


def _as_utc(field_name: str, value: object) -> datetime:
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
    return _ratio(normalized)


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
    return Decimal(value).quantize(RATIO_QUANTUM)


def _average_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        raise ValueError("values must be nonempty")
    return _ratio(sum(values, ZERO) / _decimal_count(len(values)))


def _square(value: Decimal) -> Decimal:
    return _ratio(value * value)


def _abs_probability(value: Decimal) -> Decimal:
    return _ratio(abs(value))


def _clamp_probability(value: Decimal) -> Decimal:
    return _ratio(min(ONE, max(ZERO, value)))


def _ratio(value: Decimal) -> Decimal:
    return value.quantize(RATIO_QUANTUM)
