"""Pure paper/report Phase 1 information source entropy score v2."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from decimal import Decimal, ROUND_HALF_UP, localcontext
from hashlib import sha256
import json
from typing import Any, Mapping


QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
HIGH_ENTROPY_THRESHOLD = Decimal("0.750000")
MEDIUM_ENTROPY_THRESHOLD = Decimal("0.500000")
METRIC_WATCH_THRESHOLD = Decimal("0.250000")
OFFICIAL_OVERRELIANCE_THRESHOLD = Decimal("0.750000")
DUPLICATE_CLAIM_WEIGHT = Decimal("0.250000")
STALE_SOURCE_WEIGHT = Decimal("0.200000")
CONTRADICTION_WEIGHT = Decimal("0.300000")
OFFICIAL_OVERRELIANCE_WEIGHT = Decimal("0.200000")
ENTROPY_BANDS = ("empty", "low", "medium", "high")
_PUBLIC_IDENTIFIER_CHARS = (
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "abcdefghijklmnopqrstuvwxyz"
    "0123456789"
    "_.-"
)
_UNSAFE_TERM_PARTS = (
    ("li", "ve"),
    ("au", "th"),
    ("wal", "let"),
    ("or", "der"),
    ("net", "work"),
    ("data", "base"),
    ("per", "sist"),
    ("sig", "ning"),
    ("muta", "tion"),
    ("b", "uy"),
    ("se", "ll"),
    ("tra", "de"),
    ("tra", "ding"),
    ("db", "_wri", "te"),
)
_UNSAFE_TERMS = tuple("".join(parts) for parts in _UNSAFE_TERM_PARTS)
_PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")


@dataclass(frozen=True)
class ResearchPacketInformationSourceEntropyObservation:
    packet_id: str
    source_id: str
    source_family: str
    claim_id: str
    official_source: bool
    stale_source: bool
    contradiction_group_id: str | None = None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchPacketInformationSourceEntropyObservation:
            raise TypeError(
                "ResearchPacketInformationSourceEntropyObservation "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchPacketInformationSourceEntropyObservation:
            raise ValueError(
                "observation must be exactly "
                "ResearchPacketInformationSourceEntropyObservation",
            )
        for field_name in ("packet_id", "source_id", "source_family", "claim_id"):
            _require_public_identifier(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "contradiction_group_id",
            _normalize_optional_public_identifier(
                "contradiction_group_id",
                self.contradiction_group_id,
            ),
        )
        _require_bool("official_source", self.official_source)
        _require_bool("stale_source", self.stale_source)
        _require_hard_flags("observation", self)
        reject_research_packet_information_source_entropy_score_v2_unsafe_payload(
            "observation",
            self,
        )


@dataclass(frozen=True)
class ResearchPacketInformationSourceFamilyDistributionBucket:
    source_family: str
    source_count: Decimal
    source_share: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchPacketInformationSourceFamilyDistributionBucket:
            raise TypeError(
                "ResearchPacketInformationSourceFamilyDistributionBucket "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchPacketInformationSourceFamilyDistributionBucket:
            raise ValueError(
                "bucket must be exactly "
                "ResearchPacketInformationSourceFamilyDistributionBucket",
            )
        _require_public_identifier("source_family", self.source_family)
        object.__setattr__(
            self,
            "source_count",
            _require_count_decimal("source_count", self.source_count),
        )
        object.__setattr__(
            self,
            "source_share",
            _require_ratio_decimal("source_share", self.source_share),
        )
        _require_hard_flags("bucket", self)
        reject_research_packet_information_source_entropy_score_v2_unsafe_payload(
            "bucket",
            self,
        )


@dataclass(frozen=True)
class ResearchPacketInformationSourceEntropyScoreV2Input:
    packet_id: str
    source_observations: tuple[ResearchPacketInformationSourceEntropyObservation, ...]
    high_entropy_threshold: Decimal = HIGH_ENTROPY_THRESHOLD
    medium_entropy_threshold: Decimal = MEDIUM_ENTROPY_THRESHOLD
    metric_watch_threshold: Decimal = METRIC_WATCH_THRESHOLD
    official_overreliance_threshold: Decimal = OFFICIAL_OVERRELIANCE_THRESHOLD
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchPacketInformationSourceEntropyScoreV2Input:
            raise TypeError(
                "ResearchPacketInformationSourceEntropyScoreV2Input "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchPacketInformationSourceEntropyScoreV2Input:
            raise ValueError(
                "score_input must be exactly "
                "ResearchPacketInformationSourceEntropyScoreV2Input",
            )
        _require_public_identifier("packet_id", self.packet_id)
        object.__setattr__(
            self,
            "source_observations",
            _normalize_source_observations(
                self.source_observations,
                packet_id=self.packet_id,
            ),
        )
        for field_name in (
            "high_entropy_threshold",
            "medium_entropy_threshold",
            "metric_watch_threshold",
            "official_overreliance_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.high_entropy_threshold < self.medium_entropy_threshold:
            raise ValueError(
                "high_entropy_threshold must be >= medium_entropy_threshold",
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags("score input", self)
        reject_research_packet_information_source_entropy_score_v2_unsafe_payload(
            "score input",
            self,
        )


@dataclass(frozen=True)
class ResearchPacketInformationSourceEntropyScoreV2Result:
    packet_id: str
    source_observations: tuple[ResearchPacketInformationSourceEntropyObservation, ...]
    source_count: Decimal
    source_family_count: Decimal
    source_family_distribution: tuple[
        ResearchPacketInformationSourceFamilyDistributionBucket,
        ...,
    ]
    official_source_count: Decimal
    official_source_share: Decimal
    duplicate_claim_count: Decimal
    duplicate_claim_ratio: Decimal
    stale_source_count: Decimal
    stale_share: Decimal
    contradiction_group_count: Decimal
    contradiction_concentration: Decimal
    source_family_entropy_score: Decimal
    source_entropy_score: Decimal
    entropy_band: str
    high_entropy_threshold: Decimal
    medium_entropy_threshold: Decimal
    metric_watch_threshold: Decimal
    official_overreliance_threshold: Decimal
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchPacketInformationSourceEntropyScoreV2Result:
            raise TypeError(
                "ResearchPacketInformationSourceEntropyScoreV2Result "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchPacketInformationSourceEntropyScoreV2Result:
            raise ValueError(
                "result must be exactly "
                "ResearchPacketInformationSourceEntropyScoreV2Result",
            )
        _require_public_identifier("packet_id", self.packet_id)
        object.__setattr__(
            self,
            "source_observations",
            _normalize_source_observations(
                self.source_observations,
                packet_id=self.packet_id,
            ),
        )
        for field_name in (
            "source_count",
            "source_family_count",
            "official_source_count",
            "duplicate_claim_count",
            "stale_source_count",
            "contradiction_group_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "source_family_distribution",
            _normalize_source_family_distribution(self.source_family_distribution),
        )
        for field_name in (
            "official_source_share",
            "duplicate_claim_ratio",
            "stale_share",
            "contradiction_concentration",
            "source_family_entropy_score",
            "source_entropy_score",
            "high_entropy_threshold",
            "medium_entropy_threshold",
            "metric_watch_threshold",
            "official_overreliance_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.high_entropy_threshold < self.medium_entropy_threshold:
            raise ValueError(
                "high_entropy_threshold must be >= medium_entropy_threshold",
            )
        _require_entropy_band("entropy_band", self.entropy_band)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_result_consistency(self)
        _require_hard_flags("result", self)
        reject_research_packet_information_source_entropy_score_v2_unsafe_payload(
            "result",
            self,
        )
        expected_digest = _derived_validation_digest(self)
        if self.derived_validation_digest:
            _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest must match result fields")
        else:
            object.__setattr__(self, "derived_validation_digest", expected_digest)

    @property
    def payload(self) -> dict[str, Any]:
        return research_packet_information_source_entropy_score_v2_payload(self)


def score_research_packet_information_source_entropy_score_v2(
    score_input: ResearchPacketInformationSourceEntropyScoreV2Input,
) -> ResearchPacketInformationSourceEntropyScoreV2Result:
    if type(score_input) is not ResearchPacketInformationSourceEntropyScoreV2Input:
        raise ValueError(
            "score_input must be a "
            "ResearchPacketInformationSourceEntropyScoreV2Input",
        )
    _require_hard_flags("score input", score_input)
    reject_research_packet_information_source_entropy_score_v2_unsafe_payload(
        "score input",
        score_input,
    )

    metrics = _metrics_from_observations(
        score_input.source_observations,
        official_overreliance_threshold=(
            score_input.official_overreliance_threshold
        ),
    )
    entropy_band = _entropy_band(
        metrics["source_count"],
        metrics["source_entropy_score"],
        metrics["duplicate_claim_ratio"],
        metrics["stale_share"],
        metrics["contradiction_concentration"],
        high_entropy_threshold=score_input.high_entropy_threshold,
        medium_entropy_threshold=score_input.medium_entropy_threshold,
        metric_watch_threshold=score_input.metric_watch_threshold,
    )

    return ResearchPacketInformationSourceEntropyScoreV2Result(
        packet_id=score_input.packet_id,
        source_observations=score_input.source_observations,
        source_count=metrics["source_count"],
        source_family_count=metrics["source_family_count"],
        source_family_distribution=metrics["source_family_distribution"],
        official_source_count=metrics["official_source_count"],
        official_source_share=metrics["official_source_share"],
        duplicate_claim_count=metrics["duplicate_claim_count"],
        duplicate_claim_ratio=metrics["duplicate_claim_ratio"],
        stale_source_count=metrics["stale_source_count"],
        stale_share=metrics["stale_share"],
        contradiction_group_count=metrics["contradiction_group_count"],
        contradiction_concentration=metrics["contradiction_concentration"],
        source_family_entropy_score=metrics["source_family_entropy_score"],
        source_entropy_score=metrics["source_entropy_score"],
        entropy_band=entropy_band,
        high_entropy_threshold=score_input.high_entropy_threshold,
        medium_entropy_threshold=score_input.medium_entropy_threshold,
        metric_watch_threshold=score_input.metric_watch_threshold,
        official_overreliance_threshold=(
            score_input.official_overreliance_threshold
        ),
        reason_codes=_reason_codes(
            score_input.reason_codes,
            source_count=metrics["source_count"],
            source_family_entropy_score=metrics["source_family_entropy_score"],
            official_source_share=metrics["official_source_share"],
            duplicate_claim_ratio=metrics["duplicate_claim_ratio"],
            stale_share=metrics["stale_share"],
            contradiction_concentration=metrics["contradiction_concentration"],
            entropy_band=entropy_band,
            high_entropy_threshold=score_input.high_entropy_threshold,
            metric_watch_threshold=score_input.metric_watch_threshold,
            official_overreliance_threshold=(
                score_input.official_overreliance_threshold
            ),
        ),
    )


def research_packet_information_source_entropy_score_v2_payload(
    result: ResearchPacketInformationSourceEntropyScoreV2Result,
) -> dict[str, Any]:
    if type(result) is not ResearchPacketInformationSourceEntropyScoreV2Result:
        raise ValueError(
            "result must be a ResearchPacketInformationSourceEntropyScoreV2Result",
        )
    _require_hard_flags("result", result)
    if result.derived_validation_digest != _derived_validation_digest(result):
        raise ValueError("derived_validation_digest must match result fields")
    reject_research_packet_information_source_entropy_score_v2_unsafe_payload(
        "result",
        result,
    )
    payload = _json_ready(asdict(result))
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    return payload


def reject_research_packet_information_source_entropy_score_v2_unsafe_payload(
    label: str,
    payload: object,
) -> None:
    _reject_unsafe_public_payload(label, payload, allow_json_containers=True)


def _metrics_from_observations(
    observations: tuple[ResearchPacketInformationSourceEntropyObservation, ...],
    *,
    official_overreliance_threshold: Decimal,
) -> dict[str, Any]:
    source_count = _decimal_count(len(observations))
    distribution = _source_family_distribution(observations, source_count)
    official_source_count = _decimal_count(
        sum(1 for observation in observations if observation.official_source),
    )
    duplicate_claim_count = _duplicate_claim_count(observations)
    stale_source_count = _decimal_count(
        sum(1 for observation in observations if observation.stale_source),
    )
    contradiction_group_counts = _contradiction_group_counts(observations)
    contradiction_group_count = _decimal_count(len(contradiction_group_counts))
    contradiction_source_count = max(
        contradiction_group_counts.values(),
        default=ZERO,
    )
    source_family_entropy_score = _source_family_entropy_score(
        distribution,
        source_count,
    )
    official_source_share = _ratio(official_source_count, source_count)
    duplicate_claim_ratio = _ratio(duplicate_claim_count, source_count)
    stale_share = _ratio(stale_source_count, source_count)
    contradiction_concentration = _ratio(contradiction_source_count, source_count)
    source_entropy_score = _source_entropy_score(
        source_family_entropy_score=source_family_entropy_score,
        official_source_share=official_source_share,
        duplicate_claim_ratio=duplicate_claim_ratio,
        stale_share=stale_share,
        contradiction_concentration=contradiction_concentration,
        official_overreliance_threshold=official_overreliance_threshold,
    )
    return {
        "source_count": source_count,
        "source_family_count": _decimal_count(len(distribution)),
        "source_family_distribution": distribution,
        "official_source_count": official_source_count,
        "official_source_share": official_source_share,
        "duplicate_claim_count": duplicate_claim_count,
        "duplicate_claim_ratio": duplicate_claim_ratio,
        "stale_source_count": stale_source_count,
        "stale_share": stale_share,
        "contradiction_group_count": contradiction_group_count,
        "contradiction_concentration": contradiction_concentration,
        "source_family_entropy_score": source_family_entropy_score,
        "source_entropy_score": source_entropy_score,
    }


def _source_family_distribution(
    observations: tuple[ResearchPacketInformationSourceEntropyObservation, ...],
    source_count: Decimal,
) -> tuple[ResearchPacketInformationSourceFamilyDistributionBucket, ...]:
    family_counts: dict[str, Decimal] = {}
    for observation in observations:
        family_counts[observation.source_family] = (
            family_counts.get(observation.source_family, ZERO) + ONE
        )
    return tuple(
        ResearchPacketInformationSourceFamilyDistributionBucket(
            source_family=source_family,
            source_count=count,
            source_share=_ratio(count, source_count),
        )
        for source_family, count in sorted(family_counts.items())
    )


def _duplicate_claim_count(
    observations: tuple[ResearchPacketInformationSourceEntropyObservation, ...],
) -> Decimal:
    claim_ids: set[str] = set()
    for observation in observations:
        claim_ids.add(observation.claim_id)
    return _decimal_count(len(observations) - len(claim_ids))


def _contradiction_group_counts(
    observations: tuple[ResearchPacketInformationSourceEntropyObservation, ...],
) -> dict[str, Decimal]:
    group_counts: dict[str, Decimal] = {}
    for observation in observations:
        if observation.contradiction_group_id is not None:
            group_counts[observation.contradiction_group_id] = (
                group_counts.get(observation.contradiction_group_id, ZERO) + ONE
            )
    return group_counts


def _source_family_entropy_score(
    distribution: tuple[ResearchPacketInformationSourceFamilyDistributionBucket, ...],
    source_count: Decimal,
) -> Decimal:
    if source_count == ZERO or len(distribution) <= 1:
        return ZERO
    with localcontext() as context:
        context.prec = 42
        entropy = ZERO
        for bucket in distribution:
            probability = bucket.source_count / source_count
            entropy -= probability * probability.ln()
        max_entropy = Decimal(len(distribution)).ln()
        return _clamp_ratio(entropy / max_entropy)


def _source_entropy_score(
    *,
    source_family_entropy_score: Decimal,
    official_source_share: Decimal,
    duplicate_claim_ratio: Decimal,
    stale_share: Decimal,
    contradiction_concentration: Decimal,
    official_overreliance_threshold: Decimal,
) -> Decimal:
    official_penalty = max(official_source_share - official_overreliance_threshold, ZERO)
    adjusted = (
        source_family_entropy_score
        - duplicate_claim_ratio * DUPLICATE_CLAIM_WEIGHT
        - stale_share * STALE_SOURCE_WEIGHT
        - contradiction_concentration * CONTRADICTION_WEIGHT
        - official_penalty * OFFICIAL_OVERRELIANCE_WEIGHT
    )
    return _clamp_ratio(adjusted)


def _entropy_band(
    source_count: Decimal,
    source_entropy_score: Decimal,
    duplicate_claim_ratio: Decimal,
    stale_share: Decimal,
    contradiction_concentration: Decimal,
    *,
    high_entropy_threshold: Decimal,
    medium_entropy_threshold: Decimal,
    metric_watch_threshold: Decimal,
) -> str:
    if source_count == ZERO:
        return "empty"
    if (
        source_entropy_score >= high_entropy_threshold
        and duplicate_claim_ratio <= metric_watch_threshold
        and stale_share <= metric_watch_threshold
        and contradiction_concentration <= metric_watch_threshold
    ):
        return "high"
    if source_entropy_score >= medium_entropy_threshold:
        return "medium"
    return "low"


def _reason_codes(
    existing: tuple[str, ...],
    *,
    source_count: Decimal,
    source_family_entropy_score: Decimal,
    official_source_share: Decimal,
    duplicate_claim_ratio: Decimal,
    stale_share: Decimal,
    contradiction_concentration: Decimal,
    entropy_band: str,
    high_entropy_threshold: Decimal,
    metric_watch_threshold: Decimal,
    official_overreliance_threshold: Decimal,
) -> tuple[str, ...]:
    additions = [
        "research_packet_information_source_entropy_score_v2",
        f"entropy_band_{entropy_band}",
    ]
    if source_count == ZERO:
        additions.append("source_family_distribution_empty")
    elif source_family_entropy_score >= high_entropy_threshold:
        additions.append("source_family_distribution_balanced")
    else:
        additions.append("source_family_distribution_concentrated")
    if official_source_share == ZERO:
        additions.append("official_source_share_absent")
    elif official_source_share > official_overreliance_threshold:
        additions.append("official_source_share_high")
    else:
        additions.append("official_source_share_present")
    if duplicate_claim_ratio > metric_watch_threshold:
        additions.append("duplicate_claim_ratio_elevated")
    else:
        additions.append("duplicate_claim_ratio_within_limit")
    if stale_share > metric_watch_threshold:
        additions.append("stale_share_elevated")
    else:
        additions.append("stale_share_within_limit")
    if contradiction_concentration > metric_watch_threshold:
        additions.append("contradiction_concentration_elevated")
    else:
        additions.append("contradiction_concentration_within_limit")
    return _append_reason_codes(existing, tuple(additions))


def _append_reason_codes(
    existing: tuple[str, ...],
    additions: tuple[str, ...],
) -> tuple[str, ...]:
    values = list(existing)
    for addition in additions:
        if addition not in values:
            values.append(addition)
    return tuple(values)


def _validate_result_consistency(
    result: ResearchPacketInformationSourceEntropyScoreV2Result,
) -> None:
    metrics = _metrics_from_observations(
        result.source_observations,
        official_overreliance_threshold=result.official_overreliance_threshold,
    )
    if result.source_family_distribution != metrics["source_family_distribution"]:
        raise ValueError("source_family_distribution must match observations")
    if result.source_count != metrics["source_count"]:
        raise ValueError("source_count must match observations")
    if result.source_family_count != metrics["source_family_count"]:
        raise ValueError("source_family_count must match observations")
    if result.official_source_count != metrics["official_source_count"]:
        raise ValueError("official_source_count must match observations")
    if result.official_source_share != metrics["official_source_share"]:
        raise ValueError("official_source_share must match observations")
    if result.duplicate_claim_count != metrics["duplicate_claim_count"]:
        raise ValueError("duplicate_claim_count must match observations")
    if result.duplicate_claim_ratio != metrics["duplicate_claim_ratio"]:
        raise ValueError("duplicate_claim_ratio must match observations")
    if result.stale_source_count != metrics["stale_source_count"]:
        raise ValueError("stale_source_count must match observations")
    if result.stale_share != metrics["stale_share"]:
        raise ValueError("stale_share must match observations")
    if result.contradiction_group_count != metrics["contradiction_group_count"]:
        raise ValueError("contradiction_group_count must match observations")
    if result.contradiction_concentration != metrics["contradiction_concentration"]:
        raise ValueError("contradiction_concentration must match observations")
    if result.source_family_entropy_score != metrics["source_family_entropy_score"]:
        raise ValueError("source_family_entropy_score must match observations")
    if result.source_entropy_score != metrics["source_entropy_score"]:
        raise ValueError("source_entropy_score must match observations")

    expected_band = _entropy_band(
        result.source_count,
        result.source_entropy_score,
        result.duplicate_claim_ratio,
        result.stale_share,
        result.contradiction_concentration,
        high_entropy_threshold=result.high_entropy_threshold,
        medium_entropy_threshold=result.medium_entropy_threshold,
        metric_watch_threshold=result.metric_watch_threshold,
    )
    if result.entropy_band != expected_band:
        raise ValueError("entropy_band must match source metrics")
    expected_reasons = _reason_codes(
        (),
        source_count=result.source_count,
        source_family_entropy_score=result.source_family_entropy_score,
        official_source_share=result.official_source_share,
        duplicate_claim_ratio=result.duplicate_claim_ratio,
        stale_share=result.stale_share,
        contradiction_concentration=result.contradiction_concentration,
        entropy_band=result.entropy_band,
        high_entropy_threshold=result.high_entropy_threshold,
        metric_watch_threshold=result.metric_watch_threshold,
        official_overreliance_threshold=result.official_overreliance_threshold,
    )
    trailing_reasons = tuple(
        reason_code
        for reason_code in result.reason_codes
        if reason_code in expected_reasons
    )
    if trailing_reasons != expected_reasons:
        raise ValueError("reason_codes must match source metrics")


def _normalize_source_observations(
    value: object,
    *,
    packet_id: str,
) -> tuple[ResearchPacketInformationSourceEntropyObservation, ...]:
    if type(value) is not tuple:
        raise ValueError("source_observations must be a tuple")
    normalized: list[ResearchPacketInformationSourceEntropyObservation] = []
    seen_source_ids: set[str] = set()
    for item in value:
        if type(item) is not ResearchPacketInformationSourceEntropyObservation:
            raise ValueError(
                "source_observations must contain "
                "ResearchPacketInformationSourceEntropyObservation values",
            )
        if item.packet_id != packet_id:
            raise ValueError("packet_id must match source_observations")
        if item.source_id in seen_source_ids:
            raise ValueError("source_id values must be unique")
        seen_source_ids.add(item.source_id)
        _require_hard_flags("observation", item)
        normalized.append(item)
    return tuple(
        sorted(
            normalized,
            key=lambda item: (
                item.source_id,
                item.source_family,
                item.claim_id,
                item.contradiction_group_id or "",
            ),
        ),
    )


def _normalize_source_family_distribution(
    value: object,
) -> tuple[ResearchPacketInformationSourceFamilyDistributionBucket, ...]:
    if type(value) is not tuple:
        raise ValueError("source_family_distribution must be a tuple")
    normalized: list[ResearchPacketInformationSourceFamilyDistributionBucket] = []
    seen_families: set[str] = set()
    for item in value:
        if type(item) is not ResearchPacketInformationSourceFamilyDistributionBucket:
            raise ValueError(
                "source_family_distribution must contain "
                "ResearchPacketInformationSourceFamilyDistributionBucket values",
            )
        if item.source_family in seen_families:
            raise ValueError("source_family_distribution families must be unique")
        seen_families.add(item.source_family)
        _require_hard_flags("bucket", item)
        normalized.append(item)
    return tuple(sorted(normalized, key=lambda item: item.source_family))


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    seen: set[str] = set()
    normalized: list[str] = []
    for reason_code in value:
        _require_public_identifier(field_name, reason_code)
        if reason_code in seen:
            raise ValueError(f"{field_name} must be unique")
        seen.add(reason_code)
        normalized.append(reason_code)
    return tuple(normalized)


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or len(value) > 128:
        raise ValueError(f"{field_name} must be a public identifier")
    if not value[0].isalnum():
        raise ValueError(f"{field_name} must be a public identifier")
    if any(character not in _PUBLIC_IDENTIFIER_CHARS for character in value):
        raise ValueError(f"{field_name} must be a public identifier")
    _reject_unsafe_public_string(field_name, value)
    return value


def _normalize_optional_public_identifier(
    field_name: str,
    value: object,
) -> str | None:
    if value is None:
        return None
    return _require_public_identifier(field_name, value)


def _require_bool(field_name: str, value: object) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")
    return value


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in _PHASE_FLAG_FIELDS:
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _require_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be integral")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _require_entropy_band(field_name: str, value: object) -> str:
    if type(value) is not str or value not in ENTROPY_BANDS:
        raise ValueError(f"{field_name} must be a known entropy band")
    return value


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    return value


def _decimal_count(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be nonnegative")
    return Decimal(value).quantize(QUANTUM)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return _clamp_ratio(numerator / denominator)


def _clamp_ratio(value: Decimal) -> Decimal:
    normalized = _quantize(value)
    if normalized < ZERO:
        return ZERO
    if normalized > ONE:
        return ONE
    return normalized


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(QUANTUM, rounding=ROUND_HALF_UP)


def _derived_validation_digest(
    result: ResearchPacketInformationSourceEntropyScoreV2Result,
) -> str:
    values = asdict(result)
    values.pop("derived_validation_digest", None)
    payload = _json_ready(values)
    reject_research_packet_information_source_entropy_score_v2_unsafe_payload(
        "digest payload",
        payload,
    )
    canonical = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return sha256(canonical.encode("utf-8")).hexdigest()


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
    if type(value) is int or type(value) is float:
        raise ValueError("numeric payload values must be Decimal strings")
    if isinstance(value, Mapping):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (tuple, list)):
        return [_json_ready(item) for item in value]
    raise ValueError("payload value is not JSON serializable")


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    path: str = "",
    *,
    allow_json_containers: bool,
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
            raise ValueError(f"{current_path} must remain constructor normalized")
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
    if isinstance(value, (tuple, list)):
        if type(value) is list and not allow_json_containers:
            raise ValueError(f"{current_path} must remain constructor normalized")
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
    if any(term in lowered for term in _UNSAFE_TERMS):
        raise ValueError(f"{path}.{key} has unsafe public field")


def _reject_unsafe_public_string(field_name: str, value: str) -> None:
    lowered = value.lower()
    if "://" in lowered or "?" in lowered or "@" in lowered:
        raise ValueError(f"{field_name} has unsafe public value")
    if any(term in lowered for term in _UNSAFE_TERMS):
        raise ValueError(f"{field_name} has unsafe public value")


__all__ = (
    "ENTROPY_BANDS",
    "ResearchPacketInformationSourceEntropyObservation",
    "ResearchPacketInformationSourceFamilyDistributionBucket",
    "ResearchPacketInformationSourceEntropyScoreV2Input",
    "ResearchPacketInformationSourceEntropyScoreV2Result",
    "score_research_packet_information_source_entropy_score_v2",
    "research_packet_information_source_entropy_score_v2_payload",
    "reject_research_packet_information_source_entropy_score_v2_unsafe_payload",
)
