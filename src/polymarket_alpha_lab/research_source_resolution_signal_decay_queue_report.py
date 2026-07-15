"""Report-only source resolution signal decay queue reducer."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime, timedelta
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
import re
from typing import Any, Mapping, Sequence


DEFAULT_RESEARCH_SOURCE_RESOLUTION_SIGNAL_DECAY_QUEUE_REPORT_CONFIG_VERSION = (
    "research-source-resolution-signal-decay-queue-report-v0"
)
SOURCE_RESOLUTION_SIGNAL_DECAY_QUEUE_STATUSES = ("pass", "watch", "block")
SOURCE_RESOLUTION_AUTHORITY_TIERS = ("official", "primary", "secondary", "tertiary")

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
SECONDS_PER_HOUR = Decimal("3600.000000")
SECONDS_PER_DAY = Decimal("86400.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000")
PUBLIC_LABEL_RE = re.compile(r"^[a-z0-9][a-z0-9_.-]{0,127}$")
DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
PUBLIC_DECIMAL_RE = re.compile(r"^(?:0|[1-9][0-9]*)\.[0-9]{6}$")

AUTHORITY_TIER_SCORE = {
    "official": Decimal("1.000000"),
    "primary": Decimal("0.850000"),
    "secondary": Decimal("0.650000"),
    "tertiary": Decimal("0.450000"),
}

QUEUE_ACTION_BY_STATUS = {
    "pass": "paper_source_resolution_signal_decay_queue_monitor",
    "watch": "paper_source_resolution_signal_decay_queue_watch",
    "block": "paper_source_resolution_signal_decay_queue_block",
}

REPORT_REASON_BY_STATUS = {
    "pass": "source_resolution_signal_decay_report_pass",
    "watch": "source_resolution_signal_decay_report_watch",
    "block": "source_resolution_signal_decay_report_block",
}

STATUS_REASON_BY_STATUS = {
    "pass": "source_resolution_signal_decay_pass",
    "watch": "source_resolution_signal_decay_watch",
    "block": "source_resolution_signal_decay_block",
}

AUTHORITY_DECAY_REASON = "authority_tier_decay_pressure"
VERIFICATION_AGE_REASON = "latest_verification_age_pressure"
CONTRADICTION_PRESSURE_REASON = "contradiction_pressure"
CORROBORATION_GAP_REASON = "corroboration_depth_gap"
EXTRACTION_CONFIDENCE_GAP_REASON = "extraction_confidence_gap"
DEADLINE_PROXIMITY_REASON = "deadline_proximity_pressure"

ROW_REASON_CODES = (
    AUTHORITY_DECAY_REASON,
    VERIFICATION_AGE_REASON,
    CONTRADICTION_PRESSURE_REASON,
    CORROBORATION_GAP_REASON,
    EXTRACTION_CONFIDENCE_GAP_REASON,
    DEADLINE_PROXIMITY_REASON,
    STATUS_REASON_BY_STATUS["pass"],
    STATUS_REASON_BY_STATUS["watch"],
    STATUS_REASON_BY_STATUS["block"],
)
REPORT_REASON_CODES = (
    REPORT_REASON_BY_STATUS["pass"],
    REPORT_REASON_BY_STATUS["watch"],
    REPORT_REASON_BY_STATUS["block"],
    *ROW_REASON_CODES,
)

UNSAFE_PUBLIC_KEY_FRAGMENTS = frozenset(
    (
        "candidate",
        "market",
        "slug",
        "question",
        "url",
        "text",
        "dsn",
        "table",
        "token",
        "secret",
        "credential",
        "api_key",
        "wallet",
        "order",
        "trade",
        "sizing",
        "recommend",
        "execution",
        "execute",
        "live",
        "authorization",
        "auth_token",
        "bearer",
        "password",
        "private_key",
        "session",
        "cookie",
        "raw",
        "scrape",
        "network",
        "database",
    ),
)
UNSAFE_PUBLIC_VALUE_FRAGMENTS = frozenset(
    (
        "candidate",
        "market",
        "slug",
        "question",
        "http://",
        "https://",
        "source_url",
        "source_text",
        "postgres://",
        "dsn",
        "table",
        "token",
        "secret",
        "credential",
        "api_key",
        "wallet",
        "order",
        "trade",
        "sizing",
        "recommend",
        "execution",
        "execute",
        "live",
        "authorization",
        "auth_token",
        "bearer",
        "password",
        "private_key",
        "session",
        "cookie",
        "raw_source",
        "scrape",
        "network",
        "database",
    ),
)
UNSAFE_PUBLIC_KEYS = frozenset(
    (
        "candidate_id",
        "market_id",
        "market_slug",
        "question",
        "source_url",
        "source_text",
        "raw_source",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "sizing",
        "recommendation",
        "execution",
        "live",
        "authorization",
        "auth_token",
        "password",
        "private_key",
        "session",
        "cookie",
    ),
)
PUBLIC_DECIMAL_KEYS = frozenset(
    (
        "queue_item_count",
        "pass_count",
        "watch_count",
        "block_count",
        "average_signal_decay_score",
        "max_signal_decay_score",
        "max_latest_verification_age_hours",
        "min_extraction_confidence",
        "latest_verification_age_hours",
        "deadline_proximity_hours",
        "authority_tier_score",
        "authority_decay_score",
        "verification_age_score",
        "contradiction_pressure",
        "corroboration_depth",
        "corroboration_gap_score",
        "extraction_confidence",
        "extraction_confidence_gap_score",
        "deadline_proximity_score",
        "signal_decay_score",
        "count",
        "queue_ratio",
        "watch_score_threshold",
        "block_score_threshold",
        "max_watch_verification_age_hours",
        "deadline_proximity_window_hours",
        "min_pass_corroboration_depth",
        "authority_tier_weight",
        "latest_verification_age_weight",
        "contradiction_pressure_weight",
        "corroboration_depth_weight",
        "extraction_confidence_weight",
        "deadline_proximity_weight",
    ),
)

__all__ = (
    "DEFAULT_RESEARCH_SOURCE_RESOLUTION_SIGNAL_DECAY_QUEUE_REPORT_CONFIG_VERSION",
    "SOURCE_RESOLUTION_SIGNAL_DECAY_QUEUE_STATUSES",
    "SOURCE_RESOLUTION_AUTHORITY_TIERS",
    "ResearchSourceResolutionSignalDecayQueueConfig",
    "ResearchSourceResolutionSignalDecayObservation",
    "ResearchSourceResolutionSignalDecayQueueReasonCodeCount",
    "ResearchSourceResolutionSignalDecayQueueReport",
    "ResearchSourceResolutionSignalDecayQueueRow",
    "build_research_source_resolution_signal_decay_queue_report",
    "research_source_resolution_signal_decay_queue_report_digest",
    "research_source_resolution_signal_decay_queue_report_payload",
)


class _FinalDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalDataclass and issubclass(base, _FinalDataclass):
                raise TypeError(f"{base.__name__} subclass is not allowed")


@dataclass(frozen=True)
class ResearchSourceResolutionSignalDecayQueueConfig(_FinalDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_SOURCE_RESOLUTION_SIGNAL_DECAY_QUEUE_REPORT_CONFIG_VERSION
    )
    watch_score_threshold: Decimal = Decimal("0.350000")
    block_score_threshold: Decimal = Decimal("0.700000")
    max_watch_verification_age_hours: Decimal = Decimal("72.000000")
    deadline_proximity_window_hours: Decimal = Decimal("48.000000")
    min_pass_corroboration_depth: Decimal = Decimal("4.000000")
    authority_tier_weight: Decimal = Decimal("0.150000")
    latest_verification_age_weight: Decimal = Decimal("0.200000")
    contradiction_pressure_weight: Decimal = Decimal("0.250000")
    corroboration_depth_weight: Decimal = Decimal("0.150000")
    extraction_confidence_weight: Decimal = Decimal("0.150000")
    deadline_proximity_weight: Decimal = Decimal("0.100000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchSourceResolutionSignalDecayQueueConfig, "config")
        _require_public_label("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_RESOLUTION_SIGNAL_DECAY_QUEUE_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "watch_score_threshold",
            "block_score_threshold",
            "authority_tier_weight",
            "latest_verification_age_weight",
            "contradiction_pressure_weight",
            "corroboration_depth_weight",
            "extraction_confidence_weight",
            "deadline_proximity_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_watch_verification_age_hours",
            "deadline_proximity_window_hours",
            "min_pass_corroboration_depth",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_count_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchSourceResolutionSignalDecayObservation(_FinalDataclass):
    scope_label: str
    authority_tier: str
    latest_verified_at: datetime
    contradiction_pressure: Decimal
    corroboration_depth: Decimal
    extraction_confidence: Decimal
    deadline_at: datetime
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchSourceResolutionSignalDecayObservation, "observation")
        _require_public_label("scope_label", self.scope_label)
        _require_authority_tier("authority_tier", self.authority_tier)
        object.__setattr__(
            self,
            "latest_verified_at",
            _as_utc("latest_verified_at", self.latest_verified_at),
        )
        object.__setattr__(
            self,
            "deadline_at",
            _as_utc("deadline_at", self.deadline_at),
        )
        object.__setattr__(
            self,
            "contradiction_pressure",
            _require_ratio_decimal("contradiction_pressure", self.contradiction_pressure),
        )
        object.__setattr__(
            self,
            "corroboration_depth",
            _require_nonnegative_count_decimal(
                "corroboration_depth",
                self.corroboration_depth,
            ),
        )
        object.__setattr__(
            self,
            "extraction_confidence",
            _require_ratio_decimal("extraction_confidence", self.extraction_confidence),
        )
        _require_hard_flags("observation", self)
        _reject_unsafe_public_payload("observation", self)


@dataclass(frozen=True)
class ResearchSourceResolutionSignalDecayQueueRow(_FinalDataclass):
    scope_label: str
    queue_status: str
    generated_at: datetime
    latest_verified_at: datetime
    latest_verification_age_hours: Decimal
    deadline_at: datetime
    deadline_proximity_hours: Decimal
    authority_tier: str
    authority_tier_score: Decimal
    authority_decay_score: Decimal
    verification_age_score: Decimal
    contradiction_pressure: Decimal
    corroboration_depth: Decimal
    corroboration_gap_score: Decimal
    extraction_confidence: Decimal
    extraction_confidence_gap_score: Decimal
    deadline_proximity_score: Decimal
    signal_decay_score: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchSourceResolutionSignalDecayQueueRow, "row")
        _require_public_label("scope_label", self.scope_label)
        _require_status("queue_status", self.queue_status)
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "latest_verified_at",
            _as_utc("latest_verified_at", self.latest_verified_at),
        )
        object.__setattr__(
            self,
            "deadline_at",
            _as_utc("deadline_at", self.deadline_at),
        )
        _require_authority_tier("authority_tier", self.authority_tier)
        for field_name in (
            "latest_verification_age_hours",
            "deadline_proximity_hours",
            "corroboration_depth",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "authority_tier_score",
            "authority_decay_score",
            "verification_age_score",
            "contradiction_pressure",
            "corroboration_gap_score",
            "extraction_confidence",
            "extraction_confidence_gap_score",
            "deadline_proximity_score",
            "signal_decay_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _require_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _validate_row(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchSourceResolutionSignalDecayQueueReasonCodeCount(_FinalDataclass):
    reason_code: str
    count: Decimal
    queue_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchSourceResolutionSignalDecayQueueReasonCodeCount,
            "reason_code_count",
        )
        _require_reason_code("reason_code", self.reason_code, ROW_REASON_CODES)
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_count_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "queue_ratio",
            _require_ratio_decimal("queue_ratio", self.queue_ratio),
        )
        _require_hard_flags("reason_code_count", self)
        _reject_unsafe_public_payload("reason_code_count", self)


@dataclass(frozen=True)
class ResearchSourceResolutionSignalDecayQueueReport(_FinalDataclass):
    generated_at: datetime
    config_version: str
    config: ResearchSourceResolutionSignalDecayQueueConfig
    status: str
    queue_action: str
    queue_item_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_signal_decay_score: Decimal
    max_signal_decay_score: Decimal
    max_latest_verification_age_hours: Decimal
    min_extraction_confidence: Decimal
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchSourceResolutionSignalDecayQueueReasonCodeCount, ...]
    rows: tuple[ResearchSourceResolutionSignalDecayQueueRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchSourceResolutionSignalDecayQueueReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(self, "config", _normalize_config(self.config))
        _require_public_label("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_RESOLUTION_SIGNAL_DECAY_QUEUE_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        if self.config_version != self.config.config_version:
            raise ValueError("config_version must match config")
        _require_status("status", self.status)
        _require_public_label("queue_action", self.queue_action)
        if self.queue_action != QUEUE_ACTION_BY_STATUS[self.status]:
            raise ValueError("queue_action must match status")
        for field_name in (
            "queue_item_count",
            "pass_count",
            "watch_count",
            "block_count",
            "max_latest_verification_age_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_signal_decay_score",
            "max_signal_decay_score",
            "min_extraction_confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _require_reason_codes("reason_codes", self.reason_codes, REPORT_REASON_CODES),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        _require_digest("derived_validation_digest", self.derived_validation_digest)
        _validate_report(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _report_digest_from_values(_report_values_without_digest(self))
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest does not match report fields")

    @property
    def payload(self) -> dict[str, Any]:
        return research_source_resolution_signal_decay_queue_report_payload(self)


def build_research_source_resolution_signal_decay_queue_report(
    observations: Sequence[ResearchSourceResolutionSignalDecayObservation],
    *,
    generated_at: datetime,
    config: ResearchSourceResolutionSignalDecayQueueConfig | None = None,
) -> ResearchSourceResolutionSignalDecayQueueReport:
    """Build a deterministic report-only queue of source resolution decay checks."""

    if config is None:
        config = ResearchSourceResolutionSignalDecayQueueConfig()
    config = _normalize_config(config)
    generated_at = _as_utc("generated_at", generated_at)
    normalized_observations = _normalize_observations(observations)
    for observation in normalized_observations:
        if observation.latest_verified_at > generated_at:
            raise ValueError("latest_verified_at must not be after generated_at")
    rows = tuple(
        sorted(
            (
                _row_from_observation(
                    observation,
                    generated_at=generated_at,
                    config=config,
                )
                for observation in normalized_observations
            ),
            key=_row_sort_key,
        ),
    )
    status = _report_status(rows)
    values: dict[str, object] = {
        "generated_at": generated_at,
        "config_version": config.config_version,
        "config": config,
        "status": status,
        "queue_action": QUEUE_ACTION_BY_STATUS[status],
        "queue_item_count": _decimal_count(len(rows)),
        "pass_count": _decimal_count(_status_count(rows, "pass")),
        "watch_count": _decimal_count(_status_count(rows, "watch")),
        "block_count": _decimal_count(_status_count(rows, "block")),
        "average_signal_decay_score": _average(
            tuple(row.signal_decay_score for row in rows),
        ),
        "max_signal_decay_score": max(
            (row.signal_decay_score for row in rows),
            default=ZERO,
        ),
        "max_latest_verification_age_hours": max(
            (row.latest_verification_age_hours for row in rows),
            default=ZERO,
        ),
        "min_extraction_confidence": min(
            (row.extraction_confidence for row in rows),
            default=ZERO,
        ),
        "reason_codes": _report_reason_codes(rows, status),
        "reason_code_counts": _reason_code_counts(rows),
        "rows": rows,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchSourceResolutionSignalDecayQueueReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def research_source_resolution_signal_decay_queue_report_payload(
    report: ResearchSourceResolutionSignalDecayQueueReport | Mapping[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchSourceResolutionSignalDecayQueueReport:
        report = _revalidate_report(report)
        _require_hard_flags("report", report)
        _reject_unsafe_public_payload("report", report)
        payload = _json_ready(asdict(report))
    elif type(report) is dict:
        _reject_unsafe_public_payload("payload", report, allow_json_containers=True)
        payload = _json_ready(report)
        if type(payload) is not dict:
            raise ValueError("payload must be a JSON object")
        _validate_public_payload(payload)
        reconstructed = _report_from_payload(payload)
        canonical_payload = _json_ready(asdict(reconstructed))
        if payload != canonical_payload:
            raise ValueError("payload must match canonical schema and derived fields")
        payload = canonical_payload
    else:
        raise ValueError(
            "report must be a ResearchSourceResolutionSignalDecayQueueReport",
        )
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    _reject_unsafe_public_payload("payload", payload, allow_json_containers=True)
    _validate_public_payload(payload)
    return payload


def research_source_resolution_signal_decay_queue_report_digest(
    report: ResearchSourceResolutionSignalDecayQueueReport | Mapping[str, Any],
) -> str:
    payload = research_source_resolution_signal_decay_queue_report_payload(report)
    digest = payload["derived_validation_digest"]
    if type(digest) is not str:
        raise ValueError("derived_validation_digest must be a string")
    return digest


def _row_from_observation(
    observation: ResearchSourceResolutionSignalDecayObservation,
    *,
    generated_at: datetime,
    config: ResearchSourceResolutionSignalDecayQueueConfig,
) -> ResearchSourceResolutionSignalDecayQueueRow:
    age_hours = _duration_hours(observation.latest_verified_at, generated_at)
    deadline_hours = _future_duration_hours(generated_at, observation.deadline_at)
    authority_score = AUTHORITY_TIER_SCORE[observation.authority_tier]
    authority_decay = _clamp_ratio(ONE - authority_score)
    verification_age_score = _clamp_ratio(
        _safe_ratio(age_hours, config.max_watch_verification_age_hours),
    )
    corroboration_gap_score = _clamp_ratio(
        _safe_ratio(
            max(config.min_pass_corroboration_depth - observation.corroboration_depth, ZERO),
            config.min_pass_corroboration_depth,
        ),
    )
    extraction_gap_score = _clamp_ratio(ONE - observation.extraction_confidence)
    deadline_score = _clamp_ratio(
        _safe_ratio(
            max(config.deadline_proximity_window_hours - deadline_hours, ZERO),
            config.deadline_proximity_window_hours,
        ),
    )
    signal_decay_score = _clamp_ratio(
        (authority_decay * config.authority_tier_weight)
        + (verification_age_score * config.latest_verification_age_weight)
        + (observation.contradiction_pressure * config.contradiction_pressure_weight)
        + (corroboration_gap_score * config.corroboration_depth_weight)
        + (extraction_gap_score * config.extraction_confidence_weight)
        + (deadline_score * config.deadline_proximity_weight),
    )
    queue_status = _queue_status(signal_decay_score, config)
    return ResearchSourceResolutionSignalDecayQueueRow(
        scope_label=observation.scope_label,
        queue_status=queue_status,
        generated_at=generated_at,
        latest_verified_at=observation.latest_verified_at,
        latest_verification_age_hours=age_hours,
        deadline_at=observation.deadline_at,
        deadline_proximity_hours=deadline_hours,
        authority_tier=observation.authority_tier,
        authority_tier_score=authority_score,
        authority_decay_score=authority_decay,
        verification_age_score=verification_age_score,
        contradiction_pressure=observation.contradiction_pressure,
        corroboration_depth=observation.corroboration_depth,
        corroboration_gap_score=corroboration_gap_score,
        extraction_confidence=observation.extraction_confidence,
        extraction_confidence_gap_score=extraction_gap_score,
        deadline_proximity_score=deadline_score,
        signal_decay_score=signal_decay_score,
        reason_codes=_row_reason_codes(
            queue_status=queue_status,
            authority_decay_score=authority_decay,
            verification_age_score=verification_age_score,
            contradiction_pressure=observation.contradiction_pressure,
            corroboration_gap_score=corroboration_gap_score,
            extraction_confidence_gap_score=extraction_gap_score,
            deadline_proximity_score=deadline_score,
        ),
    )


def _row_reason_codes(
    *,
    queue_status: str,
    authority_decay_score: Decimal,
    verification_age_score: Decimal,
    contradiction_pressure: Decimal,
    corroboration_gap_score: Decimal,
    extraction_confidence_gap_score: Decimal,
    deadline_proximity_score: Decimal,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if authority_decay_score >= Decimal("0.250000"):
        reasons.append(AUTHORITY_DECAY_REASON)
    if verification_age_score >= Decimal("0.500000"):
        reasons.append(VERIFICATION_AGE_REASON)
    if contradiction_pressure >= Decimal("0.250000"):
        reasons.append(CONTRADICTION_PRESSURE_REASON)
    if corroboration_gap_score > ZERO:
        reasons.append(CORROBORATION_GAP_REASON)
    if extraction_confidence_gap_score >= Decimal("0.250000"):
        reasons.append(EXTRACTION_CONFIDENCE_GAP_REASON)
    if deadline_proximity_score >= Decimal("0.500000"):
        reasons.append(DEADLINE_PROXIMITY_REASON)
    reasons.append(STATUS_REASON_BY_STATUS[queue_status])
    return _require_reason_codes("reason_codes", tuple(reasons), ROW_REASON_CODES)


def _queue_status(
    signal_decay_score: Decimal,
    config: ResearchSourceResolutionSignalDecayQueueConfig,
) -> str:
    if signal_decay_score >= config.block_score_threshold:
        return "block"
    if signal_decay_score >= config.watch_score_threshold:
        return "watch"
    return "pass"


def _report_status(rows: tuple[ResearchSourceResolutionSignalDecayQueueRow, ...]) -> str:
    if any(row.queue_status == "block" for row in rows):
        return "block"
    if any(row.queue_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchSourceResolutionSignalDecayQueueRow, ...],
    status: str,
) -> tuple[str, ...]:
    row_reasons = {reason for row in rows for reason in row.reason_codes}
    return (
        REPORT_REASON_BY_STATUS[status],
        *(reason for reason in ROW_REASON_CODES if reason in row_reasons),
    )


def _reason_code_counts(
    rows: tuple[ResearchSourceResolutionSignalDecayQueueRow, ...],
) -> tuple[ResearchSourceResolutionSignalDecayQueueReasonCodeCount, ...]:
    counts = Counter(reason for row in rows for reason in row.reason_codes)
    row_count = _decimal_count(len(rows))
    return tuple(
        ResearchSourceResolutionSignalDecayQueueReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(counts[reason_code]),
            queue_ratio=_safe_ratio(_decimal_count(counts[reason_code]), row_count),
        )
        for reason_code in ROW_REASON_CODES
        if counts[reason_code]
    )


def _normalize_config(
    config: ResearchSourceResolutionSignalDecayQueueConfig,
) -> ResearchSourceResolutionSignalDecayQueueConfig:
    if type(config) is not ResearchSourceResolutionSignalDecayQueueConfig:
        raise ValueError(
            "config must be a ResearchSourceResolutionSignalDecayQueueConfig",
        )
    return ResearchSourceResolutionSignalDecayQueueConfig(
        **_dataclass_field_values(config),
    )


def _normalize_observations(
    observations: Sequence[ResearchSourceResolutionSignalDecayObservation],
) -> tuple[ResearchSourceResolutionSignalDecayObservation, ...]:
    if isinstance(observations, (str, bytes)):
        raise ValueError("observations must be a sequence")
    items = tuple(observations)
    normalized: list[ResearchSourceResolutionSignalDecayObservation] = []
    seen: set[str] = set()
    for observation in items:
        if type(observation) is not ResearchSourceResolutionSignalDecayObservation:
            raise ValueError(
                "observations must contain ResearchSourceResolutionSignalDecayObservation",
            )
        revalidated = ResearchSourceResolutionSignalDecayObservation(
            **_dataclass_field_values(observation),
        )
        if revalidated.scope_label in seen:
            raise ValueError("scope_label values must be unique")
        seen.add(revalidated.scope_label)
        normalized.append(revalidated)
    return tuple(normalized)


def _normalize_rows(
    rows: tuple[ResearchSourceResolutionSignalDecayQueueRow, ...],
) -> tuple[ResearchSourceResolutionSignalDecayQueueRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    normalized_items: list[ResearchSourceResolutionSignalDecayQueueRow] = []
    for row in rows:
        if type(row) is not ResearchSourceResolutionSignalDecayQueueRow:
            raise ValueError("rows must contain ResearchSourceResolutionSignalDecayQueueRow")
        normalized_items.append(
            ResearchSourceResolutionSignalDecayQueueRow(
                **_dataclass_field_values(row),
            ),
        )
    normalized = tuple(normalized_items)
    sorted_rows = tuple(sorted(normalized, key=_row_sort_key))
    if normalized != sorted_rows:
        raise ValueError("rows must be sorted by queue priority")
    if len({row.scope_label for row in normalized}) != len(normalized):
        raise ValueError("rows must have unique scope_label values")
    return normalized


def _normalize_reason_code_counts(
    counts: tuple[ResearchSourceResolutionSignalDecayQueueReasonCodeCount, ...],
) -> tuple[ResearchSourceResolutionSignalDecayQueueReasonCodeCount, ...]:
    if type(counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    normalized_items: list[ResearchSourceResolutionSignalDecayQueueReasonCodeCount] = []
    for item in counts:
        if type(item) is not ResearchSourceResolutionSignalDecayQueueReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchSourceResolutionSignalDecayQueueReasonCodeCount",
            )
        normalized_items.append(
            ResearchSourceResolutionSignalDecayQueueReasonCodeCount(
                **_dataclass_field_values(item),
            ),
        )
    normalized = tuple(normalized_items)
    expected = tuple(
        sorted(
            normalized,
            key=lambda item: ROW_REASON_CODES.index(item.reason_code),
        ),
    )
    if normalized != expected:
        raise ValueError("reason_code_counts must be sorted")
    if len({item.reason_code for item in normalized}) != len(normalized):
        raise ValueError("reason_code_counts must be unique")
    return normalized


def _row_sort_key(
    row: ResearchSourceResolutionSignalDecayQueueRow,
) -> tuple[int, Decimal, Decimal, Decimal, Decimal, Decimal, Decimal, Decimal, str]:
    return (
        {"block": 0, "watch": 1, "pass": 2}[row.queue_status],
        -row.signal_decay_score,
        row.deadline_proximity_hours,
        -row.latest_verification_age_hours,
        -row.contradiction_pressure,
        -row.corroboration_gap_score,
        -row.extraction_confidence_gap_score,
        -row.authority_decay_score,
        row.scope_label,
    )


def _status_count(
    rows: tuple[ResearchSourceResolutionSignalDecayQueueRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.queue_status == status)


def _validate_config(config: ResearchSourceResolutionSignalDecayQueueConfig) -> None:
    if config.block_score_threshold <= config.watch_score_threshold:
        raise ValueError("block_score_threshold must exceed watch_score_threshold")
    weights = (
        config.authority_tier_weight
        + config.latest_verification_age_weight
        + config.contradiction_pressure_weight
        + config.corroboration_depth_weight
        + config.extraction_confidence_weight
        + config.deadline_proximity_weight
    )
    if _quantize(weights) != ONE:
        raise ValueError("signal decay weights must sum to 1.000000")


def _validate_row(
    row: ResearchSourceResolutionSignalDecayQueueRow,
    config: ResearchSourceResolutionSignalDecayQueueConfig | None = None,
) -> None:
    if row.latest_verified_at > row.generated_at:
        raise ValueError("latest_verified_at must not be after generated_at")
    if row.latest_verification_age_hours != _duration_hours(
        row.latest_verified_at,
        row.generated_at,
    ):
        raise ValueError("latest_verification_age_hours must match timestamps")
    if row.deadline_proximity_hours != _future_duration_hours(
        row.generated_at,
        row.deadline_at,
    ):
        raise ValueError("deadline_proximity_hours must match deadline")
    if row.authority_tier_score != AUTHORITY_TIER_SCORE[row.authority_tier]:
        raise ValueError("authority_tier_score must match authority_tier")
    if row.authority_decay_score != _clamp_ratio(ONE - row.authority_tier_score):
        raise ValueError("authority_decay_score must match authority_tier_score")
    if config is None:
        return
    config = _normalize_config(config)
    if row.verification_age_score != _clamp_ratio(
        _safe_ratio(
            row.latest_verification_age_hours,
            config.max_watch_verification_age_hours,
        ),
    ):
        raise ValueError("verification_age_score must match latest verification age")
    if row.corroboration_gap_score != _clamp_ratio(
        _safe_ratio(
            max(config.min_pass_corroboration_depth - row.corroboration_depth, ZERO),
            config.min_pass_corroboration_depth,
        ),
    ):
        raise ValueError("corroboration_gap_score must match corroboration_depth")
    if row.extraction_confidence_gap_score != _clamp_ratio(
        ONE - row.extraction_confidence,
    ):
        raise ValueError(
            "extraction_confidence_gap_score must match extraction_confidence",
        )
    if row.deadline_proximity_score != _clamp_ratio(
        _safe_ratio(
            max(config.deadline_proximity_window_hours - row.deadline_proximity_hours, ZERO),
            config.deadline_proximity_window_hours,
        ),
    ):
        raise ValueError("deadline_proximity_score must match deadline proximity")
    expected_signal_decay_score = _clamp_ratio(
        (row.authority_decay_score * config.authority_tier_weight)
        + (row.verification_age_score * config.latest_verification_age_weight)
        + (row.contradiction_pressure * config.contradiction_pressure_weight)
        + (row.corroboration_gap_score * config.corroboration_depth_weight)
        + (row.extraction_confidence_gap_score * config.extraction_confidence_weight)
        + (row.deadline_proximity_score * config.deadline_proximity_weight),
    )
    if row.signal_decay_score != expected_signal_decay_score:
        raise ValueError("signal_decay_score must match row score components")
    if row.queue_status != _queue_status(row.signal_decay_score, config):
        raise ValueError("queue_status must match signal_decay_score")
    if row.reason_codes != _row_reason_codes(
        queue_status=row.queue_status,
        authority_decay_score=row.authority_decay_score,
        verification_age_score=row.verification_age_score,
        contradiction_pressure=row.contradiction_pressure,
        corroboration_gap_score=row.corroboration_gap_score,
        extraction_confidence_gap_score=row.extraction_confidence_gap_score,
        deadline_proximity_score=row.deadline_proximity_score,
    ):
        raise ValueError("reason_codes must match row score components")


def _validate_report(report: ResearchSourceResolutionSignalDecayQueueReport) -> None:
    for row in report.rows:
        _validate_row(row, report.config)
        if row.generated_at != report.generated_at:
            raise ValueError("row generated_at must match report generated_at")
    if report.queue_item_count != _decimal_count(len(report.rows)):
        raise ValueError("queue_item_count must equal row count")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must equal pass rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must equal watch rows")
    if report.block_count != _decimal_count(_status_count(report.rows, "block")):
        raise ValueError("block_count must equal block rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match queued rows")
    if report.average_signal_decay_score != _average(
        tuple(row.signal_decay_score for row in report.rows),
    ):
        raise ValueError("average_signal_decay_score must match rows")
    if report.max_signal_decay_score != max(
        (row.signal_decay_score for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_signal_decay_score must match rows")
    if report.max_latest_verification_age_hours != max(
        (row.latest_verification_age_hours for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_latest_verification_age_hours must match rows")
    if report.min_extraction_confidence != min(
        (row.extraction_confidence for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("min_extraction_confidence must match rows")
    if report.reason_codes != _report_reason_codes(report.rows, report.status):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows):
        raise ValueError("reason_code_counts must match rows")


def _revalidate_report(
    report: ResearchSourceResolutionSignalDecayQueueReport,
) -> ResearchSourceResolutionSignalDecayQueueReport:
    if type(report) is not ResearchSourceResolutionSignalDecayQueueReport:
        raise ValueError(
            "report must be a ResearchSourceResolutionSignalDecayQueueReport",
        )
    return ResearchSourceResolutionSignalDecayQueueReport(
        **_dataclass_field_values(report),
    )


def _validate_public_payload(payload: dict[str, Any]) -> None:
    _validate_payload_schema(payload)
    _validate_payload_flags(payload)
    _validate_payload_statuses(payload)
    _validate_payload_decimal_strings(payload)
    _validate_payload_digest(payload)


def _validate_payload_schema(payload: dict[str, Any]) -> None:
    _require_payload_schema_keys(
        "payload",
        payload,
        _dataclass_schema_keys(ResearchSourceResolutionSignalDecayQueueReport),
    )
    _require_payload_string_list("reason_codes", payload["reason_codes"])
    _require_payload_schema_keys(
        "config",
        payload["config"],
        _dataclass_schema_keys(ResearchSourceResolutionSignalDecayQueueConfig),
    )
    _validate_payload_object_list(
        "reason_code_counts",
        payload["reason_code_counts"],
        _dataclass_schema_keys(ResearchSourceResolutionSignalDecayQueueReasonCodeCount),
    )
    for item in payload["reason_code_counts"]:
        _require_payload_string("reason_code", item["reason_code"])
    _validate_payload_object_list(
        "rows",
        payload["rows"],
        _dataclass_schema_keys(ResearchSourceResolutionSignalDecayQueueRow),
    )
    for item in payload["rows"]:
        _require_payload_string_list("row reason_codes", item["reason_codes"])


def _validate_payload_object_list(
    name: str,
    values: object,
    expected_keys: tuple[str, ...],
) -> None:
    if type(values) is not list:
        raise ValueError(f"{name} schema must be a canonical list")
    for item in values:
        _require_payload_schema_keys(name, item, expected_keys)


def _require_payload_schema_keys(
    name: str,
    value: object,
    expected_keys: tuple[str, ...],
) -> None:
    if type(value) is not dict:
        raise ValueError(f"{name} schema must be a canonical object")
    if tuple(value.keys()) != expected_keys:
        raise ValueError(f"{name} schema key order must be canonical")


def _report_from_payload(
    payload: dict[str, Any],
) -> ResearchSourceResolutionSignalDecayQueueReport:
    return ResearchSourceResolutionSignalDecayQueueReport(
        generated_at=_datetime_from_payload("generated_at", payload["generated_at"]),
        config_version=_require_payload_string(
            "config_version",
            payload["config_version"],
        ),
        config=_config_from_payload(payload["config"]),
        status=_require_payload_string("status", payload["status"]),
        queue_action=_require_payload_string("queue_action", payload["queue_action"]),
        queue_item_count=_decimal_from_payload(
            "queue_item_count",
            payload["queue_item_count"],
        ),
        pass_count=_decimal_from_payload("pass_count", payload["pass_count"]),
        watch_count=_decimal_from_payload("watch_count", payload["watch_count"]),
        block_count=_decimal_from_payload("block_count", payload["block_count"]),
        average_signal_decay_score=_decimal_from_payload(
            "average_signal_decay_score",
            payload["average_signal_decay_score"],
        ),
        max_signal_decay_score=_decimal_from_payload(
            "max_signal_decay_score",
            payload["max_signal_decay_score"],
        ),
        max_latest_verification_age_hours=_decimal_from_payload(
            "max_latest_verification_age_hours",
            payload["max_latest_verification_age_hours"],
        ),
        min_extraction_confidence=_decimal_from_payload(
            "min_extraction_confidence",
            payload["min_extraction_confidence"],
        ),
        reason_codes=_string_tuple_from_payload(
            "reason_codes",
            payload["reason_codes"],
        ),
        reason_code_counts=tuple(
            _reason_code_count_from_payload(item)
            for item in payload["reason_code_counts"]
        ),
        rows=tuple(_row_from_payload(item) for item in payload["rows"]),
        derived_validation_digest=_require_payload_string(
            "derived_validation_digest",
            payload["derived_validation_digest"],
        ),
        paper_only=_bool_from_payload("paper_only", payload["paper_only"]),
        report_only=_bool_from_payload("report_only", payload["report_only"]),
        readonly=_bool_from_payload("readonly", payload["readonly"]),
    )


def _config_from_payload(
    payload: dict[str, Any],
) -> ResearchSourceResolutionSignalDecayQueueConfig:
    return ResearchSourceResolutionSignalDecayQueueConfig(
        config_version=_require_payload_string("config_version", payload["config_version"]),
        watch_score_threshold=_decimal_from_payload(
            "watch_score_threshold",
            payload["watch_score_threshold"],
        ),
        block_score_threshold=_decimal_from_payload(
            "block_score_threshold",
            payload["block_score_threshold"],
        ),
        max_watch_verification_age_hours=_decimal_from_payload(
            "max_watch_verification_age_hours",
            payload["max_watch_verification_age_hours"],
        ),
        deadline_proximity_window_hours=_decimal_from_payload(
            "deadline_proximity_window_hours",
            payload["deadline_proximity_window_hours"],
        ),
        min_pass_corroboration_depth=_decimal_from_payload(
            "min_pass_corroboration_depth",
            payload["min_pass_corroboration_depth"],
        ),
        authority_tier_weight=_decimal_from_payload(
            "authority_tier_weight",
            payload["authority_tier_weight"],
        ),
        latest_verification_age_weight=_decimal_from_payload(
            "latest_verification_age_weight",
            payload["latest_verification_age_weight"],
        ),
        contradiction_pressure_weight=_decimal_from_payload(
            "contradiction_pressure_weight",
            payload["contradiction_pressure_weight"],
        ),
        corroboration_depth_weight=_decimal_from_payload(
            "corroboration_depth_weight",
            payload["corroboration_depth_weight"],
        ),
        extraction_confidence_weight=_decimal_from_payload(
            "extraction_confidence_weight",
            payload["extraction_confidence_weight"],
        ),
        deadline_proximity_weight=_decimal_from_payload(
            "deadline_proximity_weight",
            payload["deadline_proximity_weight"],
        ),
        paper_only=_bool_from_payload("paper_only", payload["paper_only"]),
        report_only=_bool_from_payload("report_only", payload["report_only"]),
        readonly=_bool_from_payload("readonly", payload["readonly"]),
    )


def _reason_code_count_from_payload(
    payload: dict[str, Any],
) -> ResearchSourceResolutionSignalDecayQueueReasonCodeCount:
    return ResearchSourceResolutionSignalDecayQueueReasonCodeCount(
        reason_code=_require_payload_string("reason_code", payload["reason_code"]),
        count=_decimal_from_payload("count", payload["count"]),
        queue_ratio=_decimal_from_payload("queue_ratio", payload["queue_ratio"]),
        paper_only=_bool_from_payload("paper_only", payload["paper_only"]),
        report_only=_bool_from_payload("report_only", payload["report_only"]),
        readonly=_bool_from_payload("readonly", payload["readonly"]),
    )


def _row_from_payload(
    payload: dict[str, Any],
) -> ResearchSourceResolutionSignalDecayQueueRow:
    return ResearchSourceResolutionSignalDecayQueueRow(
        scope_label=_require_payload_string("scope_label", payload["scope_label"]),
        queue_status=_require_payload_string("queue_status", payload["queue_status"]),
        generated_at=_datetime_from_payload("generated_at", payload["generated_at"]),
        latest_verified_at=_datetime_from_payload(
            "latest_verified_at",
            payload["latest_verified_at"],
        ),
        latest_verification_age_hours=_decimal_from_payload(
            "latest_verification_age_hours",
            payload["latest_verification_age_hours"],
        ),
        deadline_at=_datetime_from_payload("deadline_at", payload["deadline_at"]),
        deadline_proximity_hours=_decimal_from_payload(
            "deadline_proximity_hours",
            payload["deadline_proximity_hours"],
        ),
        authority_tier=_require_payload_string(
            "authority_tier",
            payload["authority_tier"],
        ),
        authority_tier_score=_decimal_from_payload(
            "authority_tier_score",
            payload["authority_tier_score"],
        ),
        authority_decay_score=_decimal_from_payload(
            "authority_decay_score",
            payload["authority_decay_score"],
        ),
        verification_age_score=_decimal_from_payload(
            "verification_age_score",
            payload["verification_age_score"],
        ),
        contradiction_pressure=_decimal_from_payload(
            "contradiction_pressure",
            payload["contradiction_pressure"],
        ),
        corroboration_depth=_decimal_from_payload(
            "corroboration_depth",
            payload["corroboration_depth"],
        ),
        corroboration_gap_score=_decimal_from_payload(
            "corroboration_gap_score",
            payload["corroboration_gap_score"],
        ),
        extraction_confidence=_decimal_from_payload(
            "extraction_confidence",
            payload["extraction_confidence"],
        ),
        extraction_confidence_gap_score=_decimal_from_payload(
            "extraction_confidence_gap_score",
            payload["extraction_confidence_gap_score"],
        ),
        deadline_proximity_score=_decimal_from_payload(
            "deadline_proximity_score",
            payload["deadline_proximity_score"],
        ),
        signal_decay_score=_decimal_from_payload(
            "signal_decay_score",
            payload["signal_decay_score"],
        ),
        reason_codes=_string_tuple_from_payload(
            "reason_codes",
            payload["reason_codes"],
        ),
        paper_only=_bool_from_payload("paper_only", payload["paper_only"]),
        report_only=_bool_from_payload("report_only", payload["report_only"]),
        readonly=_bool_from_payload("readonly", payload["readonly"]),
    )


def _dataclass_schema_keys(cls: type[object]) -> tuple[str, ...]:
    return tuple(field.name for field in fields(cls))


def _dataclass_field_values(value: object) -> dict[str, object]:
    if not is_dataclass(value) or isinstance(value, type):
        raise ValueError("value must be a dataclass instance")
    return {field.name: getattr(value, field.name) for field in fields(value)}


def _decimal_from_payload(name: str, value: object) -> Decimal:
    if type(value) is not str or not PUBLIC_DECIMAL_RE.fullmatch(value):
        raise ValueError(f"{name} must be a Decimal-derived string")
    return Decimal(value)


def _datetime_from_payload(name: str, value: object) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{name} must be an ISO-8601 datetime string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be an ISO-8601 datetime string") from exc
    return _as_utc(name, parsed)


def _require_payload_string(name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    return value


def _require_payload_string_list(name: str, values: object) -> tuple[str, ...]:
    return _string_tuple_from_payload(name, values)


def _string_tuple_from_payload(name: str, values: object) -> tuple[str, ...]:
    if type(values) is not list:
        raise ValueError(f"{name} must be a canonical list")
    return tuple(_require_payload_string(name, value) for value in values)


def _bool_from_payload(name: str, value: object) -> bool:
    return _require_bool(name, value)


def _validate_payload_flags(payload: dict[str, Any]) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if payload.get(flag_name) is not True:
            raise ValueError(f"{flag_name} must be True")
    _validate_nested_payload_flags(payload)


def _validate_nested_payload_flags(value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if key in {"paper_only", "report_only", "readonly"} and item is not True:
                raise ValueError(f"{key} must be True")
            _validate_nested_payload_flags(item)
        return
    if isinstance(value, list):
        for item in value:
            _validate_nested_payload_flags(item)


def _validate_payload_statuses(value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if key in {"status", "queue_status"} and item not in (
                "pass",
                "watch",
                "block",
            ):
                raise ValueError("status must be pass, watch, or block")
            _validate_payload_statuses(item)
        return
    if isinstance(value, list):
        for item in value:
            _validate_payload_statuses(item)


def _validate_payload_decimal_strings(value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if key in PUBLIC_DECIMAL_KEYS:
                if type(item) is not str or not PUBLIC_DECIMAL_RE.fullmatch(item):
                    raise ValueError(f"{key} must be a Decimal-derived string")
                _require_nonnegative_decimal(key, Decimal(item))
            _validate_payload_decimal_strings(item)
        return
    if isinstance(value, list):
        for item in value:
            _validate_payload_decimal_strings(item)


def _validate_payload_digest(payload: dict[str, Any]) -> None:
    digest = payload.get("derived_validation_digest")
    if type(digest) is not str or not DIGEST_RE.fullmatch(digest):
        raise ValueError("derived_validation_digest must be a SHA-256 hex digest")
    expected = _payload_digest(payload)
    if digest != expected:
        raise ValueError("derived_validation_digest does not match payload")


def _report_values_without_digest(
    report: ResearchSourceResolutionSignalDecayQueueReport,
) -> dict[str, object]:
    values = asdict(report)
    values.pop("derived_validation_digest")
    return values


def _report_digest_from_values(values: Mapping[str, object]) -> str:
    ready = _json_ready(dict(values))
    if type(ready) is not dict:
        raise ValueError("report values must produce a JSON object")
    return _payload_digest(ready)


def _payload_digest(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest", None)
    encoded = json.dumps(
        unsigned,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    *,
    allow_json_containers: bool = False,
) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(
            label,
            asdict(value),
            allow_json_containers=allow_json_containers,
        )
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            if _has_unsafe_public_key(key):
                raise ValueError(f"unsafe public payload key in {label}")
            _reject_unsafe_public_payload(
                label,
                item,
                allow_json_containers=allow_json_containers,
            )
        return
    if isinstance(value, (list, tuple)):
        if not allow_json_containers and not isinstance(value, tuple):
            raise ValueError(f"{label} public payload containers must be tuples")
        for item in value:
            _reject_unsafe_public_payload(
                label,
                item,
                allow_json_containers=allow_json_containers,
            )
        return
    if type(value) is str and _has_unsafe_public_value(value):
        raise ValueError(f"unsafe public payload value in {label}")


def _has_unsafe_public_key(value: str) -> bool:
    normalized = value.lower()
    return normalized in UNSAFE_PUBLIC_KEYS or any(
        fragment in normalized for fragment in UNSAFE_PUBLIC_KEY_FRAGMENTS
    )


def _has_unsafe_public_value(value: str) -> bool:
    normalized = value.lower()
    return any(fragment in normalized for fragment in UNSAFE_PUBLIC_VALUE_FRAGMENTS)


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_public_label(name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not PUBLIC_LABEL_RE.fullmatch(value):
        raise ValueError(f"{name} must be a public label")
    if _has_unsafe_public_value(value):
        raise ValueError(f"{name} must not expose unsafe public surfaces")
    return value


def _require_authority_tier(name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if value not in SOURCE_RESOLUTION_AUTHORITY_TIERS:
        raise ValueError(f"{name} must be a supported authority tier")
    return value


def _require_status(name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if value not in SOURCE_RESOLUTION_SIGNAL_DECAY_QUEUE_STATUSES:
        raise ValueError(f"{name} must be pass, watch, or block")
    return value


def _require_reason_code(name: str, value: object, allowed: tuple[str, ...]) -> str:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if value not in allowed:
        raise ValueError(f"{name} must be supported")
    return value


def _require_reason_codes(
    name: str,
    values: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{name} must be a tuple")
    normalized = tuple(_require_reason_code(name, value, allowed) for value in values)
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{name} must be unique")
    return tuple(reason for reason in allowed if reason in set(normalized))


def _require_hard_flags(label: str, value: object) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        flag = getattr(value, flag_name, None)
        if flag is not True:
            raise ValueError(f"{label} {flag_name} must be True")
        _require_bool(flag_name, flag)


def _require_bool(name: str, value: object) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{name} must be a bool")
    return value


def _require_digest(name: str, value: object) -> str:
    if type(value) is not str or not DIGEST_RE.fullmatch(value):
        raise ValueError(f"{name} must be a SHA-256 hex digest")
    return value


def _require_raw_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    return value


def _require_decimal(name: str, value: object) -> Decimal:
    return _quantize(_require_raw_decimal(name, value))


def _require_nonnegative_decimal(name: str, value: object) -> Decimal:
    decimal_value = _require_raw_decimal(name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return _quantize(decimal_value)


def _require_nonnegative_count_decimal(name: str, value: object) -> Decimal:
    decimal_value = _require_raw_decimal(name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    with localcontext(DECIMAL_CONTEXT):
        integral_value = decimal_value.to_integral_value()
    if decimal_value != integral_value:
        raise ValueError(f"{name} must be a whole-number Decimal")
    return _quantize(decimal_value)


def _require_positive_count_decimal(name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_count_decimal(name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{name} must be positive")
    return decimal_value


def _require_ratio_decimal(name: str, value: object) -> Decimal:
    decimal_value = _require_raw_decimal(name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{name} must be between 0.000000 and 1.000000")
    return _quantize(decimal_value)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        quantized = value.quantize(QUANTUM)
    if quantized == ZERO:
        return ZERO
    return quantized


def _clamp_ratio(value: Decimal) -> Decimal:
    return min(max(_quantize(value), ZERO), ONE)


def _safe_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(numerator / denominator)


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(sum(values, ZERO) / _decimal_count(len(values)))


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count must be a nonnegative int")
    return _quantize(Decimal(value))


def _as_utc(name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _duration_hours(start: datetime, end: datetime) -> Decimal:
    seconds = _timedelta_total_seconds_decimal(end - start)
    if seconds < ZERO:
        raise ValueError("duration must be nonnegative")
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(seconds / SECONDS_PER_HOUR)


def _future_duration_hours(start: datetime, end: datetime) -> Decimal:
    seconds = _timedelta_total_seconds_decimal(end - start)
    if seconds <= ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(seconds / SECONDS_PER_HOUR)


def _timedelta_total_seconds_decimal(value: timedelta) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return (
            (Decimal(value.days) * SECONDS_PER_DAY)
            + Decimal(value.seconds)
            + (Decimal(value.microseconds) / MICROSECONDS_PER_SECOND)
        )


def _json_ready(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must be exactly Decimal")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(_quantize(value))
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("JSON datetime value must be exactly datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if type(value) is bool:
        return value
    if type(value) is int:
        raise ValueError("JSON numeric values must use Decimal-derived strings")
    if type(value) is float:
        raise ValueError("JSON value must not be a float")
    if type(value) is str:
        if _has_unsafe_public_value(value):
            raise ValueError("JSON string exposes unsafe public surfaces")
        return value
    if type(value) is dict:
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            if _has_unsafe_public_key(key):
                raise ValueError("JSON object key exposes unsafe public surfaces")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _public_dataclass_names() -> tuple[str, ...]:
    return tuple(
        name
        for name, value in globals().items()
        if name.startswith("ResearchSourceResolutionSignalDecay")
        and isinstance(value, type)
        and is_dataclass(value)
    )


def _assert_public_dataclass_flags() -> None:
    for name in _public_dataclass_names():
        cls = globals()[name]
        field_names = {field.name for field in fields(cls)}
        if {"paper_only", "report_only", "readonly"} - field_names:
            raise RuntimeError(f"{name} must expose hard report-only flags")


_assert_public_dataclass_flags()
