"""Pure report-only source-claim verification priority queue report.

The module ranks caller-supplied source-claim verification observations for
analyst review. It performs no network access, scraping, persistence,
execution, recommendation, sizing, auth, or mutation work.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
from hashlib import sha256
import json
import re
from typing import Any


DEFAULT_RESEARCH_SOURCE_CLAIM_VERIFICATION_PRIORITY_QUEUE_CONFIG_VERSION = (
    "research-source-claim-verification-priority-queue-report-v0"
)

QUEUE_STATUSES = ("pass", "watch", "block")
PASS_REASON_CODE = "source_claim_verification_priority_pass"
DERIVED_VALIDATION_DIGEST_FIELD = "derived_validation_digest"
PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
QUANTUM = Decimal("0.000001")
MICROSECOND_DIVISOR = Decimal("1000000")

PUBLIC_LABEL_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
DOMAIN_LIKE_RE = re.compile(
    r"(?:^|[._-])[a-z0-9-]+\."
    r"(?:ai|app|co|com|dev|edu|gov|io|net|org|test|xyz)"
    r"(?:$|[._-])",
)
RAW_PUBLIC_ID_RE = re.compile(
    r"(?:^|[._-])0x[0-9a-f]{8,}(?:$|[._-])"
    r"|(?:^|[._-])[0-9a-f]{8}-[0-9a-f]{4}-"
    r"[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}(?:$|[._-])",
)
BARE_RAW_ID_RE = re.compile(r"(?:^|[._-])(?:\d{18,}|[0-9a-f]{32,})(?:$|[._-])")
QUESTION_SLUG_RE = re.compile(
    r"(?:^|[._-])(?:can|could|did|do|does|how|is|may|might|shall|should|"
    r"was|were|what|when|where|which|who|why|will|would)(?:[._-][a-z0-9]+){2,}"
    r"(?:$|[._-])",
)

SAFE_REASON_CODES = (
    "freshness_watch",
    "freshness_block",
    "authority_watch",
    "authority_block",
    "contradiction_watch",
    "contradiction_block",
    "extraction_confidence_watch",
    "extraction_confidence_block",
    "corroboration_gap_watch",
    "corroboration_gap_block",
    "deadline_proximity_watch",
    "deadline_proximity_block",
    "claim_verification_priority_watch",
    "claim_verification_priority_block",
    PASS_REASON_CODE,
)

UNSAFE_KEY_FRAGMENTS = (
    "candidate_id",
    "condition_id",
    "market_id",
    "market_slug",
    "slug",
    "question",
    "url",
    "source_text",
    "raw_text",
    "raw",
    "dsn",
    "table",
    "token",
    "wallet",
    "order",
    "trade",
    "live",
    "private_key",
    "api_key",
)
UNSAFE_VALUE_FRAGMENTS = (
    "://",
    "www.",
    "candidate_id",
    "condition_id",
    "market_id",
    "market_slug",
    "slug",
    "question",
    "url",
    "source_text",
    "raw_text",
    "raw",
    "dsn",
    "table",
    "token",
    "wallet",
    "order",
    "trade",
    "live",
    "private_key",
    "api_key",
    "secret",
    "credential",
    "database",
    "network",
    "persist",
    "signing",
    "mutation",
    "buy",
    "sell",
)

PUBLIC_ROW_PAYLOAD_FIELDS_WITHOUT_DIGEST = (
    "config_version",
    "priority_rank",
    "claim_label",
    "source_family_label",
    "resolution_bucket",
    "source_observed_at",
    "resolution_deadline_at",
    "source_age_seconds",
    "source_authority_score",
    "freshness_score",
    "contradiction_severity",
    "extraction_confidence_score",
    "extraction_uncertainty_score",
    "corroborating_source_count",
    "required_corroborating_source_count",
    "corroboration_gap_score",
    "deadline_seconds",
    "deadline_proximity_score",
    "verification_priority_score",
    "verification_status",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)
PUBLIC_ROW_PAYLOAD_FIELDS = (
    *PUBLIC_ROW_PAYLOAD_FIELDS_WITHOUT_DIGEST,
    DERIVED_VALIDATION_DIGEST_FIELD,
)
PUBLIC_REPORT_PAYLOAD_FIELDS_WITHOUT_DIGEST = (
    "config_version",
    "generated_at",
    "status",
    "claim_count",
    "pass_count",
    "watch_count",
    "block_count",
    "average_verification_priority_score",
    "max_verification_priority_score",
    "average_source_authority_score",
    "average_freshness_score",
    "average_contradiction_severity",
    "average_extraction_confidence_score",
    "average_corroboration_gap_score",
    "average_deadline_proximity_score",
    "reason_codes",
    "rows",
    "paper_only",
    "report_only",
    "readonly",
)
PUBLIC_REPORT_PAYLOAD_FIELDS = (
    *PUBLIC_REPORT_PAYLOAD_FIELDS_WITHOUT_DIGEST,
    DERIVED_VALIDATION_DIGEST_FIELD,
)


__all__ = (
    "DEFAULT_RESEARCH_SOURCE_CLAIM_VERIFICATION_PRIORITY_QUEUE_CONFIG_VERSION",
    "QUEUE_STATUSES",
    "ResearchSourceClaimVerificationPriorityQueueConfig",
    "ResearchSourceClaimVerificationPriorityQueueObservation",
    "ResearchSourceClaimVerificationPriorityQueueReport",
    "ResearchSourceClaimVerificationPriorityQueueRow",
    "build_research_source_claim_verification_priority_queue_report",
    "research_source_claim_verification_priority_queue_report_digest",
    "research_source_claim_verification_priority_queue_report_payload",
    "validate_research_source_claim_verification_priority_queue_public_payload",
)


@dataclass(frozen=True)
class ResearchSourceClaimVerificationPriorityQueueConfig:
    config_version: str = (
        DEFAULT_RESEARCH_SOURCE_CLAIM_VERIFICATION_PRIORITY_QUEUE_CONFIG_VERSION
    )
    max_source_age_seconds: Decimal = Decimal("86400.000000")
    deadline_priority_window_seconds: Decimal = Decimal("172800.000000")
    component_watch_threshold: Decimal = Decimal("0.500000")
    component_block_threshold: Decimal = Decimal("0.800000")
    priority_watch_threshold: Decimal = Decimal("0.350000")
    priority_block_threshold: Decimal = Decimal("0.700000")
    authority_weight: Decimal = Decimal("0.180000")
    freshness_weight: Decimal = Decimal("0.160000")
    contradiction_weight: Decimal = Decimal("0.240000")
    extraction_confidence_weight: Decimal = Decimal("0.120000")
    corroboration_gap_weight: Decimal = Decimal("0.160000")
    deadline_proximity_weight: Decimal = Decimal("0.140000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchSourceClaimVerificationPriorityQueueConfig "
            "does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("config", self, ResearchSourceClaimVerificationPriorityQueueConfig)
        _require_public_label("config_version", self.config_version)
        for field_name in (
            "max_source_age_seconds",
            "deadline_priority_window_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "component_watch_threshold",
            "component_block_threshold",
            "priority_watch_threshold",
            "priority_block_threshold",
            "authority_weight",
            "freshness_weight",
            "contradiction_weight",
            "extraction_confidence_weight",
            "corroboration_gap_weight",
            "deadline_proximity_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        if self.component_block_threshold <= self.component_watch_threshold:
            raise ValueError(
                "component_block_threshold must exceed component_watch_threshold",
            )
        if self.priority_block_threshold <= self.priority_watch_threshold:
            raise ValueError("priority_block_threshold must exceed priority_watch_threshold")
        _require_weight_sum(self)
        _reject_unsafe_public_payload("config", self)
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchSourceClaimVerificationPriorityQueueObservation:
    claim_label: str
    source_family_label: str
    resolution_bucket: str
    source_observed_at: datetime
    resolution_deadline_at: datetime
    source_authority_score: Decimal
    extraction_confidence_score: Decimal
    contradiction_severity: Decimal
    corroborating_source_count: Decimal
    required_corroborating_source_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchSourceClaimVerificationPriorityQueueObservation "
            "does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            "observation",
            self,
            ResearchSourceClaimVerificationPriorityQueueObservation,
        )
        for field_name in ("claim_label", "source_family_label", "resolution_bucket"):
            _require_public_label(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "source_observed_at",
            _as_utc("source_observed_at", self.source_observed_at),
        )
        object.__setattr__(
            self,
            "resolution_deadline_at",
            _as_utc("resolution_deadline_at", self.resolution_deadline_at),
        )
        for field_name in (
            "source_authority_score",
            "extraction_confidence_score",
            "contradiction_severity",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "corroborating_source_count",
            _normalize_nonnegative_whole_decimal(
                "corroborating_source_count",
                self.corroborating_source_count,
            ),
        )
        object.__setattr__(
            self,
            "required_corroborating_source_count",
            _normalize_positive_whole_decimal(
                "required_corroborating_source_count",
                self.required_corroborating_source_count,
            ),
        )
        if self.corroborating_source_count > self.required_corroborating_source_count:
            raise ValueError(
                "corroborating_source_count must not exceed "
                "required_corroborating_source_count",
            )
        _reject_unsafe_public_payload("observation", self)
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class ResearchSourceClaimVerificationPriorityQueueRow:
    config_version: str
    priority_rank: Decimal
    claim_label: str
    source_family_label: str
    resolution_bucket: str
    source_observed_at: datetime
    resolution_deadline_at: datetime
    source_age_seconds: Decimal
    source_authority_score: Decimal
    freshness_score: Decimal
    contradiction_severity: Decimal
    extraction_confidence_score: Decimal
    extraction_uncertainty_score: Decimal
    corroborating_source_count: Decimal
    required_corroborating_source_count: Decimal
    corroboration_gap_score: Decimal
    deadline_seconds: Decimal
    deadline_proximity_score: Decimal
    verification_priority_score: Decimal
    verification_status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchSourceClaimVerificationPriorityQueueRow "
            "does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("row", self, ResearchSourceClaimVerificationPriorityQueueRow)
        for field_name in (
            "config_version",
            "claim_label",
            "source_family_label",
            "resolution_bucket",
        ):
            _require_public_label(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "source_observed_at",
            _as_utc("source_observed_at", self.source_observed_at),
        )
        object.__setattr__(
            self,
            "resolution_deadline_at",
            _as_utc("resolution_deadline_at", self.resolution_deadline_at),
        )
        for field_name in ("priority_rank", "source_age_seconds", "deadline_seconds"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "source_authority_score",
            "freshness_score",
            "contradiction_severity",
            "extraction_confidence_score",
            "extraction_uncertainty_score",
            "corroboration_gap_score",
            "deadline_proximity_score",
            "verification_priority_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "corroborating_source_count",
            "required_corroborating_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        if self.required_corroborating_source_count <= ZERO:
            raise ValueError("required_corroborating_source_count must be positive")
        _require_status("verification_status", self.verification_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _reject_unsafe_public_payload("row", self)
        _require_hard_flags("row", self)
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                DERIVED_VALIDATION_DIGEST_FIELD,
                _row_derived_validation_digest(self),
            )
        else:
            object.__setattr__(
                self,
                DERIVED_VALIDATION_DIGEST_FIELD,
                _require_sha256_digest(
                    DERIVED_VALIDATION_DIGEST_FIELD,
                    self.derived_validation_digest,
                ),
            )
        _validate_row_consistency(self)
        _validate_row_derived_validation_digest(self)


@dataclass(frozen=True)
class ResearchSourceClaimVerificationPriorityQueueReport:
    config_version: str
    generated_at: datetime
    status: str
    claim_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_verification_priority_score: Decimal
    max_verification_priority_score: Decimal
    average_source_authority_score: Decimal
    average_freshness_score: Decimal
    average_contradiction_severity: Decimal
    average_extraction_confidence_score: Decimal
    average_corroboration_gap_score: Decimal
    average_deadline_proximity_score: Decimal
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchSourceClaimVerificationPriorityQueueRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchSourceClaimVerificationPriorityQueueReport "
            "does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("report", self, ResearchSourceClaimVerificationPriorityQueueReport)
        _require_public_label("config_version", self.config_version)
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_status("status", self.status)
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        for field_name in ("claim_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_verification_priority_score",
            "max_verification_priority_score",
            "average_source_authority_score",
            "average_freshness_score",
            "average_contradiction_severity",
            "average_extraction_confidence_score",
            "average_corroboration_gap_score",
            "average_deadline_proximity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _reject_unsafe_public_payload("report", self)
        _require_hard_flags("report", self)
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                DERIVED_VALIDATION_DIGEST_FIELD,
                _report_derived_validation_digest(self),
            )
        else:
            object.__setattr__(
                self,
                DERIVED_VALIDATION_DIGEST_FIELD,
                _require_sha256_digest(
                    DERIVED_VALIDATION_DIGEST_FIELD,
                    self.derived_validation_digest,
                ),
            )
        _validate_report_consistency(self)
        _validate_report_derived_validation_digest(self)

    @property
    def payload(self) -> dict[str, object]:
        return research_source_claim_verification_priority_queue_report_payload(self)


def build_research_source_claim_verification_priority_queue_report(
    observations: Iterable[object],
    *,
    generated_at: datetime,
    config: ResearchSourceClaimVerificationPriorityQueueConfig | None = None,
) -> ResearchSourceClaimVerificationPriorityQueueReport:
    """Build a deterministic local queue report for claim verification."""

    if config is None:
        config = ResearchSourceClaimVerificationPriorityQueueConfig()
    _require_exact_type("config", config, ResearchSourceClaimVerificationPriorityQueueConfig)
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_observations = _normalize_observations(observations)
    _reject_invalid_observation_timing(normalized_observations, generated_at_utc)

    ranked_metrics = tuple(
        sorted(
            (
                _metrics_from_observation(
                    observation,
                    generated_at=generated_at_utc,
                    config=config,
                )
                for observation in normalized_observations
            ),
            key=_metrics_sort_key,
        ),
    )
    rows = tuple(
        ResearchSourceClaimVerificationPriorityQueueRow(
            priority_rank=_count(index),
            **metrics,
        )
        for index, metrics in enumerate(ranked_metrics, start=1)
    )
    return ResearchSourceClaimVerificationPriorityQueueReport(
        config_version=config.config_version,
        generated_at=generated_at_utc,
        status=_report_status(rows),
        claim_count=_count(len(normalized_observations)),
        pass_count=_row_status_count(rows, "pass"),
        watch_count=_row_status_count(rows, "watch"),
        block_count=_row_status_count(rows, "block"),
        average_verification_priority_score=_average(
            tuple(row.verification_priority_score for row in rows),
        ),
        max_verification_priority_score=_max_decimal(
            tuple(row.verification_priority_score for row in rows),
        ),
        average_source_authority_score=_average(
            tuple(row.source_authority_score for row in rows),
        ),
        average_freshness_score=_average(tuple(row.freshness_score for row in rows)),
        average_contradiction_severity=_average(
            tuple(row.contradiction_severity for row in rows),
        ),
        average_extraction_confidence_score=_average(
            tuple(row.extraction_confidence_score for row in rows),
        ),
        average_corroboration_gap_score=_average(
            tuple(row.corroboration_gap_score for row in rows),
        ),
        average_deadline_proximity_score=_average(
            tuple(row.deadline_proximity_score for row in rows),
        ),
        reason_codes=_report_reason_codes(rows),
        rows=rows,
    )


def research_source_claim_verification_priority_queue_report_payload(
    report: ResearchSourceClaimVerificationPriorityQueueReport | dict[str, object],
) -> dict[str, object]:
    if type(report) is ResearchSourceClaimVerificationPriorityQueueReport:
        _require_hard_flags("report", report)
        _reject_unsafe_public_payload("report", report)
        _validate_report_derived_validation_digest(report)
        payload = _report_public_payload_without_digest(report)
        payload[DERIVED_VALIDATION_DIGEST_FIELD] = report.derived_validation_digest
        return payload
    if type(report) is dict:
        _reject_unsafe_public_payload("payload", report)
        _validate_public_report_payload(report)
        return dict(report)
    raise ValueError(
        "report must be a ResearchSourceClaimVerificationPriorityQueueReport",
    )


def research_source_claim_verification_priority_queue_report_digest(
    report: ResearchSourceClaimVerificationPriorityQueueReport,
) -> str:
    if type(report) is not ResearchSourceClaimVerificationPriorityQueueReport:
        raise ValueError(
            "report must be a ResearchSourceClaimVerificationPriorityQueueReport",
        )
    _require_hard_flags("report", report)
    _validate_report_derived_validation_digest(report)
    return report.derived_validation_digest


def validate_research_source_claim_verification_priority_queue_public_payload(
    payload: object,
) -> bool:
    try:
        if type(payload) is not dict:
            return False
        _reject_unsafe_public_payload("payload", payload)
        _validate_public_report_payload(payload)
        return True
    except (TypeError, ValueError):
        return False


def _metrics_from_observation(
    observation: ResearchSourceClaimVerificationPriorityQueueObservation,
    *,
    generated_at: datetime,
    config: ResearchSourceClaimVerificationPriorityQueueConfig,
) -> dict[str, Any]:
    source_age_seconds = _datetime_delta_seconds(generated_at, observation.source_observed_at)
    deadline_seconds = _datetime_delta_seconds(
        observation.resolution_deadline_at,
        generated_at,
    )
    freshness_score = _cap_probability(
        _ratio_raw(source_age_seconds, config.max_source_age_seconds),
    )
    extraction_uncertainty_score = _cap_probability(
        ONE - observation.extraction_confidence_score,
    )
    corroboration_gap_score = _cap_probability(
        ONE
        - _ratio_raw(
            observation.corroborating_source_count,
            observation.required_corroborating_source_count,
        ),
    )
    deadline_proximity_score = _cap_probability(
        ONE - _ratio_raw(deadline_seconds, config.deadline_priority_window_seconds),
    )
    verification_priority_score = _weighted_verification_priority_score(
        source_authority_score=observation.source_authority_score,
        freshness_score=freshness_score,
        contradiction_severity=observation.contradiction_severity,
        extraction_uncertainty_score=extraction_uncertainty_score,
        corroboration_gap_score=corroboration_gap_score,
        deadline_proximity_score=deadline_proximity_score,
        config=config,
    )
    verification_status = _verification_status(
        verification_priority_score,
        component_values=(
            observation.source_authority_score,
            freshness_score,
            observation.contradiction_severity,
            extraction_uncertainty_score,
            corroboration_gap_score,
            deadline_proximity_score,
        ),
        config=config,
    )
    return {
        "config_version": config.config_version,
        "claim_label": observation.claim_label,
        "source_family_label": observation.source_family_label,
        "resolution_bucket": observation.resolution_bucket,
        "source_observed_at": observation.source_observed_at,
        "resolution_deadline_at": observation.resolution_deadline_at,
        "source_age_seconds": source_age_seconds,
        "source_authority_score": observation.source_authority_score,
        "freshness_score": freshness_score,
        "contradiction_severity": observation.contradiction_severity,
        "extraction_confidence_score": observation.extraction_confidence_score,
        "extraction_uncertainty_score": extraction_uncertainty_score,
        "corroborating_source_count": observation.corroborating_source_count,
        "required_corroborating_source_count": (
            observation.required_corroborating_source_count
        ),
        "corroboration_gap_score": corroboration_gap_score,
        "deadline_seconds": deadline_seconds,
        "deadline_proximity_score": deadline_proximity_score,
        "verification_priority_score": verification_priority_score,
        "verification_status": verification_status,
        "reason_codes": _row_reason_codes(
            source_authority_score=observation.source_authority_score,
            freshness_score=freshness_score,
            contradiction_severity=observation.contradiction_severity,
            extraction_uncertainty_score=extraction_uncertainty_score,
            corroboration_gap_score=corroboration_gap_score,
            deadline_proximity_score=deadline_proximity_score,
            verification_priority_score=verification_priority_score,
            verification_status=verification_status,
            config=config,
        ),
    }


def _weighted_verification_priority_score(
    *,
    source_authority_score: Decimal,
    freshness_score: Decimal,
    contradiction_severity: Decimal,
    extraction_uncertainty_score: Decimal,
    corroboration_gap_score: Decimal,
    deadline_proximity_score: Decimal,
    config: ResearchSourceClaimVerificationPriorityQueueConfig,
) -> Decimal:
    return _cap_probability(
        (source_authority_score * config.authority_weight)
        + (freshness_score * config.freshness_weight)
        + (contradiction_severity * config.contradiction_weight)
        + (extraction_uncertainty_score * config.extraction_confidence_weight)
        + (corroboration_gap_score * config.corroboration_gap_weight)
        + (deadline_proximity_score * config.deadline_proximity_weight),
    )


def _row_reason_codes(
    *,
    source_authority_score: Decimal,
    freshness_score: Decimal,
    contradiction_severity: Decimal,
    extraction_uncertainty_score: Decimal,
    corroboration_gap_score: Decimal,
    deadline_proximity_score: Decimal,
    verification_priority_score: Decimal,
    verification_status: str,
    config: ResearchSourceClaimVerificationPriorityQueueConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    _append_component_reason(reason_codes, "authority", source_authority_score, config)
    _append_component_reason(reason_codes, "freshness", freshness_score, config)
    _append_component_reason(
        reason_codes,
        "contradiction",
        contradiction_severity,
        config,
    )
    _append_component_reason(
        reason_codes,
        "extraction_confidence",
        extraction_uncertainty_score,
        config,
    )
    _append_component_reason(
        reason_codes,
        "corroboration_gap",
        corroboration_gap_score,
        config,
    )
    _append_component_reason(
        reason_codes,
        "deadline_proximity",
        deadline_proximity_score,
        config,
    )
    if verification_priority_score >= config.priority_block_threshold:
        reason_codes.append("claim_verification_priority_block")
    elif verification_priority_score >= config.priority_watch_threshold:
        reason_codes.append("claim_verification_priority_watch")
    if not reason_codes:
        reason_codes.append(PASS_REASON_CODE)
    if verification_status == "pass" and reason_codes != [PASS_REASON_CODE]:
        raise ValueError("pass rows must only use pass reason code")
    return _normalize_reason_codes("reason_codes", tuple(reason_codes))


def _append_component_reason(
    reason_codes: list[str],
    component_name: str,
    component_value: Decimal,
    config: ResearchSourceClaimVerificationPriorityQueueConfig,
) -> None:
    if component_value >= config.component_block_threshold:
        reason_codes.append(f"{component_name}_block")
    elif component_value >= config.component_watch_threshold:
        reason_codes.append(f"{component_name}_watch")


def _verification_status(
    verification_priority_score: Decimal,
    *,
    component_values: tuple[Decimal, ...],
    config: ResearchSourceClaimVerificationPriorityQueueConfig,
) -> str:
    if (
        verification_priority_score >= config.priority_block_threshold
        or any(value >= config.component_block_threshold for value in component_values)
    ):
        return "block"
    if (
        verification_priority_score >= config.priority_watch_threshold
        or any(value >= config.component_watch_threshold for value in component_values)
    ):
        return "watch"
    return "pass"


def _report_status(
    rows: tuple[ResearchSourceClaimVerificationPriorityQueueRow, ...],
) -> str:
    if any(row.verification_status == "block" for row in rows):
        return "block"
    if any(row.verification_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchSourceClaimVerificationPriorityQueueRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (PASS_REASON_CODE,)
    reason_codes: list[str] = []
    for row in rows:
        reason_codes.extend(row.reason_codes)
    return _normalize_reason_codes("reason_codes", tuple(reason_codes))


def _row_status_count(
    rows: tuple[ResearchSourceClaimVerificationPriorityQueueRow, ...],
    status: str,
) -> Decimal:
    _require_status("status", status)
    return _count(sum(1 for row in rows if row.verification_status == status))


def _metrics_sort_key(metrics: dict[str, Any]) -> tuple[Decimal, Decimal, str]:
    return (
        -metrics["verification_priority_score"],
        -metrics["contradiction_severity"],
        metrics["claim_label"],
    )


def _row_sort_key(
    row: ResearchSourceClaimVerificationPriorityQueueRow,
) -> tuple[Decimal, Decimal, str]:
    return (
        -row.verification_priority_score,
        -row.contradiction_severity,
        row.claim_label,
    )


def _report_public_payload_without_digest(
    report: ResearchSourceClaimVerificationPriorityQueueReport,
) -> dict[str, object]:
    return {
        "config_version": report.config_version,
        "generated_at": _datetime_payload(report.generated_at),
        "status": report.status,
        "claim_count": _decimal_payload(report.claim_count),
        "pass_count": _decimal_payload(report.pass_count),
        "watch_count": _decimal_payload(report.watch_count),
        "block_count": _decimal_payload(report.block_count),
        "average_verification_priority_score": _decimal_payload(
            report.average_verification_priority_score,
        ),
        "max_verification_priority_score": _decimal_payload(
            report.max_verification_priority_score,
        ),
        "average_source_authority_score": _decimal_payload(
            report.average_source_authority_score,
        ),
        "average_freshness_score": _decimal_payload(report.average_freshness_score),
        "average_contradiction_severity": _decimal_payload(
            report.average_contradiction_severity,
        ),
        "average_extraction_confidence_score": _decimal_payload(
            report.average_extraction_confidence_score,
        ),
        "average_corroboration_gap_score": _decimal_payload(
            report.average_corroboration_gap_score,
        ),
        "average_deadline_proximity_score": _decimal_payload(
            report.average_deadline_proximity_score,
        ),
        "reason_codes": list(report.reason_codes),
        "rows": [_row_public_payload(row) for row in report.rows],
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _row_public_payload(
    row: ResearchSourceClaimVerificationPriorityQueueRow,
) -> dict[str, object]:
    _validate_row_derived_validation_digest(row)
    payload = _row_public_payload_without_digest(row)
    payload[DERIVED_VALIDATION_DIGEST_FIELD] = row.derived_validation_digest
    return payload


def _row_public_payload_without_digest(
    row: ResearchSourceClaimVerificationPriorityQueueRow,
) -> dict[str, object]:
    return {
        "config_version": row.config_version,
        "priority_rank": _decimal_payload(row.priority_rank),
        "claim_label": row.claim_label,
        "source_family_label": row.source_family_label,
        "resolution_bucket": row.resolution_bucket,
        "source_observed_at": _datetime_payload(row.source_observed_at),
        "resolution_deadline_at": _datetime_payload(row.resolution_deadline_at),
        "source_age_seconds": _decimal_payload(row.source_age_seconds),
        "source_authority_score": _decimal_payload(row.source_authority_score),
        "freshness_score": _decimal_payload(row.freshness_score),
        "contradiction_severity": _decimal_payload(row.contradiction_severity),
        "extraction_confidence_score": _decimal_payload(
            row.extraction_confidence_score,
        ),
        "extraction_uncertainty_score": _decimal_payload(
            row.extraction_uncertainty_score,
        ),
        "corroborating_source_count": _decimal_payload(row.corroborating_source_count),
        "required_corroborating_source_count": _decimal_payload(
            row.required_corroborating_source_count,
        ),
        "corroboration_gap_score": _decimal_payload(row.corroboration_gap_score),
        "deadline_seconds": _decimal_payload(row.deadline_seconds),
        "deadline_proximity_score": _decimal_payload(row.deadline_proximity_score),
        "verification_priority_score": _decimal_payload(
            row.verification_priority_score,
        ),
        "verification_status": row.verification_status,
        "reason_codes": list(row.reason_codes),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _row_derived_validation_digest(
    row: ResearchSourceClaimVerificationPriorityQueueRow,
) -> str:
    return _derived_validation_digest(
        "research_source_claim_verification_priority_queue_report_row",
        _row_public_payload_without_digest(row),
        PUBLIC_ROW_PAYLOAD_FIELDS_WITHOUT_DIGEST,
    )


def _report_derived_validation_digest(
    report: ResearchSourceClaimVerificationPriorityQueueReport,
) -> str:
    return _derived_validation_digest(
        "research_source_claim_verification_priority_queue_report",
        _report_public_payload_without_digest(report),
        PUBLIC_REPORT_PAYLOAD_FIELDS_WITHOUT_DIGEST,
    )


def _derived_validation_digest(
    label: str,
    payload: dict[str, object],
    field_names: tuple[str, ...],
) -> str:
    canonical = json.dumps(
        {field_name: payload[field_name] for field_name in field_names},
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return sha256(f"{label}|{canonical}".encode("utf-8")).hexdigest()


def _validate_row_derived_validation_digest(
    row: ResearchSourceClaimVerificationPriorityQueueRow,
) -> None:
    if row.derived_validation_digest != _row_derived_validation_digest(row):
        raise ValueError("derived_validation_digest must match row fields")


def _validate_report_derived_validation_digest(
    report: ResearchSourceClaimVerificationPriorityQueueReport,
) -> None:
    if report.derived_validation_digest != _report_derived_validation_digest(report):
        raise ValueError("derived_validation_digest must match report fields")


def _validate_row_consistency(
    row: ResearchSourceClaimVerificationPriorityQueueRow,
) -> None:
    if row.corroborating_source_count > row.required_corroborating_source_count:
        raise ValueError(
            "corroborating_source_count must not exceed "
            "required_corroborating_source_count",
        )
    if row.extraction_uncertainty_score != _cap_probability(
        ONE - row.extraction_confidence_score,
    ):
        raise ValueError("extraction_uncertainty_score must match confidence")
    if row.corroboration_gap_score != _cap_probability(
        ONE
        - _ratio_raw(
            row.corroborating_source_count,
            row.required_corroborating_source_count,
        ),
    ):
        raise ValueError("corroboration_gap_score must match corroboration counts")
    if row.verification_status == "pass" and row.reason_codes != (PASS_REASON_CODE,):
        raise ValueError("pass rows must only use pass reason code")
    if row.verification_status != "pass" and row.reason_codes == (PASS_REASON_CODE,):
        raise ValueError("non-pass rows must not only use pass reason code")


def _validate_report_consistency(
    report: ResearchSourceClaimVerificationPriorityQueueReport,
) -> None:
    if report.claim_count != _count(len(report.rows)):
        raise ValueError("claim_count must match rows")
    if report.pass_count != _row_status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _row_status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _row_status_count(report.rows, "block"):
        raise ValueError("block_count must match rows")
    if report.average_verification_priority_score != _average(
        tuple(row.verification_priority_score for row in report.rows),
    ):
        raise ValueError("average_verification_priority_score must match rows")
    if report.max_verification_priority_score != _max_decimal(
        tuple(row.verification_priority_score for row in report.rows),
    ):
        raise ValueError("max_verification_priority_score must match rows")
    if report.average_source_authority_score != _average(
        tuple(row.source_authority_score for row in report.rows),
    ):
        raise ValueError("average_source_authority_score must match rows")
    if report.average_freshness_score != _average(
        tuple(row.freshness_score for row in report.rows),
    ):
        raise ValueError("average_freshness_score must match rows")
    if report.average_contradiction_severity != _average(
        tuple(row.contradiction_severity for row in report.rows),
    ):
        raise ValueError("average_contradiction_severity must match rows")
    if report.average_extraction_confidence_score != _average(
        tuple(row.extraction_confidence_score for row in report.rows),
    ):
        raise ValueError("average_extraction_confidence_score must match rows")
    if report.average_corroboration_gap_score != _average(
        tuple(row.corroboration_gap_score for row in report.rows),
    ):
        raise ValueError("average_corroboration_gap_score must match rows")
    if report.average_deadline_proximity_score != _average(
        tuple(row.deadline_proximity_score for row in report.rows),
    ):
        raise ValueError("average_deadline_proximity_score must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    for expected_rank, row in enumerate(report.rows, start=1):
        if row.priority_rank != _count(expected_rank):
            raise ValueError("priority_rank values must match row order")
    if report.rows != tuple(sorted(report.rows, key=_row_sort_key)):
        raise ValueError("rows must be sorted deterministically")


def _validate_public_report_payload(payload: dict[str, object]) -> None:
    _require_exact_payload_fields(payload, PUBLIC_REPORT_PAYLOAD_FIELDS, "report")
    _require_public_label("config_version", payload["config_version"])
    _require_datetime_payload_string("generated_at", payload["generated_at"])
    _require_status("status", payload["status"])
    for field_name in ("claim_count", "pass_count", "watch_count", "block_count"):
        _require_decimal_payload_string(field_name, payload[field_name], whole=True)
    for field_name in (
        "average_verification_priority_score",
        "max_verification_priority_score",
        "average_source_authority_score",
        "average_freshness_score",
        "average_contradiction_severity",
        "average_extraction_confidence_score",
        "average_corroboration_gap_score",
        "average_deadline_proximity_score",
    ):
        _require_decimal_payload_string(field_name, payload[field_name], probability=True)
    _normalize_public_reason_codes("reason_codes", payload["reason_codes"])
    rows = payload["rows"]
    if type(rows) is not list:
        raise ValueError("rows must be a list")
    for row_payload in rows:
        if type(row_payload) is not dict:
            raise ValueError("rows must contain row payload dictionaries")
        _reject_unsafe_public_payload("row payload", row_payload)
        _validate_public_row_payload(row_payload)
    _require_hard_flags("payload", _DictFlags(payload))
    _require_sha256_digest(
        DERIVED_VALIDATION_DIGEST_FIELD,
        payload[DERIVED_VALIDATION_DIGEST_FIELD],
    )
    if payload[DERIVED_VALIDATION_DIGEST_FIELD] != _derived_validation_digest(
        "research_source_claim_verification_priority_queue_report",
        payload,
        PUBLIC_REPORT_PAYLOAD_FIELDS_WITHOUT_DIGEST,
    ):
        raise ValueError("derived_validation_digest must match payload fields")


def _validate_public_row_payload(payload: dict[str, object]) -> None:
    _require_exact_payload_fields(payload, PUBLIC_ROW_PAYLOAD_FIELDS, "row")
    for field_name in (
        "config_version",
        "claim_label",
        "source_family_label",
        "resolution_bucket",
    ):
        _require_public_label(field_name, payload[field_name])
    _require_datetime_payload_string("source_observed_at", payload["source_observed_at"])
    _require_datetime_payload_string(
        "resolution_deadline_at",
        payload["resolution_deadline_at"],
    )
    for field_name in (
        "priority_rank",
        "source_age_seconds",
        "corroborating_source_count",
        "required_corroborating_source_count",
        "deadline_seconds",
    ):
        _require_decimal_payload_string(
            field_name,
            payload[field_name],
            whole=field_name
            in {
                "priority_rank",
                "corroborating_source_count",
                "required_corroborating_source_count",
            },
        )
    for field_name in (
        "source_authority_score",
        "freshness_score",
        "contradiction_severity",
        "extraction_confidence_score",
        "extraction_uncertainty_score",
        "corroboration_gap_score",
        "deadline_proximity_score",
        "verification_priority_score",
    ):
        _require_decimal_payload_string(field_name, payload[field_name], probability=True)
    _require_status("verification_status", payload["verification_status"])
    _normalize_public_reason_codes("reason_codes", payload["reason_codes"])
    _require_hard_flags("row payload", _DictFlags(payload))
    _require_sha256_digest(
        DERIVED_VALIDATION_DIGEST_FIELD,
        payload[DERIVED_VALIDATION_DIGEST_FIELD],
    )
    if payload[DERIVED_VALIDATION_DIGEST_FIELD] != _derived_validation_digest(
        "research_source_claim_verification_priority_queue_report_row",
        payload,
        PUBLIC_ROW_PAYLOAD_FIELDS_WITHOUT_DIGEST,
    ):
        raise ValueError("derived_validation_digest must match row payload fields")


def _require_exact_payload_fields(
    payload: dict[str, object],
    field_names: tuple[str, ...],
    label: str,
) -> None:
    missing = [field_name for field_name in field_names if field_name not in payload]
    if missing:
        raise ValueError(f"{missing[0]} is required")
    extra = sorted(set(payload) - set(field_names))
    if extra:
        raise ValueError(f"unexpected {label} payload field: {extra[0]}")


def _normalize_observations(
    values: Iterable[object],
) -> tuple[ResearchSourceClaimVerificationPriorityQueueObservation, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("observations must be an iterable")
    try:
        observations = tuple(values)
    except TypeError as exc:
        raise ValueError("observations must be an iterable") from exc
    normalized: list[ResearchSourceClaimVerificationPriorityQueueObservation] = []
    for observation in observations:
        _require_exact_type(
            "observation",
            observation,
            ResearchSourceClaimVerificationPriorityQueueObservation,
        )
        _reject_unsafe_public_payload("observation", observation)
        _require_hard_flags("observation", observation)
        normalized.append(observation)
    return tuple(
        sorted(
            normalized,
            key=lambda observation: (
                observation.claim_label,
                observation.source_family_label,
                observation.resolution_bucket,
            ),
        ),
    )


def _normalize_rows(
    value: object,
) -> tuple[ResearchSourceClaimVerificationPriorityQueueRow, ...]:
    if type(value) is not tuple:
        raise ValueError("rows must be a tuple")
    rows: list[ResearchSourceClaimVerificationPriorityQueueRow] = []
    for row in value:
        _require_exact_type("row", row, ResearchSourceClaimVerificationPriorityQueueRow)
        _require_hard_flags("row", row)
        _validate_row_derived_validation_digest(row)
        rows.append(row)
    return tuple(sorted(rows, key=_row_sort_key))


def _reject_invalid_observation_timing(
    observations: tuple[ResearchSourceClaimVerificationPriorityQueueObservation, ...],
    generated_at: datetime,
) -> None:
    for observation in observations:
        if observation.source_observed_at > generated_at:
            raise ValueError("source_observed_at must not be after generated_at")
        if observation.resolution_deadline_at < generated_at:
            raise ValueError("resolution_deadline_at must not be before generated_at")


def _require_weight_sum(
    config: ResearchSourceClaimVerificationPriorityQueueConfig,
) -> None:
    weight_sum = _quantize_decimal(
        config.authority_weight
        + config.freshness_weight
        + config.contradiction_weight
        + config.extraction_confidence_weight
        + config.corroboration_gap_weight
        + config.deadline_proximity_weight,
    )
    if weight_sum != ONE:
        raise ValueError("weights must sum to one")


def _ratio_raw(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= ZERO:
        raise ValueError("denominator must be positive")
    return numerator / denominator


def _cap_probability(value: Decimal) -> Decimal:
    normalized = _quantize_decimal(value)
    if normalized < ZERO:
        return ZERO
    if normalized > ONE:
        return ONE
    return normalized


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _quantize_decimal(sum(values, ZERO) / Decimal(len(values)))


def _max_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return max(values)


def _count(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be nonnegative")
    return _quantize_decimal(Decimal(value))


def _datetime_delta_seconds(later: datetime, earlier: datetime) -> Decimal:
    delta = later - earlier
    seconds = Decimal(delta.days * 86400 + delta.seconds)
    microseconds = Decimal(delta.microseconds) / MICROSECOND_DIVISOR
    return _quantize_decimal(seconds + microseconds)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be exactly datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    offset = value.utcoffset()
    if offset is None:
        raise ValueError(f"{field_name} utcoffset must not be None")
    return value.astimezone(UTC)


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    seen: set[str] = set()
    for reason_code in value:
        _require_public_label(field_name, reason_code)
        if reason_code not in SAFE_REASON_CODES:
            raise ValueError(f"{field_name} must be known")
        seen.add(reason_code)
    return tuple(reason_code for reason_code in SAFE_REASON_CODES if reason_code in seen)


def _normalize_public_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a list")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    codes: list[str] = []
    for reason_code in value:
        _require_public_label(field_name, reason_code)
        if reason_code not in SAFE_REASON_CODES:
            raise ValueError(f"{field_name} must be known")
        codes.append(reason_code)
    if len(set(codes)) != len(codes):
        raise ValueError(f"{field_name} must be unique")
    return tuple(codes)


def _require_exact_type(field_name: str, value: object, expected_type: type[object]) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be exactly {expected_type.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in PHASE_FLAG_FIELDS:
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_public_label(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    _reject_unsafe_public_string(field_name, value)
    if not PUBLIC_LABEL_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public label")
    return value


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value not in QUEUE_STATUSES:
        raise ValueError(f"{field_name} must be one of pass, watch, block")
    return value


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_probability_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _normalize_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return normalized


def _normalize_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_positive_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize_decimal(value)


def _quantize_decimal(value: Decimal) -> Decimal:
    return value.quantize(QUANTUM, rounding=ROUND_HALF_UP)


def _decimal_payload(value: Decimal) -> str:
    return str(_normalize_decimal("payload numeric", value))


def _datetime_payload(value: datetime) -> str:
    return _as_utc("payload datetime", value).isoformat()


def _require_decimal_payload_string(
    field_name: str,
    value: object,
    *,
    whole: bool = False,
    probability: bool = False,
) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a Decimal payload string")
    try:
        decimal_value = Decimal(value)
    except Exception as exc:
        raise ValueError(f"{field_name} must be a Decimal payload string") from exc
    if not decimal_value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    normalized = _quantize_decimal(decimal_value)
    if str(normalized) != value:
        raise ValueError(f"{field_name} must use six decimal places")
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if whole and normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    if probability and normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _require_datetime_payload_string(field_name: str, value: object) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a datetime payload string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a datetime payload string") from exc
    return _as_utc(field_name, parsed)


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str or not DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a sha256 digest")
    return value


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _reject_unsafe_public_string(label, field.name, is_key=True)
            _reject_unsafe_public_payload(field.name, getattr(value, field.name))
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _reject_unsafe_public_string(label, key, is_key=True)
            _reject_unsafe_public_payload(key, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) is str:
        _reject_unsafe_public_string(label, value)


def _reject_unsafe_public_string(
    field_name: str,
    value: str,
    *,
    is_key: bool = False,
) -> None:
    lowered = value.lower()
    if field_name == DERIVED_VALIDATION_DIGEST_FIELD and (
        value == "" or DIGEST_RE.fullmatch(value)
    ):
        return
    fragments = UNSAFE_KEY_FRAGMENTS if is_key else UNSAFE_VALUE_FRAGMENTS
    if any(fragment in lowered for fragment in fragments):
        raise ValueError(f"unsafe public value in {field_name}")
    if not is_key and (
        DOMAIN_LIKE_RE.search(lowered)
        or RAW_PUBLIC_ID_RE.search(lowered)
        or BARE_RAW_ID_RE.search(lowered)
        or QUESTION_SLUG_RE.search(lowered)
    ):
        raise ValueError(f"unsafe public value in {field_name}")


@dataclass(frozen=True)
class _DictFlags:
    value: dict[str, object]

    @property
    def paper_only(self) -> object:
        return self.value.get("paper_only")

    @property
    def report_only(self) -> object:
        return self.value.get("report_only")

    @property
    def readonly(self) -> object:
        return self.value.get("readonly")
