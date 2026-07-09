"""Report-only scoring for sanitized team domain claim-review memory quality."""

from __future__ import annotations

from collections import Counter
from collections.abc import Sequence
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from hashlib import sha256
import json
import re
from typing import Any


DEFAULT_RESEARCH_TEAM_DOMAIN_CLAIM_REVIEW_MEMORY_SCORE_CONFIG_VERSION = (
    "research-team-domain-claim-review-memory-score-report-v0"
)

PUBLIC_STATUSES = ("pass", "watch", "block")

EMPTY_REASON = "domain_claim_review_memory_score_empty"
PASS_REASON = "domain_claim_review_memory_score_pass"
REPORT_PASS_REASON = "domain_claim_review_memory_score_report_pass"
REPORT_WATCH_REASON = "domain_claim_review_memory_score_report_watch"
REPORT_BLOCK_REASON = "domain_claim_review_memory_score_report_block"

MEMORY_AGE_BLOCK_REASON = "memory_age_block"
MEMORY_AGE_WATCH_REASON = "memory_age_watch"
MEMORY_HIT_RATE_BLOCK_REASON = "memory_hit_rate_block"
MEMORY_HIT_RATE_WATCH_REASON = "memory_hit_rate_watch"
CORRECTION_RATE_BLOCK_REASON = "correction_rate_block"
CORRECTION_RATE_WATCH_REASON = "correction_rate_watch"
REVIEWER_ALIGNMENT_BLOCK_REASON = "reviewer_alignment_block"
REVIEWER_ALIGNMENT_WATCH_REASON = "reviewer_alignment_watch"
UNRESOLVED_PRESSURE_BLOCK_REASON = "unresolved_pressure_block"
UNRESOLVED_PRESSURE_WATCH_REASON = "unresolved_pressure_watch"
STALE_MEMORY_PRESSURE_BLOCK_REASON = "stale_memory_pressure_block"
STALE_MEMORY_PRESSURE_WATCH_REASON = "stale_memory_pressure_watch"
MEMORY_SCORE_BLOCK_REASON = "memory_score_block"
MEMORY_SCORE_WATCH_REASON = "memory_score_watch"

ROW_REASON_CODES = (
    MEMORY_AGE_BLOCK_REASON,
    MEMORY_AGE_WATCH_REASON,
    MEMORY_HIT_RATE_BLOCK_REASON,
    MEMORY_HIT_RATE_WATCH_REASON,
    CORRECTION_RATE_BLOCK_REASON,
    CORRECTION_RATE_WATCH_REASON,
    REVIEWER_ALIGNMENT_BLOCK_REASON,
    REVIEWER_ALIGNMENT_WATCH_REASON,
    UNRESOLVED_PRESSURE_BLOCK_REASON,
    UNRESOLVED_PRESSURE_WATCH_REASON,
    STALE_MEMORY_PRESSURE_BLOCK_REASON,
    STALE_MEMORY_PRESSURE_WATCH_REASON,
    MEMORY_SCORE_BLOCK_REASON,
    MEMORY_SCORE_WATCH_REASON,
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
    MEMORY_AGE_BLOCK_REASON,
    MEMORY_HIT_RATE_BLOCK_REASON,
    CORRECTION_RATE_BLOCK_REASON,
    REVIEWER_ALIGNMENT_BLOCK_REASON,
    UNRESOLVED_PRESSURE_BLOCK_REASON,
    STALE_MEMORY_PRESSURE_BLOCK_REASON,
    MEMORY_SCORE_BLOCK_REASON,
)
WATCH_REASONS = (
    REPORT_WATCH_REASON,
    MEMORY_AGE_WATCH_REASON,
    MEMORY_HIT_RATE_WATCH_REASON,
    CORRECTION_RATE_WATCH_REASON,
    REVIEWER_ALIGNMENT_WATCH_REASON,
    UNRESOLVED_PRESSURE_WATCH_REASON,
    STALE_MEMORY_PRESSURE_WATCH_REASON,
    MEMORY_SCORE_WATCH_REASON,
)

QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SECONDS_PER_DAY = Decimal("86400.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000.000000")
DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
DECIMAL_TEXT_RE = re.compile(r"^(0|[1-9][0-9]*)\.[0-9]{6}$")
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
    "DEFAULT_RESEARCH_TEAM_DOMAIN_CLAIM_REVIEW_MEMORY_SCORE_CONFIG_VERSION",
    "PUBLIC_STATUSES",
    "ResearchTeamDomainClaimReviewMemoryScoreConfig",
    "ResearchTeamDomainClaimReviewMemoryScoreInput",
    "ResearchTeamDomainClaimReviewMemoryScoreRow",
    "ResearchTeamDomainClaimReviewMemoryScoreReasonCodeCount",
    "ResearchTeamDomainClaimReviewMemoryScoreReport",
    "build_research_team_domain_claim_review_memory_score_report",
    "research_team_domain_claim_review_memory_score_public_payload",
    "research_team_domain_claim_review_memory_score_report_digest",
    "validate_research_team_domain_claim_review_memory_score_public_payload",
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
class ResearchTeamDomainClaimReviewMemoryScoreConfig(_FinalPublicDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_TEAM_DOMAIN_CLAIM_REVIEW_MEMORY_SCORE_CONFIG_VERSION
    )
    memory_hit_rate_weight: Decimal = Decimal("0.300000")
    correction_rate_weight: Decimal = Decimal("0.200000")
    memory_freshness_weight: Decimal = Decimal("0.200000")
    reviewer_alignment_weight: Decimal = Decimal("0.200000")
    unresolved_resolution_weight: Decimal = Decimal("0.100000")
    memory_age_watch_seconds: Decimal = Decimal("1209600.000000")
    memory_age_block_seconds: Decimal = Decimal("2592000.000000")
    memory_hit_rate_watch_below: Decimal = Decimal("0.600000")
    memory_hit_rate_block_below: Decimal = Decimal("0.300000")
    correction_rate_watch_below: Decimal = Decimal("0.600000")
    correction_rate_block_below: Decimal = Decimal("0.300000")
    reviewer_alignment_watch_below: Decimal = Decimal("0.750000")
    reviewer_alignment_block_below: Decimal = Decimal("0.500000")
    unresolved_pressure_watch_ratio: Decimal = Decimal("0.250000")
    unresolved_pressure_block_ratio: Decimal = Decimal("0.500000")
    stale_memory_watch_ratio: Decimal = Decimal("0.250000")
    stale_memory_block_ratio: Decimal = Decimal("0.500000")
    memory_score_watch_threshold: Decimal = Decimal("0.700000")
    memory_score_block_threshold: Decimal = Decimal("0.400000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            "config",
            self,
            ResearchTeamDomainClaimReviewMemoryScoreConfig,
        )
        object.__setattr__(
            self,
            "config_version",
            _require_supported_config_version(self.config_version),
        )
        for field_name in (
            "memory_hit_rate_weight",
            "correction_rate_weight",
            "memory_freshness_weight",
            "reviewer_alignment_weight",
            "unresolved_resolution_weight",
            "memory_hit_rate_watch_below",
            "memory_hit_rate_block_below",
            "correction_rate_watch_below",
            "correction_rate_block_below",
            "reviewer_alignment_watch_below",
            "reviewer_alignment_block_below",
            "unresolved_pressure_watch_ratio",
            "unresolved_pressure_block_ratio",
            "stale_memory_watch_ratio",
            "stale_memory_block_ratio",
            "memory_score_watch_threshold",
            "memory_score_block_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("memory_age_watch_seconds", "memory_age_block_seconds"):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchTeamDomainClaimReviewMemoryScoreInput(_FinalPublicDataclass):
    domain_key: str
    team_key: str
    claim_review_reference: str
    reviewed_at: datetime
    memory_observed_at: datetime
    claim_review_count: Decimal
    memory_hit_count: Decimal
    corrected_claim_review_count: Decimal
    unresolved_claim_review_count: Decimal
    stale_memory_count: Decimal
    reviewer_alignment_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type("input", self, ResearchTeamDomainClaimReviewMemoryScoreInput)
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
            "claim_review_reference",
            _require_private_reference(
                "claim_review_reference",
                self.claim_review_reference,
            ),
        )
        object.__setattr__(self, "reviewed_at", _as_utc("reviewed_at", self.reviewed_at))
        object.__setattr__(
            self,
            "memory_observed_at",
            _as_utc("memory_observed_at", self.memory_observed_at),
        )
        object.__setattr__(
            self,
            "claim_review_count",
            _require_positive_whole_decimal(
                "claim_review_count",
                self.claim_review_count,
            ),
        )
        for field_name in (
            "memory_hit_count",
            "corrected_claim_review_count",
            "unresolved_claim_review_count",
            "stale_memory_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_whole_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reviewer_alignment_score",
            _require_ratio_decimal(
                "reviewer_alignment_score",
                self.reviewer_alignment_score,
            ),
        )
        _validate_input_counts(self)
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchTeamDomainClaimReviewMemoryScoreRow(_FinalPublicDataclass):
    memory_rank: Decimal
    domain_key: str
    team_key: str
    claim_review_digest: str
    reviewed_at: datetime
    memory_observed_at: datetime
    memory_age_seconds: Decimal
    claim_review_count: Decimal
    memory_hit_count: Decimal
    memory_hit_rate: Decimal
    corrected_claim_review_count: Decimal
    correction_rate: Decimal
    unresolved_claim_review_count: Decimal
    unresolved_pressure: Decimal
    stale_memory_count: Decimal
    stale_memory_pressure: Decimal
    memory_freshness_score: Decimal
    reviewer_alignment_score: Decimal
    memory_score: Decimal
    memory_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type("row", self, ResearchTeamDomainClaimReviewMemoryScoreRow)
        object.__setattr__(
            self,
            "memory_rank",
            _require_positive_decimal("memory_rank", self.memory_rank),
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
            "claim_review_digest",
            _require_sha256_digest("claim_review_digest", self.claim_review_digest),
        )
        object.__setattr__(self, "reviewed_at", _as_utc("reviewed_at", self.reviewed_at))
        object.__setattr__(
            self,
            "memory_observed_at",
            _as_utc("memory_observed_at", self.memory_observed_at),
        )
        for field_name in (
            "memory_age_seconds",
            "claim_review_count",
            "memory_hit_count",
            "corrected_claim_review_count",
            "unresolved_claim_review_count",
            "stale_memory_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "memory_hit_rate",
            "correction_rate",
            "unresolved_pressure",
            "stale_memory_pressure",
            "memory_freshness_score",
            "reviewer_alignment_score",
            "memory_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "memory_status",
            _require_status("memory_status", self.memory_status),
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
class ResearchTeamDomainClaimReviewMemoryScoreReasonCodeCount(_FinalPublicDataclass):
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            "reason count",
            self,
            ResearchTeamDomainClaimReviewMemoryScoreReasonCodeCount,
        )
        object.__setattr__(
            self,
            "reason_code",
            _require_reason_code("reason_code", self.reason_code),
        )
        object.__setattr__(
            self,
            "count",
            _require_positive_whole_decimal("count", self.count),
        )
        _require_hard_flags("reason count", self)
        _reject_unsafe_public_payload("reason count", self)


