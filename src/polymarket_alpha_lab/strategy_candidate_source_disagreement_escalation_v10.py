"""Pure candidate source disagreement escalation v10 reducer."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    UNSAFE_SURFACE_FIELD_FRAGMENTS,
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


DEFAULT_CONFIG_VERSION = "strategy-candidate-source-disagreement-escalation-v10"
RATIO_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
THREE = Decimal("3")
MAX_RECENCY_GAP_HOURS = Decimal("24.000000")
URGENT_RESOLUTION_HOURS = Decimal("6.000000")
NEAR_RESOLUTION_HOURS = Decimal("48.000000")
CONTRADICTION_WEIGHT = Decimal("0.300000")
RELIABILITY_SPREAD_WEIGHT = Decimal("0.200000")
RECENCY_GAP_WEIGHT = Decimal("0.150000")
RESOLUTION_URGENCY_WEIGHT = Decimal("0.200000")
MARKET_MOVE_WEIGHT = Decimal("0.150000")
WATCH_PRIORITY_SCORE = Decimal("0.100000")
HIGH_PRIORITY_SCORE = Decimal("0.350000")
CRITICAL_PRIORITY_SCORE = Decimal("0.600000")
HIGH_CONTRADICTION_RATE = Decimal("0.300000")
HIGH_RELIABILITY_SPREAD = Decimal("0.200000")
WATCH_MARKET_MOVE = Decimal("0.050000")
MATERIAL_MARKET_MOVE = Decimal("0.100000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
VALIDATION_DIGEST_ALGORITHM = "sha256"
HEX_DIGITS = frozenset("0123456789abcdef")

ESCALATION_STATUSES = ("clear", "watch", "high", "critical")
ESCALATION_ACTIONS = (
    "keep_research_signal",
    "queue_source_recheck",
    "escalate_research_lead",
    "pause_candidate_signal",
)


@dataclass(frozen=True)
class StrategyCandidateSourceDisagreementEscalationV10Config:
    config_version: str = DEFAULT_CONFIG_VERSION
    watch_priority_score: Decimal = WATCH_PRIORITY_SCORE
    high_priority_score: Decimal = HIGH_PRIORITY_SCORE
    critical_priority_score: Decimal = CRITICAL_PRIORITY_SCORE
    high_contradiction_rate: Decimal = HIGH_CONTRADICTION_RATE
    high_reliability_spread: Decimal = HIGH_RELIABILITY_SPREAD
    watch_market_move: Decimal = WATCH_MARKET_MOVE
    material_market_move: Decimal = MATERIAL_MARKET_MOVE
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            "config",
            self,
            StrategyCandidateSourceDisagreementEscalationV10Config,
        )
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "watch_priority_score",
            "high_priority_score",
            "critical_priority_score",
            "high_contradiction_rate",
            "high_reliability_spread",
            "watch_market_move",
            "material_market_move",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        if self.watch_priority_score > self.high_priority_score:
            raise ValueError(
                "watch_priority_score must be less than or equal to high_priority_score",
            )
        if self.high_priority_score > self.critical_priority_score:
            raise ValueError(
                "high_priority_score must be less than or equal to "
                "critical_priority_score",
            )
        if self.watch_market_move > self.material_market_move:
            raise ValueError(
                "watch_market_move must be less than or equal to material_market_move",
            )
        _reject_unsafe_public_payload("config", self)
        _require_safety_flags("config", self)


@dataclass(frozen=True)
class StrategyCandidateSourceDisagreementEscalationV10Input:
    candidate_id: str
    market_slug: str
    contradiction_rate: Decimal
    source_reliability_spread: Decimal
    recency_gap_hours: Decimal
    time_to_resolution_hours: Decimal
    market_move_since_disagreement: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            "input",
            self,
            StrategyCandidateSourceDisagreementEscalationV10Input,
        )
        _require_canonical_string("candidate_id", self.candidate_id)
        _require_canonical_string("market_slug", self.market_slug)
        for field_name in (
            "contradiction_rate",
            "source_reliability_spread",
            "market_move_since_disagreement",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in ("recency_gap_hours", "time_to_resolution_hours"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _reject_unsafe_public_payload("input", self)
        _require_safety_flags("input", self)


@dataclass(frozen=True)
class StrategyCandidateSourceDisagreementEscalationV10Result:
    config_version: str
    candidate_id: str
    market_slug: str
    contradiction_rate: Decimal
    source_reliability_spread: Decimal
    recency_gap_hours: Decimal
    recency_gap_pressure: Decimal
    time_to_resolution_hours: Decimal
    resolution_urgency: Decimal
    market_move_since_disagreement: Decimal
    escalation_priority_score: Decimal
    escalation_status: str
    escalation_action: str
    reason_codes: tuple[str, ...]
    validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            "result",
            self,
            StrategyCandidateSourceDisagreementEscalationV10Result,
        )
        _require_canonical_string("config_version", self.config_version)
        _require_canonical_string("candidate_id", self.candidate_id)
        _require_canonical_string("market_slug", self.market_slug)
        for field_name in (
            "contradiction_rate",
            "source_reliability_spread",
            "recency_gap_pressure",
            "resolution_urgency",
            "market_move_since_disagreement",
            "escalation_priority_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in ("recency_gap_hours", "time_to_resolution_hours"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_member("escalation_status", self.escalation_status, ESCALATION_STATUSES)
        _require_member("escalation_action", self.escalation_action, ESCALATION_ACTIONS)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, require_nonempty=True),
        )
        object.__setattr__(
            self,
            "validation_digest",
            _require_validation_digest("validation_digest", self.validation_digest),
        )
        _validate_result(self)
        _validate_result_digest(self)
        _reject_unsafe_public_payload("result", self)
        _require_safety_flags("result", self)

    @property
    def payload(self) -> dict[str, Any]:
        return strategy_candidate_source_disagreement_escalation_v10_payload(self)


def evaluate_strategy_candidate_source_disagreement_escalation_v10(
    source_disagreement: StrategyCandidateSourceDisagreementEscalationV10Input,
    *,
    config: StrategyCandidateSourceDisagreementEscalationV10Config | None = None,
) -> StrategyCandidateSourceDisagreementEscalationV10Result:
    active_config = config or StrategyCandidateSourceDisagreementEscalationV10Config()
    if type(source_disagreement) is not StrategyCandidateSourceDisagreementEscalationV10Input:
        raise ValueError(
            "source_disagreement must be a "
            "StrategyCandidateSourceDisagreementEscalationV10Input",
        )
    if type(active_config) is not StrategyCandidateSourceDisagreementEscalationV10Config:
        raise ValueError(
            "config must be a StrategyCandidateSourceDisagreementEscalationV10Config",
        )
    _reject_unsafe_public_payload("source_disagreement", source_disagreement)
    _reject_unsafe_public_payload("config", active_config)
    _require_safety_flags("source_disagreement", source_disagreement)
    _require_safety_flags("config", active_config)
    recency_gap_pressure = _recency_gap_pressure(source_disagreement.recency_gap_hours)
    resolution_urgency = _resolution_urgency(
        source_disagreement.time_to_resolution_hours,
    )
    escalation_priority_score = _escalation_priority_score(
        contradiction_rate=source_disagreement.contradiction_rate,
        source_reliability_spread=source_disagreement.source_reliability_spread,
        recency_gap_pressure=recency_gap_pressure,
        resolution_urgency=resolution_urgency,
        market_move_since_disagreement=(
            source_disagreement.market_move_since_disagreement
        ),
    )
    escalation_status = _escalation_status(
        escalation_priority_score,
        config=active_config,
    )
    reason_codes = _reason_codes(
        source_disagreement,
        escalation_status=escalation_status,
        config=active_config,
    )
    validation_digest = _result_validation_digest(
        config_version=active_config.config_version,
        candidate_id=source_disagreement.candidate_id,
        market_slug=source_disagreement.market_slug,
        contradiction_rate=source_disagreement.contradiction_rate,
        source_reliability_spread=source_disagreement.source_reliability_spread,
        recency_gap_hours=source_disagreement.recency_gap_hours,
        recency_gap_pressure=recency_gap_pressure,
        time_to_resolution_hours=source_disagreement.time_to_resolution_hours,
        resolution_urgency=resolution_urgency,
        market_move_since_disagreement=(
            source_disagreement.market_move_since_disagreement
        ),
        escalation_priority_score=escalation_priority_score,
        escalation_status=escalation_status,
        escalation_action=_escalation_action(escalation_status),
        reason_codes=reason_codes,
    )
    return StrategyCandidateSourceDisagreementEscalationV10Result(
        config_version=active_config.config_version,
        candidate_id=source_disagreement.candidate_id,
        market_slug=source_disagreement.market_slug,
        contradiction_rate=source_disagreement.contradiction_rate,
        source_reliability_spread=source_disagreement.source_reliability_spread,
        recency_gap_hours=source_disagreement.recency_gap_hours,
        recency_gap_pressure=recency_gap_pressure,
        time_to_resolution_hours=source_disagreement.time_to_resolution_hours,
        resolution_urgency=resolution_urgency,
        market_move_since_disagreement=(
            source_disagreement.market_move_since_disagreement
        ),
        escalation_priority_score=escalation_priority_score,
        escalation_status=escalation_status,
        escalation_action=_escalation_action(escalation_status),
        reason_codes=reason_codes,
        validation_digest=validation_digest,
    )


def strategy_candidate_source_disagreement_escalation_v10_payload(
    result: StrategyCandidateSourceDisagreementEscalationV10Result | dict[str, Any],
) -> dict[str, Any]:
    if type(result) is dict:
        return _validated_public_payload(result)
    if type(result) is not StrategyCandidateSourceDisagreementEscalationV10Result:
        raise ValueError(
            "result must be a StrategyCandidateSourceDisagreementEscalationV10Result",
        )
    _reject_unsafe_public_payload("result", result)
    _require_safety_flags("result", result)
    payload = {
        "config_version": result.config_version,
        "candidate_id": result.candidate_id,
        "market_slug": result.market_slug,
        "contradiction_rate": _decimal_payload(result.contradiction_rate),
        "source_reliability_spread": _decimal_payload(
            result.source_reliability_spread,
        ),
        "recency_gap_hours": _decimal_payload(result.recency_gap_hours),
        "recency_gap_pressure": _decimal_payload(result.recency_gap_pressure),
        "time_to_resolution_hours": _decimal_payload(result.time_to_resolution_hours),
        "resolution_urgency": _decimal_payload(result.resolution_urgency),
        "market_move_since_disagreement": _decimal_payload(
            result.market_move_since_disagreement,
        ),
        "escalation_priority_score": _decimal_payload(
            result.escalation_priority_score,
        ),
        "escalation_status": result.escalation_status,
        "escalation_action": result.escalation_action,
        "reason_codes": list(result.reason_codes),
        "validation_digest": result.validation_digest,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return _validated_public_payload(payload)


def _recency_gap_pressure(recency_gap_hours: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _cap_probability(recency_gap_hours / MAX_RECENCY_GAP_HOURS)


def _resolution_urgency(time_to_resolution_hours: Decimal) -> Decimal:
    if time_to_resolution_hours <= URGENT_RESOLUTION_HOURS:
        return ONE
    if time_to_resolution_hours >= NEAR_RESOLUTION_HOURS:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        span = NEAR_RESOLUTION_HOURS - URGENT_RESOLUTION_HOURS
        remaining = NEAR_RESOLUTION_HOURS - time_to_resolution_hours
        return _cap_probability(remaining / span)


def _escalation_priority_score(
    *,
    contradiction_rate: Decimal,
    source_reliability_spread: Decimal,
    recency_gap_pressure: Decimal,
    resolution_urgency: Decimal,
    market_move_since_disagreement: Decimal,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        score = (
            contradiction_rate * CONTRADICTION_WEIGHT
            + source_reliability_spread * RELIABILITY_SPREAD_WEIGHT
            + recency_gap_pressure * RECENCY_GAP_WEIGHT
            + resolution_urgency * RESOLUTION_URGENCY_WEIGHT
            + market_move_since_disagreement * MARKET_MOVE_WEIGHT
        )
        return _cap_probability(score)


def _escalation_status(
    escalation_priority_score: Decimal,
    *,
    config: StrategyCandidateSourceDisagreementEscalationV10Config,
) -> str:
    if escalation_priority_score >= config.critical_priority_score:
        return "critical"
    if escalation_priority_score >= config.high_priority_score:
        return "high"
    if escalation_priority_score >= config.watch_priority_score:
        return "watch"
    return "clear"


def _escalation_action(escalation_status: str) -> str:
    if escalation_status == "critical":
        return "pause_candidate_signal"
    if escalation_status == "high":
        return "escalate_research_lead"
    if escalation_status == "watch":
        return "queue_source_recheck"
    return "keep_research_signal"


def _reason_codes(
    source_disagreement: StrategyCandidateSourceDisagreementEscalationV10Input,
    *,
    escalation_status: str,
    config: StrategyCandidateSourceDisagreementEscalationV10Config,
) -> tuple[str, ...]:
    prefix = "candidate_source_disagreement_escalation_v10"
    reason_codes = [f"{prefix}_{escalation_status}"]
    if source_disagreement.contradiction_rate >= config.high_contradiction_rate:
        reason_codes.append(f"{prefix}_contradiction_rate_high")
    if source_disagreement.source_reliability_spread >= config.high_reliability_spread:
        reason_codes.append(f"{prefix}_reliability_spread_high")
    if source_disagreement.recency_gap_hours >= MAX_RECENCY_GAP_HOURS:
        reason_codes.append(f"{prefix}_recency_gap_stale")
    if source_disagreement.time_to_resolution_hours <= URGENT_RESOLUTION_HOURS:
        reason_codes.append(f"{prefix}_resolution_urgent")
    elif source_disagreement.time_to_resolution_hours <= NEAR_RESOLUTION_HOURS / THREE:
        reason_codes.append(f"{prefix}_resolution_near")
    if source_disagreement.market_move_since_disagreement >= config.material_market_move:
        reason_codes.append(f"{prefix}_market_move_material")
    elif source_disagreement.market_move_since_disagreement >= config.watch_market_move:
        reason_codes.append(f"{prefix}_market_move_watch")
    return _normalize_reason_codes(tuple(reason_codes), require_nonempty=True)


def _validate_result(
    result: StrategyCandidateSourceDisagreementEscalationV10Result,
) -> None:
    expected_recency_gap_pressure = _recency_gap_pressure(result.recency_gap_hours)
    if result.recency_gap_pressure != expected_recency_gap_pressure:
        raise ValueError("recency_gap_pressure must match recency_gap_hours")
    expected_resolution_urgency = _resolution_urgency(result.time_to_resolution_hours)
    if result.resolution_urgency != expected_resolution_urgency:
        raise ValueError("resolution_urgency must match time_to_resolution_hours")
    expected_priority_score = _escalation_priority_score(
        contradiction_rate=result.contradiction_rate,
        source_reliability_spread=result.source_reliability_spread,
        recency_gap_pressure=result.recency_gap_pressure,
        resolution_urgency=result.resolution_urgency,
        market_move_since_disagreement=result.market_move_since_disagreement,
    )
    if result.escalation_priority_score != expected_priority_score:
        raise ValueError("escalation_priority_score must match inputs")
    if result.config_version == DEFAULT_CONFIG_VERSION:
        default_config = StrategyCandidateSourceDisagreementEscalationV10Config()
        expected_status = _escalation_status(
            result.escalation_priority_score,
            config=default_config,
        )
        if result.escalation_status != expected_status:
            raise ValueError("escalation_status must match escalation_priority_score")
    expected_action = _escalation_action(result.escalation_status)
    if result.escalation_action != expected_action:
        raise ValueError("escalation_action must match escalation_status")


def _validate_result_digest(
    result: StrategyCandidateSourceDisagreementEscalationV10Result,
) -> None:
    expected_digest = _result_validation_digest(
        config_version=result.config_version,
        candidate_id=result.candidate_id,
        market_slug=result.market_slug,
        contradiction_rate=result.contradiction_rate,
        source_reliability_spread=result.source_reliability_spread,
        recency_gap_hours=result.recency_gap_hours,
        recency_gap_pressure=result.recency_gap_pressure,
        time_to_resolution_hours=result.time_to_resolution_hours,
        resolution_urgency=result.resolution_urgency,
        market_move_since_disagreement=result.market_move_since_disagreement,
        escalation_priority_score=result.escalation_priority_score,
        escalation_status=result.escalation_status,
        escalation_action=result.escalation_action,
        reason_codes=result.reason_codes,
    )
    if result.validation_digest != expected_digest:
        raise ValueError("validation_digest must match result")


def _result_validation_digest(
    *,
    config_version: str,
    candidate_id: str,
    market_slug: str,
    contradiction_rate: Decimal,
    source_reliability_spread: Decimal,
    recency_gap_hours: Decimal,
    recency_gap_pressure: Decimal,
    time_to_resolution_hours: Decimal,
    resolution_urgency: Decimal,
    market_move_since_disagreement: Decimal,
    escalation_priority_score: Decimal,
    escalation_status: str,
    escalation_action: str,
    reason_codes: tuple[str, ...],
) -> str:
    digest_parts = (
        VALIDATION_DIGEST_ALGORITHM,
        config_version,
        candidate_id,
        market_slug,
        _decimal_payload(contradiction_rate),
        _decimal_payload(source_reliability_spread),
        _decimal_payload(recency_gap_hours),
        _decimal_payload(recency_gap_pressure),
        _decimal_payload(time_to_resolution_hours),
        _decimal_payload(resolution_urgency),
        _decimal_payload(market_move_since_disagreement),
        _decimal_payload(escalation_priority_score),
        escalation_status,
        escalation_action,
        "\x1f".join(reason_codes),
        "paper_only=True",
        "report_only=True",
        "readonly=True",
    )
    return hashlib.sha256("\n".join(digest_parts).encode("utf-8")).hexdigest()


def _validated_public_payload(payload: dict[str, Any]) -> dict[str, Any]:
    _reject_unsafe_public_payload("payload", payload)
    ready = json_ready_no_floats(payload)
    if type(ready) is not dict:
        raise ValueError("payload must be a JSON object")
    _require_safety_flags("payload", _DictFlags(ready))
    _validate_payload_digest(ready)
    return ready


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


def _validate_payload_digest(payload: dict[str, Any]) -> None:
    reason_codes = _payload_reason_codes(payload)
    validation_digest = _require_validation_digest(
        "validation_digest",
        _payload_field(payload, "validation_digest"),
    )
    expected_digest = _result_validation_digest(
        config_version=_payload_canonical_string(payload, "config_version"),
        candidate_id=_payload_canonical_string(payload, "candidate_id"),
        market_slug=_payload_canonical_string(payload, "market_slug"),
        contradiction_rate=_payload_decimal(payload, "contradiction_rate"),
        source_reliability_spread=_payload_decimal(
            payload,
            "source_reliability_spread",
        ),
        recency_gap_hours=_payload_decimal(payload, "recency_gap_hours"),
        recency_gap_pressure=_payload_decimal(payload, "recency_gap_pressure"),
        time_to_resolution_hours=_payload_decimal(
            payload,
            "time_to_resolution_hours",
        ),
        resolution_urgency=_payload_decimal(payload, "resolution_urgency"),
        market_move_since_disagreement=_payload_decimal(
            payload,
            "market_move_since_disagreement",
        ),
        escalation_priority_score=_payload_decimal(
            payload,
            "escalation_priority_score",
        ),
        escalation_status=_payload_member(
            payload,
            "escalation_status",
            ESCALATION_STATUSES,
        ),
        escalation_action=_payload_member(
            payload,
            "escalation_action",
            ESCALATION_ACTIONS,
        ),
        reason_codes=reason_codes,
    )
    if validation_digest != expected_digest:
        raise ValueError("validation_digest must match payload")


def _payload_field(payload: dict[str, Any], field_name: str) -> object:
    if field_name not in payload:
        raise ValueError(f"payload must include {field_name}")
    return payload[field_name]


def _payload_canonical_string(payload: dict[str, Any], field_name: str) -> str:
    value = _payload_field(payload, field_name)
    _require_canonical_string(field_name, value)
    return value


def _payload_member(
    payload: dict[str, Any],
    field_name: str,
    allowed_values: tuple[str, ...],
) -> str:
    value = _payload_field(payload, field_name)
    _require_member(field_name, value, allowed_values)
    return value


def _payload_decimal(payload: dict[str, Any], field_name: str) -> Decimal:
    value = _payload_field(payload, field_name)
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a Decimal string")
    try:
        decimal_value = Decimal(value)
    except Exception as exc:
        raise ValueError(f"{field_name} must be a Decimal string") from exc
    return _normalize_decimal(field_name, decimal_value)


def _payload_reason_codes(payload: dict[str, Any]) -> tuple[str, ...]:
    value = _payload_field(payload, "reason_codes")
    if type(value) is not list:
        raise ValueError("reason_codes must be a list")
    return _normalize_reason_codes(tuple(value), require_nonempty=True)


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _normalize_probability(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return decimal_value


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    decimal_value = value.quantize(RATIO_QUANTUM)
    if decimal_value != value:
        raise ValueError(f"{field_name} must use the required decimal precision")
    return decimal_value


def _quantize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value.quantize(RATIO_QUANTUM)


def _cap_probability(value: Decimal) -> Decimal:
    if value > ONE:
        return ONE
    if value < ZERO:
        return ZERO
    return _quantize_decimal("probability", value)


def _require_exact_type(field_name: str, value: object, expected_type: type[object]) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be {expected_type.__name__}")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    if "\n" in value or "\r" in value or "\t" in value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_member(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> None:
    if type(value) is not str or value not in allowed_values:
        raise ValueError(f"{field_name} must be a known value")


def _normalize_reason_codes(
    value: object,
    *,
    require_nonempty: bool = False,
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    if require_nonempty and not value:
        raise ValueError("reason_codes must not be empty")
    seen: set[str] = set()
    normalized: list[str] = []
    for reason_code in value:
        if type(reason_code) is not str:
            raise ValueError("reason_codes must contain canonical strings")
        if not reason_code or reason_code.strip() != reason_code:
            raise ValueError("reason_codes must contain canonical strings")
        if "\n" in reason_code or "\r" in reason_code or "\t" in reason_code:
            raise ValueError("reason_codes must contain canonical strings")
        if reason_code in seen:
            raise ValueError("reason_codes must be unique")
        seen.add(reason_code)
        normalized.append(reason_code)
    return tuple(normalized)


def _require_safety_flags(label: str, value: object) -> None:
    try:
        require_paper_only_flags(label, value)
    except AttributeError as exc:
        raise ValueError(f"{label} must expose paper_only/report_only/readonly") from exc


def _require_validation_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a validation digest")
    if len(value) != 64 or any(character not in HEX_DIGITS for character in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")
    return value


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    reject_unsafe_surface_fields(label, value)
    _reject_unsafe_public_values(label, value)


def _reject_unsafe_public_values(label: str, value: object) -> None:
    if type(value) is str:
        if _has_unsafe_public_value(value):
            raise ValueError(f"unsafe live surface value in {label}")
        return
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError(f"{label} Decimal values must be exact Decimal")
        if not value.is_finite():
            raise ValueError(f"{label} Decimal values must be finite")
        return
    if type(value) in (bool, type(None)):
        return
    if isinstance(value, dict):
        for item in value.values():
            _reject_unsafe_public_values(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_values(label, item)
        return
    if hasattr(value, "__dataclass_fields__") and not isinstance(value, type):
        for field_name in value.__dataclass_fields__:
            _reject_unsafe_public_values(label, getattr(value, field_name))
        return
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")


def _has_unsafe_public_value(value: str) -> bool:
    lowered = value.lower()
    for fragment in UNSAFE_SURFACE_FIELD_FRAGMENTS:
        if fragment == "sign":
            tokens = lowered.replace("_", " ").replace("-", " ").split()
            if "sign" in tokens or "signing" in tokens or "signature" in tokens:
                return True
            continue
        if fragment in lowered:
            return True
    return False


def _decimal_payload(value: Decimal) -> str:
    if type(value) is not Decimal:
        raise ValueError("payload decimal must be a Decimal")
    return format(value, "f")
