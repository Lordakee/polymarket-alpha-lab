"""Paper-only readonly event resolution uncertainty band strategy."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
HALF = Decimal("0.500000")

AMBIGUITY_BPS_WEIGHT = Decimal("1800.000000")
PRECEDENT_GAP_BPS_WEIGHT = Decimal("1100.000000")
SOURCE_DISAGREEMENT_BPS_WEIGHT = Decimal("1300.000000")
HISTORICAL_DISPUTE_BPS_WEIGHT = Decimal("4000.000000")
RULE_CHANGE_PROPOSED_BPS = Decimal("400.000000")
RULE_CHANGE_CONFIRMED_BPS = Decimal("2500.000000")
IMMEDIATE_TIME_WINDOW_BPS = Decimal("900.000000")
SHORT_TIME_WINDOW_BPS = Decimal("292.000000")
NEAR_TIME_WINDOW_BPS = Decimal("150.000000")
LONG_TIME_WINDOW_BPS = Decimal("25.000000")
MAX_UNCERTAINTY_BPS = Decimal("8000.000000")

AMBIGUITY_ELEVATED_THRESHOLD = Decimal("0.600000")
SOURCE_DISAGREEMENT_ELEVATED_THRESHOLD = Decimal("0.600000")
HISTORICAL_DISPUTE_ELEVATED_THRESHOLD = Decimal("0.100000")
STRONG_PRECEDENT_THRESHOLD = Decimal("0.750000")
BLOCK_THRESHOLD_BPS = Decimal("8000.000000")
ELEVATED_THRESHOLD_BPS = Decimal("3000.000000")
WATCH_THRESHOLD_BPS = Decimal("1500.000000")
IMMEDIATE_RESOLUTION_MINUTES = Decimal("60.000000")
SHORT_RESOLUTION_MINUTES = Decimal("360.000000")
NEAR_RESOLUTION_MINUTES = Decimal("1440.000000")

RULE_CHANGE_NONE = "none"
RULE_CHANGE_PROPOSED = "proposed"
RULE_CHANGE_CONFIRMED = "confirmed"
RULE_CHANGE_STATUSES = (
    RULE_CHANGE_NONE,
    RULE_CHANGE_PROPOSED,
    RULE_CHANGE_CONFIRMED,
)
UNCERTAINTY_STATUSES = ("ok", "watch", "elevated", "block")


@dataclass(frozen=True)
class StrategyEventResolutionUncertaintyBandV10Input:
    market_id: str
    resolution_ambiguity_score: Decimal
    precedent_score: Decimal
    rule_change_status: str
    source_disagreement_score: Decimal
    time_to_resolution_minutes: Decimal
    historical_dispute_rate: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("market_id", self.market_id)
        for field_name in (
            "resolution_ambiguity_score",
            "precedent_score",
            "source_disagreement_score",
            "historical_dispute_rate",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_member(
            "rule_change_status",
            self.rule_change_status,
            RULE_CHANGE_STATUSES,
        )
        object.__setattr__(
            self,
            "time_to_resolution_minutes",
            _normalize_nonnegative_decimal(
                "time_to_resolution_minutes",
                self.time_to_resolution_minutes,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        reject_unsafe_surface_fields("event resolution uncertainty input", self)
        require_paper_only_flags("event resolution uncertainty input", self)


@dataclass(frozen=True)
class StrategyEventResolutionUncertaintyBandV10Result:
    market_id: str
    resolution_ambiguity_score: Decimal
    precedent_score: Decimal
    rule_change_status: str
    source_disagreement_score: Decimal
    time_to_resolution_minutes: Decimal
    historical_dispute_rate: Decimal
    uncertainty_status: str
    lower_confidence_adjustment_bps: Decimal
    upper_confidence_adjustment_bps: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("market_id", self.market_id)
        for field_name in (
            "resolution_ambiguity_score",
            "precedent_score",
            "source_disagreement_score",
            "historical_dispute_rate",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_member(
            "rule_change_status",
            self.rule_change_status,
            RULE_CHANGE_STATUSES,
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
            "uncertainty_status",
            self.uncertainty_status,
            UNCERTAINTY_STATUSES,
        )
        object.__setattr__(
            self,
            "lower_confidence_adjustment_bps",
            _normalize_lower_adjustment_bps(
                "lower_confidence_adjustment_bps",
                self.lower_confidence_adjustment_bps,
            ),
        )
        object.__setattr__(
            self,
            "upper_confidence_adjustment_bps",
            _normalize_upper_adjustment_bps(
                "upper_confidence_adjustment_bps",
                self.upper_confidence_adjustment_bps,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        reject_unsafe_surface_fields("event resolution uncertainty result", self)
        require_paper_only_flags("event resolution uncertainty result", self)

    @property
    def payload(self) -> dict[str, Any]:
        return strategy_event_resolution_uncertainty_band_v10_payload(self)


def evaluate_strategy_event_resolution_uncertainty_band_v10(
    resolution: StrategyEventResolutionUncertaintyBandV10Input,
) -> StrategyEventResolutionUncertaintyBandV10Result:
    if type(resolution) is not StrategyEventResolutionUncertaintyBandV10Input:
        raise ValueError(
            "resolution must be a StrategyEventResolutionUncertaintyBandV10Input",
        )
    require_paper_only_flags("event resolution uncertainty input", resolution)
    reject_unsafe_surface_fields("event resolution uncertainty input", resolution)

    uncertainty_bps = _uncertainty_bps(resolution)
    uncertainty_status = _uncertainty_status(uncertainty_bps)
    return StrategyEventResolutionUncertaintyBandV10Result(
        market_id=resolution.market_id,
        resolution_ambiguity_score=resolution.resolution_ambiguity_score,
        precedent_score=resolution.precedent_score,
        rule_change_status=resolution.rule_change_status,
        source_disagreement_score=resolution.source_disagreement_score,
        time_to_resolution_minutes=resolution.time_to_resolution_minutes,
        historical_dispute_rate=resolution.historical_dispute_rate,
        uncertainty_status=uncertainty_status,
        lower_confidence_adjustment_bps=_quantize_decimal(
            "lower_confidence_adjustment_bps",
            ZERO - uncertainty_bps,
        ),
        upper_confidence_adjustment_bps=_quantize_decimal(
            "upper_confidence_adjustment_bps",
            uncertainty_bps * HALF,
        ),
        reason_codes=_reason_codes(
            resolution.reason_codes,
            resolution=resolution,
            uncertainty_status=uncertainty_status,
        ),
    )


def strategy_event_resolution_uncertainty_band_v10_payload(
    result: StrategyEventResolutionUncertaintyBandV10Result,
) -> dict[str, Any]:
    if type(result) is not StrategyEventResolutionUncertaintyBandV10Result:
        raise ValueError(
            "result must be a StrategyEventResolutionUncertaintyBandV10Result",
        )
    require_paper_only_flags("event resolution uncertainty result", result)
    reject_unsafe_surface_fields("event resolution uncertainty result", result)
    return json_ready_no_floats(
        {
            "market_id": result.market_id,
            "resolution_ambiguity_score": result.resolution_ambiguity_score,
            "precedent_score": result.precedent_score,
            "rule_change_status": result.rule_change_status,
            "source_disagreement_score": result.source_disagreement_score,
            "time_to_resolution_minutes": result.time_to_resolution_minutes,
            "historical_dispute_rate": result.historical_dispute_rate,
            "uncertainty_status": result.uncertainty_status,
            "lower_confidence_adjustment_bps": (
                result.lower_confidence_adjustment_bps
            ),
            "upper_confidence_adjustment_bps": (
                result.upper_confidence_adjustment_bps
            ),
            "reason_codes": result.reason_codes,
            "paper_only": result.paper_only,
            "report_only": result.report_only,
            "readonly": result.readonly,
        },
    )


def _uncertainty_bps(
    resolution: StrategyEventResolutionUncertaintyBandV10Input,
) -> Decimal:
    precedent_gap = _quantize_decimal(
        "precedent_gap",
        ONE - resolution.precedent_score,
    )
    raw_bps = (
        resolution.resolution_ambiguity_score * AMBIGUITY_BPS_WEIGHT
        + precedent_gap * PRECEDENT_GAP_BPS_WEIGHT
        + resolution.source_disagreement_score * SOURCE_DISAGREEMENT_BPS_WEIGHT
        + resolution.historical_dispute_rate * HISTORICAL_DISPUTE_BPS_WEIGHT
        + _rule_change_bps(resolution.rule_change_status)
        + _time_window_bps(resolution.time_to_resolution_minutes)
    )
    capped_bps = min(_quantize_decimal("uncertainty_bps", raw_bps), MAX_UNCERTAINTY_BPS)
    return _quantize_decimal("uncertainty_bps", capped_bps)


def _rule_change_bps(rule_change_status: str) -> Decimal:
    if rule_change_status == RULE_CHANGE_CONFIRMED:
        return RULE_CHANGE_CONFIRMED_BPS
    if rule_change_status == RULE_CHANGE_PROPOSED:
        return RULE_CHANGE_PROPOSED_BPS
    return ZERO


def _time_window_bps(time_to_resolution_minutes: Decimal) -> Decimal:
    if time_to_resolution_minutes <= IMMEDIATE_RESOLUTION_MINUTES:
        return IMMEDIATE_TIME_WINDOW_BPS
    if time_to_resolution_minutes <= SHORT_RESOLUTION_MINUTES:
        return SHORT_TIME_WINDOW_BPS
    if time_to_resolution_minutes <= NEAR_RESOLUTION_MINUTES:
        return NEAR_TIME_WINDOW_BPS
    return LONG_TIME_WINDOW_BPS


def _uncertainty_status(uncertainty_bps: Decimal) -> str:
    if uncertainty_bps >= BLOCK_THRESHOLD_BPS:
        return "block"
    if uncertainty_bps >= ELEVATED_THRESHOLD_BPS:
        return "elevated"
    if uncertainty_bps >= WATCH_THRESHOLD_BPS:
        return "watch"
    return "ok"


def _reason_codes(
    existing: tuple[str, ...],
    *,
    resolution: StrategyEventResolutionUncertaintyBandV10Input,
    uncertainty_status: str,
) -> tuple[str, ...]:
    additions = ["event_resolution_uncertainty_band_v10"]
    if resolution.resolution_ambiguity_score >= AMBIGUITY_ELEVATED_THRESHOLD:
        additions.append("ambiguity_score_elevated")
    if resolution.source_disagreement_score >= SOURCE_DISAGREEMENT_ELEVATED_THRESHOLD:
        additions.append("source_disagreement_elevated")
    if resolution.precedent_score >= STRONG_PRECEDENT_THRESHOLD:
        additions.append("strong_precedent_support")
    if resolution.rule_change_status == RULE_CHANGE_PROPOSED:
        additions.append("rule_change_proposed")
    if resolution.rule_change_status == RULE_CHANGE_CONFIRMED:
        additions.append("rule_change_confirmed")
    if resolution.time_to_resolution_minutes <= SHORT_RESOLUTION_MINUTES:
        additions.append("short_time_to_resolution")
    if resolution.historical_dispute_rate >= HISTORICAL_DISPUTE_ELEVATED_THRESHOLD:
        additions.append("historical_dispute_rate_elevated")
    additions.append(f"uncertainty_{uncertainty_status}")
    return _append_reason_codes(existing, tuple(additions))


def _append_reason_codes(
    existing: tuple[str, ...],
    additions: tuple[str, ...],
) -> tuple[str, ...]:
    values = list(existing)
    for addition in additions:
        if addition not in values:
            values.append(addition)
    return tuple(values)


def _normalize_reason_codes(field_name: str, value: Any) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    for reason_code in value:
        _require_canonical_string(field_name, reason_code)
    return value


def _normalize_probability(field_name: str, value: Any) -> Decimal:
    decimal = _normalize_decimal(field_name, value)
    if decimal < ZERO or decimal > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return decimal


def _normalize_nonnegative_decimal(field_name: str, value: Any) -> Decimal:
    decimal = _normalize_decimal(field_name, value)
    if decimal < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal


def _normalize_lower_adjustment_bps(field_name: str, value: Any) -> Decimal:
    decimal = _normalize_decimal(field_name, value)
    if decimal > ZERO:
        raise ValueError(f"{field_name} must be nonpositive")
    return decimal


def _normalize_upper_adjustment_bps(field_name: str, value: Any) -> Decimal:
    decimal = _normalize_decimal(field_name, value)
    if decimal < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal


def _normalize_decimal(field_name: str, value: Any) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    return _quantize_decimal(field_name, value)


def _quantize_decimal(field_name: str, value: Decimal) -> Decimal:
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value.quantize(QUANTUM)


def _require_member(
    field_name: str,
    value: Any,
    allowed_values: tuple[str, ...],
) -> None:
    _require_canonical_string(field_name, value)
    if value not in allowed_values:
        raise ValueError(f"{field_name} must be one of {', '.join(allowed_values)}")


def _require_canonical_string(field_name: str, value: Any) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


__all__ = (
    "RULE_CHANGE_CONFIRMED",
    "RULE_CHANGE_NONE",
    "RULE_CHANGE_PROPOSED",
    "RULE_CHANGE_STATUSES",
    "StrategyEventResolutionUncertaintyBandV10Input",
    "StrategyEventResolutionUncertaintyBandV10Result",
    "evaluate_strategy_event_resolution_uncertainty_band_v10",
    "strategy_event_resolution_uncertainty_band_v10_payload",
)
