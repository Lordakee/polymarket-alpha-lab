"""Phase 1 report-only source-family independence score."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
import re
from typing import Any, Mapping, Sequence


DEFAULT_RESEARCH_PACKET_SOURCE_FAMILY_INDEPENDENCE_SCORE_V2_CONFIG_VERSION = (
    "research-packet-source-family-independence-score-v2"
)

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_SCORE_STATUSES = frozenset(("strong", "watch", "blocked"))
_PHASE_FLAG_FIELDS = frozenset(("paper_only", "report_only", "readonly"))
_UNSAFE_PUBLIC_TERMS = (
    "live",
    "auth",
    "wallet",
    "order",
    "network",
    "database",
    "persist",
    "signing",
    "mutation",
    "buy",
    "sell",
    "trade",
)
_REASON_CODE_SEQUENCE = (
    "empty_sources",
    "family_count_below_floor",
    "family_count_met",
    "shared_ownership_or_derivation_risk",
    "ownership_derivation_clear",
    "official_source_missing",
    "official_source_covered",
    "duplicate_claims_present",
    "duplicate_claims_clear",
    "stale_sources_present",
    "sources_current",
    "contradiction_severity_present",
    "contradictions_clear",
    "independence_score_strong",
    "independence_score_watch",
    "independence_score_blocked",
)


@dataclass(frozen=True)
class ResearchPacketSourceFamilyIndependenceScoreConfig:
    config_version: str = (
        DEFAULT_RESEARCH_PACKET_SOURCE_FAMILY_INDEPENDENCE_SCORE_V2_CONFIG_VERSION
    )
    required_distinct_family_count: Decimal = Decimal("4.000000")
    stale_after_seconds: Decimal = Decimal("172800.000000")
    min_strong_score: Decimal = Decimal("0.750000")
    min_watch_score: Decimal = Decimal("0.500000")
    distinct_family_count_weight: Decimal = Decimal("0.300000")
    ownership_derivation_weight: Decimal = Decimal("0.200000")
    official_source_weight: Decimal = Decimal("0.150000")
    duplicate_claim_weight: Decimal = Decimal("0.150000")
    stale_source_weight: Decimal = Decimal("0.100000")
    contradiction_weight: Decimal = Decimal("0.100000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchPacketSourceFamilyIndependenceScoreConfig:
            raise TypeError(
                "ResearchPacketSourceFamilyIndependenceScoreConfig does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchPacketSourceFamilyIndependenceScoreConfig:
            raise ValueError(
                "config must be exactly "
                "ResearchPacketSourceFamilyIndependenceScoreConfig",
            )
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_PACKET_SOURCE_FAMILY_INDEPENDENCE_SCORE_V2_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        object.__setattr__(
            self,
            "required_distinct_family_count",
            _require_positive_count_decimal(
                "required_distinct_family_count",
                self.required_distinct_family_count,
            ),
        )
        object.__setattr__(
            self,
            "stale_after_seconds",
            _require_positive_count_decimal(
                "stale_after_seconds",
                self.stale_after_seconds,
            ),
        )
        for field_name in (
            "min_strong_score",
            "min_watch_score",
            "distinct_family_count_weight",
            "ownership_derivation_weight",
            "official_source_weight",
            "duplicate_claim_weight",
            "stale_source_weight",
            "contradiction_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.min_strong_score < self.min_watch_score:
            raise ValueError("min_strong_score must be at least min_watch_score")
        _validate_weight_sum(self)
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchPacketSourceFamilyIndependenceScoreSource:
    packet_id: str
    source_id: str
    source_family: str
    owner_family: str
    derivation_family: str | None
    claim_fingerprint: str
    is_official_source: bool
    source_age_seconds: Decimal
    contradiction_severity: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchPacketSourceFamilyIndependenceScoreSource:
            raise TypeError(
                "ResearchPacketSourceFamilyIndependenceScoreSource does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchPacketSourceFamilyIndependenceScoreSource:
            raise ValueError(
                "source must be exactly "
                "ResearchPacketSourceFamilyIndependenceScoreSource",
            )
        for field_name in (
            "packet_id",
            "source_id",
            "source_family",
            "owner_family",
            "claim_fingerprint",
        ):
            _require_public_identifier(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "derivation_family",
            _normalize_optional_public_identifier(
                "derivation_family",
                self.derivation_family,
            ),
        )
        object.__setattr__(
            self,
            "is_official_source",
            _require_bool("is_official_source", self.is_official_source),
        )
        object.__setattr__(
            self,
            "source_age_seconds",
            _require_nonnegative_count_decimal(
                "source_age_seconds",
                self.source_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "contradiction_severity",
            _require_ratio_decimal(
                "contradiction_severity",
                self.contradiction_severity,
            ),
        )
        _require_hard_flags("source", self)
        _reject_unsafe_public_payload("source", self)


@dataclass(frozen=True)
class ResearchPacketSourceFamilyIndependenceScoreReport:
    packet_id: str
    config_version: str
    source_count: Decimal
    distinct_source_family_count: Decimal
    required_distinct_family_count: Decimal
    shared_ownership_derivation_source_count: Decimal
    official_source_count: Decimal
    duplicate_claim_count: Decimal
    stale_source_count: Decimal
    stale_after_seconds: Decimal
    min_strong_score: Decimal
    min_watch_score: Decimal
    distinct_family_count_weight: Decimal
    ownership_derivation_weight: Decimal
    official_source_weight: Decimal
    duplicate_claim_weight: Decimal
    stale_source_weight: Decimal
    contradiction_weight: Decimal
    family_count_score: Decimal
    shared_ownership_derivation_risk: Decimal
    official_source_coverage: Decimal
    duplicate_claim_ratio: Decimal
    stale_source_ratio: Decimal
    contradiction_severity: Decimal
    independence_score: Decimal
    score_status: str
    reason_codes: tuple[str, ...]
    source_evidence_digest: str
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchPacketSourceFamilyIndependenceScoreReport:
            raise TypeError(
                "ResearchPacketSourceFamilyIndependenceScoreReport does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchPacketSourceFamilyIndependenceScoreReport:
            raise ValueError(
                "report must be exactly "
                "ResearchPacketSourceFamilyIndependenceScoreReport",
            )
        _require_public_identifier("packet_id", self.packet_id)
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_PACKET_SOURCE_FAMILY_INDEPENDENCE_SCORE_V2_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "source_count",
            "distinct_source_family_count",
            "shared_ownership_derivation_source_count",
            "official_source_count",
            "duplicate_claim_count",
            "stale_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "required_distinct_family_count",
            "stale_after_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_strong_score",
            "min_watch_score",
            "distinct_family_count_weight",
            "ownership_derivation_weight",
            "official_source_weight",
            "duplicate_claim_weight",
            "stale_source_weight",
            "contradiction_weight",
            "family_count_score",
            "shared_ownership_derivation_risk",
            "official_source_coverage",
            "duplicate_claim_ratio",
            "stale_source_ratio",
            "contradiction_severity",
            "independence_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.min_strong_score < self.min_watch_score:
            raise ValueError("min_strong_score must be at least min_watch_score")
        _validate_weight_sum(self)
        _require_score_status("score_status", self.score_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _require_sha256_digest("source_evidence_digest", self.source_evidence_digest)
        _require_sha256_digest(
            "derived_validation_digest",
            self.derived_validation_digest,
        )
        _validate_report_consistency(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _report_digest_from_values(_report_values_without_digest(self))
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest does not match report payload")

    @property
    def payload(self) -> dict[str, object]:
        payload = _json_ready(asdict(self))
        _reject_unsafe_public_payload(
            "ResearchPacketSourceFamilyIndependenceScoreReport.payload",
            payload,
            allow_json_containers=True,
        )
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        return payload


@dataclass(frozen=True)
class _Metrics:
    source_count: Decimal
    distinct_source_family_count: Decimal
    shared_ownership_derivation_source_count: Decimal
    official_source_count: Decimal
    duplicate_claim_count: Decimal
    stale_source_count: Decimal
    family_count_score: Decimal
    shared_ownership_derivation_risk: Decimal
    official_source_coverage: Decimal
    duplicate_claim_ratio: Decimal
    stale_source_ratio: Decimal
    contradiction_severity: Decimal
    independence_score: Decimal


def build_research_packet_source_family_independence_score_v2_report(
    sources: Sequence[ResearchPacketSourceFamilyIndependenceScoreSource],
    *,
    packet_id: str,
    config: ResearchPacketSourceFamilyIndependenceScoreConfig | None = None,
) -> ResearchPacketSourceFamilyIndependenceScoreReport:
    """Build a deterministic local report-only source-family independence score."""

    packet_id = _require_public_identifier("packet_id", packet_id)
    if config is None:
        config = ResearchPacketSourceFamilyIndependenceScoreConfig()
    if type(config) is not ResearchPacketSourceFamilyIndependenceScoreConfig:
        raise ValueError(
            "config must be a ResearchPacketSourceFamilyIndependenceScoreConfig",
        )
    normalized_sources = _normalize_sources(sources, packet_id=packet_id)
    metrics = _metrics(normalized_sources, config)
    score_status = _score_status(metrics, config)
    values: dict[str, object] = {
        "packet_id": packet_id,
        "config_version": config.config_version,
        "source_count": metrics.source_count,
        "distinct_source_family_count": metrics.distinct_source_family_count,
        "required_distinct_family_count": config.required_distinct_family_count,
        "shared_ownership_derivation_source_count": (
            metrics.shared_ownership_derivation_source_count
        ),
        "official_source_count": metrics.official_source_count,
        "duplicate_claim_count": metrics.duplicate_claim_count,
        "stale_source_count": metrics.stale_source_count,
        "stale_after_seconds": config.stale_after_seconds,
        "min_strong_score": config.min_strong_score,
        "min_watch_score": config.min_watch_score,
        "distinct_family_count_weight": config.distinct_family_count_weight,
        "ownership_derivation_weight": config.ownership_derivation_weight,
        "official_source_weight": config.official_source_weight,
        "duplicate_claim_weight": config.duplicate_claim_weight,
        "stale_source_weight": config.stale_source_weight,
        "contradiction_weight": config.contradiction_weight,
        "family_count_score": metrics.family_count_score,
        "shared_ownership_derivation_risk": (
            metrics.shared_ownership_derivation_risk
        ),
        "official_source_coverage": metrics.official_source_coverage,
        "duplicate_claim_ratio": metrics.duplicate_claim_ratio,
        "stale_source_ratio": metrics.stale_source_ratio,
        "contradiction_severity": metrics.contradiction_severity,
        "independence_score": metrics.independence_score,
        "score_status": score_status,
        "reason_codes": _reason_codes(metrics, score_status, config),
        "source_evidence_digest": _source_digest(normalized_sources),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchPacketSourceFamilyIndependenceScoreReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def _metrics(
    sources: tuple[ResearchPacketSourceFamilyIndependenceScoreSource, ...],
    config: ResearchPacketSourceFamilyIndependenceScoreConfig,
) -> _Metrics:
    source_count = _decimal_count(len(sources))
    distinct_source_family_count = _decimal_count(
        len({source.source_family for source in sources}),
    )
    shared_ownership_derivation_source_count = _decimal_count(
        _shared_ownership_derivation_source_count(sources),
    )
    official_source_count = _decimal_count(
        sum(1 for source in sources if source.is_official_source),
    )
    unique_claim_fingerprint_count = len(
        {source.claim_fingerprint for source in sources},
    )
    duplicate_claim_count = _decimal_count(max(len(sources) - unique_claim_fingerprint_count, 0))
    stale_source_count = _decimal_count(
        sum(1 for source in sources if source.source_age_seconds > config.stale_after_seconds),
    )
    contradiction_severity = max(
        (source.contradiction_severity for source in sources),
        default=_ZERO,
    )
    family_count_score = _capped_ratio(
        distinct_source_family_count,
        config.required_distinct_family_count,
    )
    shared_ownership_derivation_risk = _share(
        shared_ownership_derivation_source_count,
        source_count,
    )
    official_source_coverage = _share(official_source_count, source_count)
    duplicate_claim_ratio = _share(duplicate_claim_count, source_count)
    stale_source_ratio = _share(stale_source_count, source_count)
    if source_count == _ZERO:
        independence_score = _ZERO
    else:
        independence_score = _independence_score(
            family_count_score=family_count_score,
            shared_ownership_derivation_risk=shared_ownership_derivation_risk,
            official_source_coverage=official_source_coverage,
            duplicate_claim_ratio=duplicate_claim_ratio,
            stale_source_ratio=stale_source_ratio,
            contradiction_severity=contradiction_severity,
            config=config,
        )
    return _Metrics(
        source_count=source_count,
        distinct_source_family_count=distinct_source_family_count,
        shared_ownership_derivation_source_count=(
            shared_ownership_derivation_source_count
        ),
        official_source_count=official_source_count,
        duplicate_claim_count=duplicate_claim_count,
        stale_source_count=stale_source_count,
        family_count_score=family_count_score,
        shared_ownership_derivation_risk=shared_ownership_derivation_risk,
        official_source_coverage=official_source_coverage,
        duplicate_claim_ratio=duplicate_claim_ratio,
        stale_source_ratio=stale_source_ratio,
        contradiction_severity=contradiction_severity,
        independence_score=independence_score,
    )


def _shared_ownership_derivation_source_count(
    sources: tuple[ResearchPacketSourceFamilyIndependenceScoreSource, ...],
) -> int:
    owner_counts: dict[str, int] = {}
    derivation_counts: dict[str, int] = {}
    for source in sources:
        owner_counts[source.owner_family] = owner_counts.get(source.owner_family, 0) + 1
        if source.derivation_family is not None:
            derivation_counts[source.derivation_family] = (
                derivation_counts.get(source.derivation_family, 0) + 1
            )

    risky_source_ids: set[str] = set()
    for source in sources:
        has_shared_owner = owner_counts[source.owner_family] > 1
        has_shared_derivation = (
            source.derivation_family is not None
            and derivation_counts[source.derivation_family] > 1
        )
        if has_shared_owner or has_shared_derivation:
            risky_source_ids.add(source.source_id)
    return len(risky_source_ids)


def _independence_score(
    *,
    family_count_score: Decimal,
    shared_ownership_derivation_risk: Decimal,
    official_source_coverage: Decimal,
    duplicate_claim_ratio: Decimal,
    stale_source_ratio: Decimal,
    contradiction_severity: Decimal,
    config: ResearchPacketSourceFamilyIndependenceScoreConfig
    | ResearchPacketSourceFamilyIndependenceScoreReport,
) -> Decimal:
    ownership_derivation_quality = _ONE - shared_ownership_derivation_risk
    duplicate_claim_quality = _ONE - duplicate_claim_ratio
    stale_source_quality = _ONE - stale_source_ratio
    contradiction_quality = _ONE - contradiction_severity
    score = (
        (family_count_score * config.distinct_family_count_weight)
        + (ownership_derivation_quality * config.ownership_derivation_weight)
        + (official_source_coverage * config.official_source_weight)
        + (duplicate_claim_quality * config.duplicate_claim_weight)
        + (stale_source_quality * config.stale_source_weight)
        + (contradiction_quality * config.contradiction_weight)
    )
    return _clamp_ratio(score)


def _score_status(
    metrics: _Metrics,
    config: ResearchPacketSourceFamilyIndependenceScoreConfig
    | ResearchPacketSourceFamilyIndependenceScoreReport,
) -> str:
    if metrics.source_count == _ZERO:
        return "blocked"
    if metrics.independence_score >= config.min_strong_score:
        return "strong"
    if metrics.independence_score >= config.min_watch_score:
        return "watch"
    return "blocked"


def _reason_codes(
    metrics: _Metrics,
    score_status: str,
    config: ResearchPacketSourceFamilyIndependenceScoreConfig
    | ResearchPacketSourceFamilyIndependenceScoreReport,
) -> tuple[str, ...]:
    if metrics.source_count == _ZERO:
        return ("empty_sources", "independence_score_blocked")

    reason_codes: list[str] = []
    if metrics.distinct_source_family_count >= config.required_distinct_family_count:
        reason_codes.append("family_count_met")
    else:
        reason_codes.append("family_count_below_floor")

    if metrics.shared_ownership_derivation_risk > _ZERO:
        reason_codes.append("shared_ownership_or_derivation_risk")
    else:
        reason_codes.append("ownership_derivation_clear")

    if metrics.official_source_coverage > _ZERO:
        reason_codes.append("official_source_covered")
    else:
        reason_codes.append("official_source_missing")

    if metrics.duplicate_claim_ratio > _ZERO:
        reason_codes.append("duplicate_claims_present")
    else:
        reason_codes.append("duplicate_claims_clear")

    if metrics.stale_source_ratio > _ZERO:
        reason_codes.append("stale_sources_present")
    else:
        reason_codes.append("sources_current")

    if metrics.contradiction_severity > _ZERO:
        reason_codes.append("contradiction_severity_present")
    else:
        reason_codes.append("contradictions_clear")

    reason_codes.append(f"independence_score_{score_status}")
    return _normalize_reason_codes(tuple(reason_codes))


def _validate_report_consistency(
    report: ResearchPacketSourceFamilyIndependenceScoreReport,
) -> None:
    if report.distinct_source_family_count > report.source_count:
        raise ValueError("distinct_source_family_count must not exceed source_count")
    if report.shared_ownership_derivation_source_count > report.source_count:
        raise ValueError(
            "shared_ownership_derivation_source_count must not exceed source_count",
        )
    if report.official_source_count > report.source_count:
        raise ValueError("official_source_count must not exceed source_count")
    if report.duplicate_claim_count > report.source_count:
        raise ValueError("duplicate_claim_count must not exceed source_count")
    if report.stale_source_count > report.source_count:
        raise ValueError("stale_source_count must not exceed source_count")

    metrics = _Metrics(
        source_count=report.source_count,
        distinct_source_family_count=report.distinct_source_family_count,
        shared_ownership_derivation_source_count=(
            report.shared_ownership_derivation_source_count
        ),
        official_source_count=report.official_source_count,
        duplicate_claim_count=report.duplicate_claim_count,
        stale_source_count=report.stale_source_count,
        family_count_score=report.family_count_score,
        shared_ownership_derivation_risk=report.shared_ownership_derivation_risk,
        official_source_coverage=report.official_source_coverage,
        duplicate_claim_ratio=report.duplicate_claim_ratio,
        stale_source_ratio=report.stale_source_ratio,
        contradiction_severity=report.contradiction_severity,
        independence_score=report.independence_score,
    )
    expected_family_count_score = _capped_ratio(
        report.distinct_source_family_count,
        report.required_distinct_family_count,
    )
    if report.family_count_score != expected_family_count_score:
        raise ValueError("family_count_score must match distinct family coverage")
    if report.shared_ownership_derivation_risk != _share(
        report.shared_ownership_derivation_source_count,
        report.source_count,
    ):
        raise ValueError(
            "shared_ownership_derivation_risk must match shared source count",
        )
    if report.official_source_coverage != _share(
        report.official_source_count,
        report.source_count,
    ):
        raise ValueError("official_source_coverage must match official_source_count")
    if report.duplicate_claim_ratio != _share(
        report.duplicate_claim_count,
        report.source_count,
    ):
        raise ValueError("duplicate_claim_ratio must match duplicate_claim_count")
    if report.stale_source_ratio != _share(
        report.stale_source_count,
        report.source_count,
    ):
        raise ValueError("stale_source_ratio must match stale_source_count")
    if report.source_count == _ZERO:
        expected_score = _ZERO
    else:
        expected_score = _independence_score(
            family_count_score=report.family_count_score,
            shared_ownership_derivation_risk=report.shared_ownership_derivation_risk,
            official_source_coverage=report.official_source_coverage,
            duplicate_claim_ratio=report.duplicate_claim_ratio,
            stale_source_ratio=report.stale_source_ratio,
            contradiction_severity=report.contradiction_severity,
            config=report,
        )
    if report.independence_score != expected_score:
        raise ValueError("independence_score must match component scores")
    expected_status = _score_status(metrics, report)
    if report.score_status != expected_status:
        raise ValueError("score_status must match independence_score")
    expected_reasons = _reason_codes(metrics, expected_status, report)
    if report.reason_codes != expected_reasons:
        raise ValueError("reason_codes must match score dimensions")


def _normalize_sources(
    sources: Sequence[ResearchPacketSourceFamilyIndependenceScoreSource],
    *,
    packet_id: str,
) -> tuple[ResearchPacketSourceFamilyIndependenceScoreSource, ...]:
    if isinstance(sources, (str, bytes)) or not isinstance(sources, Sequence):
        raise ValueError("sources must be a sequence")
    normalized: list[ResearchPacketSourceFamilyIndependenceScoreSource] = []
    source_ids: set[str] = set()
    for source in sources:
        if type(source) is not ResearchPacketSourceFamilyIndependenceScoreSource:
            raise ValueError(
                "sources must contain "
                "ResearchPacketSourceFamilyIndependenceScoreSource",
            )
        if source.packet_id != packet_id:
            raise ValueError("packet_id must match all sources")
        if source.source_id in source_ids:
            raise ValueError("source_id must be unique")
        source_ids.add(source.source_id)
        normalized.append(source)
    return tuple(sorted(normalized, key=lambda source: (source.packet_id, source.source_id)))


def _validate_weight_sum(
    value: ResearchPacketSourceFamilyIndependenceScoreConfig
    | ResearchPacketSourceFamilyIndependenceScoreReport,
) -> None:
    weight_sum = _quantize(
        value.distinct_family_count_weight
        + value.ownership_derivation_weight
        + value.official_source_weight
        + value.duplicate_claim_weight
        + value.stale_source_weight
        + value.contradiction_weight,
    )
    if weight_sum != _ONE:
        raise ValueError("score weights must sum to one")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in _PHASE_FLAG_FIELDS:
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_bool(field_name: str, value: object) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")
    return value


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not _PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    _reject_unsafe_public_string(field_name, value)
    return value


def _normalize_optional_public_identifier(field_name: str, value: object) -> str | None:
    if value is None:
        return None
    return _require_public_identifier(field_name, value)


def _reject_unsafe_public_string(field_name: str, value: str) -> None:
    lowered = value.lower()
    if "://" in lowered or "?" in lowered or "@" in lowered:
        raise ValueError(f"{field_name} has unsafe public value")
    if any(term in lowered for term in _UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"{field_name} has unsafe public value")


def _require_score_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in _SCORE_STATUSES:
        raise ValueError(f"{field_name} must be a known score status")
    return value


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str or not _DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    return value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_positive_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_count_decimal(field_name, value)
    if normalized <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO or normalized > _ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _decimal_count(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be nonnegative")
    return Decimal(value).quantize(_QUANT)


def _share(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == _ZERO:
        return _ZERO
    return _quantize(numerator / denominator)


def _capped_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= _ZERO:
        raise ValueError("denominator must be positive")
    return _clamp_ratio(numerator / denominator)


def _clamp_ratio(value: Decimal) -> Decimal:
    normalized = _quantize(value)
    if normalized < _ZERO:
        return _ZERO
    if normalized > _ONE:
        return _ONE
    return normalized


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(_QUANT, rounding=ROUND_HALF_UP)


def _normalize_reason_codes(reason_codes: Sequence[str]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)) or not isinstance(reason_codes, Sequence):
        raise ValueError("reason_codes must be a sequence")
    normalized: list[str] = []
    for reason_code in reason_codes:
        _require_public_identifier("reason_code", reason_code)
        if reason_code not in _REASON_CODE_SEQUENCE:
            raise ValueError("reason_code must be supported")
        if reason_code not in normalized:
            normalized.append(reason_code)
    return tuple(
        reason_code
        for reason_code in _REASON_CODE_SEQUENCE
        if reason_code in normalized
    )


def _source_digest(
    sources: tuple[ResearchPacketSourceFamilyIndependenceScoreSource, ...],
) -> str:
    return _digest_from_value(tuple(asdict(source) for source in sources))


def _report_values_without_digest(
    report: ResearchPacketSourceFamilyIndependenceScoreReport,
) -> dict[str, object]:
    values = asdict(report)
    values.pop("derived_validation_digest", None)
    return values


def _report_digest_from_values(values: Mapping[str, object]) -> str:
    return _digest_from_value(values)


def _digest_from_value(value: object) -> str:
    payload = _json_ready(value)
    _reject_unsafe_public_payload(
        "digest payload",
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
        return str(value)
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
    if value is None or type(value) is bool or type(value) is Decimal:
        return
    raise ValueError(f"{current_path} is not a supported public payload value")


def _reject_unsafe_public_key(key: str, path: str) -> None:
    lowered = key.lower()
    if any(term in lowered for term in _UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"{path}.{key} has unsafe public field")


__all__ = (
    "DEFAULT_RESEARCH_PACKET_SOURCE_FAMILY_INDEPENDENCE_SCORE_V2_CONFIG_VERSION",
    "ResearchPacketSourceFamilyIndependenceScoreConfig",
    "ResearchPacketSourceFamilyIndependenceScoreReport",
    "ResearchPacketSourceFamilyIndependenceScoreSource",
    "build_research_packet_source_family_independence_score_v2_report",
)
