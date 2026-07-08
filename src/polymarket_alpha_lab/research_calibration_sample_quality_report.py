"""Read-only probability calibration sample quality summaries."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, localcontext
from typing import Any

from polymarket_alpha_lab.team_paper_guard import require_paper_only_flags


DEFAULT_RESEARCH_CALIBRATION_SAMPLE_QUALITY_CONFIG_VERSION = (
    "research-calibration-sample-quality-v0"
)

RATIO_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
NEGATIVE_ONE = Decimal("-1.000000")
DECIMAL_CONTEXT = Context(prec=64)
REPORT_STATUSES = frozenset(("pass", "watch", "block"))
UNSAFE_PUBLIC_FRAGMENTS = frozenset(
    (
        "candidate",
        "market",
        "source",
        "url",
        "text",
        "dsn",
        "table",
        "token",
    ),
)
PUBLIC_REASON_PREFIX = "input_"

__all__ = (
    "DEFAULT_RESEARCH_CALIBRATION_SAMPLE_QUALITY_CONFIG_VERSION",
    "ResearchCalibrationSampleQualityConfig",
    "ResearchCalibrationSampleQualityDomainInput",
    "ResearchCalibrationSampleQualityReasonCodeCount",
    "ResearchCalibrationSampleQualityReport",
    "ResearchCalibrationSampleQualityRow",
    "build_research_calibration_sample_quality_report",
    "research_calibration_sample_quality_report_payload",
)


@dataclass(frozen=True)
class ResearchCalibrationSampleQualityConfig:
    config_version: str = DEFAULT_RESEARCH_CALIBRATION_SAMPLE_QUALITY_CONFIG_VERSION
    min_pass_sample_count: Decimal = Decimal("100")
    min_watch_sample_count: Decimal = Decimal("50")
    min_pass_domain_count: Decimal = Decimal("3")
    min_watch_domain_count: Decimal = Decimal("2")
    min_pass_settlement_label_completeness: Decimal = Decimal("0.950000")
    min_watch_settlement_label_completeness: Decimal = Decimal("0.800000")
    max_pass_bias_delta: Decimal = Decimal("0.050000")
    max_watch_bias_delta: Decimal = Decimal("0.100000")
    min_pass_review_quality_score: Decimal = Decimal("0.900000")
    min_watch_review_quality_score: Decimal = Decimal("0.700000")
    pass_quality_score: Decimal = Decimal("0.800000")
    watch_quality_score: Decimal = Decimal("0.600000")
    sample_size_weight: Decimal = Decimal("0.200000")
    domain_coverage_weight: Decimal = Decimal("0.200000")
    settlement_label_weight: Decimal = Decimal("0.200000")
    bias_stability_weight: Decimal = Decimal("0.200000")
    review_quality_weight: Decimal = Decimal("0.200000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchCalibrationSampleQualityConfig:
            raise ValueError("config must be exactly ResearchCalibrationSampleQualityConfig")
        _require_public_slug("config_version", self.config_version)
        for field_name in (
            "min_pass_sample_count",
            "min_watch_sample_count",
            "min_pass_domain_count",
            "min_watch_domain_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_whole_decimal(field_name, getattr(self, field_name)),
            )
        if self.min_pass_sample_count <= self.min_watch_sample_count:
            raise ValueError("min_pass_sample_count must be greater than min_watch_sample_count")
        if self.min_pass_domain_count <= self.min_watch_domain_count:
            raise ValueError("min_pass_domain_count must be greater than min_watch_domain_count")
        for field_name in (
            "min_pass_settlement_label_completeness",
            "min_watch_settlement_label_completeness",
            "max_pass_bias_delta",
            "max_watch_bias_delta",
            "min_pass_review_quality_score",
            "min_watch_review_quality_score",
            "pass_quality_score",
            "watch_quality_score",
            "sample_size_weight",
            "domain_coverage_weight",
            "settlement_label_weight",
            "bias_stability_weight",
            "review_quality_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        if (
            self.min_pass_settlement_label_completeness
            <= self.min_watch_settlement_label_completeness
        ):
            raise ValueError(
                "min_pass_settlement_label_completeness must be greater than "
                "min_watch_settlement_label_completeness",
            )
        if self.max_pass_bias_delta >= self.max_watch_bias_delta:
            raise ValueError("max_pass_bias_delta must be less than max_watch_bias_delta")
        if self.min_pass_review_quality_score <= self.min_watch_review_quality_score:
            raise ValueError(
                "min_pass_review_quality_score must be greater than "
                "min_watch_review_quality_score",
            )
        if self.pass_quality_score <= self.watch_quality_score:
            raise ValueError("pass_quality_score must be greater than watch_quality_score")
        weight_sum = _quantize_probability(
            "weight_sum",
            self.sample_size_weight
            + self.domain_coverage_weight
            + self.settlement_label_weight
            + self.bias_stability_weight
            + self.review_quality_weight,
        )
        if weight_sum != ONE:
            raise ValueError("quality weights must sum to 1")
        require_paper_only_flags("calibration sample quality config", self)


@dataclass(frozen=True)
class ResearchCalibrationSampleQualityDomainInput:
    domain: str
    sample_count: Decimal
    settled_label_count: Decimal
    positive_label_count: Decimal
    current_bias: Decimal
    previous_bias: Decimal | None
    reviewed_count: Decimal
    high_quality_review_count: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchCalibrationSampleQualityDomainInput:
            raise ValueError("domain input must be exactly ResearchCalibrationSampleQualityDomainInput")
        _require_public_slug("domain", self.domain)
        for field_name in (
            "sample_count",
            "settled_label_count",
            "positive_label_count",
            "reviewed_count",
            "high_quality_review_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        if self.settled_label_count > self.sample_count:
            raise ValueError("settled_label_count must not exceed sample_count")
        if self.positive_label_count > self.settled_label_count:
            raise ValueError("positive_label_count must not exceed settled_label_count")
        if self.reviewed_count > self.sample_count:
            raise ValueError("reviewed_count must not exceed sample_count")
        if self.high_quality_review_count > self.reviewed_count:
            raise ValueError("high_quality_review_count must not exceed reviewed_count")
        object.__setattr__(
            self,
            "current_bias",
            _require_bias_decimal("current_bias", self.current_bias),
        )
        object.__setattr__(
            self,
            "previous_bias",
            _require_optional_bias_decimal("previous_bias", self.previous_bias),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=True),
        )
        require_paper_only_flags("calibration sample quality input", self)


@dataclass(frozen=True)
class ResearchCalibrationSampleQualityRow:
    domain: str
    sample_count: Decimal
    settled_label_count: Decimal
    missing_label_count: Decimal
    positive_label_count: Decimal
    reviewed_count: Decimal
    high_quality_review_count: Decimal
    current_bias: Decimal
    previous_bias: Decimal | None
    settlement_label_completeness_score: Decimal
    bias_stability_delta: Decimal | None
    bias_stability_score: Decimal
    review_quality_score: Decimal
    quality_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchCalibrationSampleQualityRow:
            raise ValueError("row must be exactly ResearchCalibrationSampleQualityRow")
        _require_public_slug("domain", self.domain)
        for field_name in (
            "sample_count",
            "settled_label_count",
            "missing_label_count",
            "positive_label_count",
            "reviewed_count",
            "high_quality_review_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "current_bias",
            _require_bias_decimal("current_bias", self.current_bias),
        )
        object.__setattr__(
            self,
            "previous_bias",
            _require_optional_bias_decimal("previous_bias", self.previous_bias),
        )
        for field_name in (
            "settlement_label_completeness_score",
            "bias_stability_score",
            "review_quality_score",
            "quality_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "bias_stability_delta",
            _require_optional_probability_decimal(
                "bias_stability_delta",
                self.bias_stability_delta,
            ),
        )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        require_paper_only_flags("calibration sample quality row", self)
        _validate_row_consistency(self)


@dataclass(frozen=True)
class ResearchCalibrationSampleQualityReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchCalibrationSampleQualityReasonCodeCount:
            raise ValueError(
                "reason code count must be exactly ResearchCalibrationSampleQualityReasonCodeCount",
            )
        _require_public_slug("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_positive_whole_decimal("count", self.count),
        )
        require_paper_only_flags("calibration sample quality reason count", self)


@dataclass(frozen=True)
class ResearchCalibrationSampleQualityReport:
    generated_at: datetime
    config_version: str
    sample_count: Decimal
    domain_count: Decimal
    settled_label_count: Decimal
    missing_label_count: Decimal
    positive_label_count: Decimal
    reviewed_count: Decimal
    high_quality_review_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    sample_size_score: Decimal
    domain_coverage_score: Decimal
    settlement_label_completeness_score: Decimal
    bias_stability_score: Decimal
    review_quality_score: Decimal
    quality_score: Decimal
    status: str
    rows: tuple[ResearchCalibrationSampleQualityRow, ...]
    reason_code_counts: tuple[ResearchCalibrationSampleQualityReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchCalibrationSampleQualityReport:
            raise ValueError("report must be exactly ResearchCalibrationSampleQualityReport")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_slug("config_version", self.config_version)
        for field_name in (
            "sample_count",
            "domain_count",
            "settled_label_count",
            "missing_label_count",
            "positive_label_count",
            "reviewed_count",
            "high_quality_review_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "sample_size_score",
            "domain_coverage_score",
            "settlement_label_completeness_score",
            "bias_stability_score",
            "review_quality_score",
            "quality_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
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
        require_paper_only_flags("calibration sample quality report", self)
        _validate_report_consistency(self)


def build_research_calibration_sample_quality_report(
    domain_rows: object,
    *,
    config: ResearchCalibrationSampleQualityConfig,
    generated_at: datetime,
) -> ResearchCalibrationSampleQualityReport:
    if type(config) is not ResearchCalibrationSampleQualityConfig:
        raise ValueError("config must be a ResearchCalibrationSampleQualityConfig")
    require_paper_only_flags("calibration sample quality config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    inputs = _normalize_domain_inputs(domain_rows)
    rows = tuple(sorted((_build_row(row, config) for row in inputs), key=lambda row: row.domain))

    sample_count = sum((row.sample_count for row in rows), Decimal("0"))
    domain_count = Decimal(len(rows))
    settled_label_count = sum((row.settled_label_count for row in rows), Decimal("0"))
    missing_label_count = sum((row.missing_label_count for row in rows), Decimal("0"))
    positive_label_count = sum((row.positive_label_count for row in rows), Decimal("0"))
    reviewed_count = sum((row.reviewed_count for row in rows), Decimal("0"))
    high_quality_review_count = sum(
        (row.high_quality_review_count for row in rows),
        Decimal("0"),
    )
    sample_size_score = _capped_ratio(sample_count, config.min_pass_sample_count)
    domain_coverage_score = _capped_ratio(domain_count, config.min_pass_domain_count)
    settlement_label_score = _safe_ratio(settled_label_count, sample_count)
    bias_stability_score = _average_probability(
        tuple(row.bias_stability_score for row in rows),
    )
    average_bias_stability_delta = _average_optional_probability(
        tuple(row.bias_stability_delta for row in rows),
    )
    review_quality_score = _safe_ratio(high_quality_review_count, reviewed_count)
    quality_score = _weighted_quality_score(
        config=config,
        sample_size_score=sample_size_score,
        domain_coverage_score=domain_coverage_score,
        settlement_label_completeness_score=settlement_label_score,
        bias_stability_score=bias_stability_score,
        review_quality_score=review_quality_score,
    )
    status = _report_status(
        sample_count=sample_count,
        domain_count=domain_count,
        settlement_label_completeness_score=settlement_label_score,
        average_bias_stability_delta=average_bias_stability_delta,
        bias_stability_score=bias_stability_score,
        review_quality_score=review_quality_score,
        quality_score=quality_score,
        config=config,
    )
    reason_codes = _report_reason_codes(
        status=status,
        sample_count=sample_count,
        domain_count=domain_count,
        settlement_label_completeness_score=settlement_label_score,
        average_bias_stability_delta=average_bias_stability_delta,
        bias_stability_score=bias_stability_score,
        review_quality_score=review_quality_score,
        quality_score=quality_score,
        config=config,
    )
    return ResearchCalibrationSampleQualityReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        sample_count=sample_count,
        domain_count=domain_count,
        settled_label_count=settled_label_count,
        missing_label_count=missing_label_count,
        positive_label_count=positive_label_count,
        reviewed_count=reviewed_count,
        high_quality_review_count=high_quality_review_count,
        pass_count=_decimal_status_count(rows, "pass"),
        watch_count=_decimal_status_count(rows, "watch"),
        block_count=_decimal_status_count(rows, "block"),
        sample_size_score=sample_size_score,
        domain_coverage_score=domain_coverage_score,
        settlement_label_completeness_score=settlement_label_score,
        bias_stability_score=bias_stability_score,
        review_quality_score=review_quality_score,
        quality_score=quality_score,
        status=status,
        rows=rows,
        reason_code_counts=_reason_code_counts(reason_codes),
        reason_codes=reason_codes,
    )


def research_calibration_sample_quality_report_payload(
    report: ResearchCalibrationSampleQualityReport,
) -> dict[str, Any]:
    if type(report) is not ResearchCalibrationSampleQualityReport:
        raise ValueError("report must be a ResearchCalibrationSampleQualityReport")
    require_paper_only_flags("calibration sample quality report", report)
    payload = _payload_value(report)
    _reject_unsafe_public_payload("calibration sample quality report payload", payload)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    return payload


def _build_row(
    row: ResearchCalibrationSampleQualityDomainInput,
    config: ResearchCalibrationSampleQualityConfig,
) -> ResearchCalibrationSampleQualityRow:
    settlement_score = _safe_ratio(row.settled_label_count, row.sample_count)
    bias_delta = (
        None
        if row.previous_bias is None
        else _absolute_probability(row.current_bias - row.previous_bias)
    )
    bias_score = ZERO if bias_delta is None else _clamped_one_minus_ratio(
        bias_delta,
        config.max_watch_bias_delta,
    )
    review_score = _safe_ratio(row.high_quality_review_count, row.reviewed_count)
    quality_score = _average_probability((settlement_score, bias_score, review_score))
    status = _row_status(
        settlement_label_completeness_score=settlement_score,
        bias_stability_delta=bias_delta,
        review_quality_score=review_score,
        config=config,
    )
    reason_codes = _row_reason_codes(
        input_reason_codes=row.reason_codes,
        status=status,
        settlement_label_completeness_score=settlement_score,
        bias_stability_delta=bias_delta,
        review_quality_score=review_score,
        config=config,
    )
    return ResearchCalibrationSampleQualityRow(
        domain=row.domain,
        sample_count=row.sample_count,
        settled_label_count=row.settled_label_count,
        missing_label_count=row.sample_count - row.settled_label_count,
        positive_label_count=row.positive_label_count,
        reviewed_count=row.reviewed_count,
        high_quality_review_count=row.high_quality_review_count,
        current_bias=row.current_bias,
        previous_bias=row.previous_bias,
        settlement_label_completeness_score=settlement_score,
        bias_stability_delta=bias_delta,
        bias_stability_score=bias_score,
        review_quality_score=review_score,
        quality_score=quality_score,
        status=status,
        reason_codes=reason_codes,
    )


def _row_status(
    *,
    settlement_label_completeness_score: Decimal,
    bias_stability_delta: Decimal | None,
    review_quality_score: Decimal,
    config: ResearchCalibrationSampleQualityConfig,
) -> str:
    if (
        settlement_label_completeness_score
        < config.min_watch_settlement_label_completeness
    ):
        return "block"
    if bias_stability_delta is None or bias_stability_delta > config.max_watch_bias_delta:
        return "block"
    if review_quality_score < config.min_watch_review_quality_score:
        return "block"
    if (
        settlement_label_completeness_score < config.min_pass_settlement_label_completeness
        or bias_stability_delta > config.max_pass_bias_delta
        or review_quality_score < config.min_pass_review_quality_score
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    input_reason_codes: tuple[str, ...],
    status: str,
    settlement_label_completeness_score: Decimal,
    bias_stability_delta: Decimal | None,
    review_quality_score: Decimal,
    config: ResearchCalibrationSampleQualityConfig,
) -> tuple[str, ...]:
    reasons = [f"{PUBLIC_REASON_PREFIX}{reason_code}" for reason_code in input_reason_codes]
    if status == "pass":
        reasons.append("sample_quality_pass")
        return tuple(sorted(dict.fromkeys(reasons)))
    if (
        settlement_label_completeness_score
        < (
            config.min_watch_settlement_label_completeness
            if status == "block"
            else config.min_pass_settlement_label_completeness
        )
    ):
        reasons.append(f"settlement_label_completeness_{status}")
    if bias_stability_delta is None:
        reasons.append("bias_stability_block")
    elif bias_stability_delta > (
        config.max_watch_bias_delta if status == "block" else config.max_pass_bias_delta
    ):
        reasons.append(f"bias_stability_{status}")
    if review_quality_score < (
        config.min_watch_review_quality_score
        if status == "block"
        else config.min_pass_review_quality_score
    ):
        reasons.append(f"review_quality_{status}")
    reasons.append(f"sample_quality_{status}")
    return tuple(sorted(dict.fromkeys(reasons)))


def _report_status(
    *,
    sample_count: Decimal,
    domain_count: Decimal,
    settlement_label_completeness_score: Decimal,
    average_bias_stability_delta: Decimal | None,
    bias_stability_score: Decimal,
    review_quality_score: Decimal,
    quality_score: Decimal,
    config: ResearchCalibrationSampleQualityConfig,
) -> str:
    if (
        sample_count < config.min_watch_sample_count
        or domain_count < config.min_watch_domain_count
        or settlement_label_completeness_score
        < config.min_watch_settlement_label_completeness
        or average_bias_stability_delta is None
        or average_bias_stability_delta > config.max_watch_bias_delta
        or review_quality_score < config.min_watch_review_quality_score
        or quality_score < config.watch_quality_score
    ):
        return "block"
    if (
        sample_count < config.min_pass_sample_count
        or domain_count < config.min_pass_domain_count
        or settlement_label_completeness_score
        < config.min_pass_settlement_label_completeness
        or average_bias_stability_delta > config.max_pass_bias_delta
        or review_quality_score < config.min_pass_review_quality_score
        or quality_score < config.pass_quality_score
    ):
        return "watch"
    return "pass"


def _report_reason_codes(
    *,
    status: str,
    sample_count: Decimal,
    domain_count: Decimal,
    settlement_label_completeness_score: Decimal,
    average_bias_stability_delta: Decimal | None,
    bias_stability_score: Decimal,
    review_quality_score: Decimal,
    quality_score: Decimal,
    config: ResearchCalibrationSampleQualityConfig,
) -> tuple[str, ...]:
    if status == "pass":
        return ("calibration_sample_quality_pass",)
    sample_threshold = (
        config.min_watch_sample_count if status == "block" else config.min_pass_sample_count
    )
    domain_threshold = (
        config.min_watch_domain_count if status == "block" else config.min_pass_domain_count
    )
    label_threshold = (
        config.min_watch_settlement_label_completeness
        if status == "block"
        else config.min_pass_settlement_label_completeness
    )
    bias_delta_threshold = (
        config.max_watch_bias_delta if status == "block" else config.max_pass_bias_delta
    )
    review_threshold = (
        config.min_watch_review_quality_score
        if status == "block"
        else config.min_pass_review_quality_score
    )
    reason_codes: list[str] = []
    if sample_count < sample_threshold:
        reason_codes.append(f"sample_size_{status}")
    if domain_count < domain_threshold:
        reason_codes.append(f"domain_coverage_{status}")
    if settlement_label_completeness_score < label_threshold:
        reason_codes.append(f"settlement_label_completeness_{status}")
    if average_bias_stability_delta is None or average_bias_stability_delta > bias_delta_threshold:
        reason_codes.append(f"bias_stability_{status}")
    if review_quality_score < review_threshold:
        reason_codes.append(f"review_quality_{status}")
    reason_codes.append(f"calibration_sample_quality_{status}")
    return tuple(sorted(dict.fromkeys(reason_codes)))


def _bias_score_threshold(max_delta: Decimal) -> Decimal:
    return _clamped_one_minus_ratio(max_delta, Decimal("1.000000"))


def _weighted_quality_score(
    *,
    config: ResearchCalibrationSampleQualityConfig,
    sample_size_score: Decimal,
    domain_coverage_score: Decimal,
    settlement_label_completeness_score: Decimal,
    bias_stability_score: Decimal,
    review_quality_score: Decimal,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_probability(
            "quality_score",
            (sample_size_score * config.sample_size_weight)
            + (domain_coverage_score * config.domain_coverage_weight)
            + (settlement_label_completeness_score * config.settlement_label_weight)
            + (bias_stability_score * config.bias_stability_weight)
            + (review_quality_score * config.review_quality_weight),
        )


def _reason_code_counts(
    reason_codes: tuple[str, ...],
) -> tuple[ResearchCalibrationSampleQualityReasonCodeCount, ...]:
    return tuple(
        ResearchCalibrationSampleQualityReasonCodeCount(
            reason_code=reason_code,
            count=Decimal("1"),
        )
        for reason_code in reason_codes
    )


def _validate_row_consistency(row: ResearchCalibrationSampleQualityRow) -> None:
    if row.settled_label_count > row.sample_count:
        raise ValueError("settled_label_count must not exceed sample_count")
    if row.positive_label_count > row.settled_label_count:
        raise ValueError("positive_label_count must not exceed settled_label_count")
    if row.reviewed_count > row.sample_count:
        raise ValueError("reviewed_count must not exceed sample_count")
    if row.high_quality_review_count > row.reviewed_count:
        raise ValueError("high_quality_review_count must not exceed reviewed_count")
    if row.missing_label_count != row.sample_count - row.settled_label_count:
        raise ValueError("missing_label_count must match sample_count less settled labels")
    if row.settlement_label_completeness_score != _safe_ratio(
        row.settled_label_count,
        row.sample_count,
    ):
        raise ValueError("settlement_label_completeness_score must match counts")
    expected_delta = (
        None
        if row.previous_bias is None
        else _absolute_probability(row.current_bias - row.previous_bias)
    )
    if row.bias_stability_delta != expected_delta:
        raise ValueError("bias_stability_delta must match bias values")
    if row.bias_stability_score != (
        ZERO
        if expected_delta is None
        else _clamped_one_minus_ratio(expected_delta, Decimal("0.100000"))
    ):
        raise ValueError("bias_stability_score must match bias delta")
    if row.review_quality_score != _safe_ratio(
        row.high_quality_review_count,
        row.reviewed_count,
    ):
        raise ValueError("review_quality_score must match review counts")
    if row.quality_score != _average_probability(
        (
            row.settlement_label_completeness_score,
            row.bias_stability_score,
            row.review_quality_score,
        ),
    ):
        raise ValueError("quality_score must match component scores")
    if f"sample_quality_{row.status}" not in row.reason_codes:
        raise ValueError("reason_codes must include sample quality status")


def _validate_report_consistency(report: ResearchCalibrationSampleQualityReport) -> None:
    if report.rows != tuple(sorted(report.rows, key=lambda row: row.domain)):
        raise ValueError("rows must be sorted")
    if report.sample_count != sum((row.sample_count for row in report.rows), Decimal("0")):
        raise ValueError("sample_count must match rows")
    if report.domain_count != Decimal(len(report.rows)):
        raise ValueError("domain_count must match rows")
    if report.settled_label_count != sum(
        (row.settled_label_count for row in report.rows),
        Decimal("0"),
    ):
        raise ValueError("settled_label_count must match rows")
    if report.missing_label_count != sum(
        (row.missing_label_count for row in report.rows),
        Decimal("0"),
    ):
        raise ValueError("missing_label_count must match rows")
    if report.positive_label_count != sum(
        (row.positive_label_count for row in report.rows),
        Decimal("0"),
    ):
        raise ValueError("positive_label_count must match rows")
    if report.reviewed_count != sum((row.reviewed_count for row in report.rows), Decimal("0")):
        raise ValueError("reviewed_count must match rows")
    if report.high_quality_review_count != sum(
        (row.high_quality_review_count for row in report.rows),
        Decimal("0"),
    ):
        raise ValueError("high_quality_review_count must match rows")
    if report.pass_count != _decimal_status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_status_count(report.rows, "block"):
        raise ValueError("block_count must match rows")
    expected_prefix = f"calibration_sample_quality_{report.status}"
    if expected_prefix not in report.reason_codes:
        raise ValueError("status must match reason_codes")
    if report.reason_code_counts != _reason_code_counts(report.reason_codes):
        raise ValueError("reason_code_counts must match reason_codes")


def _normalize_domain_inputs(
    value: object,
) -> tuple[ResearchCalibrationSampleQualityDomainInput, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("domain_rows must be an iterable")
    try:
        rows = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("domain_rows must be an iterable") from exc
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ResearchCalibrationSampleQualityDomainInput:
            raise ValueError(
                "domain_rows must contain ResearchCalibrationSampleQualityDomainInput values",
            )
        require_paper_only_flags("calibration sample quality input", row)
        if row.domain in seen:
            raise ValueError("domain_rows must contain unique domains")
        seen.add(row.domain)
    return rows


def _normalize_rows(value: object) -> tuple[ResearchCalibrationSampleQualityRow, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        rows = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for row in rows:
        if type(row) is not ResearchCalibrationSampleQualityRow:
            raise ValueError("rows must contain ResearchCalibrationSampleQualityRow values")
        require_paper_only_flags("calibration sample quality row", row)
    if len({row.domain for row in rows}) != len(rows):
        raise ValueError("rows must contain unique domains")
    return rows


def _normalize_reason_code_counts(
    value: object,
) -> tuple[ResearchCalibrationSampleQualityReasonCodeCount, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        rows = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    for row in rows:
        if type(row) is not ResearchCalibrationSampleQualityReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain ResearchCalibrationSampleQualityReasonCodeCount values",
            )
        require_paper_only_flags("calibration sample quality reason count", row)
    return rows


def _normalize_reason_codes(
    field_name: str,
    value: object,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable")
    try:
        items = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable") from exc
    if not items and not allow_empty:
        raise ValueError(f"{field_name} must not be empty")
    normalized: list[str] = []
    for item in items:
        _require_public_slug(field_name, item)
        if item not in normalized:
            normalized.append(item)
    return tuple(normalized)


def _decimal_status_count(
    rows: tuple[ResearchCalibrationSampleQualityRow, ...],
    status: str,
) -> Decimal:
    return Decimal(sum(1 for row in rows if row.status == status))


def _safe_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == Decimal("0"):
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_probability("ratio", numerator / denominator)


def _capped_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == Decimal("0"):
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        value = numerator / denominator
    if value > ONE:
        return ONE
    return _quantize_probability("ratio", value)


def _clamped_one_minus_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    ratio = _capped_ratio(numerator, denominator)
    value = ONE - ratio
    if value < ZERO:
        return ZERO
    return _quantize_probability("ratio", value)


def _average_probability(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_probability("average", sum(values, ZERO) / Decimal(len(values)))


def _average_optional_probability(values: tuple[Decimal | None, ...]) -> Decimal | None:
    if not values or any(value is None for value in values):
        return None
    concrete_values = tuple(value for value in values if value is not None)
    return _average_probability(concrete_values)


def _absolute_probability(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _require_probability_decimal("absolute", abs(value))


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in REPORT_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_public_slug(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    lowered = value.lower()
    if value != lowered:
        raise ValueError(f"{field_name} must be lowercase")
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{field_name} contains unsafe public content")
    for char in value:
        if not (char.islower() or char.isdigit() or char in ("-", "_")):
            raise ValueError(f"{field_name} must contain only public slug characters")


def _require_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_whole_decimal(field_name, value)
    if normalized <= Decimal("0"):
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < Decimal("0"):
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return normalized


def _require_optional_probability_decimal(field_name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _require_probability_decimal(field_name, value)


def _require_probability_decimal(field_name: str, value: object) -> Decimal:
    normalized = _quantize_probability(field_name, _require_decimal(field_name, value))
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _require_optional_bias_decimal(field_name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _require_bias_decimal(field_name, value)


def _require_bias_decimal(field_name: str, value: object) -> Decimal:
    normalized = _quantize_probability(field_name, _require_decimal(field_name, value))
    if normalized < NEGATIVE_ONE or normalized > ONE:
        raise ValueError(f"{field_name} must be between negative one and one")
    return normalized


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _quantize_probability(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(RATIO_QUANTUM)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _payload_value(value: object) -> Any:
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("payload Decimal value must be finite")
        return format(value, "f")
    if type(value) is datetime:
        return value.astimezone(UTC).isoformat()
    if type(value) is tuple:
        return [_payload_value(item) for item in value]
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _payload_value(getattr(value, field.name))
            for field in fields(value)
        }
    if value is None or type(value) in (str, bool):
        return value
    raise ValueError("payload contains an unsupported value")


def _reject_unsafe_public_payload(label: str, value: object, path: str = "") -> None:
    if type(value) is str:
        lowered = value.lower()
        if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
            raise ValueError(f"{path or label} contains unsafe public content")
        return
    if value is None or type(value) is bool:
        return
    if type(value) is float:
        raise ValueError(f"{path or label} must not be a float")
    if type(value) is int:
        raise ValueError(f"{path or label} must use Decimal-derived strings")
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            lowered_key = key.lower()
            if any(fragment in lowered_key for fragment in UNSAFE_PUBLIC_FRAGMENTS):
                raise ValueError(f"unsafe field in {label}: {key}")
            item_path = key if not path else f"{path}.{key}"
            if key in {"paper_only", "report_only", "readonly"} and item is not True:
                raise ValueError(f"{item_path} must be True")
            _reject_unsafe_public_payload(label, item, item_path)
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            item_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_unsafe_public_payload(label, item, item_path)
        return
    raise ValueError(f"{path or label} is not JSON serializable")