@dataclass(frozen=True)
class ResearchTeamDomainClaimReviewMemoryScoreReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    report_status: str
    input_count: Decimal
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_memory_score: Decimal
    min_memory_score: Decimal
    max_unresolved_pressure: Decimal
    oldest_memory_age_seconds: Decimal
    rows: tuple[ResearchTeamDomainClaimReviewMemoryScoreRow, ...]
    reason_code_counts: tuple[ResearchTeamDomainClaimReviewMemoryScoreReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type("report", self, ResearchTeamDomainClaimReviewMemoryScoreReport)
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
            "average_memory_score",
            "min_memory_score",
            "max_unresolved_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "oldest_memory_age_seconds",
            _require_nonnegative_decimal(
                "oldest_memory_age_seconds",
                self.oldest_memory_age_seconds,
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
    def public_payload(self) -> dict[str, Any]:
        payload = _json_ready(asdict(self))
        if type(payload) is not dict:
            raise ValueError("public payload must be a JSON object")
        validate_research_team_domain_claim_review_memory_score_public_payload(payload)
        return payload


def build_research_team_domain_claim_review_memory_score_report(
    claim_reviews: Sequence[ResearchTeamDomainClaimReviewMemoryScoreInput],
    *,
    generated_at: datetime,
    config: ResearchTeamDomainClaimReviewMemoryScoreConfig | None = None,
) -> ResearchTeamDomainClaimReviewMemoryScoreReport:
    """Build a deterministic public-safe report from sanitized claim reviews."""

    if config is None:
        config = ResearchTeamDomainClaimReviewMemoryScoreConfig()
    if type(config) is not ResearchTeamDomainClaimReviewMemoryScoreConfig:
        raise ValueError(
            "config must be a ResearchTeamDomainClaimReviewMemoryScoreConfig",
        )
    generated_at = _as_utc("generated_at", generated_at)
    normalized_reviews = _normalize_inputs(claim_reviews, generated_at=generated_at)
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
        "average_memory_score": _average_memory_score(rows),
        "min_memory_score": _min_memory_score(rows),
        "max_unresolved_pressure": _max_row_ratio(rows, "unresolved_pressure"),
        "oldest_memory_age_seconds": _oldest_memory_age_seconds(rows),
        "rows": rows,
        "reason_code_counts": _reason_code_counts(rows, reason_codes),
        "reason_codes": reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchTeamDomainClaimReviewMemoryScoreReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def research_team_domain_claim_review_memory_score_public_payload(
    value: object,
) -> dict[str, Any]:
    if type(value) is ResearchTeamDomainClaimReviewMemoryScoreReport:
        _require_hard_flags("report", value)
        payload = value.public_payload
    elif type(value) is dict:
        payload = _json_ready(value)
    else:
        raise ValueError(
            "value must be a ResearchTeamDomainClaimReviewMemoryScoreReport "
            "or JSON object",
        )
    if type(payload) is not dict:
        raise ValueError("public payload must be a JSON object")
    validate_research_team_domain_claim_review_memory_score_public_payload(payload)
    return payload


def research_team_domain_claim_review_memory_score_report_digest(value: object) -> str:
    if type(value) is ResearchTeamDomainClaimReviewMemoryScoreReport:
        return value.derived_validation_digest
    payload = research_team_domain_claim_review_memory_score_public_payload(value)
    return _digest_from_public_payload(payload)


def validate_research_team_domain_claim_review_memory_score_public_payload(
    payload: object,
) -> None:
    if type(payload) is not dict:
        raise ValueError("public payload must be a JSON object")
    _validate_payload_flags(payload, "public payload")
    _reject_unsafe_public_payload("public payload", payload)
    _validate_public_payload_shape(payload)
    supplied_digest = payload.get("derived_validation_digest")
    _require_sha256_digest("derived_validation_digest", supplied_digest)
    expected_digest = _digest_from_public_payload(payload)
    if supplied_digest != expected_digest:
        raise ValueError("derived_validation_digest must match public payload")


def _build_row(
    review: ResearchTeamDomainClaimReviewMemoryScoreInput,
    *,
    generated_at: datetime,
    config: ResearchTeamDomainClaimReviewMemoryScoreConfig,
) -> ResearchTeamDomainClaimReviewMemoryScoreRow:
    memory_age_seconds = _duration_seconds(review.memory_observed_at, generated_at)
    memory_hit_rate = _safe_ratio(review.memory_hit_count, review.claim_review_count)
    correction_rate = _safe_ratio(
        review.corrected_claim_review_count,
        review.claim_review_count,
    )
    unresolved_pressure = _safe_ratio(
        review.unresolved_claim_review_count,
        review.claim_review_count,
    )
    stale_memory_pressure = _safe_ratio(
        review.stale_memory_count,
        review.claim_review_count,
    )
    memory_freshness_score = _memory_freshness_score(
        memory_age_seconds,
        config=config,
    )
    memory_score = _memory_score(
        memory_hit_rate=memory_hit_rate,
        correction_rate=correction_rate,
        memory_freshness_score=memory_freshness_score,
        reviewer_alignment_score=review.reviewer_alignment_score,
        unresolved_pressure=unresolved_pressure,
        config=config,
    )
    reason_codes = _row_reason_codes(
        memory_age_seconds=memory_age_seconds,
        memory_hit_rate=memory_hit_rate,
        correction_rate=correction_rate,
        reviewer_alignment_score=review.reviewer_alignment_score,
        unresolved_pressure=unresolved_pressure,
        stale_memory_pressure=stale_memory_pressure,
        memory_score=memory_score,
        config=config,
    )
    return ResearchTeamDomainClaimReviewMemoryScoreRow(
        memory_rank=ONE,
        domain_key=review.domain_key,
        team_key=review.team_key,
        claim_review_digest=_private_reference_digest(review.claim_review_reference),
        reviewed_at=review.reviewed_at,
        memory_observed_at=review.memory_observed_at,
        memory_age_seconds=memory_age_seconds,
        claim_review_count=review.claim_review_count,
        memory_hit_count=review.memory_hit_count,
        memory_hit_rate=memory_hit_rate,
        corrected_claim_review_count=review.corrected_claim_review_count,
        correction_rate=correction_rate,
        unresolved_claim_review_count=review.unresolved_claim_review_count,
        unresolved_pressure=unresolved_pressure,
        stale_memory_count=review.stale_memory_count,
        stale_memory_pressure=stale_memory_pressure,
        memory_freshness_score=memory_freshness_score,
        reviewer_alignment_score=review.reviewer_alignment_score,
        memory_score=memory_score,
        memory_status=_status_for_reason_codes(reason_codes),
        reason_codes=reason_codes,
    )


def _rank_rows(
    rows: tuple[ResearchTeamDomainClaimReviewMemoryScoreRow, ...],
) -> tuple[ResearchTeamDomainClaimReviewMemoryScoreRow, ...]:
    sorted_rows = tuple(sorted(rows, key=_row_sort_key))
    return tuple(
        ResearchTeamDomainClaimReviewMemoryScoreRow(
            memory_rank=_decimal_count(index),
            domain_key=row.domain_key,
            team_key=row.team_key,
            claim_review_digest=row.claim_review_digest,
            reviewed_at=row.reviewed_at,
            memory_observed_at=row.memory_observed_at,
            memory_age_seconds=row.memory_age_seconds,
            claim_review_count=row.claim_review_count,
            memory_hit_count=row.memory_hit_count,
            memory_hit_rate=row.memory_hit_rate,
            corrected_claim_review_count=row.corrected_claim_review_count,
            correction_rate=row.correction_rate,
            unresolved_claim_review_count=row.unresolved_claim_review_count,
            unresolved_pressure=row.unresolved_pressure,
            stale_memory_count=row.stale_memory_count,
            stale_memory_pressure=row.stale_memory_pressure,
            memory_freshness_score=row.memory_freshness_score,
            reviewer_alignment_score=row.reviewer_alignment_score,
            memory_score=row.memory_score,
            memory_status=row.memory_status,
            reason_codes=row.reason_codes,
        )
        for index, row in enumerate(sorted_rows, start=1)
    )


def _row_sort_key(
    row: ResearchTeamDomainClaimReviewMemoryScoreRow,
) -> tuple[int, Decimal, str, str, str]:
    return (
        {"block": 0, "watch": 1, "pass": 2}[row.memory_status],
        row.memory_score,
        row.domain_key,
        row.team_key,
        row.claim_review_digest,
    )


def _memory_score(
    *,
    memory_hit_rate: Decimal,
    correction_rate: Decimal,
    memory_freshness_score: Decimal,
    reviewer_alignment_score: Decimal,
    unresolved_pressure: Decimal,
    config: ResearchTeamDomainClaimReviewMemoryScoreConfig,
) -> Decimal:
    return _clamp_ratio(
        memory_hit_rate * config.memory_hit_rate_weight
        + correction_rate * config.correction_rate_weight
        + memory_freshness_score * config.memory_freshness_weight
        + reviewer_alignment_score * config.reviewer_alignment_weight
        + (ONE - unresolved_pressure) * config.unresolved_resolution_weight,
    )


def _memory_freshness_score(
    memory_age_seconds: Decimal,
    *,
    config: ResearchTeamDomainClaimReviewMemoryScoreConfig,
) -> Decimal:
    return _clamp_ratio(ONE - (memory_age_seconds / config.memory_age_block_seconds))


def _row_reason_codes(
    *,
    memory_age_seconds: Decimal,
    memory_hit_rate: Decimal,
    correction_rate: Decimal,
    reviewer_alignment_score: Decimal,
    unresolved_pressure: Decimal,
    stale_memory_pressure: Decimal,
    memory_score: Decimal,
    config: ResearchTeamDomainClaimReviewMemoryScoreConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if memory_age_seconds >= config.memory_age_block_seconds:
        reason_codes.append(MEMORY_AGE_BLOCK_REASON)
    elif memory_age_seconds >= config.memory_age_watch_seconds:
        reason_codes.append(MEMORY_AGE_WATCH_REASON)

    if memory_hit_rate < config.memory_hit_rate_block_below:
        reason_codes.append(MEMORY_HIT_RATE_BLOCK_REASON)
    elif memory_hit_rate < config.memory_hit_rate_watch_below:
        reason_codes.append(MEMORY_HIT_RATE_WATCH_REASON)

    if correction_rate < config.correction_rate_block_below:
        reason_codes.append(CORRECTION_RATE_BLOCK_REASON)
    elif correction_rate < config.correction_rate_watch_below:
        reason_codes.append(CORRECTION_RATE_WATCH_REASON)

    if reviewer_alignment_score < config.reviewer_alignment_block_below:
        reason_codes.append(REVIEWER_ALIGNMENT_BLOCK_REASON)
    elif reviewer_alignment_score < config.reviewer_alignment_watch_below:
        reason_codes.append(REVIEWER_ALIGNMENT_WATCH_REASON)

    if unresolved_pressure >= config.unresolved_pressure_block_ratio:
        reason_codes.append(UNRESOLVED_PRESSURE_BLOCK_REASON)
    elif unresolved_pressure >= config.unresolved_pressure_watch_ratio:
        reason_codes.append(UNRESOLVED_PRESSURE_WATCH_REASON)

    if stale_memory_pressure >= config.stale_memory_block_ratio:
        reason_codes.append(STALE_MEMORY_PRESSURE_BLOCK_REASON)
    elif stale_memory_pressure >= config.stale_memory_watch_ratio:
        reason_codes.append(STALE_MEMORY_PRESSURE_WATCH_REASON)

    if memory_score < config.memory_score_block_threshold:
        reason_codes.append(MEMORY_SCORE_BLOCK_REASON)
    elif memory_score < config.memory_score_watch_threshold:
        reason_codes.append(MEMORY_SCORE_WATCH_REASON)

    if not reason_codes:
        reason_codes.append(PASS_REASON)
    return tuple(reason_codes)


def _report_reason_codes(
    rows: tuple[ResearchTeamDomainClaimReviewMemoryScoreRow, ...],
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


def _normalize_inputs(
    values: Sequence[ResearchTeamDomainClaimReviewMemoryScoreInput],
    *,
    generated_at: datetime,
) -> tuple[ResearchTeamDomainClaimReviewMemoryScoreInput, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("claim_reviews must be a sequence")
    try:
        items = tuple(values)
    except TypeError as exc:
        raise ValueError("claim_reviews must be a sequence") from exc
    normalized = tuple(_coerce_input(value) for value in items)
    for item in normalized:
        if item.reviewed_at > generated_at:
            raise ValueError("reviewed_at must not be after generated_at")
        if item.memory_observed_at > generated_at:
            raise ValueError("memory_observed_at must not be after generated_at")
    return tuple(
        sorted(
            normalized,
            key=lambda item: (
                item.domain_key,
                item.team_key,
                _private_reference_digest(item.claim_review_reference),
            ),
        ),
    )


def _coerce_input(value: object) -> ResearchTeamDomainClaimReviewMemoryScoreInput:
    if type(value) is ResearchTeamDomainClaimReviewMemoryScoreInput:
        _require_hard_flags("input", value)
        return value
    _require_hard_flags("input", value)
    return ResearchTeamDomainClaimReviewMemoryScoreInput(
        domain_key=_field_value(value, "domain_key"),
        team_key=_field_value(value, "team_key"),
        claim_review_reference=_field_value(value, "claim_review_reference"),
        reviewed_at=_field_value(value, "reviewed_at"),
        memory_observed_at=_field_value(value, "memory_observed_at"),
        claim_review_count=_field_value(value, "claim_review_count"),
        memory_hit_count=_field_value(value, "memory_hit_count"),
        corrected_claim_review_count=_field_value(value, "corrected_claim_review_count"),
        unresolved_claim_review_count=_field_value(
            value,
            "unresolved_claim_review_count",
        ),
        stale_memory_count=_field_value(value, "stale_memory_count"),
        reviewer_alignment_score=_field_value(value, "reviewer_alignment_score"),
        paper_only=_field_value(value, "paper_only"),
        report_only=_field_value(value, "report_only"),
        readonly=_field_value(value, "readonly"),
    )


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


def _average_memory_score(
    rows: tuple[ResearchTeamDomainClaimReviewMemoryScoreRow, ...],
) -> Decimal:
    if not rows:
        return ZERO
    return _clamp_ratio(sum((row.memory_score for row in rows), ZERO) / Decimal(len(rows)))


def _min_memory_score(
    rows: tuple[ResearchTeamDomainClaimReviewMemoryScoreRow, ...],
) -> Decimal:
    if not rows:
        return ZERO
    return _require_ratio_decimal("min_memory_score", min(row.memory_score for row in rows))


def _max_row_ratio(
    rows: tuple[ResearchTeamDomainClaimReviewMemoryScoreRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    return _require_ratio_decimal(field_name, max(getattr(row, field_name) for row in rows))


def _oldest_memory_age_seconds(
    rows: tuple[ResearchTeamDomainClaimReviewMemoryScoreRow, ...],
) -> Decimal:
    if not rows:
        return ZERO
    return _require_nonnegative_decimal(
        "oldest_memory_age_seconds",
        max(row.memory_age_seconds for row in rows),
    )


def _status_count(
    rows: tuple[ResearchTeamDomainClaimReviewMemoryScoreRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.memory_status == status))


def _reason_code_counts(
    rows: tuple[ResearchTeamDomainClaimReviewMemoryScoreRow, ...],
    report_reason_codes: tuple[str, ...],
) -> tuple[ResearchTeamDomainClaimReviewMemoryScoreReasonCodeCount, ...]:
    counts = Counter(reason_code for row in rows for reason_code in row.reason_codes)
    for reason_code in report_reason_codes:
        counts[reason_code] += 1
    return tuple(
        ResearchTeamDomainClaimReviewMemoryScoreReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(counts[reason_code]),
        )
        for reason_code in REPORT_REASON_CODES
        if counts[reason_code] > 0
    )


def _validate_config(config: ResearchTeamDomainClaimReviewMemoryScoreConfig) -> None:
    total_weight = (
        config.memory_hit_rate_weight
        + config.correction_rate_weight
        + config.memory_freshness_weight
        + config.reviewer_alignment_weight
        + config.unresolved_resolution_weight
    ).quantize(QUANT)
    if total_weight != ONE:
        raise ValueError("memory score weights must sum to 1")
    if config.memory_age_block_seconds < config.memory_age_watch_seconds:
        raise ValueError("memory_age_block_seconds must be at least watch seconds")
    for block_field, watch_field in (
        ("memory_hit_rate_block_below", "memory_hit_rate_watch_below"),
        ("correction_rate_block_below", "correction_rate_watch_below"),
        ("reviewer_alignment_block_below", "reviewer_alignment_watch_below"),
    ):
        if getattr(config, block_field) > getattr(config, watch_field):
            raise ValueError(f"{block_field} must not exceed watch threshold")
    for block_field, watch_field in (
        ("unresolved_pressure_block_ratio", "unresolved_pressure_watch_ratio"),
        ("stale_memory_block_ratio", "stale_memory_watch_ratio"),
    ):
        if getattr(config, block_field) < getattr(config, watch_field):
            raise ValueError(f"{block_field} must be at least watch ratio")
    if config.memory_score_block_threshold >= config.memory_score_watch_threshold:
        raise ValueError(
            "memory_score_block_threshold must be less than watch threshold",
        )


def _validate_input_counts(
    value: ResearchTeamDomainClaimReviewMemoryScoreInput,
) -> None:
    for field_name in (
        "memory_hit_count",
        "corrected_claim_review_count",
        "unresolved_claim_review_count",
        "stale_memory_count",
    ):
        if getattr(value, field_name) > value.claim_review_count:
            raise ValueError(f"{field_name} must not exceed claim_review_count")


def _validate_row(row: ResearchTeamDomainClaimReviewMemoryScoreRow) -> None:
    if row.memory_hit_count > row.claim_review_count:
        raise ValueError("memory_hit_count must not exceed claim_review_count")
    if row.corrected_claim_review_count > row.claim_review_count:
        raise ValueError(
            "corrected_claim_review_count must not exceed claim_review_count",
        )
    if row.unresolved_claim_review_count > row.claim_review_count:
        raise ValueError(
            "unresolved_claim_review_count must not exceed claim_review_count",
        )
    if row.stale_memory_count > row.claim_review_count:
        raise ValueError("stale_memory_count must not exceed claim_review_count")
    if row.memory_hit_rate != _safe_ratio(row.memory_hit_count, row.claim_review_count):
        raise ValueError("memory_hit_rate must match counts")
    if row.correction_rate != _safe_ratio(
        row.corrected_claim_review_count,
        row.claim_review_count,
    ):
        raise ValueError("correction_rate must match counts")
    if row.unresolved_pressure != _safe_ratio(
        row.unresolved_claim_review_count,
        row.claim_review_count,
    ):
        raise ValueError("unresolved_pressure must match counts")
    if row.stale_memory_pressure != _safe_ratio(
        row.stale_memory_count,
        row.claim_review_count,
    ):
        raise ValueError("stale_memory_pressure must match counts")
    if row.memory_status != _status_for_reason_codes(row.reason_codes):
        raise ValueError("memory_status must match reason_codes")
    if row.reason_codes != tuple(
        reason_code for reason_code in ROW_REASON_CODES if reason_code in row.reason_codes
    ):
        raise ValueError("reason_codes must use canonical reason code order")


def _validate_report(report: ResearchTeamDomainClaimReviewMemoryScoreReport) -> None:
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
    if report.average_memory_score != _average_memory_score(report.rows):
        raise ValueError("average_memory_score must match rows")
    if report.min_memory_score != _min_memory_score(report.rows):
        raise ValueError("min_memory_score must match rows")
    if report.max_unresolved_pressure != _max_row_ratio(
        report.rows,
        "unresolved_pressure",
    ):
        raise ValueError("max_unresolved_pressure must match rows")
    if report.oldest_memory_age_seconds != _oldest_memory_age_seconds(report.rows):
        raise ValueError("oldest_memory_age_seconds must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.report_status != _status_for_reason_codes(report.reason_codes):
        raise ValueError("report_status must match reason_codes")


def _normalize_rows(
    rows: tuple[ResearchTeamDomainClaimReviewMemoryScoreRow, ...],
) -> tuple[ResearchTeamDomainClaimReviewMemoryScoreRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchTeamDomainClaimReviewMemoryScoreRow:
            raise ValueError(
                "rows must contain ResearchTeamDomainClaimReviewMemoryScoreRow values",
            )
        _require_hard_flags("row", row)
    sorted_rows = tuple(sorted(rows, key=lambda row: row.memory_rank))
    if rows != sorted_rows:
        raise ValueError("rows must be sorted by memory_rank")
    return rows


def _normalize_reason_code_counts(
    counts: tuple[ResearchTeamDomainClaimReviewMemoryScoreReasonCodeCount, ...],
) -> tuple[ResearchTeamDomainClaimReviewMemoryScoreReasonCodeCount, ...]:
    if type(counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for count in counts:
        if type(count) is not ResearchTeamDomainClaimReviewMemoryScoreReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchTeamDomainClaimReviewMemoryScoreReasonCodeCount values",
            )
        _require_hard_flags("reason count", count)
    sorted_counts = tuple(
        sorted(
            counts,
            key=lambda count: REPORT_REASON_CODES.index(count.reason_code),
        ),
    )
    if counts != sorted_counts:
        raise ValueError("reason_code_counts must use canonical order")
    return counts


def _field_value(value: object, field_name: str) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            if field.name == field_name:
                return getattr(value, field_name)
    if hasattr(value, field_name):
        return getattr(value, field_name)
    raise ValueError(f"{field_name} is required")


def _json_ready(value: object) -> Any:
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("public payload Decimal value must be finite")
        return str(value)
    if type(value) is datetime:
        return _as_utc("datetime", value).isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _json_ready(getattr(value, field.name))
            for field in fields(value)
        }
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if type(value) in (str, bool) or value is None:
        return value
    raise ValueError("unsupported public payload value")


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
    return normalized.quantize(QUANT, rounding=ROUND_HALF_UP)


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized.quantize(QUANT, rounding=ROUND_HALF_UP)


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized.quantize(QUANT, rounding=ROUND_HALF_UP)


def _require_whole_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return normalized


def _require_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_whole_count_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count source must be an int")
    if value < 0:
        raise ValueError("count source must be nonnegative")
    return Decimal(value).quantize(QUANT, rounding=ROUND_HALF_UP)


def _clamp_ratio(value: Decimal) -> Decimal:
    return max(ZERO, min(ONE, value)).quantize(QUANT, rounding=ROUND_HALF_UP)


def _require_supported_config_version(value: object) -> str:
    if type(value) is not str:
        raise ValueError("config_version must be a string")
    if value != DEFAULT_RESEARCH_TEAM_DOMAIN_CLAIM_REVIEW_MEMORY_SCORE_CONFIG_VERSION:
        raise ValueError("config_version is not supported")
    _reject_unsafe_public_text("config_version", value)
    return value


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str or not PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    _reject_unsafe_public_text(field_name, value)
    return value


def _require_private_reference(field_name: str, value: object) -> str:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a nonempty private reference")
    return value


def _require_reason_code(field_name: str, value: object) -> str:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a reason code")
    allowed = "abcdefghijklmnopqrstuvwxyz0123456789_"
    if any(character not in allowed for character in value):
        raise ValueError(f"{field_name} must contain deterministic code text")
    _reject_unsafe_public_text(field_name, value)
    return value


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in PUBLIC_STATUSES:
        raise ValueError(f"{field_name} must be one of {PUBLIC_STATUSES}")
    return value


def _normalize_reason_codes(
    values: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    normalized = tuple(_require_reason_code("reason_codes", value) for value in values)
    if not normalized:
        raise ValueError("reason_codes must be nonempty")
    if len(set(normalized)) != len(normalized):
        raise ValueError("reason_codes must be unique")
    if any(value not in allowed for value in normalized):
        raise ValueError("reason_codes must be known")
    return normalized


def _require_exact_type(name: str, value: object, expected_type: type[object]) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{name} must be exactly {expected_type.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if _field_value(value, field_name) is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _validate_payload_flags(payload: dict[str, Any], label: str) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload.get(field_name) is not True:
            raise ValueError(f"{label} {field_name} must be True")


REPORT_PUBLIC_PAYLOAD_KEYS = frozenset(
    (
        "generated_at",
        "config_version",
        "report_status",
        "input_count",
        "row_count",
        "pass_count",
        "watch_count",
        "block_count",
        "average_memory_score",
        "min_memory_score",
        "max_unresolved_pressure",
        "oldest_memory_age_seconds",
        "rows",
        "reason_code_counts",
        "reason_codes",
        "derived_validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
ROW_PUBLIC_PAYLOAD_KEYS = frozenset(
    (
        "memory_rank",
        "domain_key",
        "team_key",
        "claim_review_digest",
        "reviewed_at",
        "memory_observed_at",
        "memory_age_seconds",
        "claim_review_count",
        "memory_hit_count",
        "memory_hit_rate",
        "corrected_claim_review_count",
        "correction_rate",
        "unresolved_claim_review_count",
        "unresolved_pressure",
        "stale_memory_count",
        "stale_memory_pressure",
        "memory_freshness_score",
        "reviewer_alignment_score",
        "memory_score",
        "memory_status",
        "reason_codes",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
REASON_COUNT_PUBLIC_PAYLOAD_KEYS = frozenset(
    (
        "reason_code",
        "count",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
REPORT_COUNT_FIELDS = frozenset(
    (
        "input_count",
        "row_count",
        "pass_count",
        "watch_count",
        "block_count",
    ),
)
REPORT_RATIO_FIELDS = frozenset(
    (
        "average_memory_score",
        "min_memory_score",
        "max_unresolved_pressure",
    ),
)
ROW_COUNT_FIELDS = frozenset(
    (
        "claim_review_count",
        "memory_hit_count",
        "corrected_claim_review_count",
        "unresolved_claim_review_count",
        "stale_memory_count",
    ),
)
ROW_RATIO_FIELDS = frozenset(
    (
        "memory_hit_rate",
        "correction_rate",
        "unresolved_pressure",
        "stale_memory_pressure",
        "memory_freshness_score",
        "reviewer_alignment_score",
        "memory_score",
    ),
)


def _validate_public_payload_shape(payload: dict[str, Any]) -> None:
    if set(payload) != REPORT_PUBLIC_PAYLOAD_KEYS:
        raise ValueError("public payload keys must match report schema")
    _require_public_payload_datetime("generated_at", payload["generated_at"])
    _require_supported_config_version(payload["config_version"])
    _require_status("report_status", payload["report_status"])
    for field_name in REPORT_COUNT_FIELDS:
        _require_public_payload_decimal_text(
            field_name,
            payload[field_name],
            whole=True,
        )
    for field_name in REPORT_RATIO_FIELDS:
        _require_public_payload_decimal_text(
            field_name,
            payload[field_name],
            ratio=True,
        )
    _require_public_payload_decimal_text(
        "oldest_memory_age_seconds",
        payload["oldest_memory_age_seconds"],
    )
    _validate_public_payload_rows(payload["rows"])
    _validate_public_payload_reason_code_counts(payload["reason_code_counts"])
    _validate_public_payload_reason_codes(
        "reason_codes",
        payload["reason_codes"],
        REPORT_REASON_CODES,
    )


def _validate_public_payload_rows(value: object) -> None:
    if type(value) is not list:
        raise ValueError("rows must be a public payload list")
    for row in value:
        if type(row) is not dict:
            raise ValueError("rows must contain public payload objects")
        if set(row) != ROW_PUBLIC_PAYLOAD_KEYS:
            raise ValueError("row public payload keys must match row schema")
        _validate_payload_flags(row, "row public payload")
        _require_public_payload_decimal_text("memory_rank", row["memory_rank"])
        _require_public_identifier("domain_key", row["domain_key"])
        _require_public_identifier("team_key", row["team_key"])
        _require_sha256_digest("claim_review_digest", row["claim_review_digest"])
        _require_public_payload_datetime("reviewed_at", row["reviewed_at"])
        _require_public_payload_datetime(
            "memory_observed_at",
            row["memory_observed_at"],
        )
        _require_public_payload_decimal_text(
            "memory_age_seconds",
            row["memory_age_seconds"],
        )
        for field_name in ROW_COUNT_FIELDS:
            _require_public_payload_decimal_text(
                field_name,
                row[field_name],
                whole=True,
            )
        for field_name in ROW_RATIO_FIELDS:
            _require_public_payload_decimal_text(
                field_name,
                row[field_name],
                ratio=True,
            )
        _require_status("memory_status", row["memory_status"])
        _validate_public_payload_reason_codes(
            "row reason_codes",
            row["reason_codes"],
            ROW_REASON_CODES,
        )


def _validate_public_payload_reason_code_counts(value: object) -> None:
    if type(value) is not list:
        raise ValueError("reason_code_counts must be a public payload list")
    for item in value:
        if type(item) is not dict:
            raise ValueError("reason_code_counts must contain public payload objects")
        if set(item) != REASON_COUNT_PUBLIC_PAYLOAD_KEYS:
            raise ValueError(
                "reason_code_count public payload keys must match count schema",
            )
        _validate_payload_flags(item, "reason_code_count public payload")
        _require_reason_code("reason_code", item["reason_code"])
        if item["reason_code"] not in REPORT_REASON_CODES:
            raise ValueError("reason_code must be known")
        _require_public_payload_decimal_text("count", item["count"], whole=True)


def _validate_public_payload_reason_codes(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> None:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a public payload list")
    normalized = tuple(_require_reason_code(field_name, item) for item in value)
    if not normalized:
        raise ValueError(f"{field_name} must be nonempty")
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} must be unique")
    if any(item not in allowed for item in normalized):
        raise ValueError(f"{field_name} must be known")


def _require_public_payload_datetime(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be an ISO datetime string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be an ISO datetime string") from exc
    if _as_utc(field_name, parsed).isoformat() != value:
        raise ValueError(f"{field_name} must be canonical UTC ISO datetime")
    return value


def _require_public_payload_decimal_text(
    field_name: str,
    value: object,
    *,
    ratio: bool = False,
    whole: bool = False,
) -> Decimal:
    if type(value) is not str or DECIMAL_TEXT_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be canonical Decimal text")
    parsed = _require_decimal(field_name, Decimal(value))
    if ratio and (parsed < ZERO or parsed > ONE):
        raise ValueError(f"{field_name} must be between 0 and 1")
    if whole and parsed != parsed.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return parsed


def _private_reference_digest(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str or DIGEST_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a SHA-256 digest")
    return value


def _report_values_without_digest(
    report: ResearchTeamDomainClaimReviewMemoryScoreReport,
) -> dict[str, object]:
    values = asdict(report)
    values.pop("derived_validation_digest")
    return values


def _report_digest_from_values(values: dict[str, object]) -> str:
    payload = _json_ready(values)
    if type(payload) is not dict:
        raise ValueError("digest payload must be a JSON object")
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _digest_from_public_payload(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest", None)
    return _report_digest_from_values(unsigned)


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value))
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            _reject_unsafe_public_text(f"{label} key", key)
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(value, (tuple, list)):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(value, str):
        _reject_unsafe_public_text(label, value)


def _reject_unsafe_public_text(label: str, value: str) -> None:
    lowered = value.casefold()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"unsafe public payload surface in {label}")
