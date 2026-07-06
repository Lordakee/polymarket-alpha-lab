"""Pure paper-only outcome rule clarity scoring for strategy candidates."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, fields, is_dataclass
from decimal import Decimal


__all__ = (
    "StrategyCandidateOutcomeRuleClarityConfig",
    "StrategyCandidateOutcomeRuleClarityInput",
    "StrategyCandidateOutcomeRuleClarityScore",
    "score_strategy_candidate_outcome_rule_clarity_v10",
    "strategy_candidate_outcome_rule_clarity_v10_payload",
)


DEFAULT_CONFIG_VERSION = "strategy-candidate-outcome-rule-clarity-v10"
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1")
CLARITY_STATUSES = ("clear", "watch", "unclear")
STATUS_REASON_PREFIX = "strategy_candidate_outcome_rule_clarity_"
VALIDATION_DIGEST_ALGORITHM = (
    "strategy-candidate-outcome-rule-clarity-v10-sha256"
)
HEX_DIGITS = frozenset("0123456789abcdef")
UNSAFE_PAYLOAD_FIELD_FRAGMENTS = (
    "account",
    "api_key",
    "broker",
    "cancel",
    "client",
    "connect",
    "credential",
    "database",
    "db",
    "execute",
    "fetch",
    "network",
    "order",
    "persist",
    "private",
    "request",
    "secret",
    "sign",
    "submit",
    "token",
    "trade",
    "wallet",
    "write",
)
UNSAFE_PAYLOAD_VALUE_FRAGMENTS = (
    "api_key",
    "broker",
    "cancel_order",
    "live_trading",
    "market_order",
    "private-key",
    "private_key",
    "secret",
    "submit_order",
    "token",
    "trade_wallet",
    "wallet",
)


@dataclass(frozen=True)
class StrategyCandidateOutcomeRuleClarityConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    minimum_clear_score: Decimal = Decimal("0.750000")
    minimum_watch_score: Decimal = Decimal("0.500000")
    minimum_source_authority_score: Decimal = Decimal("0.700000")
    minimum_adjudication_dependency_score: Decimal = Decimal("0.700000")
    maximum_ambiguity_count: Decimal = Decimal("4")
    maximum_days_to_resolution: Decimal = Decimal("84.000000")
    measurable_criteria_weight: Decimal = Decimal("0.300000")
    source_authority_weight: Decimal = Decimal("0.250000")
    ambiguity_weight: Decimal = Decimal("0.200000")
    adjudication_dependency_weight: Decimal = Decimal("0.150000")
    time_to_resolution_weight: Decimal = Decimal("0.100000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "minimum_clear_score",
            "minimum_watch_score",
            "minimum_source_authority_score",
            "minimum_adjudication_dependency_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        if self.minimum_watch_score > self.minimum_clear_score:
            raise ValueError(
                "minimum_watch_score must be less than or equal to minimum_clear_score",
            )
        object.__setattr__(
            self,
            "maximum_ambiguity_count",
            _normalize_positive_count(
                "maximum_ambiguity_count",
                self.maximum_ambiguity_count,
            ),
        )
        object.__setattr__(
            self,
            "maximum_days_to_resolution",
            _normalize_positive_decimal(
                "maximum_days_to_resolution",
                self.maximum_days_to_resolution,
            ),
        )
        for field_name in (
            "measurable_criteria_weight",
            "source_authority_weight",
            "ambiguity_weight",
            "adjudication_dependency_weight",
            "time_to_resolution_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        if _weight_sum(self) != ONE:
            raise ValueError("weights must sum to 1.000000")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class StrategyCandidateOutcomeRuleClarityInput:
    candidate_id: str
    market_slug: str
    outcome_name: str
    measurable_criteria_count: Decimal
    required_measurable_criteria_count: Decimal
    source_authority_score: Decimal
    ambiguity_count: Decimal
    adjudication_dependency_score: Decimal
    days_to_resolution: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("candidate_id", "market_slug", "outcome_name"):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "measurable_criteria_count",
            _normalize_nonnegative_count(
                "measurable_criteria_count",
                self.measurable_criteria_count,
            ),
        )
        object.__setattr__(
            self,
            "required_measurable_criteria_count",
            _normalize_positive_count(
                "required_measurable_criteria_count",
                self.required_measurable_criteria_count,
            ),
        )
        object.__setattr__(
            self,
            "ambiguity_count",
            _normalize_nonnegative_count("ambiguity_count", self.ambiguity_count),
        )
        for field_name in (
            "source_authority_score",
            "adjudication_dependency_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "days_to_resolution",
            _normalize_nonnegative_decimal(
                "days_to_resolution",
                self.days_to_resolution,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags("candidate_state", self)


@dataclass(frozen=True)
class StrategyCandidateOutcomeRuleClarityScore:
    config_version: str
    candidate_id: str
    market_slug: str
    outcome_name: str
    clarity_status: str
    measurable_criteria_count: Decimal
    required_measurable_criteria_count: Decimal
    measurable_criteria_score: Decimal
    source_authority_score: Decimal
    ambiguity_count: Decimal
    ambiguity_score: Decimal
    adjudication_dependency_score: Decimal
    days_to_resolution: Decimal
    time_to_resolution_score: Decimal
    outcome_rule_clarity_score: Decimal
    reason_codes: tuple[str, ...]
    validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "config_version",
            "candidate_id",
            "market_slug",
            "outcome_name",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        _require_member("clarity_status", self.clarity_status, CLARITY_STATUSES)
        object.__setattr__(
            self,
            "measurable_criteria_count",
            _normalize_nonnegative_count(
                "measurable_criteria_count",
                self.measurable_criteria_count,
            ),
        )
        object.__setattr__(
            self,
            "required_measurable_criteria_count",
            _normalize_positive_count(
                "required_measurable_criteria_count",
                self.required_measurable_criteria_count,
            ),
        )
        object.__setattr__(
            self,
            "ambiguity_count",
            _normalize_nonnegative_count("ambiguity_count", self.ambiguity_count),
        )
        for field_name in (
            "measurable_criteria_score",
            "source_authority_score",
            "ambiguity_score",
            "adjudication_dependency_score",
            "time_to_resolution_score",
            "outcome_rule_clarity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "days_to_resolution",
            _normalize_nonnegative_decimal(
                "days_to_resolution",
                self.days_to_resolution,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(
            self,
            "validation_digest",
            _require_validation_digest("validation_digest", self.validation_digest),
        )
        _validate_score_consistency(self)
        _validate_score_digest(self)
        _require_hard_flags("score_result", self)


def score_strategy_candidate_outcome_rule_clarity_v10(
    candidate_state: StrategyCandidateOutcomeRuleClarityInput,
    config: StrategyCandidateOutcomeRuleClarityConfig,
) -> StrategyCandidateOutcomeRuleClarityScore:
    """Score one candidate's outcome rule clarity without side effects."""

    _require_exact_type(
        "candidate_state",
        candidate_state,
        StrategyCandidateOutcomeRuleClarityInput,
    )
    _require_exact_type("config", config, StrategyCandidateOutcomeRuleClarityConfig)

    measurable_criteria_score = _capped_ratio_from_counts(
        candidate_state.measurable_criteria_count,
        candidate_state.required_measurable_criteria_count,
    )
    ambiguity_score = _inverse_count_score(
        candidate_state.ambiguity_count,
        config.maximum_ambiguity_count,
    )
    time_to_resolution_score = _inverse_limit_score(
        candidate_state.days_to_resolution,
        config.maximum_days_to_resolution,
    )
    composite_score = _quantize_decimal(
        "outcome_rule_clarity_score",
        (
            measurable_criteria_score * config.measurable_criteria_weight
            + candidate_state.source_authority_score * config.source_authority_weight
            + ambiguity_score * config.ambiguity_weight
            + candidate_state.adjudication_dependency_score
            * config.adjudication_dependency_weight
            + time_to_resolution_score * config.time_to_resolution_weight
        ),
    )
    clarity_status = _clarity_status(composite_score, config)
    blockers = _blocker_reason_codes(candidate_state, config)
    reason_codes = _score_reason_codes(
        clarity_status,
        candidate_state.reason_codes,
        blockers,
    )
    validation_digest = _score_validation_digest(
        config_version=config.config_version,
        candidate_id=candidate_state.candidate_id,
        market_slug=candidate_state.market_slug,
        outcome_name=candidate_state.outcome_name,
        clarity_status=clarity_status,
        measurable_criteria_count=candidate_state.measurable_criteria_count,
        required_measurable_criteria_count=(
            candidate_state.required_measurable_criteria_count
        ),
        measurable_criteria_score=measurable_criteria_score,
        source_authority_score=candidate_state.source_authority_score,
        ambiguity_count=candidate_state.ambiguity_count,
        ambiguity_score=ambiguity_score,
        adjudication_dependency_score=candidate_state.adjudication_dependency_score,
        days_to_resolution=candidate_state.days_to_resolution,
        time_to_resolution_score=time_to_resolution_score,
        outcome_rule_clarity_score=composite_score,
        reason_codes=reason_codes,
    )

    return StrategyCandidateOutcomeRuleClarityScore(
        config_version=config.config_version,
        candidate_id=candidate_state.candidate_id,
        market_slug=candidate_state.market_slug,
        outcome_name=candidate_state.outcome_name,
        clarity_status=clarity_status,
        measurable_criteria_count=candidate_state.measurable_criteria_count,
        required_measurable_criteria_count=(
            candidate_state.required_measurable_criteria_count
        ),
        measurable_criteria_score=measurable_criteria_score,
        source_authority_score=candidate_state.source_authority_score,
        ambiguity_count=candidate_state.ambiguity_count,
        ambiguity_score=ambiguity_score,
        adjudication_dependency_score=candidate_state.adjudication_dependency_score,
        days_to_resolution=candidate_state.days_to_resolution,
        time_to_resolution_score=time_to_resolution_score,
        outcome_rule_clarity_score=composite_score,
        reason_codes=reason_codes,
        validation_digest=validation_digest,
    )


