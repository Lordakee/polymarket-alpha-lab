"""Report-only reducer for domain evidence memory reuse quality."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_UP, localcontext
import hashlib
import json
import re
from typing import Any, Mapping, Sequence


DEFAULT_RESEARCH_TEAM_DOMAIN_EVIDENCE_MEMORY_REUSE_CONFIG_VERSION = (
    "research-team-domain-evidence-memory-reuse-report-v1"
)

EMPTY_REASON = "domain_evidence_memory_reuse_empty_observations"
INSUFFICIENT_PRECEDENT_REASON = "insufficient_relevant_precedent_coverage"
STALE_MEMORY_REASON = "stale_memory_penalty_applied"
SOURCE_FRESHNESS_REASON = "source_freshness_watch"
CALIBRATION_REASON = "calibration_value_watch"
CONFLICT_HANDLED_REASON = "cross_domain_conflict_handled"
CONFLICT_UNRESOLVED_REASON = "cross_domain_conflict_unresolved"
PRODUCTIVE_SCORE_REASON = "productive_reuse_score_watch"
PASS_REASON = "productive_domain_evidence_memory_reuse_passed"

REASON_CODES = (
    EMPTY_REASON,
    INSUFFICIENT_PRECEDENT_REASON,
    STALE_MEMORY_REASON,
    SOURCE_FRESHNESS_REASON,
    CALIBRATION_REASON,
    CONFLICT_HANDLED_REASON,
    CONFLICT_UNRESOLVED_REASON,
    PRODUCTIVE_SCORE_REASON,
    PASS_REASON,
)
REASON_CODE_RANK = {reason_code: index for index, reason_code in enumerate(REASON_CODES)}
BLOCK_REASONS = (EMPTY_REASON, INSUFFICIENT_PRECEDENT_REASON, CONFLICT_UNRESOLVED_REASON)
WATCH_REASONS = (
    STALE_MEMORY_REASON,
    SOURCE_FRESHNESS_REASON,
    CALIBRATION_REASON,
    CONFLICT_HANDLED_REASON,
    PRODUCTIVE_SCORE_REASON,
)
STATUSES = ("pass", "watch", "block")
NEXT_REVIEW_STEPS = {
    "pass": "continue_domain_memory_reuse",
    "watch": "review_domain_memory_reuse_inputs",
    "block": "pause_domain_memory_reuse",
}

QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
FOUR = Decimal("4.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_UP)
PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
PUBLIC_DECIMAL_RE = re.compile(r"^(?:0|[1-9][0-9]*)\.[0-9]{6}$")
PHASE_FLAG_FIELDS = frozenset(("paper_only", "report_only", "readonly"))
MAX_PUBLIC_PAYLOAD_DEPTH = 64
UNSAFE_PUBLIC_TERMS = (
    "api_key",
    "auth",
    "candidate",
    "credential",
    "market",
    "password",
    "private",
    "secret",
    "slug",
    "question",
    "url",
    "dsn",
    "table",
    "token",
    "wallet",
    "order",
    "trade",
    "live",
)

__all__ = (
    "DEFAULT_RESEARCH_TEAM_DOMAIN_EVIDENCE_MEMORY_REUSE_CONFIG_VERSION",
    "ResearchTeamDomainEvidenceMemoryReuseConfig",
    "ResearchTeamDomainEvidenceMemoryReuseObservation",
    "ResearchTeamDomainEvidenceMemoryReuseReasonCodeCount",
    "ResearchTeamDomainEvidenceMemoryReuseReport",
    "ResearchTeamDomainEvidenceMemoryReuseRow",
    "build_research_team_domain_evidence_memory_reuse_report",
    "research_team_domain_evidence_memory_reuse_report_payload",
)


@dataclass(frozen=True)
class ResearchTeamDomainEvidenceMemoryReuseConfig:
    config_version: str = DEFAULT_RESEARCH_TEAM_DOMAIN_EVIDENCE_MEMORY_REUSE_CONFIG_VERSION
    min_relevant_precedent_score: Decimal = Decimal("0.600000")
    min_relevant_precedent_coverage: Decimal = Decimal("0.600000")
    stale_memory_age_seconds: Decimal = Decimal("2592000.000000")
    stale_source_age_seconds: Decimal = Decimal("172800.000000")
    stale_memory_penalty_per_item: Decimal = Decimal("0.250000")
    min_source_freshness_score: Decimal = Decimal("0.600000")
    min_calibration_value: Decimal = Decimal("0.550000")
    min_conflict_handling_score: Decimal = Decimal("0.600000")
    min_productive_reuse_score: Decimal = Decimal("0.650000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamDomainEvidenceMemoryReuseConfig:
            raise TypeError(
                "ResearchTeamDomainEvidenceMemoryReuseConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchTeamDomainEvidenceMemoryReuseConfig:
            raise ValueError(
                "config must be exactly ResearchTeamDomainEvidenceMemoryReuseConfig",
            )
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_TEAM_DOMAIN_EVIDENCE_MEMORY_REUSE_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "min_relevant_precedent_score",
            "min_relevant_precedent_coverage",
            "stale_memory_penalty_per_item",
            "min_source_freshness_score",
            "min_calibration_value",
            "min_conflict_handling_score",
            "min_productive_reuse_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("stale_memory_age_seconds", "stale_source_age_seconds"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchTeamDomainEvidenceMemoryReuseObservation:
    team_key: str
    domain_key: str
    internal_reference: str
    captured_at: datetime
    reused_at: datetime
    source_observed_at: datetime
    relevant_precedent_score: Decimal
    source_freshness_score: Decimal
    calibration_value: Decimal
    cross_domain_conflict_count: Decimal
    conflict_handling_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamDomainEvidenceMemoryReuseObservation:
            raise TypeError(
                "ResearchTeamDomainEvidenceMemoryReuseObservation does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchTeamDomainEvidenceMemoryReuseObservation:
            raise ValueError(
                "observation must be exactly "
                "ResearchTeamDomainEvidenceMemoryReuseObservation",
            )
        _require_public_identifier("team_key", self.team_key)
        _require_public_identifier("domain_key", self.domain_key)
        object.__setattr__(
            self,
            "internal_reference",
            _require_private_reference("internal_reference", self.internal_reference),
        )
        object.__setattr__(self, "captured_at", _as_utc("captured_at", self.captured_at))
        object.__setattr__(self, "reused_at", _as_utc("reused_at", self.reused_at))
        object.__setattr__(
            self,
            "source_observed_at",
            _as_utc("source_observed_at", self.source_observed_at),
        )
        for field_name in (
            "relevant_precedent_score",
            "source_freshness_score",
            "calibration_value",
            "conflict_handling_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "cross_domain_conflict_count",
            _require_whole_count_decimal(
                "cross_domain_conflict_count",
                self.cross_domain_conflict_count,
            ),
        )
        if self.reused_at < self.captured_at:
            raise ValueError("reused_at must not be before captured_at")
        if self.source_observed_at > self.reused_at:
            raise ValueError("source_observed_at must not be after reused_at")
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class ResearchTeamDomainEvidenceMemoryReuseRow:
    team_key: str
    domain_key: str
    reuse_status: str
    observation_count: Decimal
    relevant_precedent_count: Decimal
    relevant_precedent_coverage: Decimal
    stale_memory_count: Decimal
    stale_source_count: Decimal
    stale_memory_penalty: Decimal
    average_relevant_precedent_score: Decimal
    average_source_freshness_score: Decimal
    average_calibration_value: Decimal
    cross_domain_conflict_count: Decimal
    average_conflict_handling_score: Decimal
    productive_reuse_score: Decimal
    memory_reference_digests: tuple[str, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamDomainEvidenceMemoryReuseRow:
            raise TypeError(
                "ResearchTeamDomainEvidenceMemoryReuseRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchTeamDomainEvidenceMemoryReuseRow:
            raise ValueError("row must be exactly ResearchTeamDomainEvidenceMemoryReuseRow")
        _require_public_identifier("team_key", self.team_key)
        _require_public_identifier("domain_key", self.domain_key)
        _require_status("reuse_status", self.reuse_status)
        for field_name in (
            "observation_count",
            "relevant_precedent_count",
            "stale_memory_count",
            "stale_source_count",
            "cross_domain_conflict_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_whole_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "relevant_precedent_coverage",
            "stale_memory_penalty",
            "average_relevant_precedent_score",
            "average_source_freshness_score",
            "average_calibration_value",
            "average_conflict_handling_score",
            "productive_reuse_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "memory_reference_digests",
            _normalize_memory_reference_digests(self.memory_reference_digests),
        )
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _validate_row(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchTeamDomainEvidenceMemoryReuseReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamDomainEvidenceMemoryReuseReasonCodeCount:
            raise TypeError(
                "ResearchTeamDomainEvidenceMemoryReuseReasonCodeCount does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchTeamDomainEvidenceMemoryReuseReasonCodeCount:
            raise ValueError(
                "reason count must be exactly "
                "ResearchTeamDomainEvidenceMemoryReuseReasonCodeCount",
            )
        _require_member("reason_code", self.reason_code, REASON_CODES)
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
class ResearchTeamDomainEvidenceMemoryReuseReport:
    generated_at: datetime
    config_version: str
    min_relevant_precedent_score: Decimal
    min_relevant_precedent_coverage: Decimal
    stale_memory_age_seconds: Decimal
    stale_source_age_seconds: Decimal
    stale_memory_penalty_per_item: Decimal
    min_source_freshness_score: Decimal
    min_calibration_value: Decimal
    min_conflict_handling_score: Decimal
    min_productive_reuse_score: Decimal
    report_status: str
    next_review_step: str
    observation_count: Decimal
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    stale_memory_count: Decimal
    stale_source_count: Decimal
    cross_domain_conflict_count: Decimal
    average_productive_reuse_score: Decimal
    rows: tuple[ResearchTeamDomainEvidenceMemoryReuseRow, ...]
    reason_code_counts: tuple[ResearchTeamDomainEvidenceMemoryReuseReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamDomainEvidenceMemoryReuseReport:
            raise TypeError(
                "ResearchTeamDomainEvidenceMemoryReuseReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchTeamDomainEvidenceMemoryReuseReport:
            raise ValueError(
                "report must be exactly ResearchTeamDomainEvidenceMemoryReuseReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_TEAM_DOMAIN_EVIDENCE_MEMORY_REUSE_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "min_relevant_precedent_score",
            "min_relevant_precedent_coverage",
            "stale_memory_penalty_per_item",
            "min_source_freshness_score",
            "min_calibration_value",
            "min_conflict_handling_score",
            "min_productive_reuse_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("stale_memory_age_seconds", "stale_source_age_seconds"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("report_status", self.report_status)
        _require_public_identifier("next_review_step", self.next_review_step)
        for field_name in (
            "observation_count",
            "row_count",
            "pass_count",
            "watch_count",
            "block_count",
            "stale_memory_count",
            "stale_source_count",
            "cross_domain_conflict_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_whole_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_productive_reuse_score",
            _require_ratio_decimal(
                "average_productive_reuse_score",
                self.average_productive_reuse_score,
            ),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
        _validate_report(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _report_digest_from_values(_report_values_without_digest(self))
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest does not match report payload")

    @property
    def payload(self) -> dict[str, object]:
        _reject_unsafe_public_payload("report", self)
        reconstructed = _reconstruct_public_dataclass(
            self,
            ResearchTeamDomainEvidenceMemoryReuseReport,
        )
        payload = _json_ready(asdict(reconstructed))
        if type(payload) is not dict:
            raise ValueError("payload must be a JSON object")
        _validate_public_payload(payload)
        return payload


def build_research_team_domain_evidence_memory_reuse_report(
    observations: Sequence[ResearchTeamDomainEvidenceMemoryReuseObservation],
    *,
    generated_at: datetime,
    config: ResearchTeamDomainEvidenceMemoryReuseConfig | None = None,
) -> ResearchTeamDomainEvidenceMemoryReuseReport:
    """Build a local report-only domain evidence memory reuse snapshot."""

    if config is None:
        config = ResearchTeamDomainEvidenceMemoryReuseConfig()
    if type(config) is not ResearchTeamDomainEvidenceMemoryReuseConfig:
        raise ValueError("config must be a ResearchTeamDomainEvidenceMemoryReuseConfig")
    config = _reconstruct_public_dataclass(
        config,
        ResearchTeamDomainEvidenceMemoryReuseConfig,
    )
    generated_at = _as_utc("generated_at", generated_at)
    normalized_observations = _normalize_observations(observations, generated_at=generated_at)
    rows = _build_rows(normalized_observations, config=config, generated_at=generated_at)
    reason_codes = _report_reason_codes(rows)
    report_status = _status_for_reason_codes(reason_codes)
    values: dict[str, object] = {
        "generated_at": generated_at,
        "config_version": config.config_version,
        "min_relevant_precedent_score": config.min_relevant_precedent_score,
        "min_relevant_precedent_coverage": config.min_relevant_precedent_coverage,
        "stale_memory_age_seconds": config.stale_memory_age_seconds,
        "stale_source_age_seconds": config.stale_source_age_seconds,
        "stale_memory_penalty_per_item": config.stale_memory_penalty_per_item,
        "min_source_freshness_score": config.min_source_freshness_score,
        "min_calibration_value": config.min_calibration_value,
        "min_conflict_handling_score": config.min_conflict_handling_score,
        "min_productive_reuse_score": config.min_productive_reuse_score,
        "report_status": report_status,
        "next_review_step": NEXT_REVIEW_STEPS[report_status],
        "observation_count": _decimal_count(len(normalized_observations)),
        "row_count": _decimal_count(len(rows)),
        "pass_count": _status_count(rows, "pass"),
        "watch_count": _status_count(rows, "watch"),
        "block_count": _status_count(rows, "block"),
        "stale_memory_count": _sum_row_field(rows, "stale_memory_count"),
        "stale_source_count": _sum_row_field(rows, "stale_source_count"),
        "cross_domain_conflict_count": _sum_row_field(
            rows,
            "cross_domain_conflict_count",
        ),
        "average_productive_reuse_score": _weighted_row_average(
            rows,
            "productive_reuse_score",
        ),
        "rows": rows,
        "reason_code_counts": _reason_code_counts(rows, reason_codes),
        "reason_codes": reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchTeamDomainEvidenceMemoryReuseReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def research_team_domain_evidence_memory_reuse_report_payload(
    value: object,
) -> dict[str, Any]:
    if type(value) is ResearchTeamDomainEvidenceMemoryReuseReport:
        return value.payload
    elif type(value) is not dict:
        raise ValueError(
            "value must be a ResearchTeamDomainEvidenceMemoryReuseReport or JSON object",
        )
    _validate_public_payload(value)
    normalized = _json_ready(value)
    if type(normalized) is not dict:
        raise ValueError("payload must be a JSON object")
    return normalized


def _normalize_observations(
    observations: Sequence[ResearchTeamDomainEvidenceMemoryReuseObservation],
    *,
    generated_at: datetime,
) -> tuple[ResearchTeamDomainEvidenceMemoryReuseObservation, ...]:
    if isinstance(observations, (str, bytes)) or not isinstance(observations, Sequence):
        raise ValueError("observations must be a sequence")
    normalized: list[ResearchTeamDomainEvidenceMemoryReuseObservation] = []
    for observation in observations:
        if type(observation) is not ResearchTeamDomainEvidenceMemoryReuseObservation:
            raise ValueError(
                "observations must contain "
                "ResearchTeamDomainEvidenceMemoryReuseObservation",
            )
        observation = _reconstruct_public_dataclass(
            observation,
            ResearchTeamDomainEvidenceMemoryReuseObservation,
        )
        _require_hard_flags("observation", observation)
        if observation.captured_at > generated_at:
            raise ValueError("captured_at must not be after generated_at")
        if observation.reused_at > generated_at:
            raise ValueError("reused_at must not be after generated_at")
        if observation.source_observed_at > generated_at:
            raise ValueError("source_observed_at must not be after generated_at")
        normalized.append(observation)
    return tuple(
        sorted(
            normalized,
            key=_observation_sort_key,
        )
    )


def _observation_sort_key(
    item: ResearchTeamDomainEvidenceMemoryReuseObservation,
) -> tuple[object, ...]:
    return (
        item.team_key,
        item.domain_key,
        item.reused_at,
        item.internal_reference,
        item.captured_at,
        item.source_observed_at,
        item.relevant_precedent_score,
        item.source_freshness_score,
        item.calibration_value,
        item.cross_domain_conflict_count,
        item.conflict_handling_score,
        item.paper_only,
        item.report_only,
        item.readonly,
    )


def _build_rows(
    observations: tuple[ResearchTeamDomainEvidenceMemoryReuseObservation, ...],
    *,
    config: ResearchTeamDomainEvidenceMemoryReuseConfig,
    generated_at: datetime,
) -> tuple[ResearchTeamDomainEvidenceMemoryReuseRow, ...]:
    grouped: dict[tuple[str, str], list[ResearchTeamDomainEvidenceMemoryReuseObservation]] = {}
    for observation in observations:
        grouped.setdefault((observation.team_key, observation.domain_key), []).append(
            observation,
        )
    return tuple(
        _build_row(
            team_key=team_key,
            domain_key=domain_key,
            observations=tuple(grouped[(team_key, domain_key)]),
            config=config,
            generated_at=generated_at,
        )
        for team_key, domain_key in sorted(grouped)
    )


def _build_row(
    *,
    team_key: str,
    domain_key: str,
    observations: tuple[ResearchTeamDomainEvidenceMemoryReuseObservation, ...],
    config: ResearchTeamDomainEvidenceMemoryReuseConfig,
    generated_at: datetime,
) -> ResearchTeamDomainEvidenceMemoryReuseRow:
    observation_count = _decimal_count(len(observations))
    relevant_count = _decimal_count(
        sum(
            1
            for item in observations
            if item.relevant_precedent_score >= config.min_relevant_precedent_score
        ),
    )
    stale_memory_count = _decimal_count(
        sum(
            1
            for item in observations
            if _age_seconds(generated_at, item.captured_at)
            > config.stale_memory_age_seconds
        ),
    )
    stale_source_count = _decimal_count(
        sum(
            1
            for item in observations
            if _age_seconds(generated_at, item.source_observed_at)
            > config.stale_source_age_seconds
        ),
    )
    conflict_count = _quantize(
        _sum_decimals(
            tuple(item.cross_domain_conflict_count for item in observations),
        ),
    )
    conflict_observations = tuple(
        item for item in observations if item.cross_domain_conflict_count > ZERO
    )
    coverage = _ratio(relevant_count, observation_count)
    stale_penalty = _clamp_ratio(
        _multiply_decimal(
            stale_memory_count,
            config.stale_memory_penalty_per_item,
        ),
    )
    average_precedent = _average(
        tuple(item.relevant_precedent_score for item in observations),
    )
    average_freshness = _average(
        tuple(item.source_freshness_score for item in observations),
    )
    average_calibration = _average(tuple(item.calibration_value for item in observations))
    average_conflict_handling = (
        _average(tuple(item.conflict_handling_score for item in conflict_observations))
        if conflict_observations
        else ONE
    )
    productive_score = _clamp_ratio(
        _subtract_decimal(
            _divide_decimal(
                _sum_decimals(
                    (
                        coverage,
                        average_precedent,
                        average_freshness,
                        average_calibration,
                    ),
                ),
                FOUR,
            ),
            stale_penalty,
        ),
    )
    reason_codes = _row_reason_codes(
        relevant_precedent_coverage=coverage,
        stale_memory_count=stale_memory_count,
        stale_source_count=stale_source_count,
        average_source_freshness_score=average_freshness,
        average_calibration_value=average_calibration,
        cross_domain_conflict_count=conflict_count,
        average_conflict_handling_score=average_conflict_handling,
        productive_reuse_score=productive_score,
        config=config,
    )
    return ResearchTeamDomainEvidenceMemoryReuseRow(
        team_key=team_key,
        domain_key=domain_key,
        reuse_status=_status_for_reason_codes(reason_codes),
        observation_count=observation_count,
        relevant_precedent_count=relevant_count,
        relevant_precedent_coverage=coverage,
        stale_memory_count=stale_memory_count,
        stale_source_count=stale_source_count,
        stale_memory_penalty=stale_penalty,
        average_relevant_precedent_score=average_precedent,
        average_source_freshness_score=average_freshness,
        average_calibration_value=average_calibration,
        cross_domain_conflict_count=conflict_count,
        average_conflict_handling_score=average_conflict_handling,
        productive_reuse_score=productive_score,
        memory_reference_digests=tuple(
            sorted({_reference_digest(item.internal_reference) for item in observations}),
        ),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    relevant_precedent_coverage: Decimal,
    stale_memory_count: Decimal,
    stale_source_count: Decimal,
    average_source_freshness_score: Decimal,
    average_calibration_value: Decimal,
    cross_domain_conflict_count: Decimal,
    average_conflict_handling_score: Decimal,
    productive_reuse_score: Decimal,
    config: ResearchTeamDomainEvidenceMemoryReuseConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if relevant_precedent_coverage < config.min_relevant_precedent_coverage:
        reason_codes.append(INSUFFICIENT_PRECEDENT_REASON)
    if stale_memory_count > ZERO:
        reason_codes.append(STALE_MEMORY_REASON)
    if (
        stale_source_count > ZERO
        or average_source_freshness_score < config.min_source_freshness_score
    ):
        reason_codes.append(SOURCE_FRESHNESS_REASON)
    if average_calibration_value < config.min_calibration_value:
        reason_codes.append(CALIBRATION_REASON)
    if cross_domain_conflict_count > ZERO:
        if average_conflict_handling_score < config.min_conflict_handling_score:
            reason_codes.append(CONFLICT_UNRESOLVED_REASON)
        else:
            reason_codes.append(CONFLICT_HANDLED_REASON)
    if productive_reuse_score < config.min_productive_reuse_score:
        reason_codes.append(PRODUCTIVE_SCORE_REASON)
    if not reason_codes:
        reason_codes.append(PASS_REASON)
    return _combined_reason_codes(tuple(reason_codes))


def _report_reason_codes(
    rows: tuple[ResearchTeamDomainEvidenceMemoryReuseRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON,)
    return _combined_reason_codes(tuple(code for row in rows for code in row.reason_codes))


def _combined_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    if any(reason_code != PASS_REASON for reason_code in reason_codes):
        reason_codes = tuple(
            reason_code for reason_code in reason_codes if reason_code != PASS_REASON
        )
    return tuple(
        sorted(
            set(reason_codes),
            key=lambda reason_code: REASON_CODE_RANK[reason_code],
        )
    )


def _reason_code_counts(
    rows: tuple[ResearchTeamDomainEvidenceMemoryReuseRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchTeamDomainEvidenceMemoryReuseReasonCodeCount, ...]:
    if reason_codes == (EMPTY_REASON,):
        return (
            ResearchTeamDomainEvidenceMemoryReuseReasonCodeCount(
                reason_code=EMPTY_REASON,
                count=ONE,
            ),
        )
    counter: Counter[str] = Counter()
    for row in rows:
        for reason_code in row.reason_codes:
            if reason_code in reason_codes:
                counter[reason_code] += 1
    return tuple(
        ResearchTeamDomainEvidenceMemoryReuseReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(counter[reason_code]),
        )
        for reason_code in reason_codes
    )


def _status_for_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in BLOCK_REASONS for reason_code in reason_codes):
        return "block"
    if any(reason_code in WATCH_REASONS for reason_code in reason_codes):
        return "watch"
    return "pass"


def _status_count(
    rows: tuple[ResearchTeamDomainEvidenceMemoryReuseRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.reuse_status == status))


def _validate_row(
    row: ResearchTeamDomainEvidenceMemoryReuseRow,
    *,
    config: ResearchTeamDomainEvidenceMemoryReuseConfig | None = None,
) -> None:
    if row.observation_count <= ZERO:
        raise ValueError("observation_count must be positive")
    if row.relevant_precedent_count > row.observation_count:
        raise ValueError("relevant_precedent_count cannot exceed observation_count")
    for field_name in ("stale_memory_count", "stale_source_count"):
        if getattr(row, field_name) > row.observation_count:
            raise ValueError(f"{field_name} cannot exceed observation_count")
    expected_coverage = _ratio(row.relevant_precedent_count, row.observation_count)
    if row.relevant_precedent_coverage != expected_coverage:
        raise ValueError("relevant_precedent_coverage must match counts")
    expected_productive_score = _clamp_ratio(
        _subtract_decimal(
            _divide_decimal(
                _sum_decimals(
                    (
                        row.relevant_precedent_coverage,
                        row.average_relevant_precedent_score,
                        row.average_source_freshness_score,
                        row.average_calibration_value,
                    ),
                ),
                FOUR,
            ),
            row.stale_memory_penalty,
        ),
    )
    if row.productive_reuse_score != expected_productive_score:
        raise ValueError("productive_reuse_score must match row components")
    if not row.memory_reference_digests:
        raise ValueError("memory_reference_digests must not be empty")
    if len(row.memory_reference_digests) > int(row.observation_count):
        raise ValueError("memory_reference_digests cannot exceed observation_count")
    if row.reuse_status != _status_for_reason_codes(row.reason_codes):
        raise ValueError("reuse_status must match reason_codes")
    if (row.stale_memory_count > ZERO) != (STALE_MEMORY_REASON in row.reason_codes):
        raise ValueError("stale memory reason must match stale_memory_count")
    if (
        row.stale_source_count > ZERO
        and SOURCE_FRESHNESS_REASON not in row.reason_codes
    ):
        raise ValueError("stale source count requires source freshness reason")
    conflict_reason_count = sum(
        reason_code in row.reason_codes
        for reason_code in (CONFLICT_HANDLED_REASON, CONFLICT_UNRESOLVED_REASON)
    )
    if row.cross_domain_conflict_count == ZERO and conflict_reason_count:
        raise ValueError("conflict reason requires cross_domain_conflict_count")
    if (
        row.cross_domain_conflict_count == ZERO
        and row.average_conflict_handling_score != ONE
    ):
        raise ValueError(
            "average_conflict_handling_score must be one without conflicts",
        )
    if row.cross_domain_conflict_count > ZERO and conflict_reason_count != 1:
        raise ValueError("cross_domain_conflict_count requires one conflict reason")
    if PASS_REASON in row.reason_codes and row.reason_codes != (PASS_REASON,):
        raise ValueError("pass reason must not be combined with other reasons")
    if row.reuse_status == "pass" and row.reason_codes != (PASS_REASON,):
        raise ValueError("pass rows must have only the pass reason")
    if config is not None:
        if type(config) is not ResearchTeamDomainEvidenceMemoryReuseConfig:
            raise ValueError(
                "config must be exactly ResearchTeamDomainEvidenceMemoryReuseConfig",
            )
        _validate_precedent_summary(row, config)
        expected_stale_memory_penalty = _clamp_ratio(
            _multiply_decimal(
                row.stale_memory_count,
                config.stale_memory_penalty_per_item,
            ),
        )
        if row.stale_memory_penalty != expected_stale_memory_penalty:
            raise ValueError("stale_memory_penalty must match config and count")
        expected_reason_codes = _row_reason_codes(
            relevant_precedent_coverage=row.relevant_precedent_coverage,
            stale_memory_count=row.stale_memory_count,
            stale_source_count=row.stale_source_count,
            average_source_freshness_score=row.average_source_freshness_score,
            average_calibration_value=row.average_calibration_value,
            cross_domain_conflict_count=row.cross_domain_conflict_count,
            average_conflict_handling_score=row.average_conflict_handling_score,
            productive_reuse_score=row.productive_reuse_score,
            config=config,
        )
        if row.reason_codes != expected_reason_codes:
            raise ValueError("reason_codes must match row values and config")
        expected_status = _status_for_reason_codes(expected_reason_codes)
        if row.reuse_status != expected_status:
            raise ValueError("reuse_status must match row values and config")


def _validate_precedent_summary(
    row: ResearchTeamDomainEvidenceMemoryReuseRow,
    config: ResearchTeamDomainEvidenceMemoryReuseConfig,
) -> None:
    if config.min_relevant_precedent_score == ZERO:
        if row.relevant_precedent_count != row.observation_count:
            raise ValueError(
                "relevant_precedent_count must include every observation at a zero floor",
            )
        return

    minimum_average = _clamp_ratio(
        _divide_decimal(
            _multiply_decimal(
                row.relevant_precedent_count,
                config.min_relevant_precedent_score,
            ),
            row.observation_count,
        ),
    )
    if row.average_relevant_precedent_score < minimum_average:
        raise ValueError(
            "average_relevant_precedent_score is below the count-implied minimum",
        )

    if row.relevant_precedent_count == row.observation_count:
        return
    non_relevant_count = _subtract_decimal(
        row.observation_count,
        row.relevant_precedent_count,
    )
    maximum_non_relevant_score = _subtract_decimal(
        config.min_relevant_precedent_score,
        QUANT,
    )
    maximum_average = _clamp_ratio(
        _divide_decimal(
            _sum_decimals(
                (
                    _multiply_decimal(row.relevant_precedent_count, ONE),
                    _multiply_decimal(
                        non_relevant_count,
                        maximum_non_relevant_score,
                    ),
                ),
            ),
            row.observation_count,
        ),
    )
    if row.average_relevant_precedent_score > maximum_average:
        raise ValueError(
            "average_relevant_precedent_score exceeds the count-implied maximum",
        )


def _validate_report(report: ResearchTeamDomainEvidenceMemoryReuseReport) -> None:
    _require_hard_flags("report", report)
    config = _config_from_report(report)
    for row in report.rows:
        _require_hard_flags("row", row)
        _validate_row(row, config=config)
    for item in report.reason_code_counts:
        _require_hard_flags("reason count", item)
        _require_member("reason_code", item.reason_code, REASON_CODES)
        normalized_count = _require_whole_count_decimal("count", item.count)
        if normalized_count != item.count or normalized_count <= ZERO:
            raise ValueError("reason code count must be a positive whole Decimal")
    if report.observation_count != _sum_row_field(report.rows, "observation_count"):
        raise ValueError("observation_count must match rows")
    if report.row_count != _decimal_count(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, "block"):
        raise ValueError("block_count must match rows")
    if report.stale_memory_count != _sum_row_field(
        report.rows,
        "stale_memory_count",
    ):
        raise ValueError("stale_memory_count must match rows")
    if report.stale_source_count != _sum_row_field(
        report.rows,
        "stale_source_count",
    ):
        raise ValueError("stale_source_count must match rows")
    if report.cross_domain_conflict_count != _sum_row_field(
        report.rows,
        "cross_domain_conflict_count",
    ):
        raise ValueError("cross_domain_conflict_count must match rows")
    if report.average_productive_reuse_score != _weighted_row_average(
        report.rows,
        "productive_reuse_score",
    ):
        raise ValueError("average_productive_reuse_score must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows, report.reason_codes):
        raise ValueError("reason_code_counts must match rows")
    expected_status = _status_for_reason_codes(report.reason_codes)
    if report.report_status != expected_status:
        raise ValueError("report_status must match reason_codes")
    if report.next_review_step != NEXT_REVIEW_STEPS[report.report_status]:
        raise ValueError("next_review_step must match report_status")


def _config_from_report(
    report: ResearchTeamDomainEvidenceMemoryReuseReport,
) -> ResearchTeamDomainEvidenceMemoryReuseConfig:
    return ResearchTeamDomainEvidenceMemoryReuseConfig(
        config_version=report.config_version,
        min_relevant_precedent_score=report.min_relevant_precedent_score,
        min_relevant_precedent_coverage=report.min_relevant_precedent_coverage,
        stale_memory_age_seconds=report.stale_memory_age_seconds,
        stale_source_age_seconds=report.stale_source_age_seconds,
        stale_memory_penalty_per_item=report.stale_memory_penalty_per_item,
        min_source_freshness_score=report.min_source_freshness_score,
        min_calibration_value=report.min_calibration_value,
        min_conflict_handling_score=report.min_conflict_handling_score,
        min_productive_reuse_score=report.min_productive_reuse_score,
    )


def _normalize_rows(
    rows: Sequence[ResearchTeamDomainEvidenceMemoryReuseRow],
) -> tuple[ResearchTeamDomainEvidenceMemoryReuseRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
        raise ValueError("rows must be a sequence")
    normalized: list[ResearchTeamDomainEvidenceMemoryReuseRow] = []
    seen_keys: set[tuple[str, str]] = set()
    for row in rows:
        if type(row) is not ResearchTeamDomainEvidenceMemoryReuseRow:
            raise ValueError("rows must contain ResearchTeamDomainEvidenceMemoryReuseRow")
        row = _reconstruct_public_dataclass(
            row,
            ResearchTeamDomainEvidenceMemoryReuseRow,
        )
        _require_hard_flags("row", row)
        _validate_row(row)
        key = (row.team_key, row.domain_key)
        if key in seen_keys:
            raise ValueError("team_key and domain_key rows must be unique")
        seen_keys.add(key)
        normalized.append(row)
    return tuple(sorted(normalized, key=lambda row: (row.team_key, row.domain_key)))


def _normalize_reason_code_counts(
    reason_code_counts: Sequence[ResearchTeamDomainEvidenceMemoryReuseReasonCodeCount],
) -> tuple[ResearchTeamDomainEvidenceMemoryReuseReasonCodeCount, ...]:
    if isinstance(reason_code_counts, (str, bytes)) or not isinstance(
        reason_code_counts,
        Sequence,
    ):
        raise ValueError("reason_code_counts must be a sequence")
    normalized: list[ResearchTeamDomainEvidenceMemoryReuseReasonCodeCount] = []
    for item in reason_code_counts:
        if type(item) is not ResearchTeamDomainEvidenceMemoryReuseReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchTeamDomainEvidenceMemoryReuseReasonCodeCount",
            )
        item = _reconstruct_public_dataclass(
            item,
            ResearchTeamDomainEvidenceMemoryReuseReasonCodeCount,
        )
        _require_hard_flags("reason count", item)
        normalized.append(item)
    return tuple(sorted(normalized, key=lambda item: REASON_CODE_RANK[item.reason_code]))


def _reconstruct_public_dataclass(value: object, dataclass_type: type[Any]) -> Any:
    return dataclass_type(
        **{field.name: getattr(value, field.name) for field in fields(dataclass_type)},
    )


def _normalize_reason_codes(reason_codes: Sequence[str]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)) or not isinstance(reason_codes, Sequence):
        raise ValueError("reason_codes must be a sequence")
    normalized: list[str] = []
    for reason_code in reason_codes:
        _require_member("reason_code", reason_code, REASON_CODES)
        if reason_code not in normalized:
            normalized.append(reason_code)
    return tuple(
        reason_code for reason_code in REASON_CODES if reason_code in normalized
    )


def _normalize_memory_reference_digests(
    values: Sequence[str],
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Sequence):
        raise ValueError("memory_reference_digests must be a sequence")
    normalized: list[str] = []
    for value in values:
        if type(value) is not str or not value.startswith("sha256:"):
            raise ValueError("memory_reference_digests must contain sha256 digests")
        digest = value.removeprefix("sha256:")
        _require_sha256_digest("memory_reference_digests", digest)
        if value not in normalized:
            normalized.append(value)
    return tuple(sorted(normalized))


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in PHASE_FLAG_FIELDS:
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_member(field_name: str, value: object, members: tuple[str, ...]) -> str:
    if type(value) is not str or value not in members:
        raise ValueError(f"{field_name} must be supported")
    return value


def _require_status(field_name: str, value: object) -> str:
    return _require_member(field_name, value, STATUSES)


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    _reject_unsafe_public_string(field_name, value)
    return value


def _require_private_reference(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} must be non-empty")
    return value


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str or not DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    return value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    raw = _require_decimal(field_name, value)
    if raw < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return _quantize(raw)


def _require_whole_count_decimal(field_name: str, value: object) -> Decimal:
    raw = _require_decimal(field_name, value)
    if raw < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    with localcontext(DECIMAL_CONTEXT):
        is_whole = raw == raw.to_integral_value()
    if not is_whole:
        raise ValueError(f"{field_name} must be a whole count")
    return _quantize(raw)


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    raw = _require_decimal(field_name, value)
    if raw < ZERO or raw > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return _quantize(raw)


def _decimal_count(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be nonnegative")
    return _quantize(Decimal(value))


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _quantize(
        _divide_decimal(
            _sum_decimals(values),
            Decimal(len(values)),
        ),
    )


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= ZERO:
        return ZERO
    return _clamp_ratio(_divide_decimal(numerator, denominator))


def _sum_decimals(values: tuple[Decimal, ...]) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return sum(values, ZERO)


def _sum_row_field(
    rows: tuple[ResearchTeamDomainEvidenceMemoryReuseRow, ...],
    field_name: str,
) -> Decimal:
    return _quantize(
        _sum_decimals(tuple(getattr(row, field_name) for row in rows)),
    )


def _multiply_decimal(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return left * right


def _divide_decimal(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        raise ValueError("Decimal denominator must be nonzero")
    with localcontext(DECIMAL_CONTEXT):
        return numerator / denominator


def _subtract_decimal(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return left - right


def _weighted_row_average(
    rows: tuple[ResearchTeamDomainEvidenceMemoryReuseRow, ...],
    field_name: str,
) -> Decimal:
    total_weight = _sum_row_field(rows, "observation_count")
    if total_weight <= ZERO:
        return ZERO
    weighted_total = _sum_decimals(
        tuple(
            _multiply_decimal(getattr(row, field_name), row.observation_count)
            for row in rows
        ),
    )
    return _clamp_ratio(_divide_decimal(weighted_total, total_weight))


def _clamp_ratio(value: Decimal) -> Decimal:
    if value < ZERO:
        return ZERO
    if value > ONE:
        return ONE
    return _quantize(value)


def _quantize(value: Decimal) -> Decimal:
    if type(value) is not Decimal or not value.is_finite():
        raise ValueError("Decimal value must be finite")
    try:
        with localcontext(DECIMAL_CONTEXT) as context:
            normalized = value.quantize(
                QUANT,
                rounding=ROUND_HALF_UP,
                context=context,
            )
    except InvalidOperation as exc:
        raise ValueError("Decimal value must be quantizable") from exc
    if normalized == ZERO:
        return ZERO
    return normalized


def _age_seconds(later: datetime, earlier: datetime) -> Decimal:
    delta = later - earlier
    with localcontext(DECIMAL_CONTEXT):
        seconds = (
            Decimal(delta.days * 86400 + delta.seconds)
            + Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND
        )
    return _require_nonnegative_decimal("age_seconds", seconds)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _reference_digest(value: str) -> str:
    return f"sha256:{hashlib.sha256(value.encode('utf-8')).hexdigest()}"


def _report_values_without_digest(
    report: ResearchTeamDomainEvidenceMemoryReuseReport,
) -> dict[str, object]:
    values = asdict(report)
    values.pop("derived_validation_digest", None)
    return values


def _report_digest_from_values(values: Mapping[str, object]) -> str:
    payload = _json_ready(values)
    _reject_unsafe_public_payload(
        "derived_validation_digest payload",
        payload,
        allow_json_containers=True,
    )
    canonical = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("Decimal payload value must be finite")
        return str(_quantize(value))
    if type(value) is datetime:
        return _as_utc("datetime payload value", value).isoformat()
    if type(value) is bool or type(value) is str:
        return value
    if type(value) is int or isinstance(value, float):
        raise ValueError("numeric payload values must be Decimal strings")
    if isinstance(value, Mapping):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("payload value is not JSON serializable")


def _validate_payload_flags(payload: Mapping[str, object], label: str) -> None:
    for field_name in PHASE_FLAG_FIELDS:
        if payload.get(field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _validate_public_payload(payload: dict[str, Any]) -> None:
    _require_exact_json_types("payload", payload)
    _reject_unsafe_public_payload("payload", payload, allow_json_containers=True)
    _validate_payload_flags(payload, "payload")
    reconstructed = _report_from_public_payload(payload)
    canonical_payload = _json_ready(asdict(reconstructed))
    if canonical_payload != payload:
        raise ValueError("payload must use canonical report representation")


def _require_exact_json_types(
    label: str,
    value: object,
    path: str = "",
    active_container_ids: set[int] | None = None,
    depth: int = 0,
) -> None:
    if depth > MAX_PUBLIC_PAYLOAD_DEPTH:
        raise ValueError("public payload nesting is too deep")
    if active_container_ids is None:
        active_container_ids = set()
    current_path = path or label
    if type(value) is dict:
        container_id = id(value)
        if container_id in active_container_ids:
            raise ValueError("payload must not contain cyclic JSON containers")
        active_container_ids.add(container_id)
        try:
            for key, item in value.items():
                if type(key) is not str:
                    raise ValueError(f"{current_path} must use exact JSON types")
                _require_exact_json_types(
                    label,
                    item,
                    key if not path else f"{path}.{key}",
                    active_container_ids,
                    depth + 1,
                )
        finally:
            active_container_ids.remove(container_id)
        return
    if type(value) is list:
        container_id = id(value)
        if container_id in active_container_ids:
            raise ValueError("payload must not contain cyclic JSON containers")
        active_container_ids.add(container_id)
        try:
            for index, item in enumerate(value):
                _require_exact_json_types(
                    label,
                    item,
                    f"{current_path}[{index}]",
                    active_container_ids,
                    depth + 1,
                )
        finally:
            active_container_ids.remove(container_id)
        return
    if value is None or type(value) is str or type(value) is bool:
        return
    if type(value) is int or isinstance(value, (float, Decimal)):
        raise ValueError(
            f"{current_path} must use exact JSON scalar and container types; "
            "Decimal-derived numerics must be canonical Decimal strings",
        )
    raise ValueError(f"{current_path} must use exact JSON scalar and container types")


def _report_from_public_payload(
    payload: dict[str, Any],
) -> ResearchTeamDomainEvidenceMemoryReuseReport:
    _require_exact_payload_schema(
        "report payload",
        payload,
        ResearchTeamDomainEvidenceMemoryReuseReport,
    )
    digest = payload["derived_validation_digest"]
    _require_sha256_digest("derived_validation_digest", digest)
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest")
    if digest != _report_digest_from_values(unsigned):
        raise ValueError("derived_validation_digest does not match report payload")
    rows_value = payload["rows"]
    if type(rows_value) is not list:
        raise ValueError("rows must be a list")
    reason_counts_value = payload["reason_code_counts"]
    if type(reason_counts_value) is not list:
        raise ValueError("reason_code_counts must be a list")
    return ResearchTeamDomainEvidenceMemoryReuseReport(
        generated_at=_datetime_from_public("generated_at", payload["generated_at"]),
        config_version=_string_from_public("config_version", payload["config_version"]),
        min_relevant_precedent_score=_decimal_from_public(
            "min_relevant_precedent_score",
            payload["min_relevant_precedent_score"],
        ),
        min_relevant_precedent_coverage=_decimal_from_public(
            "min_relevant_precedent_coverage",
            payload["min_relevant_precedent_coverage"],
        ),
        stale_memory_age_seconds=_decimal_from_public(
            "stale_memory_age_seconds",
            payload["stale_memory_age_seconds"],
        ),
        stale_source_age_seconds=_decimal_from_public(
            "stale_source_age_seconds",
            payload["stale_source_age_seconds"],
        ),
        stale_memory_penalty_per_item=_decimal_from_public(
            "stale_memory_penalty_per_item",
            payload["stale_memory_penalty_per_item"],
        ),
        min_source_freshness_score=_decimal_from_public(
            "min_source_freshness_score",
            payload["min_source_freshness_score"],
        ),
        min_calibration_value=_decimal_from_public(
            "min_calibration_value",
            payload["min_calibration_value"],
        ),
        min_conflict_handling_score=_decimal_from_public(
            "min_conflict_handling_score",
            payload["min_conflict_handling_score"],
        ),
        min_productive_reuse_score=_decimal_from_public(
            "min_productive_reuse_score",
            payload["min_productive_reuse_score"],
        ),
        report_status=_string_from_public("report_status", payload["report_status"]),
        next_review_step=_string_from_public(
            "next_review_step",
            payload["next_review_step"],
        ),
        observation_count=_decimal_from_public(
            "observation_count",
            payload["observation_count"],
        ),
        row_count=_decimal_from_public("row_count", payload["row_count"]),
        pass_count=_decimal_from_public("pass_count", payload["pass_count"]),
        watch_count=_decimal_from_public("watch_count", payload["watch_count"]),
        block_count=_decimal_from_public("block_count", payload["block_count"]),
        stale_memory_count=_decimal_from_public(
            "stale_memory_count",
            payload["stale_memory_count"],
        ),
        stale_source_count=_decimal_from_public(
            "stale_source_count",
            payload["stale_source_count"],
        ),
        cross_domain_conflict_count=_decimal_from_public(
            "cross_domain_conflict_count",
            payload["cross_domain_conflict_count"],
        ),
        average_productive_reuse_score=_decimal_from_public(
            "average_productive_reuse_score",
            payload["average_productive_reuse_score"],
        ),
        rows=tuple(_row_from_public_payload(row) for row in rows_value),
        reason_code_counts=tuple(
            _reason_count_from_public_payload(item) for item in reason_counts_value
        ),
        reason_codes=_string_tuple_from_public(
            "reason_codes",
            payload["reason_codes"],
        ),
        derived_validation_digest=digest,
        paper_only=_true_flag_from_public("paper_only", payload["paper_only"]),
        report_only=_true_flag_from_public("report_only", payload["report_only"]),
        readonly=_true_flag_from_public("readonly", payload["readonly"]),
    )


def _row_from_public_payload(
    value: object,
) -> ResearchTeamDomainEvidenceMemoryReuseRow:
    if type(value) is not dict:
        raise ValueError("row payload must be a dict")
    _require_exact_payload_schema(
        "row payload",
        value,
        ResearchTeamDomainEvidenceMemoryReuseRow,
    )
    return ResearchTeamDomainEvidenceMemoryReuseRow(
        team_key=_string_from_public("team_key", value["team_key"]),
        domain_key=_string_from_public("domain_key", value["domain_key"]),
        reuse_status=_string_from_public("reuse_status", value["reuse_status"]),
        observation_count=_decimal_from_public(
            "observation_count",
            value["observation_count"],
        ),
        relevant_precedent_count=_decimal_from_public(
            "relevant_precedent_count",
            value["relevant_precedent_count"],
        ),
        relevant_precedent_coverage=_decimal_from_public(
            "relevant_precedent_coverage",
            value["relevant_precedent_coverage"],
        ),
        stale_memory_count=_decimal_from_public(
            "stale_memory_count",
            value["stale_memory_count"],
        ),
        stale_source_count=_decimal_from_public(
            "stale_source_count",
            value["stale_source_count"],
        ),
        stale_memory_penalty=_decimal_from_public(
            "stale_memory_penalty",
            value["stale_memory_penalty"],
        ),
        average_relevant_precedent_score=_decimal_from_public(
            "average_relevant_precedent_score",
            value["average_relevant_precedent_score"],
        ),
        average_source_freshness_score=_decimal_from_public(
            "average_source_freshness_score",
            value["average_source_freshness_score"],
        ),
        average_calibration_value=_decimal_from_public(
            "average_calibration_value",
            value["average_calibration_value"],
        ),
        cross_domain_conflict_count=_decimal_from_public(
            "cross_domain_conflict_count",
            value["cross_domain_conflict_count"],
        ),
        average_conflict_handling_score=_decimal_from_public(
            "average_conflict_handling_score",
            value["average_conflict_handling_score"],
        ),
        productive_reuse_score=_decimal_from_public(
            "productive_reuse_score",
            value["productive_reuse_score"],
        ),
        memory_reference_digests=_string_tuple_from_public(
            "memory_reference_digests",
            value["memory_reference_digests"],
        ),
        reason_codes=_string_tuple_from_public("reason_codes", value["reason_codes"]),
        paper_only=_true_flag_from_public("paper_only", value["paper_only"]),
        report_only=_true_flag_from_public("report_only", value["report_only"]),
        readonly=_true_flag_from_public("readonly", value["readonly"]),
    )


def _reason_count_from_public_payload(
    value: object,
) -> ResearchTeamDomainEvidenceMemoryReuseReasonCodeCount:
    if type(value) is not dict:
        raise ValueError("reason count payload must be a dict")
    _require_exact_payload_schema(
        "reason count payload",
        value,
        ResearchTeamDomainEvidenceMemoryReuseReasonCodeCount,
    )
    return ResearchTeamDomainEvidenceMemoryReuseReasonCodeCount(
        reason_code=_string_from_public("reason_code", value["reason_code"]),
        count=_decimal_from_public("count", value["count"]),
        paper_only=_true_flag_from_public("paper_only", value["paper_only"]),
        report_only=_true_flag_from_public("report_only", value["report_only"]),
        readonly=_true_flag_from_public("readonly", value["readonly"]),
    )


def _require_exact_payload_schema(
    label: str,
    payload: Mapping[str, object],
    dataclass_type: type[Any],
) -> None:
    expected = tuple(field.name for field in fields(dataclass_type))
    if tuple(payload) != expected:
        raise ValueError(f"{label} must use exact schema in canonical order")


def _decimal_from_public(field_name: str, value: object) -> Decimal:
    if type(value) is not str or not PUBLIC_DECIMAL_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a canonical Decimal string")
    return Decimal(value)


def _datetime_from_public(field_name: str, value: object) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a canonical UTC datetime string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(
            f"{field_name} must be a canonical UTC datetime string",
        ) from exc
    normalized = _as_utc(field_name, parsed)
    if normalized.isoformat() != value:
        raise ValueError(f"{field_name} must be a canonical UTC datetime string")
    return normalized


def _string_from_public(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    return value


def _string_tuple_from_public(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a list")
    return tuple(_string_from_public(field_name, item) for item in value)


def _true_flag_from_public(field_name: str, value: object) -> bool:
    if value is not True:
        raise ValueError(f"{field_name} must be True")
    return True


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    path: str = "",
    *,
    allow_json_containers: bool = False,
) -> None:
    current_path = path or label
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            if field.name == "internal_reference":
                continue
            _reject_unsafe_public_key(field.name, current_path)
            _reject_unsafe_public_payload(
                label,
                getattr(value, field.name),
                field.name if not path else f"{path}.{field.name}",
                allow_json_containers=allow_json_containers,
            )
        return
    if isinstance(value, Mapping):
        if not allow_json_containers:
            raise ValueError(f"{current_path} must remain constructor-normalized")
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _reject_unsafe_public_key(key, current_path)
            _reject_unsafe_public_payload(
                label,
                item,
                key if not path else f"{path}.{key}",
                allow_json_containers=True,
            )
        return
    if isinstance(value, (list, tuple)):
        if type(value) is list and not allow_json_containers:
            raise ValueError(f"{current_path} must remain constructor-normalized")
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(
                label,
                item,
                f"{current_path}[{index}]",
                allow_json_containers=allow_json_containers,
            )
        return
    if type(value) is str:
        _reject_unsafe_public_string(current_path, value)
        return
    if type(value) is bool or value is None or type(value) is Decimal or type(value) is datetime:
        return
    raise ValueError(f"{current_path} is not a supported public payload value")


def _reject_unsafe_public_key(key: str, path: str) -> None:
    lowered = key.lower()
    if any(term in lowered for term in UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"{path}.{key} has unsafe public field")


def _reject_unsafe_public_string(field_name: str, value: str) -> None:
    lowered = value.lower()
    if "://" in lowered or "?" in lowered or "@" in lowered:
        raise ValueError(f"{field_name} has unsafe public value")
    if any(term in lowered for term in UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"{field_name} has unsafe public value")
