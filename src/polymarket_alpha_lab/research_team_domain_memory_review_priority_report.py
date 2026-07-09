"""Report-only priority reducer for sanitized domain memory reviews."""

from __future__ import annotations

from collections import Counter
from collections.abc import Sequence
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
import re
from typing import Any, Mapping


DEFAULT_RESEARCH_TEAM_DOMAIN_MEMORY_REVIEW_PRIORITY_CONFIG_VERSION = (
    "research-team-domain-memory-review-priority-report-v0"
)

PUBLIC_STATUSES = ("pass", "watch", "block")

EMPTY_REASON = "memory_review_priority_empty"
PASS_REASON = "memory_review_priority_pass"
REPORT_PASS_REASON = "memory_review_priority_report_pass"
REPORT_WATCH_REASON = "memory_review_priority_report_watch"
REPORT_BLOCK_REASON = "memory_review_priority_report_block"

CALIBRATION_MISSING_BLOCK_REASON = "calibration_missing_block"
CALIBRATION_AGE_BLOCK_REASON = "calibration_age_block"
CALIBRATION_AGE_WATCH_REASON = "calibration_age_watch"
FORECAST_MISS_RECURRENCE_BLOCK_REASON = "forecast_miss_recurrence_block"
FORECAST_MISS_RECURRENCE_WATCH_REASON = "forecast_miss_recurrence_watch"
EVIDENCE_REUSE_QUALITY_BLOCK_REASON = "evidence_reuse_quality_block"
EVIDENCE_REUSE_QUALITY_WATCH_REASON = "evidence_reuse_quality_watch"
UNRESOLVED_FEEDBACK_BLOCK_REASON = "unresolved_feedback_block"
UNRESOLVED_FEEDBACK_WATCH_REASON = "unresolved_feedback_watch"
REVIEW_CAPACITY_PRESSURE_BLOCK_REASON = "review_capacity_pressure_block"
REVIEW_CAPACITY_PRESSURE_WATCH_REASON = "review_capacity_pressure_watch"
PRIORITY_SCORE_BLOCK_REASON = "review_priority_score_block"
PRIORITY_SCORE_WATCH_REASON = "review_priority_score_watch"

ROW_REASON_CODES = (
    CALIBRATION_MISSING_BLOCK_REASON,
    CALIBRATION_AGE_BLOCK_REASON,
    CALIBRATION_AGE_WATCH_REASON,
    FORECAST_MISS_RECURRENCE_BLOCK_REASON,
    FORECAST_MISS_RECURRENCE_WATCH_REASON,
    EVIDENCE_REUSE_QUALITY_BLOCK_REASON,
    EVIDENCE_REUSE_QUALITY_WATCH_REASON,
    UNRESOLVED_FEEDBACK_BLOCK_REASON,
    UNRESOLVED_FEEDBACK_WATCH_REASON,
    REVIEW_CAPACITY_PRESSURE_BLOCK_REASON,
    REVIEW_CAPACITY_PRESSURE_WATCH_REASON,
    PRIORITY_SCORE_BLOCK_REASON,
    PRIORITY_SCORE_WATCH_REASON,
    PASS_REASON,
)
REPORT_REASON_CODES = (
    EMPTY_REASON,
    REPORT_BLOCK_REASON,
    REPORT_WATCH_REASON,
    REPORT_PASS_REASON,
) + ROW_REASON_CODES
BLOCK_REASONS = (
    EMPTY_REASON,
    REPORT_BLOCK_REASON,
    CALIBRATION_MISSING_BLOCK_REASON,
    CALIBRATION_AGE_BLOCK_REASON,
    FORECAST_MISS_RECURRENCE_BLOCK_REASON,
    EVIDENCE_REUSE_QUALITY_BLOCK_REASON,
    UNRESOLVED_FEEDBACK_BLOCK_REASON,
    REVIEW_CAPACITY_PRESSURE_BLOCK_REASON,
    PRIORITY_SCORE_BLOCK_REASON,
)
WATCH_REASONS = (
    REPORT_WATCH_REASON,
    CALIBRATION_AGE_WATCH_REASON,
    FORECAST_MISS_RECURRENCE_WATCH_REASON,
    EVIDENCE_REUSE_QUALITY_WATCH_REASON,
    UNRESOLVED_FEEDBACK_WATCH_REASON,
    REVIEW_CAPACITY_PRESSURE_WATCH_REASON,
    PRIORITY_SCORE_WATCH_REASON,
)

QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SECONDS_PER_DAY = Decimal("86400.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000.000000")
DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
UNSAFE_PUBLIC_FRAGMENTS = (
    "candidate",
    "market_id",
    "market_slug",
    "market",
    "slug",
    "question",
    "source_url",
    "source_text",
    "source",
    "://",
    "dsn",
    "table",
    "token",
    "secret",
    "auth",
    "wallet",
    "order",
    "trade",
    "trading",
    "live",
    "sizing",
    "recommendation",
)

