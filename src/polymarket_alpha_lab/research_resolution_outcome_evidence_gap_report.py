"""Pure report-only resolution outcome evidence gap report."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


DEFAULT_RESEARCH_RESOLUTION_OUTCOME_EVIDENCE_GAP_REPORT_CONFIG_VERSION = (
    "research-resolution-outcome-evidence-gap-report-v0"
)

RESOLUTION_OUTCOME_EVIDENCE_GAP_STATUSES = ("pass", "watch", "block")

PASS_REASON = "resolution_outcome_evidence_gap_pass"
WATCH_REASON = "resolution_outcome_evidence_gap_watch"
BLOCK_REASON = "resolution_outcome_evidence_gap_block"
SOURCE_AGE_WATCH_REASON = "aggregate_source_age_watch"
SOURCE_AGE_BLOCK_REASON = "aggregate_source_age_block"
SOURCE_CLASS_WATCH_REASON = "source_class_diversity_watch"
SOURCE_CLASS_BLOCK_REASON = "source_class_diversity_block"
CONTRADICTION_WATCH_REASON = "contradiction_pressure_watch"
CONTRADICTION_BLOCK_REASON = "contradiction_pressure_block"
ORACLE_CLARITY_WATCH_REASON = "oracle_clarity_watch"
ORACLE_CLARITY_BLOCK_REASON = "oracle_clarity_block"
DEADLINE_NEAR_REASON = "resolution_deadline_near"
DEADLINE_IMMINENT_REASON = "resolution_deadline_imminent"

REASON_CODES = (
    PASS_REASON,
    WATCH_REASON,
    BLOCK_REASON,
    SOURCE_AGE_WATCH_REASON,
    SOURCE_AGE_BLOCK_REASON,
    SOURCE_CLASS_WATCH_REASON,
    SOURCE_CLASS_BLOCK_REASON,
    CONTRADICTION_WATCH_REASON,
    CONTRADICTION_BLOCK_REASON,
    ORACLE_CLARITY_WATCH_REASON,
    ORACLE_CLARITY_BLOCK_REASON,
    DEADLINE_NEAR_REASON,
    DEADLINE_IMMINENT_REASON,
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")


@dataclass(frozen=True)
class ResearchResolutionOutcomeEvidenceGapConfig:
    config_version: str = DEFAULT_RESEARCH_RESOLUTION_OUTCOME_EVIDENCE_GAP_REPORT_CONFIG_VERSION
    fresh_source_age_seconds: Decimal = Decimal("3600.000000")
    stale_source_age_seconds: Decimal = Decimal("7200.000000")
    required_source_class_count: Decimal = Decimal("3.000000")
    minimum_source_class_count: Decimal = Decimal("2.000000")
    contradiction_watch_threshold: Decimal = Decimal("0.250000")
    contradiction_block_threshold: Decimal = Decimal("0.500000")
    oracle_clarity_watch_threshold: Decimal = Decimal("0.700000")
    oracle_clarity_block_threshold: Decimal = Decimal("0.450000")
    near_deadline_seconds: Decimal = Decimal("86400.000000")
    imminent_deadline_seconds: Decimal = Decimal("3600.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        raise TypeError("ResearchResolutionOutcomeEvidenceGapConfig does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not ResearchResolutionOutcomeEvidenceGapConfig:
            raise ValueError("config must be exactly ResearchResolutionOutcomeEvidenceGapConfig")
        _require_public_string("config_version", self.config_version)
        if self.config_version != DEFAULT_RESEARCH_RESOLUTION_OUTCOME_EVIDENCE_GAP_REPORT_CONFIG_VERSION:
            raise ValueError("config_version must be supported")
        for field_name in (
            "fresh_source_age_seconds",
            "stale_source_age_seconds",
            "required_source_class_count",
            "minimum_source_class_count",
            "near_deadline_seconds",
            "imminent_deadline_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "contradiction_watch_threshold",
            "contradiction_block_threshold",
            "oracle_clarity_watch_threshold",
            "oracle_clarity_block_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.stale_source_age_seconds <= self.fresh_source_age_seconds:
            raise ValueError("stale_source_age_seconds must exceed fresh_source_age_seconds")
        if self.required_source_class_count < self.minimum_source_class_count:
            raise ValueError("required_source_class_count must be at least minimum_source_class_count")
        if self.contradiction_block_threshold <= self.contradiction_watch_threshold:
            raise ValueError("contradiction_block_threshold must exceed contradiction_watch_threshold")
        if self.oracle_clarity_watch_threshold <= self.oracle_clarity_block_threshold:
            raise ValueError("oracle_clarity_watch_threshold must exceed oracle_clarity_block_threshold")
        if self.near_deadline_seconds <= self.imminent_deadline_seconds:
            raise ValueError("near_deadline_seconds must exceed imminent_deadline_seconds")
        reject_unsafe_surface_fields("resolution outcome evidence gap config", self)
        require_paper_only_flags("resolution outcome evidence gap config", self)


@dataclass(frozen=True)
class ResearchResolutionOutcomeEvidenceGapInputs:
    resolution_event_count: Decimal
    aggregate_source_age_seconds: Decimal
    source_class_count: Decimal
    contradiction_pressure: Decimal
    oracle_clarity_score: Decimal
    seconds_to_resolution_deadline: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        raise TypeError("ResearchResolutionOutcomeEvidenceGapInputs does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not ResearchResolutionOutcomeEvidenceGapInputs:
            raise ValueError("inputs must be exactly ResearchResolutionOutcomeEvidenceGapInputs")
        for field_name in (
            "resolution_event_count",
            "aggregate_source_age_seconds",
            "source_class_count",
            "seconds_to_resolution_deadline",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("contradiction_pressure", "oracle_clarity_score"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        reject_unsafe_surface_fields("resolution outcome evidence gap inputs", self)
        require_paper_only_flags("resolution outcome evidence gap inputs", self)


@dataclass(frozen=True)
class ResearchResolutionOutcomeEvidenceGapReport:
    generated_at: datetime
    config_version: str
    report_status: str
    reason_codes: tuple[str, ...]
    resolution_event_count: Decimal
    aggregate_source_age_seconds: Decimal
    source_class_count: Decimal
    required_source_class_count: Decimal
    source_class_gap_count: Decimal
    contradiction_pressure: Decimal
    oracle_clarity_score: Decimal
    seconds_to_resolution_deadline: Decimal
    source_age_pressure: Decimal
    source_class_gap_ratio: Decimal
    oracle_ambiguity_pressure: Decimal
    deadline_proximity_pressure: Decimal
    evidence_gap_score: Decimal
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        raise TypeError("ResearchResolutionOutcomeEvidenceGapReport does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not ResearchResolutionOutcomeEvidenceGapReport:
            raise ValueError("report must be exactly ResearchResolutionOutcomeEvidenceGapReport")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        if self.config_version != DEFAULT_RESEARCH_RESOLUTION_OUTCOME_EVIDENCE_GAP_REPORT_CONFIG_VERSION:
            raise ValueError("config_version must be supported")
        _require_member("report_status", self.report_status, RESOLUTION_OUTCOME_EVIDENCE_GAP_STATUSES)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        for field_name in (
            "resolution_event_count",
            "aggregate_source_age_seconds",
            "source_class_count",
            "required_source_class_count",
            "source_class_gap_count",
            "seconds_to_resolution_deadline",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "contradiction_pressure",
            "oracle_clarity_score",
            "source_age_pressure",
            "source_class_gap_ratio",
            "oracle_ambiguity_pressure",
            "deadline_proximity_pressure",
            "evidence_gap_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.derived_validation_digest:
            _require_sha256("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != _derived_validation_digest(self):
                raise ValueError("derived_validation_digest must match report fields")
        else:
            object.__setattr__(
                self,
                "derived_validation_digest",
                _derived_validation_digest(self),
            )
        reject_unsafe_surface_fields("resolution outcome evidence gap report", self)
        require_paper_only_flags("resolution outcome evidence gap report", self)


def build_research_resolution_outcome_evidence_gap_report(
    inputs: ResearchResolutionOutcomeEvidenceGapInputs,
    *,
    config: ResearchResolutionOutcomeEvidenceGapConfig,
    generated_at: datetime,
) -> ResearchResolutionOutcomeEvidenceGapReport:
    if type(inputs) is not ResearchResolutionOutcomeEvidenceGapInputs:
        raise ValueError("inputs must be a ResearchResolutionOutcomeEvidenceGapInputs")
    if type(config) is not ResearchResolutionOutcomeEvidenceGapConfig:
        raise ValueError("config must be a ResearchResolutionOutcomeEvidenceGapConfig")
    require_paper_only_flags("inputs", inputs)
    require_paper_only_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)

    source_age_pressure = _source_age_pressure(inputs.aggregate_source_age_seconds, config)
    source_class_gap_count = _nonnegative_difference(
        config.required_source_class_count,
        inputs.source_class_count,
    )
    source_class_gap_ratio = _safe_ratio(
        source_class_gap_count,
        config.required_source_class_count,
    )
    oracle_ambiguity_pressure = _ratio_difference(ONE, inputs.oracle_clarity_score)
    deadline_proximity_pressure = _deadline_proximity_pressure(
        inputs.seconds_to_resolution_deadline,
        config,
    )
    report_status = _report_status(inputs, config)
    return ResearchResolutionOutcomeEvidenceGapReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        report_status=report_status,
        reason_codes=_reason_codes(inputs, config, report_status),
        resolution_event_count=inputs.resolution_event_count,
        aggregate_source_age_seconds=inputs.aggregate_source_age_seconds,
        source_class_count=inputs.source_class_count,
        required_source_class_count=config.required_source_class_count,
        source_class_gap_count=source_class_gap_count,
        contradiction_pressure=inputs.contradiction_pressure,
        oracle_clarity_score=inputs.oracle_clarity_score,
        seconds_to_resolution_deadline=inputs.seconds_to_resolution_deadline,
        source_age_pressure=source_age_pressure,
        source_class_gap_ratio=source_class_gap_ratio,
        oracle_ambiguity_pressure=oracle_ambiguity_pressure,
        deadline_proximity_pressure=deadline_proximity_pressure,
        evidence_gap_score=_evidence_gap_score(
            source_age_pressure=source_age_pressure,
            source_class_gap_ratio=source_class_gap_ratio,
            contradiction_pressure=inputs.contradiction_pressure,
            oracle_ambiguity_pressure=oracle_ambiguity_pressure,
            deadline_proximity_pressure=deadline_proximity_pressure,
        ),
    )


def research_resolution_outcome_evidence_gap_report_payload(
    report: ResearchResolutionOutcomeEvidenceGapReport,
) -> dict[str, Any]:
    if type(report) is not ResearchResolutionOutcomeEvidenceGapReport:
        raise ValueError("report must be a ResearchResolutionOutcomeEvidenceGapReport")
    require_paper_only_flags("report", report)
    if report.derived_validation_digest != _derived_validation_digest(report):
        raise ValueError("derived_validation_digest must match report fields")
    reject_unsafe_surface_fields("resolution outcome evidence gap report", report)
    return json_ready_no_floats(report)


def _report_status(
    inputs: ResearchResolutionOutcomeEvidenceGapInputs,
    config: ResearchResolutionOutcomeEvidenceGapConfig,
) -> str:
    if (
        inputs.aggregate_source_age_seconds > config.stale_source_age_seconds
        or inputs.source_class_count < config.minimum_source_class_count
        or inputs.contradiction_pressure >= config.contradiction_block_threshold
        or inputs.oracle_clarity_score <= config.oracle_clarity_block_threshold
        or inputs.seconds_to_resolution_deadline <= config.imminent_deadline_seconds
    ):
        return "block"
    if (
        inputs.aggregate_source_age_seconds > config.fresh_source_age_seconds
        or inputs.source_class_count < config.required_source_class_count
        or inputs.contradiction_pressure >= config.contradiction_watch_threshold
        or inputs.oracle_clarity_score < config.oracle_clarity_watch_threshold
        or inputs.seconds_to_resolution_deadline <= config.near_deadline_seconds
    ):
        return "watch"
    return "pass"


def _reason_codes(
    inputs: ResearchResolutionOutcomeEvidenceGapInputs,
    config: ResearchResolutionOutcomeEvidenceGapConfig,
    report_status: str,
) -> tuple[str, ...]:
    codes = [_status_reason(report_status)]
    if inputs.aggregate_source_age_seconds > config.stale_source_age_seconds:
        codes.append(SOURCE_AGE_BLOCK_REASON)
    elif inputs.aggregate_source_age_seconds > config.fresh_source_age_seconds:
        codes.append(SOURCE_AGE_WATCH_REASON)
    if inputs.source_class_count < config.minimum_source_class_count:
        codes.append(SOURCE_CLASS_BLOCK_REASON)
    elif inputs.source_class_count < config.required_source_class_count:
        codes.append(SOURCE_CLASS_WATCH_REASON)
    if inputs.contradiction_pressure >= config.contradiction_block_threshold:
        codes.append(CONTRADICTION_BLOCK_REASON)
    elif inputs.contradiction_pressure >= config.contradiction_watch_threshold:
        codes.append(CONTRADICTION_WATCH_REASON)
    if inputs.oracle_clarity_score <= config.oracle_clarity_block_threshold:
        codes.append(ORACLE_CLARITY_BLOCK_REASON)
    elif inputs.oracle_clarity_score < config.oracle_clarity_watch_threshold:
        codes.append(ORACLE_CLARITY_WATCH_REASON)
    if inputs.seconds_to_resolution_deadline <= config.imminent_deadline_seconds:
        codes.append(DEADLINE_IMMINENT_REASON)
    elif inputs.seconds_to_resolution_deadline <= config.near_deadline_seconds:
        codes.append(DEADLINE_NEAR_REASON)
    return _normalize_reason_codes(tuple(codes))


def _status_reason(report_status: str) -> str:
    if report_status == "block":
        return BLOCK_REASON
    if report_status == "watch":
        return WATCH_REASON
    return PASS_REASON


def _source_age_pressure(
    aggregate_source_age_seconds: Decimal,
    config: ResearchResolutionOutcomeEvidenceGapConfig,
) -> Decimal:
    if aggregate_source_age_seconds <= config.fresh_source_age_seconds:
        return ZERO
    pressure = _safe_ratio(
        aggregate_source_age_seconds - config.fresh_source_age_seconds,
        config.stale_source_age_seconds - config.fresh_source_age_seconds,
    )
    return _cap_ratio(pressure)


def _deadline_proximity_pressure(
    seconds_to_resolution_deadline: Decimal,
    config: ResearchResolutionOutcomeEvidenceGapConfig,
) -> Decimal:
    if seconds_to_resolution_deadline >= config.near_deadline_seconds:
        return ZERO
    pressure = _safe_ratio(
        config.near_deadline_seconds - seconds_to_resolution_deadline,
        config.near_deadline_seconds,
    )
    return _cap_ratio(pressure)


def _evidence_gap_score(
    *,
    source_age_pressure: Decimal,
    source_class_gap_ratio: Decimal,
    contradiction_pressure: Decimal,
    oracle_ambiguity_pressure: Decimal,
    deadline_proximity_pressure: Decimal,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        value = (
            source_age_pressure
            + source_class_gap_ratio
            + contradiction_pressure
            + oracle_ambiguity_pressure
            + deadline_proximity_pressure
        ) / Decimal("5")
    return _cap_ratio(value)


def _cap_ratio(value: Decimal) -> Decimal:
    if value < ZERO:
        return ZERO
    if value > ONE:
        return ONE
    return value.quantize(QUANT)


def _ratio_difference(first: Decimal, second: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _cap_ratio(first - second)


def _nonnegative_difference(first: Decimal, second: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        value = first - second
    if value < ZERO:
        return ZERO
    return value.quantize(QUANT)


def _safe_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(QUANT)


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    normalized = value.quantize(QUANT)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must not exceed 1")
    return normalized


def _require_member(field_name: str, value: object, allowed_values: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed_values:
        allowed = ", ".join(allowed_values)
        raise ValueError(f"{field_name} must be one of: {allowed}")


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")


def _normalize_reason_codes(values: tuple[str, ...]) -> tuple[str, ...]:
    if type(values) is not tuple or not values:
        raise ValueError("reason_codes must be a non-empty tuple")
    normalized: list[str] = []
    for value in values:
        if type(value) is not str or value not in REASON_CODES:
            raise ValueError("reason_codes contains an unknown reason code")
        if value not in normalized:
            normalized.append(value)
    return tuple(normalized)


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_sha256(field_name: str, value: object) -> None:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _derived_validation_digest(report: ResearchResolutionOutcomeEvidenceGapReport) -> str:
    payload = json_ready_no_floats(asdict(report))
    if type(payload) is not dict:
        raise ValueError("report payload must be a dict")
    payload.pop("derived_validation_digest", None)
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return sha256(canonical.encode("utf-8")).hexdigest()


__all__ = (
    "DEFAULT_RESEARCH_RESOLUTION_OUTCOME_EVIDENCE_GAP_REPORT_CONFIG_VERSION",
    "RESOLUTION_OUTCOME_EVIDENCE_GAP_STATUSES",
    "ResearchResolutionOutcomeEvidenceGapConfig",
    "ResearchResolutionOutcomeEvidenceGapInputs",
    "ResearchResolutionOutcomeEvidenceGapReport",
    "build_research_resolution_outcome_evidence_gap_report",
    "research_resolution_outcome_evidence_gap_report_payload",
)
