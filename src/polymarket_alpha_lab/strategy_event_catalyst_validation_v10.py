"""Paper/report-only catalyst validation for probability event markets."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Context, Decimal, localcontext
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


QUANTUM = Decimal("0.000001")
INTEGER_QUANTUM = Decimal("1")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64)

HIGH_OFFICIAL_CONFIRMATION_SCORE = Decimal("0.800000")
PARTIAL_OFFICIAL_CONFIRMATION_SCORE = Decimal("0.500000")
CONFIRMED_SOURCE_QUORUM = Decimal("2.000000")
SINGLE_CONFIRMED_SOURCE = Decimal("1.000000")
RUMOR_SOURCE_CLUSTER = Decimal("2.000000")
MARKET_MOVE_SUPPORT_BPS = Decimal("75.000000")
MAX_CONFIDENCE_ADJUSTMENT = Decimal("0.100000")
MIN_CONFIDENCE_ADJUSTMENT = Decimal("-0.100000")

CATALYST_STATUSES = (
    "confirmed",
    "probable",
    "rumor",
    "timing_mismatch",
    "insufficient_evidence",
)
RESEARCH_ACTIONS = {
    "confirmed": "document_confirmed_catalyst_and_update_research_view",
    "probable": "verify_primary_sources_before_confidence_lift",
    "rumor": "collect_independent_confirmation_before_confidence_lift",
    "timing_mismatch": "exclude_catalyst_until_timing_is_resolved",
    "insufficient_evidence": "keep_on_watchlist_without_confidence_change",
}
CONFIDENCE_ADJUSTMENTS = {
    "confirmed": Decimal("0.100000"),
    "probable": Decimal("0.030000"),
    "rumor": Decimal("-0.040000"),
    "timing_mismatch": Decimal("-0.100000"),
    "insufficient_evidence": Decimal("0.000000"),
}


@dataclass(frozen=True)
class StrategyEventCatalystValidationV10Input:
    catalyst_type: str
    expected_event_time_minutes: Decimal
    confirmed_source_count: Decimal
    rumor_source_count: Decimal
    official_confirmation_score: Decimal
    market_move_bps: Decimal
    time_to_resolution_minutes: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("catalyst_type", self.catalyst_type)
        object.__setattr__(
            self,
            "expected_event_time_minutes",
            _nonnegative_decimal(
                "expected_event_time_minutes",
                self.expected_event_time_minutes,
            ),
        )
        object.__setattr__(
            self,
            "confirmed_source_count",
            _nonnegative_integer_decimal(
                "confirmed_source_count",
                self.confirmed_source_count,
            ),
        )
        object.__setattr__(
            self,
            "rumor_source_count",
            _nonnegative_integer_decimal("rumor_source_count", self.rumor_source_count),
        )
        object.__setattr__(
            self,
            "official_confirmation_score",
            _probability(
                "official_confirmation_score",
                self.official_confirmation_score,
            ),
        )
        object.__setattr__(
            self,
            "market_move_bps",
            _decimal("market_move_bps", self.market_move_bps),
        )
        object.__setattr__(
            self,
            "time_to_resolution_minutes",
            _nonnegative_decimal(
                "time_to_resolution_minutes",
                self.time_to_resolution_minutes,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        reject_unsafe_surface_fields("event catalyst validation input", self)
        require_paper_only_flags("event catalyst validation input", self)


@dataclass(frozen=True)
class StrategyEventCatalystValidationV10Result:
    catalyst_type: str
    expected_event_time_minutes: Decimal
    confirmed_source_count: Decimal
    rumor_source_count: Decimal
    official_confirmation_score: Decimal
    market_move_bps: Decimal
    absolute_market_move_bps: Decimal
    time_to_resolution_minutes: Decimal
    catalyst_status: str
    confidence_adjustment: Decimal
    research_action: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("catalyst_type", self.catalyst_type)
        for field_name in (
            "expected_event_time_minutes",
            "time_to_resolution_minutes",
            "absolute_market_move_bps",
        ):
            object.__setattr__(
                self,
                field_name,
                _nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("confirmed_source_count", "rumor_source_count"):
            object.__setattr__(
                self,
                field_name,
                _nonnegative_integer_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "official_confirmation_score",
            _probability(
                "official_confirmation_score",
                self.official_confirmation_score,
            ),
        )
        object.__setattr__(
            self,
            "market_move_bps",
            _decimal("market_move_bps", self.market_move_bps),
        )
        _require_member("catalyst_status", self.catalyst_status, CATALYST_STATUSES)
        object.__setattr__(
            self,
            "confidence_adjustment",
            _confidence_adjustment(
                "confidence_adjustment",
                self.confidence_adjustment,
            ),
        )
        _require_canonical_string("research_action", self.research_action)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_result_shape(self)
        reject_unsafe_surface_fields("event catalyst validation result", self)
        require_paper_only_flags("event catalyst validation result", self)

    @property
    def payload(self) -> dict[str, Any]:
        return strategy_event_catalyst_validation_v10_payload(self)


def build_strategy_event_catalyst_validation_v10(
    value: StrategyEventCatalystValidationV10Input,
) -> StrategyEventCatalystValidationV10Result:
    if type(value) is not StrategyEventCatalystValidationV10Input:
        raise ValueError("input must be a StrategyEventCatalystValidationV10Input")
    reject_unsafe_surface_fields("event catalyst validation input", value)
    require_paper_only_flags("event catalyst validation input", value)

    absolute_market_move_bps = _absolute_decimal(value.market_move_bps)
    catalyst_status = _catalyst_status(value)
    return StrategyEventCatalystValidationV10Result(
        catalyst_type=value.catalyst_type,
        expected_event_time_minutes=value.expected_event_time_minutes,
        confirmed_source_count=value.confirmed_source_count,
        rumor_source_count=value.rumor_source_count,
        official_confirmation_score=value.official_confirmation_score,
        market_move_bps=value.market_move_bps,
        absolute_market_move_bps=absolute_market_move_bps,
        time_to_resolution_minutes=value.time_to_resolution_minutes,
        catalyst_status=catalyst_status,
        confidence_adjustment=CONFIDENCE_ADJUSTMENTS[catalyst_status],
        research_action=RESEARCH_ACTIONS[catalyst_status],
        reason_codes=_reason_codes(
            value,
            catalyst_status=catalyst_status,
            absolute_market_move_bps=absolute_market_move_bps,
        ),
    )


def strategy_event_catalyst_validation_v10_payload(
    report: StrategyEventCatalystValidationV10Result,
) -> dict[str, Any]:
    if type(report) is not StrategyEventCatalystValidationV10Result:
        raise ValueError("report must be a StrategyEventCatalystValidationV10Result")
    require_paper_only_flags("event catalyst validation result", report)
    reject_unsafe_surface_fields("event catalyst validation result", report)
    return json_ready_no_floats(
        {
            "catalyst_type": report.catalyst_type,
            "expected_event_time_minutes": report.expected_event_time_minutes,
            "confirmed_source_count": report.confirmed_source_count,
            "rumor_source_count": report.rumor_source_count,
            "official_confirmation_score": report.official_confirmation_score,
            "market_move_bps": report.market_move_bps,
            "absolute_market_move_bps": report.absolute_market_move_bps,
            "time_to_resolution_minutes": report.time_to_resolution_minutes,
            "catalyst_status": report.catalyst_status,
            "confidence_adjustment": report.confidence_adjustment,
            "research_action": report.research_action,
            "reason_codes": report.reason_codes,
            "paper_only": report.paper_only,
            "report_only": report.report_only,
            "readonly": report.readonly,
        },
    )


def _catalyst_status(value: StrategyEventCatalystValidationV10Input) -> str:
    if value.expected_event_time_minutes > value.time_to_resolution_minutes:
        return "timing_mismatch"
    if (
        value.official_confirmation_score >= HIGH_OFFICIAL_CONFIRMATION_SCORE
        and value.confirmed_source_count >= CONFIRMED_SOURCE_QUORUM
    ):
        return "confirmed"
    if (
        value.confirmed_source_count == ZERO
        and value.rumor_source_count >= RUMOR_SOURCE_CLUSTER
        and value.official_confirmation_score < PARTIAL_OFFICIAL_CONFIRMATION_SCORE
    ):
        return "rumor"
    if (
        value.official_confirmation_score >= PARTIAL_OFFICIAL_CONFIRMATION_SCORE
        or value.confirmed_source_count >= SINGLE_CONFIRMED_SOURCE
        or value.rumor_source_count >= RUMOR_SOURCE_CLUSTER
    ):
        return "probable"
    return "insufficient_evidence"


def _reason_codes(
    value: StrategyEventCatalystValidationV10Input,
    *,
    catalyst_status: str,
    absolute_market_move_bps: Decimal,
) -> tuple[str, ...]:
    if catalyst_status == "timing_mismatch":
        reason_codes = ["event_expected_after_resolution"]
        reason_codes.extend(_official_confirmation_reasons(value, include_low=True))
        reason_codes.extend(_source_confirmation_reasons(value, include_empty=True))
        reason_codes.extend(_market_move_reasons(value, absolute_market_move_bps))
        return _dedupe((*reason_codes, *value.reason_codes))

    if catalyst_status == "confirmed":
        reason_codes = [
            "official_confirmation_high",
            "confirmed_source_quorum_met",
        ]
        reason_codes.extend(_market_move_reasons(value, absolute_market_move_bps))
        reason_codes.append("catalyst_timing_before_resolution")
        return _dedupe((*reason_codes, *value.reason_codes))

    if catalyst_status == "probable":
        reason_codes = []
        reason_codes.extend(_official_confirmation_reasons(value, include_low=False))
        reason_codes.extend(_source_confirmation_reasons(value, include_empty=False))
        if value.rumor_source_count >= RUMOR_SOURCE_CLUSTER:
            reason_codes.append("rumor_source_cluster")
        reason_codes.extend(_market_move_reasons(value, absolute_market_move_bps))
        reason_codes.append("catalyst_timing_before_resolution")
        return _dedupe((*reason_codes, *value.reason_codes))

    if catalyst_status == "rumor":
        reason_codes = ["rumor_sources_without_confirmation"]
        if absolute_market_move_bps >= MARKET_MOVE_SUPPORT_BPS:
            reason_codes.append("market_move_without_official_confirmation")
        reason_codes.append("catalyst_timing_before_resolution")
        return _dedupe((*reason_codes, *value.reason_codes))

    reason_codes = []
    if value.confirmed_source_count == ZERO and value.rumor_source_count == ZERO:
        reason_codes.append("no_catalyst_sources")
    reason_codes.extend(_official_confirmation_reasons(value, include_low=True))
    reason_codes.append("catalyst_timing_before_resolution")
    return _dedupe((*reason_codes, *value.reason_codes))


def _official_confirmation_reasons(
    value: StrategyEventCatalystValidationV10Input,
    *,
    include_low: bool,
) -> tuple[str, ...]:
    if value.official_confirmation_score >= HIGH_OFFICIAL_CONFIRMATION_SCORE:
        return ("official_confirmation_high",)
    if value.official_confirmation_score >= PARTIAL_OFFICIAL_CONFIRMATION_SCORE:
        return ("official_confirmation_partial",)
    if include_low:
        return ("low_official_confirmation",)
    return ()


def _source_confirmation_reasons(
    value: StrategyEventCatalystValidationV10Input,
    *,
    include_empty: bool,
) -> tuple[str, ...]:
    if value.confirmed_source_count >= CONFIRMED_SOURCE_QUORUM:
        return ("confirmed_source_quorum_met",)
    if value.confirmed_source_count == SINGLE_CONFIRMED_SOURCE:
        return ("single_confirmed_source",)
    if include_empty and value.rumor_source_count == ZERO:
        return ("no_catalyst_sources",)
    return ()


def _market_move_reasons(
    value: StrategyEventCatalystValidationV10Input,
    absolute_market_move_bps: Decimal,
) -> tuple[str, ...]:
    if (
        absolute_market_move_bps >= MARKET_MOVE_SUPPORT_BPS
        and (
            value.confirmed_source_count > ZERO
            or value.official_confirmation_score >= PARTIAL_OFFICIAL_CONFIRMATION_SCORE
        )
    ):
        return ("market_move_supports_catalyst",)
    return ()


def _validate_result_shape(result: StrategyEventCatalystValidationV10Result) -> None:
    if result.absolute_market_move_bps != _absolute_decimal(result.market_move_bps):
        raise ValueError("absolute_market_move_bps must match market_move_bps")
    if result.research_action != RESEARCH_ACTIONS[result.catalyst_status]:
        raise ValueError("research_action must match catalyst_status")
    expected_confidence_adjustment = CONFIDENCE_ADJUSTMENTS[result.catalyst_status]
    if result.confidence_adjustment != expected_confidence_adjustment:
        raise ValueError("confidence_adjustment must match catalyst_status")


def _absolute_decimal(value: Decimal) -> Decimal:
    if value < ZERO:
        return _quantize(-value)
    return _quantize(value)


def _confidence_adjustment(name: str, value: object) -> Decimal:
    decimal = _decimal(name, value)
    if decimal < MIN_CONFIDENCE_ADJUSTMENT or decimal > MAX_CONFIDENCE_ADJUSTMENT:
        raise ValueError(f"{name} must be between -0.100000 and 0.100000")
    return decimal


def _probability(name: str, value: object) -> Decimal:
    decimal = _decimal(name, value)
    if decimal < ZERO or decimal > ONE:
        raise ValueError(f"{name} must be between 0 and 1")
    return decimal


def _nonnegative_decimal(name: str, value: object) -> Decimal:
    decimal = _decimal(name, value)
    if decimal < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return decimal


def _nonnegative_integer_decimal(name: str, value: object) -> Decimal:
    decimal = _nonnegative_decimal(name, value)
    if decimal != decimal.quantize(INTEGER_QUANTUM):
        raise ValueError(f"{name} must be an integer Decimal")
    return decimal


def _decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    return _quantize(value)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _normalize_reason_codes(
    name: str,
    value: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{name} must be a tuple")
    for reason_code in value:
        _require_canonical_string(name, reason_code)
    return _dedupe(value)


def _dedupe(values: tuple[str, ...]) -> tuple[str, ...]:
    result: list[str] = []
    seen_values: set[str] = set()
    for value in values:
        if value not in seen_values:
            result.append(value)
            seen_values.add(value)
    return tuple(result)


def _require_member(name: str, value: object, allowed_values: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed_values:
        joined_values = ", ".join(allowed_values)
        raise ValueError(f"{name} must be one of: {joined_values}")


def _require_canonical_string(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{name} must be a canonical nonblank string")


__all__ = (
    "StrategyEventCatalystValidationV10Input",
    "StrategyEventCatalystValidationV10Result",
    "build_strategy_event_catalyst_validation_v10",
    "strategy_event_catalyst_validation_v10_payload",
)
