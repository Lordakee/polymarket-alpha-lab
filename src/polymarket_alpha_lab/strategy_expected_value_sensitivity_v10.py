"""Pure Decimal EV sensitivity model for probability event research."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Context, Decimal, InvalidOperation, localcontext


__all__ = (
    "StrategyExpectedValueSensitivityV10Input",
    "StrategyExpectedValueSensitivityV10Report",
    "evaluate_strategy_expected_value_sensitivity_v10",
    "strategy_expected_value_sensitivity_v10_payload",
)


QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
BPS_DENOMINATOR = Decimal("10000.000000")
DECIMAL_CONTEXT = Context(prec=64)

SENSITIVITY_TIERS = ("high_conviction", "fragile", "negative")
TIER_REASON_BY_STATUS = {
    "high_conviction": "sensitivity_tier_high_conviction",
    "fragile": "sensitivity_tier_fragile",
    "negative": "sensitivity_tier_negative",
}
TIER_REASON_CODES = frozenset(TIER_REASON_BY_STATUS.values())


@dataclass(frozen=True)
class StrategyExpectedValueSensitivityV10Input:
    market_price: Decimal
    forecast_probability: Decimal
    fee_rate: Decimal
    slippage_bps: Decimal
    probability_error_bps: Decimal
    settlement_cost_bps: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("market_price", "forecast_probability", "fee_rate"):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "slippage_bps",
            "probability_error_bps",
            "settlement_cost_bps",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_bps_decimal(field_name, getattr(self, field_name)),
            )
        _require_safety_flags("row", self)


@dataclass(frozen=True)
class StrategyExpectedValueSensitivityV10Report:
    market_price: Decimal
    forecast_probability: Decimal
    fee_rate: Decimal
    slippage_bps: Decimal
    probability_error_bps: Decimal
    settlement_cost_bps: Decimal
    slippage_rate: Decimal
    probability_error_rate: Decimal
    settlement_cost_rate: Decimal
    total_cost_drag: Decimal
    base_ev: Decimal
    worst_case_ev: Decimal
    breakeven_probability: Decimal
    sensitivity_tier: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("market_price", "forecast_probability", "fee_rate"):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "slippage_bps",
            "probability_error_bps",
            "settlement_cost_bps",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_bps_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "slippage_rate",
            "probability_error_rate",
            "settlement_cost_rate",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "total_cost_drag",
            _normalize_nonnegative_decimal("total_cost_drag", self.total_cost_drag),
        )
        for field_name in ("base_ev", "worst_case_ev"):
            object.__setattr__(
                self,
                field_name,
                _normalize_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "breakeven_probability",
            _normalize_nonnegative_decimal(
                "breakeven_probability",
                self.breakeven_probability,
            ),
        )
        _require_member("sensitivity_tier", self.sensitivity_tier, SENSITIVITY_TIERS)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, require_nonempty=True),
        )
        _validate_report(self)
        _require_safety_flags("report", self)


def evaluate_strategy_expected_value_sensitivity_v10(
    row: object,
) -> StrategyExpectedValueSensitivityV10Report:
    if type(row) is not StrategyExpectedValueSensitivityV10Input:
        raise ValueError("row must be a StrategyExpectedValueSensitivityV10Input")
    _require_safety_flags("row", row)

    slippage_rate = _bps_to_rate(row.slippage_bps)
    probability_error_rate = _bps_to_rate(row.probability_error_bps)
    settlement_cost_rate = _bps_to_rate(row.settlement_cost_bps)
    total_cost_drag = _add_decimal(
        _add_decimal(row.fee_rate, slippage_rate),
        settlement_cost_rate,
    )
    breakeven_probability = _add_decimal(row.market_price, total_cost_drag)
    base_ev = _subtract_decimal(row.forecast_probability, breakeven_probability)
    worst_case_ev = _subtract_decimal(base_ev, probability_error_rate)
    sensitivity_tier = _sensitivity_tier(base_ev, worst_case_ev)

    return StrategyExpectedValueSensitivityV10Report(
        market_price=row.market_price,
        forecast_probability=row.forecast_probability,
        fee_rate=row.fee_rate,
        slippage_bps=row.slippage_bps,
        probability_error_bps=row.probability_error_bps,
        settlement_cost_bps=row.settlement_cost_bps,
        slippage_rate=slippage_rate,
        probability_error_rate=probability_error_rate,
        settlement_cost_rate=settlement_cost_rate,
        total_cost_drag=total_cost_drag,
        base_ev=base_ev,
        worst_case_ev=worst_case_ev,
        breakeven_probability=breakeven_probability,
        sensitivity_tier=sensitivity_tier,
        reason_codes=_reason_codes(
            sensitivity_tier=sensitivity_tier,
            base_ev=base_ev,
            worst_case_ev=worst_case_ev,
            probability_error_rate=probability_error_rate,
            total_cost_drag=total_cost_drag,
        ),
    )


def strategy_expected_value_sensitivity_v10_payload(
    report: StrategyExpectedValueSensitivityV10Report,
) -> dict[str, object]:
    if type(report) is not StrategyExpectedValueSensitivityV10Report:
        raise ValueError("report must be a StrategyExpectedValueSensitivityV10Report")
    _require_safety_flags("report", report)
    return {
        "market_price": _decimal_payload(report.market_price),
        "forecast_probability": _decimal_payload(report.forecast_probability),
        "fee_rate": _decimal_payload(report.fee_rate),
        "slippage_bps": _decimal_payload(report.slippage_bps),
        "probability_error_bps": _decimal_payload(report.probability_error_bps),
        "settlement_cost_bps": _decimal_payload(report.settlement_cost_bps),
        "slippage_rate": _decimal_payload(report.slippage_rate),
        "probability_error_rate": _decimal_payload(report.probability_error_rate),
        "settlement_cost_rate": _decimal_payload(report.settlement_cost_rate),
        "total_cost_drag": _decimal_payload(report.total_cost_drag),
        "base_ev": _decimal_payload(report.base_ev),
        "worst_case_ev": _decimal_payload(report.worst_case_ev),
        "breakeven_probability": _decimal_payload(report.breakeven_probability),
        "sensitivity_tier": report.sensitivity_tier,
        "reason_codes": list(report.reason_codes),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _sensitivity_tier(base_ev: Decimal, worst_case_ev: Decimal) -> str:
    if base_ev <= ZERO:
        return "negative"
    if worst_case_ev <= ZERO:
        return "fragile"
    return "high_conviction"


def _reason_codes(
    *,
    sensitivity_tier: str,
    base_ev: Decimal,
    worst_case_ev: Decimal,
    probability_error_rate: Decimal,
    total_cost_drag: Decimal,
) -> tuple[str, ...]:
    return _normalize_reason_codes(
        (
            TIER_REASON_BY_STATUS[sensitivity_tier],
            "base_ev_positive" if base_ev > ZERO else "base_ev_nonpositive",
            (
                "worst_case_ev_positive"
                if worst_case_ev > ZERO
                else "worst_case_ev_nonpositive"
            ),
            (
                "probability_error_buffered"
                if probability_error_rate > ZERO
                else "probability_error_none"
            ),
            "cost_drag_present" if total_cost_drag > ZERO else "cost_drag_none",
        ),
        require_nonempty=True,
    )


def _validate_report(report: StrategyExpectedValueSensitivityV10Report) -> None:
    if report.slippage_rate != _bps_to_rate(report.slippage_bps):
        raise ValueError("slippage_rate must match slippage_bps")
    if report.probability_error_rate != _bps_to_rate(report.probability_error_bps):
        raise ValueError("probability_error_rate must match probability_error_bps")
    if report.settlement_cost_rate != _bps_to_rate(report.settlement_cost_bps):
        raise ValueError("settlement_cost_rate must match settlement_cost_bps")
    expected_total_cost_drag = _add_decimal(
        _add_decimal(report.fee_rate, report.slippage_rate),
        report.settlement_cost_rate,
    )
    if report.total_cost_drag != expected_total_cost_drag:
        raise ValueError("total_cost_drag must match fee and cost rates")
    expected_breakeven_probability = _add_decimal(
        report.market_price,
        report.total_cost_drag,
    )
    if report.breakeven_probability != expected_breakeven_probability:
        raise ValueError("breakeven_probability must match price plus costs")
    expected_base_ev = _subtract_decimal(
        report.forecast_probability,
        report.breakeven_probability,
    )
    if report.base_ev != expected_base_ev:
        raise ValueError("base_ev must match forecast less breakeven")
    expected_worst_case_ev = _subtract_decimal(
        report.base_ev,
        report.probability_error_rate,
    )
    if report.worst_case_ev != expected_worst_case_ev:
        raise ValueError("worst_case_ev must match base_ev less probability error")
    expected_tier = _sensitivity_tier(report.base_ev, report.worst_case_ev)
    if report.sensitivity_tier != expected_tier:
        raise ValueError("sensitivity_tier must match EV thresholds")
    expected_tier_reason = TIER_REASON_BY_STATUS[report.sensitivity_tier]
    if expected_tier_reason not in report.reason_codes:
        raise ValueError("reason_codes must include tier reason")
    conflicting_tier_reasons = (
        TIER_REASON_CODES - frozenset((expected_tier_reason,))
    ).intersection(report.reason_codes)
    if conflicting_tier_reasons:
        raise ValueError("reason_codes must not include conflicting tier reasons")


def _require_safety_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only") is not True:
        raise ValueError(f"paper_only must be True for {label}")
    if getattr(value, "report_only") is not True:
        raise ValueError(f"report_only must be True for {label}")
    if getattr(value, "readonly") is not True:
        raise ValueError(f"readonly must be True for {label}")


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed}")


def _normalize_bps_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > BPS_DENOMINATOR:
        raise ValueError(f"{field_name} must not exceed 10000")
    return normalized


def _normalize_probability_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be a probability Decimal")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if isinstance(value, Decimal) and type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    try:
        with localcontext(DECIMAL_CONTEXT):
            return value.quantize(QUANTUM)
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"{field_name} must be quantizable") from exc


def _add_decimal(first: Decimal, second: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return (first + second).quantize(QUANTUM)


def _subtract_decimal(first: Decimal, second: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return (first - second).quantize(QUANTUM)


def _divide_decimal(numerator: Decimal, denominator: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(QUANTUM)


def _bps_to_rate(value: Decimal) -> Decimal:
    return _divide_decimal(value, BPS_DENOMINATOR)


def _normalize_reason_codes(
    values: object,
    *,
    require_nonempty: bool,
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("reason_codes must be an iterable")
    if isinstance(values, (set, frozenset)):
        raise ValueError("reason_codes must be an ordered iterable")
    try:
        reason_codes = tuple(values)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable") from exc
    if require_nonempty and not reason_codes:
        raise ValueError("reason_codes must not be empty")
    for reason_code in reason_codes:
        _require_canonical_reason_code("reason_codes", reason_code)
    return tuple(dict.fromkeys(reason_codes))


def _require_canonical_reason_code(field_name: str, value: object) -> None:
    if type(value) is not str or not value:
        raise ValueError(f"{field_name} must contain canonical reason codes")
    if value != value.lower() or value.strip() != value:
        raise ValueError(f"{field_name} must contain canonical reason codes")
    for part in value.split("_"):
        if not part or not part.isalnum() or part != part.lower():
            raise ValueError(f"{field_name} must contain canonical reason codes")


def _decimal_payload(value: Decimal) -> str:
    return format(_normalize_decimal("payload decimal", value), "f")
