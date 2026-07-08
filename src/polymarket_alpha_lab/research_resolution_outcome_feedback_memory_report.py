"""Aggregate outcome-learning memory report for resolved research cohorts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any


DEFAULT_RESEARCH_RESOLUTION_OUTCOME_FEEDBACK_MEMORY_REPORT_CONFIG_VERSION = (
    "research-resolution-outcome-feedback-memory-report-v0"
)

STATUSES = ("pass", "watch", "block")
CALIBRATION_BUCKETS = ("p00_20", "p20_40", "p40_60", "p60_80", "p80_100")
ERROR_CATEGORIES = (
    "none",
    "calibration_miss",
    "evidence_gap",
    "resolution_rule_misread",
    "stale_thesis",
    "contradiction_missed",
    "other",
)

PASS_REASON_CODE = "outcome_feedback_memory_pass"
EMPTY_REASON_CODE = "outcome_feedback_memory_empty"
ROW_REASON_PRIORITY = (
    "calibration_error_block",
    "stale_thesis_block",
    "thesis_age_block",
    "error_category_block",
    "sample_size_low_block",
    "calibration_error_watch",
    "stale_thesis_watch",
    "thesis_age_watch",
    "error_category_watch",
    "sample_size_low_watch",
    PASS_REASON_CODE,
)
REPORT_REASON_PRIORITY = (
    "outcome_feedback_memory_block",
    "outcome_feedback_memory_watch",
    PASS_REASON_CODE,
    EMPTY_REASON_CODE,
) + ROW_REASON_PRIORITY[:-1]
REASON_CODES = tuple(dict.fromkeys(REPORT_REASON_PRIORITY))
STATUS_RANK = {
    "block": Decimal("0.000000"),
    "watch": Decimal("1.000000"),
    "pass": Decimal("2.000000"),
}
BLOCK_ERROR_CATEGORIES = frozenset(
    ("resolution_rule_misread", "contradiction_missed"),
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
HEX_CHARS = frozenset("0123456789abcdef")


def _join(*parts: str) -> str:
    return "".join(parts)


UNSAFE_PUBLIC_FRAGMENTS = frozenset(
    (
        _join("market", "_", "id"),
        _join("market", "_", "sl", "ug"),
        _join("sl", "ug"),
        _join("ques", "tion"),
        _join("source", "_", "text"),
        _join("source", " ", "text"),
        _join("raw", "_", "text"),
        _join("raw", " ", "text"),
        _join("source", "_", "url"),
        "url",
        "http",
        _join("private", "_", "key"),
        _join("wal", "let"),
        _join("au", "th"),
        _join("tok", "en"),
        _join("ord", "er"),
        _join("li", "ve"),
        _join("tra", "ding"),
        _join("net", "work"),
        _join("data", "base"),
        "dsn",
        _join("per", "sist"),
        "credential",
        "secret",
        "broker",
        "submit",
        "cancel",
        "sign",
        "mutation",
    ),
)


class _FinalPublicDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalPublicDataclass and issubclass(
                base,
                _FinalPublicDataclass,
            ):
                raise TypeError(f"{base.__name__} subclass is not allowed")


@dataclass(frozen=True)
class ResearchResolutionOutcomeFeedbackMemoryConfig(_FinalPublicDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_RESOLUTION_OUTCOME_FEEDBACK_MEMORY_REPORT_CONFIG_VERSION
    )
    watch_abs_calibration_error: Decimal = Decimal("0.100000")
    block_abs_calibration_error: Decimal = Decimal("0.250000")
    watch_stale_thesis_ratio: Decimal = Decimal("0.300000")
    block_stale_thesis_ratio: Decimal = Decimal("0.600000")
    watch_thesis_age_seconds: Decimal = Decimal("604800.000000")
    block_thesis_age_seconds: Decimal = Decimal("1209600.000000")
    min_pass_sample_count: Decimal = Decimal("10.000000")
    min_watch_sample_count: Decimal = Decimal("3.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchResolutionOutcomeFeedbackMemoryConfig, "config")
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_RESOLUTION_OUTCOME_FEEDBACK_MEMORY_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "watch_abs_calibration_error",
            "block_abs_calibration_error",
            "watch_stale_thesis_ratio",
            "block_stale_thesis_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_thesis_age_seconds",
            "block_thesis_age_seconds",
            "min_pass_sample_count",
            "min_watch_sample_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.watch_abs_calibration_error > self.block_abs_calibration_error:
            raise ValueError("watch calibration threshold must not exceed block threshold")
        if self.watch_stale_thesis_ratio > self.block_stale_thesis_ratio:
            raise ValueError("watch stale threshold must not exceed block threshold")
        if self.watch_thesis_age_seconds > self.block_thesis_age_seconds:
            raise ValueError("watch thesis age threshold must not exceed block threshold")
        if self.min_watch_sample_count > self.min_pass_sample_count:
            raise ValueError("watch sample threshold must not exceed pass threshold")
        _require_hard_flags(self)


@dataclass(frozen=True)
class ResearchResolutionOutcomeFeedbackMemoryInput(_FinalPublicDataclass):
    team_id: str
    category_id: str
    calibration_bucket: str
    forecast_probability: Decimal
    realized_outcome_rate: Decimal
    sample_count: Decimal
    error_category: str
    stale_thesis_ratio: Decimal
    thesis_age_seconds: Decimal
    resolved_at: datetime
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchResolutionOutcomeFeedbackMemoryInput, "input")
        for field_name in ("team_id", "category_id"):
            _require_public_string(field_name, getattr(self, field_name))
        _require_member("calibration_bucket", self.calibration_bucket, CALIBRATION_BUCKETS)
        object.__setattr__(
            self,
            "forecast_probability",
            _require_ratio_decimal("forecast_probability", self.forecast_probability),
        )
        object.__setattr__(
            self,
            "realized_outcome_rate",
            _require_ratio_decimal("realized_outcome_rate", self.realized_outcome_rate),
        )
        object.__setattr__(
            self,
            "sample_count",
            _require_count_decimal("sample_count", self.sample_count),
        )
        _require_member("error_category", self.error_category, ERROR_CATEGORIES)
        object.__setattr__(
            self,
            "stale_thesis_ratio",
            _require_ratio_decimal("stale_thesis_ratio", self.stale_thesis_ratio),
        )
        object.__setattr__(
            self,
            "thesis_age_seconds",
            _require_nonnegative_decimal("thesis_age_seconds", self.thesis_age_seconds),
        )
        object.__setattr__(self, "resolved_at", _as_utc("resolved_at", self.resolved_at))
        if _bucket_for_probability(self.forecast_probability) != self.calibration_bucket:
            raise ValueError("calibration_bucket must match forecast_probability")
        _require_hard_flags(self)


@dataclass(frozen=True)
class ResearchResolutionOutcomeFeedbackMemoryReasonCodeCount(_FinalPublicDataclass):
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchResolutionOutcomeFeedbackMemoryReasonCodeCount,
            "reason_code_count",
        )
        _require_member("reason_code", self.reason_code, ROW_REASON_PRIORITY[:-1])
        object.__setattr__(
            self,
            "count",
            _require_count_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "row_ratio",
            _require_ratio_decimal("row_ratio", self.row_ratio),
        )
        _require_hard_flags(self)


@dataclass(frozen=True)
class ResearchResolutionOutcomeFeedbackMemoryBucketRow(_FinalPublicDataclass):
    calibration_bucket: str
    row_count: Decimal
    forecast_probability_average: Decimal
    realized_outcome_rate_average: Decimal
    abs_calibration_error_average: Decimal
    stale_thesis_indicator_count: Decimal
    feedback_queue_count: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchResolutionOutcomeFeedbackMemoryBucketRow,
            "bucket_row",
        )
        _require_member("calibration_bucket", self.calibration_bucket, CALIBRATION_BUCKETS)
        for field_name in (
            "row_count",
            "stale_thesis_indicator_count",
            "feedback_queue_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "forecast_probability_average",
            "realized_outcome_rate_average",
            "abs_calibration_error_average",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_member("status", self.status, STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_PRIORITY),
        )
        _require_hard_flags(self)


@dataclass(frozen=True)
class ResearchResolutionOutcomeFeedbackMemoryRow(_FinalPublicDataclass):
    team_id: str
    category_id: str
    calibration_bucket: str
    forecast_probability: Decimal
    realized_outcome_rate: Decimal
    abs_calibration_error: Decimal
    sample_count: Decimal
    error_category: str
    stale_thesis_ratio: Decimal
    thesis_age_seconds: Decimal
    stale_thesis_indicator: bool
    resolved_at: datetime
    status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchResolutionOutcomeFeedbackMemoryRow, "row")
        for field_name in ("team_id", "category_id"):
            _require_public_string(field_name, getattr(self, field_name))
        _require_member("calibration_bucket", self.calibration_bucket, CALIBRATION_BUCKETS)
        for field_name in (
            "forecast_probability",
            "realized_outcome_rate",
            "abs_calibration_error",
            "stale_thesis_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "sample_count",
            _require_count_decimal("sample_count", self.sample_count),
        )
        _require_member("error_category", self.error_category, ERROR_CATEGORIES)
        object.__setattr__(
            self,
            "thesis_age_seconds",
            _require_nonnegative_decimal("thesis_age_seconds", self.thesis_age_seconds),
        )
        _require_bool("stale_thesis_indicator", self.stale_thesis_indicator)
        object.__setattr__(self, "resolved_at", _as_utc("resolved_at", self.resolved_at))
        _require_member("status", self.status, STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_PRIORITY),
        )
        _require_hard_flags(self)
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                "derived_validation_digest",
                _row_derived_validation_digest(self),
            )
        else:
            object.__setattr__(
                self,
                "derived_validation_digest",
                _require_sha256_digest(
                    "derived_validation_digest",
                    self.derived_validation_digest,
                ),
            )
        _validate_row(self)


@dataclass(frozen=True)
class ResearchResolutionOutcomeFeedbackMemoryReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    status: str
    input_count: Decimal
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    feedback_queue_count: Decimal
    feedback_queue_ratio: Decimal
    calibration_bucket_count: Decimal
    stale_thesis_indicator_count: Decimal
    max_abs_calibration_error: Decimal
    average_abs_calibration_error: Decimal
    max_stale_thesis_ratio: Decimal
    max_thesis_age_seconds: Decimal
    watch_abs_calibration_error: Decimal
    block_abs_calibration_error: Decimal
    watch_stale_thesis_ratio: Decimal
    block_stale_thesis_ratio: Decimal
    watch_thesis_age_seconds: Decimal
    block_thesis_age_seconds: Decimal
    min_pass_sample_count: Decimal
    min_watch_sample_count: Decimal
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchResolutionOutcomeFeedbackMemoryReasonCodeCount, ...]
    calibration_buckets: tuple[ResearchResolutionOutcomeFeedbackMemoryBucketRow, ...]
    rows: tuple[ResearchResolutionOutcomeFeedbackMemoryRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchResolutionOutcomeFeedbackMemoryReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        _require_member("status", self.status, STATUSES)
        for field_name in (
            "input_count",
            "row_count",
            "pass_count",
            "watch_count",
            "block_count",
            "feedback_queue_count",
            "calibration_bucket_count",
            "stale_thesis_indicator_count",
            "min_pass_sample_count",
            "min_watch_sample_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "feedback_queue_ratio",
            "max_abs_calibration_error",
            "average_abs_calibration_error",
            "max_stale_thesis_ratio",
            "watch_abs_calibration_error",
            "block_abs_calibration_error",
            "watch_stale_thesis_ratio",
            "block_stale_thesis_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_thesis_age_seconds",
            "watch_thesis_age_seconds",
            "block_thesis_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, REASON_CODES),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "calibration_buckets",
            _normalize_bucket_rows(self.calibration_buckets),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_hard_flags(self)
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                "derived_validation_digest",
                _report_derived_validation_digest(self),
            )
        else:
            object.__setattr__(
                self,
                "derived_validation_digest",
                _require_sha256_digest(
                    "derived_validation_digest",
                    self.derived_validation_digest,
                ),
            )
        _validate_report(self)


def build_research_resolution_outcome_feedback_memory_report(
    inputs: list[ResearchResolutionOutcomeFeedbackMemoryInput]
    | tuple[ResearchResolutionOutcomeFeedbackMemoryInput, ...],
    *,
    config: ResearchResolutionOutcomeFeedbackMemoryConfig,
    generated_at: datetime,
) -> ResearchResolutionOutcomeFeedbackMemoryReport:
    if type(config) is not ResearchResolutionOutcomeFeedbackMemoryConfig:
        raise ValueError("config must be a ResearchResolutionOutcomeFeedbackMemoryConfig")
    _require_hard_flags(config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(inputs)
    _validate_unique_inputs(normalized_inputs)
    _validate_not_after_generated_at(normalized_inputs, generated_at=generated_at_utc)
    rows = tuple(
        sorted(
            (_build_row(value, config=config) for value in normalized_inputs),
            key=_row_sort_key,
        ),
    )
    row_count = _count(len(rows))
    feedback_queue_count = _count(sum(1 for row in rows if row.status != "pass"))
    return ResearchResolutionOutcomeFeedbackMemoryReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        status=_report_status(rows),
        input_count=row_count,
        row_count=row_count,
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        feedback_queue_count=feedback_queue_count,
        feedback_queue_ratio=_ratio(feedback_queue_count, row_count),
        calibration_bucket_count=_count(len(frozenset(row.calibration_bucket for row in rows))),
        stale_thesis_indicator_count=_count(
            sum(1 for row in rows if row.stale_thesis_indicator),
        ),
        max_abs_calibration_error=max(
            (row.abs_calibration_error for row in rows),
            default=ZERO,
        ),
        average_abs_calibration_error=_average(
            tuple(row.abs_calibration_error for row in rows),
        ),
        max_stale_thesis_ratio=max(
            (row.stale_thesis_ratio for row in rows),
            default=ZERO,
        ),
        max_thesis_age_seconds=max(
            (row.thesis_age_seconds for row in rows),
            default=ZERO,
        ),
        watch_abs_calibration_error=config.watch_abs_calibration_error,
        block_abs_calibration_error=config.block_abs_calibration_error,
        watch_stale_thesis_ratio=config.watch_stale_thesis_ratio,
        block_stale_thesis_ratio=config.block_stale_thesis_ratio,
        watch_thesis_age_seconds=config.watch_thesis_age_seconds,
        block_thesis_age_seconds=config.block_thesis_age_seconds,
        min_pass_sample_count=config.min_pass_sample_count,
        min_watch_sample_count=config.min_watch_sample_count,
        reason_codes=_report_reason_codes(rows),
        reason_code_counts=_reason_code_counts(rows),
        calibration_buckets=_bucket_rows(rows),
        rows=rows,
    )


def research_resolution_outcome_feedback_memory_report_payload(
    report: ResearchResolutionOutcomeFeedbackMemoryReport,
) -> dict[str, Any]:
    if type(report) is not ResearchResolutionOutcomeFeedbackMemoryReport:
        raise ValueError(
            "report must be a ResearchResolutionOutcomeFeedbackMemoryReport",
        )
    _validate_report(report)
    payload = _report_public_payload_for_digest(report)
    payload["derived_validation_digest"] = report.derived_validation_digest
    validate_research_resolution_outcome_feedback_memory_public_payload(payload)
    return payload


def validate_research_resolution_outcome_feedback_memory_public_payload(
    payload: dict[str, Any],
) -> bool:
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _reject_unsafe_public_payload("outcome feedback memory payload", payload)
    _require_public_payload_flags(payload)
    _reject_public_numeric_values(payload)
    digest_value = _payload_required_string(payload, "derived_validation_digest")
    _require_sha256_digest("derived_validation_digest", digest_value)
    if digest_value != _public_payload_derived_validation_digest(payload):
        raise ValueError("derived_validation_digest must match public payload")
    return True


def _build_row(
    value: ResearchResolutionOutcomeFeedbackMemoryInput,
    *,
    config: ResearchResolutionOutcomeFeedbackMemoryConfig,
) -> ResearchResolutionOutcomeFeedbackMemoryRow:
    abs_error = _abs_decimal(value.forecast_probability - value.realized_outcome_rate)
    stale_indicator = (
        value.stale_thesis_ratio >= config.watch_stale_thesis_ratio
        or value.thesis_age_seconds >= config.watch_thesis_age_seconds
    )
    reason_codes = _row_reason_codes(
        abs_calibration_error=abs_error,
        stale_thesis_ratio=value.stale_thesis_ratio,
        thesis_age_seconds=value.thesis_age_seconds,
        sample_count=value.sample_count,
        error_category=value.error_category,
        config=config,
    )
    return ResearchResolutionOutcomeFeedbackMemoryRow(
        team_id=value.team_id,
        category_id=value.category_id,
        calibration_bucket=value.calibration_bucket,
        forecast_probability=value.forecast_probability,
        realized_outcome_rate=value.realized_outcome_rate,
        abs_calibration_error=abs_error,
        sample_count=value.sample_count,
        error_category=value.error_category,
        stale_thesis_ratio=value.stale_thesis_ratio,
        thesis_age_seconds=value.thesis_age_seconds,
        stale_thesis_indicator=stale_indicator,
        resolved_at=value.resolved_at,
        status=_row_status(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    abs_calibration_error: Decimal,
    stale_thesis_ratio: Decimal,
    thesis_age_seconds: Decimal,
    sample_count: Decimal,
    error_category: str,
    config: ResearchResolutionOutcomeFeedbackMemoryConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if abs_calibration_error >= config.block_abs_calibration_error:
        reason_codes.append("calibration_error_block")
    elif abs_calibration_error >= config.watch_abs_calibration_error:
        reason_codes.append("calibration_error_watch")

    if stale_thesis_ratio >= config.block_stale_thesis_ratio:
        reason_codes.append("stale_thesis_block")
    elif stale_thesis_ratio >= config.watch_stale_thesis_ratio:
        reason_codes.append("stale_thesis_watch")

    if thesis_age_seconds >= config.block_thesis_age_seconds:
        reason_codes.append("thesis_age_block")
    elif thesis_age_seconds >= config.watch_thesis_age_seconds:
        reason_codes.append("thesis_age_watch")

    if error_category in BLOCK_ERROR_CATEGORIES:
        reason_codes.append("error_category_block")
    elif error_category != "none":
        reason_codes.append("error_category_watch")

    if sample_count < config.min_watch_sample_count:
        reason_codes.append("sample_size_low_block")
    elif sample_count < config.min_pass_sample_count:
        reason_codes.append("sample_size_low_watch")

    if not reason_codes:
        return (PASS_REASON_CODE,)
    return tuple(reason for reason in ROW_REASON_PRIORITY if reason in reason_codes)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason.endswith("_block") for reason in reason_codes):
        return "block"
    if any(reason.endswith("_watch") for reason in reason_codes):
        return "watch"
    return "pass"


def _report_status(rows: tuple[ResearchResolutionOutcomeFeedbackMemoryRow, ...]) -> str:
    statuses = tuple(row.status for row in rows)
    if "block" in statuses:
        return "block"
    if "watch" in statuses:
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchResolutionOutcomeFeedbackMemoryRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON_CODE,)
    status = _report_status(rows)
    present = frozenset(
        reason
        for row in rows
        for reason in row.reason_codes
        if reason != PASS_REASON_CODE
    )
    if not present:
        return (PASS_REASON_CODE,)
    status_reason = (
        "outcome_feedback_memory_block"
        if status == "block"
        else "outcome_feedback_memory_watch"
    )
    return (status_reason,) + tuple(
        reason for reason in ROW_REASON_PRIORITY[:-1] if reason in present
    )


def _reason_code_counts(
    rows: tuple[ResearchResolutionOutcomeFeedbackMemoryRow, ...],
) -> tuple[ResearchResolutionOutcomeFeedbackMemoryReasonCodeCount, ...]:
    return tuple(
        ResearchResolutionOutcomeFeedbackMemoryReasonCodeCount(
            reason_code=reason_code,
            count=_reason_count(rows, reason_code),
            row_ratio=_ratio(_reason_count(rows, reason_code), _count(len(rows))),
        )
        for reason_code in ROW_REASON_PRIORITY[:-1]
        if _reason_count(rows, reason_code) > ZERO
    )


def _bucket_rows(
    rows: tuple[ResearchResolutionOutcomeFeedbackMemoryRow, ...],
) -> tuple[ResearchResolutionOutcomeFeedbackMemoryBucketRow, ...]:
    bucket_rows: list[ResearchResolutionOutcomeFeedbackMemoryBucketRow] = []
    for calibration_bucket in CALIBRATION_BUCKETS:
        matches = tuple(row for row in rows if row.calibration_bucket == calibration_bucket)
        if not matches:
            continue
        row_count = _count(len(matches))
        feedback_queue_count = _count(sum(1 for row in matches if row.status != "pass"))
        stale_count = _count(sum(1 for row in matches if row.stale_thesis_indicator))
        bucket_rows.append(
            ResearchResolutionOutcomeFeedbackMemoryBucketRow(
                calibration_bucket=calibration_bucket,
                row_count=row_count,
                forecast_probability_average=_average(
                    tuple(row.forecast_probability for row in matches),
                ),
                realized_outcome_rate_average=_average(
                    tuple(row.realized_outcome_rate for row in matches),
                ),
                abs_calibration_error_average=_average(
                    tuple(row.abs_calibration_error for row in matches),
                ),
                stale_thesis_indicator_count=stale_count,
                feedback_queue_count=feedback_queue_count,
                status=_report_status(matches),
                reason_codes=_bucket_reason_codes(matches),
            ),
        )
    return tuple(bucket_rows)


def _bucket_reason_codes(
    rows: tuple[ResearchResolutionOutcomeFeedbackMemoryRow, ...],
) -> tuple[str, ...]:
    present = frozenset(
        reason
        for row in rows
        for reason in row.reason_codes
        if reason != PASS_REASON_CODE
    )
    if not present:
        return (PASS_REASON_CODE,)
    return tuple(reason for reason in ROW_REASON_PRIORITY[:-1] if reason in present)


def _normalize_inputs(
    value: object,
) -> tuple[ResearchResolutionOutcomeFeedbackMemoryInput, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("inputs must be a list or tuple")
    inputs = tuple(value)
    for item in inputs:
        if type(item) is not ResearchResolutionOutcomeFeedbackMemoryInput:
            raise ValueError(
                "inputs must contain ResearchResolutionOutcomeFeedbackMemoryInput values",
            )
        _require_hard_flags(item)
    return inputs


def _normalize_rows(
    value: object,
) -> tuple[ResearchResolutionOutcomeFeedbackMemoryRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    seen: set[tuple[str, str, str, str]] = set()
    for row in rows:
        if type(row) is not ResearchResolutionOutcomeFeedbackMemoryRow:
            raise ValueError("rows must contain ResearchResolutionOutcomeFeedbackMemoryRow values")
        _require_hard_flags(row)
        key = _item_key(row)
        if key in seen:
            raise ValueError("rows must not contain duplicate aggregate feedback")
        seen.add(key)
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must use deterministic sequence")
    return rows


def _normalize_bucket_rows(
    value: object,
) -> tuple[ResearchResolutionOutcomeFeedbackMemoryBucketRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("calibration_buckets must be a list or tuple")
    rows = tuple(value)
    seen: set[str] = set()
    expected = tuple(
        row
        for calibration_bucket in CALIBRATION_BUCKETS
        for row in rows
        if row.calibration_bucket == calibration_bucket
    )
    if rows != expected:
        raise ValueError("calibration_buckets must use deterministic sequence")
    for row in rows:
        if type(row) is not ResearchResolutionOutcomeFeedbackMemoryBucketRow:
            raise ValueError(
                "calibration_buckets must contain "
                "ResearchResolutionOutcomeFeedbackMemoryBucketRow values",
            )
        _require_hard_flags(row)
        if row.calibration_bucket in seen:
            raise ValueError("calibration_buckets must not contain duplicates")
        seen.add(row.calibration_bucket)
    return rows


def _normalize_reason_code_counts(
    value: object,
) -> tuple[ResearchResolutionOutcomeFeedbackMemoryReasonCodeCount, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    counts = tuple(value)
    seen: set[str] = set()
    for item in counts:
        if type(item) is not ResearchResolutionOutcomeFeedbackMemoryReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchResolutionOutcomeFeedbackMemoryReasonCodeCount values",
            )
        _require_hard_flags(item)
        if item.reason_code in seen:
            raise ValueError("reason_code_counts must not contain duplicates")
        seen.add(item.reason_code)
    expected = tuple(
        item
        for reason_code in ROW_REASON_PRIORITY[:-1]
        for item in counts
        if item.reason_code == reason_code
    )
    if counts != expected:
        raise ValueError("reason_code_counts must use deterministic sequence")
    return counts


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    reason_codes = tuple(value)
    seen: set[str] = set()
    for reason_code in reason_codes:
        _require_member(field_name, reason_code, allowed_values)
        if reason_code in seen:
            raise ValueError(f"{field_name} must not contain duplicates")
        seen.add(reason_code)
    expected = tuple(reason for reason in allowed_values if reason in seen)
    if reason_codes != expected:
        raise ValueError(f"{field_name} must use deterministic sequence")
    return reason_codes


def _validate_unique_inputs(
    inputs: tuple[ResearchResolutionOutcomeFeedbackMemoryInput, ...],
) -> None:
    seen: set[tuple[str, str, str, str]] = set()
    for item in inputs:
        key = _item_key(item)
        if key in seen:
            raise ValueError("inputs contain duplicate aggregate feedback")
        seen.add(key)


def _validate_not_after_generated_at(
    inputs: tuple[ResearchResolutionOutcomeFeedbackMemoryInput, ...],
    *,
    generated_at: datetime,
) -> None:
    for item in inputs:
        if item.resolved_at > generated_at:
            raise ValueError("resolved_at must not be after generated_at")


def _validate_row(row: ResearchResolutionOutcomeFeedbackMemoryRow) -> None:
    if _bucket_for_probability(row.forecast_probability) != row.calibration_bucket:
        raise ValueError("calibration_bucket must match forecast_probability")
    if row.abs_calibration_error != _abs_decimal(
        row.forecast_probability - row.realized_outcome_rate,
    ):
        raise ValueError("abs_calibration_error must match probabilities")
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")
    if row.status == "pass" and row.reason_codes != (PASS_REASON_CODE,):
        raise ValueError("pass rows must use pass reason code")
    if row.status != "pass" and PASS_REASON_CODE in row.reason_codes:
        raise ValueError("non-pass rows must not use pass reason code")
    if row.derived_validation_digest != _row_derived_validation_digest(row):
        raise ValueError("derived_validation_digest must match row fields")


def _validate_report(report: ResearchResolutionOutcomeFeedbackMemoryReport) -> None:
    rows = report.rows
    row_count = _count(len(rows))
    if report.input_count != row_count:
        raise ValueError("input_count must match rows")
    if report.row_count != row_count:
        raise ValueError("row_count must match rows")
    for field_name, status in (
        ("pass_count", "pass"),
        ("watch_count", "watch"),
        ("block_count", "block"),
    ):
        if getattr(report, field_name) != _status_count(rows, status):
            raise ValueError(f"{field_name} must match rows")
    if report.pass_count + report.watch_count + report.block_count != report.row_count:
        raise ValueError("status counts must match row_count")
    if report.feedback_queue_count != _count(sum(1 for row in rows if row.status != "pass")):
        raise ValueError("feedback_queue_count must match rows")
    if report.feedback_queue_ratio != _ratio(
        report.feedback_queue_count,
        report.row_count,
    ):
        raise ValueError("feedback_queue_ratio must match rows")
    if report.calibration_bucket_count != _count(
        len(frozenset(row.calibration_bucket for row in rows)),
    ):
        raise ValueError("calibration_bucket_count must match rows")
    if report.stale_thesis_indicator_count != _count(
        sum(1 for row in rows if row.stale_thesis_indicator),
    ):
        raise ValueError("stale_thesis_indicator_count must match rows")
    if report.max_abs_calibration_error != max(
        (row.abs_calibration_error for row in rows),
        default=ZERO,
    ):
        raise ValueError("max_abs_calibration_error must match rows")
    if report.average_abs_calibration_error != _average(
        tuple(row.abs_calibration_error for row in rows),
    ):
        raise ValueError("average_abs_calibration_error must match rows")
    if report.max_stale_thesis_ratio != max(
        (row.stale_thesis_ratio for row in rows),
        default=ZERO,
    ):
        raise ValueError("max_stale_thesis_ratio must match rows")
    if report.max_thesis_age_seconds != max(
        (row.thesis_age_seconds for row in rows),
        default=ZERO,
    ):
        raise ValueError("max_thesis_age_seconds must match rows")
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts must match rows")
    if report.calibration_buckets != _bucket_rows(rows):
        raise ValueError("calibration_buckets must match rows")
    if report.derived_validation_digest != _report_derived_validation_digest(report):
        raise ValueError("derived_validation_digest must match report fields")


def _item_key(
    value: ResearchResolutionOutcomeFeedbackMemoryInput
    | ResearchResolutionOutcomeFeedbackMemoryRow,
) -> tuple[str, str, str, str]:
    return (
        value.team_id,
        value.category_id,
        value.calibration_bucket,
        value.error_category,
    )


def _row_sort_key(
    row: ResearchResolutionOutcomeFeedbackMemoryRow,
) -> tuple[Decimal, Decimal, Decimal, str, str, str, str]:
    return (
        STATUS_RANK[row.status],
        -row.abs_calibration_error,
        -row.stale_thesis_ratio,
        row.team_id,
        row.category_id,
        row.calibration_bucket,
        row.error_category,
    )


def _status_count(
    rows: tuple[ResearchResolutionOutcomeFeedbackMemoryRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _reason_count(
    rows: tuple[ResearchResolutionOutcomeFeedbackMemoryRow, ...],
    reason_code: str,
) -> Decimal:
    return _count(sum(1 for row in rows if reason_code in row.reason_codes))


def _bucket_for_probability(value: Decimal) -> str:
    if value < Decimal("0.200000"):
        return "p00_20"
    if value < Decimal("0.400000"):
        return "p20_40"
    if value < Decimal("0.600000"):
        return "p40_60"
    if value < Decimal("0.800000"):
        return "p60_80"
    return "p80_100"


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(QUANTUM, rounding=ROUND_HALF_EVEN)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(sum(values, ZERO) / Decimal(len(values)))


def _abs_decimal(value: Decimal) -> Decimal:
    return _quantize(abs(value))


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(QUANTUM, rounding=ROUND_HALF_EVEN)


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return _quantize(decimal_value)


def _require_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be an integral Decimal")
    return decimal_value


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _quantize(decimal_value)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    _reject_unsafe_text(field_name, value)


def _require_member(field_name: str, value: object, allowed_values: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed_values:
        joined = ", ".join(allowed_values)
        raise ValueError(f"{field_name} must be one of {joined}")


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be a {expected_type.__name__}")


def _require_hard_flags(value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError("paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError("report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError("readonly must be True")


def _row_public_payload_for_digest(
    row: ResearchResolutionOutcomeFeedbackMemoryRow,
) -> dict[str, Any]:
    payload = _json_value(row)
    if type(payload) is not dict:
        raise ValueError("row payload must be a JSON object")
    payload.pop("derived_validation_digest", None)
    return payload


def _report_public_payload_for_digest(
    report: ResearchResolutionOutcomeFeedbackMemoryReport,
) -> dict[str, Any]:
    payload = _json_value(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    payload.pop("derived_validation_digest", None)
    return payload


def _row_derived_validation_digest(
    row: ResearchResolutionOutcomeFeedbackMemoryRow,
) -> str:
    return _public_payload_derived_validation_digest(_row_public_payload_for_digest(row))


def _report_derived_validation_digest(
    report: ResearchResolutionOutcomeFeedbackMemoryReport,
) -> str:
    return _public_payload_derived_validation_digest(_report_public_payload_for_digest(report))


def _public_payload_derived_validation_digest(payload: dict[str, Any]) -> str:
    digest_payload = dict(payload)
    digest_payload.pop("derived_validation_digest", None)
    _reject_unsafe_public_payload("digest payload", digest_payload)
    encoded = json.dumps(
        digest_payload,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _json_value(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _json_value(getattr(value, field.name)) for field in fields(value)}
    if type(value) is Decimal:
        return str(value)
    if type(value) is datetime:
        return value.astimezone(UTC).isoformat()
    if type(value) in (str, bool):
        return value
    if type(value) in (int, float):
        raise ValueError("JSON value must use Decimal strings, not numeric values")
    if isinstance(value, tuple):
        return [_json_value(item) for item in value]
    if isinstance(value, list):
        return [_json_value(item) for item in value]
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_value(item)
        return ready
    raise ValueError("value is not JSON serializable")


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(character not in HEX_CHARS for character in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    return value


def _payload_required_string(payload: dict[str, Any], key: str) -> str:
    if key not in payload:
        raise ValueError(f"{key} is required")
    value = payload[key]
    if type(value) is not str:
        raise ValueError(f"{key} must be a string")
    return value


def _reject_public_numeric_values(value: object) -> None:
    if type(value) in (int, float, Decimal):
        raise ValueError("public payload must not contain numeric values")
    if isinstance(value, dict):
        for item in value.values():
            _reject_public_numeric_values(item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_public_numeric_values(item)


def _require_public_payload_flags(value: object) -> None:
    if isinstance(value, dict):
        for flag_name in ("paper_only", "report_only", "readonly"):
            if flag_name in value and value[flag_name] is not True:
                raise ValueError(f"{flag_name} must be True")
        for item in value.values():
            _require_public_payload_flags(item)
        return
    if isinstance(value, list):
        for item in value:
            _require_public_payload_flags(item)


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if type(value) is str:
        _reject_unsafe_text(label, value)
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _reject_unsafe_text(label, key)
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_unsafe_public_payload(label, item)


def _reject_unsafe_text(label: str, value: str) -> None:
    normalized = value.lower()
    if any(fragment in normalized for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"unsafe public payload value in {label}")


__all__ = (
    "DEFAULT_RESEARCH_RESOLUTION_OUTCOME_FEEDBACK_MEMORY_REPORT_CONFIG_VERSION",
    "STATUSES",
    "CALIBRATION_BUCKETS",
    "ERROR_CATEGORIES",
    "ResearchResolutionOutcomeFeedbackMemoryConfig",
    "ResearchResolutionOutcomeFeedbackMemoryInput",
    "ResearchResolutionOutcomeFeedbackMemoryReasonCodeCount",
    "ResearchResolutionOutcomeFeedbackMemoryBucketRow",
    "ResearchResolutionOutcomeFeedbackMemoryRow",
    "ResearchResolutionOutcomeFeedbackMemoryReport",
    "build_research_resolution_outcome_feedback_memory_report",
    "research_resolution_outcome_feedback_memory_report_payload",
    "validate_research_resolution_outcome_feedback_memory_public_payload",
)
