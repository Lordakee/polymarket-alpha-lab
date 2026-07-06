"""Pure paper/report candidate liquidity and settlement risk blend v2."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from decimal import Decimal
from hashlib import sha256
from typing import Any


QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
HUNDRED = Decimal("100.000000")
INSIDE_LIMIT_SCORE = Decimal("80.000000")
LIQUIDITY_CAPACITY_WEIGHT = Decimal("0.200000")
SPREAD_WEIGHT = Decimal("0.150000")
DEPTH_WEIGHT = Decimal("0.250000")
SETTLEMENT_LAG_WEIGHT = Decimal("0.150000")
RESOLUTION_CLARITY_WEIGHT = Decimal("0.150000")
EXIT_EASE_WEIGHT = Decimal("0.100000")
BLEND_STATUSES = ("candidate", "watch", "blocked")
BLEND_DECISIONS = ("paper_candidate", "manual_review", "reject")
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
)
_UNSAFE_TERMS = tuple("".join(parts) for parts in _UNSAFE_TERM_PARTS)
_DIGEST_FIELDS = (
    "candidate_id",
    "available_liquidity_usd",
    "target_notional_usd",
    "liquidity_capacity_score",
    "spread_bps",
    "maximum_spread_bps",
    "spread_score",
    "depth_usd",
    "minimum_depth_usd",
    "depth_score",
    "settlement_lag_hours",
    "maximum_settlement_lag_hours",
    "settlement_lag_score",
    "resolution_ambiguity_score",
    "resolution_clarity_score",
    "exit_difficulty_score",
    "exit_ease_score",
    "paper_blend_score",
    "risk_score",
    "minimum_actionable_score",
    "blend_status",
    "blend_decision",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)


@dataclass(frozen=True)
class StrategyCandidateLiquiditySettlementRiskBlendV2Input:
    candidate_id: str
    available_liquidity_usd: Decimal
    target_notional_usd: Decimal
    spread_bps: Decimal
    maximum_spread_bps: Decimal
    depth_usd: Decimal
    minimum_depth_usd: Decimal
    settlement_lag_hours: Decimal
    maximum_settlement_lag_hours: Decimal
    resolution_ambiguity_score: Decimal
    exit_difficulty_score: Decimal
    minimum_actionable_score: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("candidate_id", self.candidate_id)
        for field_name in (
            "available_liquidity_usd",
            "spread_bps",
            "depth_usd",
            "settlement_lag_hours",
            "minimum_actionable_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "target_notional_usd",
            "maximum_spread_bps",
            "minimum_depth_usd",
            "maximum_settlement_lag_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "resolution_ambiguity_score",
            "exit_difficulty_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        reject_strategy_candidate_liquidity_settlement_risk_blend_v2_unsafe_payload(
            "candidate liquidity settlement blend input",
            self,
        )
        _require_paper_flags("candidate liquidity settlement blend input", self)


@dataclass(frozen=True)
class StrategyCandidateLiquiditySettlementRiskBlendV2Result:
    candidate_id: str
    available_liquidity_usd: Decimal
    target_notional_usd: Decimal
    liquidity_capacity_score: Decimal
    spread_bps: Decimal
    maximum_spread_bps: Decimal
    spread_score: Decimal
    depth_usd: Decimal
    minimum_depth_usd: Decimal
    depth_score: Decimal
    settlement_lag_hours: Decimal
    maximum_settlement_lag_hours: Decimal
    settlement_lag_score: Decimal
    resolution_ambiguity_score: Decimal
    resolution_clarity_score: Decimal
    exit_difficulty_score: Decimal
    exit_ease_score: Decimal
    paper_blend_score: Decimal
    risk_score: Decimal
    minimum_actionable_score: Decimal
    blend_status: str
    blend_decision: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("candidate_id", self.candidate_id)
        for field_name in (
            "available_liquidity_usd",
            "liquidity_capacity_score",
            "spread_bps",
            "spread_score",
            "depth_usd",
            "depth_score",
            "settlement_lag_hours",
            "settlement_lag_score",
            "resolution_clarity_score",
            "exit_ease_score",
            "paper_blend_score",
            "risk_score",
            "minimum_actionable_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "target_notional_usd",
            "maximum_spread_bps",
            "minimum_depth_usd",
            "maximum_settlement_lag_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "resolution_ambiguity_score",
            "exit_difficulty_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        _require_choice("blend_status", self.blend_status, BLEND_STATUSES)
        _require_choice("blend_decision", self.blend_decision, BLEND_DECISIONS)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_result_consistency(self)
        reject_strategy_candidate_liquidity_settlement_risk_blend_v2_unsafe_payload(
            "candidate liquidity settlement blend result",
            self,
        )
        _require_paper_flags("candidate liquidity settlement blend result", self)
        expected_digest = _derived_validation_digest(self)
        if self.derived_validation_digest:
            _require_canonical_digest(self.derived_validation_digest)
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest must match result fields")
        else:
            object.__setattr__(self, "derived_validation_digest", expected_digest)

    @property
    def payload(self) -> dict[str, Any]:
        return strategy_candidate_liquidity_settlement_risk_blend_v2_payload(self)


def estimate_strategy_candidate_liquidity_settlement_risk_blend_v2(
    blend_input: StrategyCandidateLiquiditySettlementRiskBlendV2Input,
) -> StrategyCandidateLiquiditySettlementRiskBlendV2Result:
    if type(blend_input) is not StrategyCandidateLiquiditySettlementRiskBlendV2Input:
        raise ValueError(
            "blend_input must be a StrategyCandidateLiquiditySettlementRiskBlendV2Input",
        )
    reject_strategy_candidate_liquidity_settlement_risk_blend_v2_unsafe_payload(
        "candidate liquidity settlement blend input",
        blend_input,
    )
    _require_paper_flags("candidate liquidity settlement blend input", blend_input)

    liquidity_capacity_score = _ratio_capacity_score(
        "liquidity_capacity_score",
        blend_input.available_liquidity_usd,
        blend_input.target_notional_usd,
    )
    spread_score = _inverse_limit_score(
        "spread_score",
        blend_input.spread_bps,
        blend_input.maximum_spread_bps,
    )
    depth_score = _ratio_capacity_score(
        "depth_score",
        blend_input.depth_usd,
        blend_input.minimum_depth_usd,
    )
    settlement_lag_score = _inverse_limit_score(
        "settlement_lag_score",
        blend_input.settlement_lag_hours,
        blend_input.maximum_settlement_lag_hours,
    )
    resolution_clarity_score = _unit_inverse_score(
        "resolution_clarity_score",
        blend_input.resolution_ambiguity_score,
    )
    exit_ease_score = _unit_inverse_score(
        "exit_ease_score",
        blend_input.exit_difficulty_score,
    )
    paper_blend_score = _paper_blend_score(
        liquidity_capacity_score=liquidity_capacity_score,
        spread_score=spread_score,
        depth_score=depth_score,
        settlement_lag_score=settlement_lag_score,
        resolution_clarity_score=resolution_clarity_score,
        exit_ease_score=exit_ease_score,
    )
    risk_score = _normalize_nonnegative_decimal(
        "risk_score",
        HUNDRED - paper_blend_score,
    )
    blend_status = _blend_status(
        paper_blend_score,
        blend_input.minimum_actionable_score,
    )

    return StrategyCandidateLiquiditySettlementRiskBlendV2Result(
        candidate_id=blend_input.candidate_id,
        available_liquidity_usd=blend_input.available_liquidity_usd,
        target_notional_usd=blend_input.target_notional_usd,
        liquidity_capacity_score=liquidity_capacity_score,
        spread_bps=blend_input.spread_bps,
        maximum_spread_bps=blend_input.maximum_spread_bps,
        spread_score=spread_score,
        depth_usd=blend_input.depth_usd,
        minimum_depth_usd=blend_input.minimum_depth_usd,
        depth_score=depth_score,
        settlement_lag_hours=blend_input.settlement_lag_hours,
        maximum_settlement_lag_hours=blend_input.maximum_settlement_lag_hours,
        settlement_lag_score=settlement_lag_score,
        resolution_ambiguity_score=blend_input.resolution_ambiguity_score,
        resolution_clarity_score=resolution_clarity_score,
        exit_difficulty_score=blend_input.exit_difficulty_score,
        exit_ease_score=exit_ease_score,
        paper_blend_score=paper_blend_score,
        risk_score=risk_score,
        minimum_actionable_score=blend_input.minimum_actionable_score,
        blend_status=blend_status,
        blend_decision=_blend_decision(blend_status),
        reason_codes=_reason_codes(
            blend_input.reason_codes,
            liquidity_capacity_score=liquidity_capacity_score,
            spread_score=spread_score,
            depth_score=depth_score,
            settlement_lag_score=settlement_lag_score,
            resolution_clarity_score=resolution_clarity_score,
            exit_ease_score=exit_ease_score,
            paper_blend_score=paper_blend_score,
            minimum_actionable_score=blend_input.minimum_actionable_score,
            blend_status=blend_status,
        ),
    )


def strategy_candidate_liquidity_settlement_risk_blend_v2_payload(
    result: StrategyCandidateLiquiditySettlementRiskBlendV2Result,
) -> dict[str, Any]:
    if type(result) is not StrategyCandidateLiquiditySettlementRiskBlendV2Result:
        raise ValueError(
            "result must be a StrategyCandidateLiquiditySettlementRiskBlendV2Result",
        )
    _require_paper_flags("candidate liquidity settlement blend result", result)
    if result.derived_validation_digest != _derived_validation_digest(result):
        raise ValueError("derived_validation_digest must match result fields")
    reject_strategy_candidate_liquidity_settlement_risk_blend_v2_unsafe_payload(
        "candidate liquidity settlement blend result",
        result,
    )
    return _json_ready(asdict(result))


def reject_strategy_candidate_liquidity_settlement_risk_blend_v2_unsafe_payload(
    label: str,
    payload: object,
) -> None:
    for item in _iter_public_strings(payload):
        lowered = item.lower()
        if any(term in lowered for term in _UNSAFE_TERMS):
            raise ValueError(f"unsafe public payload entry in {label}")


def _ratio_capacity_score(field_name: str, value: Decimal, target: Decimal) -> Decimal:
    if value >= target:
        return HUNDRED
    return _normalize_nonnegative_decimal(field_name, value / target * HUNDRED)


def _inverse_limit_score(field_name: str, value: Decimal, limit: Decimal) -> Decimal:
    if value >= limit:
        return ZERO
    return _normalize_nonnegative_decimal(field_name, HUNDRED - value / limit * HUNDRED)


def _unit_inverse_score(field_name: str, value: Decimal) -> Decimal:
    return _normalize_nonnegative_decimal(field_name, (ONE - value) * HUNDRED)


def _paper_blend_score(
    *,
    liquidity_capacity_score: Decimal,
    spread_score: Decimal,
    depth_score: Decimal,
    settlement_lag_score: Decimal,
    resolution_clarity_score: Decimal,
    exit_ease_score: Decimal,
) -> Decimal:
    return _normalize_nonnegative_decimal(
        "paper_blend_score",
        liquidity_capacity_score * LIQUIDITY_CAPACITY_WEIGHT
        + spread_score * SPREAD_WEIGHT
        + depth_score * DEPTH_WEIGHT
        + settlement_lag_score * SETTLEMENT_LAG_WEIGHT
        + resolution_clarity_score * RESOLUTION_CLARITY_WEIGHT
        + exit_ease_score * EXIT_EASE_WEIGHT,
    )


def _blend_status(paper_blend_score: Decimal, minimum_actionable_score: Decimal) -> str:
    if paper_blend_score <= ZERO:
        return "blocked"
    if paper_blend_score < minimum_actionable_score:
        return "watch"
    return "candidate"


def _blend_decision(blend_status: str) -> str:
    if blend_status == "candidate":
        return "paper_candidate"
    if blend_status == "watch":
        return "manual_review"
    if blend_status == "blocked":
        return "reject"
    raise ValueError("blend_status must be supported")


def _reason_codes(
    existing: tuple[str, ...],
    *,
    liquidity_capacity_score: Decimal,
    spread_score: Decimal,
    depth_score: Decimal,
    settlement_lag_score: Decimal,
    resolution_clarity_score: Decimal,
    exit_ease_score: Decimal,
    paper_blend_score: Decimal,
    minimum_actionable_score: Decimal,
    blend_status: str,
) -> tuple[str, ...]:
    additions = [
        "strategy_candidate_liquidity_settlement_risk_blend_v2",
        f"blend_{blend_status}",
        _capacity_reason_code(liquidity_capacity_score),
        _spread_reason_code(spread_score),
        _depth_reason_code(depth_score),
        _settlement_reason_code(settlement_lag_score),
        _resolution_reason_code(resolution_clarity_score),
        _exit_reason_code(exit_ease_score),
    ]
    if paper_blend_score <= ZERO:
        additions.append("blend_below_or_equal_zero")
    elif paper_blend_score < minimum_actionable_score:
        additions.append("blend_positive_below_minimum")
    else:
        additions.append("minimum_actionable_score_met")
    return _append_reason_codes(existing, tuple(additions))


def _capacity_reason_code(liquidity_capacity_score: Decimal) -> str:
    if liquidity_capacity_score >= HUNDRED:
        return "liquidity_capacity_sufficient"
    return "liquidity_capacity_shortfall"


def _spread_reason_code(spread_score: Decimal) -> str:
    if spread_score >= HUNDRED:
        return "spread_zero"
    if spread_score >= INSIDE_LIMIT_SCORE:
        return "spread_inside_limit"
    if spread_score > ZERO:
        return "spread_penalty_applied"
    return "spread_at_or_above_limit"


def _depth_reason_code(depth_score: Decimal) -> str:
    if depth_score >= HUNDRED:
        return "depth_sufficient"
    return "depth_shortfall"


def _settlement_reason_code(settlement_lag_score: Decimal) -> str:
    if settlement_lag_score >= HUNDRED:
        return "settlement_immediate"
    if settlement_lag_score >= INSIDE_LIMIT_SCORE:
        return "settlement_lag_inside_limit"
    if settlement_lag_score > ZERO:
        return "settlement_lag_penalty_applied"
    return "settlement_lag_at_or_above_limit"


def _resolution_reason_code(resolution_clarity_score: Decimal) -> str:
    if resolution_clarity_score >= HUNDRED:
        return "resolution_clear"
    return "resolution_ambiguity_present"


def _exit_reason_code(exit_ease_score: Decimal) -> str:
    if exit_ease_score >= INSIDE_LIMIT_SCORE:
        return "exit_easy"
    if exit_ease_score > ZERO:
        return "exit_difficulty_present"
    return "exit_difficulty_maximum"


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
    result: StrategyCandidateLiquiditySettlementRiskBlendV2Result,
) -> None:
    if result.liquidity_capacity_score != _ratio_capacity_score(
        "liquidity_capacity_score",
        result.available_liquidity_usd,
        result.target_notional_usd,
    ):
        raise ValueError("liquidity_capacity_score must match liquidity inputs")
    if result.spread_score != _inverse_limit_score(
        "spread_score",
        result.spread_bps,
        result.maximum_spread_bps,
    ):
        raise ValueError("spread_score must match spread inputs")
    if result.depth_score != _ratio_capacity_score(
        "depth_score",
        result.depth_usd,
        result.minimum_depth_usd,
    ):
        raise ValueError("depth_score must match depth inputs")
    if result.settlement_lag_score != _inverse_limit_score(
        "settlement_lag_score",
        result.settlement_lag_hours,
        result.maximum_settlement_lag_hours,
    ):
        raise ValueError("settlement_lag_score must match lag inputs")
    if result.resolution_clarity_score != _unit_inverse_score(
        "resolution_clarity_score",
        result.resolution_ambiguity_score,
    ):
        raise ValueError("resolution_clarity_score must match ambiguity input")
    if result.exit_ease_score != _unit_inverse_score(
        "exit_ease_score",
        result.exit_difficulty_score,
    ):
        raise ValueError("exit_ease_score must match difficulty input")
    if result.paper_blend_score != _paper_blend_score(
        liquidity_capacity_score=result.liquidity_capacity_score,
        spread_score=result.spread_score,
        depth_score=result.depth_score,
        settlement_lag_score=result.settlement_lag_score,
        resolution_clarity_score=result.resolution_clarity_score,
        exit_ease_score=result.exit_ease_score,
    ):
        raise ValueError("paper_blend_score must match component scores")
    if result.risk_score != _normalize_nonnegative_decimal(
        "risk_score",
        HUNDRED - result.paper_blend_score,
    ):
        raise ValueError("risk_score must match paper_blend_score")
    if result.blend_status != _blend_status(
        result.paper_blend_score,
        result.minimum_actionable_score,
    ):
        raise ValueError("blend_status must match paper_blend_score")
    if result.blend_decision != _blend_decision(result.blend_status):
        raise ValueError("blend_decision must match blend_status")


def _derived_validation_digest(
    result: StrategyCandidateLiquiditySettlementRiskBlendV2Result,
) -> str:
    parts = tuple(
        f"{field_name}={_digest_value(getattr(result, field_name))}"
        for field_name in _DIGEST_FIELDS
    )
    return sha256("|".join(parts).encode("utf-8")).hexdigest()


def _digest_value(value: object) -> str:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, tuple):
        return "[" + ",".join(_digest_value(item) for item in value) + "]"
    if type(value) is bool:
        return "true" if value else "false"
    if type(value) is str:
        return value
    raise ValueError("digest value must be public scalar data")


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    seen: set[str] = set()
    for reason_code in value:
        _require_canonical_string(field_name, reason_code)
        if reason_code in seen:
            raise ValueError(f"{field_name} must be unique")
        seen.add(reason_code)
    return value


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_unit_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be <= 1")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value.quantize(QUANTUM)


def _require_choice(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> None:
    if value not in allowed_values:
        raise ValueError(f"{field_name} must be one of {allowed_values!r}")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_canonical_digest(value: object) -> None:
    _require_canonical_string("derived_validation_digest", value)
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError("derived_validation_digest must be lowercase hex")


def _require_paper_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _iter_public_strings(value: object) -> tuple[str, ...]:
    if is_dataclass(value) and not isinstance(value, type):
        return _iter_public_strings(asdict(value))
    if isinstance(value, dict):
        items: list[str] = []
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            items.append(key)
            items.extend(_iter_public_strings(item))
        return tuple(items)
    if type(value) is str:
        return (value,)
    if isinstance(value, (list, tuple)):
        items = []
        for item in value:
            items.extend(_iter_public_strings(item))
        return tuple(items)
    return ()


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if isinstance(value, int) and not isinstance(value, bool):
        raise ValueError("JSON value must not be an int")
    if isinstance(value, (str, bool)):
        return value
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


__all__ = (
    "BLEND_STATUSES",
    "BLEND_DECISIONS",
    "StrategyCandidateLiquiditySettlementRiskBlendV2Input",
    "StrategyCandidateLiquiditySettlementRiskBlendV2Result",
    "estimate_strategy_candidate_liquidity_settlement_risk_blend_v2",
    "strategy_candidate_liquidity_settlement_risk_blend_v2_payload",
    "reject_strategy_candidate_liquidity_settlement_risk_blend_v2_unsafe_payload",
)
