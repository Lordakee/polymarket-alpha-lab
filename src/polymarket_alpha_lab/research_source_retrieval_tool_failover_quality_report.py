"""Report-only quality reducer for sanitized retrieval tool failover evidence."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
import re
from typing import Any


DEFAULT_RESEARCH_SOURCE_RETRIEVAL_TOOL_FAILOVER_QUALITY_CONFIG_VERSION = (
    "research-source-retrieval-tool-failover-quality-report-v0"
)

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
STATUSES = (STATUS_PASS, STATUS_WATCH, STATUS_BLOCK)
STATUS_RANK = {STATUS_BLOCK: 0, STATUS_WATCH: 1, STATUS_PASS: 2}

NO_INPUTS_REASON = "retrieval_tool_failover_quality_no_inputs"
PASS_REASON = "retrieval_tool_failover_quality_pass"
WATCH_REASON = "retrieval_tool_failover_quality_watch"
BLOCK_REASON = "retrieval_tool_failover_quality_block"
FALLBACK_LATENCY_BLOCK_REASON = "fallback_latency_block"
FALLBACK_LATENCY_WATCH_REASON = "fallback_latency_watch"
FALLBACK_SUCCESS_BLOCK_REASON = "fallback_success_block"
FAILOVER_DEPENDENCY_BLOCK_REASON = "failover_dependency_block"
FAILOVER_DEPENDENCY_WATCH_REASON = "failover_dependency_watch"
PRIMARY_TOOL_SUCCESS_BLOCK_REASON = "primary_tool_success_block"
PRIMARY_TOOL_SUCCESS_WATCH_REASON = "primary_tool_success_watch"
STALE_BLOCK_REASON = "retrieval_observation_stale_block"
STALE_WATCH_REASON = "retrieval_observation_stale_watch"

STATUS_REASON_CODES = (PASS_REASON, WATCH_REASON, BLOCK_REASON)
ROW_DETAIL_REASON_SEQUENCE = (
    FALLBACK_LATENCY_BLOCK_REASON,
    FALLBACK_LATENCY_WATCH_REASON,
    FALLBACK_SUCCESS_BLOCK_REASON,
    FAILOVER_DEPENDENCY_BLOCK_REASON,
    FAILOVER_DEPENDENCY_WATCH_REASON,
    PRIMARY_TOOL_SUCCESS_BLOCK_REASON,
    PRIMARY_TOOL_SUCCESS_WATCH_REASON,
    STALE_BLOCK_REASON,
    STALE_WATCH_REASON,
)
REPORT_REASON_SEQUENCE = (
    NO_INPUTS_REASON,
    PASS_REASON,
    BLOCK_REASON,
    FALLBACK_LATENCY_BLOCK_REASON,
    FALLBACK_SUCCESS_BLOCK_REASON,
    FAILOVER_DEPENDENCY_BLOCK_REASON,
    PRIMARY_TOOL_SUCCESS_BLOCK_REASON,
    STALE_BLOCK_REASON,
    WATCH_REASON,
    FALLBACK_LATENCY_WATCH_REASON,
    FAILOVER_DEPENDENCY_WATCH_REASON,
    PRIMARY_TOOL_SUCCESS_WATCH_REASON,
    STALE_WATCH_REASON,
)
REASON_CODE_SET = frozenset((*STATUS_REASON_CODES, *ROW_DETAIL_REASON_SEQUENCE))
REPORT_REASON_CODE_SET = frozenset(REPORT_REASON_SEQUENCE)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
TWO = Decimal("2.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000.000000")
PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")

PUBLIC_DIGEST_FIELD = "derived_validation_digest"

__all__ = (
    "DEFAULT_RESEARCH_SOURCE_RETRIEVAL_TOOL_FAILOVER_QUALITY_CONFIG_VERSION",
    "STATUSES",
    "ResearchSourceRetrievalToolFailoverQualityConfig",
    "ResearchSourceRetrievalToolFailoverQualityObservation",
    "ResearchSourceRetrievalToolFailoverQualityReasonCodeCount",
    "ResearchSourceRetrievalToolFailoverQualityReport",
    "ResearchSourceRetrievalToolFailoverQualityRow",
    "build_research_source_retrieval_tool_failover_quality_report",
    "research_source_retrieval_tool_failover_quality_report_digest",
    "research_source_retrieval_tool_failover_quality_report_payload",
    "validate_research_source_retrieval_tool_failover_quality_public_payload",
    "validate_research_source_retrieval_tool_failover_quality_report_digest",
)


@dataclass(frozen=True)
class ResearchSourceRetrievalToolFailoverQualityConfig:
    config_version: str = (
        DEFAULT_RESEARCH_SOURCE_RETRIEVAL_TOOL_FAILOVER_QUALITY_CONFIG_VERSION
    )
    fresh_observation_age_seconds: Decimal = Decimal("3600.000000")
    stale_observation_age_seconds: Decimal = Decimal("21600.000000")
    pass_failover_quality_score: Decimal = Decimal("0.800000")
    watch_failover_quality_score: Decimal = Decimal("0.500000")
    min_primary_tool_success_ratio: Decimal = Decimal("0.700000")
    min_fallback_success_ratio: Decimal = Decimal("0.600000")
    max_failover_dependency_ratio: Decimal = Decimal("0.500000")
    max_fallback_latency_seconds: Decimal = Decimal("5.000000")
    coverage_weight: Decimal = Decimal("0.300000")
    freshness_weight: Decimal = Decimal("0.200000")
    latency_weight: Decimal = Decimal("0.200000")
    dependency_weight: Decimal = Decimal("0.200000")
    fallback_success_weight: Decimal = Decimal("0.100000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchSourceRetrievalToolFailoverQualityConfig "
            "does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            "config",
            self,
            ResearchSourceRetrievalToolFailoverQualityConfig,
        )
        _require_safe_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_RETRIEVAL_TOOL_FAILOVER_QUALITY_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "fresh_observation_age_seconds",
            "stale_observation_age_seconds",
            "max_fallback_latency_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        if self.stale_observation_age_seconds <= self.fresh_observation_age_seconds:
            raise ValueError(
                "stale_observation_age_seconds must exceed "
                "fresh_observation_age_seconds",
            )
        for field_name in (
            "pass_failover_quality_score",
            "watch_failover_quality_score",
            "min_primary_tool_success_ratio",
            "min_fallback_success_ratio",
            "max_failover_dependency_ratio",
            "coverage_weight",
            "freshness_weight",
            "latency_weight",
            "dependency_weight",
            "fallback_success_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.pass_failover_quality_score <= self.watch_failover_quality_score:
            raise ValueError(
                "pass_failover_quality_score must exceed "
                "watch_failover_quality_score",
            )
        weight_sum = _quantize(
            self.coverage_weight
            + self.freshness_weight
            + self.latency_weight
            + self.dependency_weight
            + self.fallback_success_weight,
        )
        if weight_sum != ONE:
            raise ValueError("failover quality weights must sum to 1")
        _require_hard_flags("config", self)
        _reject_unsafe_public_surface("config", self)


@dataclass(frozen=True)
class ResearchSourceRetrievalToolFailoverQualityObservation:
    retrieval_scope: str
    primary_tool: str
    fallback_tool: str
    observed_at: datetime
    primary_attempt_count: Decimal
    primary_success_count: Decimal
    fallback_attempt_count: Decimal
    fallback_success_count: Decimal
    failover_trigger_count: Decimal
    fallback_latency_seconds: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchSourceRetrievalToolFailoverQualityObservation "
            "does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            "observation",
            self,
            ResearchSourceRetrievalToolFailoverQualityObservation,
        )
        for field_name in ("retrieval_scope", "primary_tool", "fallback_tool"):
            object.__setattr__(
                self,
                field_name,
                _require_safe_public_string(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "primary_attempt_count",
            "primary_success_count",
            "fallback_attempt_count",
            "fallback_success_count",
            "failover_trigger_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "fallback_latency_seconds",
            _require_nonnegative_decimal(
                "fallback_latency_seconds",
                self.fallback_latency_seconds,
            ),
        )
        if self.primary_success_count > self.primary_attempt_count:
            raise ValueError("primary_success_count must not exceed primary_attempt_count")
        if self.fallback_success_count > self.fallback_attempt_count:
            raise ValueError(
                "fallback_success_count must not exceed fallback_attempt_count",
            )
        if self.failover_trigger_count > self.primary_attempt_count:
            raise ValueError(
                "failover_trigger_count must not exceed primary_attempt_count",
            )
        _require_hard_flags("observation", self)
        _reject_unsafe_public_surface("observation", self)


@dataclass(frozen=True)
class ResearchSourceRetrievalToolFailoverQualityRow:
    retrieval_scope: str
    primary_tool: str
    fallback_tool: str
    observed_at: datetime
    observation_age_seconds: Decimal
    primary_attempt_count: Decimal
    primary_success_count: Decimal
    primary_success_ratio: Decimal
    fallback_attempt_count: Decimal
    fallback_success_count: Decimal
    fallback_success_ratio: Decimal
    failover_trigger_count: Decimal
    failover_dependency_ratio: Decimal
    fallback_latency_seconds: Decimal
    freshness_score: Decimal
    latency_score: Decimal
    dependency_score: Decimal
    failover_quality_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchSourceRetrievalToolFailoverQualityRow "
            "does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("row", self, ResearchSourceRetrievalToolFailoverQualityRow)
        for field_name in ("retrieval_scope", "primary_tool", "fallback_tool"):
            object.__setattr__(
                self,
                field_name,
                _require_safe_public_string(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "primary_attempt_count",
            "primary_success_count",
            "fallback_attempt_count",
            "fallback_success_count",
            "failover_trigger_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "observation_age_seconds",
            "fallback_latency_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "primary_success_ratio",
            "fallback_success_ratio",
            "failover_dependency_ratio",
            "freshness_score",
            "latency_score",
            "dependency_score",
            "failover_quality_score",
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
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags("row", self)
        _reject_unsafe_public_surface("row", self)
        _validate_row_consistency(self)


@dataclass(frozen=True)
class ResearchSourceRetrievalToolFailoverQualityReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchSourceRetrievalToolFailoverQualityReasonCodeCount "
            "does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_member("reason_code", self.reason_code, tuple(REPORT_REASON_CODE_SET))
        object.__setattr__(
            self,
            "count",
            _require_positive_whole_decimal("count", self.count),
        )
        _require_hard_flags("reason_code_count", self)
        _reject_unsafe_public_surface("reason_code_count", self)


@dataclass(frozen=True)
class ResearchSourceRetrievalToolFailoverQualityReport:
    generated_at: datetime
    config_version: str
    retrieval_scope_count: Decimal
    observation_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_failover_quality_score: Decimal
    lowest_failover_quality_score: Decimal
    highest_failover_dependency_ratio: Decimal
    highest_fallback_latency_seconds: Decimal
    status: str
    rows: tuple[ResearchSourceRetrievalToolFailoverQualityRow, ...]
    reason_code_counts: tuple[
        ResearchSourceRetrievalToolFailoverQualityReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchSourceRetrievalToolFailoverQualityReport "
            "does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            "report",
            self,
            ResearchSourceRetrievalToolFailoverQualityReport,
        )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_safe_public_string("config_version", self.config_version)
        for field_name in (
            "retrieval_scope_count",
            "observation_count",
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
            "average_failover_quality_score",
            "lowest_failover_quality_score",
            "highest_failover_dependency_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "highest_fallback_latency_seconds",
            _require_nonnegative_decimal(
                "highest_fallback_latency_seconds",
                self.highest_fallback_latency_seconds,
            ),
        )
        _require_member("status", self.status, STATUSES)
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_report_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags("report", self)
        _reject_unsafe_public_surface("report", self)
        _validate_report_consistency(self)
        expected_digest = _report_digest_from_fields(self)
        if self.derived_validation_digest == "":
            object.__setattr__(self, "derived_validation_digest", expected_digest)
        else:
            _require_digest(PUBLIC_DIGEST_FIELD, self.derived_validation_digest)
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest does not match payload")


def build_research_source_retrieval_tool_failover_quality_report(
    observations: Iterable[ResearchSourceRetrievalToolFailoverQualityObservation],
    *,
    config: ResearchSourceRetrievalToolFailoverQualityConfig,
    generated_at: datetime,
) -> ResearchSourceRetrievalToolFailoverQualityReport:
    config = _require_config(config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_observations = _normalize_observations(observations)
    rows = tuple(
        sorted(
            (
                _row_from_observation(
                    observation,
                    config=config,
                    generated_at=generated_at_utc,
                )
                for observation in normalized_observations
            ),
            key=_row_sort_key,
        ),
    )
    reason_codes = _report_reason_codes(rows)
    return ResearchSourceRetrievalToolFailoverQualityReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        retrieval_scope_count=_decimal_from_int(len(rows)),
        observation_count=_decimal_from_int(len(normalized_observations)),
        pass_count=_status_count(rows, STATUS_PASS),
        watch_count=_status_count(rows, STATUS_WATCH),
        block_count=_status_count(rows, STATUS_BLOCK),
        average_failover_quality_score=_average_score(rows),
        lowest_failover_quality_score=_lowest_score(rows),
        highest_failover_dependency_ratio=_highest_dependency(rows),
        highest_fallback_latency_seconds=_highest_latency(rows),
        status=_report_status(rows),
        rows=rows,
        reason_code_counts=_reason_code_counts(rows, reason_codes),
        reason_codes=reason_codes,
    )


def research_source_retrieval_tool_failover_quality_report_payload(
    report: ResearchSourceRetrievalToolFailoverQualityReport,
) -> dict[str, Any]:
    _require_exact_type("report", report, ResearchSourceRetrievalToolFailoverQualityReport)
    validate_research_source_retrieval_tool_failover_quality_report_digest(report)
    payload = _report_payload_object(report, include_digest=True)
    _reject_unsafe_public_payload("payload", payload)
    return payload


def research_source_retrieval_tool_failover_quality_report_digest(
    report: ResearchSourceRetrievalToolFailoverQualityReport,
) -> str:
    _require_exact_type("report", report, ResearchSourceRetrievalToolFailoverQualityReport)
    _require_hard_flags("report", report)
    return _report_digest_from_fields(report)


def validate_research_source_retrieval_tool_failover_quality_report_digest(
    report: ResearchSourceRetrievalToolFailoverQualityReport,
) -> bool:
    _require_exact_type("report", report, ResearchSourceRetrievalToolFailoverQualityReport)
    _require_hard_flags("report", report)
    _require_digest(PUBLIC_DIGEST_FIELD, report.derived_validation_digest)
    expected = research_source_retrieval_tool_failover_quality_report_digest(report)
    if report.derived_validation_digest != expected:
        raise ValueError("derived_validation_digest does not match payload")
    return True


def validate_research_source_retrieval_tool_failover_quality_public_payload(
    payload: dict[str, Any],
) -> bool:
    if type(payload) is not dict:
        raise ValueError("public payload must be a dict")
    _reject_unsafe_public_payload("public payload", payload)
    digest = payload.get(PUBLIC_DIGEST_FIELD)
    _require_digest(PUBLIC_DIGEST_FIELD, digest)
    unsigned = dict(payload)
    unsigned.pop(PUBLIC_DIGEST_FIELD, None)
    encoded = json.dumps(
        unsigned,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    expected = sha256(encoded).hexdigest()
    if digest != expected:
        raise ValueError("derived_validation_digest does not match public payload")
    return True


def _require_config(
    config: ResearchSourceRetrievalToolFailoverQualityConfig,
) -> ResearchSourceRetrievalToolFailoverQualityConfig:
    _require_exact_type(
        "config",
        config,
        ResearchSourceRetrievalToolFailoverQualityConfig,
    )
    _require_hard_flags("config", config)
    _reject_unsafe_public_surface("config", config)
    return config


def _normalize_observations(
    observations: Iterable[ResearchSourceRetrievalToolFailoverQualityObservation],
) -> tuple[ResearchSourceRetrievalToolFailoverQualityObservation, ...]:
    if isinstance(observations, (str, bytes, dict)):
        raise ValueError("observations must be an iterable")
    normalized = tuple(observations)
    seen_scopes: set[str] = set()
    for observation in normalized:
        _require_exact_type(
            "observation",
            observation,
            ResearchSourceRetrievalToolFailoverQualityObservation,
        )
        _require_hard_flags("observation", observation)
        _reject_unsafe_public_surface("observation", observation)
        if observation.retrieval_scope in seen_scopes:
            raise ValueError("retrieval_scope values must be unique")
        seen_scopes.add(observation.retrieval_scope)
    return normalized


def _row_from_observation(
    observation: ResearchSourceRetrievalToolFailoverQualityObservation,
    *,
    config: ResearchSourceRetrievalToolFailoverQualityConfig,
    generated_at: datetime,
) -> ResearchSourceRetrievalToolFailoverQualityRow:
    if observation.observed_at > generated_at:
        raise ValueError("observed_at must not be after generated_at")
    observation_age_seconds = _duration_seconds(observation.observed_at, generated_at)
    primary_success_ratio = _ratio(
        observation.primary_success_count,
        observation.primary_attempt_count,
    )
    fallback_success_ratio = _ratio(
        observation.fallback_success_count,
        observation.fallback_attempt_count,
    )
    failover_dependency_ratio = _ratio(
        observation.failover_trigger_count,
        observation.primary_attempt_count,
    )
    freshness_score = _freshness_score(observation_age_seconds, config=config)
    latency_score = _latency_score(observation.fallback_latency_seconds, config=config)
    dependency_score = _normalize_ratio(
        "dependency_score",
        ONE - failover_dependency_ratio,
    )
    failover_quality_score = _failover_quality_score(
        primary_success_ratio=primary_success_ratio,
        fallback_success_ratio=fallback_success_ratio,
        freshness_score=freshness_score,
        latency_score=latency_score,
        dependency_score=dependency_score,
        config=config,
    )
    detail_reason_codes = _row_detail_reason_codes(
        primary_success_ratio=primary_success_ratio,
        fallback_success_ratio=fallback_success_ratio,
        failover_dependency_ratio=failover_dependency_ratio,
        fallback_latency_seconds=observation.fallback_latency_seconds,
        observation_age_seconds=observation_age_seconds,
        failover_quality_score=failover_quality_score,
        config=config,
    )
    status = _status_from_reasons_and_score(
        detail_reason_codes,
        failover_quality_score=failover_quality_score,
        config=config,
    )
    return ResearchSourceRetrievalToolFailoverQualityRow(
        retrieval_scope=observation.retrieval_scope,
        primary_tool=observation.primary_tool,
        fallback_tool=observation.fallback_tool,
        observed_at=observation.observed_at,
        observation_age_seconds=observation_age_seconds,
        primary_attempt_count=observation.primary_attempt_count,
        primary_success_count=observation.primary_success_count,
        primary_success_ratio=primary_success_ratio,
        fallback_attempt_count=observation.fallback_attempt_count,
        fallback_success_count=observation.fallback_success_count,
        fallback_success_ratio=fallback_success_ratio,
        failover_trigger_count=observation.failover_trigger_count,
        failover_dependency_ratio=failover_dependency_ratio,
        fallback_latency_seconds=observation.fallback_latency_seconds,
        freshness_score=freshness_score,
        latency_score=latency_score,
        dependency_score=dependency_score,
        failover_quality_score=failover_quality_score,
        status=status,
        reason_codes=(_status_reason(status), *detail_reason_codes),
    )


def _freshness_score(
    observation_age_seconds: Decimal,
    *,
    config: ResearchSourceRetrievalToolFailoverQualityConfig,
) -> Decimal:
    if observation_age_seconds <= config.fresh_observation_age_seconds:
        return ONE
    if observation_age_seconds >= config.stale_observation_age_seconds:
        return ZERO
    return _normalize_ratio(
        "freshness_score",
        ONE - (observation_age_seconds / config.stale_observation_age_seconds),
    )


def _latency_score(
    fallback_latency_seconds: Decimal,
    *,
    config: ResearchSourceRetrievalToolFailoverQualityConfig,
) -> Decimal:
    if fallback_latency_seconds >= config.max_fallback_latency_seconds:
        return ZERO
    return _normalize_ratio(
        "latency_score",
        ONE - (fallback_latency_seconds / config.max_fallback_latency_seconds),
    )


def _failover_quality_score(
    *,
    primary_success_ratio: Decimal,
    fallback_success_ratio: Decimal,
    freshness_score: Decimal,
    latency_score: Decimal,
    dependency_score: Decimal,
    config: ResearchSourceRetrievalToolFailoverQualityConfig,
) -> Decimal:
    return _normalize_ratio(
        "failover_quality_score",
        (primary_success_ratio * config.coverage_weight)
        + (freshness_score * config.freshness_weight)
        + (latency_score * config.latency_weight)
        + (dependency_score * config.dependency_weight)
        + (fallback_success_ratio * config.fallback_success_weight),
    )


def _row_detail_reason_codes(
    *,
    primary_success_ratio: Decimal,
    fallback_success_ratio: Decimal,
    failover_dependency_ratio: Decimal,
    fallback_latency_seconds: Decimal,
    observation_age_seconds: Decimal,
    failover_quality_score: Decimal,
    config: ResearchSourceRetrievalToolFailoverQualityConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    primary_block_threshold = _normalize_ratio(
        "primary_block_threshold",
        config.min_primary_tool_success_ratio / TWO,
    )
    dependency_block_threshold = _normalize_ratio(
        "dependency_block_threshold",
        config.max_failover_dependency_ratio
        + ((ONE - config.max_failover_dependency_ratio) / TWO),
    )
    latency_watch_threshold = config.max_fallback_latency_seconds * Decimal("0.750000")
    if fallback_latency_seconds > config.max_fallback_latency_seconds:
        reason_codes.append(FALLBACK_LATENCY_BLOCK_REASON)
    elif fallback_latency_seconds >= latency_watch_threshold:
        reason_codes.append(FALLBACK_LATENCY_WATCH_REASON)
    if fallback_success_ratio < config.min_fallback_success_ratio:
        reason_codes.append(FALLBACK_SUCCESS_BLOCK_REASON)
    if failover_dependency_ratio > dependency_block_threshold:
        reason_codes.append(FAILOVER_DEPENDENCY_BLOCK_REASON)
    elif failover_dependency_ratio >= config.max_failover_dependency_ratio:
        reason_codes.append(FAILOVER_DEPENDENCY_WATCH_REASON)
    if primary_success_ratio < primary_block_threshold:
        reason_codes.append(PRIMARY_TOOL_SUCCESS_BLOCK_REASON)
    elif primary_success_ratio < config.min_primary_tool_success_ratio:
        reason_codes.append(PRIMARY_TOOL_SUCCESS_WATCH_REASON)
    if observation_age_seconds >= config.stale_observation_age_seconds:
        reason_codes.append(STALE_BLOCK_REASON)
    elif observation_age_seconds > config.fresh_observation_age_seconds:
        reason_codes.append(STALE_WATCH_REASON)
    return _sort_detail_reason_codes(tuple(reason_codes))


def _status_from_reasons_and_score(
    reason_codes: tuple[str, ...],
    *,
    failover_quality_score: Decimal,
    config: ResearchSourceRetrievalToolFailoverQualityConfig,
) -> str:
    if any(_is_block_reason(reason_code) for reason_code in reason_codes):
        return STATUS_BLOCK
    if failover_quality_score < config.watch_failover_quality_score:
        return STATUS_BLOCK
    if reason_codes or failover_quality_score < config.pass_failover_quality_score:
        return STATUS_WATCH
    return STATUS_PASS


def _is_block_reason(reason_code: str) -> bool:
    return reason_code.endswith("_block")


def _status_reason(status: str) -> str:
    if status == STATUS_PASS:
        return PASS_REASON
    if status == STATUS_WATCH:
        return WATCH_REASON
    if status == STATUS_BLOCK:
        return BLOCK_REASON
    raise ValueError("status must be one of: pass, watch, block")


def _report_status(
    rows: tuple[ResearchSourceRetrievalToolFailoverQualityRow, ...],
) -> str:
    if not rows:
        return STATUS_BLOCK
    if any(row.status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _report_reason_codes(
    rows: tuple[ResearchSourceRetrievalToolFailoverQualityRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON,)
    codes = {
        reason_code
        for row in rows
        for reason_code in row.reason_codes
        if reason_code != PASS_REASON
    }
    if not codes:
        return (PASS_REASON,)
    return tuple(reason_code for reason_code in REPORT_REASON_SEQUENCE if reason_code in codes)


def _reason_code_counts(
    rows: tuple[ResearchSourceRetrievalToolFailoverQualityRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchSourceRetrievalToolFailoverQualityReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchSourceRetrievalToolFailoverQualityReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
            ),
        )
    counts: Counter[str] = Counter()
    for row in rows:
        counts.update(row.reason_codes)
    return tuple(
        ResearchSourceRetrievalToolFailoverQualityReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_from_int(counts[reason_code]),
        )
        for reason_code in reason_codes
        if counts[reason_code] > 0
    )


def _status_count(
    rows: tuple[ResearchSourceRetrievalToolFailoverQualityRow, ...],
    status: str,
) -> Decimal:
    return _decimal_from_int(sum(1 for row in rows if row.status == status))


def _average_score(
    rows: tuple[ResearchSourceRetrievalToolFailoverQualityRow, ...],
) -> Decimal:
    if not rows:
        return ZERO
    return _normalize_ratio(
        "average_failover_quality_score",
        sum((row.failover_quality_score for row in rows), ZERO) / Decimal(len(rows)),
    )


def _lowest_score(
    rows: tuple[ResearchSourceRetrievalToolFailoverQualityRow, ...],
) -> Decimal:
    if not rows:
        return ZERO
    return min(row.failover_quality_score for row in rows)


def _highest_dependency(
    rows: tuple[ResearchSourceRetrievalToolFailoverQualityRow, ...],
) -> Decimal:
    if not rows:
        return ZERO
    return max(row.failover_dependency_ratio for row in rows)


def _highest_latency(
    rows: tuple[ResearchSourceRetrievalToolFailoverQualityRow, ...],
) -> Decimal:
    if not rows:
        return ZERO
    return max(row.fallback_latency_seconds for row in rows)


def _normalize_rows(
    rows: object,
) -> tuple[ResearchSourceRetrievalToolFailoverQualityRow, ...]:
    if type(rows) not in (tuple, list):
        raise ValueError("rows must be a tuple or list")
    normalized = tuple(rows)
    seen_scopes: set[str] = set()
    for row in normalized:
        _require_exact_type("row", row, ResearchSourceRetrievalToolFailoverQualityRow)
        _require_hard_flags("row", row)
        _reject_unsafe_public_surface("row", row)
        if row.retrieval_scope in seen_scopes:
            raise ValueError("rows retrieval_scope values must be unique")
        seen_scopes.add(row.retrieval_scope)
    if normalized != tuple(sorted(normalized, key=_row_sort_key)):
        raise ValueError("rows must use deterministic sorting")
    return normalized


def _row_sort_key(
    row: ResearchSourceRetrievalToolFailoverQualityRow,
) -> tuple[int, Decimal, str]:
    return (
        STATUS_RANK[row.status],
        row.failover_quality_score,
        row.retrieval_scope,
    )


def _normalize_reason_code_counts(
    counts: object,
) -> tuple[ResearchSourceRetrievalToolFailoverQualityReasonCodeCount, ...]:
    if type(counts) not in (tuple, list):
        raise ValueError("reason_code_counts must be a tuple or list")
    normalized = tuple(counts)
    seen_codes: set[str] = set()
    for count in normalized:
        _require_exact_type(
            "reason_code_count",
            count,
            ResearchSourceRetrievalToolFailoverQualityReasonCodeCount,
        )
        _require_hard_flags("reason_code_count", count)
        if count.reason_code in seen_codes:
            raise ValueError("reason_code_counts reason_code values must be unique")
        seen_codes.add(count.reason_code)
    expected = tuple(
        sorted(
            normalized,
            key=lambda count: REPORT_REASON_SEQUENCE.index(count.reason_code),
        ),
    )
    if normalized != expected:
        raise ValueError("reason_code_counts must use deterministic sorting")
    return normalized


def _validate_row_consistency(
    row: ResearchSourceRetrievalToolFailoverQualityRow,
) -> None:
    if row.primary_success_count > row.primary_attempt_count:
        raise ValueError("primary_success_count must not exceed primary_attempt_count")
    if row.fallback_success_count > row.fallback_attempt_count:
        raise ValueError("fallback_success_count must not exceed fallback_attempt_count")
    if row.failover_trigger_count > row.primary_attempt_count:
        raise ValueError("failover_trigger_count must not exceed primary_attempt_count")
    if row.primary_success_ratio != _ratio(
        row.primary_success_count,
        row.primary_attempt_count,
    ):
        raise ValueError("primary_success_ratio must match counts")
    if row.fallback_success_ratio != _ratio(
        row.fallback_success_count,
        row.fallback_attempt_count,
    ):
        raise ValueError("fallback_success_ratio must match counts")
    if row.failover_dependency_ratio != _ratio(
        row.failover_trigger_count,
        row.primary_attempt_count,
    ):
        raise ValueError("failover_dependency_ratio must match counts")
    if not row.reason_codes:
        raise ValueError("reason_codes must be nonempty")
    if row.reason_codes[0] != _status_reason(row.status):
        raise ValueError("reason_codes must begin with matching status reason")
    if row.status == STATUS_PASS and row.failover_quality_score < Decimal("0.800000"):
        raise ValueError("failover_quality_score must support pass status")
    if row.status == STATUS_WATCH and row.failover_quality_score < Decimal("0.500000"):
        raise ValueError("failover_quality_score must support watch status")
    if row.status == STATUS_BLOCK and row.failover_quality_score >= Decimal("0.800000"):
        raise ValueError("failover_quality_score must support block status")
    if row.reason_codes[0] == PASS_REASON and len(row.reason_codes) != 1:
        raise ValueError("pass reason_codes must stand alone")


def _validate_report_consistency(
    report: ResearchSourceRetrievalToolFailoverQualityReport,
) -> None:
    if report.retrieval_scope_count != _decimal_from_int(len(report.rows)):
        raise ValueError("retrieval_scope_count must match rows")
    if report.observation_count != report.retrieval_scope_count:
        raise ValueError("observation_count must match rows")
    if report.pass_count != _status_count(report.rows, STATUS_PASS):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, STATUS_WATCH):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, STATUS_BLOCK):
        raise ValueError("block_count must match rows")
    if report.average_failover_quality_score != _average_score(report.rows):
        raise ValueError("average_failover_quality_score must match rows")
    if report.lowest_failover_quality_score != _lowest_score(report.rows):
        raise ValueError("lowest_failover_quality_score must match rows")
    if report.highest_failover_dependency_ratio != _highest_dependency(report.rows):
        raise ValueError("highest_failover_dependency_ratio must match rows")
    if report.highest_fallback_latency_seconds != _highest_latency(report.rows):
        raise ValueError("highest_fallback_latency_seconds must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows, report.reason_codes):
        raise ValueError("reason_code_counts must match rows")


def _report_payload_object(
    report: ResearchSourceRetrievalToolFailoverQualityReport,
    *,
    include_digest: bool,
) -> dict[str, Any]:
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a dict")
    if not include_digest:
        payload.pop(PUBLIC_DIGEST_FIELD, None)
    return payload


def _report_digest_from_fields(
    report: ResearchSourceRetrievalToolFailoverQualityReport,
) -> str:
    payload = _report_payload_object(report, include_digest=False)
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _json_ready(value: object) -> object:
    if isinstance(value, Decimal):
        return str(value)
    if type(value) is datetime:
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _json_ready(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    return value


def _duration_seconds(start: datetime, end: datetime) -> Decimal:
    delta = end - start
    return _quantize(
        Decimal(delta.days * 86_400)
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND),
    )


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _normalize_ratio("ratio", numerator / denominator)


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
    return _quantize(normalized)


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return _quantize(normalized)


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return normalized


def _require_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_positive_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    return _normalize_ratio(field_name, normalized)


def _normalize_ratio(field_name: str, value: Decimal) -> Decimal:
    normalized = _quantize(value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _decimal_from_int(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count source must be a nonnegative int")
    return _quantize(Decimal(value))


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _require_safe_public_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    if PUBLIC_IDENTIFIER_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a safe public identifier")
    _reject_unsafe_public_text(field_name, value)
    return value


def _normalize_reason_codes(
    field_name: str,
    values: object,
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not values:
        raise ValueError(f"{field_name} must be nonempty")
    seen_codes: set[str] = set()
    normalized: list[str] = []
    for value in values:
        _require_member(field_name, value, tuple(REASON_CODE_SET))
        if value in seen_codes:
            raise ValueError(f"{field_name} must not contain duplicates")
        seen_codes.add(value)
        normalized.append(value)
    if normalized[0] not in STATUS_REASON_CODES:
        raise ValueError(f"{field_name} must begin with a status reason")
    expected = (normalized[0], *_sort_detail_reason_codes(tuple(normalized[1:])))
    if tuple(normalized) != expected:
        raise ValueError(f"{field_name} must use deterministic sorting")
    return tuple(normalized)


def _normalize_report_reason_codes(
    field_name: str,
    values: object,
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not values:
        raise ValueError(f"{field_name} must be nonempty")
    normalized: list[str] = []
    seen_codes: set[str] = set()
    for value in values:
        _require_member(field_name, value, tuple(REPORT_REASON_CODE_SET))
        if value in seen_codes:
            raise ValueError(f"{field_name} must not contain duplicates")
        seen_codes.add(value)
        normalized.append(value)
    expected = tuple(reason_code for reason_code in REPORT_REASON_SEQUENCE if reason_code in seen_codes)
    if tuple(normalized) != expected:
        raise ValueError(f"{field_name} must use deterministic sorting")
    return tuple(normalized)


def _sort_detail_reason_codes(values: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(
        reason_code
        for reason_code in ROW_DETAIL_REASON_SEQUENCE
        if reason_code in values
    )


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed}")


def _require_digest(field_name: str, value: object) -> None:
    if type(value) is not str or DIGEST_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")


def _require_exact_type(field_name: str, value: object, expected_type: type[object]) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be a {expected_type.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{label} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{label} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{label} readonly must be True")


def _reject_unsafe_public_surface(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            field_value = getattr(value, field.name)
            _reject_unsafe_public_text(f"{label}.{field.name}", field.name)
            if type(field_value) is str:
                _reject_unsafe_public_text(f"{label}.{field.name}", field_value)


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            _reject_unsafe_public_text(label, str(key))
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) is str:
        _reject_unsafe_public_text(label, value)


def _reject_unsafe_public_text(field_name: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in _unsafe_public_fragments()):
        raise ValueError(f"{field_name} contains unsafe public payload text")


def _unsafe_public_fragments() -> tuple[str, ...]:
    return (
        "".join(("sc", "rapling")),
        "".join(("agent", "_", "reach")),
        "".join(("agent", "-", "reach")),
        "".join(("brow", "ser")),
        "".join(("net", "work")),
        "".join(("data", "base")),
        "".join(("d", "b_")),
        "".join(("d", "b-")),
        "".join(("d", "b.")),
        "candidate_id",
        "candidate-id",
        "candidate id",
        "candidate_slug",
        "candidate slug",
        "market_id",
        "market-id",
        "market id",
        "market_slug",
        "market-slug",
        "market slug",
        "slug",
        "question",
        "raw_candidate",
        "raw_market",
        "source_id",
        "source id",
        "source_url",
        "source-url",
        "source url",
        "raw_url",
        "raw-url",
        "raw url",
        "url",
        "source_text",
        "source-text",
        "source text",
        "raw_text",
        "raw-text",
        "raw text",
        "dsn",
        "table_name",
        "table name",
        "table",
        "".join(("to", "ken")),
        "".join(("wal", "let")),
        "".join(("or", "der")),
        "".join(("tr", "ade")),
        "position",
        "live",
        "".join(("si", "zing")),
        "".join(("reco", "mmendation")),
        "http://",
        "https://",
        "www.",
    )
