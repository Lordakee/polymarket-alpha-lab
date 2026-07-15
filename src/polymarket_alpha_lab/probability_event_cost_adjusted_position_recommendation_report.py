"""Read-only cost-adjusted position recommendation report for probability events."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from hashlib import sha256
import json
from re import Pattern, compile
from typing import Mapping


__all__ = (
    "PROBABILITY_EVENT_COST_ADJUSTED_POSITION_RECOMMENDATION_REPORT_VERSION",
    "ProbabilityEventCostAdjustedPositionRecommendationInput",
    "ProbabilityEventCostAdjustedPositionRecommendationReport",
    "build_probability_event_cost_adjusted_position_recommendation_report",
    "probability_event_cost_adjusted_position_recommendation_report_payload",
    "probability_event_cost_adjusted_position_recommendation_report_digest",
)


PROBABILITY_EVENT_COST_ADJUSTED_POSITION_RECOMMENDATION_REPORT_VERSION = (
    "probability-event-cost-adjusted-position-recommendation-v0"
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DAYS_IN_YEAR = Decimal("365.000000")
EXTENDED_SETTLEMENT_DAYS = Decimal("30.000000")
WATCH_MARGIN_OF_SAFETY = Decimal("0.010000")
DIGEST_RE: Pattern[str] = compile(r"^[0-9a-f]{64}$")

OUTCOME_SIDES = ("yes", "no")
READINESS_STATUSES = ("pass", "watch", "blocked")
CAPITAL_LOCKUP_HINTS = (
    "standard_capital_lockup_review",
    "extended_settlement_delay_capital_locked",
)
MANUAL_NEXT_STEPS = (
    "document_phase1_readonly_position_boundary",
    "manual_review_costs_lockup_and_position_cap",
    "do_not_size_until_cost_adjusted_ev_improves",
)
REASON_CODES = (
    "cost_adjusted_expected_value_positive",
    "cost_adjusted_expected_value_not_positive",
    "cost_adjusted_break_even_exceeds_probability_ceiling",
    "margin_of_safety_positive",
    "margin_of_safety_not_positive",
    "kelly_upper_bound_manual_cap_applied",
    "kelly_upper_bound_below_manual_cap",
    "kelly_upper_bound_zero",
    "capital_lockup_cost_present",
    "extended_settlement_delay_capital_lockup_watch",
    "margin_of_safety_below_watch_threshold",
)
PROBABILITY_FIELDS = (
    "forecast_probability",
    "market_probability",
    "taker_fee_probability",
    "spread_probability",
    "slippage_probability",
    "annual_capital_charge_probability",
    "uncertainty_buffer_probability",
    "manual_fraction_cap_probability",
)
REPORT_DECIMAL_FIELDS = (
    *PROBABILITY_FIELDS,
    "settlement_delay_days",
    "capital_lockup_cost_probability",
    "cost_adjusted_break_even_probability",
    "expected_value_probability",
    "margin_of_safety_probability",
    "kelly_upper_bound_probability",
    "recommended_position_fraction_probability",
)
PAYLOAD_KEYS = (
    "config_version",
    "event_id",
    "market_slug",
    "outcome_side",
    "readiness_status",
    "forecast_probability",
    "market_probability",
    "taker_fee_probability",
    "spread_probability",
    "slippage_probability",
    "settlement_delay_days",
    "annual_capital_charge_probability",
    "capital_lockup_cost_probability",
    "cost_adjusted_break_even_probability",
    "expected_value_probability",
    "uncertainty_buffer_probability",
    "margin_of_safety_probability",
    "kelly_upper_bound_probability",
    "manual_fraction_cap_probability",
    "recommended_position_fraction_probability",
    "capital_lockup_hint",
    "reason_codes",
    "manual_next_step",
    "paper_only",
    "report_only",
    "readonly",
    "payload_digest",
)


class ProbabilityEventCostAdjustedPositionRecommendationPublicPayload(dict[str, object]):
    """Immutable public payload for the position recommendation report."""

    def __readonly(self, *args: object, **kwargs: object) -> None:
        raise TypeError("public_payload is immutable")

    __setitem__ = __readonly
    __delitem__ = __readonly
    clear = __readonly
    pop = __readonly
    popitem = __readonly
    setdefault = __readonly
    update = __readonly
    __ior__ = __readonly


@dataclass(frozen=True)
class ProbabilityEventCostAdjustedPositionRecommendationInput:
    event_id: str
    market_slug: str
    outcome_side: str
    forecast_probability: Decimal
    market_probability: Decimal
    taker_fee_probability: Decimal
    spread_probability: Decimal
    slippage_probability: Decimal
    settlement_delay_days: Decimal
    annual_capital_charge_probability: Decimal
    uncertainty_buffer_probability: Decimal
    manual_fraction_cap_probability: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ProbabilityEventCostAdjustedPositionRecommendationInput:
            raise TypeError(
                "ProbabilityEventCostAdjustedPositionRecommendationInput does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ProbabilityEventCostAdjustedPositionRecommendationInput:
            raise ValueError(
                "input must be exactly ProbabilityEventCostAdjustedPositionRecommendationInput",
            )
        object.__setattr__(self, "event_id", _require_identifier("event_id", self.event_id))
        object.__setattr__(
            self,
            "market_slug",
            _require_identifier("market_slug", self.market_slug),
        )
        object.__setattr__(
            self,
            "outcome_side",
            _require_outcome_side("outcome_side", self.outcome_side),
        )
        for field_name in PROBABILITY_FIELDS:
            object.__setattr__(
                self,
                field_name,
                _require_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "settlement_delay_days",
            _require_nonnegative_decimal(
                "settlement_delay_days",
                self.settlement_delay_days,
            ),
        )
        if self.manual_fraction_cap_probability == ZERO:
            raise ValueError("manual_fraction_cap_probability must be positive")
        _require_hard_flags(self)


@dataclass(frozen=True)
class ProbabilityEventCostAdjustedPositionRecommendationReport:
    config_version: str
    event_id: str
    market_slug: str
    outcome_side: str
    readiness_status: str
    forecast_probability: Decimal
    market_probability: Decimal
    taker_fee_probability: Decimal
    spread_probability: Decimal
    slippage_probability: Decimal
    settlement_delay_days: Decimal
    annual_capital_charge_probability: Decimal
    capital_lockup_cost_probability: Decimal
    cost_adjusted_break_even_probability: Decimal
    expected_value_probability: Decimal
    uncertainty_buffer_probability: Decimal
    margin_of_safety_probability: Decimal
    kelly_upper_bound_probability: Decimal
    manual_fraction_cap_probability: Decimal
    recommended_position_fraction_probability: Decimal
    capital_lockup_hint: str
    reason_codes: tuple[str, ...]
    manual_next_step: str
    payload_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ProbabilityEventCostAdjustedPositionRecommendationReport:
            raise TypeError(
                "ProbabilityEventCostAdjustedPositionRecommendationReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ProbabilityEventCostAdjustedPositionRecommendationReport:
            raise ValueError(
                "report must be exactly ProbabilityEventCostAdjustedPositionRecommendationReport",
            )
        _require_config_version(self.config_version)
        object.__setattr__(self, "event_id", _require_identifier("event_id", self.event_id))
        object.__setattr__(
            self,
            "market_slug",
            _require_identifier("market_slug", self.market_slug),
        )
        object.__setattr__(
            self,
            "outcome_side",
            _require_outcome_side("outcome_side", self.outcome_side),
        )
        object.__setattr__(
            self,
            "readiness_status",
            _require_status("readiness_status", self.readiness_status),
        )
        for field_name in REPORT_DECIMAL_FIELDS:
            if field_name == "settlement_delay_days":
                decimal = _require_nonnegative_decimal(field_name, getattr(self, field_name))
            elif field_name in (
                "expected_value_probability",
                "margin_of_safety_probability",
            ):
                decimal = _require_decimal(field_name, getattr(self, field_name))
            else:
                decimal = _require_probability(field_name, getattr(self, field_name))
            object.__setattr__(self, field_name, decimal)
        if self.manual_fraction_cap_probability == ZERO:
            raise ValueError("manual_fraction_cap_probability must be positive")
        object.__setattr__(
            self,
            "capital_lockup_hint",
            _require_capital_lockup_hint("capital_lockup_hint", self.capital_lockup_hint),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _require_manual_next_step(self.manual_next_step)
        _require_digest("payload_digest", self.payload_digest)
        _require_hard_flags(self)
        _validate_report(self)
        expected_digest = _payload_digest(_payload_items(self, payload_digest=""))
        if self.payload_digest != expected_digest:
            raise ValueError("payload_digest must match public payload")

    @property
    def public_payload(
        self,
    ) -> ProbabilityEventCostAdjustedPositionRecommendationPublicPayload:
        _validate_report_for_public_export(self)
        payload = ProbabilityEventCostAdjustedPositionRecommendationPublicPayload(
            _payload_items(self, payload_digest=self.payload_digest),
        )
        _validate_public_payload(payload)
        return payload


def build_probability_event_cost_adjusted_position_recommendation_report(
    inputs: ProbabilityEventCostAdjustedPositionRecommendationInput,
) -> ProbabilityEventCostAdjustedPositionRecommendationReport:
    """Build a deterministic Phase 1 cost-adjusted sizing recommendation."""

    if type(inputs) is not ProbabilityEventCostAdjustedPositionRecommendationInput:
        raise ValueError(
            "inputs must be a ProbabilityEventCostAdjustedPositionRecommendationInput",
        )
    _validate_input(inputs)
    derived = _derived_values(inputs)
    values: dict[str, object] = {
        "config_version": PROBABILITY_EVENT_COST_ADJUSTED_POSITION_RECOMMENDATION_REPORT_VERSION,
        "event_id": inputs.event_id,
        "market_slug": inputs.market_slug,
        "outcome_side": inputs.outcome_side,
        "forecast_probability": inputs.forecast_probability,
        "market_probability": inputs.market_probability,
        "taker_fee_probability": inputs.taker_fee_probability,
        "spread_probability": inputs.spread_probability,
        "slippage_probability": inputs.slippage_probability,
        "settlement_delay_days": inputs.settlement_delay_days,
        "annual_capital_charge_probability": inputs.annual_capital_charge_probability,
        "uncertainty_buffer_probability": inputs.uncertainty_buffer_probability,
        "manual_fraction_cap_probability": inputs.manual_fraction_cap_probability,
        **derived,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ProbabilityEventCostAdjustedPositionRecommendationReport(
        **values,
        payload_digest=_payload_digest(_payload_values(values, payload_digest="")),
    )


def probability_event_cost_adjusted_position_recommendation_report_payload(
    report: ProbabilityEventCostAdjustedPositionRecommendationReport,
) -> ProbabilityEventCostAdjustedPositionRecommendationPublicPayload:
    _validate_report_for_public_export(report)
    return report.public_payload


def probability_event_cost_adjusted_position_recommendation_report_digest(
    report: ProbabilityEventCostAdjustedPositionRecommendationReport,
) -> str:
    _validate_report_for_public_export(report)
    return _payload_digest(_payload_items(report, payload_digest=""))


def _derived_values(
    source: (
        ProbabilityEventCostAdjustedPositionRecommendationInput
        | ProbabilityEventCostAdjustedPositionRecommendationReport
    ),
) -> dict[str, object]:
    raw_capital_lockup_cost = _capital_lockup_cost(source)
    capital_lockup_cost = _min_decimal(raw_capital_lockup_cost, ONE)
    raw_break_even = _quantize(
        source.market_probability
        + source.taker_fee_probability
        + source.spread_probability
        + source.slippage_probability
        + raw_capital_lockup_cost,
    )
    break_even = _min_decimal(raw_break_even, ONE)
    expected_value = _quantize(source.forecast_probability - raw_break_even)
    margin_of_safety = _quantize(expected_value - source.uncertainty_buffer_probability)
    kelly_upper_bound = _kelly_upper_bound(expected_value, raw_break_even)
    recommended_position = _min_decimal(
        kelly_upper_bound,
        source.manual_fraction_cap_probability,
    )
    readiness_status = _readiness_status(
        expected_value=expected_value,
        margin_of_safety=margin_of_safety,
        settlement_delay_days=source.settlement_delay_days,
    )
    return {
        "readiness_status": readiness_status,
        "capital_lockup_cost_probability": capital_lockup_cost,
        "cost_adjusted_break_even_probability": break_even,
        "expected_value_probability": expected_value,
        "margin_of_safety_probability": margin_of_safety,
        "kelly_upper_bound_probability": kelly_upper_bound,
        "recommended_position_fraction_probability": recommended_position,
        "capital_lockup_hint": _capital_lockup_hint(source.settlement_delay_days),
        "reason_codes": _reason_codes(
            expected_value=expected_value,
            raw_break_even=raw_break_even,
            margin_of_safety=margin_of_safety,
            kelly_upper_bound=kelly_upper_bound,
            recommended_position=recommended_position,
            manual_fraction_cap=source.manual_fraction_cap_probability,
            settlement_delay_days=source.settlement_delay_days,
            capital_lockup_cost=capital_lockup_cost,
        ),
        "manual_next_step": _manual_next_step(readiness_status),
    }


def _validate_report(
    report: ProbabilityEventCostAdjustedPositionRecommendationReport,
) -> None:
    if type(report) is not ProbabilityEventCostAdjustedPositionRecommendationReport:
        raise ValueError(
            "report must be a ProbabilityEventCostAdjustedPositionRecommendationReport",
        )
    _require_config_version(report.config_version)
    _require_identifier("event_id", report.event_id)
    _require_identifier("market_slug", report.market_slug)
    _require_outcome_side("outcome_side", report.outcome_side)
    _require_status("readiness_status", report.readiness_status)
    for field_name in REPORT_DECIMAL_FIELDS:
        if field_name == "settlement_delay_days":
            _require_nonnegative_decimal(field_name, getattr(report, field_name))
        elif field_name in (
            "expected_value_probability",
            "margin_of_safety_probability",
        ):
            _require_decimal(field_name, getattr(report, field_name))
        else:
            _require_probability(field_name, getattr(report, field_name))
    if report.manual_fraction_cap_probability == ZERO:
        raise ValueError("manual_fraction_cap_probability must be positive")
    _require_capital_lockup_hint("capital_lockup_hint", report.capital_lockup_hint)
    _normalize_reason_codes(report.reason_codes)
    _require_manual_next_step(report.manual_next_step)
    _require_digest("payload_digest", report.payload_digest)
    _require_hard_flags(report)
    expected = _derived_values(report)
    for field_name, expected_value in expected.items():
        if getattr(report, field_name) != expected_value:
            raise ValueError(f"{field_name} must match input fields")


def _validate_report_for_public_export(
    report: ProbabilityEventCostAdjustedPositionRecommendationReport,
) -> None:
    _validate_report(report)
    expected_digest = _payload_digest(_payload_items(report, payload_digest=""))
    if report.payload_digest != expected_digest:
        raise ValueError("payload_digest must match public payload")


def _capital_lockup_cost(
    source: (
        ProbabilityEventCostAdjustedPositionRecommendationInput
        | ProbabilityEventCostAdjustedPositionRecommendationReport
    ),
) -> Decimal:
    return _quantize(
        source.market_probability
        * source.annual_capital_charge_probability
        * source.settlement_delay_days
        / DAYS_IN_YEAR,
    )


def _kelly_upper_bound(expected_value: Decimal, break_even: Decimal) -> Decimal:
    if expected_value <= ZERO:
        return ZERO
    denominator = _quantize(ONE - break_even)
    if denominator <= ZERO:
        return ZERO
    return _require_probability(
        "kelly_upper_bound_probability",
        _quantize(expected_value / denominator),
    )


def _readiness_status(
    *,
    expected_value: Decimal,
    margin_of_safety: Decimal,
    settlement_delay_days: Decimal,
) -> str:
    if expected_value <= ZERO:
        return "blocked"
    if margin_of_safety < WATCH_MARGIN_OF_SAFETY:
        return "watch"
    if settlement_delay_days > EXTENDED_SETTLEMENT_DAYS:
        return "watch"
    return "pass"


def _reason_codes(
    *,
    expected_value: Decimal,
    raw_break_even: Decimal,
    margin_of_safety: Decimal,
    kelly_upper_bound: Decimal,
    recommended_position: Decimal,
    manual_fraction_cap: Decimal,
    settlement_delay_days: Decimal,
    capital_lockup_cost: Decimal,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if expected_value > ZERO:
        reason_codes.append("cost_adjusted_expected_value_positive")
    else:
        reason_codes.append("cost_adjusted_expected_value_not_positive")
    if raw_break_even > ONE:
        reason_codes.append("cost_adjusted_break_even_exceeds_probability_ceiling")
    if margin_of_safety > ZERO:
        reason_codes.append("margin_of_safety_positive")
    else:
        reason_codes.append("margin_of_safety_not_positive")
    if kelly_upper_bound == ZERO:
        reason_codes.append("kelly_upper_bound_zero")
    elif recommended_position == manual_fraction_cap:
        reason_codes.append("kelly_upper_bound_manual_cap_applied")
    else:
        reason_codes.append("kelly_upper_bound_below_manual_cap")
    if capital_lockup_cost > ZERO:
        reason_codes.append("capital_lockup_cost_present")
    if settlement_delay_days > EXTENDED_SETTLEMENT_DAYS:
        reason_codes.append("extended_settlement_delay_capital_lockup_watch")
    if ZERO < margin_of_safety < WATCH_MARGIN_OF_SAFETY:
        reason_codes.append("margin_of_safety_below_watch_threshold")
    return tuple(reason_codes)


def _validate_input(
    inputs: ProbabilityEventCostAdjustedPositionRecommendationInput,
) -> None:
    if type(inputs) is not ProbabilityEventCostAdjustedPositionRecommendationInput:
        raise ValueError(
            "inputs must be a ProbabilityEventCostAdjustedPositionRecommendationInput",
        )
    _require_identifier("event_id", inputs.event_id)
    _require_identifier("market_slug", inputs.market_slug)
    _require_outcome_side("outcome_side", inputs.outcome_side)
    for field_name in PROBABILITY_FIELDS:
        _require_probability(field_name, getattr(inputs, field_name))
    _require_nonnegative_decimal("settlement_delay_days", inputs.settlement_delay_days)
    if inputs.manual_fraction_cap_probability == ZERO:
        raise ValueError("manual_fraction_cap_probability must be positive")
    _require_hard_flags(inputs)


def _manual_next_step(readiness_status: str) -> str:
    if readiness_status == "pass":
        return "document_phase1_readonly_position_boundary"
    if readiness_status == "watch":
        return "manual_review_costs_lockup_and_position_cap"
    return "do_not_size_until_cost_adjusted_ev_improves"


def _capital_lockup_hint(settlement_delay_days: Decimal) -> str:
    if settlement_delay_days > EXTENDED_SETTLEMENT_DAYS:
        return "extended_settlement_delay_capital_locked"
    return "standard_capital_lockup_review"


def _validate_public_payload(payload: Mapping[str, object]) -> Mapping[str, object]:
    if not isinstance(payload, Mapping):
        raise ValueError("payload must be a mapping")
    if tuple(payload.keys()) != PAYLOAD_KEYS:
        raise ValueError("payload must match the canonical position recommendation schema")
    _require_config_version(payload["config_version"])
    _require_identifier("event_id", payload["event_id"])
    _require_identifier("market_slug", payload["market_slug"])
    _require_outcome_side("outcome_side", payload["outcome_side"])
    _require_status("readiness_status", payload["readiness_status"])
    for field_name in REPORT_DECIMAL_FIELDS:
        value = payload[field_name]
        if type(value) is not str:
            raise ValueError(f"{field_name} must be serialized as a string")
        if field_name == "settlement_delay_days":
            _require_nonnegative_decimal(field_name, Decimal(value))
        elif field_name in (
            "expected_value_probability",
            "margin_of_safety_probability",
        ):
            _require_decimal(field_name, Decimal(value))
        else:
            _require_probability(field_name, Decimal(value))
    _require_capital_lockup_hint("capital_lockup_hint", payload["capital_lockup_hint"])
    reason_codes = payload["reason_codes"]
    if type(reason_codes) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    _normalize_reason_codes(reason_codes)
    _require_manual_next_step(payload["manual_next_step"])
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload[field_name] is not True:
            raise ValueError(f"{field_name} must be True")
    _require_digest("payload_digest", payload["payload_digest"])
    return payload


def _payload_items(
    report: ProbabilityEventCostAdjustedPositionRecommendationReport,
    *,
    payload_digest: str,
) -> dict[str, object]:
    return _payload_values(
        {
            "config_version": report.config_version,
            "event_id": report.event_id,
            "market_slug": report.market_slug,
            "outcome_side": report.outcome_side,
            "readiness_status": report.readiness_status,
            "forecast_probability": report.forecast_probability,
            "market_probability": report.market_probability,
            "taker_fee_probability": report.taker_fee_probability,
            "spread_probability": report.spread_probability,
            "slippage_probability": report.slippage_probability,
            "settlement_delay_days": report.settlement_delay_days,
            "annual_capital_charge_probability": report.annual_capital_charge_probability,
            "capital_lockup_cost_probability": report.capital_lockup_cost_probability,
            "cost_adjusted_break_even_probability": (
                report.cost_adjusted_break_even_probability
            ),
            "expected_value_probability": report.expected_value_probability,
            "uncertainty_buffer_probability": report.uncertainty_buffer_probability,
            "margin_of_safety_probability": report.margin_of_safety_probability,
            "kelly_upper_bound_probability": report.kelly_upper_bound_probability,
            "manual_fraction_cap_probability": report.manual_fraction_cap_probability,
            "recommended_position_fraction_probability": (
                report.recommended_position_fraction_probability
            ),
            "capital_lockup_hint": report.capital_lockup_hint,
            "reason_codes": report.reason_codes,
            "manual_next_step": report.manual_next_step,
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
        payload_digest=payload_digest,
    )


def _payload_values(values: Mapping[str, object], *, payload_digest: str) -> dict[str, object]:
    return {
        "config_version": values["config_version"],
        "event_id": values["event_id"],
        "market_slug": values["market_slug"],
        "outcome_side": values["outcome_side"],
        "readiness_status": values["readiness_status"],
        "forecast_probability": _decimal_text(values["forecast_probability"]),
        "market_probability": _decimal_text(values["market_probability"]),
        "taker_fee_probability": _decimal_text(values["taker_fee_probability"]),
        "spread_probability": _decimal_text(values["spread_probability"]),
        "slippage_probability": _decimal_text(values["slippage_probability"]),
        "settlement_delay_days": _decimal_text(values["settlement_delay_days"]),
        "annual_capital_charge_probability": _decimal_text(
            values["annual_capital_charge_probability"],
        ),
        "capital_lockup_cost_probability": _decimal_text(
            values["capital_lockup_cost_probability"],
        ),
        "cost_adjusted_break_even_probability": _decimal_text(
            values["cost_adjusted_break_even_probability"],
        ),
        "expected_value_probability": _decimal_text(values["expected_value_probability"]),
        "uncertainty_buffer_probability": _decimal_text(
            values["uncertainty_buffer_probability"],
        ),
        "margin_of_safety_probability": _decimal_text(
            values["margin_of_safety_probability"],
        ),
        "kelly_upper_bound_probability": _decimal_text(
            values["kelly_upper_bound_probability"],
        ),
        "manual_fraction_cap_probability": _decimal_text(
            values["manual_fraction_cap_probability"],
        ),
        "recommended_position_fraction_probability": _decimal_text(
            values["recommended_position_fraction_probability"],
        ),
        "capital_lockup_hint": values["capital_lockup_hint"],
        "reason_codes": values["reason_codes"],
        "manual_next_step": values["manual_next_step"],
        "paper_only": True,
        "report_only": True,
        "readonly": True,
        "payload_digest": payload_digest,
    }


def _payload_digest(payload: Mapping[str, object]) -> str:
    return sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8"),
    ).hexdigest()


def _require_config_version(value: object) -> str:
    if (
        type(value) is not str
        or value
        != PROBABILITY_EVENT_COST_ADJUSTED_POSITION_RECOMMENDATION_REPORT_VERSION
    ):
        raise ValueError("config_version must be the supported report version")
    return value


def _require_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    for character in value:
        if not (character.islower() or character.isdigit() or character in "-_"):
            raise ValueError(f"{field_name} must use lowercase public identifier characters")
    return value


def _require_outcome_side(field_name: str, value: object) -> str:
    if type(value) is not str or value not in OUTCOME_SIDES:
        raise ValueError(f"{field_name} must be a string containing yes or no")
    return value


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in READINESS_STATUSES:
        raise ValueError(
            f"{field_name} must be a string containing pass, watch, or blocked",
        )
    return value


def _require_capital_lockup_hint(field_name: str, value: object) -> str:
    if type(value) is not str or value not in CAPITAL_LOCKUP_HINTS:
        raise ValueError(f"{field_name} must be a supported capital lockup hint")
    return value


def _require_manual_next_step(value: object) -> str:
    if type(value) is not str or value not in MANUAL_NEXT_STEPS:
        raise ValueError("manual_next_step must be supported")
    return value


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    for reason_code in value:
        if type(reason_code) is not str or reason_code not in REASON_CODES:
            raise ValueError("reason_codes must be supported")
    return value


def _require_probability(field_name: str, value: object) -> Decimal:
    decimal = _require_decimal(field_name, value)
    if decimal < ZERO or decimal > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return decimal


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal = _require_decimal(field_name, value)
    if decimal < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    normalized = _quantize(value)
    if value != normalized or value.as_tuple().exponent != QUANTUM.as_tuple().exponent:
        raise ValueError(f"{field_name} must use six decimal places")
    return normalized


def _require_digest(field_name: str, value: object) -> str:
    if type(value) is not str or not DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    return value


def _require_hard_flags(value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True")


def _min_decimal(left: Decimal, right: Decimal) -> Decimal:
    if left <= right:
        return left
    return right


def _quantize(value: Decimal) -> Decimal:
    normalized = value.quantize(QUANTUM, rounding=ROUND_HALF_UP)
    if normalized == Decimal("-0.000000"):
        return ZERO
    return normalized


def _decimal_text(value: object) -> str:
    if type(value) is not Decimal:
        raise ValueError("payload decimal value must be a Decimal")
    return format(value, "f")
