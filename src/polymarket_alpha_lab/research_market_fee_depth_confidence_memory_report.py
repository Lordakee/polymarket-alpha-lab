"""Deterministic report-only market cost depth confidence memory study."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
import hashlib
import json
from typing import Any


__all__ = (
    "ResearchMarketFeeDepthConfidenceMemoryConfig",
    "ResearchMarketFeeDepthConfidenceMemoryObservation",
    "ResearchMarketFeeDepthConfidenceMemoryReport",
    "ResearchMarketFeeDepthConfidenceMemorySegment",
    "build_research_market_fee_depth_confidence_memory_report",
    "research_market_fee_depth_confidence_memory_public_payload",
    "validate_research_market_fee_depth_confidence_memory_public_payload",
)


DEFAULT_CONFIG_VERSION = "fee-depth-confidence-memory-v0"
STATUSES = ("pass", "watch", "block")
ZERO = Decimal("0")
ONE = Decimal("1")
TWO = Decimal("2")
RATIO_QUANTUM = Decimal("0.000001")


@dataclass(frozen=True)
class ResearchMarketFeeDepthConfidenceMemoryConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    max_fee_rate: Decimal = Decimal("0.020000")
    max_spread_cost: Decimal = Decimal("0.100000")
    min_depth_value: Decimal = Decimal("100.000000")
    min_confidence_score: Decimal = Decimal("0.600000")
    min_memory_observations: Decimal = Decimal("2")
    pass_score: Decimal = Decimal("0.750000")
    watch_score: Decimal = Decimal("0.450000")
    cost_weight: Decimal = Decimal("0.250000")
    depth_weight: Decimal = Decimal("0.250000")
    confidence_weight: Decimal = Decimal("0.250000")
    memory_weight: Decimal = Decimal("0.250000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "max_fee_rate",
            "max_spread_cost",
            "min_depth_value",
            "min_memory_observations",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_confidence_score",
            "pass_score",
            "watch_score",
            "cost_weight",
            "depth_weight",
            "confidence_weight",
            "memory_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        if self.pass_score <= self.watch_score:
            raise ValueError("pass_score must be greater than watch_score")
        if self.min_memory_observations != self.min_memory_observations.to_integral_value():
            raise ValueError("min_memory_observations must be a whole count")
        weight_sum = _quantize(
            self.cost_weight
            + self.depth_weight
            + self.confidence_weight
            + self.memory_weight,
        )
        if weight_sum != ONE:
            raise ValueError(
                "cost_weight, depth_weight, confidence_weight, and memory_weight "
                "must sum to 1",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchMarketFeeDepthConfidenceMemoryObservation:
    case_id: str
    sample_id: str
    observed_at: datetime
    fee_rate: Decimal
    spread_cost: Decimal
    depth_value: Decimal
    confidence_score: Decimal
    private_candidate_ref: str | None = None
    private_market_ref: str | None = None
    private_source_ref: str | None = None
    private_notes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("case_id", self.case_id)
        _require_canonical_string("sample_id", self.sample_id)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in ("fee_rate", "spread_cost", "depth_value"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "confidence_score",
            _require_probability_decimal("confidence_score", self.confidence_score),
        )
        for field_name in (
            "private_candidate_ref",
            "private_market_ref",
            "private_source_ref",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_optional_private_string(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "private_notes",
            _normalize_private_notes(self.private_notes),
        )
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class ResearchMarketFeeDepthConfidenceMemorySegment:
    case_id: str
    case_digest: str
    observation_count: Decimal
    latest_observed_at: datetime
    average_fee_rate: Decimal
    average_spread_cost: Decimal
    average_depth_value: Decimal
    confidence_score: Decimal
    memory_score: Decimal
    cost_score: Decimal
    depth_score: Decimal
    cost_weight: Decimal
    depth_weight: Decimal
    confidence_weight: Decimal
    memory_weight: Decimal
    pass_score: Decimal
    watch_score: Decimal
    composite_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("case_id", self.case_id)
        object.__setattr__(self, "case_digest", _require_sha256("case_digest", self.case_digest))
        object.__setattr__(
            self,
            "observation_count",
            _require_positive_whole_decimal("observation_count", self.observation_count),
        )
        object.__setattr__(
            self,
            "latest_observed_at",
            _as_utc("latest_observed_at", self.latest_observed_at),
        )
        for field_name in ("average_fee_rate", "average_spread_cost", "average_depth_value"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "confidence_score",
            "memory_score",
            "cost_score",
            "depth_score",
            "cost_weight",
            "depth_weight",
            "confidence_weight",
            "memory_weight",
            "pass_score",
            "watch_score",
            "composite_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        if self.pass_score <= self.watch_score:
            raise ValueError("pass_score must be greater than watch_score")
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _require_hard_flags("segment", self)
        _validate_segment_consistency(self)


@dataclass(frozen=True)
class ResearchMarketFeeDepthConfidenceMemoryReport:
    generated_at: datetime
    config_version: str
    segment_count: Decimal
    observation_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_score: Decimal | None
    status: str
    segments: tuple[ResearchMarketFeeDepthConfidenceMemorySegment, ...]
    reason_codes: tuple[str, ...]
    public_payload_sha256: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "segment_count",
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
        object.__setattr__(
            self,
            "average_score",
            _require_optional_probability_decimal("average_score", self.average_score),
        )
        _require_status("status", self.status)
        object.__setattr__(self, "segments", _normalize_segments(self.segments))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        object.__setattr__(
            self,
            "public_payload_sha256",
            _require_sha256("public_payload_sha256", self.public_payload_sha256),
        )
        _require_hard_flags("report", self)
        _validate_report_consistency(self)


def build_research_market_fee_depth_confidence_memory_report(
    observations: Iterable[object],
    *,
    config: ResearchMarketFeeDepthConfidenceMemoryConfig,
    generated_at: datetime,
) -> ResearchMarketFeeDepthConfidenceMemoryReport:
    if type(config) is not ResearchMarketFeeDepthConfidenceMemoryConfig:
        raise ValueError(
            "config must be a ResearchMarketFeeDepthConfidenceMemoryConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    items = _normalize_observations(observations)
    for item in items:
        if item.observed_at > generated_at_utc:
            raise ValueError("observed_at must not be after generated_at")

    grouped: dict[str, list[ResearchMarketFeeDepthConfidenceMemoryObservation]] = {}
    for item in items:
        grouped.setdefault(item.case_id, []).append(item)

    segments = tuple(
        _build_segment(case_id=case_id, observations=tuple(grouped[case_id]), config=config)
        for case_id in sorted(grouped)
    )
    reason_codes = _report_reason_codes(segments)
    segment_count = _decimal_count(len(segments))
    observation_count = sum((segment.observation_count for segment in segments), ZERO)
    pass_count = _decimal_count(_status_count(segments, "pass"))
    watch_count = _decimal_count(_status_count(segments, "watch"))
    block_count = _decimal_count(_status_count(segments, "block"))
    average_score = _average_decimal_or_none(
        tuple(segment.composite_score for segment in segments),
    )
    status = _report_status(reason_codes)
    digest = _payload_sha256(
        _public_payload_without_digest_from_parts(
            generated_at=generated_at_utc,
            config_version=config.config_version,
            segment_count=segment_count,
            observation_count=observation_count,
            pass_count=pass_count,
            watch_count=watch_count,
            block_count=block_count,
            average_score=average_score,
            status=status,
            segments=segments,
            reason_codes=reason_codes,
            paper_only=True,
            report_only=True,
            readonly=True,
        ),
    )

    return ResearchMarketFeeDepthConfidenceMemoryReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        segment_count=segment_count,
        observation_count=observation_count,
        pass_count=pass_count,
        watch_count=watch_count,
        block_count=block_count,
        average_score=average_score,
        status=status,
        segments=segments,
        reason_codes=reason_codes,
        public_payload_sha256=digest,
    )


def research_market_fee_depth_confidence_memory_public_payload(
    report: ResearchMarketFeeDepthConfidenceMemoryReport,
) -> dict[str, Any]:
    if type(report) is not ResearchMarketFeeDepthConfidenceMemoryReport:
        raise ValueError("report must be a ResearchMarketFeeDepthConfidenceMemoryReport")
    _require_hard_flags("report", report)
    payload = _public_payload_without_digest(report)
    payload["sha256_digest"] = report.public_payload_sha256
    if _payload_sha256({k: v for k, v in payload.items() if k != "sha256_digest"}) != (
        report.public_payload_sha256
    ):
        raise ValueError("public_payload_sha256 does not match public payload")
    return payload


def validate_research_market_fee_depth_confidence_memory_public_payload(
    payload: object,
) -> bool:
    if not isinstance(payload, dict):
        return False
    digest = payload.get("sha256_digest")
    if type(digest) is not str or not _is_sha256(digest):
        return False
    unsigned_payload = {key: value for key, value in payload.items() if key != "sha256_digest"}
    return _payload_sha256(unsigned_payload) == digest


def _build_segment(
    *,
    case_id: str,
    observations: tuple[ResearchMarketFeeDepthConfidenceMemoryObservation, ...],
    config: ResearchMarketFeeDepthConfidenceMemoryConfig,
) -> ResearchMarketFeeDepthConfidenceMemorySegment:
    if not observations:
        raise ValueError("observations must be nonempty")
    sample_ids = tuple(item.sample_id for item in observations)
    if len(set(sample_ids)) != len(sample_ids):
        raise ValueError("sample_id values must be unique within a case_id")
    sorted_items = tuple(sorted(observations, key=lambda item: item.sample_id))
    observation_count = _decimal_count(len(sorted_items))
    average_fee_rate = _average_decimal(tuple(item.fee_rate for item in sorted_items))
    average_spread_cost = _average_decimal(tuple(item.spread_cost for item in sorted_items))
    average_depth_value = _average_decimal(tuple(item.depth_value for item in sorted_items))
    confidence_score = _average_decimal(tuple(item.confidence_score for item in sorted_items))
    memory_score = _bounded_ratio(observation_count, config.min_memory_observations)
    cost_score = _average_decimal(
        (
            _one_minus_bounded_ratio(average_fee_rate, config.max_fee_rate),
            _one_minus_bounded_ratio(average_spread_cost, config.max_spread_cost),
        ),
    )
    depth_score = _bounded_ratio(average_depth_value, config.min_depth_value)
    composite_score = _weighted_score(
        cost_score=cost_score,
        depth_score=depth_score,
        confidence_score=confidence_score,
        memory_score=memory_score,
        cost_weight=config.cost_weight,
        depth_weight=config.depth_weight,
        confidence_weight=config.confidence_weight,
        memory_weight=config.memory_weight,
    )
    status = _score_status(
        composite_score,
        pass_score=config.pass_score,
        watch_score=config.watch_score,
    )
    reason_codes = _segment_reason_codes(
        cost_score=cost_score,
        depth_score=depth_score,
        confidence_score=confidence_score,
        memory_score=memory_score,
        composite_score=composite_score,
        config=config,
    )

    return ResearchMarketFeeDepthConfidenceMemorySegment(
        case_id=case_id,
        case_digest=_sha256_text(case_id),
        observation_count=observation_count,
        latest_observed_at=max(item.observed_at for item in sorted_items),
        average_fee_rate=average_fee_rate,
        average_spread_cost=average_spread_cost,
        average_depth_value=average_depth_value,
        confidence_score=confidence_score,
        memory_score=memory_score,
        cost_score=cost_score,
        depth_score=depth_score,
        cost_weight=config.cost_weight,
        depth_weight=config.depth_weight,
        confidence_weight=config.confidence_weight,
        memory_weight=config.memory_weight,
        pass_score=config.pass_score,
        watch_score=config.watch_score,
        composite_score=composite_score,
        status=status,
        reason_codes=reason_codes,
    )


def _segment_reason_codes(
    *,
    cost_score: Decimal,
    depth_score: Decimal,
    confidence_score: Decimal,
    memory_score: Decimal,
    composite_score: Decimal,
    config: ResearchMarketFeeDepthConfidenceMemoryConfig,
) -> tuple[str, ...]:
    return tuple(
        sorted(
            {
                _component_reason_code("cost", cost_score, config),
                _component_reason_code("depth", depth_score, config),
                _component_reason_code("confidence", confidence_score, config),
                _component_reason_code("memory", memory_score, config),
                f"segment_{_score_status(composite_score, pass_score=config.pass_score, watch_score=config.watch_score)}",
            },
        ),
    )


def _component_reason_code(
    prefix: str,
    score: Decimal,
    config: ResearchMarketFeeDepthConfidenceMemoryConfig,
) -> str:
    return (
        f"{prefix}_"
        f"{_score_status(score, pass_score=config.pass_score, watch_score=config.watch_score)}"
    )


def _report_reason_codes(
    segments: tuple[ResearchMarketFeeDepthConfidenceMemorySegment, ...],
) -> tuple[str, ...]:
    if not segments:
        return ("no_observations",)
    codes: set[str] = set()
    if any(segment.status == "block" for segment in segments):
        codes.add("segment_block")
    if any(segment.status == "watch" for segment in segments):
        codes.add("segment_watch")
    if all(segment.status == "pass" for segment in segments):
        codes.add("all_segments_pass")
    counter = Counter(code for segment in segments for code in segment.reason_codes)
    codes.update(code for code, count in counter.items() if count > 1)
    return tuple(sorted(codes))


def _report_status(reason_codes: tuple[str, ...]) -> str:
    if "no_observations" in reason_codes or "segment_block" in reason_codes:
        return "block"
    if "segment_watch" in reason_codes:
        return "watch"
    return "pass"


def _score_status(score: Decimal, *, pass_score: Decimal, watch_score: Decimal) -> str:
    if score >= pass_score:
        return "pass"
    if score >= watch_score:
        return "watch"
    return "block"


def _validate_segment_consistency(
    segment: ResearchMarketFeeDepthConfidenceMemorySegment,
) -> None:
    expected_digest = _sha256_text(segment.case_id)
    if segment.case_digest != expected_digest:
        raise ValueError("case_digest does not match case_id")
    expected_score = _weighted_score(
        cost_score=segment.cost_score,
        depth_score=segment.depth_score,
        confidence_score=segment.confidence_score,
        memory_score=segment.memory_score,
        cost_weight=segment.cost_weight,
        depth_weight=segment.depth_weight,
        confidence_weight=segment.confidence_weight,
        memory_weight=segment.memory_weight,
    )
    if segment.composite_score != expected_score:
        raise ValueError("composite_score does not match component scores")
    expected_status = _score_status(
        segment.composite_score,
        pass_score=segment.pass_score,
        watch_score=segment.watch_score,
    )
    if segment.status != expected_status:
        raise ValueError("status does not match composite_score")
    required_segment_code = f"segment_{segment.status}"
    if required_segment_code not in segment.reason_codes:
        raise ValueError("reason_codes must include segment status")


def _validate_report_consistency(report: ResearchMarketFeeDepthConfidenceMemoryReport) -> None:
    if report.segment_count != _decimal_count(len(report.segments)):
        raise ValueError("segment_count does not match segments")
    expected_observation_count = sum(
        (segment.observation_count for segment in report.segments),
        ZERO,
    )
    if report.observation_count != expected_observation_count:
        raise ValueError("observation_count does not match segments")
    expected_pass_count = _decimal_count(_status_count(report.segments, "pass"))
    expected_watch_count = _decimal_count(_status_count(report.segments, "watch"))
    expected_block_count = _decimal_count(_status_count(report.segments, "block"))
    if report.pass_count != expected_pass_count:
        raise ValueError("pass_count does not match segments")
    if report.watch_count != expected_watch_count:
        raise ValueError("watch_count does not match segments")
    if report.block_count != expected_block_count:
        raise ValueError("block_count does not match segments")
    expected_average_score = _average_decimal_or_none(
        tuple(segment.composite_score for segment in report.segments),
    )
    if report.average_score != expected_average_score:
        raise ValueError("average_score does not match segments")
    expected_reason_codes = _report_reason_codes(report.segments)
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes do not match segments")
    expected_status = _report_status(expected_reason_codes)
    if report.status != expected_status:
        raise ValueError("status does not match reason_codes")
    expected_digest = _payload_sha256(_public_payload_without_digest(report))
    if report.public_payload_sha256 != expected_digest:
        raise ValueError("public_payload_sha256 does not match public payload")


def _weighted_score(
    *,
    cost_score: Decimal,
    depth_score: Decimal,
    confidence_score: Decimal,
    memory_score: Decimal,
    cost_weight: Decimal,
    depth_weight: Decimal,
    confidence_weight: Decimal,
    memory_weight: Decimal,
) -> Decimal:
    return _quantize(
        cost_score * cost_weight
        + depth_score * depth_weight
        + confidence_score * confidence_weight
        + memory_score * memory_weight,
    )


def _average_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        raise ValueError("values must be nonempty")
    return _quantize(sum(values, ZERO) / Decimal(len(values)))


def _average_decimal_or_none(values: tuple[Decimal, ...]) -> Decimal | None:
    if not values:
        return None
    return _average_decimal(values)


def _bounded_ratio(value: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= ZERO:
        raise ValueError("denominator must be positive")
    ratio = value / denominator
    if ratio > ONE:
        ratio = ONE
    if ratio < ZERO:
        ratio = ZERO
    return _quantize(ratio)


def _one_minus_bounded_ratio(value: Decimal, denominator: Decimal) -> Decimal:
    return _quantize(ONE - _bounded_ratio(value, denominator))


def _normalize_observations(
    observations: Iterable[object],
) -> tuple[ResearchMarketFeeDepthConfidenceMemoryObservation, ...]:
    if isinstance(observations, (str, bytes)):
        raise ValueError("observations must be an iterable")
    try:
        values = tuple(observations)
    except TypeError as exc:
        raise ValueError("observations must be an iterable") from exc
    normalized: list[ResearchMarketFeeDepthConfidenceMemoryObservation] = []
    for value in values:
        if type(value) is not ResearchMarketFeeDepthConfidenceMemoryObservation:
            raise ValueError(
                "observations must contain ResearchMarketFeeDepthConfidenceMemoryObservation",
            )
        _require_hard_flags("observation", value)
        normalized.append(value)
    return tuple(normalized)


def _normalize_segments(
    segments: object,
) -> tuple[ResearchMarketFeeDepthConfidenceMemorySegment, ...]:
    if type(segments) is not tuple:
        raise ValueError("segments must be a tuple")
    normalized: list[ResearchMarketFeeDepthConfidenceMemorySegment] = []
    for value in segments:
        if type(value) is not ResearchMarketFeeDepthConfidenceMemorySegment:
            raise ValueError(
                "segments must contain ResearchMarketFeeDepthConfidenceMemorySegment",
        )
        _require_hard_flags("segment", value)
        normalized.append(value)
    return tuple(sorted(normalized, key=lambda item: item.case_id))


def _public_payload_without_digest(
    report: ResearchMarketFeeDepthConfidenceMemoryReport,
) -> dict[str, Any]:
    return _public_payload_without_digest_from_parts(
        generated_at=report.generated_at,
        config_version=report.config_version,
        segment_count=report.segment_count,
        observation_count=report.observation_count,
        pass_count=report.pass_count,
        watch_count=report.watch_count,
        block_count=report.block_count,
        average_score=report.average_score,
        status=report.status,
        segments=report.segments,
        reason_codes=report.reason_codes,
        paper_only=report.paper_only,
        report_only=report.report_only,
        readonly=report.readonly,
    )


def _public_payload_without_digest_from_parts(
    *,
    generated_at: datetime,
    config_version: str,
    segment_count: Decimal,
    observation_count: Decimal,
    pass_count: Decimal,
    watch_count: Decimal,
    block_count: Decimal,
    average_score: Decimal | None,
    status: str,
    segments: tuple[ResearchMarketFeeDepthConfidenceMemorySegment, ...],
    reason_codes: tuple[str, ...],
    paper_only: bool,
    report_only: bool,
    readonly: bool,
) -> dict[str, Any]:
    return {
        "generated_at": generated_at.isoformat(),
        "config_version": config_version,
        "segment_count": str(segment_count),
        "observation_count": str(observation_count),
        "pass_count": str(pass_count),
        "watch_count": str(watch_count),
        "block_count": str(block_count),
        "average_score": None if average_score is None else str(average_score),
        "status": status,
        "segments": [_segment_public_payload(segment) for segment in segments],
        "reason_codes": list(reason_codes),
        "paper_only": paper_only,
        "report_only": report_only,
        "readonly": readonly,
    }


def _segment_public_payload(
    segment: ResearchMarketFeeDepthConfidenceMemorySegment,
) -> dict[str, Any]:
    return {
        "case_digest": segment.case_digest,
        "observation_count": str(segment.observation_count),
        "latest_observed_at": segment.latest_observed_at.isoformat(),
        "average_fee_rate": str(segment.average_fee_rate),
        "average_spread_cost": str(segment.average_spread_cost),
        "average_depth_value": str(segment.average_depth_value),
        "confidence_score": str(segment.confidence_score),
        "memory_score": str(segment.memory_score),
        "cost_score": str(segment.cost_score),
        "depth_score": str(segment.depth_score),
        "composite_score": str(segment.composite_score),
        "status": segment.status,
        "reason_codes": list(segment.reason_codes),
    }


def _payload_sha256(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _is_sha256(value: str) -> bool:
    return len(value) == 64 and all(char in "0123456789abcdef" for char in value)


def _require_sha256(field_name: str, value: object) -> str:
    if type(value) is not str or not _is_sha256(value):
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")
    return value


def _status_count(
    segments: tuple[ResearchMarketFeeDepthConfidenceMemorySegment, ...],
    status: str,
) -> int:
    return sum(1 for segment in segments if segment.status == status)


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count source must be an int")
    if value < 0:
        raise ValueError("count source must be nonnegative")
    return Decimal(value)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(RATIO_QUANTUM)


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
    return normalized


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_probability_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _quantize(normalized)


def _require_optional_probability_decimal(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _require_probability_decimal(field_name, value)


def _require_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_positive_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return normalized


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return normalized


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a nonempty canonical string")


def _require_optional_private_string(field_name: str, value: object) -> str | None:
    if value is None:
        return None
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a nonempty private string")
    return value


def _normalize_private_notes(values: object) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError("private_notes must be a tuple")
    normalized: list[str] = []
    for value in values:
        if type(value) is not str or not value or value.strip() != value:
            raise ValueError("private_notes must contain nonempty private strings")
        normalized.append(value)
    return tuple(normalized)


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


def _require_reason_code(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    allowed = "abcdefghijklmnopqrstuvwxyz0123456789_"
    if any(char not in allowed for char in value):
        raise ValueError(f"{field_name} must contain lowercase reason codes")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be one of {STATUSES}")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_hard_flags(field_name: str, value: object) -> None:
    for flag in ("paper_only", "report_only", "readonly"):
        if getattr(value, flag, None) is not True:
            raise ValueError(f"{field_name}.{flag} must be True")
