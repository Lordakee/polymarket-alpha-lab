"""Pure read-only market/source disagreement triage v10 reducer."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any


__all__ = (
    "StrategyMarketSourceDisagreementTriageV10Input",
    "StrategyMarketSourceDisagreementTriageV10Result",
    "evaluate_strategy_market_source_disagreement_triage_v10",
    "strategy_market_source_disagreement_triage_v10_payload",
)


RATIO_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
THREE = Decimal("3.000000")
WATCH_SOURCE_SPREAD = Decimal("0.100000")
DIVERGENT_SOURCE_SPREAD = Decimal("0.200000")
CRITICAL_SOURCE_SPREAD = Decimal("0.300000")
WATCH_OFFICIAL_MARKET_GAP = Decimal("0.100000")
DIVERGENT_OFFICIAL_MARKET_GAP = Decimal("0.200000")
CRITICAL_OFFICIAL_MARKET_GAP = Decimal("0.500000")
WATCH_MARKET_SOURCE_MEAN_GAP = Decimal("0.150000")
DIVERGENT_MARKET_SOURCE_MEAN_GAP = Decimal("0.250000")
LOW_SOURCE_RELIABILITY = Decimal("0.600000")
IMMINENT_RESOLUTION_MINUTES = Decimal("60.000000")
NEAR_RESOLUTION_MINUTES = Decimal("240.000000")
WATCH_PENALTY_WEIGHT = Decimal("0.640000")
RELIABILITY_RISK_PENALTY_WEIGHT = Decimal("0.080000")
NEAR_RESOLUTION_PENALTY = Decimal("0.006000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

DISAGREEMENT_STATUSES = ("aligned", "watch", "divergent", "critical")
TRIAGE_ACTIONS = (
    "keep_report_signal",
    "queue_source_recheck",
    "escalate_source_review",
    "quarantine_probability_signal",
)


@dataclass(frozen=True)
class StrategyMarketSourceDisagreementTriageV10Input:
    official_source_probability: Decimal
    primary_source_probability: Decimal
    secondary_source_probability: Decimal
    market_price_probability: Decimal
    source_reliability_weight: Decimal
    time_to_resolution_minutes: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "official_source_probability",
            "primary_source_probability",
            "secondary_source_probability",
            "market_price_probability",
            "source_reliability_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "time_to_resolution_minutes",
            _normalize_nonnegative_decimal(
                "time_to_resolution_minutes",
                self.time_to_resolution_minutes,
            ),
        )
        _require_safety_flags("input", self)


@dataclass(frozen=True)
class StrategyMarketSourceDisagreementTriageV10Result:
    official_source_probability: Decimal
    primary_source_probability: Decimal
    secondary_source_probability: Decimal
    market_price_probability: Decimal
    source_reliability_weight: Decimal
    time_to_resolution_minutes: Decimal
    source_spread: Decimal
    official_market_gap: Decimal
    market_source_mean_gap: Decimal
    disagreement_status: str
    triage_action: str
    confidence_penalty: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "official_source_probability",
            "primary_source_probability",
            "secondary_source_probability",
            "market_price_probability",
            "source_reliability_weight",
            "source_spread",
            "official_market_gap",
            "market_source_mean_gap",
            "confidence_penalty",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "time_to_resolution_minutes",
            _normalize_nonnegative_decimal(
                "time_to_resolution_minutes",
                self.time_to_resolution_minutes,
            ),
        )
        _require_member(
            "disagreement_status",
            self.disagreement_status,
            DISAGREEMENT_STATUSES,
        )
        _require_member("triage_action", self.triage_action, TRIAGE_ACTIONS)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, require_nonempty=True),
        )
        _require_safety_flags("result", self)

    @property
    def payload(self) -> dict[str, Any]:
        return strategy_market_source_disagreement_triage_v10_payload(self)


def evaluate_strategy_market_source_disagreement_triage_v10(
    source_disagreement: StrategyMarketSourceDisagreementTriageV10Input,
) -> StrategyMarketSourceDisagreementTriageV10Result:
    if type(source_disagreement) is not StrategyMarketSourceDisagreementTriageV10Input:
        raise ValueError(
            "source_disagreement must be a "
            "StrategyMarketSourceDisagreementTriageV10Input",
        )
    _require_safety_flags("source_disagreement", source_disagreement)

    source_spread = _source_spread(source_disagreement)
    official_market_gap = _gap(
        source_disagreement.official_source_probability,
        source_disagreement.market_price_probability,
    )
    market_source_mean_gap = _market_source_mean_gap(source_disagreement)
    disagreement_status = _disagreement_status(
        source_spread=source_spread,
        official_market_gap=official_market_gap,
        market_source_mean_gap=market_source_mean_gap,
    )

    return StrategyMarketSourceDisagreementTriageV10Result(
        official_source_probability=source_disagreement.official_source_probability,
        primary_source_probability=source_disagreement.primary_source_probability,
        secondary_source_probability=source_disagreement.secondary_source_probability,
        market_price_probability=source_disagreement.market_price_probability,
        source_reliability_weight=source_disagreement.source_reliability_weight,
        time_to_resolution_minutes=source_disagreement.time_to_resolution_minutes,
        source_spread=source_spread,
        official_market_gap=official_market_gap,
        market_source_mean_gap=market_source_mean_gap,
        disagreement_status=disagreement_status,
        triage_action=_triage_action(disagreement_status),
        confidence_penalty=_confidence_penalty(
            source_disagreement,
            source_spread=source_spread,
            official_market_gap=official_market_gap,
            market_source_mean_gap=market_source_mean_gap,
            disagreement_status=disagreement_status,
        ),
        reason_codes=_reason_codes(
            source_disagreement,
            source_spread=source_spread,
            official_market_gap=official_market_gap,
            market_source_mean_gap=market_source_mean_gap,
            disagreement_status=disagreement_status,
        ),
    )


def strategy_market_source_disagreement_triage_v10_payload(
    result: StrategyMarketSourceDisagreementTriageV10Result,
) -> dict[str, Any]:
    if type(result) is not StrategyMarketSourceDisagreementTriageV10Result:
        raise ValueError(
            "result must be a StrategyMarketSourceDisagreementTriageV10Result",
        )
    _require_safety_flags("result", result)
    return {
        "official_source_probability": _decimal_payload(
            result.official_source_probability,
        ),
        "primary_source_probability": _decimal_payload(
            result.primary_source_probability,
        ),
        "secondary_source_probability": _decimal_payload(
            result.secondary_source_probability,
        ),
        "market_price_probability": _decimal_payload(result.market_price_probability),
        "source_reliability_weight": _decimal_payload(
            result.source_reliability_weight,
        ),
        "time_to_resolution_minutes": _decimal_payload(
            result.time_to_resolution_minutes,
        ),
        "source_spread": _decimal_payload(result.source_spread),
        "official_market_gap": _decimal_payload(result.official_market_gap),
        "market_source_mean_gap": _decimal_payload(result.market_source_mean_gap),
        "disagreement_status": result.disagreement_status,
        "triage_action": result.triage_action,
        "confidence_penalty": _decimal_payload(result.confidence_penalty),
        "reason_codes": list(result.reason_codes),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _source_spread(
    source_disagreement: StrategyMarketSourceDisagreementTriageV10Input,
) -> Decimal:
    probabilities = (
        source_disagreement.official_source_probability,
        source_disagreement.primary_source_probability,
        source_disagreement.secondary_source_probability,
    )
    return _quantize_decimal("source_spread", max(probabilities) - min(probabilities))


def _market_source_mean_gap(
    source_disagreement: StrategyMarketSourceDisagreementTriageV10Input,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        source_mean = (
            source_disagreement.official_source_probability
            + source_disagreement.primary_source_probability
            + source_disagreement.secondary_source_probability
        ) / THREE
        return _gap(source_mean, source_disagreement.market_price_probability)


def _gap(left_probability: Decimal, right_probability: Decimal) -> Decimal:
    return _quantize_decimal(
        "probability_gap",
        abs(left_probability - right_probability),
    )


def _disagreement_status(
    *,
    source_spread: Decimal,
    official_market_gap: Decimal,
    market_source_mean_gap: Decimal,
) -> str:
    if (
        source_spread >= CRITICAL_SOURCE_SPREAD
        or official_market_gap >= CRITICAL_OFFICIAL_MARKET_GAP
    ):
        return "critical"
    if (
        source_spread >= DIVERGENT_SOURCE_SPREAD
        or official_market_gap >= DIVERGENT_OFFICIAL_MARKET_GAP
        or market_source_mean_gap >= DIVERGENT_MARKET_SOURCE_MEAN_GAP
    ):
        return "divergent"
    if (
        source_spread >= WATCH_SOURCE_SPREAD
        or official_market_gap >= WATCH_OFFICIAL_MARKET_GAP
        or market_source_mean_gap >= WATCH_MARKET_SOURCE_MEAN_GAP
    ):
        return "watch"
    return "aligned"


def _triage_action(disagreement_status: str) -> str:
    if disagreement_status == "critical":
        return "quarantine_probability_signal"
    if disagreement_status == "divergent":
        return "escalate_source_review"
    if disagreement_status == "watch":
        return "queue_source_recheck"
    return "keep_report_signal"


def _confidence_penalty(
    source_disagreement: StrategyMarketSourceDisagreementTriageV10Input,
    *,
    source_spread: Decimal,
    official_market_gap: Decimal,
    market_source_mean_gap: Decimal,
    disagreement_status: str,
) -> Decimal:
    if disagreement_status == "aligned":
        return ZERO
    penalty_basis = max(source_spread, official_market_gap, market_source_mean_gap)
    if disagreement_status == "critical":
        return _cap_probability(penalty_basis)
    with localcontext(DECIMAL_CONTEXT):
        penalty = penalty_basis * WATCH_PENALTY_WEIGHT
        if disagreement_status == "divergent":
            reliability_gap = ONE - source_disagreement.source_reliability_weight
            penalty += reliability_gap * RELIABILITY_RISK_PENALTY_WEIGHT
            if source_disagreement.time_to_resolution_minutes <= NEAR_RESOLUTION_MINUTES:
                penalty += NEAR_RESOLUTION_PENALTY
        return _cap_probability(penalty)


def _reason_codes(
    source_disagreement: StrategyMarketSourceDisagreementTriageV10Input,
    *,
    source_spread: Decimal,
    official_market_gap: Decimal,
    market_source_mean_gap: Decimal,
    disagreement_status: str,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if disagreement_status == "aligned":
        reason_codes.append("market_sources_aligned")
    else:
        reason_codes.append(f"market_source_disagreement_{disagreement_status}")
    if source_spread >= CRITICAL_SOURCE_SPREAD:
        reason_codes.append("source_spread_critical")
    elif disagreement_status == "watch" and source_spread >= WATCH_SOURCE_SPREAD:
        reason_codes.append("source_spread_watch")
    elif disagreement_status == "divergent" and source_spread >= DIVERGENT_SOURCE_SPREAD:
        reason_codes.append("source_spread_divergent")
    if official_market_gap >= CRITICAL_OFFICIAL_MARKET_GAP:
        reason_codes.append("official_market_gap_critical")
    elif official_market_gap >= DIVERGENT_OFFICIAL_MARKET_GAP:
        reason_codes.append("official_market_gap_divergent")
    elif disagreement_status == "watch" and official_market_gap >= WATCH_OFFICIAL_MARKET_GAP:
        reason_codes.append("official_market_gap_watch")
    if market_source_mean_gap >= DIVERGENT_MARKET_SOURCE_MEAN_GAP:
        reason_codes.append("market_source_mean_gap_divergent")
    elif market_source_mean_gap >= WATCH_MARKET_SOURCE_MEAN_GAP:
        reason_codes.append("market_source_mean_gap_watch")
    if source_disagreement.source_reliability_weight <= LOW_SOURCE_RELIABILITY:
        reason_codes.append("source_reliability_low")
    if source_disagreement.time_to_resolution_minutes <= IMMINENT_RESOLUTION_MINUTES:
        reason_codes.append("resolution_imminent")
    elif source_disagreement.time_to_resolution_minutes <= NEAR_RESOLUTION_MINUTES:
        reason_codes.append("resolution_near")
    return _normalize_reason_codes(tuple(reason_codes), require_nonempty=True)


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
    return _quantize_decimal("confidence_penalty", value)


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
    for field_name in ("paper_only", "report_only", "readonly"):
        if not hasattr(value, field_name):
            raise ValueError(f"{label} must expose {field_name}")
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True")


def _decimal_payload(value: Decimal) -> str:
    if type(value) is not Decimal:
        raise ValueError("payload decimal must be a Decimal")
    return format(value, "f")
