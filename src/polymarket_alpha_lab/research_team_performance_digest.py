"""Pure report-only digest for anonymized research-team performance."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json


DEFAULT_RESEARCH_TEAM_PERFORMANCE_DIGEST_CONFIG_VERSION = (
    "research-team-performance-digest-v0"
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
SCORE_QUANT = Decimal("0.000001")
COUNT_QUANT = Decimal("1")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")

STATUSES = ("pass", "watch", "block")
REPORT_REASON_CODES = (
    "research_team_performance_pass",
    "research_team_performance_watch",
    "research_team_performance_block",
    "research_team_performance_empty",
)
ROW_REASON_CODES = (
    "calibration_stable",
    "calibration_watch",
    "calibration_block",
    "error_patterns_stable",
    "error_patterns_watch",
    "error_patterns_block",
    "review_completion_sufficient",
    "review_completion_watch",
    "review_completion_block",
    "evidence_quality_sufficient",
    "evidence_quality_watch",
    "evidence_quality_block",
    "sample_size_sufficient",
    "sample_size_insufficient",
)
UNSAFE_PUBLIC_TEXT_FRAGMENTS = (
    "candidate_id",
    "candidate-",
    "candidate:",
    "market_id",
    "market_slug",
    "market-",
    "slug",
    "question",
    "source_ref",
    "source_url",
    "source_text",
    "source_id",
    "source-",
    "source:",
    "http://",
    "https://",
    "postgres://",
    "postgresql://",
    "mysql://",
    "sqlite://",
    "dsn",
    "_table",
    "table_",
    "table=",
    "token",
    "wallet",
    "auth",
    "order",
    "trade",
    "position",
    "buy",
    "sell",
    "recommend",
)

__all__ = (
    "DEFAULT_RESEARCH_TEAM_PERFORMANCE_DIGEST_CONFIG_VERSION",
    "ResearchTeamPerformanceDigestConfig",
    "ResearchTeamPerformanceObservation",
    "ResearchTeamPerformanceRow",
    "ResearchTeamPerformanceDigestReport",
    "build_research_team_performance_digest",
    "research_team_performance_digest_payload",
)


@dataclass(frozen=True)
class ResearchTeamPerformanceDigestConfig:
    config_version: str = DEFAULT_RESEARCH_TEAM_PERFORMANCE_DIGEST_CONFIG_VERSION
    calibration_error_weight: Decimal = Decimal("0.300000")
    error_pattern_weight: Decimal = Decimal("0.250000")
    review_gap_weight: Decimal = Decimal("0.200000")
    evidence_gap_weight: Decimal = Decimal("0.250000")
    pass_risk_ceiling: Decimal = Decimal("0.150000")
    watch_risk_ceiling: Decimal = Decimal("0.350000")
    watch_calibration_error_ratio: Decimal = Decimal("0.150000")
    block_calibration_error_ratio: Decimal = Decimal("0.300000")
    watch_error_pattern_rate: Decimal = Decimal("0.150000")
    block_error_pattern_rate: Decimal = Decimal("0.500000")
    watch_review_completion_ratio: Decimal = Decimal("0.850000")
    block_review_completion_ratio: Decimal = Decimal("0.600000")
    watch_evidence_quality_score: Decimal = Decimal("0.750000")
    block_evidence_quality_score: Decimal = Decimal("0.500000")
    min_domain_sample_count: Decimal = Decimal("5")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "config_version",
            _require_public_string("config_version", self.config_version),
        )
        for field_name in (
            "calibration_error_weight",
            "error_pattern_weight",
            "review_gap_weight",
            "evidence_gap_weight",
            "pass_risk_ceiling",
            "watch_risk_ceiling",
            "watch_calibration_error_ratio",
            "block_calibration_error_ratio",
            "watch_error_pattern_rate",
            "block_error_pattern_rate",
            "watch_review_completion_ratio",
            "block_review_completion_ratio",
            "watch_evidence_quality_score",
            "block_evidence_quality_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "min_domain_sample_count",
            _normalize_positive_integral_decimal(
                "min_domain_sample_count",
                self.min_domain_sample_count,
            ),
        )
        _validate_config(self)
        _require_hard_flags("ResearchTeamPerformanceDigestConfig", self)
        _reject_unsafe_public_payload(
            "ResearchTeamPerformanceDigestConfig",
            _payload_value(asdict(self)),
        )


@dataclass(frozen=True)
class ResearchTeamPerformanceObservation:
    domain: str
    calibration_error_ratio: Decimal
    error_pattern_count: Decimal
    review_completion_ratio: Decimal
    evidence_quality_score: Decimal
    sample_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "domain",
            _require_public_string("domain", self.domain),
        )
        for field_name in (
            "calibration_error_ratio",
            "review_completion_ratio",
            "evidence_quality_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "error_pattern_count",
            _normalize_nonnegative_integral_decimal(
                "error_pattern_count",
                self.error_pattern_count,
            ),
        )
        object.__setattr__(
            self,
            "sample_count",
            _normalize_positive_integral_decimal("sample_count", self.sample_count),
        )
        if self.error_pattern_count > self.sample_count:
            raise ValueError("error_pattern_count must not exceed sample_count")
        _require_hard_flags("ResearchTeamPerformanceObservation", self)
        _reject_unsafe_public_payload(
            "ResearchTeamPerformanceObservation",
            _payload_value(asdict(self)),
        )


@dataclass(frozen=True)
class ResearchTeamPerformanceRow:
    domain: str
    observation_count: Decimal
    sample_count: Decimal
    calibration_error_ratio: Decimal
    error_pattern_count: Decimal
    error_pattern_rate: Decimal
    review_completion_ratio: Decimal
    evidence_quality_score: Decimal
    quality_risk_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "domain",
            _require_public_string("domain", self.domain),
        )
        for field_name in ("observation_count", "sample_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_integral_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        object.__setattr__(
            self,
            "error_pattern_count",
            _normalize_nonnegative_integral_decimal(
                "error_pattern_count",
                self.error_pattern_count,
            ),
        )
        for field_name in (
            "calibration_error_ratio",
            "error_pattern_rate",
            "review_completion_ratio",
            "evidence_quality_score",
            "quality_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_known_strings(
                "reason_codes",
                self.reason_codes,
                ROW_REASON_CODES,
                allow_empty=False,
            ),
        )
        _require_hard_flags("ResearchTeamPerformanceRow", self)
        _reject_unsafe_public_payload(
            "ResearchTeamPerformanceRow",
            _payload_value(asdict(self)),
        )
        _validate_row_consistency(self)


@dataclass(frozen=True)
class ResearchTeamPerformanceDigestReport:
    generated_at: datetime
    config_version: str
    status: str
    domain_count: Decimal
    observation_count: Decimal
    sample_count: Decimal
    pass_domain_count: Decimal
    watch_domain_count: Decimal
    block_domain_count: Decimal
    average_quality_risk_score: Decimal
    rows: tuple[ResearchTeamPerformanceRow, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_public_string("config_version", self.config_version),
        )
        _require_status("status", self.status)
        for field_name in (
            "domain_count",
            "observation_count",
            "sample_count",
            "pass_domain_count",
            "watch_domain_count",
            "block_domain_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_integral_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        object.__setattr__(
            self,
            "average_quality_risk_score",
            _normalize_ratio("average_quality_risk_score", self.average_quality_risk_score),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_known_strings(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODES,
                allow_empty=False,
            ),
        )
        _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
        _require_hard_flags("ResearchTeamPerformanceDigestReport", self)
        _reject_unsafe_public_payload(
            "ResearchTeamPerformanceDigestReport",
            _payload_value(asdict(self)),
        )
        _validate_report_consistency(self)

    @property
    def payload(self) -> dict[str, object]:
        return research_team_performance_digest_payload(self)


def build_research_team_performance_digest(
    observations: Iterable[object],
    *,
    config: ResearchTeamPerformanceDigestConfig,
    generated_at: datetime,
) -> ResearchTeamPerformanceDigestReport:
    if type(config) is not ResearchTeamPerformanceDigestConfig:
        raise ValueError("config must be a ResearchTeamPerformanceDigestConfig")
    _require_hard_flags("ResearchTeamPerformanceDigestConfig", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    items = _normalize_observations(observations)
    rows = tuple(_row_for_domain(domain, grouped, config) for domain, grouped in _domain_groups(items))
    status = _report_status(rows)
    values = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "status": status,
        "domain_count": _count(len(rows)),
        "observation_count": _count(len(items)),
        "sample_count": _sum_rows(rows, "sample_count"),
        "pass_domain_count": _status_count(rows, "pass"),
        "watch_domain_count": _status_count(rows, "watch"),
        "block_domain_count": _status_count(rows, "block"),
        "average_quality_risk_score": _average_risk(rows),
        "rows": rows,
        "reason_codes": _report_reason_codes(rows, status),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values["derived_validation_digest"] = _derived_validation_digest(values)
    return ResearchTeamPerformanceDigestReport(**values)


def research_team_performance_digest_payload(
    report: ResearchTeamPerformanceDigestReport,
) -> dict[str, object]:
    if type(report) is not ResearchTeamPerformanceDigestReport:
        raise ValueError("report must be a ResearchTeamPerformanceDigestReport")
    _require_hard_flags("ResearchTeamPerformanceDigestReport", report)
    payload = _payload_value(report)
    _reject_unsafe_public_payload("ResearchTeamPerformanceDigestReport.payload", payload)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    return payload


def _domain_groups(
    observations: tuple[ResearchTeamPerformanceObservation, ...],
) -> tuple[tuple[str, tuple[ResearchTeamPerformanceObservation, ...]], ...]:
    grouped: dict[str, list[ResearchTeamPerformanceObservation]] = {}
    for item in observations:
        grouped.setdefault(item.domain, []).append(item)
    return tuple((domain, tuple(grouped[domain])) for domain in sorted(grouped))


def _row_for_domain(
    domain: str,
    observations: tuple[ResearchTeamPerformanceObservation, ...],
    config: ResearchTeamPerformanceDigestConfig,
) -> ResearchTeamPerformanceRow:
    sample_count = sum((item.sample_count for item in observations), Decimal("0"))
    error_pattern_count = sum(
        (item.error_pattern_count for item in observations),
        Decimal("0"),
    )
    calibration_error_ratio = _weighted_average(
        tuple((item.calibration_error_ratio, item.sample_count) for item in observations),
    )
    review_completion_ratio = _weighted_average(
        tuple((item.review_completion_ratio, item.sample_count) for item in observations),
    )
    evidence_quality_score = _weighted_average(
        tuple((item.evidence_quality_score, item.sample_count) for item in observations),
    )
    error_pattern_rate = _ratio(error_pattern_count, sample_count)
    risk_score = _quality_risk_score(
        calibration_error_ratio=calibration_error_ratio,
        error_pattern_rate=error_pattern_rate,
        review_completion_ratio=review_completion_ratio,
        evidence_quality_score=evidence_quality_score,
        config=config,
    )
    status = _row_status(
        calibration_error_ratio=calibration_error_ratio,
        error_pattern_rate=error_pattern_rate,
        review_completion_ratio=review_completion_ratio,
        evidence_quality_score=evidence_quality_score,
        sample_count=sample_count,
        quality_risk_score=risk_score,
        config=config,
    )
    return ResearchTeamPerformanceRow(
        domain=domain,
        observation_count=_count(len(observations)),
        sample_count=sample_count.quantize(COUNT_QUANT),
        calibration_error_ratio=calibration_error_ratio,
        error_pattern_count=error_pattern_count.quantize(COUNT_QUANT),
        error_pattern_rate=error_pattern_rate,
        review_completion_ratio=review_completion_ratio,
        evidence_quality_score=evidence_quality_score,
        quality_risk_score=risk_score,
        status=status,
        reason_codes=_row_reason_codes(
            calibration_error_ratio=calibration_error_ratio,
            error_pattern_rate=error_pattern_rate,
            review_completion_ratio=review_completion_ratio,
            evidence_quality_score=evidence_quality_score,
            sample_count=sample_count,
            config=config,
        ),
    )


def _quality_risk_score(
    *,
    calibration_error_ratio: Decimal,
    error_pattern_rate: Decimal,
    review_completion_ratio: Decimal,
    evidence_quality_score: Decimal,
    config: ResearchTeamPerformanceDigestConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(
            calibration_error_ratio * config.calibration_error_weight
            + error_pattern_rate * config.error_pattern_weight
            + (ONE - review_completion_ratio) * config.review_gap_weight
            + (ONE - evidence_quality_score) * config.evidence_gap_weight,
        )


def _row_status(
    *,
    calibration_error_ratio: Decimal,
    error_pattern_rate: Decimal,
    review_completion_ratio: Decimal,
    evidence_quality_score: Decimal,
    sample_count: Decimal,
    quality_risk_score: Decimal,
    config: ResearchTeamPerformanceDigestConfig,
) -> str:
    if (
        sample_count < config.min_domain_sample_count
        or calibration_error_ratio >= config.block_calibration_error_ratio
        or error_pattern_rate >= config.block_error_pattern_rate
        or review_completion_ratio < config.block_review_completion_ratio
        or evidence_quality_score < config.block_evidence_quality_score
        or quality_risk_score > config.watch_risk_ceiling
    ):
        return "block"
    if (
        calibration_error_ratio >= config.watch_calibration_error_ratio
        or error_pattern_rate >= config.watch_error_pattern_rate
        or review_completion_ratio < config.watch_review_completion_ratio
        or evidence_quality_score < config.watch_evidence_quality_score
        or quality_risk_score > config.pass_risk_ceiling
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    calibration_error_ratio: Decimal,
    error_pattern_rate: Decimal,
    review_completion_ratio: Decimal,
    evidence_quality_score: Decimal,
    sample_count: Decimal,
    config: ResearchTeamPerformanceDigestConfig,
) -> tuple[str, ...]:
    return (
        _upper_bad_reason(
            calibration_error_ratio,
            watch=config.watch_calibration_error_ratio,
            block=config.block_calibration_error_ratio,
            pass_reason="calibration_stable",
            watch_reason="calibration_watch",
            block_reason="calibration_block",
        ),
        _upper_bad_reason(
            error_pattern_rate,
            watch=config.watch_error_pattern_rate,
            block=config.block_error_pattern_rate,
            pass_reason="error_patterns_stable",
            watch_reason="error_patterns_watch",
            block_reason="error_patterns_block",
        ),
        _lower_bad_reason(
            review_completion_ratio,
            watch=config.watch_review_completion_ratio,
            block=config.block_review_completion_ratio,
            pass_reason="review_completion_sufficient",
            watch_reason="review_completion_watch",
            block_reason="review_completion_block",
        ),
        _lower_bad_reason(
            evidence_quality_score,
            watch=config.watch_evidence_quality_score,
            block=config.block_evidence_quality_score,
            pass_reason="evidence_quality_sufficient",
            watch_reason="evidence_quality_watch",
            block_reason="evidence_quality_block",
        ),
        (
            "sample_size_sufficient"
            if sample_count >= config.min_domain_sample_count
            else "sample_size_insufficient"
        ),
    )


def _upper_bad_reason(
    value: Decimal,
    *,
    watch: Decimal,
    block: Decimal,
    pass_reason: str,
    watch_reason: str,
    block_reason: str,
) -> str:
    if value >= block:
        return block_reason
    if value >= watch:
        return watch_reason
    return pass_reason


def _lower_bad_reason(
    value: Decimal,
    *,
    watch: Decimal,
    block: Decimal,
    pass_reason: str,
    watch_reason: str,
    block_reason: str,
) -> str:
    if value < block:
        return block_reason
    if value < watch:
        return watch_reason
    return pass_reason


def _report_status(rows: tuple[ResearchTeamPerformanceRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchTeamPerformanceRow, ...],
    status: str,
) -> tuple[str, ...]:
    if not rows:
        return ("research_team_performance_empty",)
    return (f"research_team_performance_{status}",)


def _normalize_observations(
    observations: Iterable[object],
) -> tuple[ResearchTeamPerformanceObservation, ...]:
    if isinstance(observations, (str, bytes)):
        raise ValueError("observations must be an iterable")
    try:
        items = tuple(observations)
    except TypeError as exc:
        raise ValueError("observations must be an iterable") from exc
    for item in items:
        if type(item) is not ResearchTeamPerformanceObservation:
            raise ValueError(
                "observations must contain ResearchTeamPerformanceObservation values",
            )
        _require_hard_flags("ResearchTeamPerformanceObservation", item)
    return items


def _normalize_rows(value: object) -> tuple[ResearchTeamPerformanceRow, ...]:
    if type(value) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in value:
        if type(row) is not ResearchTeamPerformanceRow:
            raise ValueError("rows must contain ResearchTeamPerformanceRow values")
        _require_hard_flags("ResearchTeamPerformanceRow", row)
    expected = tuple(sorted(value, key=lambda row: row.domain))
    if value != expected:
        raise ValueError("rows must be sorted by domain")
    return value


def _normalize_known_strings(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not allow_empty and not value:
        raise ValueError(f"{field_name} must be a non-empty tuple")
    normalized = tuple(_require_public_string(field_name, item) for item in value)
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} must not contain duplicates")
    if any(item not in allowed for item in normalized):
        raise ValueError(f"{field_name} must contain known values")
    return normalized


def _validate_config(config: ResearchTeamPerformanceDigestConfig) -> None:
    with localcontext(DECIMAL_CONTEXT):
        total_weight = (
            config.calibration_error_weight
            + config.error_pattern_weight
            + config.review_gap_weight
            + config.evidence_gap_weight
        ).quantize(SCORE_QUANT)
    if total_weight != ONE:
        raise ValueError("performance digest weights must sum to 1.000000")
    if config.pass_risk_ceiling > config.watch_risk_ceiling:
        raise ValueError("pass_risk_ceiling must not exceed watch_risk_ceiling")
    if config.watch_calibration_error_ratio > config.block_calibration_error_ratio:
        raise ValueError("watch_calibration_error_ratio must not exceed block threshold")
    if config.watch_error_pattern_rate > config.block_error_pattern_rate:
        raise ValueError("watch_error_pattern_rate must not exceed block threshold")
    if config.watch_review_completion_ratio < config.block_review_completion_ratio:
        raise ValueError("watch_review_completion_ratio must be at least block threshold")
    if config.watch_evidence_quality_score < config.block_evidence_quality_score:
        raise ValueError("watch_evidence_quality_score must be at least block threshold")


def _validate_row_consistency(row: ResearchTeamPerformanceRow) -> None:
    if row.error_pattern_count > row.sample_count:
        raise ValueError("error_pattern_count must not exceed sample_count")
    if row.error_pattern_rate != _ratio(row.error_pattern_count, row.sample_count):
        raise ValueError("error_pattern_rate must match error_pattern_count and sample_count")


def _validate_report_consistency(report: ResearchTeamPerformanceDigestReport) -> None:
    rows = report.rows
    if report.domain_count != _count(len(rows)):
        raise ValueError("domain_count must match rows")
    if report.sample_count != _sum_rows(rows, "sample_count"):
        raise ValueError("sample_count must match rows")
    if report.pass_domain_count != _status_count(rows, "pass"):
        raise ValueError("pass_domain_count must match rows")
    if report.watch_domain_count != _status_count(rows, "watch"):
        raise ValueError("watch_domain_count must match rows")
    if report.block_domain_count != _status_count(rows, "block"):
        raise ValueError("block_domain_count must match rows")
    if report.average_quality_risk_score != _average_risk(rows):
        raise ValueError("average_quality_risk_score must match rows")
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(rows, report.status):
        raise ValueError("reason_codes must match status")
    if report.derived_validation_digest != _derived_validation_digest(asdict(report)):
        raise ValueError("derived_validation_digest must match report fields")


def _status_count(rows: tuple[ResearchTeamPerformanceRow, ...], status: str) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _sum_rows(rows: tuple[ResearchTeamPerformanceRow, ...], field_name: str) -> Decimal:
    return sum((getattr(row, field_name) for row in rows), Decimal("0")).quantize(
        COUNT_QUANT,
    )


def _average_risk(rows: tuple[ResearchTeamPerformanceRow, ...]) -> Decimal:
    if not rows:
        return ZERO
    return _weighted_average(tuple((row.quality_risk_score, row.sample_count) for row in rows))


def _weighted_average(values: tuple[tuple[Decimal, Decimal], ...]) -> Decimal:
    total_weight = sum((weight for _, weight in values), Decimal("0"))
    if total_weight <= Decimal("0"):
        raise ValueError("weighted average requires positive total weight")
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(sum((value * weight for value, weight in values), Decimal("0")) / total_weight)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= Decimal("0"):
        raise ValueError("ratio denominator must be positive")
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(numerator / denominator)


def _count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count source must be an int")
    if value < 0:
        raise ValueError("count source must be nonnegative")
    return Decimal(value).quantize(COUNT_QUANT)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_public_string(field_name: str, value: object) -> str:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a non-empty canonical string")
    _reject_unsafe_public_text(field_name, value)
    return value


def _require_status(field_name: str, value: object) -> None:
    _require_public_string(field_name, value)
    if value not in STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    value = _require_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be >= 0.000000")
    if value > ONE:
        raise ValueError(f"{field_name} must be <= 1.000000")
    with localcontext(DECIMAL_CONTEXT):
        quantized = value.quantize(SCORE_QUANT)
    if quantized != value:
        raise ValueError(f"{field_name} must use six decimal places or fewer")
    return quantized


def _normalize_nonnegative_integral_decimal(field_name: str, value: object) -> Decimal:
    value = _require_decimal(field_name, value)
    if value < Decimal("0"):
        raise ValueError(f"{field_name} must be >= 0")
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be an integral Decimal")
    return value.quantize(COUNT_QUANT)


def _normalize_positive_integral_decimal(field_name: str, value: object) -> Decimal:
    value = _normalize_nonnegative_integral_decimal(field_name, value)
    if value <= Decimal("0"):
        raise ValueError(f"{field_name} must be positive")
    return value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _clamp_ratio(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return min(ONE, max(ZERO, value)).quantize(SCORE_QUANT)


def _require_sha256_digest(field_name: str, value: object) -> None:
    _require_public_string(field_name, value)
    if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
        raise ValueError(f"{field_name} must be a sha256 digest")


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"paper_only must be True for {field_name}")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"report_only must be True for {field_name}")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"readonly must be True for {field_name}")


def _payload_value(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _payload_value(getattr(value, field.name)) for field in fields(value)}
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("payload Decimal must be finite")
        return str(value)
    if type(value) is datetime:
        return _as_utc("payload datetime", value).isoformat()
    if type(value) is dict:
        return {str(key): _payload_value(item) for key, item in value.items()}
    if type(value) is tuple:
        return [_payload_value(item) for item in value]
    if type(value) is list:
        return [_payload_value(item) for item in value]
    if value is None or type(value) in (str, int, bool):
        return value
    raise ValueError("payload contains unsupported value")


def _derived_validation_digest(values: dict[str, object]) -> str:
    digest_payload = {
        key: _payload_value(item)
        for key, item in values.items()
        if key != "derived_validation_digest"
    }
    _reject_unsafe_public_payload("derived validation digest payload", digest_payload)
    encoded = json.dumps(
        digest_payload,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"unsafe public payload in {label}")
            _reject_unsafe_public_text(label, key)
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) in (list, tuple):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) is float:
        raise ValueError(f"unsafe public payload in {label}")
    if type(value) is str:
        _reject_unsafe_public_text(label, value)


def _reject_unsafe_public_text(label: str, value: str) -> None:
    normalized = value.lower()
    if any(fragment in normalized for fragment in UNSAFE_PUBLIC_TEXT_FRAGMENTS):
        raise ValueError(f"unsafe public payload in {label}")