__all__ = (
    "DEFAULT_RESEARCH_TEAM_DOMAIN_MEMORY_REVIEW_PRIORITY_CONFIG_VERSION",
    "PUBLIC_STATUSES",
    "ResearchTeamDomainMemoryReviewPriorityConfig",
    "ResearchTeamDomainMemoryReviewPriorityInput",
    "ResearchTeamDomainMemoryReviewPriorityRow",
    "ResearchTeamDomainMemoryReviewPriorityReasonCodeCount",
    "ResearchTeamDomainMemoryReviewPriorityReport",
    "build_research_team_domain_memory_review_priority_report",
    "research_team_domain_memory_review_priority_public_payload",
    "research_team_domain_memory_review_priority_report_digest",
)


class _FinalPublicDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalPublicDataclass and issubclass(
                base,
                _FinalPublicDataclass,
            ):
                raise TypeError(f"{base.__name__} may not be subclassed")


@dataclass(frozen=True)
class ResearchTeamDomainMemoryReviewPriorityConfig(_FinalPublicDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_TEAM_DOMAIN_MEMORY_REVIEW_PRIORITY_CONFIG_VERSION
    )
    calibration_age_pressure_weight: Decimal = Decimal("0.200000")
    forecast_miss_recurrence_weight: Decimal = Decimal("0.250000")
    evidence_reuse_quality_weight: Decimal = Decimal("0.200000")
    unresolved_feedback_weight: Decimal = Decimal("0.150000")
    review_capacity_pressure_weight: Decimal = Decimal("0.200000")
    calibration_age_watch_seconds: Decimal = Decimal("1209600.000000")
    calibration_age_block_seconds: Decimal = Decimal("2592000.000000")
    forecast_miss_recurrence_watch_ratio: Decimal = Decimal("0.250000")
    forecast_miss_recurrence_block_ratio: Decimal = Decimal("0.500000")
    evidence_reuse_quality_watch_below: Decimal = Decimal("0.750000")
    evidence_reuse_quality_block_below: Decimal = Decimal("0.500000")
    unresolved_feedback_watch_count: Decimal = Decimal("2.000000")
    unresolved_feedback_block_count: Decimal = Decimal("5.000000")
    review_capacity_pressure_watch_ratio: Decimal = Decimal("0.700000")
    review_capacity_pressure_block_ratio: Decimal = Decimal("0.900000")
    priority_score_watch_threshold: Decimal = Decimal("0.400000")
    priority_score_block_threshold: Decimal = Decimal("0.700000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type("config", self, ResearchTeamDomainMemoryReviewPriorityConfig)
        object.__setattr__(
            self,
            "config_version",
            _require_supported_config_version(self.config_version),
        )
        for field_name in (
            "calibration_age_pressure_weight",
            "forecast_miss_recurrence_weight",
            "evidence_reuse_quality_weight",
            "unresolved_feedback_weight",
            "review_capacity_pressure_weight",
            "forecast_miss_recurrence_watch_ratio",
            "forecast_miss_recurrence_block_ratio",
            "evidence_reuse_quality_watch_below",
            "evidence_reuse_quality_block_below",
            "review_capacity_pressure_watch_ratio",
            "review_capacity_pressure_block_ratio",
            "priority_score_watch_threshold",
            "priority_score_block_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "calibration_age_watch_seconds",
            "calibration_age_block_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "unresolved_feedback_watch_count",
            "unresolved_feedback_block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchTeamDomainMemoryReviewPriorityInput(_FinalPublicDataclass):
    domain_key: str
    team_key: str
    review_reference: str
    last_calibrated_at: datetime | None
    reviewed_forecast_count: Decimal
    recurring_forecast_miss_count: Decimal
    evidence_reuse_quality: Decimal
    unresolved_feedback_count: Decimal
    review_capacity_pressure: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type("input", self, ResearchTeamDomainMemoryReviewPriorityInput)
        object.__setattr__(
            self,
            "domain_key",
            _require_public_identifier("domain_key", self.domain_key),
        )
        object.__setattr__(
            self,
            "team_key",
            _require_public_identifier("team_key", self.team_key),
        )
        object.__setattr__(
            self,
            "review_reference",
            _require_private_reference("review_reference", self.review_reference),
        )
        object.__setattr__(
            self,
            "last_calibrated_at",
            _as_optional_utc("last_calibrated_at", self.last_calibrated_at),
        )
        for field_name in (
            "reviewed_forecast_count",
            "recurring_forecast_miss_count",
            "unresolved_feedback_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_whole_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("evidence_reuse_quality", "review_capacity_pressure"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.recurring_forecast_miss_count > self.reviewed_forecast_count:
            raise ValueError(
                "recurring_forecast_miss_count must not exceed reviewed_forecast_count",
            )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchTeamDomainMemoryReviewPriorityRow(_FinalPublicDataclass):
    priority_rank: Decimal
    domain_key: str
    team_key: str
    last_calibrated_at: datetime | None
    calibration_age_seconds: Decimal | None
    calibration_age_pressure: Decimal
    reviewed_forecast_count: Decimal
    recurring_forecast_miss_count: Decimal
    forecast_miss_recurrence_ratio: Decimal
    evidence_reuse_quality: Decimal
    evidence_reuse_pressure: Decimal
    unresolved_feedback_count: Decimal
    unresolved_feedback_pressure: Decimal
    review_capacity_pressure: Decimal
    review_priority_score: Decimal
    review_memory_digests: tuple[str, ...]
    priority_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type("row", self, ResearchTeamDomainMemoryReviewPriorityRow)
        object.__setattr__(
            self,
            "priority_rank",
            _require_positive_decimal("priority_rank", self.priority_rank),
        )
        object.__setattr__(
            self,
            "domain_key",
            _require_public_identifier("domain_key", self.domain_key),
        )
        object.__setattr__(
            self,
            "team_key",
            _require_public_identifier("team_key", self.team_key),
        )
        object.__setattr__(
            self,
            "last_calibrated_at",
            _as_optional_utc("last_calibrated_at", self.last_calibrated_at),
        )
        if self.calibration_age_seconds is not None:
            object.__setattr__(
                self,
                "calibration_age_seconds",
                _require_nonnegative_decimal(
                    "calibration_age_seconds",
                    self.calibration_age_seconds,
                ),
            )
        for field_name in (
            "reviewed_forecast_count",
            "recurring_forecast_miss_count",
            "unresolved_feedback_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_whole_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "calibration_age_pressure",
            "forecast_miss_recurrence_ratio",
            "evidence_reuse_quality",
            "evidence_reuse_pressure",
            "unresolved_feedback_pressure",
            "review_capacity_pressure",
            "review_priority_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "review_memory_digests",
            _normalize_review_memory_digests(self.review_memory_digests),
        )
        object.__setattr__(
            self,
            "priority_status",
            _require_status("priority_status", self.priority_status),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, ROW_REASON_CODES),
        )
        _validate_row(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchTeamDomainMemoryReviewPriorityReasonCodeCount(_FinalPublicDataclass):
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            "reason count",
            self,
            ResearchTeamDomainMemoryReviewPriorityReasonCodeCount,
        )
        object.__setattr__(
            self,
            "reason_code",
            _require_reason_code("reason_code", self.reason_code),
        )
        object.__setattr__(
            self,
            "count",
            _require_whole_count_decimal("count", self.count),
        )
        if self.count <= ZERO:
            raise ValueError("count must be positive")
        _require_hard_flags("reason count", self)
        _reject_unsafe_public_payload("reason count", self)


@dataclass(frozen=True)
class ResearchTeamDomainMemoryReviewPriorityReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    report_status: str
    input_count: Decimal
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_review_priority_score: Decimal
    oldest_calibration_age_seconds: Decimal
    max_forecast_miss_recurrence_ratio: Decimal
    min_evidence_reuse_quality: Decimal
    max_review_capacity_pressure: Decimal
    rows: tuple[ResearchTeamDomainMemoryReviewPriorityRow, ...]
    reason_code_counts: tuple[ResearchTeamDomainMemoryReviewPriorityReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type("report", self, ResearchTeamDomainMemoryReviewPriorityReport)
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_supported_config_version(self.config_version),
        )
        object.__setattr__(
            self,
            "report_status",
            _require_status("report_status", self.report_status),
        )
        for field_name in (
            "input_count",
            "row_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_whole_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_review_priority_score",
            "max_forecast_miss_recurrence_ratio",
            "min_evidence_reuse_quality",
            "max_review_capacity_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "oldest_calibration_age_seconds",
            _require_nonnegative_decimal(
                "oldest_calibration_age_seconds",
                self.oldest_calibration_age_seconds,
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
            _normalize_reason_codes(self.reason_codes, REPORT_REASON_CODES),
        )
        object.__setattr__(
            self,
            "derived_validation_digest",
            _require_sha256_digest(
                "derived_validation_digest",
                self.derived_validation_digest,
            ),
        )
        _validate_report(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _report_digest_from_values(_report_values_without_digest(self))
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest must match report fields")

    @property
    def public_payload(self) -> dict[str, object]:
        payload = _json_ready(asdict(self))
        if type(payload) is not dict:
            raise ValueError("public payload must be a JSON object")
        _validate_payload_flags(payload, "public_payload")
        _reject_unsafe_public_payload("public_payload", payload)
        return payload


def build_research_team_domain_memory_review_priority_report(
    reviews: Sequence[ResearchTeamDomainMemoryReviewPriorityInput],
    *,
    generated_at: datetime,
    config: ResearchTeamDomainMemoryReviewPriorityConfig | None = None,
) -> ResearchTeamDomainMemoryReviewPriorityReport:
    """Build a deterministic public-safe report from sanitized memory reviews."""

    if config is None:
        config = ResearchTeamDomainMemoryReviewPriorityConfig()
    if type(config) is not ResearchTeamDomainMemoryReviewPriorityConfig:
        raise ValueError(
            "config must be a ResearchTeamDomainMemoryReviewPriorityConfig",
        )
    generated_at = _as_utc("generated_at", generated_at)
    normalized_reviews = _normalize_inputs(reviews, generated_at=generated_at)
    rows = _rank_rows(
        tuple(
            _build_row(review, generated_at=generated_at, config=config)
            for review in normalized_reviews
        ),
    )
    reason_codes = _report_reason_codes(rows)
    values: dict[str, object] = {
        "generated_at": generated_at,
        "config_version": config.config_version,
        "report_status": _status_for_reason_codes(reason_codes),
        "input_count": _decimal_count(len(normalized_reviews)),
        "row_count": _decimal_count(len(rows)),
        "pass_count": _status_count(rows, "pass"),
        "watch_count": _status_count(rows, "watch"),
        "block_count": _status_count(rows, "block"),
        "average_review_priority_score": _average_row_score(rows),
        "oldest_calibration_age_seconds": _oldest_calibration_age_seconds(rows),
        "max_forecast_miss_recurrence_ratio": _max_row_ratio(
            rows,
            "forecast_miss_recurrence_ratio",
        ),
        "min_evidence_reuse_quality": _min_row_ratio(rows, "evidence_reuse_quality"),
        "max_review_capacity_pressure": _max_row_ratio(
            rows,
            "review_capacity_pressure",
        ),
        "rows": rows,
        "reason_code_counts": _reason_code_counts(rows, reason_codes),
        "reason_codes": reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchTeamDomainMemoryReviewPriorityReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def research_team_domain_memory_review_priority_public_payload(
    value: object,
) -> dict[str, Any]:
    if type(value) is ResearchTeamDomainMemoryReviewPriorityReport:
        _require_hard_flags("report", value)
        payload = value.public_payload
    elif type(value) is dict:
        payload = _json_ready(value)
    else:
        raise ValueError(
            "value must be a ResearchTeamDomainMemoryReviewPriorityReport or JSON object",
        )
    if type(payload) is not dict:
        raise ValueError("public payload must be a JSON object")
    _validate_payload_flags(payload, "public_payload")
    _reject_unsafe_public_payload("public_payload", payload)
    return payload


def research_team_domain_memory_review_priority_report_digest(value: object) -> str:
    if type(value) is ResearchTeamDomainMemoryReviewPriorityReport:
        return value.derived_validation_digest
    if type(value) is dict:
        payload = research_team_domain_memory_review_priority_public_payload(value)
        digest_payload = dict(payload)
        digest_payload.pop("derived_validation_digest", None)
        return _report_digest_from_values(digest_payload)
    raise ValueError(
        "value must be a ResearchTeamDomainMemoryReviewPriorityReport or JSON object",
    )


def _build_row(
    review: ResearchTeamDomainMemoryReviewPriorityInput,
    *,
    generated_at: datetime,
    config: ResearchTeamDomainMemoryReviewPriorityConfig,
) -> ResearchTeamDomainMemoryReviewPriorityRow:
    calibration_age_seconds = _calibration_age_seconds(
        generated_at=generated_at,
        last_calibrated_at=review.last_calibrated_at,
    )
    calibration_age_pressure = _calibration_age_pressure(
        calibration_age_seconds,
        config=config,
    )
    forecast_miss_recurrence_ratio = _safe_ratio(
        review.recurring_forecast_miss_count,
        review.reviewed_forecast_count,
    )
    evidence_reuse_pressure = _clamp_ratio(ONE - review.evidence_reuse_quality)
    unresolved_feedback_pressure = _clamp_ratio(
        review.unresolved_feedback_count / config.unresolved_feedback_block_count,
    )
    review_priority_score = _priority_score(
        calibration_age_pressure=calibration_age_pressure,
        forecast_miss_recurrence_ratio=forecast_miss_recurrence_ratio,
        evidence_reuse_pressure=evidence_reuse_pressure,
        unresolved_feedback_pressure=unresolved_feedback_pressure,
        review_capacity_pressure=review.review_capacity_pressure,
        config=config,
    )
    reason_codes = _row_reason_codes(
        last_calibrated_at=review.last_calibrated_at,
        calibration_age_seconds=calibration_age_seconds,
        forecast_miss_recurrence_ratio=forecast_miss_recurrence_ratio,
        evidence_reuse_quality=review.evidence_reuse_quality,
        unresolved_feedback_count=review.unresolved_feedback_count,
        review_capacity_pressure=review.review_capacity_pressure,
        review_priority_score=review_priority_score,
        config=config,
    )
    return ResearchTeamDomainMemoryReviewPriorityRow(
        priority_rank=ONE,
        domain_key=review.domain_key,
        team_key=review.team_key,
        last_calibrated_at=review.last_calibrated_at,
        calibration_age_seconds=calibration_age_seconds,
        calibration_age_pressure=calibration_age_pressure,
        reviewed_forecast_count=review.reviewed_forecast_count,
        recurring_forecast_miss_count=review.recurring_forecast_miss_count,
        forecast_miss_recurrence_ratio=forecast_miss_recurrence_ratio,
        evidence_reuse_quality=review.evidence_reuse_quality,
        evidence_reuse_pressure=evidence_reuse_pressure,
        unresolved_feedback_count=review.unresolved_feedback_count,
        unresolved_feedback_pressure=unresolved_feedback_pressure,
        review_capacity_pressure=review.review_capacity_pressure,
        review_priority_score=review_priority_score,
        review_memory_digests=(_private_reference_digest(review.review_reference),),
        priority_status=_status_for_reason_codes(reason_codes),
        reason_codes=reason_codes,
    )


def _rank_rows(
    rows: tuple[ResearchTeamDomainMemoryReviewPriorityRow, ...],
) -> tuple[ResearchTeamDomainMemoryReviewPriorityRow, ...]:
    sorted_rows = tuple(sorted(rows, key=_row_sort_key))
    return tuple(
        ResearchTeamDomainMemoryReviewPriorityRow(
            priority_rank=_decimal_count(index),
            domain_key=row.domain_key,
            team_key=row.team_key,
            last_calibrated_at=row.last_calibrated_at,
            calibration_age_seconds=row.calibration_age_seconds,
            calibration_age_pressure=row.calibration_age_pressure,
            reviewed_forecast_count=row.reviewed_forecast_count,
            recurring_forecast_miss_count=row.recurring_forecast_miss_count,
            forecast_miss_recurrence_ratio=row.forecast_miss_recurrence_ratio,
            evidence_reuse_quality=row.evidence_reuse_quality,
            evidence_reuse_pressure=row.evidence_reuse_pressure,
            unresolved_feedback_count=row.unresolved_feedback_count,
            unresolved_feedback_pressure=row.unresolved_feedback_pressure,
            review_capacity_pressure=row.review_capacity_pressure,
            review_priority_score=row.review_priority_score,
            review_memory_digests=row.review_memory_digests,
            priority_status=row.priority_status,
            reason_codes=row.reason_codes,
        )
        for index, row in enumerate(sorted_rows, start=1)
    )


def _row_sort_key(
    row: ResearchTeamDomainMemoryReviewPriorityRow,
) -> tuple[int, Decimal, str, str]:
    score_sort = ZERO if row.priority_status == "pass" else -row.review_priority_score
    return (
        {"block": 0, "watch": 1, "pass": 2}[row.priority_status],
        score_sort,
        row.domain_key,
        row.team_key,
    )


def _priority_score(
    *,
    calibration_age_pressure: Decimal,
    forecast_miss_recurrence_ratio: Decimal,
    evidence_reuse_pressure: Decimal,
    unresolved_feedback_pressure: Decimal,
    review_capacity_pressure: Decimal,
    config: ResearchTeamDomainMemoryReviewPriorityConfig,
) -> Decimal:
    return _clamp_ratio(
        calibration_age_pressure * config.calibration_age_pressure_weight
        + forecast_miss_recurrence_ratio * config.forecast_miss_recurrence_weight
        + evidence_reuse_pressure * config.evidence_reuse_quality_weight
        + unresolved_feedback_pressure * config.unresolved_feedback_weight
        + review_capacity_pressure * config.review_capacity_pressure_weight,
    )


def _row_reason_codes(
    *,
    last_calibrated_at: datetime | None,
    calibration_age_seconds: Decimal | None,
    forecast_miss_recurrence_ratio: Decimal,
    evidence_reuse_quality: Decimal,
    unresolved_feedback_count: Decimal,
    review_capacity_pressure: Decimal,
    review_priority_score: Decimal,
    config: ResearchTeamDomainMemoryReviewPriorityConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if last_calibrated_at is None:
        reason_codes.append(CALIBRATION_MISSING_BLOCK_REASON)
    elif calibration_age_seconds is not None:
        if calibration_age_seconds >= config.calibration_age_block_seconds:
            reason_codes.append(CALIBRATION_AGE_BLOCK_REASON)
        elif calibration_age_seconds >= config.calibration_age_watch_seconds:
            reason_codes.append(CALIBRATION_AGE_WATCH_REASON)

    if forecast_miss_recurrence_ratio >= config.forecast_miss_recurrence_block_ratio:
        reason_codes.append(FORECAST_MISS_RECURRENCE_BLOCK_REASON)
    elif forecast_miss_recurrence_ratio >= config.forecast_miss_recurrence_watch_ratio:
        reason_codes.append(FORECAST_MISS_RECURRENCE_WATCH_REASON)

    if evidence_reuse_quality < config.evidence_reuse_quality_block_below:
        reason_codes.append(EVIDENCE_REUSE_QUALITY_BLOCK_REASON)
    elif evidence_reuse_quality < config.evidence_reuse_quality_watch_below:
        reason_codes.append(EVIDENCE_REUSE_QUALITY_WATCH_REASON)

    if unresolved_feedback_count >= config.unresolved_feedback_block_count:
        reason_codes.append(UNRESOLVED_FEEDBACK_BLOCK_REASON)
    elif unresolved_feedback_count >= config.unresolved_feedback_watch_count:
        reason_codes.append(UNRESOLVED_FEEDBACK_WATCH_REASON)

    if review_capacity_pressure >= config.review_capacity_pressure_block_ratio:
        reason_codes.append(REVIEW_CAPACITY_PRESSURE_BLOCK_REASON)
    elif review_capacity_pressure >= config.review_capacity_pressure_watch_ratio:
        reason_codes.append(REVIEW_CAPACITY_PRESSURE_WATCH_REASON)

    if review_priority_score >= config.priority_score_block_threshold:
        reason_codes.append(PRIORITY_SCORE_BLOCK_REASON)
    elif review_priority_score >= config.priority_score_watch_threshold:
        reason_codes.append(PRIORITY_SCORE_WATCH_REASON)

    if not reason_codes:
        reason_codes.append(PASS_REASON)
    return tuple(reason_codes)


def _report_reason_codes(
    rows: tuple[ResearchTeamDomainMemoryReviewPriorityRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON,)
    row_reason_codes = tuple(
        reason_code for row in rows for reason_code in row.reason_codes
    )
    status_reason = (
        REPORT_BLOCK_REASON
        if any(reason_code in BLOCK_REASONS for reason_code in row_reason_codes)
        else REPORT_WATCH_REASON
        if any(reason_code in WATCH_REASONS for reason_code in row_reason_codes)
        else REPORT_PASS_REASON
    )
    reasons = [status_reason]
    reasons.extend(
        reason_code for reason_code in ROW_REASON_CODES if reason_code in row_reason_codes
    )
    return tuple(reasons)


def _status_for_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in BLOCK_REASONS for reason_code in reason_codes):
        return "block"
    if any(reason_code in WATCH_REASONS for reason_code in reason_codes):
        return "watch"
    return "pass"


def _calibration_age_seconds(
    *,
    generated_at: datetime,
    last_calibrated_at: datetime | None,
) -> Decimal | None:
    if last_calibrated_at is None:
        return None
    if last_calibrated_at > generated_at:
        raise ValueError("last_calibrated_at must not be after generated_at")
    return _duration_seconds(last_calibrated_at, generated_at)


def _calibration_age_pressure(
    age_seconds: Decimal | None,
    *,
    config: ResearchTeamDomainMemoryReviewPriorityConfig,
) -> Decimal:
    if age_seconds is None:
        return ONE
    return _clamp_ratio(age_seconds / config.calibration_age_block_seconds)


def _duration_seconds(start: datetime, end: datetime) -> Decimal:
    if end < start:
        raise ValueError("end time must be at least start time")
    delta = end - start
    return (
        Decimal(delta.days) * SECONDS_PER_DAY
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND)
    ).quantize(QUANT, rounding=ROUND_HALF_UP)


def _safe_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return _clamp_ratio(numerator / denominator)


def _average_row_score(
    rows: tuple[ResearchTeamDomainMemoryReviewPriorityRow, ...],
) -> Decimal:
    if not rows:
        return ZERO
    return _clamp_ratio(
        sum((row.review_priority_score for row in rows), ZERO) / Decimal(len(rows)),
    )


def _oldest_calibration_age_seconds(
    rows: tuple[ResearchTeamDomainMemoryReviewPriorityRow, ...],
) -> Decimal:
    values = tuple(row.calibration_age_seconds for row in rows if row.calibration_age_seconds is not None)
    if not values:
        return ZERO
    return _require_nonnegative_decimal("oldest_calibration_age_seconds", max(values))


def _max_row_ratio(
    rows: tuple[ResearchTeamDomainMemoryReviewPriorityRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    return _require_ratio_decimal(field_name, max(getattr(row, field_name) for row in rows))


def _min_row_ratio(
    rows: tuple[ResearchTeamDomainMemoryReviewPriorityRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    return _require_ratio_decimal(field_name, min(getattr(row, field_name) for row in rows))


def _status_count(
    rows: tuple[ResearchTeamDomainMemoryReviewPriorityRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.priority_status == status))


def _reason_code_counts(
    rows: tuple[ResearchTeamDomainMemoryReviewPriorityRow, ...],
    report_reason_codes: tuple[str, ...],
) -> tuple[ResearchTeamDomainMemoryReviewPriorityReasonCodeCount, ...]:
    counts = Counter(reason_code for row in rows for reason_code in row.reason_codes)
    for reason_code in report_reason_codes:
        counts[reason_code] += 1
    return tuple(
        ResearchTeamDomainMemoryReviewPriorityReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(counts[reason_code]),
        )
        for reason_code in REPORT_REASON_CODES
        if counts[reason_code] > 0
    )


def _validate_config(config: ResearchTeamDomainMemoryReviewPriorityConfig) -> None:
    total_weight = (
        config.calibration_age_pressure_weight
        + config.forecast_miss_recurrence_weight
        + config.evidence_reuse_quality_weight
        + config.unresolved_feedback_weight
        + config.review_capacity_pressure_weight
    ).quantize(QUANT)
    if total_weight != ONE:
        raise ValueError("priority weights must sum to 1")
    if config.calibration_age_block_seconds < config.calibration_age_watch_seconds:
        raise ValueError("calibration_age_block_seconds must be at least watch seconds")
    if (
        config.forecast_miss_recurrence_block_ratio
        < config.forecast_miss_recurrence_watch_ratio
    ):
        raise ValueError(
            "forecast_miss_recurrence_block_ratio must be at least watch ratio",
        )
    if config.evidence_reuse_quality_block_below > (
        config.evidence_reuse_quality_watch_below
    ):
        raise ValueError(
            "evidence_reuse_quality_block_below must not exceed watch threshold",
        )
    if config.unresolved_feedback_block_count < config.unresolved_feedback_watch_count:
        raise ValueError(
            "unresolved_feedback_block_count must be at least watch count",
        )
    if (
        config.review_capacity_pressure_block_ratio
        < config.review_capacity_pressure_watch_ratio
    ):
        raise ValueError(
            "review_capacity_pressure_block_ratio must be at least watch ratio",
        )
    if config.priority_score_block_threshold < config.priority_score_watch_threshold:
        raise ValueError(
            "priority_score_block_threshold must be at least watch threshold",
        )


def _validate_row(row: ResearchTeamDomainMemoryReviewPriorityRow) -> None:
    if row.recurring_forecast_miss_count > row.reviewed_forecast_count:
        raise ValueError(
            "recurring_forecast_miss_count must not exceed reviewed_forecast_count",
        )
    if row.evidence_reuse_pressure != _clamp_ratio(ONE - row.evidence_reuse_quality):
        raise ValueError("evidence_reuse_pressure must match evidence_reuse_quality")
    if row.priority_status != _status_for_reason_codes(row.reason_codes):
        raise ValueError("priority_status must match reason_codes")
    if row.reason_codes != tuple(
        reason_code for reason_code in ROW_REASON_CODES if reason_code in row.reason_codes
    ):
        raise ValueError("reason_codes must use canonical reason code order")


def _validate_report(report: ResearchTeamDomainMemoryReviewPriorityReport) -> None:
    if report.row_count != _decimal_count(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.input_count != report.row_count:
        raise ValueError("input_count must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, "block"):
        raise ValueError("block_count must match rows")
    if report.average_review_priority_score != _average_row_score(report.rows):
        raise ValueError("average_review_priority_score must match rows")
    if report.oldest_calibration_age_seconds != _oldest_calibration_age_seconds(
        report.rows,
    ):
        raise ValueError("oldest_calibration_age_seconds must match rows")
    if report.max_forecast_miss_recurrence_ratio != _max_row_ratio(
        report.rows,
        "forecast_miss_recurrence_ratio",
    ):
        raise ValueError("max_forecast_miss_recurrence_ratio must match rows")
    if report.min_evidence_reuse_quality != _min_row_ratio(
        report.rows,
        "evidence_reuse_quality",
    ):
        raise ValueError("min_evidence_reuse_quality must match rows")
    if report.max_review_capacity_pressure != _max_row_ratio(
        report.rows,
        "review_capacity_pressure",
    ):
        raise ValueError("max_review_capacity_pressure must match rows")
    if report.report_status != _status_for_reason_codes(report.reason_codes):
        raise ValueError("report_status must match reason_codes")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows, report.reason_codes):
        raise ValueError("reason_code_counts must match rows")
    if report.rows != tuple(sorted(report.rows, key=_row_sort_key)):
        raise ValueError("rows must use deterministic priority sorting")


def _normalize_inputs(
    value: object,
    *,
    generated_at: datetime,
) -> tuple[ResearchTeamDomainMemoryReviewPriorityInput, ...]:
    if isinstance(value, (str, bytes)) or type(value) not in (list, tuple):
        raise ValueError("reviews must be a list or tuple")
    reviews = tuple(value)
    seen_keys: set[tuple[str, str, str]] = set()
    for review in reviews:
        if type(review) is not ResearchTeamDomainMemoryReviewPriorityInput:
            raise ValueError(
                "reviews must contain ResearchTeamDomainMemoryReviewPriorityInput values",
            )
        _require_hard_flags("input", review)
        if review.last_calibrated_at is not None and review.last_calibrated_at > generated_at:
            raise ValueError("last_calibrated_at must not be after generated_at")
        key = (review.domain_key, review.team_key, _private_reference_digest(review.review_reference))
        if key in seen_keys:
            raise ValueError("reviews must have unique domain/team/review digest values")
        seen_keys.add(key)
    return tuple(sorted(reviews, key=lambda item: (item.domain_key, item.team_key, _private_reference_digest(item.review_reference))))


def _normalize_rows(
    value: object,
) -> tuple[ResearchTeamDomainMemoryReviewPriorityRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    seen_ranks: set[Decimal] = set()
    seen_keys: set[tuple[str, str, tuple[str, ...]]] = set()
    for row in rows:
        if type(row) is not ResearchTeamDomainMemoryReviewPriorityRow:
            raise ValueError(
                "rows must contain ResearchTeamDomainMemoryReviewPriorityRow values",
            )
        _require_hard_flags("row", row)
        if row.priority_rank in seen_ranks:
            raise ValueError("priority_rank values must be unique")
        seen_ranks.add(row.priority_rank)
        key = (row.domain_key, row.team_key, row.review_memory_digests)
        if key in seen_keys:
            raise ValueError("rows must have unique domain/team/review digest values")
        seen_keys.add(key)
    return rows


def _normalize_reason_code_counts(
    value: object,
) -> tuple[ResearchTeamDomainMemoryReviewPriorityReasonCodeCount, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    rows = tuple(value)
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ResearchTeamDomainMemoryReviewPriorityReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain ResearchTeamDomainMemoryReviewPriorityReasonCodeCount values",
            )
        _require_hard_flags("reason count", row)
        if row.reason_code in seen:
            raise ValueError("reason_code_counts reason_code values must be unique")
        seen.add(row.reason_code)
    if rows != tuple(sorted(rows, key=lambda row: REPORT_REASON_CODES.index(row.reason_code))):
        raise ValueError("reason_code_counts must be deterministic")
    return rows


def _normalize_reason_codes(
    value: object,
    allowed_reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    seen: set[str] = set()
    for reason_code in reason_codes:
        _require_canonical_string("reason_code", reason_code)
        if reason_code not in allowed_reason_codes:
            raise ValueError("reason_codes contain an unsupported reason code")
        if reason_code in seen:
            raise ValueError("reason_codes must not contain duplicates")
        seen.add(reason_code)
    if reason_codes != tuple(
        reason_code for reason_code in allowed_reason_codes if reason_code in reason_codes
    ):
        raise ValueError("reason_codes must use canonical reason code order")
    return reason_codes


def _normalize_review_memory_digests(value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("review_memory_digests must be a list or tuple")
    digests = tuple(value)
    if not digests:
        raise ValueError("review_memory_digests must not be empty")
    for digest in digests:
        _require_prefixed_sha256_digest("review_memory_digests", digest)
    if len(set(digests)) != len(digests):
        raise ValueError("review_memory_digests must be unique")
    if digests != tuple(sorted(digests)):
        raise ValueError("review_memory_digests must be deterministic")
    return digests


def _require_exact_type(label: str, value: object, expected_type: type[object]) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_supported_config_version(value: object) -> str:
    _require_canonical_string("config_version", value)
    if value != DEFAULT_RESEARCH_TEAM_DOMAIN_MEMORY_REVIEW_PRIORITY_CONFIG_VERSION:
        raise ValueError("config_version is not supported")
    return value


def _require_public_identifier(field_name: str, value: object) -> str:
    _require_canonical_string(field_name, value)
    if type(value) is not str or PUBLIC_IDENTIFIER_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a public identifier")
    _reject_unsafe_public_text(field_name, value)
    return value


def _require_private_reference(field_name: str, value: object) -> str:
    _require_canonical_string(field_name, value)
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    return value


def _require_status(field_name: str, value: object) -> str:
    _require_canonical_string(field_name, value)
    if value not in PUBLIC_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")
    return value


def _require_reason_code(field_name: str, value: object) -> str:
    _require_canonical_string(field_name, value)
    if value not in REPORT_REASON_CODES:
        raise ValueError(f"{field_name} must be a supported reason code")
    return value


def _require_sha256_digest(field_name: str, value: object) -> str:
    _require_canonical_string(field_name, value)
    if type(value) is not str or DIGEST_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    return value


def _require_prefixed_sha256_digest(field_name: str, value: object) -> str:
    _require_canonical_string(field_name, value)
    if type(value) is not str or not value.startswith("sha256:"):
        raise ValueError(f"{field_name} must contain sha256-prefixed digests")
    _require_sha256_digest(field_name, value.removeprefix("sha256:"))
    return value


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value).quantize(
        QUANT,
        rounding=ROUND_HALF_UP,
    )
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_whole_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal count")
    return decimal_value


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value).quantize(
        QUANT,
        rounding=ROUND_HALF_UP,
    )
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return decimal_value


def _clamp_ratio(value: Decimal) -> Decimal:
    decimal_value = _require_decimal("ratio", value)
    if decimal_value < ZERO:
        return ZERO
    if decimal_value > ONE:
        return ONE
    return decimal_value.quantize(QUANT, rounding=ROUND_HALF_UP)


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count must be a nonnegative int")
    return Decimal(value).quantize(QUANT, rounding=ROUND_HALF_UP)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _as_optional_utc(field_name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _private_reference_digest(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def _report_values_without_digest(
    report: ResearchTeamDomainMemoryReviewPriorityReport,
) -> dict[str, object]:
    values = asdict(report)
    values.pop("derived_validation_digest", None)
    return values


def _report_digest_from_values(values: Mapping[str, object]) -> str:
    payload = _json_ready(values)
    _reject_unsafe_public_payload("digest payload", payload)
    canonical = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _json_ready(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, dict):
        ready: dict[str, object] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if type(value) is datetime:
        return _as_utc("datetime", value).isoformat()
    if value is None:
        return None
    if type(value) is bool:
        return value
    if type(value) is int or type(value) is float:
        raise ValueError("JSON numeric value must use Decimal")
    if type(value) is str:
        return value
    raise ValueError("value is not JSON serializable")


def _validate_payload_flags(payload: dict[str, object], label: str) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload.get(field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    path: str = "",
) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value), path)
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            item_path = key if not path else f"{path}.{key}"
            _reject_unsafe_public_text(item_path, key)
            if key in ("paper_only", "report_only", "readonly") and item is not True:
                raise ValueError(f"{item_path} must be True")
            _reject_unsafe_public_payload(label, item, item_path)
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            item_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_unsafe_public_payload(label, item, item_path)
        return
    if type(value) is str:
        _reject_unsafe_public_text(path or label, value)
        return
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError(f"{path or label} must be finite")
        return
    if type(value) is datetime:
        _as_utc(path or label, value)
        return
    if value is None or type(value) is bool:
        return
    if type(value) is int or type(value) is float:
        raise ValueError("public payload numeric value must use Decimal")
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_public_text(path: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"unsafe public payload at {path}")
