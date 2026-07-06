"""Pure paper report market context gap escalation reducer."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any


__all__ = (
    "StrategyMarketContextGapEscalationV10Input",
    "StrategyMarketContextGapEscalationV10Result",
    "build_strategy_market_context_gap_escalation_v10_result",
    "evaluate_strategy_market_context_gap_escalation_v10",
    "strategy_market_context_gap_escalation_v10_payload",
)


VALUE_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")

MISSING_PRIMARY_SOURCE_WEIGHT = Decimal("0.350000")
STALE_CONTEXT_WEIGHT = Decimal("0.200000")
MARKET_MOVEMENT_WEIGHT = Decimal("0.180000")
RESOLUTION_TIMING_WEIGHT = Decimal("0.150000")
CONFIDENCE_GAP_WEIGHT = Decimal("0.100000")

CONTEXT_SCORE_FULL_AGE_MINUTES = Decimal("1440.000000")
MARKET_MOVE_FULL_BPS = Decimal("900.000000")
STALE_CONTEXT_MINUTES = Decimal("720.000000")
CRITICAL_CONTEXT_STALE_MINUTES = Decimal("1440.000000")
MATERIAL_MARKET_MOVE_BPS = Decimal("150.000000")
EXTREME_MARKET_MOVE_BPS = Decimal("800.000000")
NEAR_RESOLUTION_MINUTES = Decimal("240.000000")
LOW_DOMAIN_CONFIDENCE = Decimal("0.700000")
VERY_LOW_DOMAIN_CONFIDENCE = Decimal("0.500000")
WATCH_SCORE = Decimal("0.050000")
ESCALATE_SCORE = Decimal("0.100000")
BLOCK_SCORE = Decimal("0.550000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

ESCALATION_TIERS = ("clear", "watch", "escalate", "block_until_researched")
REQUIRED_ACTIONS = (
    "continue_screening",
    "monitor_context_drift",
    "assign_context_research",
    "block_until_required_context_refreshed",
)
CONTEXT_GAP_REASONS = (
    "missing_primary_sources",
    "stale_context",
    "market_moved_since_research",
    "near_resolution",
    "low_domain_confidence",
)
REASON_CODES = (
    "context_gap_escalation_clear",
    "context_gap_watch",
    "context_gap_escalate",
    "context_gap_block_until_researched",
    "missing_primary_sources",
    "context_stale",
    "context_critical_stale",
    "market_move_material_since_research",
    "market_move_extreme_since_research",
    "resolution_near",
    "resolution_imminent",
    "domain_confidence_watch",
    "domain_confidence_low",
)


@dataclass(frozen=True)
class StrategyMarketContextGapEscalationV10Input:
    market_id: str
    required_primary_source_count: Decimal
    missing_primary_source_count: Decimal
    context_age_minutes: Decimal
    market_move_bps_since_research: Decimal
    time_to_resolution_minutes: Decimal
    domain_specialist_confidence: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("market_id", self.market_id)
        object.__setattr__(
            self,
            "required_primary_source_count",
            _normalize_positive_whole_decimal(
                "required_primary_source_count",
                self.required_primary_source_count,
            ),
        )
        object.__setattr__(
            self,
            "missing_primary_source_count",
            _normalize_nonnegative_whole_decimal(
                "missing_primary_source_count",
                self.missing_primary_source_count,
            ),
        )
        for field_name in (
            "context_age_minutes",
            "market_move_bps_since_research",
            "time_to_resolution_minutes",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "domain_specialist_confidence",
            _normalize_probability(
                "domain_specialist_confidence",
                self.domain_specialist_confidence,
            ),
        )
        if self.missing_primary_source_count > self.required_primary_source_count:
            raise ValueError(
                "missing_primary_source_count must not exceed "
                "required_primary_source_count",
            )
        _require_paper_flags("input", self)


@dataclass(frozen=True)
class StrategyMarketContextGapEscalationV10Result:
    market_id: str
    required_primary_source_count: Decimal
    missing_primary_source_count: Decimal
    context_age_minutes: Decimal
    market_move_bps_since_research: Decimal
    time_to_resolution_minutes: Decimal
    domain_specialist_confidence: Decimal
    missing_primary_source_score: Decimal
    stale_context_score: Decimal
    market_movement_score: Decimal
    resolution_timing_score: Decimal
    confidence_gap_score: Decimal
    escalation_score: Decimal
    escalation_tier: str
    required_action: str
    context_gap_reasons: tuple[str, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("market_id", self.market_id)
        object.__setattr__(
            self,
            "required_primary_source_count",
            _normalize_positive_whole_decimal(
                "required_primary_source_count",
                self.required_primary_source_count,
            ),
        )
        object.__setattr__(
            self,
            "missing_primary_source_count",
            _normalize_nonnegative_whole_decimal(
                "missing_primary_source_count",
                self.missing_primary_source_count,
            ),
        )
        for field_name in (
            "context_age_minutes",
            "market_move_bps_since_research",
            "time_to_resolution_minutes",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "domain_specialist_confidence",
            _normalize_probability(
                "domain_specialist_confidence",
                self.domain_specialist_confidence,
            ),
        )
        for field_name in (
            "missing_primary_source_score",
            "stale_context_score",
            "market_movement_score",
            "resolution_timing_score",
            "confidence_gap_score",
            "escalation_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "escalation_tier",
            _normalize_choice("escalation_tier", self.escalation_tier, ESCALATION_TIERS),
        )
        object.__setattr__(
            self,
            "required_action",
            _normalize_choice("required_action", self.required_action, REQUIRED_ACTIONS),
        )
        object.__setattr__(
            self,
            "context_gap_reasons",
            _normalize_context_gap_reasons(self.context_gap_reasons),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        if self.missing_primary_source_count > self.required_primary_source_count:
            raise ValueError(
                "missing_primary_source_count must not exceed "
                "required_primary_source_count",
            )
        _validate_result_derivations(self)
        _require_paper_flags("result", self)

    @property
    def payload(self) -> dict[str, Any]:
        return strategy_market_context_gap_escalation_v10_payload(self)


def evaluate_strategy_market_context_gap_escalation_v10(
    input_row: StrategyMarketContextGapEscalationV10Input,
) -> StrategyMarketContextGapEscalationV10Result:
    if type(input_row) is not StrategyMarketContextGapEscalationV10Input:
        raise ValueError(
            "input_row must be a StrategyMarketContextGapEscalationV10Input",
        )
    _require_paper_flags("input", input_row)

    missing_primary_source_score = _missing_primary_source_score(input_row)
    stale_context_score = _stale_context_score(input_row.context_age_minutes)
    market_movement_score = _market_movement_score(
        input_row.market_move_bps_since_research,
    )
    resolution_timing_score = _resolution_timing_score(
        input_row.time_to_resolution_minutes,
    )
    confidence_gap_score = _confidence_gap_score(
        input_row.domain_specialist_confidence,
    )
    escalation_score = _score_sum(
        (
            missing_primary_source_score,
            stale_context_score,
            market_movement_score,
            resolution_timing_score,
            confidence_gap_score,
        ),
    )
    context_gap_reasons = _context_gap_reasons(input_row)
    escalation_tier = _escalation_tier(
        input_row,
        escalation_score=escalation_score,
        context_gap_reasons=context_gap_reasons,
    )
    return StrategyMarketContextGapEscalationV10Result(
        market_id=input_row.market_id,
        required_primary_source_count=input_row.required_primary_source_count,
        missing_primary_source_count=input_row.missing_primary_source_count,
        context_age_minutes=input_row.context_age_minutes,
        market_move_bps_since_research=input_row.market_move_bps_since_research,
        time_to_resolution_minutes=input_row.time_to_resolution_minutes,
        domain_specialist_confidence=input_row.domain_specialist_confidence,
        missing_primary_source_score=missing_primary_source_score,
        stale_context_score=stale_context_score,
        market_movement_score=market_movement_score,
        resolution_timing_score=resolution_timing_score,
        confidence_gap_score=confidence_gap_score,
        escalation_score=escalation_score,
        escalation_tier=escalation_tier,
        required_action=_required_action(escalation_tier),
        context_gap_reasons=context_gap_reasons,
        reason_codes=_reason_codes(input_row, escalation_tier),
    )


def build_strategy_market_context_gap_escalation_v10_result(
    input_row: StrategyMarketContextGapEscalationV10Input,
) -> StrategyMarketContextGapEscalationV10Result:
    return evaluate_strategy_market_context_gap_escalation_v10(input_row)


def strategy_market_context_gap_escalation_v10_payload(
    result: StrategyMarketContextGapEscalationV10Result,
) -> dict[str, Any]:
    if type(result) is not StrategyMarketContextGapEscalationV10Result:
        raise ValueError(
            "result must be a StrategyMarketContextGapEscalationV10Result",
        )
    _require_paper_flags("result", result)
    return {
        "market_id": result.market_id,
        "required_primary_source_count": _decimal_payload(
            result.required_primary_source_count,
        ),
        "missing_primary_source_count": _decimal_payload(
            result.missing_primary_source_count,
        ),
        "context_age_minutes": _decimal_payload(result.context_age_minutes),
        "market_move_bps_since_research": _decimal_payload(
            result.market_move_bps_since_research,
        ),
        "time_to_resolution_minutes": _decimal_payload(
            result.time_to_resolution_minutes,
        ),
        "domain_specialist_confidence": _decimal_payload(
            result.domain_specialist_confidence,
        ),
        "missing_primary_source_score": _decimal_payload(
            result.missing_primary_source_score,
        ),
        "stale_context_score": _decimal_payload(result.stale_context_score),
        "market_movement_score": _decimal_payload(result.market_movement_score),
        "resolution_timing_score": _decimal_payload(result.resolution_timing_score),
        "confidence_gap_score": _decimal_payload(result.confidence_gap_score),
        "escalation_score": _decimal_payload(result.escalation_score),
        "escalation_tier": result.escalation_tier,
        "required_action": result.required_action,
        "context_gap_reasons": list(result.context_gap_reasons),
        "reason_codes": list(result.reason_codes),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _missing_primary_source_score(
    input_row: StrategyMarketContextGapEscalationV10Input,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(
            (
                input_row.missing_primary_source_count
                / input_row.required_primary_source_count
            )
            * MISSING_PRIMARY_SOURCE_WEIGHT,
        )


def _stale_context_score(context_age_minutes: Decimal) -> Decimal:
    return _scaled_score(
        value=context_age_minutes,
        full_value=CONTEXT_SCORE_FULL_AGE_MINUTES,
        weight=STALE_CONTEXT_WEIGHT,
    )


def _market_movement_score(market_move_bps_since_research: Decimal) -> Decimal:
    return _scaled_score(
        value=market_move_bps_since_research,
        full_value=MARKET_MOVE_FULL_BPS,
        weight=MARKET_MOVEMENT_WEIGHT,
    )


def _resolution_timing_score(time_to_resolution_minutes: Decimal) -> Decimal:
    if time_to_resolution_minutes >= CONTEXT_SCORE_FULL_AGE_MINUTES:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(
            (
                (CONTEXT_SCORE_FULL_AGE_MINUTES - time_to_resolution_minutes)
                / CONTEXT_SCORE_FULL_AGE_MINUTES
            )
            * RESOLUTION_TIMING_WEIGHT,
        )


def _confidence_gap_score(domain_specialist_confidence: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize((ONE - domain_specialist_confidence) * CONFIDENCE_GAP_WEIGHT)


def _scaled_score(*, value: Decimal, full_value: Decimal, weight: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        if value >= full_value:
            return weight
        return _quantize((value / full_value) * weight)


def _score_sum(values: tuple[Decimal, ...]) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        total = ZERO
        for value in values:
            total += value
        return _quantize(total)


def _context_gap_reasons(
    input_row: StrategyMarketContextGapEscalationV10Input,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if input_row.missing_primary_source_count > ZERO:
        reasons.append("missing_primary_sources")
    if input_row.context_age_minutes >= STALE_CONTEXT_MINUTES:
        reasons.append("stale_context")
    if input_row.market_move_bps_since_research >= MATERIAL_MARKET_MOVE_BPS:
        reasons.append("market_moved_since_research")
    if input_row.time_to_resolution_minutes <= NEAR_RESOLUTION_MINUTES:
        reasons.append("near_resolution")
    if input_row.domain_specialist_confidence < LOW_DOMAIN_CONFIDENCE:
        reasons.append("low_domain_confidence")
    return tuple(reasons)


def _escalation_tier(
    input_row: StrategyMarketContextGapEscalationV10Input,
    *,
    escalation_score: Decimal,
    context_gap_reasons: tuple[str, ...],
) -> str:
    if (
        escalation_score >= BLOCK_SCORE
        or input_row.context_age_minutes >= CRITICAL_CONTEXT_STALE_MINUTES
        or (
            input_row.missing_primary_source_count > ZERO
            and input_row.time_to_resolution_minutes <= NEAR_RESOLUTION_MINUTES
        )
    ):
        return "block_until_researched"
    if input_row.missing_primary_source_count > ZERO or escalation_score >= ESCALATE_SCORE:
        return "escalate"
    if context_gap_reasons or escalation_score >= WATCH_SCORE:
        return "watch"
    return "clear"


def _required_action(escalation_tier: str) -> str:
    if escalation_tier == "clear":
        return "continue_screening"
    if escalation_tier == "watch":
        return "monitor_context_drift"
    if escalation_tier == "escalate":
        return "assign_context_research"
    if escalation_tier == "block_until_researched":
        return "block_until_required_context_refreshed"
    raise ValueError("escalation_tier is not supported")


def _reason_codes(
    input_row: StrategyMarketContextGapEscalationV10Input,
    escalation_tier: str,
) -> tuple[str, ...]:
    if escalation_tier == "clear":
        return ("context_gap_escalation_clear",)

    codes: list[str] = [f"context_gap_{escalation_tier}"]
    if input_row.missing_primary_source_count > ZERO:
        codes.append("missing_primary_sources")
    codes.extend(_context_stale_reason_codes(input_row.context_age_minutes))
    codes.extend(
        _market_move_reason_codes(input_row.market_move_bps_since_research),
    )
    codes.extend(_resolution_reason_codes(input_row.time_to_resolution_minutes))
    codes.extend(
        _confidence_reason_codes(input_row.domain_specialist_confidence),
    )
    return _normalize_reason_codes(tuple(codes))


def _context_stale_reason_codes(context_age_minutes: Decimal) -> tuple[str, ...]:
    if context_age_minutes >= CRITICAL_CONTEXT_STALE_MINUTES:
        return ("context_critical_stale",)
    if context_age_minutes >= STALE_CONTEXT_MINUTES:
        return ("context_stale",)
    return ()


def _market_move_reason_codes(
    market_move_bps_since_research: Decimal,
) -> tuple[str, ...]:
    if market_move_bps_since_research >= EXTREME_MARKET_MOVE_BPS:
        return ("market_move_extreme_since_research",)
    if market_move_bps_since_research >= MATERIAL_MARKET_MOVE_BPS:
        return ("market_move_material_since_research",)
    return ()


def _resolution_reason_codes(time_to_resolution_minutes: Decimal) -> tuple[str, ...]:
    if time_to_resolution_minutes <= NEAR_RESOLUTION_MINUTES:
        return ("resolution_imminent",)
    if time_to_resolution_minutes <= CONTEXT_SCORE_FULL_AGE_MINUTES:
        return ("resolution_near",)
    return ()


def _confidence_reason_codes(
    domain_specialist_confidence: Decimal,
) -> tuple[str, ...]:
    if domain_specialist_confidence < VERY_LOW_DOMAIN_CONFIDENCE:
        return ("domain_confidence_low",)
    if domain_specialist_confidence < LOW_DOMAIN_CONFIDENCE:
        return ("domain_confidence_watch",)
    return ()


def _validate_result_derivations(
    result: StrategyMarketContextGapEscalationV10Result,
) -> None:
    input_row = StrategyMarketContextGapEscalationV10Input(
        market_id=result.market_id,
        required_primary_source_count=result.required_primary_source_count,
        missing_primary_source_count=result.missing_primary_source_count,
        context_age_minutes=result.context_age_minutes,
        market_move_bps_since_research=result.market_move_bps_since_research,
        time_to_resolution_minutes=result.time_to_resolution_minutes,
        domain_specialist_confidence=result.domain_specialist_confidence,
    )
    expected_missing_score = _missing_primary_source_score(input_row)
    expected_stale_score = _stale_context_score(input_row.context_age_minutes)
    expected_movement_score = _market_movement_score(
        input_row.market_move_bps_since_research,
    )
    expected_resolution_score = _resolution_timing_score(
        input_row.time_to_resolution_minutes,
    )
    expected_confidence_score = _confidence_gap_score(
        input_row.domain_specialist_confidence,
    )
    if result.missing_primary_source_score != expected_missing_score:
        raise ValueError("missing_primary_source_score must match inputs")
    if result.stale_context_score != expected_stale_score:
        raise ValueError("stale_context_score must match inputs")
    if result.market_movement_score != expected_movement_score:
        raise ValueError("market_movement_score must match inputs")
    if result.resolution_timing_score != expected_resolution_score:
        raise ValueError("resolution_timing_score must match inputs")
    if result.confidence_gap_score != expected_confidence_score:
        raise ValueError("confidence_gap_score must match inputs")

    expected_score = _score_sum(
        (
            expected_missing_score,
            expected_stale_score,
            expected_movement_score,
            expected_resolution_score,
            expected_confidence_score,
        ),
    )
    if result.escalation_score != expected_score:
        raise ValueError("escalation_score must match score components")

    expected_reasons = _context_gap_reasons(input_row)
    expected_tier = _escalation_tier(
        input_row,
        escalation_score=expected_score,
        context_gap_reasons=expected_reasons,
    )
    if result.escalation_tier != expected_tier:
        raise ValueError("escalation_tier must match inputs and score")
    if result.required_action != _required_action(expected_tier):
        raise ValueError("required_action must match escalation_tier")
    if result.context_gap_reasons != expected_reasons:
        raise ValueError("context_gap_reasons must match inputs")
    if result.reason_codes != _reason_codes(input_row, expected_tier):
        raise ValueError("reason_codes must match inputs")


def _normalize_nonnegative_whole_decimal(
    field_name: str,
    value: object,
) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return normalized


def _normalize_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_whole_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_probability(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if not isinstance(value, Decimal):
        raise ValueError(f"{field_name} must be a Decimal")
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value, field_name=field_name)


def _quantize(value: Decimal, *, field_name: str | None = None) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        normalized = value.quantize(VALUE_QUANTUM)
    if field_name is not None and normalized != value:
        raise ValueError(f"{field_name} precision is too granular")
    return normalized


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or value.strip() != value or not value:
        raise ValueError(f"{field_name} must be a nonblank trimmed string")


def _normalize_choice(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> str:
    _require_canonical_string(field_name, value)
    if value not in allowed_values:
        raise ValueError(f"{field_name} must be one of the allowed values")
    return value


def _normalize_context_gap_reasons(value: object) -> tuple[str, ...]:
    return _normalize_string_tuple(
        "context_gap_reasons",
        value,
        CONTEXT_GAP_REASONS,
        allow_empty=True,
    )


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    return _normalize_string_tuple(
        "reason_codes",
        value,
        REASON_CODES,
        allow_empty=False,
    )


def _normalize_string_tuple(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not allow_empty and not value:
        raise ValueError(f"{field_name} must not be empty")
    seen: set[str] = set()
    normalized: list[str] = []
    for item in value:
        _require_canonical_string(field_name, item)
        if item not in allowed_values:
            raise ValueError(f"{field_name} must contain supported values")
        if item in seen:
            raise ValueError(f"{field_name} must be unique")
        seen.add(item)
        normalized.append(item)
    return tuple(normalized)


def _require_paper_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _decimal_payload(value: Decimal) -> str:
    if type(value) is not Decimal:
        raise ValueError("payload decimal must be a Decimal")
    if not value.is_finite():
        raise ValueError("payload decimal must be finite")
    return format(value, "f")
