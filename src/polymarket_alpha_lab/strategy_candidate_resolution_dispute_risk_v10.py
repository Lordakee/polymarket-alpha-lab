"""Pure paper/report/readonly candidate resolution dispute risk v10."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from decimal import Decimal
import hashlib
from typing import Any


SCORE_QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")

MAX_RESOLUTION_MINUTES = Decimal("1440.000000")
URGENT_RESOLUTION_MINUTES = Decimal("60.000000")
NEAR_RESOLUTION_MINUTES = Decimal("360.000000")
RESOLUTION_PRESSURE_RANGE_MINUTES = Decimal("1380.000000")

AMBIGUOUS_RULE_CAP = Decimal("5.000000")
CONFLICTING_EVIDENCE_CAP = Decimal("4.000000")
RESOLUTION_DEPENDENCY_CAP = Decimal("5.000000")

HEAVY_AMBIGUOUS_RULE_COUNT = Decimal("5.000000")
HEAVY_CONFLICTING_EVIDENCE_COUNT = Decimal("4.000000")
HEAVY_RESOLUTION_DEPENDENCY_COUNT = Decimal("5.000000")
WEAK_SOURCE_AUTHORITY_SCORE = Decimal("0.750000")

WEIGHT_AMBIGUOUS_RULE = Decimal("0.055433")
WEIGHT_SOURCE_AUTHORITY = Decimal("0.316306")
WEIGHT_CONFLICTING_EVIDENCE = Decimal("0.428261")
WEIGHT_RESOLUTION_DEPENDENCY = Decimal("0.050000")
WEIGHT_TIME_PRESSURE = Decimal("0.150000")

ELEVATED_DISPUTE_RISK_THRESHOLD = Decimal("0.500000")
BLOCKED_DISPUTE_RISK_THRESHOLD = Decimal("0.750000")

DISPUTE_RISK_STATUSES = ("clear", "watch", "elevated", "blocked")
RECOMMENDED_ACTIONS = (
    "continue_monitoring",
    "refresh_resolution_evidence",
    "escalate_manual_review",
    "block_candidate_until_resolved",
)
REQUIRED_FOLLOWUPS = (
    "clarify_ambiguous_resolution_rules",
    "refresh_authoritative_resolution_source",
    "reconcile_conflicting_resolution_evidence",
    "confirm_resolution_dependencies",
    "complete_dispute_review_before_resolution",
)
REASON_CODES = (
    "dispute_status_clear",
    "dispute_status_watch",
    "dispute_status_elevated",
    "dispute_status_blocked",
    "dispute_risk_clear",
    "ambiguous_resolution_rules",
    "ambiguous_resolution_rules_heavy",
    "weak_source_authority",
    "conflicting_resolution_evidence",
    "conflicting_evidence_heavy",
    "resolution_dependencies_present",
    "resolution_dependencies_heavy",
    "resolution_window_sufficient",
    "resolution_window_near",
    "resolution_window_imminent",
)
UNSAFE_SURFACE_FIELD_FRAGMENTS = (
    "api_key",
    "authorization",
    "exchange_mutation",
    "private_key",
)
UNSAFE_SURFACE_FIELD_TOKENS = (
    "auth",
    "balance",
    "cancel",
    "credential",
    "order",
    "secret",
    "sign",
    "token",
    "trade",
    "wallet",
)


@dataclass(frozen=True)
class StrategyCandidateResolutionDisputeRiskV10Input:
    candidate_id: str
    market_slug: str
    outcome_name: str
    ambiguous_rule_count: Decimal
    source_authority_score: Decimal
    conflicting_evidence_count: Decimal
    resolution_dependency_count: Decimal
    time_to_resolution_minutes: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not StrategyCandidateResolutionDisputeRiskV10Input:
            raise ValueError("candidate must be a StrategyCandidateResolutionDisputeRiskV10Input")
        _require_identifier("candidate_id", self.candidate_id)
        _require_identifier("market_slug", self.market_slug)
        _require_canonical_string("outcome_name", self.outcome_name)
        for field_name in (
            "ambiguous_rule_count",
            "conflicting_evidence_count",
            "resolution_dependency_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_whole_nonnegative_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        object.__setattr__(
            self,
            "source_authority_score",
            _normalize_probability(
                "source_authority_score",
                self.source_authority_score,
            ),
        )
        object.__setattr__(
            self,
            "time_to_resolution_minutes",
            _normalize_nonnegative_decimal(
                "time_to_resolution_minutes",
                self.time_to_resolution_minutes,
            ),
        )
        _reject_unsafe_surface_fields("candidate resolution dispute risk input", self)
        _require_hard_flags(self)


@dataclass(frozen=True)
class StrategyCandidateResolutionDisputeRiskV10Result:
    candidate_id: str
    market_slug: str
    outcome_name: str
    ambiguous_rule_count: Decimal
    source_authority_score: Decimal
    conflicting_evidence_count: Decimal
    resolution_dependency_count: Decimal
    time_to_resolution_minutes: Decimal
    ambiguous_rule_pressure: Decimal
    source_authority_weakness: Decimal
    conflicting_evidence_pressure: Decimal
    resolution_dependency_pressure: Decimal
    time_pressure: Decimal
    dispute_risk_score: Decimal
    dispute_risk_status: str
    recommended_action: str
    required_followups: tuple[str, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not StrategyCandidateResolutionDisputeRiskV10Result:
            raise ValueError("result must be a StrategyCandidateResolutionDisputeRiskV10Result")
        _require_identifier("candidate_id", self.candidate_id)
        _require_identifier("market_slug", self.market_slug)
        _require_canonical_string("outcome_name", self.outcome_name)
        for field_name in (
            "ambiguous_rule_count",
            "conflicting_evidence_count",
            "resolution_dependency_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_whole_nonnegative_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        object.__setattr__(
            self,
            "source_authority_score",
            _normalize_probability(
                "source_authority_score",
                self.source_authority_score,
            ),
        )
        object.__setattr__(
            self,
            "time_to_resolution_minutes",
            _normalize_nonnegative_decimal(
                "time_to_resolution_minutes",
                self.time_to_resolution_minutes,
            ),
        )
        for field_name in (
            "ambiguous_rule_pressure",
            "source_authority_weakness",
            "conflicting_evidence_pressure",
            "resolution_dependency_pressure",
            "time_pressure",
            "dispute_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_choice("dispute_risk_status", self.dispute_risk_status, DISPUTE_RISK_STATUSES)
        _require_choice("recommended_action", self.recommended_action, RECOMMENDED_ACTIONS)
        object.__setattr__(
            self,
            "required_followups",
            _normalize_string_tuple(
                "required_followups",
                self.required_followups,
                REQUIRED_FOLLOWUPS,
                allow_empty=True,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_string_tuple(
                "reason_codes",
                self.reason_codes,
                REASON_CODES,
                allow_empty=False,
            ),
        )
        _require_hard_flags(self)
        _reject_unsafe_surface_fields("candidate resolution dispute risk result", self)
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                "derived_validation_digest",
                _derived_validation_digest(self),
            )
        else:
            object.__setattr__(
                self,
                "derived_validation_digest",
                _normalize_derived_validation_digest(
                    "derived_validation_digest",
                    self.derived_validation_digest,
                ),
            )
        _validate_result(self)

    @property
    def payload(self) -> dict[str, Any]:
        payload = asdict(self)
        _reject_unsafe_surface_fields("candidate resolution dispute risk payload", payload)
        return _payload_value(payload)


def build_strategy_candidate_resolution_dispute_risk_v10(
    candidate: StrategyCandidateResolutionDisputeRiskV10Input,
) -> StrategyCandidateResolutionDisputeRiskV10Result:
    if type(candidate) is not StrategyCandidateResolutionDisputeRiskV10Input:
        raise ValueError("candidate must be a StrategyCandidateResolutionDisputeRiskV10Input")
    _reject_unsafe_surface_fields("candidate resolution dispute risk input", candidate)
    _require_hard_flags(candidate)

    ambiguous_rule_pressure = _ratio_capped(
        candidate.ambiguous_rule_count,
        AMBIGUOUS_RULE_CAP,
    )
    source_authority_weakness = _q(ONE - candidate.source_authority_score)
    conflicting_evidence_pressure = _ratio_capped(
        candidate.conflicting_evidence_count,
        CONFLICTING_EVIDENCE_CAP,
    )
    resolution_dependency_pressure = _ratio_capped(
        candidate.resolution_dependency_count,
        RESOLUTION_DEPENDENCY_CAP,
    )
    time_pressure = _time_pressure(candidate.time_to_resolution_minutes)
    dispute_risk_score = _dispute_risk_score(
        ambiguous_rule_pressure=ambiguous_rule_pressure,
        source_authority_weakness=source_authority_weakness,
        conflicting_evidence_pressure=conflicting_evidence_pressure,
        resolution_dependency_pressure=resolution_dependency_pressure,
        time_pressure=time_pressure,
    )
    dispute_risk_status = _dispute_risk_status(dispute_risk_score)

    return StrategyCandidateResolutionDisputeRiskV10Result(
        candidate_id=candidate.candidate_id,
        market_slug=candidate.market_slug,
        outcome_name=candidate.outcome_name,
        ambiguous_rule_count=candidate.ambiguous_rule_count,
        source_authority_score=candidate.source_authority_score,
        conflicting_evidence_count=candidate.conflicting_evidence_count,
        resolution_dependency_count=candidate.resolution_dependency_count,
        time_to_resolution_minutes=candidate.time_to_resolution_minutes,
        ambiguous_rule_pressure=ambiguous_rule_pressure,
        source_authority_weakness=source_authority_weakness,
        conflicting_evidence_pressure=conflicting_evidence_pressure,
        resolution_dependency_pressure=resolution_dependency_pressure,
        time_pressure=time_pressure,
        dispute_risk_score=dispute_risk_score,
        dispute_risk_status=dispute_risk_status,
        recommended_action=_recommended_action(dispute_risk_status),
        required_followups=_required_followups(candidate),
        reason_codes=_reason_codes(candidate, dispute_risk_status),
    )


def strategy_candidate_resolution_dispute_risk_v10_payload(
    result: StrategyCandidateResolutionDisputeRiskV10Result,
) -> dict[str, Any]:
    if type(result) is not StrategyCandidateResolutionDisputeRiskV10Result:
        raise ValueError("result must be a StrategyCandidateResolutionDisputeRiskV10Result")
    _reject_unsafe_surface_fields("candidate resolution dispute risk result", result)
    _require_hard_flags(result)
    return result.payload


def _time_pressure(time_to_resolution_minutes: Decimal) -> Decimal:
    if time_to_resolution_minutes <= URGENT_RESOLUTION_MINUTES:
        return ONE
    if time_to_resolution_minutes >= MAX_RESOLUTION_MINUTES:
        return ZERO
    return _ratio_capped(
        MAX_RESOLUTION_MINUTES - time_to_resolution_minutes,
        RESOLUTION_PRESSURE_RANGE_MINUTES,
    )


def _dispute_risk_score(
    *,
    ambiguous_rule_pressure: Decimal,
    source_authority_weakness: Decimal,
    conflicting_evidence_pressure: Decimal,
    resolution_dependency_pressure: Decimal,
    time_pressure: Decimal,
) -> Decimal:
    return _q(
        (ambiguous_rule_pressure * WEIGHT_AMBIGUOUS_RULE)
        + (source_authority_weakness * WEIGHT_SOURCE_AUTHORITY)
        + (conflicting_evidence_pressure * WEIGHT_CONFLICTING_EVIDENCE)
        + (resolution_dependency_pressure * WEIGHT_RESOLUTION_DEPENDENCY)
        + (time_pressure * WEIGHT_TIME_PRESSURE),
    )


def _dispute_risk_status(dispute_risk_score: Decimal) -> str:
    if dispute_risk_score >= BLOCKED_DISPUTE_RISK_THRESHOLD:
        return "blocked"
    if dispute_risk_score >= ELEVATED_DISPUTE_RISK_THRESHOLD:
        return "elevated"
    if dispute_risk_score > ZERO:
        return "watch"
    return "clear"


def _recommended_action(dispute_risk_status: str) -> str:
    if dispute_risk_status == "clear":
        return "continue_monitoring"
    if dispute_risk_status == "watch":
        return "refresh_resolution_evidence"
    if dispute_risk_status == "elevated":
        return "escalate_manual_review"
    if dispute_risk_status == "blocked":
        return "block_candidate_until_resolved"
    raise ValueError("dispute_risk_status must be supported")


def _required_followups(
    candidate: StrategyCandidateResolutionDisputeRiskV10Input,
) -> tuple[str, ...]:
    values: list[str] = []
    if candidate.ambiguous_rule_count > ZERO:
        values.append("clarify_ambiguous_resolution_rules")
    if candidate.source_authority_score < WEAK_SOURCE_AUTHORITY_SCORE:
        values.append("refresh_authoritative_resolution_source")
    if candidate.conflicting_evidence_count > ZERO:
        values.append("reconcile_conflicting_resolution_evidence")
    if candidate.resolution_dependency_count > ZERO:
        values.append("confirm_resolution_dependencies")
    if candidate.time_to_resolution_minutes <= Decimal("180.000000"):
        values.append("complete_dispute_review_before_resolution")
    return tuple(values)


def _reason_codes(
    candidate: StrategyCandidateResolutionDisputeRiskV10Input,
    dispute_risk_status: str,
) -> tuple[str, ...]:
    values: list[str] = [f"dispute_status_{dispute_risk_status}"]
    if dispute_risk_status == "clear":
        values.append("dispute_risk_clear")
    if candidate.ambiguous_rule_count >= HEAVY_AMBIGUOUS_RULE_COUNT:
        values.append("ambiguous_resolution_rules_heavy")
    elif candidate.ambiguous_rule_count > ZERO:
        values.append("ambiguous_resolution_rules")
    if candidate.source_authority_score < WEAK_SOURCE_AUTHORITY_SCORE:
        values.append("weak_source_authority")
    if candidate.conflicting_evidence_count >= HEAVY_CONFLICTING_EVIDENCE_COUNT:
        values.append("conflicting_evidence_heavy")
    elif candidate.conflicting_evidence_count > ZERO:
        values.append("conflicting_resolution_evidence")
    if candidate.resolution_dependency_count >= HEAVY_RESOLUTION_DEPENDENCY_COUNT:
        values.append("resolution_dependencies_heavy")
    elif candidate.resolution_dependency_count > ZERO:
        values.append("resolution_dependencies_present")
    values.append(_time_reason_code(candidate.time_to_resolution_minutes))
    return tuple(values)


def _time_reason_code(time_to_resolution_minutes: Decimal) -> str:
    if time_to_resolution_minutes <= URGENT_RESOLUTION_MINUTES:
        return "resolution_window_imminent"
    if time_to_resolution_minutes <= NEAR_RESOLUTION_MINUTES:
        return "resolution_window_near"
    return "resolution_window_sufficient"


def _validate_result(result: StrategyCandidateResolutionDisputeRiskV10Result) -> None:
    expected_ambiguous_rule_pressure = _ratio_capped(
        result.ambiguous_rule_count,
        AMBIGUOUS_RULE_CAP,
    )
    expected_source_authority_weakness = _q(ONE - result.source_authority_score)
    expected_conflicting_evidence_pressure = _ratio_capped(
        result.conflicting_evidence_count,
        CONFLICTING_EVIDENCE_CAP,
    )
    expected_resolution_dependency_pressure = _ratio_capped(
        result.resolution_dependency_count,
        RESOLUTION_DEPENDENCY_CAP,
    )
    expected_time_pressure = _time_pressure(result.time_to_resolution_minutes)
    expected_dispute_risk_score = _dispute_risk_score(
        ambiguous_rule_pressure=expected_ambiguous_rule_pressure,
        source_authority_weakness=expected_source_authority_weakness,
        conflicting_evidence_pressure=expected_conflicting_evidence_pressure,
        resolution_dependency_pressure=expected_resolution_dependency_pressure,
        time_pressure=expected_time_pressure,
    )
    expected_dispute_risk_status = _dispute_risk_status(expected_dispute_risk_score)
    expected_candidate = StrategyCandidateResolutionDisputeRiskV10Input(
        candidate_id=result.candidate_id,
        market_slug=result.market_slug,
        outcome_name=result.outcome_name,
        ambiguous_rule_count=result.ambiguous_rule_count,
        source_authority_score=result.source_authority_score,
        conflicting_evidence_count=result.conflicting_evidence_count,
        resolution_dependency_count=result.resolution_dependency_count,
        time_to_resolution_minutes=result.time_to_resolution_minutes,
    )
    if result.ambiguous_rule_pressure != expected_ambiguous_rule_pressure:
        raise ValueError("ambiguous_rule_pressure must match candidate fields")
    if result.source_authority_weakness != expected_source_authority_weakness:
        raise ValueError("source_authority_weakness must match candidate fields")
    if result.conflicting_evidence_pressure != expected_conflicting_evidence_pressure:
        raise ValueError("conflicting_evidence_pressure must match candidate fields")
    if result.resolution_dependency_pressure != expected_resolution_dependency_pressure:
        raise ValueError("resolution_dependency_pressure must match candidate fields")
    if result.time_pressure != expected_time_pressure:
        raise ValueError("time_pressure must match candidate fields")
    if result.dispute_risk_score != expected_dispute_risk_score:
        raise ValueError("dispute_risk_score must match candidate fields")
    if result.dispute_risk_status != expected_dispute_risk_status:
        raise ValueError("dispute_risk_status must match dispute_risk_score")
    if result.recommended_action != _recommended_action(expected_dispute_risk_status):
        raise ValueError("recommended_action must match dispute_risk_status")
    if result.required_followups != _required_followups(expected_candidate):
        raise ValueError("required_followups must match candidate fields")
    if result.reason_codes != _reason_codes(expected_candidate, expected_dispute_risk_status):
        raise ValueError("reason_codes must match candidate fields")
    if result.derived_validation_digest != _derived_validation_digest(result):
        raise ValueError("derived_validation_digest must match result fields")


def _ratio_capped(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= ZERO:
        raise ValueError("denominator must be positive")
    ratio = numerator / denominator
    if ratio >= ONE:
        return ONE
    if ratio <= ZERO:
        return ZERO
    return _q(ratio)


def _normalize_whole_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized % ONE != ZERO:
        raise ValueError(f"{field_name} must be a whole Decimal")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_probability(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0.000000 and 1.000000")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _q(value)


def _normalize_derived_validation_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or value.lower() != value:
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a lowercase sha256 digest") from exc
    return value


def _normalize_string_tuple(
    field_name: str,
    values: object,
    allowed_values: tuple[str, ...],
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError(f"{field_name} must contain canonical strings")
    try:
        items = tuple(values)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError(f"{field_name} must contain canonical strings") from exc
    if not allow_empty and not items:
        raise ValueError(f"{field_name} must not be empty")
    if len(set(items)) != len(items):
        raise ValueError(f"{field_name} must not contain duplicates")
    for item in items:
        _require_choice(field_name, item, allowed_values)
    return items


def _require_choice(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> None:
    _require_canonical_string(field_name, value)
    if value not in allowed_values:
        raise ValueError(f"{field_name} must be one of {allowed_values!r}")


def _require_identifier(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if any(character.isspace() for character in value):
        raise ValueError(f"{field_name} must not contain whitespace")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a non-empty canonical string")


def _require_hard_flags(value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True")


def _reject_unsafe_surface_fields(label: str, payload: object) -> None:
    for key in _payload_keys(payload):
        if _is_unsafe_surface_key(key):
            raise ValueError(f"unsafe live surface field in {label}: {key}")


def _is_unsafe_surface_key(key: str) -> bool:
    normalized_key = key.lower()
    if any(fragment in normalized_key for fragment in UNSAFE_SURFACE_FIELD_FRAGMENTS):
        return True
    tokens = _surface_key_tokens(normalized_key)
    return any(token in tokens for token in UNSAFE_SURFACE_FIELD_TOKENS)


def _surface_key_tokens(key: str) -> tuple[str, ...]:
    tokens: list[str] = []
    current: list[str] = []
    for character in key:
        if ("a" <= character <= "z") or ("0" <= character <= "9"):
            current.append(character)
            continue
        if current:
            tokens.append("".join(current))
            current = []
    if current:
        tokens.append("".join(current))
    return tuple(tokens)


def _payload_keys(value: object) -> tuple[str, ...]:
    if hasattr(value, "__dataclass_fields__") and not isinstance(value, type):
        return _payload_keys(asdict(value))
    if isinstance(value, dict):
        keys: list[str] = []
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            keys.append(key)
            keys.extend(_payload_keys(item))
        return tuple(keys)
    if isinstance(value, (list, tuple)):
        keys = []
        for item in value:
            keys.extend(_payload_keys(item))
        return tuple(keys)
    return ()


def _payload_value(value: Any) -> Any:
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    if isinstance(value, list):
        return [_payload_value(item) for item in value]
    if isinstance(value, dict):
        _reject_unsafe_surface_fields("candidate resolution dispute risk payload", value)
        return {str(key): _payload_value(item) for key, item in value.items()}
    return value


def _derived_validation_digest(result: StrategyCandidateResolutionDisputeRiskV10Result) -> str:
    digest_material = "|".join(
        (
            f"candidate_id={result.candidate_id}",
            f"market_slug={result.market_slug}",
            f"outcome_name={result.outcome_name}",
            f"ambiguous_rule_count={result.ambiguous_rule_count}",
            f"source_authority_score={result.source_authority_score}",
            f"conflicting_evidence_count={result.conflicting_evidence_count}",
            f"resolution_dependency_count={result.resolution_dependency_count}",
            f"time_to_resolution_minutes={result.time_to_resolution_minutes}",
            f"ambiguous_rule_pressure={result.ambiguous_rule_pressure}",
            f"source_authority_weakness={result.source_authority_weakness}",
            f"conflicting_evidence_pressure={result.conflicting_evidence_pressure}",
            f"resolution_dependency_pressure={result.resolution_dependency_pressure}",
            f"time_pressure={result.time_pressure}",
            f"dispute_risk_score={result.dispute_risk_score}",
            f"dispute_risk_status={result.dispute_risk_status}",
            f"recommended_action={result.recommended_action}",
            f"required_followups={_digest_tuple(result.required_followups)}",
            f"reason_codes={_digest_tuple(result.reason_codes)}",
            f"paper_only={result.paper_only}",
            f"report_only={result.report_only}",
            f"readonly={result.readonly}",
        ),
    )
    return hashlib.sha256(digest_material.encode("utf-8")).hexdigest()


def _digest_tuple(values: tuple[str, ...]) -> str:
    return ",".join(values)


def _q(value: Decimal) -> Decimal:
    return value.quantize(SCORE_QUANT)


__all__ = (
    "DISPUTE_RISK_STATUSES",
    "RECOMMENDED_ACTIONS",
    "REASON_CODES",
    "REQUIRED_FOLLOWUPS",
    "StrategyCandidateResolutionDisputeRiskV10Input",
    "StrategyCandidateResolutionDisputeRiskV10Result",
    "build_strategy_candidate_resolution_dispute_risk_v10",
    "strategy_candidate_resolution_dispute_risk_v10_payload",
)
