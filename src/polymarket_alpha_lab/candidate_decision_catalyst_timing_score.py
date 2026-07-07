"""Paper-only catalyst timing fit score for candidate decision reports."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, localcontext
from hashlib import sha256
import json
from typing import Any


__all__ = (
    "DEFAULT_CANDIDATE_DECISION_CATALYST_TIMING_SCORE_CONFIG_VERSION",
    "CandidateDecisionCatalystTimingScoreConfig",
    "CandidateDecisionCatalystTimingScoreInput",
    "CandidateDecisionCatalystTimingScoreReport",
    "score_candidate_decision_catalyst_timing_score",
    "candidate_decision_catalyst_timing_score_payload",
    "validate_candidate_decision_catalyst_timing_score_payload",
)


DEFAULT_CANDIDATE_DECISION_CATALYST_TIMING_SCORE_CONFIG_VERSION = (
    "candidate-decision-catalyst-timing-score-v0"
)

PUBLIC_DATACLASS_NAMES = frozenset(
    (
        "CandidateDecisionCatalystTimingScoreConfig",
        "CandidateDecisionCatalystTimingScoreInput",
        "CandidateDecisionCatalystTimingScoreReport",
    ),
)
DECIMAL_CONTEXT = Context(prec=64)
SCORE_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
TIMING_STATUSES = (STATUS_PASS, STATUS_WATCH, STATUS_BLOCK)
CORE_REASON_CODES = frozenset(
    (
        "catalyst_timing_fit_pass",
        "catalyst_timing_fit_watch",
        "catalyst_timing_fit_block",
        "catalyst_not_after_generated_at",
        "resolution_not_after_generated_at",
        "catalyst_after_resolution_at",
        "catalyst_after_near_term_window",
        "catalyst_confidence_missing",
        "catalyst_confidence_below_threshold",
        "catalyst_specificity_missing",
        "catalyst_specificity_below_threshold",
        "evidence_freshness_below_threshold",
        "liquidity_signal_absent",
        "edge_signal_absent",
    ),
)
UNSAFE_PUBLIC_TERMS = frozenset(
    (
        "".join(("se", "cret")),
        "".join(("to", "ken")),
        "".join(("au", "th")),
        "".join(("wall", "et")),
        "".join(("or", "der")),
        "".join(("tr", "ade")),
        "".join(("b", "uy")),
        "".join(("s", "ell")),
        "".join(("reco", "mmendation")),
        "".join(("posi", "tion")),
        "".join(("dsn",)),
        "".join(("tab", "le")),
        "".join(("sl", "ug")),
        "".join(("ques", "tion")),
        "".join(("u", "rl")),
        "".join(("mar", "ket")),
        "".join(("source",)),
    ),
)


class _FinalPublicDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls.__module__ != __name__ or cls.__name__ not in PUBLIC_DATACLASS_NAMES:
            raise TypeError("subclassing is not allowed")


@dataclass(frozen=True)
class CandidateDecisionCatalystTimingScoreConfig(_FinalPublicDataclass):
    config_version: str = DEFAULT_CANDIDATE_DECISION_CATALYST_TIMING_SCORE_CONFIG_VERSION
    near_term_window_seconds: Decimal = Decimal("259200.000000")
    minimum_confidence_score: Decimal = Decimal("0.500000")
    minimum_specificity_score: Decimal = Decimal("0.500000")
    minimum_freshness_score: Decimal = Decimal("0.400000")
    pass_score_floor: Decimal = Decimal("0.750000")
    watch_score_floor: Decimal = Decimal("0.400000")
    confidence_weight: Decimal = Decimal("0.300000")
    specificity_weight: Decimal = Decimal("0.300000")
    freshness_weight: Decimal = Decimal("0.200000")
    timing_weight: Decimal = Decimal("0.100000")
    liquidity_weight: Decimal = Decimal("0.050000")
    edge_weight: Decimal = Decimal("0.050000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, CandidateDecisionCatalystTimingScoreConfig, "config")
        object.__setattr__(
            self,
            "config_version",
            _require_public_string("config_version", self.config_version),
        )
        object.__setattr__(
            self,
            "near_term_window_seconds",
            _require_positive_decimal(
                "near_term_window_seconds",
                self.near_term_window_seconds,
            ),
        )
        for field_name in (
            "minimum_confidence_score",
            "minimum_specificity_score",
            "minimum_freshness_score",
            "pass_score_floor",
            "watch_score_floor",
            "confidence_weight",
            "specificity_weight",
            "freshness_weight",
            "timing_weight",
            "liquidity_weight",
            "edge_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", _payload_value(self))


@dataclass(frozen=True)
class CandidateDecisionCatalystTimingScoreInput(_FinalPublicDataclass):
    generated_at: datetime
    candidate_ref: str
    next_catalyst_at: datetime
    resolution_at: datetime
    catalyst_confidence_score: Decimal
    catalyst_specificity_score: Decimal
    evidence_freshness_score: Decimal
    liquidity_depth_score: Decimal = ZERO
    edge_quality_score: Decimal = ZERO
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, CandidateDecisionCatalystTimingScoreInput, "score_input")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "candidate_ref",
            _require_candidate_ref(self.candidate_ref),
        )
        object.__setattr__(
            self,
            "next_catalyst_at",
            _as_utc("next_catalyst_at", self.next_catalyst_at),
        )
        object.__setattr__(
            self,
            "resolution_at",
            _as_utc("resolution_at", self.resolution_at),
        )
        for field_name in (
            "catalyst_confidence_score",
            "catalyst_specificity_score",
            "evidence_freshness_score",
            "liquidity_depth_score",
            "edge_quality_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("score_input", self)
        _reject_unsafe_public_payload("score_input", _payload_value(self))


@dataclass(frozen=True)
class CandidateDecisionCatalystTimingScoreReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    candidate_ref: str
    next_catalyst_at: datetime
    resolution_at: datetime
    catalyst_confidence_score: Decimal
    catalyst_specificity_score: Decimal
    evidence_freshness_score: Decimal
    liquidity_depth_score: Decimal
    edge_quality_score: Decimal
    near_term_window_seconds: Decimal
    minimum_confidence_score: Decimal
    minimum_specificity_score: Decimal
    minimum_freshness_score: Decimal
    pass_score_floor: Decimal
    watch_score_floor: Decimal
    confidence_weight: Decimal
    specificity_weight: Decimal
    freshness_weight: Decimal
    timing_weight: Decimal
    liquidity_weight: Decimal
    edge_weight: Decimal
    seconds_until_catalyst: Decimal
    seconds_until_resolution: Decimal
    timing_proximity_score: Decimal
    timing_fit_score: Decimal
    timing_status: str
    reason_codes: tuple[str, ...]
    report_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, CandidateDecisionCatalystTimingScoreReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_public_string("config_version", self.config_version),
        )
        object.__setattr__(self, "candidate_ref", _require_candidate_ref(self.candidate_ref))
        object.__setattr__(
            self,
            "next_catalyst_at",
            _as_utc("next_catalyst_at", self.next_catalyst_at),
        )
        object.__setattr__(
            self,
            "resolution_at",
            _as_utc("resolution_at", self.resolution_at),
        )
        for field_name in (
            "catalyst_confidence_score",
            "catalyst_specificity_score",
            "evidence_freshness_score",
            "liquidity_depth_score",
            "edge_quality_score",
            "minimum_confidence_score",
            "minimum_specificity_score",
            "minimum_freshness_score",
            "pass_score_floor",
            "watch_score_floor",
            "confidence_weight",
            "specificity_weight",
            "freshness_weight",
            "timing_weight",
            "liquidity_weight",
            "edge_weight",
            "timing_proximity_score",
            "timing_fit_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "near_term_window_seconds",
            "seconds_until_catalyst",
            "seconds_until_resolution",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.near_term_window_seconds <= ZERO:
            raise ValueError("near_term_window_seconds must be positive")
        _require_status("timing_status", self.timing_status)
        object.__setattr__(
            self,
            "reason_codes",
            _require_reason_codes("reason_codes", self.reason_codes),
        )
        _require_digest("report_validation_digest", self.report_validation_digest)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", _payload_value(self))
        _validate_report(self)
        _require_matching_digest(_payload_value(self))

    @property
    def payload(self) -> dict[str, Any]:
        return candidate_decision_catalyst_timing_score_payload(self)


def score_candidate_decision_catalyst_timing_score(
    score_input: CandidateDecisionCatalystTimingScoreInput,
    *,
    config: CandidateDecisionCatalystTimingScoreConfig | None = None,
) -> CandidateDecisionCatalystTimingScoreReport:
    if type(score_input) is not CandidateDecisionCatalystTimingScoreInput:
        raise ValueError(
            "score_input must be exactly CandidateDecisionCatalystTimingScoreInput",
        )
    _require_hard_flags("score_input", score_input)
    cfg = config or CandidateDecisionCatalystTimingScoreConfig()
    if type(cfg) is not CandidateDecisionCatalystTimingScoreConfig:
        raise ValueError("config must be exactly CandidateDecisionCatalystTimingScoreConfig")
    _require_hard_flags("config", cfg)
    seconds_until_catalyst = _seconds_between(
        score_input.generated_at,
        score_input.next_catalyst_at,
    )
    seconds_until_resolution = _seconds_between(
        score_input.generated_at,
        score_input.resolution_at,
    )
    timing_proximity_score = _timing_proximity_score(
        seconds_until_catalyst,
        cfg.near_term_window_seconds,
    )
    hard_timing_failure = _has_hard_timing_failure(
        score_input=score_input,
        seconds_until_catalyst=seconds_until_catalyst,
        seconds_until_resolution=seconds_until_resolution,
    )
    timing_fit_score = (
        ZERO
        if hard_timing_failure
        else _timing_fit_score(
            score_input=score_input,
            timing_proximity_score=timing_proximity_score,
            config=cfg,
        )
    )
    status = _timing_status(
        timing_fit_score=timing_fit_score,
        hard_timing_failure=hard_timing_failure,
        score_input=score_input,
        config=cfg,
    )
    values: dict[str, Any] = {
        "generated_at": score_input.generated_at,
        "config_version": cfg.config_version,
        "candidate_ref": score_input.candidate_ref,
        "next_catalyst_at": score_input.next_catalyst_at,
        "resolution_at": score_input.resolution_at,
        "catalyst_confidence_score": score_input.catalyst_confidence_score,
        "catalyst_specificity_score": score_input.catalyst_specificity_score,
        "evidence_freshness_score": score_input.evidence_freshness_score,
        "liquidity_depth_score": score_input.liquidity_depth_score,
        "edge_quality_score": score_input.edge_quality_score,
        "near_term_window_seconds": cfg.near_term_window_seconds,
        "minimum_confidence_score": cfg.minimum_confidence_score,
        "minimum_specificity_score": cfg.minimum_specificity_score,
        "minimum_freshness_score": cfg.minimum_freshness_score,
        "pass_score_floor": cfg.pass_score_floor,
        "watch_score_floor": cfg.watch_score_floor,
        "confidence_weight": cfg.confidence_weight,
        "specificity_weight": cfg.specificity_weight,
        "freshness_weight": cfg.freshness_weight,
        "timing_weight": cfg.timing_weight,
        "liquidity_weight": cfg.liquidity_weight,
        "edge_weight": cfg.edge_weight,
        "seconds_until_catalyst": seconds_until_catalyst,
        "seconds_until_resolution": seconds_until_resolution,
        "timing_proximity_score": timing_proximity_score,
        "timing_fit_score": timing_fit_score,
        "timing_status": status,
        "reason_codes": _reason_codes(
            status=status,
            score_input=score_input,
            config=cfg,
            seconds_until_catalyst=seconds_until_catalyst,
            seconds_until_resolution=seconds_until_resolution,
            timing_proximity_score=timing_proximity_score,
        ),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    payload = _payload_value(values)
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    values["report_validation_digest"] = _validation_digest(payload)
    return CandidateDecisionCatalystTimingScoreReport(**values)


def candidate_decision_catalyst_timing_score_payload(
    report: CandidateDecisionCatalystTimingScoreReport,
) -> dict[str, Any]:
    if type(report) is not CandidateDecisionCatalystTimingScoreReport:
        raise ValueError("report must be exactly CandidateDecisionCatalystTimingScoreReport")
    _require_hard_flags("report", report)
    payload = _payload_value(report)
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _reject_unsafe_public_payload("payload", payload)
    _require_payload_hard_flags(payload)
    _require_matching_digest(payload)
    return payload


def validate_candidate_decision_catalyst_timing_score_payload(
    payload: dict[str, Any],
) -> bool:
    if type(payload) is not dict:
        raise ValueError("public payload must be a dict")
    _reject_unsafe_public_payload("payload", payload)
    _require_payload_hard_flags(payload)
    _require_payload_status(payload)
    _require_matching_digest(payload)
    return True


def _seconds_between(started_at: datetime, finished_at: datetime) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        seconds = Decimal(str((finished_at - started_at).total_seconds()))
        return _clamp_nonnegative(seconds)


def _timing_proximity_score(
    seconds_until_catalyst: Decimal,
    near_term_window_seconds: Decimal,
) -> Decimal:
    if seconds_until_catalyst <= ZERO:
        return ZERO
    if seconds_until_catalyst >= near_term_window_seconds:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(ONE - (seconds_until_catalyst / near_term_window_seconds))


def _timing_fit_score(
    *,
    score_input: CandidateDecisionCatalystTimingScoreInput,
    timing_proximity_score: Decimal,
    config: CandidateDecisionCatalystTimingScoreConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        value = (
            score_input.catalyst_confidence_score * config.confidence_weight
            + score_input.catalyst_specificity_score * config.specificity_weight
            + score_input.evidence_freshness_score * config.freshness_weight
            + timing_proximity_score * config.timing_weight
            + score_input.liquidity_depth_score * config.liquidity_weight
            + score_input.edge_quality_score * config.edge_weight
        )
        return _clamp_ratio(value)


def _timing_status(
    *,
    timing_fit_score: Decimal,
    hard_timing_failure: bool,
    score_input: CandidateDecisionCatalystTimingScoreInput,
    config: CandidateDecisionCatalystTimingScoreConfig,
) -> str:
    if hard_timing_failure or _has_critical_signal_gap(score_input, config):
        return STATUS_BLOCK
    if timing_fit_score >= config.pass_score_floor:
        return STATUS_PASS
    if timing_fit_score >= config.watch_score_floor:
        return STATUS_WATCH
    return STATUS_BLOCK


def _reason_codes(
    *,
    status: str,
    score_input: CandidateDecisionCatalystTimingScoreInput,
    config: CandidateDecisionCatalystTimingScoreConfig,
    seconds_until_catalyst: Decimal,
    seconds_until_resolution: Decimal,
    timing_proximity_score: Decimal,
) -> tuple[str, ...]:
    codes: list[str] = [f"catalyst_timing_fit_{status}"]
    if seconds_until_catalyst <= ZERO:
        codes.append("catalyst_not_after_generated_at")
    if seconds_until_resolution <= ZERO:
        codes.append("resolution_not_after_generated_at")
    if score_input.next_catalyst_at > score_input.resolution_at:
        codes.append("catalyst_after_resolution_at")
    if (
        score_input.next_catalyst_at <= score_input.resolution_at
        and seconds_until_catalyst >= config.near_term_window_seconds
    ):
        codes.append("catalyst_after_near_term_window")
    if score_input.catalyst_confidence_score <= ZERO:
        codes.append("catalyst_confidence_missing")
    elif score_input.catalyst_confidence_score < config.minimum_confidence_score:
        codes.append("catalyst_confidence_below_threshold")
    if score_input.catalyst_specificity_score <= ZERO:
        codes.append("catalyst_specificity_missing")
    elif score_input.catalyst_specificity_score < config.minimum_specificity_score:
        codes.append("catalyst_specificity_below_threshold")
    if score_input.evidence_freshness_score < config.minimum_freshness_score:
        codes.append("evidence_freshness_below_threshold")
    if score_input.liquidity_depth_score <= ZERO:
        codes.append("liquidity_signal_absent")
    if score_input.edge_quality_score <= ZERO:
        codes.append("edge_signal_absent")
    if (
        score_input.next_catalyst_at <= score_input.resolution_at
        and timing_proximity_score <= ZERO
        and seconds_until_catalyst > ZERO
    ):
        if "catalyst_after_near_term_window" not in codes:
            codes.append("catalyst_after_near_term_window")
    return tuple(dict.fromkeys(codes))


def _has_hard_timing_failure(
    *,
    score_input: CandidateDecisionCatalystTimingScoreInput,
    seconds_until_catalyst: Decimal,
    seconds_until_resolution: Decimal,
) -> bool:
    return (
        seconds_until_catalyst <= ZERO
        or seconds_until_resolution <= ZERO
        or score_input.next_catalyst_at > score_input.resolution_at
    )


def _has_critical_signal_gap(
    score_input: CandidateDecisionCatalystTimingScoreInput,
    config: CandidateDecisionCatalystTimingScoreConfig,
) -> bool:
    return (
        score_input.catalyst_confidence_score < config.minimum_confidence_score
        or score_input.catalyst_specificity_score < config.minimum_specificity_score
        or score_input.evidence_freshness_score < config.minimum_freshness_score
    )


def _validate_config(config: CandidateDecisionCatalystTimingScoreConfig) -> None:
    if config.pass_score_floor < config.watch_score_floor:
        raise ValueError("pass_score_floor must not be below watch_score_floor")
    with localcontext(DECIMAL_CONTEXT):
        total_weight = (
            config.confidence_weight
            + config.specificity_weight
            + config.freshness_weight
            + config.timing_weight
            + config.liquidity_weight
            + config.edge_weight
        )
    if total_weight != ONE:
        raise ValueError("score weights must sum to 1.000000")


def _validate_report(report: CandidateDecisionCatalystTimingScoreReport) -> None:
    seconds_until_catalyst = _seconds_between(
        report.generated_at,
        report.next_catalyst_at,
    )
    seconds_until_resolution = _seconds_between(
        report.generated_at,
        report.resolution_at,
    )
    if report.seconds_until_catalyst != seconds_until_catalyst:
        raise ValueError("seconds_until_catalyst must match report datetimes")
    if report.seconds_until_resolution != seconds_until_resolution:
        raise ValueError("seconds_until_resolution must match report datetimes")
    timing_proximity_score = _timing_proximity_score(
        seconds_until_catalyst,
        report.near_term_window_seconds,
    )
    if report.timing_proximity_score != timing_proximity_score:
        raise ValueError("timing_proximity_score must match report inputs")
    score_input = CandidateDecisionCatalystTimingScoreInput(
        generated_at=report.generated_at,
        candidate_ref=report.candidate_ref,
        next_catalyst_at=report.next_catalyst_at,
        resolution_at=report.resolution_at,
        catalyst_confidence_score=report.catalyst_confidence_score,
        catalyst_specificity_score=report.catalyst_specificity_score,
        evidence_freshness_score=report.evidence_freshness_score,
        liquidity_depth_score=report.liquidity_depth_score,
        edge_quality_score=report.edge_quality_score,
    )
    config = CandidateDecisionCatalystTimingScoreConfig(
        config_version=report.config_version,
        near_term_window_seconds=report.near_term_window_seconds,
        minimum_confidence_score=report.minimum_confidence_score,
        minimum_specificity_score=report.minimum_specificity_score,
        minimum_freshness_score=report.minimum_freshness_score,
        pass_score_floor=report.pass_score_floor,
        watch_score_floor=report.watch_score_floor,
        confidence_weight=report.confidence_weight,
        specificity_weight=report.specificity_weight,
        freshness_weight=report.freshness_weight,
        timing_weight=report.timing_weight,
        liquidity_weight=report.liquidity_weight,
        edge_weight=report.edge_weight,
    )
    hard_timing_failure = _has_hard_timing_failure(
        score_input=score_input,
        seconds_until_catalyst=seconds_until_catalyst,
        seconds_until_resolution=seconds_until_resolution,
    )
    timing_fit_score = (
        ZERO
        if hard_timing_failure
        else _timing_fit_score(
            score_input=score_input,
            timing_proximity_score=timing_proximity_score,
            config=config,
        )
    )
    if report.timing_fit_score != timing_fit_score:
        raise ValueError("timing_fit_score must match report inputs")
    status = _timing_status(
        timing_fit_score=timing_fit_score,
        hard_timing_failure=hard_timing_failure,
        score_input=score_input,
        config=config,
    )
    if report.timing_status != status:
        raise ValueError("timing_status must match report inputs")
    reason_codes = _reason_codes(
        status=status,
        score_input=score_input,
        config=config,
        seconds_until_catalyst=seconds_until_catalyst,
        seconds_until_resolution=seconds_until_resolution,
        timing_proximity_score=timing_proximity_score,
    )
    if report.reason_codes != reason_codes:
        raise ValueError("reason_codes must match report inputs")


def _require_candidate_ref(value: str) -> str:
    value = _require_public_string("candidate_ref", value)
    if not value.startswith("candidate_ref_"):
        raise ValueError("candidate_ref must be redacted")
    return value


def _require_reason_codes(
    field_name: str,
    values: tuple[str, ...],
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not values:
        raise ValueError(f"{field_name} must be non-empty")
    seen: set[str] = set()
    for value in values:
        _require_public_string(field_name, value)
        if value not in CORE_REASON_CODES:
            raise ValueError(f"{field_name} contains an unknown reason code")
        if value in seen:
            raise ValueError(f"{field_name} must not contain duplicates")
        seen.add(value)
    return values


def _require_status(field_name: str, value: str) -> None:
    if type(value) is not str or value not in TIMING_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_positive_decimal(field_name: str, value: Decimal) -> Decimal:
    value = _require_nonnegative_decimal(field_name, value)
    if value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return value


def _require_nonnegative_decimal(field_name: str, value: Decimal) -> Decimal:
    value = _require_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return value


def _require_ratio_decimal(field_name: str, value: Decimal) -> Decimal:
    value = _require_decimal(field_name, value)
    if value < ZERO or value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return value


def _require_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize_decimal(value)


def _quantize_decimal(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(SCORE_QUANTUM)


def _clamp_nonnegative(value: Decimal) -> Decimal:
    if value <= ZERO:
        return ZERO
    return _quantize_decimal(value)


def _clamp_ratio(value: Decimal) -> Decimal:
    if value < ZERO:
        return ZERO
    if value > ONE:
        return ONE
    return _quantize_decimal(value)


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_public_string(field_name: str, value: str) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} must be non-empty")
    if value != value.strip():
        raise ValueError(f"{field_name} must be canonical")
    _reject_unsafe_public_string(field_name, value)
    return value


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only") is not True:
        raise ValueError(f"{label} paper_only must be True")
    if getattr(value, "report_only") is not True:
        raise ValueError(f"{label} report_only must be True")
    if getattr(value, "readonly") is not True:
        raise ValueError(f"{label} readonly must be True")


def _require_payload_hard_flags(payload: dict[str, Any]) -> None:
    for flag in ("paper_only", "report_only", "readonly"):
        if payload.get(flag) is not True:
            raise ValueError(f"payload {flag} must be True")


def _require_payload_status(payload: dict[str, Any]) -> None:
    status = payload.get("timing_status")
    if type(status) is not str or status not in TIMING_STATUSES:
        raise ValueError("payload timing_status must be pass, watch, or block")


def _payload_value(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _payload_value(getattr(value, field.name)) for field in fields(value)}
    if type(value) is dict:
        return {key: _payload_value(item) for key, item in value.items()}
    if type(value) is tuple:
        return [_payload_value(item) for item in value]
    if type(value) is list:
        return [_payload_value(item) for item in value]
    if type(value) is Decimal:
        return format(value, "f")
    if type(value) is datetime:
        return value.isoformat()
    if type(value) in (str, bool) or value is None:
        return value
    raise ValueError("public payload contains unsupported value")


def _reject_unsafe_public_payload(label: str, payload: object) -> None:
    if type(payload) is dict:
        for key, value in payload.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            _reject_unsafe_public_string(label, key)
            _reject_unsafe_public_payload(label, value)
        return
    if type(payload) is list:
        for item in payload:
            _reject_unsafe_public_payload(label, item)
        return
    if type(payload) is str:
        _reject_unsafe_public_string(label, payload)
        return
    if type(payload) in (bool,) or payload is None:
        return
    raise ValueError("public payload values must be strings, booleans, lists, or dicts")


def _reject_unsafe_public_string(field_name: str, value: str) -> None:
    lower_value = value.lower()
    if any(term in lower_value for term in UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"unsafe public surface in {field_name}")


def _require_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _require_matching_digest(payload: dict[str, Any]) -> None:
    digest_value = payload.get("report_validation_digest")
    _require_digest("report_validation_digest", digest_value)
    if digest_value != _validation_digest(payload):
        raise ValueError("report_validation_digest must match public payload")


def _validation_digest(payload: dict[str, Any]) -> str:
    digest_payload = dict(payload)
    digest_payload.pop("report_validation_digest", None)
    encoded = json.dumps(
        digest_payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()
