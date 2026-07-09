"""Report-only confidence reducer for sanitized multi-tool retrieval evidence."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
import re
from typing import Any


DEFAULT_RESEARCH_SOURCE_MULTI_TOOL_RETRIEVAL_CONFIDENCE_REPORT_CONFIG_VERSION = (
    "research-source-multi-tool-retrieval-confidence-report-v0"
)

TOOL_SCRAPLING = "scrapling"
TOOL_AGENT_REACH = "agent_reach"
TOOL_BROWSER_CAPTURE = "browser_capture"
TOOL_FALLBACK = "fallback"
RETRIEVAL_TOOLS = (
    TOOL_SCRAPLING,
    TOOL_AGENT_REACH,
    TOOL_BROWSER_CAPTURE,
    TOOL_FALLBACK,
)
CORE_RETRIEVAL_TOOLS = (
    TOOL_SCRAPLING,
    TOOL_AGENT_REACH,
    TOOL_BROWSER_CAPTURE,
)

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
STATUSES = (STATUS_PASS, STATUS_WATCH, STATUS_BLOCK)
STATUS_RANK = {STATUS_BLOCK: 0, STATUS_WATCH: 1, STATUS_PASS: 2}

NO_INPUTS_REASON = "multi_tool_retrieval_confidence_no_inputs"
PASS_REASON = "multi_tool_retrieval_confidence_pass"
WATCH_REASON = "multi_tool_retrieval_confidence_watch"
BLOCK_REASON = "multi_tool_retrieval_confidence_block"

REASON_CODE_SEQUENCE = (
    NO_INPUTS_REASON,
    PASS_REASON,
    WATCH_REASON,
    BLOCK_REASON,
    "coverage_below_block_threshold",
    "coverage_below_pass_threshold",
    "freshness_below_block_threshold",
    "freshness_below_pass_threshold",
    "extraction_confidence_below_block_threshold",
    "extraction_confidence_below_pass_threshold",
    "contradiction_pressure_above_block_threshold",
    "contradiction_pressure_above_pass_threshold",
    "authority_mix_below_block_threshold",
    "authority_mix_below_pass_threshold",
    "core_tool_mix_below_block_threshold",
    "core_tool_mix_below_pass_threshold",
    "retrieval_confidence_score_below_block_threshold",
    "retrieval_confidence_score_below_pass_threshold",
    "fallback_penalty_applied",
)
REASON_CODE_SET = frozenset(REASON_CODE_SEQUENCE)
REASON_CODE_RANK = {
    reason_code: index for index, reason_code in enumerate(REASON_CODE_SEQUENCE)
}

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SECONDS_PER_DAY = Decimal("86400.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000.000000")

PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
DECIMAL_PAYLOAD_RE = re.compile(r"^(?:0|[1-9][0-9]*)\.[0-9]{6}$")

UNSAFE_PUBLIC_FRAGMENTS = (
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
    "authentication",
    "authorization",
    "bearer",
    "cookie",
    "credential",
    "api_key",
    "endpoint",
    "file_path",
    "file-path",
    "file path",
    "filepath",
    "filesystem",
    "password",
    "persist",
    "postgres",
    "postgresql",
    "private_key",
    "private-key",
    "private key",
    "secret",
    "session",
    "socket",
    "sqlite",
    "supabase",
    "table_name",
    "table name",
    "table",
    "token",
    "wallet",
    "order",
    "trade",
    "position",
    "live_trading",
    "live trading",
    "live",
    "sizing",
    "recommendation",
    "network",
    "database",
    "http://",
    "https://",
    "www.",
)
ROW_STATUS_REASON_CODES = frozenset((PASS_REASON, WATCH_REASON, BLOCK_REASON))
ROW_DETAIL_REASON_CODES = REASON_CODE_SET - frozenset(
    (NO_INPUTS_REASON, PASS_REASON, WATCH_REASON, BLOCK_REASON),
)

PUBLIC_DIGEST_FIELD = "public_digest"
PUBLIC_REPORT_PAYLOAD_FIELDS = frozenset(
    (
        "generated_at",
        "config_version",
        "retrieval_scope_count",
        "observation_count",
        "pass_count",
        "watch_count",
        "block_count",
        "average_retrieval_confidence_score",
        "lowest_retrieval_confidence_score",
        "max_contradiction_pressure",
        "max_retrieval_age_seconds",
        "status",
        "reason_codes",
        "rows",
        PUBLIC_DIGEST_FIELD,
        "paper_only",
        "report_only",
        "readonly",
    ),
)
PUBLIC_ROW_PAYLOAD_FIELDS = frozenset(
    (
        "retrieval_scope",
        "tool_count",
        "core_tool_count",
        "fallback_tool_count",
        "latest_observed_at",
        "max_retrieval_age_seconds",
        "coverage_score",
        "freshness_score",
        "extraction_confidence",
        "contradiction_pressure",
        "authority_mix_score",
        "fallback_penalty",
        "retrieval_confidence_score",
        "status",
        "reason_codes",
        "paper_only",
        "report_only",
        "readonly",
    ),
)

__all__ = (
    "CORE_RETRIEVAL_TOOLS",
    "DEFAULT_RESEARCH_SOURCE_MULTI_TOOL_RETRIEVAL_CONFIDENCE_REPORT_CONFIG_VERSION",
    "RETRIEVAL_TOOLS",
    "STATUSES",
    "ResearchSourceMultiToolRetrievalConfidenceConfig",
    "ResearchSourceMultiToolRetrievalConfidenceObservation",
    "ResearchSourceMultiToolRetrievalConfidenceReport",
    "ResearchSourceMultiToolRetrievalConfidenceRow",
    "build_research_source_multi_tool_retrieval_confidence_report",
    "research_source_multi_tool_retrieval_confidence_report_public_digest",
    "research_source_multi_tool_retrieval_confidence_report_public_payload",
    "validate_research_source_multi_tool_retrieval_confidence_report_public_payload",
)


@dataclass(frozen=True)
class ResearchSourceMultiToolRetrievalConfidenceConfig:
    config_version: str = (
        DEFAULT_RESEARCH_SOURCE_MULTI_TOOL_RETRIEVAL_CONFIDENCE_REPORT_CONFIG_VERSION
    )
    fresh_retrieval_age_seconds: Decimal = Decimal("3600.000000")
    stale_retrieval_age_seconds: Decimal = Decimal("86400.000000")
    pass_retrieval_confidence_score: Decimal = Decimal("0.850000")
    watch_retrieval_confidence_score: Decimal = Decimal("0.400000")
    pass_coverage_score: Decimal = Decimal("0.800000")
    block_coverage_score: Decimal = Decimal("0.500000")
    pass_freshness_score: Decimal = Decimal("0.700000")
    block_freshness_score: Decimal = Decimal("0.250000")
    pass_extraction_confidence: Decimal = Decimal("0.800000")
    block_extraction_confidence: Decimal = Decimal("0.500000")
    pass_contradiction_pressure: Decimal = Decimal("0.250000")
    block_contradiction_pressure: Decimal = Decimal("0.650000")
    pass_authority_mix_score: Decimal = Decimal("0.700000")
    block_authority_mix_score: Decimal = Decimal("0.400000")
    minimum_core_tool_pass_count: Decimal = Decimal("1.000000")
    minimum_core_tool_block_count: Decimal = Decimal("1.000000")
    coverage_weight: Decimal = Decimal("0.250000")
    freshness_weight: Decimal = Decimal("0.200000")
    extraction_confidence_weight: Decimal = Decimal("0.250000")
    contradiction_resilience_weight: Decimal = Decimal("0.150000")
    authority_mix_weight: Decimal = Decimal("0.150000")
    fallback_tool_penalty: Decimal = Decimal("0.100000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchSourceMultiToolRetrievalConfidenceConfig does not support "
            "subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            "config",
            self,
            ResearchSourceMultiToolRetrievalConfidenceConfig,
        )
        _require_safe_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_MULTI_TOOL_RETRIEVAL_CONFIDENCE_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in ("fresh_retrieval_age_seconds", "stale_retrieval_age_seconds"):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        if self.stale_retrieval_age_seconds <= self.fresh_retrieval_age_seconds:
            raise ValueError(
                "stale_retrieval_age_seconds must exceed fresh_retrieval_age_seconds",
            )
        for field_name in (
            "pass_retrieval_confidence_score",
            "watch_retrieval_confidence_score",
            "pass_coverage_score",
            "block_coverage_score",
            "pass_freshness_score",
            "block_freshness_score",
            "pass_extraction_confidence",
            "block_extraction_confidence",
            "pass_contradiction_pressure",
            "block_contradiction_pressure",
            "pass_authority_mix_score",
            "block_authority_mix_score",
            "coverage_weight",
            "freshness_weight",
            "extraction_confidence_weight",
            "contradiction_resilience_weight",
            "authority_mix_weight",
            "fallback_tool_penalty",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "minimum_core_tool_pass_count",
            "minimum_core_tool_block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        if self.pass_retrieval_confidence_score <= self.watch_retrieval_confidence_score:
            raise ValueError(
                "pass_retrieval_confidence_score must exceed "
                "watch_retrieval_confidence_score",
            )
        _require_floor_threshold_pair(
            "pass_coverage_score",
            self.pass_coverage_score,
            "block_coverage_score",
            self.block_coverage_score,
        )
        _require_floor_threshold_pair(
            "pass_freshness_score",
            self.pass_freshness_score,
            "block_freshness_score",
            self.block_freshness_score,
        )
        _require_floor_threshold_pair(
            "pass_extraction_confidence",
            self.pass_extraction_confidence,
            "block_extraction_confidence",
            self.block_extraction_confidence,
        )
        _require_floor_threshold_pair(
            "pass_authority_mix_score",
            self.pass_authority_mix_score,
            "block_authority_mix_score",
            self.block_authority_mix_score,
        )
        if self.pass_contradiction_pressure > self.block_contradiction_pressure:
            raise ValueError(
                "pass_contradiction_pressure must not exceed "
                "block_contradiction_pressure",
            )
        if self.minimum_core_tool_block_count > self.minimum_core_tool_pass_count:
            raise ValueError(
                "minimum_core_tool_block_count must not exceed "
                "minimum_core_tool_pass_count",
            )
        weight_sum = _quantize(
            self.coverage_weight
            + self.freshness_weight
            + self.extraction_confidence_weight
            + self.contradiction_resilience_weight
            + self.authority_mix_weight,
        )
        if weight_sum != ONE:
            raise ValueError(
                "coverage_weight, freshness_weight, extraction_confidence_weight, "
                "contradiction_resilience_weight, and authority_mix_weight must sum to 1",
            )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", _json_ready(self))


@dataclass(frozen=True)
class ResearchSourceMultiToolRetrievalConfidenceObservation:
    retrieval_scope: str
    tool_name: str
    observed_at: datetime
    coverage_ratio: Decimal
    extraction_confidence: Decimal
    contradiction_pressure: Decimal
    authority_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchSourceMultiToolRetrievalConfidenceObservation does not support "
            "subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            "observation",
            self,
            ResearchSourceMultiToolRetrievalConfidenceObservation,
        )
        object.__setattr__(
            self,
            "retrieval_scope",
            _require_safe_public_identifier("retrieval_scope", self.retrieval_scope),
        )
        object.__setattr__(
            self,
            "tool_name",
            _require_tool_name("tool_name", self.tool_name),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "coverage_ratio",
            "extraction_confidence",
            "contradiction_pressure",
            "authority_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("observation", self)
        _reject_unsafe_public_payload("observation", _json_ready(self))


@dataclass(frozen=True)
class ResearchSourceMultiToolRetrievalConfidenceRow:
    retrieval_scope: str
    tool_count: Decimal
    core_tool_count: Decimal
    fallback_tool_count: Decimal
    latest_observed_at: datetime
    max_retrieval_age_seconds: Decimal
    coverage_score: Decimal
    freshness_score: Decimal
    extraction_confidence: Decimal
    contradiction_pressure: Decimal
    authority_mix_score: Decimal
    fallback_penalty: Decimal
    retrieval_confidence_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchSourceMultiToolRetrievalConfidenceRow does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            "row",
            self,
            ResearchSourceMultiToolRetrievalConfidenceRow,
        )
        object.__setattr__(
            self,
            "retrieval_scope",
            _require_safe_public_identifier("retrieval_scope", self.retrieval_scope),
        )
        for field_name in ("tool_count", "core_tool_count", "fallback_tool_count"):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "latest_observed_at",
            _as_utc("latest_observed_at", self.latest_observed_at),
        )
        object.__setattr__(
            self,
            "max_retrieval_age_seconds",
            _require_nonnegative_decimal(
                "max_retrieval_age_seconds",
                self.max_retrieval_age_seconds,
            ),
        )
        for field_name in (
            "coverage_score",
            "freshness_score",
            "extraction_confidence",
            "contradiction_pressure",
            "authority_mix_score",
            "fallback_penalty",
            "retrieval_confidence_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "status", _require_status("status", self.status))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_row_consistency(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", _json_ready(self))


@dataclass(frozen=True)
class ResearchSourceMultiToolRetrievalConfidenceReport:
    generated_at: datetime
    config_version: str
    retrieval_scope_count: Decimal
    observation_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_retrieval_confidence_score: Decimal
    lowest_retrieval_confidence_score: Decimal
    max_contradiction_pressure: Decimal
    max_retrieval_age_seconds: Decimal
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchSourceMultiToolRetrievalConfidenceRow, ...]
    public_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchSourceMultiToolRetrievalConfidenceReport does not support "
            "subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            "report",
            self,
            ResearchSourceMultiToolRetrievalConfidenceReport,
        )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_safe_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_MULTI_TOOL_RETRIEVAL_CONFIDENCE_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
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
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_retrieval_confidence_score",
            "lowest_retrieval_confidence_score",
            "max_contradiction_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_retrieval_age_seconds",
            _require_nonnegative_decimal(
                "max_retrieval_age_seconds",
                self.max_retrieval_age_seconds,
            ),
        )
        object.__setattr__(self, "status", _require_status("status", self.status))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report_consistency(self)
        _require_hard_flags("report", self)
        expected_digest = _public_digest_from_report(self)
        if self.public_digest == "":
            object.__setattr__(self, "public_digest", expected_digest)
        elif self.public_digest != expected_digest:
            raise ValueError("public_digest must match public payload")
        _require_sha256_digest("public_digest", self.public_digest)
        _reject_unsafe_public_payload("report", _json_ready(self))

    @property
    def public_payload(self) -> dict[str, Any]:
        return research_source_multi_tool_retrieval_confidence_report_public_payload(self)


def build_research_source_multi_tool_retrieval_confidence_report(
    observations: Iterable[ResearchSourceMultiToolRetrievalConfidenceObservation],
    *,
    config: ResearchSourceMultiToolRetrievalConfidenceConfig,
    generated_at: datetime,
) -> ResearchSourceMultiToolRetrievalConfidenceReport:
    _require_exact_type(
        "config",
        config,
        ResearchSourceMultiToolRetrievalConfidenceConfig,
    )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    observation_items = _normalize_observations(observations)
    for observation in observation_items:
        if observation.observed_at > generated_at_utc:
            raise ValueError("observed_at must not be after generated_at")

    grouped: dict[str, list[ResearchSourceMultiToolRetrievalConfidenceObservation]] = {}
    for observation in observation_items:
        grouped.setdefault(observation.retrieval_scope, []).append(observation)

    rows = tuple(
        _row_for_scope(
            retrieval_scope=retrieval_scope,
            observations=tuple(grouped[retrieval_scope]),
            config=config,
            generated_at=generated_at_utc,
        )
        for retrieval_scope in sorted(grouped)
    )
    return ResearchSourceMultiToolRetrievalConfidenceReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        retrieval_scope_count=_decimal_count(len(rows)),
        observation_count=_decimal_count(len(observation_items)),
        pass_count=_decimal_count(_status_count(rows, STATUS_PASS)),
        watch_count=_decimal_count(_status_count(rows, STATUS_WATCH)),
        block_count=_decimal_count(_status_count(rows, STATUS_BLOCK)),
        average_retrieval_confidence_score=_average_or_zero(
            tuple(row.retrieval_confidence_score for row in rows),
        ),
        lowest_retrieval_confidence_score=min(
            (row.retrieval_confidence_score for row in rows),
            default=ZERO,
        ),
        max_contradiction_pressure=max(
            (row.contradiction_pressure for row in rows),
            default=ZERO,
        ),
        max_retrieval_age_seconds=max(
            (row.max_retrieval_age_seconds for row in rows),
            default=ZERO,
        ),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        rows=rows,
    )


def research_source_multi_tool_retrieval_confidence_report_public_payload(
    value: ResearchSourceMultiToolRetrievalConfidenceReport | Mapping[str, Any],
) -> dict[str, Any]:
    if type(value) is ResearchSourceMultiToolRetrievalConfidenceReport:
        _validate_public_digest_for_report(value)
        payload = _json_ready(value)
    elif isinstance(value, Mapping):
        payload = _copy_json_object(value)
    else:
        raise ValueError(
            "value must be a ResearchSourceMultiToolRetrievalConfidenceReport or dict",
        )
    if type(payload) is not dict:
        raise ValueError("public payload must be a JSON object")
    validate_research_source_multi_tool_retrieval_confidence_report_public_payload(
        payload,
    )
    return payload


def research_source_multi_tool_retrieval_confidence_report_public_digest(
    value: ResearchSourceMultiToolRetrievalConfidenceReport | Mapping[str, Any],
) -> str:
    if type(value) is ResearchSourceMultiToolRetrievalConfidenceReport:
        return _public_digest_from_report(value)
    if isinstance(value, Mapping):
        payload = _copy_json_object(value)
        return _public_digest_from_payload(payload)
    raise ValueError(
        "value must be a ResearchSourceMultiToolRetrievalConfidenceReport or dict",
    )


def validate_research_source_multi_tool_retrieval_confidence_report_public_payload(
    payload: Mapping[str, Any],
) -> bool:
    if not isinstance(payload, Mapping):
        raise ValueError("public payload must be a JSON object")
    copied = _copy_json_object(payload)
    _reject_unsafe_public_payload("public payload", copied)
    _require_public_payload_shape(copied)
    _require_public_payload_flags(copied)
    _require_public_payload_statuses(copied)
    _require_public_payload_reason_codes(copied)
    digest = copied.get(PUBLIC_DIGEST_FIELD)
    if type(digest) is not str:
        raise ValueError("public_digest must be a string")
    _require_sha256_digest("public_digest", digest)
    expected_digest = _public_digest_from_payload(copied)
    if digest != expected_digest:
        raise ValueError("public_digest must match public payload")
    validated_report = _report_from_public_payload(copied)
    if _json_ready(validated_report) != copied:
        raise ValueError("public payload must use canonical schema values")
    return True


def _row_for_scope(
    *,
    retrieval_scope: str,
    observations: tuple[ResearchSourceMultiToolRetrievalConfidenceObservation, ...],
    config: ResearchSourceMultiToolRetrievalConfidenceConfig,
    generated_at: datetime,
) -> ResearchSourceMultiToolRetrievalConfidenceRow:
    if not observations:
        raise ValueError("observations must be nonempty")
    latest_observed_at = max(observation.observed_at for observation in observations)
    max_age_seconds = max(
        _duration_seconds(observation.observed_at, generated_at)
        for observation in observations
    )
    coverage_score = _average_or_zero(
        tuple(observation.coverage_ratio for observation in observations),
    )
    freshness_score = _freshness_score(max_age_seconds, config=config)
    extraction_confidence = _average_or_zero(
        tuple(observation.extraction_confidence for observation in observations),
    )
    contradiction_pressure = max(
        observation.contradiction_pressure for observation in observations
    )
    authority_mix_score = _average_or_zero(
        tuple(observation.authority_score for observation in observations),
    )
    tool_count = _decimal_count(len(observations))
    core_tool_count = _decimal_count(
        sum(1 for observation in observations if observation.tool_name in CORE_RETRIEVAL_TOOLS),
    )
    fallback_tool_count = _decimal_count(
        sum(1 for observation in observations if observation.tool_name == TOOL_FALLBACK),
    )
    fallback_penalty = _fallback_penalty(
        fallback_tool_count=fallback_tool_count,
        core_tool_count=core_tool_count,
        config=config,
    )
    retrieval_confidence_score = _retrieval_confidence_score(
        coverage_score=coverage_score,
        freshness_score=freshness_score,
        extraction_confidence=extraction_confidence,
        contradiction_pressure=contradiction_pressure,
        authority_mix_score=authority_mix_score,
        fallback_penalty=fallback_penalty,
        config=config,
    )
    reason_codes = _row_reason_codes(
        coverage_score=coverage_score,
        freshness_score=freshness_score,
        extraction_confidence=extraction_confidence,
        contradiction_pressure=contradiction_pressure,
        authority_mix_score=authority_mix_score,
        core_tool_count=core_tool_count,
        fallback_penalty=fallback_penalty,
        retrieval_confidence_score=retrieval_confidence_score,
        config=config,
    )
    status = _row_status(reason_codes)
    return ResearchSourceMultiToolRetrievalConfidenceRow(
        retrieval_scope=retrieval_scope,
        tool_count=tool_count,
        core_tool_count=core_tool_count,
        fallback_tool_count=fallback_tool_count,
        latest_observed_at=latest_observed_at,
        max_retrieval_age_seconds=max_age_seconds,
        coverage_score=coverage_score,
        freshness_score=freshness_score,
        extraction_confidence=extraction_confidence,
        contradiction_pressure=contradiction_pressure,
        authority_mix_score=authority_mix_score,
        fallback_penalty=fallback_penalty,
        retrieval_confidence_score=retrieval_confidence_score,
        status=status,
        reason_codes=(_status_reason(status), *reason_codes),
    )


def _freshness_score(
    max_age_seconds: Decimal,
    *,
    config: ResearchSourceMultiToolRetrievalConfidenceConfig,
) -> Decimal:
    if max_age_seconds <= config.fresh_retrieval_age_seconds:
        return ONE
    if max_age_seconds >= config.stale_retrieval_age_seconds:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        freshness_window = (
            config.stale_retrieval_age_seconds - config.fresh_retrieval_age_seconds
        )
        stale_age = max_age_seconds - config.fresh_retrieval_age_seconds
        return _bounded_ratio(ONE - (stale_age / freshness_window))


def _fallback_penalty(
    *,
    fallback_tool_count: Decimal,
    core_tool_count: Decimal,
    config: ResearchSourceMultiToolRetrievalConfidenceConfig,
) -> Decimal:
    if fallback_tool_count > ZERO and core_tool_count == ZERO:
        return config.fallback_tool_penalty
    return ZERO


def _retrieval_confidence_score(
    *,
    coverage_score: Decimal,
    freshness_score: Decimal,
    extraction_confidence: Decimal,
    contradiction_pressure: Decimal,
    authority_mix_score: Decimal,
    fallback_penalty: Decimal,
    config: ResearchSourceMultiToolRetrievalConfidenceConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        score = (
            coverage_score * config.coverage_weight
            + freshness_score * config.freshness_weight
            + extraction_confidence * config.extraction_confidence_weight
            + (ONE - contradiction_pressure) * config.contradiction_resilience_weight
            + authority_mix_score * config.authority_mix_weight
            - fallback_penalty
        )
    return _bounded_ratio(score)


def _row_reason_codes(
    *,
    coverage_score: Decimal,
    freshness_score: Decimal,
    extraction_confidence: Decimal,
    contradiction_pressure: Decimal,
    authority_mix_score: Decimal,
    core_tool_count: Decimal,
    fallback_penalty: Decimal,
    retrieval_confidence_score: Decimal,
    config: ResearchSourceMultiToolRetrievalConfidenceConfig,
) -> tuple[str, ...]:
    block_reasons: list[str] = []
    if coverage_score < config.block_coverage_score:
        block_reasons.append("coverage_below_block_threshold")
    if freshness_score < config.block_freshness_score:
        block_reasons.append("freshness_below_block_threshold")
    if extraction_confidence < config.block_extraction_confidence:
        block_reasons.append("extraction_confidence_below_block_threshold")
    if contradiction_pressure > config.block_contradiction_pressure:
        block_reasons.append("contradiction_pressure_above_block_threshold")
    if authority_mix_score < config.block_authority_mix_score:
        block_reasons.append("authority_mix_below_block_threshold")
    if core_tool_count < config.minimum_core_tool_block_count:
        block_reasons.append("core_tool_mix_below_block_threshold")
    if block_reasons:
        if fallback_penalty > ZERO:
            block_reasons.append("fallback_penalty_applied")
        return _normalize_reason_codes("block_reasons", tuple(block_reasons))

    watch_reasons: list[str] = []
    if coverage_score < config.pass_coverage_score:
        watch_reasons.append("coverage_below_pass_threshold")
    if freshness_score < config.pass_freshness_score:
        watch_reasons.append("freshness_below_pass_threshold")
    if extraction_confidence < config.pass_extraction_confidence:
        watch_reasons.append("extraction_confidence_below_pass_threshold")
    if contradiction_pressure > config.pass_contradiction_pressure:
        watch_reasons.append("contradiction_pressure_above_pass_threshold")
    if authority_mix_score < config.pass_authority_mix_score:
        watch_reasons.append("authority_mix_below_pass_threshold")
    if core_tool_count < config.minimum_core_tool_pass_count:
        watch_reasons.append("core_tool_mix_below_pass_threshold")
    if retrieval_confidence_score < config.watch_retrieval_confidence_score:
        watch_reasons.append("retrieval_confidence_score_below_block_threshold")
    elif (
        not watch_reasons
        and retrieval_confidence_score < config.pass_retrieval_confidence_score
    ):
        watch_reasons.append("retrieval_confidence_score_below_pass_threshold")
    if fallback_penalty > ZERO:
        watch_reasons.append("fallback_penalty_applied")
    return _normalize_reason_codes("watch_reasons", tuple(watch_reasons))


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_block_threshold") for reason_code in reason_codes):
        return STATUS_BLOCK
    if "retrieval_confidence_score_below_block_threshold" in reason_codes:
        return STATUS_BLOCK
    if reason_codes:
        return STATUS_WATCH
    return STATUS_PASS


def _status_reason(status: str) -> str:
    if status == STATUS_BLOCK:
        return BLOCK_REASON
    if status == STATUS_WATCH:
        return WATCH_REASON
    return PASS_REASON


def _normalize_observations(
    observations: Iterable[ResearchSourceMultiToolRetrievalConfidenceObservation],
) -> tuple[ResearchSourceMultiToolRetrievalConfidenceObservation, ...]:
    if isinstance(observations, (str, bytes, Mapping)):
        raise ValueError("observations must be an iterable of retrieval observations")
    normalized = tuple(observations)
    seen_scope_tool: set[tuple[str, str]] = set()
    for observation in normalized:
        _require_exact_type(
            "observation",
            observation,
            ResearchSourceMultiToolRetrievalConfidenceObservation,
        )
        _require_hard_flags("observation", observation)
        pair = (observation.retrieval_scope, observation.tool_name)
        if pair in seen_scope_tool:
            raise ValueError("retrieval_scope and tool_name pairs must be unique")
        seen_scope_tool.add(pair)
    return normalized


def _report_status(
    rows: tuple[ResearchSourceMultiToolRetrievalConfidenceRow, ...],
) -> str:
    if not rows:
        return STATUS_BLOCK
    return min((row.status for row in rows), key=lambda status: STATUS_RANK[status])


def _report_reason_codes(
    rows: tuple[ResearchSourceMultiToolRetrievalConfidenceRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON,)
    reason_codes: list[str] = [_status_reason(_report_status(rows))]
    for row in rows:
        for reason_code in row.reason_codes:
            if reason_code not in reason_codes:
                reason_codes.append(reason_code)
    return _normalize_reason_codes("reason_codes", tuple(reason_codes))


def _status_count(
    rows: tuple[ResearchSourceMultiToolRetrievalConfidenceRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _normalize_rows(
    rows: tuple[ResearchSourceMultiToolRetrievalConfidenceRow, ...],
) -> tuple[ResearchSourceMultiToolRetrievalConfidenceRow, ...]:
    if not isinstance(rows, tuple):
        raise ValueError("rows must be a tuple")
    normalized: list[ResearchSourceMultiToolRetrievalConfidenceRow] = []
    seen_scopes: set[str] = set()
    for row in rows:
        _require_exact_type("row", row, ResearchSourceMultiToolRetrievalConfidenceRow)
        _require_hard_flags("row", row)
        if row.retrieval_scope in seen_scopes:
            raise ValueError("row retrieval_scope values must be unique")
        seen_scopes.add(row.retrieval_scope)
        normalized.append(row)
    return tuple(sorted(normalized, key=lambda row: row.retrieval_scope))


def _validate_row_consistency(
    row: ResearchSourceMultiToolRetrievalConfidenceRow,
) -> None:
    if row.tool_count <= ZERO:
        raise ValueError("tool_count must be positive")
    if row.core_tool_count + row.fallback_tool_count != row.tool_count:
        raise ValueError("tool_count must equal core_tool_count plus fallback_tool_count")
    if row.core_tool_count > _decimal_count(len(CORE_RETRIEVAL_TOOLS)):
        raise ValueError("core_tool_count exceeds supported core retrieval tools")
    if row.fallback_tool_count > ONE:
        raise ValueError("fallback_tool_count exceeds supported fallback retrieval tools")
    if not row.reason_codes:
        raise ValueError("row reason_codes must be nonempty")
    status_reason_codes = tuple(
        reason_code
        for reason_code in row.reason_codes
        if reason_code in ROW_STATUS_REASON_CODES
    )
    if status_reason_codes != (_status_reason(row.status),):
        raise ValueError("row reason_codes must contain exactly one matching status reason")
    detail_reason_codes = tuple(
        reason_code
        for reason_code in row.reason_codes
        if reason_code not in ROW_STATUS_REASON_CODES
    )
    if any(reason_code not in ROW_DETAIL_REASON_CODES for reason_code in detail_reason_codes):
        raise ValueError("row reason_codes contain a report-only reason")
    if _row_status(detail_reason_codes) != row.status:
        raise ValueError("row reason_codes must match row status")


def _validate_report_consistency(
    report: ResearchSourceMultiToolRetrievalConfidenceReport,
) -> None:
    row_count = _decimal_count(len(report.rows))
    if report.retrieval_scope_count != row_count:
        raise ValueError("retrieval_scope_count must equal row count")
    expected_observation_count = _quantize(
        sum((row.tool_count for row in report.rows), ZERO),
    )
    if report.observation_count != expected_observation_count:
        raise ValueError("observation_count must match row tool counts")
    for field_name, status in (
        ("pass_count", STATUS_PASS),
        ("watch_count", STATUS_WATCH),
        ("block_count", STATUS_BLOCK),
    ):
        expected_count = _decimal_count(_status_count(report.rows, status))
        if getattr(report, field_name) != expected_count:
            raise ValueError(f"{field_name} must match rows")
    expected_average_score = _average_or_zero(
        tuple(row.retrieval_confidence_score for row in report.rows),
    )
    if report.average_retrieval_confidence_score != expected_average_score:
        raise ValueError("average_retrieval_confidence_score must match rows")
    expected_lowest_score = min(
        (row.retrieval_confidence_score for row in report.rows),
        default=ZERO,
    )
    if report.lowest_retrieval_confidence_score != expected_lowest_score:
        raise ValueError("lowest_retrieval_confidence_score must match rows")
    expected_max_contradiction = max(
        (row.contradiction_pressure for row in report.rows),
        default=ZERO,
    )
    if report.max_contradiction_pressure != expected_max_contradiction:
        raise ValueError("max_contradiction_pressure must match rows")
    expected_max_age = max(
        (row.max_retrieval_age_seconds for row in report.rows),
        default=ZERO,
    )
    if report.max_retrieval_age_seconds != expected_max_age:
        raise ValueError("max_retrieval_age_seconds must match rows")
    if any(row.latest_observed_at > report.generated_at for row in report.rows):
        raise ValueError("row latest_observed_at must not be after generated_at")
    if report.status != _report_status(report.rows):
        raise ValueError("report status must match row statuses")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("report reason_codes must match rows")


def _require_exact_type(label: str, value: object, expected_type: type[object]) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_tool_name(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    _reject_unsafe_public_text(field_name, value)
    if value not in RETRIEVAL_TOOLS:
        raise ValueError(f"{field_name} must be one of {RETRIEVAL_TOOLS}")
    return value


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value not in STATUSES:
        raise ValueError(f"{field_name} must be one of {STATUSES}")
    return value


def _normalize_reason_codes(
    field_name: str,
    value: tuple[str, ...],
) -> tuple[str, ...]:
    if not isinstance(value, tuple):
        raise ValueError(f"{field_name} must be a tuple")
    normalized: list[str] = []
    for reason_code in value:
        if type(reason_code) is not str:
            raise ValueError(f"{field_name} entries must be strings")
        if reason_code not in REASON_CODE_SET:
            raise ValueError(f"unsupported reason code: {reason_code}")
        if reason_code not in normalized:
            normalized.append(reason_code)
    return tuple(sorted(normalized, key=lambda reason_code: REASON_CODE_RANK[reason_code]))


def _require_safe_public_identifier(field_name: str, value: object) -> str:
    safe_value = _require_safe_public_string(field_name, value)
    if not PUBLIC_IDENTIFIER_RE.fullmatch(safe_value):
        raise ValueError(f"{field_name} must be a safe public identifier")
    return safe_value


def _require_safe_public_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    _reject_unsafe_public_text(field_name, value)
    if value == "":
        raise ValueError(f"{field_name} must be nonempty")
    return value


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"unsafe public payload key in {label}")
            _reject_unsafe_public_text(label, key)
            _reject_unsafe_public_payload(label, item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(label, item)
    elif isinstance(value, str):
        _reject_unsafe_public_text(label, value)
    elif is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, _json_ready(value))


def _reject_unsafe_public_text(label: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"unsafe public surface in {label}")
    if re.search(r"(^|[^a-z0-9])(auth|db)([^a-z0-9]|$)", lowered):
        raise ValueError(f"unsafe public surface in {label}")


def _require_floor_threshold_pair(
    pass_field_name: str,
    pass_value: Decimal,
    block_field_name: str,
    block_value: Decimal,
) -> None:
    if pass_value < block_value:
        raise ValueError(f"{pass_field_name} must not be below {block_field_name}")


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole-number Decimal")
    return decimal_value


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return decimal_value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        try:
            quantized = value.quantize(QUANTUM)
        except InvalidOperation as exc:
            raise ValueError("Decimal value must be quantizable") from exc
    if quantized == ZERO:
        return ZERO
    return quantized


def _bounded_ratio(value: Decimal) -> Decimal:
    decimal_value = _quantize(value)
    if decimal_value < ZERO:
        return ZERO
    if decimal_value > ONE:
        return ONE
    return decimal_value


def _average_or_zero(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _bounded_ratio(sum(values, ZERO) / _decimal_count(len(values)))


def _decimal_count(value: int) -> Decimal:
    return _quantize(Decimal(str(value)))


def _duration_seconds(start: datetime, end: datetime) -> Decimal:
    delta = end - start
    if delta.days < 0:
        raise ValueError("duration must be nonnegative")
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(
            _decimal_count(delta.days) * SECONDS_PER_DAY
            + _decimal_count(delta.seconds)
            + (_decimal_count(delta.microseconds) / MICROSECONDS_PER_SECOND),
        )


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _json_ready(value: object) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _json_ready(getattr(value, field.name))
            for field in fields(value)
        }
    if isinstance(value, Decimal):
        return str(_quantize(value))
    if isinstance(value, datetime):
        return _as_utc("datetime", value).isoformat()
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, Mapping):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if type(value) in (str, bool) or value is None:
        return value
    raise ValueError("public payload contains unsupported value")


def _copy_json_object(value: Mapping[str, Any]) -> dict[str, Any]:
    copied = _copy_json_value(value)
    if type(copied) is not dict:
        raise ValueError("public payload must be a JSON object")
    return copied


def _copy_json_value(value: Any) -> Any:
    if type(value) is dict or isinstance(value, Mapping):
        copied: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            copied[key] = _copy_json_value(item)
        return copied
    if isinstance(value, list):
        return [_copy_json_value(item) for item in value]
    if isinstance(value, tuple):
        raise ValueError("public payload arrays must be lists")
    if type(value) in (str, bool) or value is None:
        return value
    raise ValueError("public payload contains unsupported value")


def _public_digest_from_report(
    report: ResearchSourceMultiToolRetrievalConfidenceReport,
) -> str:
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("public payload must be a JSON object")
    return _public_digest_from_payload(payload)


def _public_digest_from_payload(payload: Mapping[str, Any]) -> str:
    copied = _copy_json_object(payload)
    copied.pop(PUBLIC_DIGEST_FIELD, None)
    encoded = json.dumps(copied, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return sha256(encoded.encode("utf-8")).hexdigest()


def _validate_public_digest_for_report(
    report: ResearchSourceMultiToolRetrievalConfidenceReport,
) -> None:
    _require_exact_type(
        "report",
        report,
        ResearchSourceMultiToolRetrievalConfidenceReport,
    )
    _require_hard_flags("report", report)
    _require_sha256_digest("public_digest", report.public_digest)
    expected = _public_digest_from_report(report)
    if report.public_digest != expected:
        raise ValueError("public_digest must match public payload")


def _require_sha256_digest(field_name: str, value: str) -> None:
    if not SHA256_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a SHA-256 hex digest")


def _require_public_payload_flags(payload: Mapping[str, Any]) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload.get(field_name) is not True:
            raise ValueError(f"{field_name} must be True for public payload")
    rows = payload.get("rows")
    if isinstance(rows, list):
        for row in rows:
            if isinstance(row, Mapping):
                for field_name in ("paper_only", "report_only", "readonly"):
                    if row.get(field_name) is not True:
                        raise ValueError(f"{field_name} must be True for row payload")


def _require_public_payload_shape(payload: Mapping[str, Any]) -> None:
    unexpected_fields = tuple(
        sorted(set(payload) - PUBLIC_REPORT_PAYLOAD_FIELDS),
    )
    if unexpected_fields:
        raise ValueError("unexpected public payload field")
    missing_fields = tuple(
        sorted(PUBLIC_REPORT_PAYLOAD_FIELDS - set(payload)),
    )
    if missing_fields:
        raise ValueError("missing public payload field")
    rows = payload.get("rows")
    if type(rows) is not list:
        raise ValueError("rows must be a list")
    for row in rows:
        if not isinstance(row, Mapping):
            raise ValueError("row payload must be a JSON object")
        unexpected_row_fields = tuple(
            sorted(set(row) - PUBLIC_ROW_PAYLOAD_FIELDS),
        )
        if unexpected_row_fields:
            raise ValueError("unexpected row payload field")
        missing_row_fields = tuple(
            sorted(PUBLIC_ROW_PAYLOAD_FIELDS - set(row)),
        )
        if missing_row_fields:
            raise ValueError("missing row payload field")


def _require_public_payload_statuses(payload: Mapping[str, Any]) -> None:
    _require_status("status", payload.get("status"))
    rows = payload.get("rows")
    if type(rows) is not list:
        raise ValueError("rows must be a list")
    for row in rows:
        if not isinstance(row, Mapping):
            raise ValueError("row payload must be a JSON object")
        _require_status("row status", row.get("status"))


def _require_public_payload_reason_codes(payload: Mapping[str, Any]) -> None:
    _require_public_reason_codes("reason_codes", payload.get("reason_codes"))
    rows = payload.get("rows")
    if type(rows) is not list:
        raise ValueError("rows must be a list")
    for row in rows:
        if not isinstance(row, Mapping):
            raise ValueError("row payload must be a JSON object")
        _require_public_reason_codes("row reason_codes", row.get("reason_codes"))


def _require_public_reason_codes(
    field_name: str,
    value: object,
) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a list")
    reason_codes: list[str] = []
    for reason_code in value:
        if type(reason_code) is not str:
            raise ValueError(f"{field_name} entries must be strings")
        if reason_code not in REASON_CODE_SET:
            raise ValueError(f"unsupported public reason code: {reason_code}")
        reason_codes.append(reason_code)
    normalized = _normalize_reason_codes(field_name, tuple(reason_codes))
    if tuple(reason_codes) != normalized:
        raise ValueError(f"{field_name} must use canonical unique ordering")
    return normalized


def _report_from_public_payload(
    payload: Mapping[str, Any],
) -> ResearchSourceMultiToolRetrievalConfidenceReport:
    rows_value = payload.get("rows")
    if type(rows_value) is not list:
        raise ValueError("rows must be a list")
    rows = tuple(_row_from_public_payload(row) for row in rows_value)
    return ResearchSourceMultiToolRetrievalConfidenceReport(
        generated_at=_require_datetime_payload_string(
            "generated_at",
            payload.get("generated_at"),
        ),
        config_version=_require_payload_string(
            "config_version",
            payload.get("config_version"),
        ),
        retrieval_scope_count=_require_decimal_payload_string(
            "retrieval_scope_count",
            payload.get("retrieval_scope_count"),
        ),
        observation_count=_require_decimal_payload_string(
            "observation_count",
            payload.get("observation_count"),
        ),
        pass_count=_require_decimal_payload_string(
            "pass_count",
            payload.get("pass_count"),
        ),
        watch_count=_require_decimal_payload_string(
            "watch_count",
            payload.get("watch_count"),
        ),
        block_count=_require_decimal_payload_string(
            "block_count",
            payload.get("block_count"),
        ),
        average_retrieval_confidence_score=_require_decimal_payload_string(
            "average_retrieval_confidence_score",
            payload.get("average_retrieval_confidence_score"),
        ),
        lowest_retrieval_confidence_score=_require_decimal_payload_string(
            "lowest_retrieval_confidence_score",
            payload.get("lowest_retrieval_confidence_score"),
        ),
        max_contradiction_pressure=_require_decimal_payload_string(
            "max_contradiction_pressure",
            payload.get("max_contradiction_pressure"),
        ),
        max_retrieval_age_seconds=_require_decimal_payload_string(
            "max_retrieval_age_seconds",
            payload.get("max_retrieval_age_seconds"),
        ),
        status=_require_payload_string("status", payload.get("status")),
        reason_codes=_require_public_reason_codes(
            "reason_codes",
            payload.get("reason_codes"),
        ),
        rows=rows,
        public_digest=_require_payload_string(
            PUBLIC_DIGEST_FIELD,
            payload.get(PUBLIC_DIGEST_FIELD),
        ),
        paper_only=payload.get("paper_only"),
        report_only=payload.get("report_only"),
        readonly=payload.get("readonly"),
    )


def _row_from_public_payload(
    payload: object,
) -> ResearchSourceMultiToolRetrievalConfidenceRow:
    if not isinstance(payload, Mapping):
        raise ValueError("row payload must be a JSON object")
    return ResearchSourceMultiToolRetrievalConfidenceRow(
        retrieval_scope=_require_payload_string(
            "retrieval_scope",
            payload.get("retrieval_scope"),
        ),
        tool_count=_require_decimal_payload_string(
            "tool_count",
            payload.get("tool_count"),
        ),
        core_tool_count=_require_decimal_payload_string(
            "core_tool_count",
            payload.get("core_tool_count"),
        ),
        fallback_tool_count=_require_decimal_payload_string(
            "fallback_tool_count",
            payload.get("fallback_tool_count"),
        ),
        latest_observed_at=_require_datetime_payload_string(
            "latest_observed_at",
            payload.get("latest_observed_at"),
        ),
        max_retrieval_age_seconds=_require_decimal_payload_string(
            "max_retrieval_age_seconds",
            payload.get("max_retrieval_age_seconds"),
        ),
        coverage_score=_require_decimal_payload_string(
            "coverage_score",
            payload.get("coverage_score"),
        ),
        freshness_score=_require_decimal_payload_string(
            "freshness_score",
            payload.get("freshness_score"),
        ),
        extraction_confidence=_require_decimal_payload_string(
            "extraction_confidence",
            payload.get("extraction_confidence"),
        ),
        contradiction_pressure=_require_decimal_payload_string(
            "contradiction_pressure",
            payload.get("contradiction_pressure"),
        ),
        authority_mix_score=_require_decimal_payload_string(
            "authority_mix_score",
            payload.get("authority_mix_score"),
        ),
        fallback_penalty=_require_decimal_payload_string(
            "fallback_penalty",
            payload.get("fallback_penalty"),
        ),
        retrieval_confidence_score=_require_decimal_payload_string(
            "retrieval_confidence_score",
            payload.get("retrieval_confidence_score"),
        ),
        status=_require_payload_string("row status", payload.get("status")),
        reason_codes=_require_public_reason_codes(
            "row reason_codes",
            payload.get("reason_codes"),
        ),
        paper_only=payload.get("paper_only"),
        report_only=payload.get("report_only"),
        readonly=payload.get("readonly"),
    )


def _require_payload_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    return value


def _require_datetime_payload_string(field_name: str, value: object) -> datetime:
    datetime_value = _require_payload_string(field_name, value)
    try:
        parsed = datetime.fromisoformat(datetime_value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be an ISO datetime") from exc
    normalized = _as_utc(field_name, parsed)
    if normalized.isoformat() != datetime_value:
        raise ValueError(f"{field_name} must be a canonical UTC ISO datetime")
    return normalized


def _require_decimal_payload_string(field_name: str, value: object) -> Decimal:
    decimal_value = _require_payload_string(field_name, value)
    if not DECIMAL_PAYLOAD_RE.fullmatch(decimal_value):
        raise ValueError(f"{field_name} must be a Decimal-derived string")
    parsed = Decimal(decimal_value)
    if not parsed.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if str(_quantize(parsed)) != decimal_value:
        raise ValueError(f"{field_name} must be quantized to six decimals")
    return parsed
