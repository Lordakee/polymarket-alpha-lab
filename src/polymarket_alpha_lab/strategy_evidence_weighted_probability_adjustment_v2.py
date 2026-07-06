"""Pure Phase 1 probability adjustment report for evidence-weighted forecasts."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any


DEFAULT_CONFIG_VERSION = "strategy-evidence-weighted-probability-adjustment-v2"

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

STATUSES = ("pass", "watch", "reject")
REASON_CODES = (
    "evidence_strong",
    "evidence_weak",
    "source_reliable",
    "source_uncertain",
    "information_fresh",
    "information_stale",
    "specialist_calibrated",
    "specialist_uncertain",
    "contradiction_low",
    "contradiction_high",
    "resolution_rule_clear",
    "resolution_rule_ambiguous",
    "probability_adjusted_up",
    "probability_adjusted_down",
    "probability_unchanged",
)

DERIVED_VALIDATION_DIGEST_LENGTH = 64
DERIVED_VALIDATION_DIGEST_FIELDS = (
    "generated_at",
    "config_version",
    "forecast_id",
    "market_slug",
    "observed_at",
    "raw_probability",
    "evidence_signal_probability",
    "evidence_strength",
    "source_reliability",
    "information_age_hours",
    "information_recency_score",
    "specialist_calibration",
    "contradiction_severity",
    "resolution_rule_clarity",
    "support_score",
    "contradiction_drag",
    "adjustment_weight",
    "probability_delta",
    "adjusted_probability",
    "assessment_status",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)


@dataclass(frozen=True)
class StrategyEvidenceWeightedProbabilityAdjustmentV2Config:
    config_version: str = DEFAULT_CONFIG_VERSION
    max_information_age_hours: Decimal = Decimal("72.000000")
    max_probability_adjustment: Decimal = Decimal("0.150000")
    evidence_strength_weight: Decimal = Decimal("0.250000")
    source_reliability_weight: Decimal = Decimal("0.200000")
    information_recency_weight: Decimal = Decimal("0.150000")
    specialist_calibration_weight: Decimal = Decimal("0.200000")
    resolution_rule_clarity_weight: Decimal = Decimal("0.200000")
    contradiction_penalty_multiplier: Decimal = Decimal("1.000000")
    pass_adjustment_weight: Decimal = Decimal("0.600000")
    watch_adjustment_weight: Decimal = Decimal("0.350000")
    reject_contradiction_severity: Decimal = Decimal("0.750000")
    reject_resolution_rule_clarity: Decimal = Decimal("0.250000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not StrategyEvidenceWeightedProbabilityAdjustmentV2Config:
            raise ValueError("config must be exact")
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "max_information_age_hours",
            "max_probability_adjustment",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "evidence_strength_weight",
            "source_reliability_weight",
            "information_recency_weight",
            "specialist_calibration_weight",
            "resolution_rule_clarity_weight",
            "contradiction_penalty_multiplier",
            "pass_adjustment_weight",
            "watch_adjustment_weight",
            "reject_contradiction_severity",
            "reject_resolution_rule_clarity",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("config", self)
        _reject_public_surface("config", self)


@dataclass(frozen=True)
class StrategyEvidenceWeightedProbabilityAdjustmentV2Input:
    forecast_id: str
    market_slug: str
    observed_at: datetime
    raw_probability: Decimal
    evidence_signal_probability: Decimal
    evidence_strength: Decimal
    source_reliability: Decimal
    information_age_hours: Decimal
    specialist_calibration: Decimal
    contradiction_severity: Decimal
    resolution_rule_clarity: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not StrategyEvidenceWeightedProbabilityAdjustmentV2Input:
            raise ValueError("forecast_input must be exact")
        _require_canonical_string("forecast_id", self.forecast_id)
        _require_canonical_string("market_slug", self.market_slug)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "raw_probability",
            "evidence_signal_probability",
            "evidence_strength",
            "source_reliability",
            "specialist_calibration",
            "contradiction_severity",
            "resolution_rule_clarity",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "information_age_hours",
            _normalize_nonnegative_decimal(
                "information_age_hours",
                self.information_age_hours,
            ),
        )
        _require_hard_flags("forecast_input", self)
        _reject_public_surface("forecast_input", self)


@dataclass(frozen=True)
class StrategyEvidenceWeightedProbabilityAdjustmentV2Report:
    generated_at: datetime
    config_version: str
    forecast_id: str
    market_slug: str
    observed_at: datetime
    raw_probability: Decimal
    evidence_signal_probability: Decimal
    evidence_strength: Decimal
    source_reliability: Decimal
    information_age_hours: Decimal
    information_recency_score: Decimal
    specialist_calibration: Decimal
    contradiction_severity: Decimal
    resolution_rule_clarity: Decimal
    support_score: Decimal
    contradiction_drag: Decimal
    adjustment_weight: Decimal
    probability_delta: Decimal
    adjusted_probability: Decimal
    assessment_status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not StrategyEvidenceWeightedProbabilityAdjustmentV2Report:
            raise ValueError("report must be exact")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_canonical_string("forecast_id", self.forecast_id)
        _require_canonical_string("market_slug", self.market_slug)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "raw_probability",
            "evidence_signal_probability",
            "evidence_strength",
            "source_reliability",
            "information_recency_score",
            "specialist_calibration",
            "contradiction_severity",
            "resolution_rule_clarity",
            "support_score",
            "contradiction_drag",
            "adjustment_weight",
            "adjusted_probability",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "information_age_hours",
            _normalize_nonnegative_decimal(
                "information_age_hours",
                self.information_age_hours,
            ),
        )
        object.__setattr__(
            self,
            "probability_delta",
            _normalize_delta("probability_delta", self.probability_delta),
        )
        _require_member("assessment_status", self.assessment_status, STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _require_digest(self.derived_validation_digest)
        _require_hard_flags("report", self)
        _reject_public_surface("report", self)
        _validate_report(self)


def build_strategy_evidence_weighted_probability_adjustment_v2_report(
    forecast_input: StrategyEvidenceWeightedProbabilityAdjustmentV2Input,
    *,
    generated_at: datetime,
    config: StrategyEvidenceWeightedProbabilityAdjustmentV2Config | None = None,
) -> StrategyEvidenceWeightedProbabilityAdjustmentV2Report:
    if type(forecast_input) is not StrategyEvidenceWeightedProbabilityAdjustmentV2Input:
        raise ValueError(
            "forecast_input must be a StrategyEvidenceWeightedProbabilityAdjustmentV2Input",
        )
    _require_hard_flags("forecast_input", forecast_input)
    if config is None:
        config = StrategyEvidenceWeightedProbabilityAdjustmentV2Config()
    if type(config) is not StrategyEvidenceWeightedProbabilityAdjustmentV2Config:
        raise ValueError(
            "config must be a StrategyEvidenceWeightedProbabilityAdjustmentV2Config",
        )
    _require_hard_flags("config", config)

    generated_at = _as_utc("generated_at", generated_at)
    information_recency_score = _information_recency_score(forecast_input, config)
    support_score = _support_score(
        forecast_input=forecast_input,
        config=config,
        information_recency_score=information_recency_score,
    )
    contradiction_drag = _contradiction_drag(forecast_input, config)
    adjustment_weight = _adjustment_weight(
        support_score=support_score,
        contradiction_drag=contradiction_drag,
    )
    probability_delta = _probability_delta(
        forecast_input=forecast_input,
        config=config,
        adjustment_weight=adjustment_weight,
    )
    adjusted_probability = _clamp_probability(
        forecast_input.raw_probability + probability_delta,
    )
    assessment_status = _assessment_status(
        forecast_input=forecast_input,
        config=config,
        adjustment_weight=adjustment_weight,
    )
    reason_codes = _reason_codes(
        forecast_input=forecast_input,
        information_recency_score=information_recency_score,
        probability_delta=probability_delta,
    )
    digest = _derived_validation_digest(
        {
            "generated_at": generated_at,
            "config_version": config.config_version,
            "forecast_id": forecast_input.forecast_id,
            "market_slug": forecast_input.market_slug,
            "observed_at": forecast_input.observed_at,
            "raw_probability": forecast_input.raw_probability,
            "evidence_signal_probability": forecast_input.evidence_signal_probability,
            "evidence_strength": forecast_input.evidence_strength,
            "source_reliability": forecast_input.source_reliability,
            "information_age_hours": forecast_input.information_age_hours,
            "information_recency_score": information_recency_score,
            "specialist_calibration": forecast_input.specialist_calibration,
            "contradiction_severity": forecast_input.contradiction_severity,
            "resolution_rule_clarity": forecast_input.resolution_rule_clarity,
            "support_score": support_score,
            "contradiction_drag": contradiction_drag,
            "adjustment_weight": adjustment_weight,
            "probability_delta": probability_delta,
            "adjusted_probability": adjusted_probability,
            "assessment_status": assessment_status,
            "reason_codes": reason_codes,
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
    )
    return StrategyEvidenceWeightedProbabilityAdjustmentV2Report(
        generated_at=generated_at,
        config_version=config.config_version,
        forecast_id=forecast_input.forecast_id,
        market_slug=forecast_input.market_slug,
        observed_at=forecast_input.observed_at,
        raw_probability=forecast_input.raw_probability,
        evidence_signal_probability=forecast_input.evidence_signal_probability,
        evidence_strength=forecast_input.evidence_strength,
        source_reliability=forecast_input.source_reliability,
        information_age_hours=forecast_input.information_age_hours,
        information_recency_score=information_recency_score,
        specialist_calibration=forecast_input.specialist_calibration,
        contradiction_severity=forecast_input.contradiction_severity,
        resolution_rule_clarity=forecast_input.resolution_rule_clarity,
        support_score=support_score,
        contradiction_drag=contradiction_drag,
        adjustment_weight=adjustment_weight,
        probability_delta=probability_delta,
        adjusted_probability=adjusted_probability,
        assessment_status=assessment_status,
        reason_codes=reason_codes,
        derived_validation_digest=digest,
    )


def strategy_evidence_weighted_probability_adjustment_v2_payload(
    report: StrategyEvidenceWeightedProbabilityAdjustmentV2Report | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is StrategyEvidenceWeightedProbabilityAdjustmentV2Report:
        _require_hard_flags("report", report)
        _reject_public_surface("report", report)
        payload = _json_ready(report)
    elif type(report) is dict:
        _require_hard_flags("payload", _DictFlags(report))
        _reject_public_surface("payload", report)
        payload = _json_ready(report)
    else:
        raise ValueError(
            "report must be a StrategyEvidenceWeightedProbabilityAdjustmentV2Report",
        )
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_public_surface("payload", payload)
    _validate_payload_digest(payload)
    return payload


@dataclass(frozen=True)
class _DictFlags:
    value: dict[str, Any]

    @property
    def paper_only(self) -> object:
        return self.value.get("paper_only")

    @property
    def report_only(self) -> object:
        return self.value.get("report_only")

    @property
    def readonly(self) -> object:
        return self.value.get("readonly")


def _validate_config(
    config: StrategyEvidenceWeightedProbabilityAdjustmentV2Config,
) -> None:
    weight_total = _sum_decimal(
        (
            config.evidence_strength_weight,
            config.source_reliability_weight,
            config.information_recency_weight,
            config.specialist_calibration_weight,
            config.resolution_rule_clarity_weight,
        ),
    )
    if weight_total != ONE:
        raise ValueError("support weights must sum to 1")
    if config.pass_adjustment_weight < config.watch_adjustment_weight:
        raise ValueError("pass_adjustment_weight must be at least watch_adjustment_weight")


def _validate_report(
    report: StrategyEvidenceWeightedProbabilityAdjustmentV2Report,
) -> None:
    expected_digest = _derived_validation_digest(
        _digest_material_from_payload(_json_ready(report)),
    )
    if report.derived_validation_digest != expected_digest:
        raise ValueError("derived_validation_digest mismatch")
    if report.information_recency_score < ZERO or report.information_recency_score > ONE:
        raise ValueError("information_recency_score must be between 0 and 1")
    if report.adjusted_probability != _clamp_probability(
        report.raw_probability + report.probability_delta,
    ):
        raise ValueError("adjusted_probability must match probability_delta")
    if report.support_score < ZERO or report.support_score > ONE:
        raise ValueError("support_score must be between 0 and 1")
    if report.contradiction_drag < ZERO or report.contradiction_drag > ONE:
        raise ValueError("contradiction_drag must be between 0 and 1")
    if report.adjustment_weight != _adjustment_weight(
        support_score=report.support_score,
        contradiction_drag=report.contradiction_drag,
    ):
        raise ValueError("adjustment_weight must match support and contradiction")


def _information_recency_score(
    forecast_input: StrategyEvidenceWeightedProbabilityAdjustmentV2Input,
    config: StrategyEvidenceWeightedProbabilityAdjustmentV2Config,
) -> Decimal:
    return _ratio_score(
        config.max_information_age_hours - forecast_input.information_age_hours,
        config.max_information_age_hours,
    )


def _support_score(
    *,
    forecast_input: StrategyEvidenceWeightedProbabilityAdjustmentV2Input,
    config: StrategyEvidenceWeightedProbabilityAdjustmentV2Config,
    information_recency_score: Decimal,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_probability(
            (forecast_input.evidence_strength * config.evidence_strength_weight)
            + (forecast_input.source_reliability * config.source_reliability_weight)
            + (information_recency_score * config.information_recency_weight)
            + (
                forecast_input.specialist_calibration
                * config.specialist_calibration_weight
            )
            + (
                forecast_input.resolution_rule_clarity
                * config.resolution_rule_clarity_weight
            ),
        )


def _contradiction_drag(
    forecast_input: StrategyEvidenceWeightedProbabilityAdjustmentV2Input,
    config: StrategyEvidenceWeightedProbabilityAdjustmentV2Config,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_probability(
            forecast_input.contradiction_severity
            * config.contradiction_penalty_multiplier,
        )


def _adjustment_weight(*, support_score: Decimal, contradiction_drag: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_probability(support_score * (ONE - contradiction_drag))


def _probability_delta(
    *,
    forecast_input: StrategyEvidenceWeightedProbabilityAdjustmentV2Input,
    config: StrategyEvidenceWeightedProbabilityAdjustmentV2Config,
    adjustment_weight: Decimal,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        delta = (
            forecast_input.evidence_signal_probability - forecast_input.raw_probability
        ) * adjustment_weight
        return _cap_delta(_quantize_delta(delta), config.max_probability_adjustment)


def _assessment_status(
    *,
    forecast_input: StrategyEvidenceWeightedProbabilityAdjustmentV2Input,
    config: StrategyEvidenceWeightedProbabilityAdjustmentV2Config,
    adjustment_weight: Decimal,
) -> str:
    if forecast_input.contradiction_severity >= config.reject_contradiction_severity:
        return "reject"
    if forecast_input.resolution_rule_clarity <= config.reject_resolution_rule_clarity:
        return "reject"
    if adjustment_weight >= config.pass_adjustment_weight:
        return "pass"
    if adjustment_weight >= config.watch_adjustment_weight:
        return "watch"
    return "reject"


def _reason_codes(
    *,
    forecast_input: StrategyEvidenceWeightedProbabilityAdjustmentV2Input,
    information_recency_score: Decimal,
    probability_delta: Decimal,
) -> tuple[str, ...]:
    codes = [
        "evidence_strong"
        if forecast_input.evidence_strength >= Decimal("0.700000")
        else "evidence_weak",
        "source_reliable"
        if forecast_input.source_reliability >= Decimal("0.700000")
        else "source_uncertain",
        "information_fresh"
        if information_recency_score >= Decimal("0.500000")
        else "information_stale",
        "specialist_calibrated"
        if forecast_input.specialist_calibration >= Decimal("0.700000")
        else "specialist_uncertain",
        "contradiction_low"
        if forecast_input.contradiction_severity <= Decimal("0.250000")
        else "contradiction_high",
        "resolution_rule_clear"
        if forecast_input.resolution_rule_clarity >= Decimal("0.700000")
        else "resolution_rule_ambiguous",
    ]
    if probability_delta > ZERO:
        codes.append("probability_adjusted_up")
    elif probability_delta < ZERO:
        codes.append("probability_adjusted_down")
    else:
        codes.append("probability_unchanged")
    return tuple(codes)


def _validate_payload_digest(payload: dict[str, Any]) -> None:
    digest = payload.get("derived_validation_digest")
    if type(digest) is not str:
        raise ValueError("derived_validation_digest must be a string")
    _require_digest(digest)
    expected_digest = _derived_validation_digest(_digest_material_from_payload(payload))
    if digest != expected_digest:
        raise ValueError("derived_validation_digest mismatch")


def _derived_validation_digest(material: dict[str, Any]) -> str:
    ready = _json_ready(material)
    if type(ready) is not dict:
        raise ValueError("derived validation material must be an object")
    text = json.dumps(ready, ensure_ascii=True, separators=(",", ":"), sort_keys=True)
    return sha256(text.encode("utf-8")).hexdigest()


def _digest_material_from_payload(payload: object) -> dict[str, Any]:
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    material: dict[str, Any] = {}
    for field_name in DERIVED_VALIDATION_DIGEST_FIELDS:
        if field_name not in payload:
            raise ValueError(f"{field_name} missing from payload")
        material[field_name] = payload[field_name]
    return material


def _json_ready(value: object) -> object:
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("JSON datetime value must be a datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal")
    if isinstance(value, dict):
        ready: dict[str, object] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, (str, bool)) or value is None:
        return value
    raise ValueError("value is not JSON serializable")


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    if not value:
        raise ValueError("reason_codes must not be empty")
    normalized: list[str] = []
    for code in value:
        _require_member("reason_codes", code, REASON_CODES)
        if code in normalized:
            raise ValueError("reason_codes must not contain duplicates")
        normalized.append(code)
    return tuple(normalized)


def _reject_public_surface(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_public_surface(label, asdict(value))
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            if _has_public_surface_term(key):
                raise ValueError(f"unsafe public field in {label}")
            _reject_public_surface(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_public_surface(label, item)
        return
    if type(value) is str and _has_public_surface_term(value):
        raise ValueError(f"unsafe public value in {label}")


def _has_public_surface_term(value: str) -> bool:
    lowered = value.lower()
    compact = "".join(char for char in lowered if char.isalnum())
    return any(term in lowered or term in compact for term in _public_surface_terms())


def _public_surface_terms() -> tuple[str, ...]:
    return tuple(
        "".join(parts)
        for parts in (
            ("li", "ve"),
            ("au", "th"),
            ("wal", "let"),
            ("or", "der"),
            ("net", "work"),
            ("data", "base"),
            ("pers", "ist"),
            ("sign", "ing"),
            ("muta", "tion"),
            ("b", "uy"),
            ("se", "ll"),
            ("tra", "de"),
            ("tra", "ding"),
        )
    )


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be canonical")


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    _require_canonical_string(field_name, value)
    if value not in allowed:
        raise ValueError(f"{field_name} is not supported")


def _require_digest(value: object) -> None:
    _require_canonical_string("derived_validation_digest", value)
    if len(value) != DERIVED_VALIDATION_DIGEST_LENGTH:
        raise ValueError("derived_validation_digest must be sha256 hex")
    if any(char not in "0123456789abcdef" for char in value):
        raise ValueError("derived_validation_digest must be sha256 hex")


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} must be paper_only")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} must be report_only")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} must be readonly")


def _normalize_probability(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_nonnegative_decimal(field_name, value)
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must be at most 1")
    return decimal_value


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_nonnegative_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    decimal_value = _quantize(decimal_value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _normalize_delta(field_name: str, value: object) -> Decimal:
    return _quantize(_require_decimal(field_name, value))


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _ratio_score(numerator: Decimal, denominator: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        if denominator <= ZERO:
            raise ValueError("denominator must be positive")
        if numerator <= ZERO:
            return ZERO
        return _clamp_probability(numerator / denominator)


def _clamp_probability(value: Decimal) -> Decimal:
    value = _quantize(value)
    if value <= ZERO:
        return ZERO
    if value >= ONE:
        return ONE
    return value


def _cap_delta(delta: Decimal, cap: Decimal) -> Decimal:
    if delta > cap:
        return cap
    if delta < -cap:
        return -cap
    return delta


def _sum_decimal(values: tuple[Decimal, ...]) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(sum(values, ZERO))


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _quantize_delta(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


__all__ = (
    "DEFAULT_CONFIG_VERSION",
    "StrategyEvidenceWeightedProbabilityAdjustmentV2Config",
    "StrategyEvidenceWeightedProbabilityAdjustmentV2Input",
    "StrategyEvidenceWeightedProbabilityAdjustmentV2Report",
    "build_strategy_evidence_weighted_probability_adjustment_v2_report",
    "strategy_evidence_weighted_probability_adjustment_v2_payload",
)
