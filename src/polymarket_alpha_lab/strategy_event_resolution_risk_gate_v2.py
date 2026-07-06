"""Pure phase-one event resolution risk reducer."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from decimal import Context, Decimal, localcontext
from hashlib import sha256
from typing import Any


DEFAULT_STRATEGY_EVENT_RESOLUTION_RISK_GATE_V2_CONFIG_VERSION = (
    "strategy-event-resolution-risk-gate-v2"
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MAX_RECOMMENDATION_PENALTY = Decimal("0.350000")
WATCH_THRESHOLD = Decimal("0.000001")
BLOCKED_THRESHOLD = Decimal("0.700000")
HIGH_COMPONENT_THRESHOLD = Decimal("0.750000")
DECIMAL_CONTEXT = Context(prec=64)

GATE_STATUSES = ("pass", "watch", "blocked")
REQUIRED_FOLLOWUPS = (
    "clarify_resolution_criteria",
    "resolve_resolution_criteria",
    "refresh_official_sources",
    "replace_official_sources",
    "monitor_rule_change",
    "escalate_rule_change_review",
    "review_dispute_history",
    "escalate_dispute_review",
    "track_settlement_lag",
    "plan_settlement_lag",
)
REASON_CODES = (
    "event_resolution_risk_clear",
    "ambiguous_resolution_criteria_watch",
    "ambiguous_resolution_criteria_high",
    "official_source_weakness_watch",
    "official_source_weakness_high",
    "rule_change_risk_watch",
    "rule_change_risk_high",
    "dispute_history_watch",
    "dispute_history_high",
    "settlement_lag_risk_watch",
    "settlement_lag_risk_high",
    "recommendation_penalty_watch",
    "recommendation_penalty_blocked",
)

RISK_WEIGHT_AMBIGUOUS_CRITERIA = Decimal("0.250000")
RISK_WEIGHT_OFFICIAL_SOURCE_WEAKNESS = Decimal("0.250000")
RISK_WEIGHT_RULE_CHANGE = Decimal("0.200000")
RISK_WEIGHT_DISPUTE_HISTORY = Decimal("0.150000")
RISK_WEIGHT_SETTLEMENT_LAG = Decimal("0.150000")

UNSAFE_PUBLIC_TEXT_FRAGMENTS = (
    "li" "ve",
    "au" "th",
    "wal" "let",
    "or" "der",
    "net" "work",
    "data" "base",
    "per" "sist",
    "sig" "ning",
    "muta" "tion",
    "b" "uy",
    "se" "ll",
    "tra" "de",
)

DIGEST_FIELDS = (
    "config_version",
    "market_slug",
    "condition_id",
    "outcome_name",
    "base_recommendation_probability",
    "ambiguous_resolution_criteria_score",
    "official_source_weakness_score",
    "rule_change_risk_score",
    "dispute_history_score",
    "settlement_lag_risk_score",
    "resolution_risk_score",
    "recommendation_penalty",
    "penalty_adjusted_probability",
    "gate_status",
    "required_followups",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)


@dataclass(frozen=True)
class StrategyEventResolutionRiskGateV2Input:
    market_slug: str
    condition_id: str
    outcome_name: str
    base_recommendation_probability: Decimal
    ambiguous_resolution_criteria_score: Decimal
    official_source_weakness_score: Decimal
    rule_change_risk_score: Decimal
    dispute_history_score: Decimal
    settlement_lag_risk_score: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not StrategyEventResolutionRiskGateV2Input:
            raise ValueError("input must be a StrategyEventResolutionRiskGateV2Input")
        for field_name in ("market_slug", "condition_id", "outcome_name"):
            _require_canonical_public_string(field_name, getattr(self, field_name))
        for field_name in (
            "base_recommendation_probability",
            "ambiguous_resolution_criteria_score",
            "official_source_weakness_score",
            "rule_change_risk_score",
            "dispute_history_score",
            "settlement_lag_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, allow_empty=True),
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class StrategyEventResolutionRiskGateV2Report:
    config_version: str
    market_slug: str
    condition_id: str
    outcome_name: str
    base_recommendation_probability: Decimal
    ambiguous_resolution_criteria_score: Decimal
    official_source_weakness_score: Decimal
    rule_change_risk_score: Decimal
    dispute_history_score: Decimal
    settlement_lag_risk_score: Decimal
    resolution_risk_score: Decimal
    recommendation_penalty: Decimal
    penalty_adjusted_probability: Decimal
    gate_status: str
    required_followups: tuple[str, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not StrategyEventResolutionRiskGateV2Report:
            raise ValueError("report must be a StrategyEventResolutionRiskGateV2Report")
        for field_name in (
            "config_version",
            "market_slug",
            "condition_id",
            "outcome_name",
        ):
            _require_canonical_public_string(field_name, getattr(self, field_name))
        for field_name in (
            "base_recommendation_probability",
            "ambiguous_resolution_criteria_score",
            "official_source_weakness_score",
            "rule_change_risk_score",
            "dispute_history_score",
            "settlement_lag_risk_score",
            "resolution_risk_score",
            "recommendation_penalty",
            "penalty_adjusted_probability",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_member("gate_status", self.gate_status, GATE_STATUSES)
        object.__setattr__(
            self,
            "required_followups",
            _normalize_member_tuple(
                "required_followups",
                self.required_followups,
                REQUIRED_FOLLOWUPS,
                allow_empty=True,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_member_tuple(
                "reason_codes",
                self.reason_codes,
                REASON_CODES,
                allow_empty=False,
            ),
        )
        _require_hard_flags("report", self)
        _validate_validation_digest(self)
        _validate_report(self)

    @property
    def payload(self) -> dict[str, Any]:
        return strategy_event_resolution_risk_gate_v2_payload(self)


def build_strategy_event_resolution_risk_gate_v2_report(
    input_row: StrategyEventResolutionRiskGateV2Input,
) -> StrategyEventResolutionRiskGateV2Report:
    if type(input_row) is not StrategyEventResolutionRiskGateV2Input:
        raise ValueError("input must be a StrategyEventResolutionRiskGateV2Input")
    _require_hard_flags("input", input_row)
    risk_score = _resolution_risk_score(input_row)
    penalty = _recommendation_penalty(risk_score)
    adjusted_probability = _penalty_adjusted_probability(
        input_row.base_recommendation_probability,
        penalty,
    )
    status = _gate_status(input_row, risk_score)
    followups = _required_followups(input_row)
    reason_codes = _reason_codes(input_row, status)
    values: dict[str, object] = {
        "config_version": DEFAULT_STRATEGY_EVENT_RESOLUTION_RISK_GATE_V2_CONFIG_VERSION,
        "market_slug": input_row.market_slug,
        "condition_id": input_row.condition_id,
        "outcome_name": input_row.outcome_name,
        "base_recommendation_probability": input_row.base_recommendation_probability,
        "ambiguous_resolution_criteria_score": (
            input_row.ambiguous_resolution_criteria_score
        ),
        "official_source_weakness_score": input_row.official_source_weakness_score,
        "rule_change_risk_score": input_row.rule_change_risk_score,
        "dispute_history_score": input_row.dispute_history_score,
        "settlement_lag_risk_score": input_row.settlement_lag_risk_score,
        "resolution_risk_score": risk_score,
        "recommendation_penalty": penalty,
        "penalty_adjusted_probability": adjusted_probability,
        "gate_status": status,
        "required_followups": followups,
        "reason_codes": reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return StrategyEventResolutionRiskGateV2Report(
        **values,
        derived_validation_digest=_validation_digest_from_values(values),
    )


def strategy_event_resolution_risk_gate_v2_payload(
    report: StrategyEventResolutionRiskGateV2Report,
) -> dict[str, Any]:
    if type(report) is not StrategyEventResolutionRiskGateV2Report:
        raise ValueError("report must be a StrategyEventResolutionRiskGateV2Report")
    _require_hard_flags("report", report)
    _validate_validation_digest(report)
    _validate_report(report)
    payload = _payload_value(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a dictionary")
    return payload


def _resolution_risk_score(input_row: StrategyEventResolutionRiskGateV2Input) -> Decimal:
    return _add_decimal(
        _multiply_decimal(
            input_row.ambiguous_resolution_criteria_score,
            RISK_WEIGHT_AMBIGUOUS_CRITERIA,
        ),
        _multiply_decimal(
            input_row.official_source_weakness_score,
            RISK_WEIGHT_OFFICIAL_SOURCE_WEAKNESS,
        ),
        _multiply_decimal(
            input_row.rule_change_risk_score,
            RISK_WEIGHT_RULE_CHANGE,
        ),
        _multiply_decimal(
            input_row.dispute_history_score,
            RISK_WEIGHT_DISPUTE_HISTORY,
        ),
        _multiply_decimal(
            input_row.settlement_lag_risk_score,
            RISK_WEIGHT_SETTLEMENT_LAG,
        ),
    )


def _recommendation_penalty(risk_score: Decimal) -> Decimal:
    return _multiply_decimal(risk_score, MAX_RECOMMENDATION_PENALTY)


def _penalty_adjusted_probability(
    base_probability: Decimal,
    penalty: Decimal,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        adjusted = (base_probability - penalty).quantize(QUANTUM)
    if adjusted < ZERO:
        return ZERO
    return adjusted


def _gate_status(
    input_row: StrategyEventResolutionRiskGateV2Input,
    risk_score: Decimal,
) -> str:
    if risk_score >= BLOCKED_THRESHOLD:
        return "blocked"
    for value in _component_scores(input_row):
        if value >= HIGH_COMPONENT_THRESHOLD:
            return "blocked"
    if risk_score >= WATCH_THRESHOLD:
        return "watch"
    return "pass"


def _required_followups(
    input_row: StrategyEventResolutionRiskGateV2Input,
) -> tuple[str, ...]:
    values: list[str] = []
    values.extend(
        _component_followups(
            input_row.ambiguous_resolution_criteria_score,
            watch="clarify_resolution_criteria",
            high="resolve_resolution_criteria",
        ),
    )
    values.extend(
        _component_followups(
            input_row.official_source_weakness_score,
            watch="refresh_official_sources",
            high="replace_official_sources",
        ),
    )
    values.extend(
        _component_followups(
            input_row.rule_change_risk_score,
            watch="monitor_rule_change",
            high="escalate_rule_change_review",
        ),
    )
    values.extend(
        _component_followups(
            input_row.dispute_history_score,
            watch="review_dispute_history",
            high="escalate_dispute_review",
        ),
    )
    values.extend(
        _component_followups(
            input_row.settlement_lag_risk_score,
            watch="track_settlement_lag",
            high="plan_settlement_lag",
        ),
    )
    return tuple(values)


def _reason_codes(
    input_row: StrategyEventResolutionRiskGateV2Input,
    status: str,
) -> tuple[str, ...]:
    values: list[str] = list(input_row.reason_codes)
    values.extend(
        _component_reason_codes(
            input_row.ambiguous_resolution_criteria_score,
            watch="ambiguous_resolution_criteria_watch",
            high="ambiguous_resolution_criteria_high",
        ),
    )
    values.extend(
        _component_reason_codes(
            input_row.official_source_weakness_score,
            watch="official_source_weakness_watch",
            high="official_source_weakness_high",
        ),
    )
    values.extend(
        _component_reason_codes(
            input_row.rule_change_risk_score,
            watch="rule_change_risk_watch",
            high="rule_change_risk_high",
        ),
    )
    values.extend(
        _component_reason_codes(
            input_row.dispute_history_score,
            watch="dispute_history_watch",
            high="dispute_history_high",
        ),
    )
    values.extend(
        _component_reason_codes(
            input_row.settlement_lag_risk_score,
            watch="settlement_lag_risk_watch",
            high="settlement_lag_risk_high",
        ),
    )
    if status != "pass":
        values.append(f"recommendation_penalty_{status}")
    if not values:
        values.append("event_resolution_risk_clear")
    return _unique_reason_codes(tuple(values))


def _component_scores(
    input_row: StrategyEventResolutionRiskGateV2Input,
) -> tuple[Decimal, ...]:
    return (
        input_row.ambiguous_resolution_criteria_score,
        input_row.official_source_weakness_score,
        input_row.rule_change_risk_score,
        input_row.dispute_history_score,
        input_row.settlement_lag_risk_score,
    )


def _component_followups(
    value: Decimal,
    *,
    watch: str,
    high: str,
) -> tuple[str, ...]:
    if value >= HIGH_COMPONENT_THRESHOLD:
        return (high,)
    if value > ZERO:
        return (watch,)
    return ()


def _component_reason_codes(
    value: Decimal,
    *,
    watch: str,
    high: str,
) -> tuple[str, ...]:
    if value >= HIGH_COMPONENT_THRESHOLD:
        return (high,)
    if value > ZERO:
        return (watch,)
    return ()


def _validate_report(report: StrategyEventResolutionRiskGateV2Report) -> None:
    input_row = StrategyEventResolutionRiskGateV2Input(
        market_slug=report.market_slug,
        condition_id=report.condition_id,
        outcome_name=report.outcome_name,
        base_recommendation_probability=report.base_recommendation_probability,
        ambiguous_resolution_criteria_score=(
            report.ambiguous_resolution_criteria_score
        ),
        official_source_weakness_score=report.official_source_weakness_score,
        rule_change_risk_score=report.rule_change_risk_score,
        dispute_history_score=report.dispute_history_score,
        settlement_lag_risk_score=report.settlement_lag_risk_score,
        reason_codes=tuple(
            reason_code
            for reason_code in report.reason_codes
            if reason_code not in REASON_CODES
        ),
    )
    expected_risk_score = _resolution_risk_score(input_row)
    expected_penalty = _recommendation_penalty(expected_risk_score)
    expected_adjusted_probability = _penalty_adjusted_probability(
        input_row.base_recommendation_probability,
        expected_penalty,
    )
    expected_status = _gate_status(input_row, expected_risk_score)
    if report.resolution_risk_score != expected_risk_score:
        raise ValueError("resolution_risk_score must match resolution risk inputs")
    if report.recommendation_penalty != expected_penalty:
        raise ValueError("recommendation_penalty must match resolution risk inputs")
    if report.penalty_adjusted_probability != expected_adjusted_probability:
        raise ValueError("penalty_adjusted_probability must match recommendation penalty")
    if report.gate_status != expected_status:
        raise ValueError("gate_status must match resolution risk inputs")
    if report.required_followups != _required_followups(input_row):
        raise ValueError("required_followups must match resolution risk inputs")
    if report.reason_codes != _reason_codes(input_row, expected_status):
        raise ValueError("reason_codes must match resolution risk inputs")


def _validate_validation_digest(
    report: StrategyEventResolutionRiskGateV2Report,
) -> None:
    _require_digest(report.derived_validation_digest)
    values = {field_name: getattr(report, field_name) for field_name in DIGEST_FIELDS}
    if report.derived_validation_digest != _validation_digest_from_values(values):
        raise ValueError("derived_validation_digest must match report values")


def _validation_digest_from_values(values: dict[str, object]) -> str:
    parts = tuple(
        f"{field_name}={_digest_value(values[field_name])}"
        for field_name in DIGEST_FIELDS
    )
    return sha256("\n".join(parts).encode("utf-8")).hexdigest()


def _digest_value(value: object) -> str:
    if type(value) is Decimal:
        return str(value)
    if type(value) is str:
        return value
    if type(value) is bool:
        return "true" if value else "false"
    if type(value) is tuple:
        return "[" + "|".join(_digest_value(item) for item in value) + "]"
    raise ValueError("derived_validation_digest value is not supported")


def _require_digest(value: object) -> None:
    if type(value) is not str:
        raise ValueError("derived_validation_digest must be a string")
    if len(value) != 64:
        raise ValueError("derived_validation_digest must be sha256 hex")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError("derived_validation_digest must be sha256 hex")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_canonical_public_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical string")
    _reject_unsafe_public_text(value)


def _require_member(field_name: str, value: object, values: tuple[str, ...]) -> None:
    if type(value) is not str or value not in values:
        raise ValueError(f"{field_name} must be one of {values}")


def _normalize_reason_codes(
    values: object,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    reason_codes = tuple(values)
    if not allow_empty and not reason_codes:
        raise ValueError("reason_codes must contain at least one value")
    seen: set[str] = set()
    for reason_code in reason_codes:
        _require_reason_code("reason_codes", reason_code)
        if reason_code in seen:
            raise ValueError("reason_codes must be unique")
        seen.add(reason_code)
    return reason_codes


def _normalize_member_tuple(
    field_name: str,
    values: object,
    allowed_values: tuple[str, ...],
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not allow_empty and not values:
        raise ValueError(f"{field_name} must contain at least one value")
    seen: set[str] = set()
    for value in values:
        _require_member(field_name, value, allowed_values)
        if value in seen:
            raise ValueError(f"{field_name} must not contain duplicates")
        seen.add(value)
    return tuple(values)


def _unique_reason_codes(values: tuple[str, ...]) -> tuple[str, ...]:
    seen: set[str] = set()
    unique: list[str] = []
    for value in values:
        if value not in seen:
            unique.append(value)
            seen.add(value)
    return _normalize_reason_codes(tuple(unique), allow_empty=False)


def _require_reason_code(field_name: str, value: object) -> None:
    if type(value) is not str or not value:
        raise ValueError(f"{field_name} must contain canonical reason codes")
    if value != value.lower() or value.strip() != value:
        raise ValueError(f"{field_name} must contain canonical reason codes")
    for part in value.split("_"):
        if not part or not part.isalnum() or part != part.lower():
            raise ValueError(f"{field_name} must contain canonical reason codes")
    _reject_unsafe_public_text(value)


def _normalize_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value.as_tuple().exponent < QUANTUM.as_tuple().exponent:
        raise ValueError(f"{field_name} must not exceed six decimal places")
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _add_decimal(*values: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return sum(values, ZERO).quantize(QUANTUM)


def _multiply_decimal(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return (left * right).quantize(QUANTUM)


def _payload_value(value: Any) -> Any:
    if value is None:
        return None
    if type(value) is bool:
        return value
    if type(value) in (float, int):
        raise ValueError("public payload numeric values must be Decimal strings")
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("public payload Decimal must be finite")
        return str(value)
    if type(value) is str:
        _reject_unsafe_public_text(value)
        return value
    if is_dataclass(value) and not isinstance(value, type):
        _require_hard_flags(type(value).__name__, value)
        return _payload_mapping(vars(value))
    if type(value) is dict:
        return _payload_mapping(value)
    if type(value) in (list, tuple):
        return [_payload_value(item) for item in value]
    raise ValueError("public payload value is not serializable")


def _payload_mapping(value: dict[Any, Any]) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    for key, item in value.items():
        if type(key) is not str:
            raise ValueError("public payload keys must be strings")
        if key.startswith("_"):
            continue
        _reject_unsafe_public_text(key)
        payload[key] = _payload_value(item)
    return payload


def _reject_unsafe_public_text(value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_TEXT_FRAGMENTS):
        raise ValueError("unsafe public text")


__all__ = (
    "DEFAULT_STRATEGY_EVENT_RESOLUTION_RISK_GATE_V2_CONFIG_VERSION",
    "GATE_STATUSES",
    "REASON_CODES",
    "REQUIRED_FOLLOWUPS",
    "StrategyEventResolutionRiskGateV2Input",
    "StrategyEventResolutionRiskGateV2Report",
    "build_strategy_event_resolution_risk_gate_v2_report",
    "strategy_event_resolution_risk_gate_v2_payload",
)