def strategy_candidate_outcome_rule_clarity_v10_payload(
    score_result: StrategyCandidateOutcomeRuleClarityScore,
) -> dict[str, object]:
    if type(score_result) is not StrategyCandidateOutcomeRuleClarityScore:
        raise ValueError(
            "score_result must be a StrategyCandidateOutcomeRuleClarityScore",
        )
    _require_hard_flags("score_result", score_result)
    _validate_score_consistency(score_result)
    _validate_score_digest(score_result)
    _reject_unsafe_payload_surface("score_result", score_result)
    payload = {
        "config_version": score_result.config_version,
        "candidate_id": score_result.candidate_id,
        "market_slug": score_result.market_slug,
        "outcome_name": score_result.outcome_name,
        "clarity_status": score_result.clarity_status,
        "measurable_criteria_count": _decimal_payload(
            score_result.measurable_criteria_count,
        ),
        "required_measurable_criteria_count": _decimal_payload(
            score_result.required_measurable_criteria_count,
        ),
        "measurable_criteria_score": _decimal_payload(
            score_result.measurable_criteria_score,
        ),
        "source_authority_score": _decimal_payload(score_result.source_authority_score),
        "ambiguity_count": _decimal_payload(score_result.ambiguity_count),
        "ambiguity_score": _decimal_payload(score_result.ambiguity_score),
        "adjudication_dependency_score": _decimal_payload(
            score_result.adjudication_dependency_score,
        ),
        "days_to_resolution": _decimal_payload(score_result.days_to_resolution),
        "time_to_resolution_score": _decimal_payload(
            score_result.time_to_resolution_score,
        ),
        "outcome_rule_clarity_score": _decimal_payload(
            score_result.outcome_rule_clarity_score,
        ),
        "validation_digest": score_result.validation_digest,
        "reason_codes": list(score_result.reason_codes),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    _reject_unsafe_payload_surface("outcome rule clarity payload", payload)
    return payload


def _weight_sum(config: StrategyCandidateOutcomeRuleClarityConfig) -> Decimal:
    return _quantize_decimal(
        "weights",
        (
            config.measurable_criteria_weight
            + config.source_authority_weight
            + config.ambiguity_weight
            + config.adjudication_dependency_weight
            + config.time_to_resolution_weight
        ),
    )


def _capped_ratio_from_counts(numerator: Decimal, denominator: Decimal) -> Decimal:
    ratio = _quantize_decimal(
        "ratio",
        numerator / denominator,
    )
    if ratio > ONE:
        return ONE
    return ratio


def _inverse_count_score(value: Decimal, limit: Decimal) -> Decimal:
    if value >= limit:
        return ZERO
    return _quantize_decimal(
        "count_score",
        ONE - (value / limit),
    )


def _inverse_limit_score(value: Decimal, limit: Decimal) -> Decimal:
    if value >= limit:
        return ZERO
    return _quantize_decimal("limit_score", ONE - (value / limit))


def _clarity_status(
    composite_score: Decimal,
    config: StrategyCandidateOutcomeRuleClarityConfig,
) -> str:
    if composite_score >= config.minimum_clear_score:
        return "clear"
    if composite_score >= config.minimum_watch_score:
        return "watch"
    return "unclear"


def _blocker_reason_codes(
    candidate_state: StrategyCandidateOutcomeRuleClarityInput,
    config: StrategyCandidateOutcomeRuleClarityConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if (
        candidate_state.measurable_criteria_count
        < candidate_state.required_measurable_criteria_count
    ):
        reason_codes.append("measurable_criteria_below_required")
    if candidate_state.source_authority_score < config.minimum_source_authority_score:
        reason_codes.append("source_authority_below_minimum")
    if candidate_state.ambiguity_count > config.maximum_ambiguity_count:
        reason_codes.append("ambiguity_count_above_limit")
    if (
        candidate_state.adjudication_dependency_score
        < config.minimum_adjudication_dependency_score
    ):
        reason_codes.append("adjudication_dependency_below_minimum")
    if candidate_state.days_to_resolution > config.maximum_days_to_resolution:
        reason_codes.append("time_to_resolution_above_limit")
    return tuple(reason_codes)


def _score_reason_codes(
    clarity_status: str,
    upstream_reason_codes: tuple[str, ...],
    blocker_reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    generated_reason_codes = blocker_reason_codes
    if not generated_reason_codes:
        generated_reason_codes = ("outcome_rule_clarity_sufficient",)
    reason_codes = [
        f"{STATUS_REASON_PREFIX}{clarity_status}",
        *upstream_reason_codes,
        *generated_reason_codes,
    ]
    return tuple(dict.fromkeys(reason_codes))


def _validate_score_consistency(
    score_result: StrategyCandidateOutcomeRuleClarityScore,
) -> None:
    expected_measurable_criteria_score = _capped_ratio_from_counts(
        score_result.measurable_criteria_count,
        score_result.required_measurable_criteria_count,
    )
    if score_result.measurable_criteria_score != expected_measurable_criteria_score:
        raise ValueError("measurable_criteria_score must match criteria counts")
    expected_reason_code = f"{STATUS_REASON_PREFIX}{score_result.clarity_status}"
    if not score_result.reason_codes or score_result.reason_codes[0] != expected_reason_code:
        raise ValueError("reason_codes must start with clarity_status reason code")


def _validate_score_digest(
    score_result: StrategyCandidateOutcomeRuleClarityScore,
) -> None:
    if score_result.validation_digest != _score_validation_digest(
        config_version=score_result.config_version,
        candidate_id=score_result.candidate_id,
        market_slug=score_result.market_slug,
        outcome_name=score_result.outcome_name,
        clarity_status=score_result.clarity_status,
        measurable_criteria_count=score_result.measurable_criteria_count,
        required_measurable_criteria_count=score_result.required_measurable_criteria_count,
        measurable_criteria_score=score_result.measurable_criteria_score,
        source_authority_score=score_result.source_authority_score,
        ambiguity_count=score_result.ambiguity_count,
        ambiguity_score=score_result.ambiguity_score,
        adjudication_dependency_score=score_result.adjudication_dependency_score,
        days_to_resolution=score_result.days_to_resolution,
        time_to_resolution_score=score_result.time_to_resolution_score,
        outcome_rule_clarity_score=score_result.outcome_rule_clarity_score,
        reason_codes=score_result.reason_codes,
    ):
        raise ValueError("validation_digest must match score_result")


def _score_validation_digest(
    *,
    config_version: str,
    candidate_id: str,
    market_slug: str,
    outcome_name: str,
    clarity_status: str,
    measurable_criteria_count: Decimal,
    required_measurable_criteria_count: Decimal,
    measurable_criteria_score: Decimal,
    source_authority_score: Decimal,
    ambiguity_count: Decimal,
    ambiguity_score: Decimal,
    adjudication_dependency_score: Decimal,
    days_to_resolution: Decimal,
    time_to_resolution_score: Decimal,
    outcome_rule_clarity_score: Decimal,
    reason_codes: tuple[str, ...],
) -> str:
    digest_parts = (
        VALIDATION_DIGEST_ALGORITHM,
        config_version,
        candidate_id,
        market_slug,
        outcome_name,
        clarity_status,
        _decimal_payload(measurable_criteria_count),
        _decimal_payload(required_measurable_criteria_count),
        _decimal_payload(measurable_criteria_score),
        _decimal_payload(source_authority_score),
        _decimal_payload(ambiguity_count),
        _decimal_payload(ambiguity_score),
        _decimal_payload(adjudication_dependency_score),
        _decimal_payload(days_to_resolution),
        _decimal_payload(time_to_resolution_score),
        _decimal_payload(outcome_rule_clarity_score),
        "\x1f".join(reason_codes),
        "paper_only=True",
        "report_only=True",
        "readonly=True",
    )
    return hashlib.sha256("\n".join(digest_parts).encode("utf-8")).hexdigest()


def _require_exact_type(field_name: str, value: object, expected_type: type[object]) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be a {expected_type.__name__}")
    _require_hard_flags(field_name, value)


def _require_member(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> None:
    if type(value) is not str or value not in allowed_values:
        expected = ", ".join(allowed_values)
        raise ValueError(f"{field_name} must be one of: {expected}")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_validation_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a validation digest")
    if len(value) != 64 or any(character not in HEX_DIGITS for character in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")
    return value


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    for reason_code in value:
        _require_canonical_string(field_name, reason_code)
    if len(set(value)) != len(value):
        raise ValueError(f"{field_name} must be unique")
    return value


def _normalize_positive_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_count(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return value.quantize(COUNT_QUANTUM)


def _normalize_probability_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be a probability")
    return normalized


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _quantize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _quantize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value.quantize(QUANTUM)


def _decimal_payload(value: Decimal) -> str:
    return format(value, "f")


def _require_hard_flags(field_name: str, value: object) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, flag_name, None) is not True:
            raise ValueError(f"{flag_name} must be True")


def _reject_unsafe_payload_surface(label: str, payload: object) -> None:
    for key in _iter_payload_keys(payload):
        normalized_key = key.lower()
        if any(fragment in normalized_key for fragment in UNSAFE_PAYLOAD_FIELD_FRAGMENTS):
            raise ValueError(f"unsafe payload surface in {label}: {key}")
    _reject_unsafe_payload_values(label, payload)


def _iter_payload_keys(value: object) -> tuple[str, ...]:
    if is_dataclass(value) and not isinstance(value, type):
        keys: list[str] = []
        for field in fields(value):
            keys.append(field.name)
            keys.extend(_iter_payload_keys(getattr(value, field.name)))
        return tuple(keys)
    if isinstance(value, dict):
        keys = []
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            keys.append(key)
            keys.extend(_iter_payload_keys(item))
        return tuple(keys)
    if isinstance(value, (list, tuple)):
        keys = []
        for item in value:
            keys.extend(_iter_payload_keys(item))
        return tuple(keys)
    return ()


def _reject_unsafe_payload_values(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _reject_unsafe_payload_values(label, getattr(value, field.name))
        return
    if type(value) is str:
        normalized_value = value.lower()
        if any(
            fragment in normalized_value
            for fragment in UNSAFE_PAYLOAD_VALUE_FRAGMENTS
        ):
            raise ValueError(f"unsafe payload value in {label}")
        return
    if isinstance(value, dict):
        for item in value.values():
            _reject_unsafe_payload_values(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_payload_values(label, item)
