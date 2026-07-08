"""Pure report-only source authority weighting for research packets.

The module accepts caller-supplied aggregate source observations and returns a
deterministic, redacted report. It performs no I/O and exposes no live surfaces.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
import hashlib
import json
from typing import Any


__all__ = (
    "ResearchSourceAuthorityClassMixRow",
    "ResearchSourceAuthorityObservation",
    "ResearchSourceAuthorityReasonCodeCount",
    "ResearchSourceAuthorityWeightingConfig",
    "ResearchSourceAuthorityWeightingReport",
    "ResearchSourceAuthorityWeightingRow",
    "build_research_source_authority_weighting_report",
    "research_source_authority_weighting_report_payload",
)


DEFAULT_CONFIG_VERSION = "research-source-authority-weighting-report-v0"
AUTHORITY_CLASSES = ("official", "expert", "data", "media", "social")
STATUSES = ("pass", "watch", "block")
ZERO = Decimal("0")
ONE = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
SHA256_HEX_LENGTH = 64
UNSAFE_PUBLIC_FRAGMENTS = (
    "http://",
    "https://",
    "www.",
    "raw_url",
    "source_text",
    "market_id",
    "question",
    "wallet",
    "order",
    "live",
    "trade",
    "network",
    "database",
    "signing",
    "mutation",
)


class _Missing:
    pass


_MISSING = _Missing()


@dataclass(frozen=True)
class ResearchSourceAuthorityWeightingConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    fresh_age_seconds: Decimal = Decimal("3600.000000")
    stale_age_seconds: Decimal = Decimal("86400.000000")
    official_authority_weight: Decimal = Decimal("1.000000")
    expert_authority_weight: Decimal = Decimal("0.900000")
    data_authority_weight: Decimal = Decimal("0.700000")
    media_authority_weight: Decimal = Decimal("0.500000")
    social_authority_weight: Decimal = Decimal("0.250000")
    authority_mix_score_weight: Decimal = Decimal("0.450000")
    freshness_score_weight: Decimal = Decimal("0.250000")
    coverage_score_weight: Decimal = Decimal("0.200000")
    contradiction_score_weight: Decimal = Decimal("0.100000")
    pass_authority_weighting_score: Decimal = Decimal("0.800000")
    block_authority_weighting_score: Decimal = Decimal("0.200000")
    high_contradiction_pressure: Decimal = Decimal("0.700000")
    low_recheck_urgency_threshold: Decimal = Decimal("0.250000")
    high_recheck_urgency_threshold: Decimal = Decimal("0.750000")
    required_authority_classes: tuple[str, ...] = ("official", "expert")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceAuthorityWeightingConfig:
            raise TypeError(
                "ResearchSourceAuthorityWeightingConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceAuthorityWeightingConfig:
            raise ValueError("config must be exactly ResearchSourceAuthorityWeightingConfig")
        _require_public_identifier("config_version", self.config_version)
        if self.config_version != DEFAULT_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        object.__setattr__(
            self,
            "fresh_age_seconds",
            _require_positive_decimal("fresh_age_seconds", self.fresh_age_seconds),
        )
        object.__setattr__(
            self,
            "stale_age_seconds",
            _require_positive_decimal("stale_age_seconds", self.stale_age_seconds),
        )
        if self.stale_age_seconds <= self.fresh_age_seconds:
            raise ValueError("stale_age_seconds must exceed fresh_age_seconds")
        for field_name in (
            "official_authority_weight",
            "expert_authority_weight",
            "data_authority_weight",
            "media_authority_weight",
            "social_authority_weight",
            "authority_mix_score_weight",
            "freshness_score_weight",
            "coverage_score_weight",
            "contradiction_score_weight",
            "pass_authority_weighting_score",
            "block_authority_weighting_score",
            "high_contradiction_pressure",
            "low_recheck_urgency_threshold",
            "high_recheck_urgency_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        component_sum = _quantize(
            self.authority_mix_score_weight
            + self.freshness_score_weight
            + self.coverage_score_weight
            + self.contradiction_score_weight,
        )
        if component_sum != ONE:
            raise ValueError("score component weights must sum to 1")
        if self.pass_authority_weighting_score <= self.block_authority_weighting_score:
            raise ValueError(
                "pass_authority_weighting_score must exceed "
                "block_authority_weighting_score",
            )
        if self.high_recheck_urgency_threshold <= self.low_recheck_urgency_threshold:
            raise ValueError(
                "high_recheck_urgency_threshold must exceed "
                "low_recheck_urgency_threshold",
            )
        object.__setattr__(
            self,
            "required_authority_classes",
            _normalize_authority_classes(
                "required_authority_classes",
                self.required_authority_classes,
                allow_empty=False,
                require_unique=True,
            ),
        )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchSourceAuthorityObservation:
    packet_id: str
    authority_class: str
    source_count: Decimal
    latest_observed_at: datetime
    contradiction_count: Decimal = Decimal("0.000000")
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceAuthorityObservation:
            raise TypeError("ResearchSourceAuthorityObservation does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceAuthorityObservation:
            raise ValueError("observation must be exactly ResearchSourceAuthorityObservation")
        _require_public_identifier("packet_id", self.packet_id)
        _require_enum("authority_class", self.authority_class, AUTHORITY_CLASSES)
        object.__setattr__(
            self,
            "source_count",
            _require_positive_count_decimal("source_count", self.source_count),
        )
        object.__setattr__(
            self,
            "latest_observed_at",
            _as_utc("latest_observed_at", self.latest_observed_at),
        )
        object.__setattr__(
            self,
            "contradiction_count",
            _require_nonnegative_count_decimal(
                "contradiction_count",
                self.contradiction_count,
            ),
        )
        if self.contradiction_count > self.source_count:
            raise ValueError("contradiction_count must not exceed source_count")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=True),
        )
        _require_hard_flags("observation", self)
        _reject_unsafe_public_payload("observation", self)


@dataclass(frozen=True)
class ResearchSourceAuthorityClassMixRow:
    authority_class: str
    source_count: Decimal
    source_share: Decimal
    authority_weight: Decimal
    weighted_authority_contribution: Decimal
    source_age_seconds: Decimal
    freshness_score: Decimal
    contradiction_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceAuthorityClassMixRow:
            raise TypeError("ResearchSourceAuthorityClassMixRow does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceAuthorityClassMixRow:
            raise ValueError("class mix row must be exactly ResearchSourceAuthorityClassMixRow")
        _require_enum("authority_class", self.authority_class, AUTHORITY_CLASSES)
        for field_name in ("source_count", "contradiction_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "source_age_seconds",
            _require_nonnegative_decimal("source_age_seconds", self.source_age_seconds),
        )
        for field_name in (
            "source_share",
            "authority_weight",
            "weighted_authority_contribution",
            "freshness_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.contradiction_count > self.source_count:
            raise ValueError("contradiction_count must not exceed source_count")
        _require_hard_flags("class mix row", self)
        _reject_unsafe_public_payload("class mix row", self)


@dataclass(frozen=True)
class ResearchSourceAuthorityWeightingRow:
    packet_id: str
    source_count: Decimal
    authority_class_count: Decimal
    required_authority_class_count: Decimal
    covered_required_authority_class_count: Decimal
    coverage_gap_count: Decimal
    authority_weight_score: Decimal
    freshness_score: Decimal
    contradiction_pressure: Decimal
    coverage_gap_score: Decimal
    coverage_score: Decimal
    authority_weighting_score: Decimal
    recheck_urgency_score: Decimal
    status: str
    missing_required_authority_classes: tuple[str, ...]
    authority_class_mix: tuple[ResearchSourceAuthorityClassMixRow, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceAuthorityWeightingRow:
            raise TypeError("ResearchSourceAuthorityWeightingRow does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceAuthorityWeightingRow:
            raise ValueError("row must be exactly ResearchSourceAuthorityWeightingRow")
        _require_public_identifier("packet_id", self.packet_id)
        for field_name in (
            "source_count",
            "authority_class_count",
            "required_authority_class_count",
            "covered_required_authority_class_count",
            "coverage_gap_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "authority_weight_score",
            "freshness_score",
            "contradiction_pressure",
            "coverage_gap_score",
            "coverage_score",
            "authority_weighting_score",
            "recheck_urgency_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "missing_required_authority_classes",
            _normalize_authority_classes(
                "missing_required_authority_classes",
                self.missing_required_authority_classes,
                allow_empty=True,
                require_unique=True,
            ),
        )
        object.__setattr__(
            self,
            "authority_class_mix",
            _normalize_class_mix(self.authority_class_mix),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _validate_row_consistency(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchSourceAuthorityReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceAuthorityReasonCodeCount:
            raise TypeError(
                "ResearchSourceAuthorityReasonCodeCount does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceAuthorityReasonCodeCount:
            raise ValueError(
                "reason code count must be exactly "
                "ResearchSourceAuthorityReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_positive_count_decimal("count", self.count),
        )
        _require_hard_flags("reason code count", self)
        _reject_unsafe_public_payload("reason code count", self)


@dataclass(frozen=True)
class ResearchSourceAuthorityWeightingReport:
    generated_at: datetime
    config_version: str
    status: str
    packet_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    observation_count: Decimal
    source_count: Decimal
    average_authority_weighting_score: Decimal | None
    max_recheck_urgency_score: Decimal | None
    rows: tuple[ResearchSourceAuthorityWeightingRow, ...]
    reason_code_counts: tuple[ResearchSourceAuthorityReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceAuthorityWeightingReport:
            raise TypeError(
                "ResearchSourceAuthorityWeightingReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceAuthorityWeightingReport:
            raise ValueError("report must be exactly ResearchSourceAuthorityWeightingReport")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if self.config_version != DEFAULT_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        _require_status("status", self.status)
        for field_name in (
            "packet_count",
            "pass_count",
            "watch_count",
            "block_count",
            "observation_count",
            "source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_authority_weighting_score",
            "max_recheck_urgency_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_optional_ratio_decimal(field_name, getattr(self, field_name)),
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
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
        _validate_report_consistency(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _report_digest_from_values(_report_values_without_digest(self))
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest does not match report payload")

    @property
    def payload(self) -> dict[str, object]:
        payload = _json_ready(asdict(self))
        _reject_unsafe_public_payload("report payload", payload, allow_json_containers=True)
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        return payload


def build_research_source_authority_weighting_report(
    observations: Iterable[object],
    *,
    generated_at: datetime,
    config: ResearchSourceAuthorityWeightingConfig | None = None,
) -> ResearchSourceAuthorityWeightingReport:
    """Build a deterministic aggregate authority weighting report."""

    if config is None:
        config = ResearchSourceAuthorityWeightingConfig()
    if type(config) is not ResearchSourceAuthorityWeightingConfig:
        raise ValueError("config must be a ResearchSourceAuthorityWeightingConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_observations = _normalize_observations(observations)
    for item in normalized_observations:
        if item.latest_observed_at > generated_at_utc:
            raise ValueError("latest_observed_at must not be after generated_at")
    rows = _build_rows(normalized_observations, generated_at_utc, config)
    reason_codes = _report_reason_codes(rows)
    values: dict[str, object] = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "status": _report_status(rows),
        "packet_count": _decimal_count(len(rows)),
        "pass_count": _decimal_count(_status_count(rows, "pass")),
        "watch_count": _decimal_count(_status_count(rows, "watch")),
        "block_count": _decimal_count(_status_count(rows, "block")),
        "observation_count": _decimal_count(len(normalized_observations)),
        "source_count": _sum_decimal(tuple(item.source_count for item in normalized_observations)),
        "average_authority_weighting_score": _average_optional(
            tuple(row.authority_weighting_score for row in rows),
        ),
        "max_recheck_urgency_score": (
            max((row.recheck_urgency_score for row in rows), default=None)
        ),
        "rows": rows,
        "reason_code_counts": _reason_code_counts(rows, reason_codes),
        "reason_codes": reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchSourceAuthorityWeightingReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def research_source_authority_weighting_report_payload(
    report: ResearchSourceAuthorityWeightingReport,
) -> dict[str, Any]:
    if type(report) is not ResearchSourceAuthorityWeightingReport:
        raise ValueError("report must be a ResearchSourceAuthorityWeightingReport")
    _require_hard_flags("report", report)
    return report.payload


def _build_rows(
    observations: tuple[ResearchSourceAuthorityObservation, ...],
    generated_at: datetime,
    config: ResearchSourceAuthorityWeightingConfig,
) -> tuple[ResearchSourceAuthorityWeightingRow, ...]:
    grouped: dict[str, list[ResearchSourceAuthorityObservation]] = {}
    for item in observations:
        grouped.setdefault(item.packet_id, []).append(item)
    return tuple(
        _row_for_packet(
            packet_id=packet_id,
            observations=tuple(grouped[packet_id]),
            generated_at=generated_at,
            config=config,
        )
        for packet_id in sorted(grouped)
    )


def _row_for_packet(
    *,
    packet_id: str,
    observations: tuple[ResearchSourceAuthorityObservation, ...],
    generated_at: datetime,
    config: ResearchSourceAuthorityWeightingConfig,
) -> ResearchSourceAuthorityWeightingRow:
    class_mix = _authority_class_mix(observations, generated_at, config)
    source_count = _sum_decimal(tuple(item.source_count for item in class_mix))
    observed_classes = tuple(item.authority_class for item in class_mix)
    missing_required = tuple(
        authority_class
        for authority_class in config.required_authority_classes
        if authority_class not in observed_classes
    )
    covered_required_count = len(config.required_authority_classes) - len(missing_required)
    coverage_gap_count = _decimal_count(len(missing_required))
    required_count = _decimal_count(len(config.required_authority_classes))
    coverage_gap_score = _clamp_ratio(coverage_gap_count / required_count)
    coverage_score = _clamp_ratio(ONE - coverage_gap_score)
    authority_weight_score = _clamp_ratio(
        _sum_decimal(tuple(item.weighted_authority_contribution for item in class_mix)),
    )
    freshness_score = _weighted_average(
        tuple((item.freshness_score, item.source_count) for item in class_mix),
    )
    contradiction_count = _sum_decimal(
        tuple(item.contradiction_count for item in class_mix),
    )
    contradiction_pressure = _clamp_ratio(contradiction_count / source_count)
    authority_weighting_score = _authority_weighting_score(
        authority_weight_score=authority_weight_score,
        freshness_score=freshness_score,
        coverage_score=coverage_score,
        contradiction_pressure=contradiction_pressure,
        config=config,
    )
    recheck_urgency_score = _recheck_urgency_score(
        authority_weighting_score=authority_weighting_score,
        freshness_score=freshness_score,
        contradiction_pressure=contradiction_pressure,
        coverage_gap_score=coverage_gap_score,
    )
    status = _row_status(
        authority_weighting_score=authority_weighting_score,
        contradiction_pressure=contradiction_pressure,
        coverage_gap_count=coverage_gap_count,
        config=config,
    )
    reason_codes = _row_reason_codes(
        status=status,
        authority_weight_score=authority_weight_score,
        freshness_score=freshness_score,
        contradiction_pressure=contradiction_pressure,
        coverage_gap_count=coverage_gap_count,
        recheck_urgency_score=recheck_urgency_score,
        config=config,
        input_reason_codes=tuple(
            reason_code
            for item in sorted(observations, key=lambda value: value.authority_class)
            for reason_code in item.reason_codes
        ),
    )
    return ResearchSourceAuthorityWeightingRow(
        packet_id=packet_id,
        source_count=source_count,
        authority_class_count=_decimal_count(len(class_mix)),
        required_authority_class_count=required_count,
        covered_required_authority_class_count=_decimal_count(covered_required_count),
        coverage_gap_count=coverage_gap_count,
        authority_weight_score=authority_weight_score,
        freshness_score=freshness_score,
        contradiction_pressure=contradiction_pressure,
        coverage_gap_score=coverage_gap_score,
        coverage_score=coverage_score,
        authority_weighting_score=authority_weighting_score,
        recheck_urgency_score=recheck_urgency_score,
        status=status,
        missing_required_authority_classes=missing_required,
        authority_class_mix=class_mix,
        reason_codes=reason_codes,
    )


def _authority_class_mix(
    observations: tuple[ResearchSourceAuthorityObservation, ...],
    generated_at: datetime,
    config: ResearchSourceAuthorityWeightingConfig,
) -> tuple[ResearchSourceAuthorityClassMixRow, ...]:
    grouped: dict[str, list[ResearchSourceAuthorityObservation]] = {}
    for item in observations:
        grouped.setdefault(item.authority_class, []).append(item)
    total_source_count = _sum_decimal(tuple(item.source_count for item in observations))
    rows: list[ResearchSourceAuthorityClassMixRow] = []
    for authority_class, items in sorted(grouped.items()):
        source_count = _sum_decimal(tuple(item.source_count for item in items))
        latest_observed_at = max(item.latest_observed_at for item in items)
        source_age_seconds = _age_seconds(generated_at, latest_observed_at)
        source_share = _clamp_ratio(source_count / total_source_count)
        authority_weight = _authority_weight(config, authority_class)
        rows.append(
            ResearchSourceAuthorityClassMixRow(
                authority_class=authority_class,
                source_count=source_count,
                source_share=source_share,
                authority_weight=authority_weight,
                weighted_authority_contribution=_clamp_ratio(
                    source_share * authority_weight,
                ),
                source_age_seconds=source_age_seconds,
                freshness_score=_freshness_score(
                    source_age_seconds,
                    fresh_age_seconds=config.fresh_age_seconds,
                    stale_age_seconds=config.stale_age_seconds,
                ),
                contradiction_count=_sum_decimal(
                    tuple(item.contradiction_count for item in items),
                ),
            ),
        )
    return tuple(
        sorted(
            rows,
            key=lambda row: (-row.authority_weight, row.authority_class),
        ),
    )


def _authority_weight(
    config: ResearchSourceAuthorityWeightingConfig,
    authority_class: str,
) -> Decimal:
    return {
        "official": config.official_authority_weight,
        "expert": config.expert_authority_weight,
        "data": config.data_authority_weight,
        "media": config.media_authority_weight,
        "social": config.social_authority_weight,
    }[authority_class]


def _authority_weighting_score(
    *,
    authority_weight_score: Decimal,
    freshness_score: Decimal,
    coverage_score: Decimal,
    contradiction_pressure: Decimal,
    config: ResearchSourceAuthorityWeightingConfig,
) -> Decimal:
    return _clamp_ratio(
        (authority_weight_score * config.authority_mix_score_weight)
        + (freshness_score * config.freshness_score_weight)
        + (coverage_score * config.coverage_score_weight)
        + ((ONE - contradiction_pressure) * config.contradiction_score_weight),
    )


def _recheck_urgency_score(
    *,
    authority_weighting_score: Decimal,
    freshness_score: Decimal,
    contradiction_pressure: Decimal,
    coverage_gap_score: Decimal,
) -> Decimal:
    return _clamp_ratio(
        max(
            ONE - authority_weighting_score,
            ONE - freshness_score,
            contradiction_pressure,
            coverage_gap_score,
        ),
    )


def _row_status(
    *,
    authority_weighting_score: Decimal,
    contradiction_pressure: Decimal,
    coverage_gap_count: Decimal,
    config: ResearchSourceAuthorityWeightingConfig,
) -> str:
    if contradiction_pressure >= config.high_contradiction_pressure:
        return "block"
    if authority_weighting_score < config.block_authority_weighting_score:
        return "block"
    if (
        authority_weighting_score >= config.pass_authority_weighting_score
        and coverage_gap_count == ZERO
    ):
        return "pass"
    return "watch"


def _row_reason_codes(
    *,
    status: str,
    authority_weight_score: Decimal,
    freshness_score: Decimal,
    contradiction_pressure: Decimal,
    coverage_gap_count: Decimal,
    recheck_urgency_score: Decimal,
    config: ResearchSourceAuthorityWeightingConfig,
    input_reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    reason_codes: set[str] = {f"research_source_authority_weighting_{status}"}
    reason_codes.add(
        "strong_authority_class_mix"
        if authority_weight_score >= config.pass_authority_weighting_score
        else "weak_authority_class_mix",
    )
    reason_codes.add(
        "fresh_authority_sources"
        if freshness_score > ZERO
        else "stale_authority_sources",
    )
    reason_codes.add(
        "contradiction_pressure_high"
        if contradiction_pressure >= config.high_contradiction_pressure
        else "contradiction_pressure_low",
    )
    reason_codes.add(
        "coverage_complete" if coverage_gap_count == ZERO else "coverage_gaps_present",
    )
    if recheck_urgency_score >= config.high_recheck_urgency_threshold:
        reason_codes.add("recheck_urgency_high")
    elif recheck_urgency_score <= config.low_recheck_urgency_threshold:
        reason_codes.add("recheck_urgency_low")
    else:
        reason_codes.add("recheck_urgency_watch")
    for reason_code in input_reason_codes:
        reason_codes.add(f"input_{reason_code}")
    return tuple(sorted(reason_codes))


def _report_reason_codes(
    rows: tuple[ResearchSourceAuthorityWeightingRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_research_authority_observations",)
    if all(row.status == "pass" for row in rows):
        return ("research_source_authority_weighting_pass",)
    return tuple(sorted({reason_code for row in rows for reason_code in row.reason_codes}))


def _report_status(rows: tuple[ResearchSourceAuthorityWeightingRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if all(row.status == "pass" for row in rows):
        return "pass"
    return "watch"


def _reason_code_counts(
    rows: tuple[ResearchSourceAuthorityWeightingRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchSourceAuthorityReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchSourceAuthorityReasonCodeCount(
                reason_code=reason_codes[0],
                count=ONE.quantize(RATIO_QUANTUM),
            ),
        )
    counts: Counter[str] = Counter()
    for row in rows:
        counts.update(row.reason_codes)
    return tuple(
        ResearchSourceAuthorityReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(count),
        )
        for reason_code, count in sorted(counts.items(), key=lambda item: item[0])
    )


def _normalize_observations(
    observations: Iterable[object],
) -> tuple[ResearchSourceAuthorityObservation, ...]:
    if isinstance(observations, (str, bytes)):
        raise ValueError("observations must be an iterable")
    try:
        values = tuple(observations)
    except TypeError as exc:
        raise ValueError("observations must be an iterable") from exc
    return tuple(_coerce_observation(value) for value in values)


def _coerce_observation(value: object) -> ResearchSourceAuthorityObservation:
    if type(value) is ResearchSourceAuthorityObservation:
        _require_hard_flags("observation", value)
        return value
    _require_hard_flags("observation", value)
    return ResearchSourceAuthorityObservation(
        packet_id=_field_value(value, "packet_id"),
        authority_class=_field_value(value, "authority_class"),
        source_count=_field_value(value, "source_count"),
        latest_observed_at=_field_value(value, "latest_observed_at"),
        contradiction_count=_field_value(value, "contradiction_count", default=ZERO),
        reason_codes=_field_value(value, "reason_codes", default=()),
        paper_only=_field_value(value, "paper_only"),
        report_only=_field_value(value, "report_only"),
        readonly=_field_value(value, "readonly"),
    )


def _normalize_rows(
    rows: tuple[ResearchSourceAuthorityWeightingRow, ...],
) -> tuple[ResearchSourceAuthorityWeightingRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchSourceAuthorityWeightingRow:
            raise ValueError("rows must contain ResearchSourceAuthorityWeightingRow values")
        _require_hard_flags("row", row)
    sorted_rows = tuple(sorted(rows, key=lambda row: row.packet_id))
    if rows != sorted_rows:
        raise ValueError("rows must be sorted by packet_id")
    return rows


def _normalize_class_mix(
    rows: tuple[ResearchSourceAuthorityClassMixRow, ...],
) -> tuple[ResearchSourceAuthorityClassMixRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("authority_class_mix must be a tuple")
    for row in rows:
        if type(row) is not ResearchSourceAuthorityClassMixRow:
            raise ValueError(
                "authority_class_mix must contain ResearchSourceAuthorityClassMixRow values",
            )
        _require_hard_flags("class mix row", row)
    sorted_rows = tuple(sorted(rows, key=lambda row: (-row.authority_weight, row.authority_class)))
    if rows != sorted_rows:
        raise ValueError("authority_class_mix must be sorted by authority weight")
    return rows


def _normalize_reason_code_counts(
    counts: tuple[ResearchSourceAuthorityReasonCodeCount, ...],
) -> tuple[ResearchSourceAuthorityReasonCodeCount, ...]:
    if type(counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for count in counts:
        if type(count) is not ResearchSourceAuthorityReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchSourceAuthorityReasonCodeCount values",
            )
        _require_hard_flags("reason code count", count)
    sorted_counts = tuple(sorted(counts, key=lambda count: count.reason_code))
    if counts != sorted_counts:
        raise ValueError("reason_code_counts must be sorted by reason_code")
    return counts


def _normalize_authority_classes(
    field_name: str,
    values: object,
    *,
    allow_empty: bool,
    require_unique: bool,
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized: list[str] = []
    for value in values:
        _require_enum(field_name, value, AUTHORITY_CLASSES)
        normalized.append(value)
    if not allow_empty and not normalized:
        raise ValueError(f"{field_name} must be nonempty")
    if require_unique and len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} must contain unique authority classes")
    return tuple(normalized)


def _validate_row_consistency(row: ResearchSourceAuthorityWeightingRow) -> None:
    if row.source_count <= ZERO:
        raise ValueError("source_count must be positive")
    if row.authority_class_count != _decimal_count(len(row.authority_class_mix)):
        raise ValueError("authority_class_count must match authority_class_mix")
    if row.source_count != _sum_decimal(
        tuple(item.source_count for item in row.authority_class_mix),
    ):
        raise ValueError("source_count must match authority_class_mix")
    if row.required_authority_class_count != (
        row.covered_required_authority_class_count + row.coverage_gap_count
    ):
        raise ValueError("required authority class counts must reconcile")
    if row.coverage_gap_count != _decimal_count(len(row.missing_required_authority_classes)):
        raise ValueError("coverage_gap_count must match missing_required_authority_classes")
    if row.status == "pass" and "research_source_authority_weighting_pass" not in row.reason_codes:
        raise ValueError("status must match reason_codes")
    if row.status == "watch" and "research_source_authority_weighting_watch" not in row.reason_codes:
        raise ValueError("status must match reason_codes")
    if row.status == "block" and "research_source_authority_weighting_block" not in row.reason_codes:
        raise ValueError("status must match reason_codes")


def _validate_report_consistency(report: ResearchSourceAuthorityWeightingReport) -> None:
    if report.packet_count != _decimal_count(len(report.rows)):
        raise ValueError("packet_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, "block")):
        raise ValueError("block_count must match rows")
    if report.source_count != _sum_decimal(tuple(row.source_count for row in report.rows)):
        raise ValueError("source_count must match rows")
    if report.average_authority_weighting_score != _average_optional(
        tuple(row.authority_weighting_score for row in report.rows),
    ):
        raise ValueError("average_authority_weighting_score must match rows")
    if report.max_recheck_urgency_score != max(
        (row.recheck_urgency_score for row in report.rows),
        default=None,
    ):
        raise ValueError("max_recheck_urgency_score must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")


def _field_value(value: object, field_name: str, *, default: object = _MISSING) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            if field.name == field_name:
                return getattr(value, field_name)
    if hasattr(value, field_name):
        return getattr(value, field_name)
    if default is not _MISSING:
        return default
    raise ValueError(f"{field_name} is required")


def _freshness_score(
    age_seconds: Decimal,
    *,
    fresh_age_seconds: Decimal,
    stale_age_seconds: Decimal,
) -> Decimal:
    if age_seconds <= fresh_age_seconds:
        return ONE.quantize(RATIO_QUANTUM)
    if age_seconds >= stale_age_seconds:
        return ZERO.quantize(RATIO_QUANTUM)
    return _clamp_ratio(ONE - (age_seconds / stale_age_seconds))


def _weighted_average(values: tuple[tuple[Decimal, Decimal], ...]) -> Decimal:
    if not values:
        raise ValueError("values must be nonempty")
    total_weight = _sum_decimal(tuple(weight for _, weight in values))
    if total_weight <= ZERO:
        raise ValueError("total weight must be positive")
    return _quantize(
        _sum_decimal(tuple(value * weight for value, weight in values)) / total_weight,
    )


def _average_optional(values: tuple[Decimal, ...]) -> Decimal | None:
    if not values:
        return None
    return _quantize(_sum_decimal(values) / Decimal(len(values)))


def _sum_decimal(values: tuple[Decimal, ...]) -> Decimal:
    return _quantize(sum(values, ZERO))


def _age_seconds(generated_at: datetime, observed_at: datetime) -> Decimal:
    delta = generated_at - observed_at
    return _quantize(
        Decimal(delta.days * 86_400)
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / Decimal("1000000")),
    )


def _status_count(rows: tuple[ResearchSourceAuthorityWeightingRow, ...], status: str) -> int:
    return sum(1 for row in rows if row.status == status)


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count source must be an int")
    if value < 0:
        raise ValueError("count source must be nonnegative")
    return Decimal(value).quantize(RATIO_QUANTUM)


def _clamp_ratio(value: Decimal) -> Decimal:
    return _quantize(max(ZERO, min(ONE, value)))


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(RATIO_QUANTUM)


def _as_utc(field_name: str, value: datetime) -> datetime:
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


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _quantize(normalized)


def _require_optional_ratio_decimal(field_name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _require_ratio_decimal(field_name, value)


def _require_positive_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_positive_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return normalized


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return normalized


def _require_public_identifier(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a nonempty canonical string")
    if _contains_unsafe_public_fragment(value):
        raise ValueError(f"{field_name} contains unsafe public value")
    if not all(character.islower() or character.isdigit() or character in "-_" for character in value):
        raise ValueError(f"{field_name} must be a public identifier")


def _require_reason_code(field_name: str, value: object) -> None:
    if type(value) is not str or not value:
        raise ValueError(f"{field_name} must contain reason code strings")
    if not all(character.islower() or character.isdigit() or character == "_" for character in value):
        raise ValueError(f"{field_name} must contain canonical reason codes")
    if _contains_unsafe_public_fragment(value):
        raise ValueError(f"{field_name} contains unsafe public value")


def _require_enum(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed}")


def _require_status(field_name: str, value: object) -> None:
    _require_enum(field_name, value, STATUSES)


def _normalize_reason_codes(
    field_name: str,
    values: object,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized: list[str] = []
    for value in values:
        _require_reason_code(field_name, value)
        normalized.append(value)
    if not allow_empty and not normalized:
        raise ValueError(f"{field_name} must be nonempty")
    return tuple(sorted(set(normalized)))


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if not hasattr(value, field_name):
            raise ValueError(f"{label} must expose {field_name}")
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True")


def _require_sha256_digest(field_name: str, value: object) -> None:
    if type(value) is not str or len(value) != SHA256_HEX_LENGTH:
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    if not all(character in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _report_values_without_digest(
    report: ResearchSourceAuthorityWeightingReport,
) -> dict[str, object]:
    return {
        "generated_at": report.generated_at,
        "config_version": report.config_version,
        "status": report.status,
        "packet_count": report.packet_count,
        "pass_count": report.pass_count,
        "watch_count": report.watch_count,
        "block_count": report.block_count,
        "observation_count": report.observation_count,
        "source_count": report.source_count,
        "average_authority_weighting_score": report.average_authority_weighting_score,
        "max_recheck_urgency_score": report.max_recheck_urgency_score,
        "rows": report.rows,
        "reason_code_counts": report.reason_code_counts,
        "reason_codes": report.reason_codes,
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }


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


def _json_ready(value: object) -> object:
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("Decimal values must be exact Decimal")
        return str(_quantize(value))
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("datetime values must be exact datetime")
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _json_ready(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if value is None or type(value) is bool or type(value) is str:
        return value
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    *,
    allow_json_containers: bool = False,
    path: str = "",
) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(
            label,
            asdict(value),
            allow_json_containers=True,
            path=path,
        )
        return
    if type(value) is str:
        if _contains_unsafe_public_fragment(value):
            raise ValueError(f"{path or label} contains unsafe public value")
        return
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError(f"{path or label} must be exactly Decimal")
        if not value.is_finite():
            raise ValueError(f"{path or label} must be finite")
        return
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError(f"{path or label} must be exactly datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(f"{path or label} must be timezone-aware")
        return
    if value is None or type(value) is bool:
        return
    if type(value) is int or isinstance(value, float):
        raise ValueError(f"{path or label} must use Decimal-derived string values")
    if isinstance(value, dict):
        if not allow_json_containers:
            raise ValueError(f"{label} must not expose dict values")
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            if _contains_unsafe_public_fragment(key):
                raise ValueError(f"unsafe public field in {label}: {key}")
            item_path = key if not path else f"{path}.{key}"
            if key in {"paper_only", "report_only", "readonly"} and item is not True:
                raise ValueError(f"{item_path} must be True")
            _reject_unsafe_public_payload(
                label,
                item,
                allow_json_containers=True,
                path=item_path,
            )
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            item_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_unsafe_public_payload(
                label,
                item,
                allow_json_containers=True,
                path=item_path,
            )
        return
    raise ValueError(f"{path or label} is not JSON serializable")


def _contains_unsafe_public_fragment(value: str) -> bool:
    lowered = value.lower()
    return any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS)
